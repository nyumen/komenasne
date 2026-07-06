# nasne の自動発見（SSDP / UPnP M-SEARCH）とIPキャッシュ (SPEC §2.4)
#
# - LAN に M-SEARCH を投げ、応答した MediaServer のデバイス記述XMLを取得し
#   modelName が nasne のものだけを採用する（実機検証済み）
# - 発見結果は nasne_ips.cache (JSON) に保存し、通常起動時はキャッシュを使う
# - 探索を行うのは「初回起動時（ini手動指定もキャッシュも無い）」と「--discover 指定時」のみ
import json
import os
import re
import socket
import sys
import time
import urllib.request

SSDP_ADDR = ("239.255.255.250", 1900)
SSDP_ST = "urn:schemas-upnp-org:device:MediaServer:1"
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


def _fetch_device_info(location):
    """デバイス記述XMLから (modelName, friendlyName) を取得"""
    try:
        with urllib.request.urlopen(location, timeout=3) as r:
            xml = r.read().decode(errors="replace")
    except Exception:
        return None, None
    model = re.search(r"<modelName>([^<]+)</modelName>", xml)
    friendly = re.search(r"<friendlyName>([^<]+)</friendlyName>", xml)
    return (
        model.group(1) if model else None,
        friendly.group(1) if friendly else None,
    )


def discover_nasnes(wait_sec=3.0):
    """SSDP で LAN 内の nasne を探索し、[(ip, friendlyName), ...] を IP 順で返す"""
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR[0]}:{SSDP_ADDR[1]}\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        f"ST: {SSDP_ST}\r\n"
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
            return []
        time.sleep(0.1)

    locations = {}  # ip -> LOCATION URL
    try:
        while True:
            data, addr = sock.recvfrom(8192)
            text = data.decode(errors="replace")
            m = re.search(r"(?im)^LOCATION:\s*(\S+)", text)
            if m and addr[0] not in locations:
                locations[addr[0]] = m.group(1)
    except socket.timeout:
        pass
    finally:
        sock.close()

    nasnes = []
    for ip, location in locations.items():
        model, friendly = _fetch_device_info(location)
        if model and "nasne" in model.lower():
            nasnes.append((ip, friendly or "nasne"))

    # IPアドレス順で安定させる
    nasnes.sort(key=lambda x: tuple(int(o) for o in x[0].split(".")))
    return nasnes
