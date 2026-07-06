# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from dateutil.parser import parse
import re
import subprocess
import configparser
import os
import sys
import time
import math
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger, StreamHandler, Formatter, FileHandler, INFO
import argparse
import pathlib
from pathlib import Path
from zoneinfo import ZoneInfo

# タイムゾーンの設定
JST = ZoneInfo("Asia/Tokyo")

# nasne API のタイムアウト（秒）。電源オフの nasne がいても待たされないよう短めにする
NASNE_API_TIMEOUT = 2.0

from common.channel_list import ChannelList
from common.nasne_discovery import discover_nasnes, update_ini_ips


def get_logger():
    logger = getLogger(__name__)
    logger.setLevel(INFO)
    sh = StreamHandler()
    sh.setLevel(INFO)
    logger.addHandler(sh)

    log_file_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "komenasne.log")
    fh = FileHandler(log_file_path, encoding="utf-8")
    fh.setLevel(INFO)
    fh_formatter = Formatter("%(asctime)s - %(message)s")
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    return logger


def get_item(ip_addr, playing_content_id):
    for item in get_title_list(ip_addr):
        if item["id"] == playing_content_id:
            return item


def get_title_list(ip_addr):
    """nasne の録画済みタイトル一覧を返す"""
    r = requests.get(
        f"http://{ip_addr}:64220/recorded/titleListGet?searchCriteria=0&filter=0&startingIndex=0&requestedCount=0&sortCriteria=0&withDescriptionLong=0&withUserData=0",
        timeout=10,
    )
    return json.loads(r.text).get("item", [])


def get_jkid(service_id):
    for jkch, sevice_ids in ChannelList.jk_chs.items():
        if service_id in sevice_ids:
            return jkch
    return False


def get_datetime(date_time):
    return datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S+09:00")


# ファイル名に使用できない文字（ARIB外字）を変換
def replace_title(title):
    title = title.replace("\ue180", "[デ]")
    title = title.replace("\ue182", "[二]")
    title = title.replace("\ue183", "[多]")
    title = title.replace("\ue184", "[解]")
    title = title.replace("\ue185", "[SS]")
    title = title.replace("\ue18c", "[映]")
    title = title.replace("\ue18d", "[無]")
    title = title.replace("\ue190", "[前]")
    title = title.replace("\ue191", "[後]")
    title = title.replace("\ue192", "[再]")
    title = title.replace("\ue193", "[新]")
    title = title.replace("\ue194", "[初]")
    title = title.replace("\ue195", "[終]")
    title = title.replace("\ue196", "[生]")
    title = title.replace("\ue199", "[吹]")
    title = title.replace("\ue0fd", "[手]")
    title = title.replace("\ue0fe", "[字]")
    title = title.replace("\ue2ca", "No")
    title = title.replace("\ue2f0", "！？")
    title = title.replace("\u203c", "！！")
    title = title.replace("\u3000", " ")
    title = title.replace("\u1f6f0", "")  # 衛星
    title = title.replace("/", "／")
    title = title.replace("<", "＜")
    title = title.replace(">", "＞")
    title = title.replace(":", "：")
    title = title.replace("?", "？")
    title = title.replace('"', "″")
    title = title.replace('*', "＊")
    return title


# vposをdateとdate_usecから再計算する（commenomi対策）
def rewrite_vpos(start_date_unixtime, xml_line):
    vpos_start = xml_line.find(' vpos="')
    if vpos_start == -1:
        return xml_line
    # xml内のvposの値を取得
    vpos_pos = vpos_start + 7  # len(' vpos="')
    vpos_str_count = xml_line[vpos_pos:].find('"')
    # xml内dateの値の取得
    date_start = xml_line.find(' date="')
    date_num = xml_line[date_start + 7 : date_start + 17]
    # xml内date_usecの値の取得
    date_usec_start = xml_line.find(' date_usec="')
    if date_usec_start == -1:
        date_usec_num = "0"
    else:
        date_usec_str_count = xml_line[date_usec_start + 12 :].find('"')
        date_usec_num = xml_line[date_usec_start + 12 : date_usec_start + 12 + date_usec_str_count]
    # コメントのunixtimeから動画開始時のunixtime引いた値を新しいvposとする
    comment_unixtime = float(date_num + "." + date_usec_num)
    new_vpos = math.ceil((comment_unixtime - start_date_unixtime) * 100)
    return xml_line[:vpos_pos] + str(new_vpos) + xml_line[vpos_pos + vpos_str_count :]


def get_content_data(ip_addr, playing_content_id):
    item = get_item(ip_addr, playing_content_id)
    # print(item)
    # print(item['title'].encode('unicode-escape'))
    title = replace_title(item["title"])
    jkid = get_jkid(item["serviceId"])
    start_date_time = get_datetime(item["startDateTime"])
    total_minutes = round(int(item["duration"]) / 60)
    seconds = 60 - (int(item["duration"]) % 60)
    end_date_time = start_date_time + timedelta(minutes=total_minutes) + timedelta(seconds=seconds)
    # 引数指定で再生中動画の再生時間を上書き
    if fixlive:
        end_date_time = start_date_time + timedelta(seconds=(fixlive * 60)) + timedelta(seconds=14)
        total_minutes = fixlive
    if not jkid:
        base_file = (
            item["channelName"]
            + "_"
            + start_date_time.strftime("%Y%m%d_%H%M%S")
            + "_"
            + str(total_minutes)
            + "_"
            + title
        )
        logfile = os.path.join(kakolog_dir, f"{base_file}.xml")
        # ファイルが存在しない場合
        if not os.path.exists(logfile):
            p = pathlib.Path(logfile)
            p.touch()
            ret = bluesky_write(item["channelName"], start_date_time, total_minutes, title, 0)
            if not ret:
                logger.info(f"postに失敗しました。対象: {title}")
            logger.info(
                f'エラー：「{item["channelName"]}」は定義されていないチャンネルのため、空ファイルを作成します。'
            )
            logger.info(f"ファイル名:{base_file}.xml")

    return jkid, start_date_time, end_date_time, total_minutes, title


def get_kakolog_api(start_date_time, end_date_time, title, jkid, total_minutes, logfile):
    start_unixtime = start_date_time.timestamp()
    end_unixtime = end_date_time.timestamp()
    try:
        kakolog = requests.get(
            f"https://jikkyo.tsukumijima.net/api/kakolog/{jkid}?starttime={start_unixtime}&endtime={end_unixtime}&format=xml",
            headers=headers,
            # 過去ログAPIは長尺番組だと応答に時間がかかるため長めに待つ
            timeout=60,
        )
        kakolog.raise_for_status()  # status200 チェック
    except requests.exceptions.RequestException as e:

        logger.info("エラー：ニコニコ実況過去ログAPIのサイトから取得できません。", stack_info=True)
        return False

    start_date_unixtime = start_date_time.timestamp()
    lines = []
    line_count = 0
    for xml_line in kakolog.iter_lines():
        line = rewrite_vpos(start_date_unixtime, xml_line.decode())
        lines.append(line)
        if "</chat>" in line:
            line_count += 1
        if line == "<title>503 Service Unavailable</title>":
            logger.error("エラー：ニコニコ実況過去ログAPIのサイトから取得できません。 503 Service Unavailable")
            return False

    if line_count < 1:
        logger.info("エラー：指定された期間の過去ログは存在しません。")

    try:
        with open(logfile, "w", encoding="utf-8") as saveFile:
            saveFile.writelines(lines)

    except Exception as e:
        logger.info("エラー：過去ログの書き込みに失敗しました。", e)
        return False

    total_sec = int(end_unixtime - start_unixtime)
    if total_minutes > 0:
        min_count = format(line_count // total_minutes, ",")
    else:
        min_count = "0"
    logger.info(
        "再生時間:{}時{}分{}秒 総コメント数:{} 平均コメント数/分:{}".format(
            total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60, line_count, min_count
        )
    )

    ret = bluesky_write(ChannelList.jk_names[jkid], start_date_time, total_minutes, title, line_count)
    if not ret:
        logger.info(f"postに失敗しました。対象: {title}")

    return True


def bluesky_write(ch_name, start_date_time, total_minutes, title, line_count):
    """Bluesky へ視聴記録を投稿する（SPEC §2.2）。未設定なら何もしない"""
    if not bluesky_handle or not bluesky_app_password:
        return True

    # 投稿する内容を指定
    if total_minutes > 0:
        min_count = format(line_count // total_minutes, ",")
    else:
        min_count = "0"

    post_template_file = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/post_template.txt"
    if not os.path.exists(post_template_file):
        logger.info(f"エラー：投稿テンプレートファイルが見つかりません。{post_template_file}")
        return False
    """
    #nasne の録画を再生しました。
    ------------
    Ｄｏ　Ｉｔ　Ｙｏｕｒｓｅｌｆ！！＃１０[字]

    チャンネル: テレビ東京
    録画日時: 2022年12月07日 23時59分47秒
    長さ: 30分
    実況コメント数: 3,227 （毎分: 107コメント）
    #ニコニコ実況 #komenasne
    """
    with open(post_template_file, "r", encoding="utf-8") as f:
        message = f.read()
        message = start_date_time.strftime(message)
        message = message.format(
            title=title,
            ch_name=ch_name,
            total_minutes=total_minutes,
            line_count=format(line_count, ","),
            min_count=min_count,
        )

    # Bluesky へ投稿する（atproto は起動を軽くするため必要時にのみ import）
    try:
        from atproto import Client, client_utils

        client = Client()
        client.login(bluesky_handle, bluesky_app_password)
        # ハッシュタグをリンク付きで投稿する
        text = client_utils.TextBuilder()
        parts = re.split(r"(#\S+)", message)
        for part in parts:
            if part.startswith("#"):
                text.tag(part, part[1:])
            else:
                text.text(part)
        status = client.send_post(text)
    except Exception as e:
        print(f"エラー：Blueskyへの投稿に失敗しました。{e}")
        status = False
        try:
            err_log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "post_err.log")
            with open(err_log_path, "a", encoding="utf-8") as err_f:
                err_f.write(message + "\n\n--------------------------------------------------\n\n")
        except Exception as log_err:
            logger.info(f"エラー：投稿失敗ログの書き込みに失敗しました。{log_err}")
    # 投稿が成功したかどうかを返す
    return status


def launch_detached(cmd):
    """親プロセス（DOSプロンプト等）を閉じても生き残るように子プロセスを起動する（SPEC §2.1）"""
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        try:
            # Windows Terminal の「ウィンドウを閉じるとプロセスツリーごと終了」から脱出する
            subprocess.Popen(cmd, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB, close_fds=True)
        except OSError:
            # Job が breakaway を許可していない環境ではフラグを外してリトライ
            subprocess.Popen(cmd, creationflags=flags, close_fds=True)
    else:
        # macOS / Linux（開発用）
        subprocess.Popen(cmd, start_new_session=True)


def open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title):

    base_file = f'{ChannelList.jk_names[jkid]}_{start_date_time.strftime("%Y%m%d_%H%M%S")}_{total_minutes}_{title}'
    logfile = os.path.join(kakolog_dir, f"{base_file}.xml")

    # ファイルが存在しない場合
    if not os.path.exists(logfile):
        # 過去ログAPIから取得
        logger.info(f"ファイル名:{base_file}.xml")
        ret = get_kakolog_api(start_date_time, end_date_time, title, jkid, total_minutes, logfile)
        if not ret:
            return False
    else:
        if not mode_monitoring:
            print(f"ファイル名:{base_file}.xml")

    # mode_silentがFalseの時はコメントビュアーを起動
    if not mode_silent:
        # komeviewが存在するかどうかをチェック
        if player_path is None or not os.path.exists(player_path):
            logger.info(f"エラー：komeviewが見つからないため、終了します。{player_path}")
            sys.exit(1)

        launch_detached([player_path, logfile])
    return True


def open_jkcommentviewer(service_id):
    if mode_silent or jkcommentviewer_path is None:
        return True
    channels = {
        "jk1": "https://live.nicovideo.jp/watch/ch2646436",  # NHK総合
        "jk2": "https://live.nicovideo.jp/watch/ch2646437",  # NHK Eテレ
        "jk4": "https://live.nicovideo.jp/watch/ch2646438",  # 日本テレビ
        "jk5": "https://live.nicovideo.jp/watch/ch2646439",  # テレビ朝日
        "jk6": "https://live.nicovideo.jp/watch/ch2646440",  # TBSテレビ
        "jk7": "https://live.nicovideo.jp/watch/ch2646441",  # テレビ東京
        "jk8": "https://live.nicovideo.jp/watch/ch2646442",  # フジテレビ
        "jk9": "https://live.nicovideo.jp/watch/ch2646485",  # TOKYO MX
        "jk101": "https://live.nicovideo.jp/watch/ch2647992",  # NHK BS
        "jk211": "https://live.nicovideo.jp/watch/ch2646846",  # BS11
    }
    try:
        # ライブ視聴中のチャンネルを取得する
        jkid = get_jkid(service_id)
        print(f"jkcommentviewerで再生中のチャンネル {jkid} を開きます。")
        url = channels.get(jkid)
        if not url:
            url = f"https://nx-jikkyo.tsukumijima.net/watch/{jkid}"
    except:
        logger.info("エラー：ニコニコ実況番組が見つかりません。")
        return False
    # jkcommentviewerオープン
    if not os.path.exists(jkcommentviewer_path):
        logger.info(f"エラー：jkcommentviewer.exeが見つかりません。{jkcommentviewer_path}")
        return False
    else:
        launch_detached([jkcommentviewer_path, url])
    return True


def query_nasne_status(ip_addr):
    """1台の nasne の視聴状態を取得する。失敗時は None（電源オフ等）"""
    try:
        r = requests.get(f"http://{ip_addr}:64210/status/dtcpipClientListGet", timeout=NASNE_API_TIMEOUT)
        return json.loads(r.text)
    except (requests.exceptions.RequestException, ValueError):
        return None


def playing_nasnes():
    # 全 nasne に並列で問い合わせる（タイムアウト2秒。電源オフの個体がいても待たされない / SPEC §2.5）
    with ThreadPoolExecutor(max_workers=max(len(nasne_ips), 1)) as executor:
        statuses = list(executor.map(query_nasne_status, nasne_ips))

    if all(s is None for s in statuses):
        logger.info(f"エラー：NASNEが見つかりません。（照会先: {', '.join(nasne_ips)}）")
        if mode_monitoring:
            return
        else:
            sys.exit(1)  # 致命的エラー

    for ip_addr, playing_info in zip(nasne_ips, statuses):
        if playing_info is None:
            logger.info(f"エラー：{ip_addr} のNASNEが見つかりません。")
            continue
        try:
            is_rec_playing = playing_info["client"][0]["purpose"] == 2  # 1:ライブ視聴 2:録画視聴 3:ムーブ
            if is_rec_playing:
                playing_content_id = playing_info["client"][0]["content"]["id"]
                # 再生中の番組情報を取得する
                jkid, start_date_time, end_date_time, total_minutes, title = get_content_data(
                    ip_addr, playing_content_id
                )
                # 番組終了5分以内は過去ログを取得しない
                if datetime.timestamp(
                    end_date_time + timedelta(minutes=5)
                ) < datetime.timestamp((datetime.now())):
                    # komeview用のコメント再生処理
                    ret = open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title)
                    if not ret:
                        # 取得失敗の詳細は直前でログ出力済み。
                        # 「nasneの動画が見つからない」という紛らわしいメッセージを出さずに終える
                        if mode_monitoring:
                            return True  # 常駐モードは次の周期で再試行
                        sys.exit(1)
                    return True
                else:
                    if not mode_monitoring:
                        logger.info(f"番組終了から5分間は過去ログを取得できません。しばらく待ってから再実行してください。（{title}）")
                        sys.exit(1)
        except KeyError:
            pass

        try:
            # ライブ視聴中のチャンネルを取得する
            service_id = playing_info["client"][0]["liveInfo"]["serviceId"]
            # jkcommentviewerオープン
            ret = open_jkcommentviewer(service_id)
            if not ret:
                print("jkcommentviewerオープン失敗")
            return ret
        except KeyError:
            pass
    return False

# ───────────────────────────────────────────────
# Webプレイヤー / --serve モード（SPEC §5）
# ───────────────────────────────────────────────
def api_play_payload():
    """キックAPIの本体。再生中の録画の過去ログを取得して dict で返す。"""
    with ThreadPoolExecutor(max_workers=max(len(nasne_ips), 1)) as executor:
        statuses = list(executor.map(query_nasne_status, nasne_ips))

    if all(s is None for s in statuses):
        return {"error": f"nasneが見つかりません。（照会先: {', '.join(nasne_ips)}）"}

    live_found = False
    for ip_addr, playing_info in zip(nasne_ips, statuses):
        if playing_info is None:
            continue
        try:
            if playing_info["client"][0]["purpose"] == 2:  # 録画視聴
                playing_content_id = playing_info["client"][0]["content"]["id"]
                jkid, start_date_time, end_date_time, total_minutes, title = get_content_data(
                    ip_addr, playing_content_id
                )
                if not jkid:
                    return {"error": f"未対応チャンネルのため取得できません（{title}）"}
                if datetime.timestamp(end_date_time + timedelta(minutes=5)) >= datetime.timestamp(datetime.now()):
                    return {"error": "番組終了から5分間は過去ログを取得できません。しばらく待ってから再取得してください。"}

                base_file = (
                    f'{ChannelList.jk_names[jkid]}_{start_date_time.strftime("%Y%m%d_%H%M%S")}_{total_minutes}_{title}'
                )
                logfile = os.path.join(kakolog_dir, f"{base_file}.xml")
                if not os.path.exists(logfile):
                    ret = get_kakolog_api(start_date_time, end_date_time, title, jkid, total_minutes, logfile)
                    if not ret:
                        return {"error": "ニコニコ実況過去ログAPIから取得できませんでした。"}
                with open(logfile, "r", encoding="utf-8") as f:
                    xml = f.read()
                return {"title": base_file, "filename": f"{base_file}.xml", "xml": xml}
        except KeyError:
            pass
        try:
            playing_info["client"][0]["liveInfo"]["serviceId"]
            live_found = True
        except KeyError:
            pass

    if live_found:
        return {"error": "ライブ視聴中です。Webプレイヤーは録画再生のみ対応しています。"}
    return {"error": "再生中の録画が見つかりません。nasneで録画を再生してから「取得」を押してください。"}


def run_server(port):
    """Webプレイヤーの配信とキックAPI（標準ライブラリのみ / SPEC §5.1）"""
    import http.server
    from urllib.parse import urlparse

    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    web_dir = None
    for cand in (os.path.join(app_dir, "web"), os.path.join(app_dir, "..", "web")):
        if os.path.isdir(cand):
            web_dir = os.path.abspath(cand)
            break
    if web_dir is None:
        logger.info("エラー：web フォルダが見つかりません。")
        sys.exit(1)

    class KomeHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=web_dir, **kw)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/play":
                try:
                    payload = api_play_payload()
                except Exception as e:  # 想定外エラーでもサーバは落とさない
                    payload = {"error": f"サーバ内部エラー: {e}"}
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()

        def log_message(self, format, *args):
            pass  # アクセスログは出さない

    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), KomeHandler)
    print(f"Webプレイヤーを起動しました: http://localhost:{port}/")
    print("iPad等からは Tailscale のこのPCのアドレス:ポートでアクセスしてください。Ctrl+C で終了します。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n終了します。")


def get_rec_list(ip_addr):
    """録画済みリストを、再生時に生成されるXMLファイル名と同じ形式で返す（--reclist 用）"""
    results = []
    for item in get_title_list(ip_addr):
        title = replace_title(item["title"])
        jkid = get_jkid(item["serviceId"])
        # jk_names に無いチャンネルは nasne が持つチャンネル名にフォールバック
        ch_name = (ChannelList.jk_names.get(jkid) if jkid else None) or item.get(
            "channelName", str(item.get("serviceId"))
        )
        start_date_time = get_datetime(item["startDateTime"])
        total_minutes = round(int(item["duration"]) / 60)
        results.append(f'{ch_name}_{start_date_time.strftime("%Y%m%d_%H%M%S")}_{total_minutes}_{title}.xml')
    return results


def get_rec_ng_list(ip_addr):
    r = requests.get(f"http://{ip_addr}:64210/status/recNgListGet", timeout=3)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("item", []):
        service_id = item.get("scheduledChannelID")
        title = replace_title(item.get("title", "タイトル不明"))
        total_minutes = item.get("scheduledDuration", 0) // 60

        start_dt = parse(item["scheduledStartDateTime"]).astimezone(JST)
        start_dt = start_dt - timedelta(seconds=15)
        start_str = start_dt.strftime("%Y%m%d_%H%M%S")

        jkid = get_jkid(service_id)
        ch_name = ChannelList.jk_names.get(jkid) if jkid else str(service_id)

        results.append(f"{ch_name}_{start_str}_{total_minutes}_{title}.xml")

    return results

# init
logger = get_logger()


ini_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "komenasne.ini")
ini = configparser.ConfigParser(interpolation=None)
ini.read(ini_path, "UTF-8")

# ini の ip（IPv4 らしい表記だけを採用）。未設定なら初回起動時に自動発見して ini に書き込む（SPEC §2.4）
try:
    _ip_raw = ini["NASNE"]["ip"]
except KeyError:
    _ip_raw = ""
manual_ips = [x.strip() for x in _ip_raw.split(",") if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", x.strip())]
nasne_ips = []  # 実際の解決は引数パース後（--discover / 初回探索を考慮）

headers = {"user-agent": "komenasne"}

# iniファイル読み込み（komeview_path 優先。旧キー commenomi_path も互換で読む / SPEC §2.1）
try:
    player_path = Path(ini["PLAYER"]["komeview_path"])
except KeyError:
    try:
        player_path = Path(ini["PLAYER"]["commenomi_path"])
    except KeyError:
        player_path = None

try:
    kakolog_dir = Path(ini["LOG"]["kakolog_dir"])
    if not kakolog_dir.is_absolute():
        # 相対パスの時は exe/スクリプトのある場所を基準にする
        kakolog_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), kakolog_dir)

    # フォルダが無ければ作成する
    os.makedirs(kakolog_dir, exist_ok=True)

except KeyError:
    logger.info("iniファイルにkakolog_dirを設定してください")
    sys.exit(1)

try:
    jkcommentviewer_path = ini["PLAYER"]["jkcommentviewer_path"]
except KeyError:
    jkcommentviewer_path = None

# Bluesky 投稿設定（未設定なら投稿しない / SPEC §2.2）
try:
    bluesky_handle = ini["BLUESKY"]["handle"].strip()
except KeyError:
    bluesky_handle = ""
try:
    bluesky_app_password = ini["BLUESKY"]["app_password"].strip()
except KeyError:
    bluesky_app_password = ""

# ヘルプ表示
usage_message = """直接取得モード: komenasne.exe [channel] [yyyy-mm-dd HH:MM] [total_minutes] option:[title]
例1: komenasne.exe "jk181" "2021-01-24 26:00" 30
例2: komenasne.exe "BSフジ" "2021/1/24 26:00" 30 "＜アニメギルド＞ゲキドル　＃３"
例3: komenasne.exe "BSフジ" 20210125_015945 30 "＜アニメギルド＞ゲキドル　＃３"

サイレントモード: komenasne.exe --mode_silent
常駐モード: komenasne.exe --mode_monitoring
再生中の番組時間を強制上書き: komenasne.exe --fixlive 30
ファイル名から時間変更で再取得: komenasne.exe --fixrec 30 "TOKYO MX_20230210_001202_30_お兄ちゃんはおしまい！ ＃６.xml"
nasneの再探索（IPが変わった時に実行）: komenasne.exe --discover
録画失敗リストの表示: komenasne.exe --recerror [絞り込みキーワード]
録画済みリストをreclist.txtに書き出し: komenasne.exe --reclist [絞り込みキーワード]
Webプレイヤーサーバを起動（iPad等のブラウザ用）: komenasne.exe --serve [ポート番号(省略時8765)]

チャンネルリスト: NHK Eテレ 日テレ テレ朝 TBS テレ東 フジ MX BSフジ BS11または以下のjk**を指定
"""
for k, v in ChannelList.jk_names.items():
    usage_message += f"{k} {v}\n"

# パーサーのインスタンスを作成
parser = argparse.ArgumentParser(usage=usage_message)

parser.add_argument("channel", nargs="?", default="None")
parser.add_argument("date_time", nargs="?", default=0)
parser.add_argument("total_minutes", type=int, nargs="?", default=0)
parser.add_argument("title", nargs="?", default="タイトル不明")
parser.add_argument("--discover", action="store_true")  # nasneを再探索してiniを更新
parser.add_argument("--serve", type=int, nargs="?", const=8765, default=None)  # Webプレイヤーサーバ起動
parser.add_argument("--mode_silent", action="store_true")
parser.add_argument("--mode_monitoring", action="store_true")
parser.add_argument("--fixrec", nargs=2)
parser.add_argument("--fixlive", type=int)  # 再生中動画の再生時間を上書き.分を指定する
parser.add_argument("--recerror", nargs="?", const=True, default=False)
parser.add_argument("--reclist", nargs="?", const=True, default=False)  # 録画済みリストをtxtに書き出し

# 引数を解析する
args = parser.parse_args()

# サイレントモード判断（コメントビュアーは起動せずxmlファイルを作成するだけ）
if args.mode_silent:
    mode_silent = True
else:
    mode_silent = False

# 常駐監視モード判断（プログラムを終了せず定期実行する）
if args.mode_monitoring:
    mode_monitoring = True
    mode_silent = True
else:
    mode_monitoring = False

if args.fixlive:
    fixlive = args.fixlive
else:
    fixlive = None


if not mode_silent:
    logger.info("starting..")

# ───────────────────────────────────────────────
# nasne の IP 解決（SPEC §2.4）
#   ini の ip を使用。未設定なら探索して ini に書き込む（初回起動）
#   探索(SSDP)を行うのは --discover 指定時と、初回起動時のみ
# ───────────────────────────────────────────────
direct_mode = args.channel != "None" or bool(args.fixrec)

if args.discover:
    print("nasne を探索しています…（数秒かかります）")
    found = discover_nasnes()
    if not found:
        print("nasne が見つかりませんでした。同じネットワークにいるか、ファイアウォールの設定を確認してください。")
        sys.exit(1)
    for ip, name in found:
        print(f"  {name}: {ip}")
    if update_ini_ips(ini_path, [ip for ip, _ in found]):
        print(f"{len(found)}台の nasne を komenasne.ini に反映しました。")
    else:
        print(f"エラー：komenasne.ini への書き込みに失敗しました。{ini_path}")
        sys.exit(1)
    sys.exit(0)

if not direct_mode:
    if manual_ips:
        nasne_ips = manual_ips
    else:
        # 初回起動（ini の ip が未設定）: 自動探索して ini に反映
        print("nasne のIPが未設定のため探索しています…（数秒かかります）")
        found = discover_nasnes()
        if not found:
            logger.info(
                "エラー：nasne が見つかりません。komenasne.ini の ip を設定するか、--discover を実行してください。"
            )
            sys.exit(1)
        nasne_ips = [ip for ip, _ in found]
        if update_ini_ips(ini_path, nasne_ips):
            print("発見: " + ", ".join(f"{name}={ip}" for ip, name in found) + " → komenasne.ini に反映しました。")
        else:
            logger.info(f"エラー：komenasne.ini への書き込みに失敗しました。{ini_path}")

# Webプレイヤーサーバ（SPEC §5）
if args.serve:
    run_server(args.serve)
    sys.exit(0)

# 録画失敗リスト
if args.recerror:
    keyword = args.recerror if isinstance(args.recerror, str) else None
    for ip in nasne_ips:
        try:
            ng_list = get_rec_ng_list(ip)
            if keyword:
                ng_list = [f for f in ng_list if keyword in f]
            if ng_list:
                for filename in ng_list:
                    print(filename)
            else:
                print("録画失敗はありません。")
        except Exception as e:
            logger.info(f"エラー：{ip} の録画失敗リスト取得に失敗しました。{e}")
    sys.exit(0)

# 録画済みリストを reclist.txt に書き出し
if args.reclist:
    keyword = args.reclist if isinstance(args.reclist, str) else None

    def _safe_rec_list(ip):
        try:
            return get_rec_list(ip)
        except Exception as e:
            logger.info(f"エラー：{ip} の録画リスト取得に失敗しました。{e}")
            return []

    # 全 nasne から並列で取得
    with ThreadPoolExecutor(max_workers=max(len(nasne_ips), 1)) as executor:
        rec_lists = list(executor.map(_safe_rec_list, nasne_ips))
    lines = [f for sub in rec_lists for f in sub]
    if keyword:
        lines = [f for f in lines if keyword in f]

    # 重複を除き、録画日時順に並べる
    def _sort_key(f):
        m = re.search(r"_(\d{8}_\d{6})_", f)
        return m.group(1) if m else f

    lines = sorted(set(lines), key=_sort_key)

    out_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "reclist.txt")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
    except OSError as e:
        print(f"エラー：reclist.txt の書き込みに失敗しました。{e}")
        sys.exit(1)
    print(f"{len(lines)}件を書き出しました: {out_path}")
    sys.exit(0)

# 直接取得モード
if args.channel != "None" or args.fixrec:
    if args.fixrec:
        # NHK総合_20230128_201445_35_有吉のお金発見 突撃！カネオくん「スター動物がいっぱい！動物園のお金の秘密」[字].xml
        # これを要素に分解
        fixrec_file = os.path.splitext(os.path.basename(args.fixrec[1]))[0]
        m = re.search(r"^(.+)_(\d{8}_\d{6})_\d+_(.+)", fixrec_file)
        if m is None:
            print("エラー：ファイル名が誤っています。拡張子xmlのファイル名を指定してください。")
            sys.exit(1)
        jkid = m.group(1)
        str_date_time = m.group(2)
        title = m.group(3)
        total_minutes = int(args.fixrec[0])
    else:
        jkid = args.channel  # 'jk4' または NHK Eテレ 日テレ テレ朝 TBS テレ東 フジ MX BS11
        str_date_time = args.date_time
        total_minutes = args.total_minutes  # 60
        title = args.title  # "有吉の壁▼サバゲー場で爆笑ネタ！見取り図＆吉住参戦▼カーベーイーツ！チョコ新技[字]"
    title = title.replace("?", "？")
    title = title.replace("〜", "～")
    # しょぼいカレンダーのチャンネル名も対応
    short_jkids = {
        "NHK": 1,
        "NHK総合": 1,
        "Eテレ": 2,
        "NHK Eテレ": 2,
        "日テレ": 4,
        "日本テレビ": 4,
        "テレ朝": 5,
        "テレビ朝日": 5,
        "TBS": 6,
        "TBSテレビ": 6,
        "テレ東": 7,
        "テレビ東京": 7,
        "フジ": 8,
        "フジテレビ": 8,
        "MX": 9,
        "TOKYO MX": 9,
        "NHK-BS1": 101,
        "NHK BS1": 101,
        "NHK BSプレミアム": 103,
        "BS日テレ": 141,
        "BS朝日": 151,
        "BS-TBS": 161,
        "BSテレ東": 171,
        "BSフジ": 181,
        "BS11": 211,
        "BS11イレブン": 211,
        "BS12": 222,
        "BS12トゥエルビ": 222,
    }
    if jkid in short_jkids:
        # 主要なチャンネルは短縮名でも指定できるように
        jkid = "jk" + str(short_jkids[jkid])
    if jkid not in ChannelList.jk_names:
        logger.info("エラー：「" + args.channel + "」は定義されていないチャンネルのため、連携できません。")
        sys.exit(1)

    m = re.search(r"^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$", str_date_time)
    if m:
        start_at = "{}-{}-{} {}:{}:{}".format(
            m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
        )  # "2021-01-27 19:00"
        start_date_time = parse(start_at)
    else:
        start_at = args.date_time  # "2021-01-27 19:00"
        start_date, start_time = start_at.split(" ")
        start_hour, start_min = start_time.split(":")
        # しょぼいカレンダーの25:00等表記の対応
        if int(start_hour) >= 24:
            start_hour = int(start_hour) - 24
            plus_days = 1
        else:
            plus_days = 0
        start_at = start_date + " " + str(start_hour) + ":" + start_min
        start_date_time = parse(start_at) - timedelta(seconds=15) + timedelta(days=plus_days)

    if total_minutes >= 600:
        logger.info("エラー：600分以上は指定できません。")
        sys.exit(1)
    end_date_time = start_date_time + timedelta(minutes=total_minutes) + timedelta(seconds=14)
    # commenomi用のコメント再生処理
    open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title)
    sys.exit(0)


def main():
    if mode_monitoring:
        # 常駐監視モード
        print("常駐監視モード開始 " + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))
        while True:
            playing_nasnes()
            time.sleep(60)
    else:
        # 通常実行
        ret = playing_nasnes()
        if not ret:
            if not mode_silent:
                logger.info("エラー：再生中のnasneの動画が見つからないため、終了します。")
            sys.exit(1)


if __name__ == "__main__":
    main()
