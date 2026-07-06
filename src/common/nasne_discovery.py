# nasne の自動発見（SSDP / UPnP M-SEARCH）とIPキャッシュ (SPEC §2.4)
#
# 探索方式（SONY製・バッファロー製の両方で実機検証済み）:
#   1. nasne 固有のサービス urn:schemas-sony-com:service:X_Telepathy:1 で M-SEARCH
#      ※ MediaServer:1 だとバッファロー製nasne（スタンバイ中にDLNA機能が寝ている個体）が
#        応答しないため使わない
#   2. 応答したIPに対し nasne API (http://<ip>:64210/status/boxNameGet) を並列で叩き、
#      応答したものだけを nasne と確定（名前もここから取得）
#
# - 発見結果は nasne_ips.cache (JSON) に保存し、通常起動時はキャッシュを使う
# - 探索を行うのは「初回起動時（ini手動指定もキャッシュも無い）」と「--discover 指定時」のみ
import json
import os
import re
import socket
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SSDP_ADDR = ("239.255.255.250", 1900)
# nasne 固有の UPnP サービス（SONY製・バッファロー製とも応答する）
SSDP_ST_NASNE = "urn:schemas-sony-com:service:X_Telepathy:1"
CACHE_FILENAME = "nasne_ips.cache"


def _app_dir():
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def _cache_path():
    return os.path.join(_app_dir(), CACHE_FILENAME)


def load_cached_ips():
    """キャッシュされた nasne の IP リストを返す。無ければ None"""
    try:
        with open(_cache_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        ips = data.get("ips")
        if isinstance(ips, list) and ips:
            return ips
    except (OSError, ValueError):
        pass
    return None


def save_cached_ips(ips):
    try:
        with open(_cache_path(), "w", encoding="utf-8") as f:
            json.dump({"ips": ips}, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def _msearch_ips(st, wait_sec):
    """SSDP M-SEARCH を投げ、応答したIPの集合を返す"""
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR[0]}:{SSDP_ADDR[1]}\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        f"ST: {st}\r\n"
        "\r\n"
    ).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(wait_sec)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    except OSError:
        pass

    # 取りこぼし対策で複数回送信
    for _ in range(3):
        try:
            sock.sendto(msg, SSDP_ADDR)
        except OSError:
            return set()
        time.sleep(0.1)

    ips = set()
    try:
        while True:
            _, addr = sock.recvfrom(8192)
            ips.add(addr[0])
    except socket.timeout:
        pass
    finally:
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


def discover_nasnes(wait_sec=3.0):
    """SSDP で LAN 内の nasne を探索し、[(ip, name), ...] を IP 順で返す"""
    candidates = _msearch_ips(SSDP_ST_NASNE, wait_sec)
    if not candidates:
        # 保険: nasne固有STに応答しないファームウェア向けに全機器から拾う
        candidates = _msearch_ips("ssdp:all", wait_sec)
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda ip: tuple(int(o) for o in ip.split(".")))
    with ThreadPoolExecutor(max_workers=len(ordered)) as executor:
        names = list(executor.map(_probe_nasne, ordered))

    return [(ip, name) for ip, name in zip(ordered, names) if name is not None]
