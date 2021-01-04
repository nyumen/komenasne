# -*- coding: utf-8 -*-
import requests
import json

nasne_ip = "192.168.0.4"
channel_names = []

get_title_lists = requests.get(f'http://' + nasne_ip + ':64220/recorded/titleListGet?searchCriteria=0&filter=0&startingIndex=0&requestedCount=0&sortCriteria=0&withDescriptionLong=0&withUserData=0')
title_lists = json.loads(get_title_lists.text)

for item in title_lists['item']:
    if 'ＢＳ' not in item['channelName']:
        channel_names.append(item['channelName'])

print(set(channel_names))
