# -*- coding: utf-8 -*-


from boto3 import resource
from google.oauth2 import service_account
from gspread import Client, Spreadsheet, authorize, utils, worksheet
from myLibrary import commonConstant

"""
技能シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

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
    spreadsheetId: str = event["SpreadsheetId"]
    players: list[dict] = event["Players"]
    levelCap: dict = event["LevelCap"]
    maxExp: int = int(levelCap["MaxExp"])
    minimumExp: int = int(levelCap["MinimumExp"])

    # 初期化
    init(spreadsheetId)

    # 更新
    updateSheet(players, maxExp, minimumExp)


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

    # 技能シートを開く
    book: Spreadsheet = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("技能")


def updateSheet(players: "list[dict]", maxExp: int, minimumExp: int):
    """

    シートを更新

    Args:
        players list[dict]: プレイヤー情報
        maxExp int: 経験点の上限
        minimumExp int: 経験点の下限
    """
    global Sheet

    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
        "No.",
        "PC",
        "信仰",
        "Lv",
        "経験点\nピンゾロ含む",
        "ピンゾロ",
    ]
    for skill in commonConstant.SKILLS:
        headers.append(skill["name"])

    # 縦書きの伸ばし棒を置換
    displayHeader: list[str] = list(
        map(
            lambda x: x.replace("ー", "｜"),
            headers,
        )
    )
    updateData.append(displayHeader)

    skillColumnCount: int = len(commonConstant.SKILLS)
    notSkillColumnCount: int = len(headers) - skillColumnCount
    total: list = ([None] * notSkillColumnCount) + ([0] * skillColumnCount)
    formats: list[dict] = []
    for player in players:
        row: list = []

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 信仰
        row.append(player["faith"])

        # Lv
        row.append(player["level"])

        # 経験点
        row.append(player["exp"])

        # ピンゾロ
        row.append(player["fumbleExp"])

        # 技能レベル
        for skill in commonConstant.SKILLS:
            level = player[skill["key"]]
            if level == 0:
                # 技能レベル0は表示しない
                level = ""
            else:
                # 合計を加算
                total[headers.index(skill["name"])] += 1

            row.append(level)

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

        # 経験点の文字色
        expIndex: int = headers.index("経験点\nピンゾロ含む") + 1
        expTextFormat: dict = DefaultTextFormat.copy()
        if player["exp"] >= maxExp:
            expTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 1, "green": 0, "blue": 0}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, expIndex),
                    "format": {"textFormat": expTextFormat},
                }
            )
        elif player["exp"] < minimumExp:
            expTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 0, "green": 0, "blue": 1}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, expIndex),
                    "format": {"textFormat": expTextFormat},
                }
            )

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

    # 合計行
    total[notSkillColumnCount - 1] = "合計"
    updateData.append(total)

    # クリア
    Sheet.clear()

    # 更新
    Sheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
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

    # 技能レベルのヘッダー
    startA1: str = utils.rowcol_to_a1(1, notSkillColumnCount + 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # 部分的なフォーマットを設定
    Sheet.batch_format(formats)

    # 行列の固定
    Sheet.freeze(1, 2)

    # フィルター
    Sheet.set_basic_filter(1, 1, len(updateData) - 1, len(headers))
