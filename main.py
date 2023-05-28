# -*- coding: utf-8 -*-

from google.oauth2 import service_account
from googleapiclient.discovery import build
from json import load

"""
ゆとシートからデータを取得してスプレッドシートを更新
"""

# 設定ファイルのパス
CONFIG_DIRECTORY = "config/"
CONFIG_FILE = f"{CONFIG_DIRECTORY}config.json"
SERVICE_ACCOUNT_FILE = f"{CONFIG_DIRECTORY}service.json"

# スプレッドシートの情報
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def main():
    """
    メイン処理
    """

    # 設定ファイルを読み込み
    with open(CONFIG_FILE, "r") as file:
        json = load(file)
        spreadsheetId = json["spreadsheetId"]

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=spreadsheetId, range="Class Data!A2:E")
        .execute()
    )
    values = result.get("values", [])

    if not values:
        print("No data found.")
        return

    print("Name, Major:")
    for row in values:
        # Print columns A and E, which correspond to indices 0 and 4.
        print("%s, %s" % (row[0], row[4]))


if __name__ == "__main__":
    main()
