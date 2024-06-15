import requests
import json
from datetime import datetime, timezone
import pytz
import os
import math
import sys

# タイムゾーンの設定
JST = pytz.timezone("Asia/Tokyo")


class NxKakoLog:
    def __init__(self):

        self.__jk_id: str = None
        self.__start_at: float = None  # timestamp
        self.__end_at: float = None  # timestamp
        self.__channels_url = "https://nx-jikkyo.tsukumijima.net/api/v1/channels"
        self.__channels_cache_file = "channels_cache.json"
        self.__cache_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "json_cache")
        os.makedirs(self.__cache_dir, exist_ok=True)

    # コメント取得処理（AM4時を跨ぐ場合は呼び出し側で2回に分けること）
    def get_comment(self, jk_id: str, start_at: float, end_at: float) -> list:

        self.__jk_id = jk_id
        self.__start_at = start_at
        self.__end_at = end_at
        del start_at, end_at

        # NX apiから取得（キャッシュから取得）
        thread_id = None
        channels_cache_file_path = os.path.join(self.__cache_dir, self.__channels_cache_file)
        if os.path.exists(channels_cache_file_path):
            with open(channels_cache_file_path, "r", encoding="utf-8") as f:
                channels_lists = json.load(f)
            thread_id = self.__get_thread_id(channels_lists)

        if thread_id is None:
            # NX apiから取得（直接取得）
            req = requests.get(self.__channels_url)
            channels_lists = req.json()
            # キャッシュファイルに保存
            with open(channels_cache_file_path, "w", encoding="utf-8") as f:
                json.dump(channels_lists, f, ensure_ascii=False, indent=4)
            thread_id = self.__get_thread_id(channels_lists)
            if thread_id is None:
                raise Exception(f"thread_id 該当なし。処理を続行できません。")  # 雑に終了

        # スレッド情報取得
        thread_url = f"https://nx-jikkyo.tsukumijima.net/api/v1/threads/{thread_id}"
        thread_cache_file_path = os.path.join(self.__cache_dir, f"thread_cache_{thread_id}.json")
        print(thread_cache_file_path)
        if os.path.exists(thread_cache_file_path):
            # キャッシュから取得
            with open(thread_cache_file_path, "r", encoding="utf-8") as f:
                comment_list = json.load(f)
        else:
            # キャッシュファイルが存在しない
            req = requests.get(thread_url)
            comment_list = req.json()
            print("status", comment_list["status"])
            if comment_list["status"] != "ACTIVE":
                # アクティブなスレッド以外はキャッシュファイルに保存
                with open(thread_cache_file_path, "w", encoding="utf-8") as f:
                    json.dump(comment_list, f, ensure_ascii=False, indent=4)

        lines = []
        for comment in comment_list["comments"]:
            comment_at = datetime.fromisoformat(comment["date"]).timestamp()
            if comment["content"] == "最後のダン飯待機":
                print(self.__start_at, comment_at, self.__end_at)
            if self.__start_at <= comment_at < self.__end_at:
                print("あ")
                # if self.__start_at <= comment_at < self.__end_at:
                xml_output = self.__json_to_xml(comment)
                line = self.__rewrite_vpos(self.__start_at, xml_output)
                lines.append(line + "\n")
                # print(comment["vpos"], comment["date"], comment["content"])

        return lines

    def __get_thread_id(self, channels_lists: dict) -> str:

        thread_id = None
        for j in channels_lists:
            if j["id"] == self.__jk_id:
                for s in j["threads"]:
                    start_at = datetime.fromisoformat(s["start_at"]).timestamp()
                    end_at = datetime.fromisoformat(s["end_at"]).timestamp()
                    if start_at <= self.__start_at < end_at:
                        thread_id = s["id"]
                        break
        return thread_id

    # 日時文字列をパースしてUNIXエポック時間とマイクロ秒部分を取得する関数
    def __parse_date_with_usec(self, date_str: str) -> int:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))  # UTC表記に対応
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        delta = dt.astimezone(timezone.utc) - epoch
        return int(delta.total_seconds()), dt.microsecond

    # JSONデータをXML形式に変換する関数
    def __json_to_xml(self, json_data: dict) -> str:
        xml_data = (
            f'<chat thread="{json_data["thread_id"]}" '
            f'no="{json_data["no"]}" '
            f'vpos="{json_data["vpos"]}" '
            f'date="{self.__parse_date_with_usec(json_data["date"])[0]}" '
            f'date_usec="{self.__parse_date_with_usec(json_data["date"])[1]}" '
            f'mail="{json_data["mail"]}" '
            f'user_id="{json_data["user_id"]}" '
            f'anonymity="{int(json_data["anonymity"])}">'
            f'{json_data["content"]}</chat>'
        )
        return xml_data

    # vposをdateとdate_usecから再計算する（commenomi対策）
    def __rewrite_vpos(self, start_date_unixtime: float, xml_line: str) -> str:
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


# def main():

#     # テスト
#     nx_kako_log = NxKakoLog()

#     jk_id = "jk9"  # 'TOKYO MX'
#     # jk_id = "jk211"  # 'BS11'
#     # start_at = JST.localize(datetime(2024, 6, 13, 22, 29, 45)).timestamp()
#     # end_at = JST.localize(datetime(2024, 6, 13, 23, 00, 0)).timestamp()

#     # 取得処理
#     lines = nx_kako_log.get_comment(jk_id, start_at, end_at)

#     xml_file = "dungeon_mesi_240613.xml"
#     with open(xml_file, "w", encoding="utf-8") as f:
#         f.write('<?xml version="1.0" encoding="UTF-8"?>' + "\n")
#         f.write("<packet>" + "\n")
#         f.writelines(lines)
#         f.write("</packet>" + "\n")

#     print(len(lines), "件")


# if __name__ == "__main__":
#     main()
