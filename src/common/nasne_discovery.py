# nasne の自動発見（SSDP / UPnP M-SEARCH）(SPEC §2.4)
#
# 探索方式（SONY製・バッファロー製の両方で実機検証済み）:
#   1. nasne 固有のサービス urn:schemas-sony-com:service:X_Telepathy:1 で M-SEARCH
#      ※ MediaServer:1 だとバッファロー製nasne（スタンバイ中にDLNA機能が寝ている個体）が
#        応答しないため使わない
#   2. 応答したIPに対し nasne API (http://<ip>:64210/status/boxNameGet) を並列で叩き、
#      応答したものだけを nasne と確定（名前もここから取得）
#
# - 発見結果は komenasne.ini の [NASNE] ip に書き戻す（コメント行は保持）
# - 探索を行うのは「初回起動時（ini の ip が未設定）」と「--discover 指定時」のみ
import json
import re
import socket
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SSDP_ADDR = ("239.255.255.250", 1900)
# nasne 固有の UPnP サービス（SONY製・バッファロー製とも応答する）
SSDP_ST_NASNE = "urn:schemas-sony-com:service:X_Telepathy:1"


def update_ini_ips(ini_path, ips):
    """ini の [NASNE] セクションの ip 行だけを書き換える（configparser を使わずコメント行を保持する）"""
    joined = ", ".join(ips)
    try:
        with open(ini_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False

    out = []
    in_nasne = False
    replaced = False
    for line in lines:
        section = re.match(r"^\s*\[(.+)\]", line)
        if section:
            # [NASNE] を抜けるまでに ip 行が無ければセクション末尾に追加
            if in_nasne and not replaced:
                out.append(f"ip = {joined}\n")
                replaced = True
            in_nasne = section.group(1).strip().upper() == "NASNE"
        elif in_nasne and not replaced and re.match(r"^\s*ip\s*=", line):
            out.append(f"ip = {joined}\n")
            replaced = True
            continue
        out.append(line)

    if not replaced:
        if in_nasne:
            # ファイル末尾まで [NASNE] セクションだった場合
            out.append(f"ip = {joined}\n")
        else:
            out.append(f"\n[NASNE]\nip = {joined}\n")

    try:
        with open(ini_path, "w", encoding="utf-8") as f:
            f.writelines(out)
        return True
    except OSError:
        return False


def _local_ipv4_addresses():
    """このマシンのIPv4アドレス一覧（マルチキャスト送信元の候補）を返す"""
    addrs = set()
    # ホスト名から引けるアドレス（複数NIC対応）
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addrs.add(info[4][0])
    except socket.gaierror:
        pass
    # デフォルト経路のアドレス（UDP connect トリック。実際には送信しない）
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 80))
        addrs.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return [a for a in addrs if not a.startswith("127.")]


def _msearch_ips(st, wait_sec):
    """SSDP M-SEARCH を全インターフェースから投げ、応答したIPの集合を返す

    Windows では Hyper-V/WSL の仮想アダプタや VPN が居るとマルチキャストが
    LAN と別のインターフェースへ送信されることがあるため、全IPv4アドレスを
    送信元にしてそれぞれ送る。
    """
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR[0]}:{SSDP_ADDR[1]}\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        f"ST: {st}\r\n"
        "\r\n"
    ).encode()

    sockets = []
    for local_addr in _local_ipv4_addresses() or [""]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setblocking(False)
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
                if local_addr:
                    sock.bind((local_addr, 0))
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_addr))
            except OSError:
                pass
            sockets.append(sock)
        except OSError:
            continue

    if not sockets:
        return set()

    # 取りこぼし対策で複数回送信
    for _ in range(3):
        for sock in sockets:
            try:
                sock.sendto(msg, SSDP_ADDR)
            except OSError:
                pass
        time.sleep(0.1)

    ips = set()
    deadline = time.monotonic() + wait_sec
    while time.monotonic() < deadline:
        for sock in sockets:
            try:
                while True:
                    _, addr = sock.recvfrom(8192)
                    ips.add(addr[0])
            except (BlockingIOError, OSError):
                pass
        time.sleep(0.05)
    for sock in sockets:
        sock.close()
    return ips


def _probe_nasne(ip):
    """nasne API で確定判定し、本体名を返す。nasne でなければ None"""
    try:
        with urllib.request.urlopen(f"http://{ip}:64210/status/boxNameGet", timeout=2) as r:
            data = json.loads(r.read().decode(errors="replace"))
        if data.get("errorcode") == 0:
            return data.get("name") or "nasne"
    except Exception:
        pass
    return None


def _scan_subnets():
    """SSDP が使えない環境向けの保険: ローカル /24 サブネットの全ホストに
    nasne API ポートを直接プローブする（TCPなのでファイアウォールの影響を受けにくい）"""

    def _tcp_probe(ip):
        try:
            with socket.create_connection((ip, 64210), timeout=0.5):
                return ip
        except OSError:
            return None

    targets = []
    seen_subnets = set()
    for local_addr in _local_ipv4_addresses():
        prefix = ".".join(local_addr.split(".")[:3])
        if prefix in seen_subnets:
            continue
        seen_subnets.add(prefix)
        targets += [f"{prefix}.{i}" for i in range(1, 255)]

    if not targets:
        return set()

    with ThreadPoolExecutor(max_workers=64) as executor:
        results = executor.map(_tcp_probe, targets)
    return {ip for ip in results if ip}


def discover_nasnes(wait_sec=3.0):
    """LAN 内の nasne を探索し、[(ip, name), ...] を IP 順で返す

    1. SSDP（nasne固有の X_Telepathy サービス）
    2. SSDP（ssdp:all / 古いファームウェア向けの保険）
    3. サブネットスキャン（マルチキャストが使えない環境向けの保険）
    候補はいずれも nasne API（boxNameGet）で確定判定する。
    """
    candidates = _msearch_ips(SSDP_ST_NASNE, wait_sec)
    if not candidates:
        candidates = _msearch_ips("ssdp:all", wait_sec)
    if not candidates:
        candidates = _scan_subnets()
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda ip: tuple(int(o) for o in ip.split(".")))
    with ThreadPoolExecutor(max_workers=min(len(ordered), 16)) as executor:
        names = list(executor.map(_probe_nasne, ordered))

    return [(ip, name) for ip, name in zip(ordered, names) if name is not None]
