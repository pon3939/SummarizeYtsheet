# -*- coding: utf-8 -*-


from boto3 import resource
from google.oauth2 import service_account
from gspread import Client, Spreadsheet, authorize, utils, worksheet

"""
基本シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# 基本シート
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
    spreadsheetId: str = event["SpreadsheetId"]
    players: "list[dict]" = event["Players"]

    # 初期化
    init(spreadsheetId)

    # 更新
    updateSheet(players)


def init(spreadsheetId: str):
    """

    初期化

    Args:
        spreadsheetId str: スプレッドシートのID
    """
    global Sheet

    dynamodb = resource("dynamodb", region_name=AWS_REGION)

    # DBからスプレッドシートのIDを取得
    googleServiceAccounts = dynamodb.Table("GoogleServiceAccounts")
    response: dict = googleServiceAccounts.get_item(
        Key={"id": GOOGLE_SERVIE_ACCOUNT_ID}
    )
    googleServiceAccount: dict = response["Item"]

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount["json"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client: Client = authorize(credentials)

    # 基本シートを開く
    book: Spreadsheet = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("基本")


def updateSheet(players: "list[dict]"):
    """

    シートを更新

    Args:
        players list[dict]: プレイヤー情報
    """
    global Sheet

    updateData: list["dict"] = []

    # ヘッダー
    header: "list[str]" = [
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

    totalDiedTimes: int = 0
    formats: "list[dict]" = []
    for player in players:
        row: list = []

        # No.
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # PL
        row.append(player["name"])

        # 種族
        row.append(player["race"])

        # 年齢
        row.append(player["age"])

        # 性別
        row.append(player["gender"])

        # 信仰
        row.append(player["faith"])

        # 穢れ
        row.append(player["sin"])

        # 参加
        row.append(player["playerTimes"])

        # GM
        row.append(player["gameMasterTimes"])

        # 死亡
        row.append(player["diedTimes"])

        # 更新日時
        row.append(player["updateTime"])

        updateData.append(row)

        # PC列のハイパーリンク
        pcIndex: int = header.index("PC") + 1
        rowIndex: int = updateData.index(row) + 1
        pcTextFormat: dict = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # 合計行を集計
        totalDiedTimes += player["diedTimes"]

    # 合計行
    total: list = [None] * len(header)
    diedIndex: int = header.index("死亡")
    total[diedIndex - 1] = "合計"
    total[diedIndex] = totalDiedTimes
    updateData.append(total)

    # クリア
    Sheet.clear()

    # 更新
    Sheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    Sheet.format(
        f"{startA1}:{endA1}",
        {
            "textFormat": {
                "fontFamily": "Meiryo",
            },
        },
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(header))
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
