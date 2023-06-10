# -*- coding: utf-8 -*-


from json import loads

from boto3 import resource
from google.oauth2 import service_account
from gspread import authorize, utils, worksheet

"""
戦闘特技シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# DBコネクション
Dynamodb = None

# 技能シート
Sheet: worksheet = None

# シート全体に適用するテキストの書式
DefaultTextFormat: dict = {
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

    # 戦闘特技シートを開く
    book = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("戦闘特技")


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
    headers = [
        "No.",
        "PC",
        "バトルダンサー",
        "Lv.1",
        "Lv.3",
        "Lv.5",
        "Lv.7",
        "Lv.9",
        "Lv.11",
        "Lv.13",
        "Lv.15",
        "自動取得",
    ]
    updateData.append(headers)
    formats = []
    for player in players:
        row = []
        ytsheetJson = loads(player["ytsheetJson"])

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(int(player["id"]))

        # PC
        row.append(ytsheetJson["characterName"])

        # バトルダンサー
        row.append(ytsheetJson.get("combatFeatsLv1bat"))

        # Lv.1
        row.append(ytsheetJson.get("combatFeatsLv1"))

        # Lv.3
        row.append(ytsheetJson.get("combatFeatsLv3"))

        # Lv.5
        row.append(ytsheetJson.get("combatFeatsLv5"))

        # Lv.7
        row.append(ytsheetJson.get("combatFeatsLv7"))

        # Lv.9
        row.append(ytsheetJson.get("combatFeatsLv9"))

        # Lv.11
        row.append(ytsheetJson.get("combatFeatsLv11"))

        # Lv.13
        row.append(ytsheetJson.get("combatFeatsLv13"))

        # Lv.15
        row.append(ytsheetJson.get("combatFeatsLv15"))

        # 自動取得
        autoCombatFeats = ytsheetJson.get("combatFeatsAuto", "").split(",")
        for autoCombatFeat in autoCombatFeats:
            row.append(autoCombatFeat)

        updateData.append(row)

        # 書式設定
        rowIndex = updateData.index(row) + 1

        # PC列のハイパーリンク
        pcIndex = headers.index("PC") + 1
        pcTextFormat = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # 習得レベルに満たないものはグレーで表示
        level = int(ytsheetJson.get("level", "0"))
        grayOutStartIndex = None
        for i in range(3, 15, 2):
            if level < i:
                grayOutStartIndex = headers.index(f"Lv.{i}") + 1
                break

        if grayOutStartIndex is not None:
            grayOutEndIndex = headers.index("Lv.15") + 1
            grayOutTextFormat = DefaultTextFormat.copy()
            grayOutTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}
            }
            startA1 = utils.rowcol_to_a1(rowIndex, grayOutStartIndex)
            endA1 = utils.rowcol_to_a1(rowIndex, grayOutEndIndex)
            formats.append(
                {
                    "range": f"{startA1}:{endA1}",
                    "format": {"textFormat": grayOutTextFormat},
                }
            )

    # クリア
    Sheet.clear()

    # 更新
    Sheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(len(updateData), len(headers))
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
    endA1 = utils.rowcol_to_a1(1, len(headers))
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
