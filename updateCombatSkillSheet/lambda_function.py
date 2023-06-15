# -*- coding: utf-8 -*-


from google.oauth2 import service_account
from gspread import Client, Spreadsheet, authorize, utils, worksheet

"""
戦闘特技シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# 戦闘特技シート
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
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: list[dict] = event["Players"]

    # 初期化
    init(spreadsheetId, googleServiceAccount)

    # 更新
    updateSheet(players)


def init(spreadsheetId: str, googleServiceAccount: dict):
    """

    初期化

    Args:
        spreadsheetId str: スプレッドシートのID
        googleServiceAccount str: スプレッドシートの認証情報
    """
    global Sheet

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client: Client = authorize(credentials)

    # 戦闘特技シートを開く
    book: Spreadsheet = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("戦闘特技")


def updateSheet(players: "list[dict]"):
    """

    シートを更新

    Args:
        players list[Player]: プレイヤー情報
    """
    global Sheet

    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
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
    formats: list[dict] = []
    for player in players:
        row: list = []

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # バトルダンサー
        row.append(player["combatFeatsLv1bat"])

        # Lv.1
        row.append(player["combatFeatsLv1"])

        # Lv.3
        row.append(player["combatFeatsLv3"])

        # Lv.5
        row.append(player["combatFeatsLv5"])

        # Lv.7
        row.append(player["combatFeatsLv7"])

        # Lv.9
        row.append(player["combatFeatsLv9"])

        # Lv.11
        row.append(player["combatFeatsLv11"])

        # Lv.13
        row.append(player["combatFeatsLv13"])

        # Lv.15
        row.append(player["combatFeatsLv15"])

        # 自動取得
        for autoCombatFeat in player["autoCombatFeats"]:
            row.append(autoCombatFeat)

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

        # PC列のハイパーリンク
        pcIndex: int = headers.index("PC") + 1
        pcTextFormat: dict = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # 習得レベルに満たないものはグレーで表示
        grayOutStartIndex: int = None
        for i in range(3, 15, 2):
            if player["level"] < i:
                grayOutStartIndex = headers.index(f"Lv.{i}") + 1
                break

        if grayOutStartIndex is not None:
            grayOutEndIndex: int = headers.index("Lv.15") + 1
            grayOutTextFormat: dict = DefaultTextFormat.copy()
            grayOutTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}
            }
            startA1: str = utils.rowcol_to_a1(rowIndex, grayOutStartIndex)
            endA1: str = utils.rowcol_to_a1(rowIndex, grayOutEndIndex)
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
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), Sheet.col_count)
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
    endA1: str = utils.rowcol_to_a1(1, len(headers))
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
