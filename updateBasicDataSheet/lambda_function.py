# -*- coding: utf-8 -*-


from datetime import datetime
from json import loads
from re import escape, search

from boto3 import resource
from google.oauth2 import service_account
from gspread import authorize, utils, worksheet
from pytz import timezone

"""
基本シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# DBコネクション
Dynamodb = None

# 基本シート
Sheet: worksheet = None

# 自分が開催したときのGM名
SelfGameMasterNames: "list[str]" = [
    "俺",
    "私",
    "私だ",
    "私だ。",
    "自分",
    "おれさま",
    "拙者",
    "我",
    "朕",
]

# 死亡時の備考
DiedRegexp: str = "|".join(list(map(escape, ["「死亡」", "(死亡)"])))

# シート全体に適用するテキストの書式
DefaultTextFormat = {
    "fontFamily": "Meiryo",
}


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId = event["SpreadsheetId"]

    # 初期化
    init(spreadsheetId)

    # ゆとシートのデータを取得
    players = getPlayers()

    # 更新
    updateSheet(players)


def init(spreadsheetId: str):
    """

    初期化

    Args:
        spreadsheetId str: スプレッドシートのID
    """
    global Dynamodb, Sheet

    Dynamodb = resource("dynamodb", region_name=AWS_REGION)

    # DBからスプレッドシートのIDを取得
    googleServiceAccounts = Dynamodb.Table("GoogleServiceAccounts")
    response = googleServiceAccounts.get_item(
        Key={"id": GOOGLE_SERVIE_ACCOUNT_ID}
    )
    googleServiceAccount = response["Item"]

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount["json"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = authorize(credentials)

    # 基本シートを開く
    book = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("基本")


def getPlayers():
    """DBからプレイヤー情報を取得

    容量が大きいためStep Functionsでは対応不可

    """
    global Dynamodb

    teble = Dynamodb.Table("Players")
    response = teble.scan()

    # ページ分割分を取得
    players = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        response = teble.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    players.extend(response["Items"])

    # idでソート
    players.sort(key=lambda player: player["id"])

    return players


def updateSheet(players: "list[dict]"):
    """

    シートを更新

    Args:
        spreadsheetId str: スプレッドシートのID
    """
    global Sheet

    updateData = []

    # ヘッダー
    header = [
        "No.",
        "PC",
        "PL",
        "種族",
        "年齢",
        "性別",
        "信仰",
        "穢れ",
        "参加",
        "GM",
        "死亡",
        "更新日時",
    ]
    updateData.append(header)

    totalDiedTimes = 0
    formats = []
    for player in players:
        row = []
        ytsheetJson = loads(player["ytsheetJson"])

        # セッション履歴を集計
        gmTimes = 0
        playerTimes = 0
        diedTimes = 0
        historyNum = int(ytsheetJson["historyNum"])
        for i in range(1, historyNum):
            if f"history{i}Gm" not in ytsheetJson:
                # GM名が空白の履歴は読み飛ばす
                continue

            # 参加、GM回数を集計
            gm = ytsheetJson[f"history{i}Gm"]
            if gm == player["player"] or gm in SelfGameMasterNames:
                gmTimes += 1
            else:
                playerTimes += 1

            # 死亡回数を集計
            note = ytsheetJson.get(f"history{i}Note", "")
            if search(DiedRegexp, note):
                diedTimes += 1

        # 更新日時をスプレッドシートが理解できる形式に変換
        updatetime = player.get("updateTime")
        if updatetime is not None:
            # UTCをJSTに変換
            utc = datetime.strptime(updatetime, "%Y-%m-%dT%H:%M:%S.%fZ")
            utc = utc.replace(tzinfo=timezone("UTC"))
            jst = utc.astimezone(timezone("Asia/Tokyo"))
            updatetime = jst.strftime("%Y/%m/%d %H:%M:%S")

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(int(player["id"]))

        # PC
        row.append(ytsheetJson["characterName"])

        # PL
        row.append(player["player"])

        # 種族
        row.append(ytsheetJson.get("race"))

        # 年齢
        row.append(ytsheetJson.get("age", ""))

        # 性別
        row.append(ytsheetJson.get("gender"))

        # 信仰
        row.append(ytsheetJson.get("faith", "なし"))

        # 穢れ
        row.append(ytsheetJson.get("sin", 0))

        # 参加
        row.append(playerTimes)

        # GM
        row.append(gmTimes)

        # 死亡
        row.append(diedTimes)

        # 更新日時
        row.append(updatetime)

        updateData.append(row)

        # PC列のハイパーリンク
        pcIndex = row.index(ytsheetJson["characterName"]) + 1
        rowIndex = updateData.index(row) + 1
        pcTextFormat = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # 合計行を集計
        totalDiedTimes += diedTimes

    # 合計行
    total = [None] * len(header)
    diedIndex = header.index("死亡")
    total[diedIndex - 1] = "合計"
    total[diedIndex] = totalDiedTimes
    updateData.append(total)

    # クリア
    Sheet.clear()

    # 更新
    Sheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(len(updateData), len(header))
    Sheet.format(
        f"{startA1}:{endA1}",
        {
            "textFormat": {
                "fontFamily": "Meiryo",
            },
        },
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"horizontalAlignment": "CENTER"},
        }
    )

    # 部分的なフォーマットを設定
    Sheet.batch_format(formats)

    # 行列の固定
    Sheet.freeze(1, 2)

    # フィルター
    Sheet.set_basic_filter(1, 1, len(updateData) - 1, len(header))
