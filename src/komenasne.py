# -*- coding: utf-8 -*-
import requests
import json
import datetime
from dateutil.parser import parse
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import gc
import subprocess
import configparser
import platform
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
pip install beautifulsoup4
pip install python-dateutil 
pip install tweepy
iniの設定
"""

jk_chs = {
    "jk1": (
        1024,
        1025,  # 関東広域: NHK総合・東京
        10240,  # 北海道(札幌): NHK総合・札幌
        11264,  # 北海道(函館): NHK総合・函館
        12288,  # 北海道(旭川): NHK総合・旭川
        13312,  # 北海道(帯広): NHK総合・帯広
        14336,  # 北海道(釧路): NHK総合・釧路
        15360,  # 北海道(北見): NHK総合・北見
        16384,  # 北海道(室蘭): NHK総合・室蘭
        17408,  # 宮城: NHK総合・仙台
        18432,  # 秋田: NHK総合・秋田
        19456,  # 山形: NHK総合・山形
        20480,  # 岩手: NHK総合・盛岡
        21504,  # 福島: NHK総合・福島
        22528,  # 青森: NHK総合・青森
        25600,  # 群馬: NHK総合・前橋
        26624,  # 茨城: NHK総合・水戸
        28672,  # 栃木: NHK総合・宇都宮
        30720,  # 長野: NHK総合・長野
        31744,  # 新潟: NHK総合・新潟
        32768,  # 山梨: NHK総合・甲府
        33792,  # 愛知: NHK総合・名古屋
        34816,  # 石川: NHK総合・金沢
        35840,  # 静岡: NHK総合・静岡
        36864,  # 福井: NHK総合・福井
        37888,  # 富山: NHK総合・富山
        38912,  # 三重: NHK総合・津
        39936,  # 岐阜: NHK総合・岐阜
        40960,  # 大阪: NHK総合・大阪
        41984,  # 京都: NHK総合・京都
        43008,  # 兵庫: NHK総合・神戸
        44032,  # 和歌山: NHK総合・和歌山
        45056,  # 奈良: NHK総合・奈良
        46080,  # 滋賀: NHK総合・大津
        47104,  # 広島: NHK総合・広島
        48128,  # 岡山: NHK総合・岡山
        49152,  # 島根: NHK総合・松江
        50176,  # 鳥取: NHK総合・鳥取
        51200,  # 山口: NHK総合・山口
        52224,  # 愛媛: NHK総合・松山
        53248,  # 香川: NHK総合・高松
        54272,  # 徳島: NHK総合・徳島
        55296,  # 高知: NHK総合・高知
        56320,  # 福岡: NHK総合・福岡
        56832,  # 福岡: NHK総合・北九州
        57344,  # 熊本: NHK総合・熊本
        58368,  # 長崎: NHK総合・長崎
        59392,  # 鹿児島: NHK総合・鹿児島
        60416,  # 宮崎: NHK総合・宮崎
        61440,  # 大分: NHK総合・大分
        62464,  # 佐賀: NHK総合・佐賀
        63488,  # 沖縄: NHK総合・沖縄
    ),
    "jk2": (
        1032,
        1033,
        1034,  # 関東広域: NHK-Eテレ
        2056,  # 近畿広域: NHKEテレ大阪
        3080,  # 中京広域: NHKEテレ名古屋
        10248,  # 北海道(札幌): NHKEテレ札幌
        11272,  # 北海道(函館): NHKEテレ函館
        12296,  # 北海道(旭川): NHKEテレ旭川
        13320,  # 北海道(帯広): NHKEテレ帯広
        14344,  # 北海道(釧路): NHKEテレ釧路
        15368,  # 北海道(北見): NHKEテレ北見
        16392,  # 北海道(室蘭): NHKEテレ室蘭
        17416,  # 宮城: NHKEテレ仙台
        18440,  # 秋田: NHKEテレ秋田
        19464,  # 山形: NHKEテレ山形
        20488,  # 岩手: NHKEテレ盛岡
        21512,  # 福島: NHKEテレ福島
        22536,  # 青森: NHKEテレ青森
        30728,  # 長野: NHKEテレ長野
        31752,  # 新潟: NHKEテレ新潟
        32776,  # 山梨: NHKEテレ甲府
        34824,  # 石川: NHKEテレ金沢
        35848,  # 静岡: NHKEテレ静岡
        36872,  # 福井: NHKEテレ福井
        37896,  # 富山: NHKEテレ富山
        47112,  # 広島: NHKEテレ広島
        48136,  # 岡山: NHKEテレ岡山
        49160,  # 島根: NHKEテレ松江
        50184,  # 鳥取: NHKEテレ鳥取
        51208,  # 山口: NHKEテレ山口
        52232,  # 愛媛: NHKEテレ松山
        53256,  # 香川: NHKEテレ高松
        54280,  # 徳島: NHKEテレ徳島
        55304,  # 高知: NHKEテレ高知
        56328,  # 福岡: NHKEテレ福岡
        56840,  # 福岡: NHKEテレ北九州
        57352,  # 熊本: NHKEテレ熊本
        58376,  # 長崎: NHKEテレ長崎
        59400,  # 鹿児島: NHKEテレ鹿児島
        60424,  # 宮崎: NHKEテレ宮崎
        61448,  # 大分: NHKEテレ大分
        62472,  # 佐賀: NHKEテレ佐賀
        63496,  # 沖縄: NHKEテレ沖縄
    ),
    "jk4": (
        1040,
        1041,  # 関東広域: 日テレ
        2088,  # 近畿広域: 読売テレビ
        3112,  # 中京広域: 中京テレビ
        4120,  # 北海道域: STV札幌テレビ
        5136,  # 岡山香川: RNC西日本テレビ
        6176,  # 島根鳥取: 日本海テレビ
        10264,  # 北海道(札幌): STV札幌
        11288,  # 北海道(函館): STV函館
        12312,  # 北海道(旭川): STV旭川
        13336,  # 北海道(帯広): STV帯広
        14360,  # 北海道(釧路): STV釧路
        15384,  # 北海道(北見): STV北見
        16408,  # 北海道(室蘭): STV室蘭
        17440,  # 宮城: ミヤギテレビ
        18448,  # 秋田: ABS秋田放送
        19472,  # 山形: YBC山形放送
        20504,  # 岩手: テレビ岩手
        21528,  # 福島: 福島中央テレビ
        22544,  # 青森: RAB青森放送
        30736,  # 長野: テレビ信州
        31776,  # 新潟: TeNYテレビ新潟
        32784,  # 山梨: YBS山梨放送
        34832,  # 石川: テレビ金沢
        35872,  # 静岡: だいいちテレビ
        36880,  # 福井: FBCテレビ
        37904,  # 富山: KNB北日本放送
        47128,  # 広島: 広島テレビ
        51216,  # 山口: KRY山口放送
        52240,  # 愛媛: 南海放送
        54288,  # 徳島: 四国放送
        55312,  # 高知: 高知放送
        56352,  # 福岡: FBS福岡放送
        57376,  # 熊本: KKTくまもと県民
        58408,  # 長崎: NIB長崎国際テレビ
        59432,  # 鹿児島: KYT鹿児島読売TV
        61464,  # 大分: TOSテレビ大分
    ),
    "jk5": (
        1064,
        1065,
        1066,  # 関東広域: テレビ朝日
        2072,  # 近畿広域: ABCテレビ
        3104,  # 中京広域: メ～テレ
        4128,  # 北海道域: HTB北海道テレビ
        5144,  # 岡山香川: KSB瀬戸内海放送
        10272,  # 北海道(札幌): HTB札幌
        11296,  # 北海道(函館): HTB函館
        12320,  # 北海道(旭川): HTB旭川
        13344,  # 北海道(帯広): HTB帯広
        14368,  # 北海道(釧路): HTB釧路
        15392,  # 北海道(北見): HTB北見
        16416,  # 北海道(室蘭): HTB室蘭
        17448,  # 宮城: KHB東日本放送
        18464,  # 秋田: AAB秋田朝日放送
        19480,  # 山形: YTS山形テレビ
        20520,  # 岩手: 岩手朝日テレビ
        21536,  # 福島: KFB福島放送
        22560,  # 青森: 青森朝日放送
        30744,  # 長野: abn長野朝日放送
        31784,  # 新潟: 新潟テレビ21
        34840,  # 石川: 北陸朝日放送
        35880,  # 静岡: 静岡朝日テレビ
        47136,  # 広島: 広島ホームテレビ
        51232,  # 山口: yab山口朝日
        52248,  # 愛媛: 愛媛朝日
        56336,  # 福岡: KBC九州朝日放送
        57384,  # 熊本: KAB熊本朝日放送
        58400,  # 長崎: NCC長崎文化放送
        59424,  # 鹿児島: KKB鹿児島放送
        61472,  # 大分: OAB大分朝日放送
        63520,  # 沖縄: QAB琉球朝日放送
    ),
    "jk6": (
        1048,
        1049,  # 関東広域: TBS
        2064,  # 近畿広域: MBS毎日放送
        3096,  # 中京広域: CBC
        4112,  # 北海道域: HBC北海道放送
        5152,  # 岡山香川: RSKテレビ
        6168,  # 島根鳥取: BSSテレビ
        10256,  # 北海道(札幌): HBC札幌
        11280,  # 北海道(函館): HBC函館
        12304,  # 北海道(旭川): HBC旭川
        13328,  # 北海道(帯広): HBC帯広
        14352,  # 北海道(釧路): HBC釧路
        15376,  # 北海道(北見): HBC北見
        16400,  # 北海道(室蘭): HBC室蘭
        17424,  # 宮城: TBCテレビ
        19488,  # 山形: テレビユー山形
        20496,  # 岩手: IBCテレビ
        21544,  # 福島: テレビユー福島
        22552,  # 青森: ATV青森テレビ
        30752,  # 長野: SBC信越放送
        31760,  # 新潟: BSN
        32792,  # 山梨: UTY
        34848,  # 石川: MRO
        35856,  # 静岡: SBS
        37920,  # 富山: チューリップテレビ
        47120,  # 広島: RCCテレビ
        51224,  # 山口: tysテレビ山口
        52256,  # 愛媛: あいテレビ
        55320,  # 高知: テレビ高知
        56344,  # 福岡: RKB毎日放送
        57360,  # 熊本: RKK熊本放送
        58384,  # 長崎: NBC長崎放送
        59408,  # 鹿児島: MBC南日本放送
        60432,  # 宮崎: MRT宮崎放送
        61456,  # 大分: OBS大分放送
        63504,  # 沖縄: RBCテレビ
    ),
    "jk7": (
        1072,
        1073,
        1074,  # 関東広域: テレビ東京
        4144,  # 北海道域: TVH
        5160,  # 岡山香川: TSCテレビせとうち
        10288,  # 北海道(札幌): TVH札幌
        11312,  # 北海道(函館): TVH函館
        12336,  # 北海道(旭川): TVH旭川
        13360,  # 北海道(帯広): TVH帯広
        14384,  # 北海道(釧路): TVH釧路
        15408,  # 北海道(北見): TVH北見
        16432,  # 北海道(室蘭): TVH室蘭
        33840,  # 愛知: テレビ愛知
        41008,  # 大阪: テレビ大阪
        56360,  # 福岡: TVQ九州放送
    ),
    "jk8": (
        1056,
        1057,
        1058,  # 関東広域: フジテレビ
        2080,  # 近畿広域: 関西テレビ
        3088,  # 中京広域: 東海テレビ
        4136,  # 北海道域: UHB
        5168,  # 岡山香川: OHKテレビ
        6160,  # 島根鳥取: 山陰中央テレビ
        10280,  # 北海道(札幌): UHB札幌
        11304,  # 北海道(函館): UHB函館
        12328,  # 北海道(旭川): UHB旭川
        13352,  # 北海道(帯広): UHB帯広
        14376,  # 北海道(釧路): UHB釧路
        15400,  # 北海道(北見): UHB北見
        16424,  # 北海道(室蘭): UHB室蘭
        17432,  # 宮城: 仙台放送
        18456,  # 秋田: AKT秋田テレビ
        19496,  # 山形: さくらんぼテレビ
        20512,  # 岩手: めんこいテレビ
        21520,  # 福島: 福島テレビ
        30760,  # 長野: NBS長野放送
        31768,  # 新潟: NST
        34856,  # 石川: 石川テレビ
        35864,  # 静岡: テレビ静岡
        36888,  # 福井: 福井テレビ
        37912,  # 富山: BBT富山テレビ
        47144,  # 広島: TSS
        52264,  # 愛媛: テレビ愛媛
        55328,  # 高知: さんさんテレビ
        56368,  # 福岡: TNCテレビ西日本
        57368,  # 熊本: TKUテレビ熊本
        58392,  # 長崎: KTNテレビ長崎
        59416,  # 鹿児島: KTS鹿児島テレビ
        60440,  # 宮崎: UMKテレビ宮崎
        62480,  # 佐賀: STSサガテレビ
        63544,  # 沖縄: 沖縄テレビ(OTV)
    ),
    "jk9": (
        23608,  # 東京: TOKYO MX1
        23609,  # 東京: TOKYO MX2
        23615,  # 東京: TOKYO MX臨時
    ),
    "jk10": (
        29752,
        29753,
        29754,  # 埼玉: テレ玉
    ),
    "jk11": (24632,),  # 神奈川: tvk
    "jk12": (27704,),  # 千葉: チバテレビ
    "jk101": (
        101,
        102,  # NHK BS1
    ),
    "jk103": (
        103,
        104,  # NHK BSプレミアム
    ),
    "jk141": (
        141,
        142,
        143,  # BS日テレ
    ),
    "jk151": (
        151,
        152,
        153,  # BS朝日
    ),
    "jk161": (
        161,
        162,
        163,  # BS-TBS
    ),
    "jk171": (
        171,
        172,
        173,  # BSテレ東
    ),
    "jk181": (
        181,
        182,
        183,  # BSフジ
    ),
    "jk191": (191,),  # WOWOWプライム
    "jk211": (211,),  # BS11
    "jk222": (222,),  # BS12
    "jk236": (236,),  # BSアニマックス
    "jk260": (260,),  # BS松竹東急
    "jk263": (263,),  # BSJapanext
    "jk265": (265,),  # BSよしもと
    "jk333": (333,),  # AT-X
}

jk_names = {
    "jk1": "NHK総合",
    "jk2": "NHK Eテレ",
    "jk4": "日本テレビ",
    "jk5": "テレビ朝日",
    "jk6": "TBSテレビ",
    "jk7": "テレビ東京",
    "jk8": "フジテレビ",
    "jk9": "TOKYO MX",
    "jk101": "NHK BS1",
    "jk103": "NHK BSプレミアム",
    "jk141": "BS日テレ",
    "jk151": "BS朝日",
    "jk161": "BS-TBS",
    "jk171": "BSテレ東",
    "jk181": "BSフジ",
    "jk191": "WOWOWプライム",
    "jk211": "BS11",
    "jk222": "BS12",
    "jk236": "BSアニマックス",
    "jk260": "BS松竹東急",
    "jk263": "BSJapanext",
    "jk265": "BSよしもと",
    "jk333": "AT-X",
}


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
    for jkch, sevice_ids in jk_chs.items():
        if service_id in sevice_ids:
            return jkch
    return False


def get_datetime(date_time):
    return datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S+09:00")

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
    end_date_time = start_date_time + datetime.timedelta(seconds=item["duration"])
    total_minutes = round(int(item["duration"]) / 60)
    # 引数指定で再生中動画の再生時間を上書き
    if fixlive:
        end_date_time = start_date_time + datetime.timedelta(seconds=(fixlive * 60)) + datetime.timedelta(seconds=14)
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
                f"エラー：「{item["channelName"]}」は定義されていないチャンネルのため、空ファイルを作成します。"
            )
            logger.info(f"ファイル名:{base_file}.xml")

    return jkid, start_date_time, end_date_time, total_minutes, title


def get_kakolog_api(start_date_time, end_date_time, title, jkid, total_minutes, logfile, logfile_limit):
    start_unixtime = start_date_time.timestamp()
    end_unixtime = end_date_time.timestamp()
    try:
        kakolog = requests.get(
            f"https://jikkyo.tsukumijima.net/api/kakolog/{jkid}?starttime={start_unixtime}&endtime={end_unixtime}&format=xml",
            headers=headers,
            timeout=5,
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

    # # 過去ログAPIにログがないときは避難所から取得
    # if line_count < 1 and 1718000400 <= start_unixtime:
    #     lines = []
    #     try:
    #         nx_kako_log = NxKakoLog()
    #         # NX-Jikkyoからの取得処理
    #         logger.info("ニコニコ実況避難所からログを取得中")
    #         tmp_lines = nx_kako_log.get_comment(jkid, start_unixtime, end_unixtime)
    #         line_count = len(tmp_lines)
    #         if line_count < 1:
    #             logger.info("エラー：ニコニコ実況避難所に指定された期間のログは存在しません。")
    #         lines.append('<?xml version="1.0" encoding="UTF-8"?>' + "\n")
    #         lines.append("<packet>" + "\n")
    #         lines += tmp_lines
    #         lines.append("</packet>" + "\n")

    #     except Exception as e:
    #         logger.info("エラー：ニコニコ実況避難所のAPIから取得できません。")
    #         return False

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

    ret = twitter_write(jk_names[jkid], start_date_time, total_minutes, title, line_count)
    if not ret:
        logger.info("tweetに失敗しました。対象: " + title)

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
        pass
    # ツイートが成功したかどうかを返す
    return status


def open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title):

    base_file = f"{jk_names[jkid]}_{start_date_time.strftime("%Y%m%d_%H%M%S")}_{total_minutes}_{title}" 
    logfile = os.path.join(kakolog_dir, f"{base_file}.xml")
    logfile_limit = os.path.join(kakolog_dir, f"{base_file}_limit.xml")

    # ファイルが存在しない場合
    if not os.path.exists(logfile):
        # 過去ログAPIから取得
        logger.info(f"ファイル名:{base_file}.xml")
        ret = get_kakolog_api(start_date_time, end_date_time, title, jkid, total_minutes, logfile, logfile_limit)
        if not ret:
            return False
    else:
        if not mode_monitoring:
            print("ファイル名:" + base_file + ".xml")

    # mode_silentがFalseの時はコメントビュアーを起動
    if not mode_silent:
        # commenomiが存在するかどうかをチェック
        if not os.path.exists(commenomi_path):
            logger.info("エラー：commenomiが見つからないため、終了します。" + commenomi_path)
            sys.exit(1)
        if rate_per_seconde > 0 and os.path.exists(logfile_limit):
            subprocess.Popen([commenomi_path, logfile_limit])
        else:
            subprocess.Popen([commenomi_path, logfile])
    return True


def open_jkcommentviewer(service_id):
    if mode_silent or jkcommentviewer_path is None:
        return True
    # ライブ視聴中のチャンネルを取得する
    jkid = get_jkid(service_id)
    try:
        url = f"https://nx-jikkyo.tsukumijima.net/watch/jk{jkid}"
    except:
        logger.info("エラー：ニコニコ実況番組が見つかりません。")
        return False
    # jkcommentviewerオープン
    if not os.path.exists(jkcommentviewer_path):
        logger.info("エラー：jkcommentviewer.exeが見つかりません。" + jkcommentviewer_path)
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
            playing_content_id = playing_info["client"][0]["content"]["id"]
            # 再生中の番組情報を取得する
            jkid, start_date_time, end_date_time, total_minutes, title = get_content_data(ip_addr, playing_content_id)
            # 番組終了5分以内は過去ログを取得しない
            if datetime.datetime.timestamp(end_date_time + datetime.timedelta(minutes=5)) < datetime.datetime.timestamp(
                (datetime.datetime.now())
            ):
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
for k, v in jk_names.items():
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

# mode_limitが指定されているときはコメント流量を調整する
try:
    comment_limit = ini["COMMENT"]["comment_limit"]
except KeyError:
    comment_limit = None

# iniより引数の設定を優先
if "none" == args.limit:
    rate_per_seconde = 0  # 流量調整なし
elif "high" == args.limit:
    rate_per_seconde = 3  # 間引き[高]
elif "middle" == args.limit:
    rate_per_seconde = 4  # 間引き[中]
elif "low" == args.limit:
    rate_per_seconde = 5  # 間引き[低]
elif "high" == comment_limit:
    rate_per_seconde = 3
elif "middle" == comment_limit:
    rate_per_seconde = 4
elif "low" == comment_limit:
    rate_per_seconde = 5
else:
    rate_per_seconde = 0

# mode_limitが指定されているときはコメント流量を制限する
try:
    comment_aborn_or_delete = ini["COMMENT"]["aborn_or_delete"]
except KeyError:
    comment_aborn_or_delete = None
if "aborn" == comment_aborn_or_delete:
    comment_aborn_flg = True
else:
    comment_aborn_flg = False

# 間引きしたコメントの割合がこの数値以下だった場合、limitファイルを作成しない(0-99)
try:
    limit_ratio = int(ini["COMMENT"]["limit_ratio"])
except KeyError:
    limit_ratio = 0

if not mode_silent:
    logger.info("starting..")

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
    if jkid not in jk_names:
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
        start_date_time = parse(start_at) - datetime.timedelta(seconds=15) + datetime.timedelta(days=plus_days)

    if total_minutes >= 600:
        logger.info("エラー：600分以上は指定できません。")
        sys.exit(1)
    end_date_time = start_date_time + datetime.timedelta(minutes=total_minutes) + datetime.timedelta(seconds=14)
    # commenomi用のコメント再生処理
    open_comment_viewer(jkid, start_date_time, end_date_time, total_minutes, title)
    sys.exit(0)

# main
if mode_monitoring:
    # 常駐監視モード
    print("常駐監視モード開始 " + datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))
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
