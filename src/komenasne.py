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
import tempfile
import math

'''
# 必要
pip install requests
pip install beautifulsoup4
iniの設定
'''

jkchs = {
    'ＮＨＫＢＳ１' : 101,
    'ＮＨＫＢＳプ' : 103,
    'ＢＳ日テレ' : 141,
    'ＢＳ朝日' : 151,
    'ＢＳ－ＴＢＳ' : 161,
    'ＢＳジャパン' : 171,
    'ＢＳテレ東' : 171,
    'ＢＳフジ' : 181,
    'ＷＯＷＯＷプライム' : 191,
    'スターチャンネル１' : 200,
    'ＢＳ１１' : 211,
    'ＢＳ１２' : 222,
    'ＢＳアニマックス' : 236,
    'ＡＴ－Ｘ' : 333,
    '総合' : 1,
    'Ｅテレ' : 2,
    '日テレ' : 4,
    '読売テレビ' : 4, # 関西
    '中京テレビ' : 4, # 中部
    'ＦＢＳ福岡放送' :4, # 福岡
    'ＲＮＣ' : 4, # 香川・岡山
    'テレビ朝日' : 5,
    'ＡＢＣテレビ' : 5, # 関西
    'メ～テレ' : 5, # 中部
    'ＫＢＣテレビ' : 5, # 福岡
    '瀬戸内海放送' : 5, # 香川・岡山
    'ＴＢＳ' : 6,
    'ＭＢＳ' : 6, # 関西
    'ＣＢＣ' : 6, # 中部
    'ＲＫＢ毎日放送' : 6, # 福岡
    'ＲＳＫ' : 6, # 香川・岡山
    'テレビ東京' : 7,
    'テレビ大阪' : 7, # 関西
    'テレビ愛知' : 7, # 中部
    'ＴＶＱ九州放送' : 7, # 福岡
    'ＴＳＣ' : 7, # 香川・岡山
    'フジテレビ' : 8,
    '関西テレビ' : 8, # 関西
    '東海テレビ' : 8, # 中部
    'テレビ西日本' : 8, # 福岡
    'ＯＨＫ' : 8, # 香川・岡山
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
    'jk101' : 'NHK BS1',
    'jk103' : 'NHK BSプレミアム',
    'jk141' : 'BS日テレ',
    'jk151' : 'BS朝日',
    'jk161' : 'BS-TBS',
    'jk171' : 'BSテレ東',
    'jk181' : 'BSフジ',
    'jk191' : 'WOWOWプライム',
    'jk200' : 'BSスター1',
    'jk211' : 'BS11イレブン',
    'jk222' : 'BS12トゥエルビ',
    'jk236' : 'BSアニマックス',
    'jk333' : 'AT-X'}

def get_item(ip_addr, playing_content_id):
    get_title_lists = s.get(f'http://{ip_addr}:64220/recorded/titleListGet?searchCriteria=0&filter=0&startingIndex=0&requestedCount=0&sortCriteria=0&withDescriptionLong=0&withUserData=0')
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

# タイムシフトのURL（watch/lv****** ）を取得
def get_tsurl(jkid, date_time):
    # "TBSテレビ【ニコニコ実況】2020年12月26日"等
    ch_name = jk_names[jkid]
    enc_title = ch_name + '【ニコニコ実況】' + date_time.strftime("%Y年%m月%d日")
    print(enc_title)
    load_url = "https://live.nicovideo.jp/search?keyword=" + quote(enc_title) + "&status=onair&sortOrder=recentDesc&providerTypes=channel"

    html = requests.get(load_url,headers=headers)
    soup = BeautifulSoup(html.content, "html.parser")

    param = soup.find(class_="searchPage-ProgramList_TitleLink").get('href')
    return 'https://live2.nicovideo.jp/' + param

# ファイル名に使用できない文字を変換
def replace_title(title):
    title = title.replace('\ue180', '[デ]')
    title = title.replace('\ue183', '[多]')
    title = title.replace('\ue184', '[解]') 
    title = title.replace('\ue185', '[SS]') 
    title = title.replace('\ue18c', '[映]')
    title = title.replace('\ue18d', '[無]')
    title = title.replace('\ue190', '[前]') 
    title = title.replace('\ue191', '[後]') 
    title = title.replace('\ue192', '[再]')
    title = title.replace('\ue193', '[新]')
    title = title.replace('\ue195', '[終]')
    title = title.replace('\ue0fe', '[字]')
    title = title.replace('\ue2ca1', 'No1')
    title = title.replace('/', '／')
    title = title.replace('<', '＜')
    title = title.replace('>', '＞')
    title = title.replace(':', '：')
    title = title.replace('?', '？')
    return title

# vposをdateとdate_usecから再計算する（commenomi対策）
def rewrite_vpos(start_date_unixtime, xml_line):
    vpos_start = xml_line.find(' vpos="')
    if vpos_start == -1:
        return xml_line
    # xml内のvposの値を取得
    vpos_pos = vpos_start + 7 # len(' vpos="')
    vpos_str_count = xml_line[vpos_pos:].find('"')
    vpos_num = int(xml_line[vpos_pos:vpos_pos + vpos_str_count])
    # xml内dateの値の取得
    date_start = xml_line.find(' date="')
    date_num = xml_line[date_start + 7:date_start + 17]
    # xml内date_usecの値の取得
    date_usec_start = xml_line.find(' date_usec="')
    if date_usec_start == -1:
        date_usec_num = "0"
    else:
        date_usec_str_count = xml_line[date_usec_start + 12:].find('"')
        date_usec_num = xml_line[date_usec_start + 12:date_usec_start + 12 + date_usec_str_count]
    # コメントのunixtimeから動画開始時のunixtime引いた値を新しいvposとする
    comment_unixtime = float(date_num + "." + date_usec_num)
    new_vpos = math.ceil((comment_unixtime - start_date_unixtime) * 100)
    return xml_line[:vpos_pos] + str(new_vpos) + xml_line[vpos_pos + vpos_str_count:]


# init
ini = configparser.ConfigParser(interpolation=None)
ini.read('./komenasne.ini', 'UTF-8')
nase_ini = ini['NASNE']['ip']
nasne_ips = [x.strip() for x in nase_ini.split(',')]

is_windows = platform.platform().startswith("Windows")

try:
    commeon_path = ini['PLAYER']['commeon_path']
except KeyError:
    commeon_path = None

try:
    commenomi_path = ini['PLAYER']['commenomi_path']
except KeyError:
    commenomi_path = None

if commeon_path:
    # 以前のiniの互換性維持のためcommeon_pathで上書きする
    commenomi_path = commeon_path

if commenomi_path and is_windows:
    commenomi_path = commenomi_path.replace(os.sep, os.sep + os.sep)
    kakolog_dir = ini['LOG']['kakolog_dir']
    if '%temp%' in kakolog_dir:
        kakolog_dir = kakolog_dir.replace('%temp%', os.environ['temp'])
    kakolog_dir = kakolog_dir.replace(os.sep, os.sep + os.sep)

s = requests.Session();
headers = {'user-agent':'komenasne'}

# main
for ip_addr in nasne_ips:

    get_playing_info = s.get(f'http://{ip_addr}:64210/status/dtcpipClientListGet')
    playing_info = json.loads(get_playing_info.text)

    if 'client' in playing_info:
        playing_content_id = playing_info['client'][0]['content']['id']
        item = get_item(ip_addr, playing_content_id)
        #print(item)
        #print(item['title'].encode('unicode-escape'))
        title = replace_title(item['title'])
        print(item['id'] + ' ' + title + ' ' + item['channelName'])
        jkid = get_jkid(item['channelName'])
        if not jkid:
            print('エラー：「' + item['channelName'] + '」は定義されていないチャンネルのため、連携できません。')
            sys.exit(1)

        start_date_time = get_datetime(item['startDateTime'])
        end_date_time = start_date_time + datetime.timedelta(seconds=item['duration'])
        print("start:" + str(start_date_time), "end:" + str(end_date_time))
        start_unixtime = start_date_time.timestamp()
        end_unixtime = end_date_time.timestamp()

        if not is_windows or commenomi_path is None:
            # ブラウザ用のコメント再生処理、Windows・Mac兼用
            ts_time = start_date_time - datetime.timedelta(hours=4)
            try:
                url = get_tsurl(jkid, ts_time)
            except:
                print('エラー：タイムシフト番組が見つかりません。')
                sys.exit(1)
            if ts_time.strftime('%Y%m%d') == '20201216':
                # 新ニコニコ実況の初日は11時開始のため7時間減算
                ts_time = ts_time - datetime.timedelta(hours=7)
            shift_time = ts_time.strftime('%H:%M:%S')
            browser_url = url + '#' + shift_time
            print(browser_url)
            webbrowser.open(browser_url)
        else:
            # commenomi用のコメント再生処理
            kakolog = s.get(f'https://jikkyo.tsukumijima.net/api/kakolog/{jkid}?starttime={start_unixtime}&endtime={end_unixtime}&format=xml',headers=headers)
            logfile = kakolog_dir + jk_names[jkid] + '_' + start_date_time.strftime("%Y%m%d_%H%M%S") + '_' + title + '.xml'
            with open(logfile, 'w', encoding="utf-8") as saveFile:
                start_date_unixtime = start_date_time.timestamp()
                line_count = 0
                for xml_line in kakolog.iter_lines():
                    line = rewrite_vpos(start_date_unixtime, xml_line.decode())
                    saveFile.write(line + '\n')
                    line_count+=1
                    if line == '<error>指定された期間の過去ログは存在しません。</error>':
                        line_count = 0
                        break
                if line_count <= 3:
                    print('エラー：指定された期間の過去ログは存在しません。')
                    sys.exit(1)
            subprocess.Popen([commenomi_path, logfile])

        sys.exit(0)
        break

print('エラー：再生中のnasneの動画が見つからないため、終了します。')
sys.exit(1)


