import requests
import json
from datetime import datetime, timedelta, timezone, time
from dateutil import parser
import pytz
import os
import math

# タイムゾーンの設定
JST = pytz.timezone("Asia/Tokyo")


class NxKakoLog:
    def __init__(self):

        self.__jk_id: str = None
        self.__start_at: float = None  # timestamp
        self.__end_at: float = None  # timestamp
        self.__channels_url = "https://nx-jikkyo.tsukumijima.net/api/v1/channels"
        self.__channels_cache_file = "channels_cache.json"
        self.__cache_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "json_cache")
        os.makedirs(self.__cache_dir, exist_ok=True)

    # コメント取得処理（AM4時を跨ぐ場合は呼び出し側で2回に分けること）
    def get_comment(self, jk_id: str, start_at: float, end_at: float) -> list:

        self.__jk_id = jk_id
        self.__start_at = start_at
        self.__end_at = end_at
        del start_at, end_at

        # NX apiから取得（キャッシュから取得）
        channels_lists = self.__fetch_data(self.__channels_url, self.__channels_cache_file)
        thread_id = self.__get_thread_id(channels_lists)
        if thread_id is None:
            # NX apiから取得（直接取得）
            channels_lists = self.__fetch_data(self.__channels_url, self.__channels_cache_file, over_write_flg=True)
            thread_id = self.__get_thread_id(channels_lists)
            if thread_id is None:
                raise Exception(f"thread_id 該当なし。処理を続行できません。")  # 雑に終了

        # 当日の朝4時のdatetimeオブジェクトを作成
        now_dt = datetime.now(JST)
        today_am4_dt = JST.localize(datetime.combine(now_dt.date(), time(4, 0)))

        # JSTの0時から4時までの間かどうかをチェック
        if now_dt < today_am4_dt:
            # 前日の朝4時を取得
            today_am4_dt = today_am4_dt - timedelta(days=1)

        thread_url = f"https://nx-jikkyo.tsukumijima.net/api/v1/threads/{thread_id}"
        if self.__end_at <= today_am4_dt.timestamp():
            # 当日4時より前のデータはキャッシュ
            thread_cache_file = f"thread_cache_{thread_id}.json"
            comment_list = self.__fetch_data(thread_url, thread_cache_file)
        else:
            req = requests.get(thread_url)
            comment_list = req.json()

        lines = []
        for comment in comment_list["comments"]:
            comment_at = datetime.fromisoformat(comment["date"]).timestamp()
            if self.__start_at <= comment_at < self.__end_at:
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
                        print(s)
                        thread_id = s["id"]
                        break
        return thread_id

    def __get_cache_file_path(self, file_name: str) -> str:
        file_path = os.path.join(self.__cache_dir, file_name)
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), file_path)

    def __fetch_data(self, url: str, cache_file_name: str, over_write_flg: bool = False) -> dict:

        cache_file_path = self.__get_cache_file_path(cache_file_name)

        if not os.path.exists(cache_file_path) or over_write_flg:
            # キャッシュファイルが存在しない、または強制性取得フラグ
            req = requests.get(url)
            json_data = req.json()
            # キャッシュファイルに保存
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
        else:
            with open(cache_file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

        return json_data

    def __str_to_dt(self, str_dt: str) -> datetime:
        if len(str_dt) == 32:
            dt = datetime.strptime(str_dt, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            dt = datetime.strptime(str_dt, "%Y-%m-%dT%H:%M:%S%z")
        return dt

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


def main():

    # テスト
    nx_kako_log = NxKakoLog()

    jk_id = "jk9"  # 'TOKYO MX'
    # jk_id = "jk211"  # 'BS11'
    start_at = JST.localize(datetime(2024, 6, 13, 22, 29, 45)).timestamp()
    end_at = JST.localize(datetime(2024, 6, 13, 23, 00, 0)).timestamp()

    # 取得処理
    lines = nx_kako_log.get_comment(jk_id, start_at, end_at)

    xml_file = "dungeon_mesi_240613.xml"
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>' + "\n")
        f.write("<packet>" + "\n")
        f.writelines(lines)
        f.write("</packet>" + "\n")

    print(len(lines), "件")


if __name__ == "__main__":
    main()
