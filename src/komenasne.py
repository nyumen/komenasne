# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta
from dateutil.parser import parse
from urllib.parse import quote
import re
import gc
import subprocess
import configparser
import os
import sys
import time
import math
from logging import getLogger, StreamHandler, Formatter, FileHandler, INFO
import tweepy
import argparse
import pathlib
import pytz
from pathlib import Path

# from nx_kako_log import NxKakoLog

# タイムゾーンの設定
JST = pytz.timezone("Asia/Tokyo")


"""
# 必要
pip install requests
pip install python-dateutil 
pip install tweepy
iniの設定
"""


from common.channel_list import ChannelList


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
    get_title_lists = requests.get(
        f"http://{ip_addr}:64220/recorded/titleListGet?searchCriteria=0&filter=0&startingIndex=0&requestedCount=0&sortCriteria=0&withDescriptionLong=0&withUserData=0"
    )
    title_lists = json.loads(get_title_lists.text)

    for item in title_lists["item"]:
        if item["id"] == playing_content_id:
            return item


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
            ret = twitter_write(item["channelName"], start_date_time, total_minutes, title, 0)
            if not ret:
                logger.info(f"tweetに失敗しました。対象: {title}")
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
            timeout=15,
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

    # メモリ解放
    del kakolog
    gc.collect()

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

    ret = twitter_write(ChannelList.jk_names[jkid], start_date_time, total_minutes, title, line_count)
    if not ret:
        logger.info(f"postに失敗しました。対象: {title}")

    return True


def twitter_write(ch_name, start_date_time, total_minutes, title, line_count):
    if consumer_key == "" or consumer_secret == "" or access_token == "" or access_token_secret == "":
        return True
    # Twitter APIを使用するための準備
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

    # ツイートする内容を指定
    if total_minutes > 0:
        min_count = format(line_count // total_minutes, ",")
    else:
        min_count = "0"

    tweet_template_file = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/tweet_template.txt"
    if not os.path.exists(tweet_template_file):
        logger.info(f"エラー：ツイートテンプレートファイルが見つかりません。{tweet_template_file}")
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
    with open(tweet_template_file, "r", encoding="utf-8") as f:
        message = f.read()
        message = start_date_time.strftime(message)
        message = message.format(
            title=title,
            ch_name=ch_name,
            total_minutes=total_minutes,
            line_count=format(line_count, ","),
            min_count=min_count,
        )

    # ツイートする
    try:
        status = client.create_tweet(text=message)
    except Exception as e:
        print(f"エラー：ツイートに失敗しました。{e.args[0]}")
        status = False
        try:
            err_log_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "post_err.log")
            with open(err_log_path, "a", encoding="utf-8") as err_f:
                err_f.write(message + "\n\n--------------------------------------------------\n\n")
        except Exception as log_err:
            logger.info(f"エラー：投稿失敗ログの書き込みに失敗しました。{log_err}")
        pass
    # ツイートが成功したかどうかを返す
    return status


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
        # commenomiが存在するかどうかをチェック
        if not os.path.exists(commenomi_path):
            logger.info(f"エラー：commenomiが見つからないため、終了します。{commenomi_path}")
            sys.exit(1)

        subprocess.Popen([commenomi_path, logfile])
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
        subprocess.Popen([jkcommentviewer_path, url])
    return True


def playing_nasnes():
    for ip_addr in nasne_ips:
        try:
            get_playing_info = requests.get(f"http://{ip_addr}:64210/status/dtcpipClientListGet")
        except:
            logger.info(f"エラー：{ip_addr} のNASNEが見つかりません。")
            if mode_monitoring:
                return
            else:
                sys.exit(1)  # 致命的エラー
        playing_info = json.loads(get_playing_info.text)
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
                    # commenomi用のコメント再生処理
                    ret = open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title)
                    return ret
                else:
                    pass
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


ini = configparser.ConfigParser(interpolation=None)
ini.read(os.path.dirname(os.path.abspath(sys.argv[0])) + "/komenasne.ini", "UTF-8")
nase_ini = ini["NASNE"]["ip"]
nasne_ips = [x.strip() for x in nase_ini.split(",")]

headers = {"user-agent": "komenasne"}

# iniファイル読み込み
try:
    commenomi_path = Path(ini["PLAYER"]["commenomi_path"])
except KeyError:
    commenomi_path = None

try:
    kakolog_dir = Path(ini["LOG"]["kakolog_dir"])
    if not Path(kakolog_dir).is_absolute():
        # 相対パスの時
        kakolog_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), kakolog_dir)

    # フォルダが存在するかどうかをチェック
    if not os.path.exists(kakolog_dir):
        logger.info(f"エラー：ログフォルダが見つからないため、終了します。{kakolog_dir}")
        exit(1)

except KeyError:
    logger.info(f"iniファイルにkakolog_dirを設定してください")
    exit(1)

try:
    jkcommentviewer_path = ini["PLAYER"]["jkcommentviewer_path"]
except KeyError:
    jkcommentviewer_path = None

# Twitter APIを使用するためのキーを指定
try:
    consumer_key = ini["TWITTER"]["consumer_key"]
except KeyError:
    consumer_key = ""
try:
    consumer_secret = ini["TWITTER"]["consumer_secret"]
except KeyError:
    consumer_secret = ""
try:
    access_token = ini["TWITTER"]["access_token"]
except KeyError:
    access_token = ""
try:
    access_token_secret = ini["TWITTER"]["access_token_secret"]
except KeyError:
    access_token_secret = ""

# ヘルプ表示
usage_message = """直接取得モード: komenasne.exe [channel] [yyyy-mm-dd HH:MM] [total_minutes] option:[title]
例1: komenasne.exe "jk181" "2021-01-24 26:00" 30
例2: komenasne.exe "BSフジ" "2021/1/24 26:00" 30 "＜アニメギルド＞ゲキドル　＃３"
例3: komenasne.exe "BSフジ" 20210125_015945 30 "＜アニメギルド＞ゲキドル　＃３"

サイレントモード: komenasne.exe --mode_silent
常駐モード: komenasne.exe --mode_monitoring
再生中の番組時間を強制上書き: komenasne.exe --fixlive 30
ファイル名から時間変更で再取得: komenasne.exe --fixrec 30 "TOKYO MX_20230210_001202_30_お兄ちゃんはおしまい！ ＃６.xml"

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
parser.add_argument("-limit", choices=["none", "high", "middle", "low"])
parser.add_argument("--mode_silent", action="store_true")
parser.add_argument("--mode_monitoring", action="store_true")
parser.add_argument("--fixrec", nargs=2)
parser.add_argument("--fixlive", type=int)  # 再生中動画の再生時間を上書き.分を指定する
parser.add_argument("--recerror", nargs="?", const=True, default=False)

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
