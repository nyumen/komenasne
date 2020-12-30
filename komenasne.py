# -*- coding: utf-8 -*-
import requests
import json
import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import webbrowser
import subprocess
import configparser
import platform
import os
import sys

'''
# 必要
pip install requests
pip install beautifulsoup4
iniの設定

# メモ
jk1=NHK 総合，jk2=Eテレ，jk4=日本テレビ，jk5=テレビ朝日，jk6=TBS テレビ，jk7=テレビ東京，jk8=フジテレビ
，jk9=TOKYO MX，jk10=テレ玉，jk11=tvk，jk12=チバテレビ

jk101=NHKBS-1，jk103=NHK BSプレミアム，jk141=BS 日テレ，jk151=BS 朝日，jk161=BS-TBS，jk171=BSジャパン
，jk181=BSフジ，jk191=WOWOWプライム，jk192=WOWOWライブ，jk193=WOWOWシネマ，jk200=スターチャンネル1
，jk201=スターチャンネル2，jk202=スターチャンネル3，jk211=BSイレブン
'''

jkchs = {
    'ＢＳ１１' : 211,
    'ＮＨＫＢＳプ' : 103,
    'ＮＨＫＢＳ１' : 101,
    'ＢＳジャパン' : 171,
    'ＢＳ朝日' : 151,
    'ＢＳ日テレ' : 141,
    'ＢＳ－ＴＢＳ' : 161,
    'ＢＳフジ' : 181,
    '総合' : 1,
    'Ｅテレ' : 2,
    '日テレ' : 4,
    '読売テレビ' : 4, # 関西
    '中京テレビ' : 4, # 中部
    'テレビ朝日' : 5,
    'ＡＢＣテレビ' : 5, # 関西
    'メ～テレ' : 5, # 中部
    'ＴＢＳ' : 6,
    'ＭＢＳ' : 6, # 関西
    'ＣＢＣ' : 6, # 中部
    'テレビ東京' : 7,
    'テレビ大阪' : 7, # 関西
    'テレビ愛知' : 7, # 中部
    'フジテレビ' : 8,
    '関西テレビ' : 8, # 関西
    '東海テレビ' : 8, # 中部
    'ＭＸ' : 9,
    'テレ玉' : 10,
    'ＴＶＫ' : 11,
    'チバテレ' : 12}

jk_names = {
    'jk1' : 'NHK総合',
    'jk2' : 'NHK Eテレ',
    'jk4' : '日本テレビ',
    'jk5' : 'テレビ朝日',
    'jk6' : 'TBSテレビ',
    'jk7' : 'テレビ東京',
    'jk8' : 'フジテレビ',
    'jk9' : 'TOKYO MX',
    'jk211' : 'BS11'}

def get_item(ip_addr, playing_content_id):
    get_title_lists = s.get(f'http://' + ip_addr + ':64220/recorded/titleListGet?searchCriteria=0&filter=0&startingIndex=0&requestedCount=0&sortCriteria=0&withDescriptionLong=0&withUserData=0')
    title_lists = json.loads(get_title_lists.text)

    for item in title_lists['item']:
        if item['id'] == playing_content_id:
            return item

def get_jkid(channel_name):
    for ch in jkchs:
        if ch in channel_name:
            return 'jk' + str(jkchs[ch])
    return False

def get_datetime(date_time):
    return datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S+09:00")

def get_tsurl(jkid, date_time):
    # "TBSテレビ【ニコニコ実況】2020年12月26日"等
    ch_name = jk_names[jkid]
    enc_title = ch_name + '【ニコニコ実況】' + date_time.strftime("%Y年%m月%d日")
    print(enc_title)
    load_url = "https://live.nicovideo.jp/search?keyword=" + quote(enc_title) + "&status=onair&sortOrder=recentDesc&providerTypes=channel"

    html = requests.get(load_url)
    soup = BeautifulSoup(html.content, "html.parser")

    # タイムシフトのURL（watch/lv****** ）を取得
    param = soup.find(class_="searchPage-ProgramList_TitleLink").get('href')
    return 'https://live2.nicovideo.jp/' + param


# init
ini = configparser.ConfigParser()
ini.read('./komenasne.ini', 'UTF-8')
nase_ini = ini['NASNE']['ip']
nasne_ips = [x.strip() for x in nase_ini.split(',')]

jkcommentviewer_path = None
if ini['PLAYER']['jkcommentviewer_path']:
    jkcommentviewer_path = ini['PLAYER']['jkcommentviewer_path']
    if platform.platform().startswith("Windows"):
        jkcommentviewer_path = jkcommentviewer_path.replace(os.sep, os.sep + os.sep)

s = requests.Session();

# main
for ip_addr in nasne_ips:

    get_playing_info = s.get(f'http://{ip_addr}:64210/status/dtcpipClientListGet')
    playing_info = json.loads(get_playing_info.text)

    if 'client' in playing_info:
        playing_content_id = playing_info['client'][0]['content']['id']
        item = get_item(ip_addr, playing_content_id)
        #print(item)
        print(item['id'] + ' ' + item['title'] + ' ' + item['channelName'])
        jkid = get_jkid(item['channelName'])
        if not jkid:
             print('エラー：「' + item['channelName'] + '」は定義されていないチャンネルのため、連携できません。')
             sys.exit(1)

        start_date_time = get_datetime(item['startDateTime'])
        end_date_time = start_date_time + datetime.timedelta(seconds=item['duration'])
        print("start:" + str(start_date_time), "end:" + str(end_date_time))

        ts_time = start_date_time - datetime.timedelta(hours=4)
        try:
            url = get_tsurl(jkid, ts_time)
        except:
             print('エラー：タイムシフト番組が見つかりません。')
             sys.exit(1)

        if jkcommentviewer_path is None:
            if ts_time.strftime('%Y%m%d') == '20201216':
                # 新ニコニコ実況の初日は11時開始のため7時間減算
                ts_time = ts_time - datetime.timedelta(hours=7)
            shift_time = ts_time.strftime('%H:%M:%S')
            browser_url = url + '#' + shift_time
            print(browser_url)
            webbrowser.open(browser_url)
        else:
            jkcommentviewer_url = url + '?start_date=' + start_date_time.strftime("%Y%m%d%H%M%S") + '&end_date=' + end_date_time.strftime("%Y%m%d%H%M%S")
            path = jkcommentviewer_path + " " + jkcommentviewer_url
            print(path)
            subprocess.Popen([jkcommentviewer_path, jkcommentviewer_url])

        break
        sys.exit(0)

print('エラー：再生中のnasneの動画が見つからないため、終了します。')
sys.exit(1)


