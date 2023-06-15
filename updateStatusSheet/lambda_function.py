# -*- coding: utf-8 -*-


from boto3 import resource
from google.oauth2 import service_account
from gspread import Client, Spreadsheet, authorize, utils, worksheet
from myLibrary import commonConstant

"""
能力値シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# ダイスの期待値
DICE_EXPECTED_VALUE: float = 3.5

# 能力値シート
Sheet: worksheet = None

# シート全体に適用するテキストの書式
DefaultTextFormat: dict = {
    "fontFamily": "Meiryo",
}

# 初期作成時に振るダイスの数と能力増加分
RACES_STATUSES: "list[dict]" = {
    "人間": {"diceCount": 12, "fixedValue": 0},
    "エルフ": {"diceCount": 11, "fixedValue": 0},
    "ドワーフ": {"diceCount": 10, "fixedValue": 12},
    "タビット": {"diceCount": 9, "fixedValue": 6},
    "ルーンフォーク": {"diceCount": 10, "fixedValue": 0},
    "ナイトメア": {"diceCount": 10, "fixedValue": 0},
    "リカント": {"diceCount": 8, "fixedValue": 9},
    "リルドラケン": {"diceCount": 10, "fixedValue": 6},
    "グラスランナー": {"diceCount": 10, "fixedValue": 12},
    "メリア": {"diceCount": 7, "fixedValue": 6},
    "ティエンス": {"diceCount": 10, "fixedValue": 6},
    "レプラカーン": {"diceCount": 11, "fixedValue": 0},
    "ウィークリング": {"diceCount": 12, "fixedValue": 3},
    "ソレイユ": {"diceCount": 9, "fixedValue": 6},
    "アルヴ": {"diceCount": 8, "fixedValue": 12},
    "シャドウ": {"diceCount": 10, "fixedValue": 0},
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

    # 能力値シートを開く
    book: Spreadsheet = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("能力値")


def updateSheet(players: "list[dict]"):
    """

    シートを更新

    Args:
        players list[Player]: プレイヤー情報
    """
    global Sheet

    updateData: list[list] = []

    # ヘッダー
    header: list[str] = [
        "No.",
        "PC",
        "種族",
    ]
    statuseHeaders: list[str] = []
    statuseDetailHeaders: list[str] = []
    for statusKey in commonConstant.STATUS_KEYS:
        statusName: str = statusKey["name"]
        statuseHeaders.append(statusName)
        statuseDetailHeaders.append(statusName + "詳細")
    header.extend(statuseHeaders)
    header.extend(statuseDetailHeaders)
    header.extend(
        [
            "成長",
            "初期能力値合計",
            "初期能力期待値",
            "期待値との差",
            "初期作成時に振る\nダイスの数",
            "初期能力固定値分",
            "ダイス平均",
            "備考",
        ]
    )
    updateData.append(header)

    formats: list[dict] = []
    for player in players:
        row: list = []

        # 各能力値を集計
        expectedHtb: int = 0
        totalBaseStatus: int = 0
        statuses: list[int] = []
        statusTexts: list[str] = []
        for statusKey in commonConstant.STATUS_KEYS:
            status: dict = player[statusKey["key"]]
            baseStatus: int = status["htb"] + status["baseStatus"]
            statusPoint: int = baseStatus + status["increasedStatus"]
            statusText: str = f'{baseStatus}+{status["increasedStatus"]}'
            if status["additionalStatus"] > 0:
                # 増強分が存在する場合のみ詳細に表示する
                statusPoint += status["additionalStatus"]
                statusText += f'+{status["additionalStatus"]}'
            expectedHtb += status["htb"]
            totalBaseStatus += baseStatus
            statuses.append(statusPoint)
            statusTexts.append(statusText)

        # 初期能力期待値を計算
        isAdventurer: bool = player["birth"] == "冒険者"
        if isAdventurer:
            expectedHtb = DICE_EXPECTED_VALUE * 2 * 6

        race: str = player["race"]
        raceKey: str = race
        if "ナイトメア" in raceKey:
            raceKey = "ナイトメア"
        elif "ウィークリング" in raceKey:
            raceKey = "ウィークリング"

        racesStatus: dict = RACES_STATUSES[raceKey]
        expectedStatus: int = (
            expectedHtb
            + DICE_EXPECTED_VALUE * racesStatus["diceCount"]
            + racesStatus["fixedValue"]
        )

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 種族
        row.append(race)

        # 各能力値
        row.extend(statuses)
        row.extend(statusTexts)

        # 成長
        row.append(player["growthTimes"])

        # 初期能力値合計
        row.append(totalBaseStatus)

        # 初期能力期待値
        row.append(expectedStatus)

        # 期待値との差
        row.append(totalBaseStatus - expectedStatus)

        # 初期作成時に振るダイスの数
        row.append(racesStatus["diceCount"])

        # 初期能力固定値分
        fixedStatus: int = expectedHtb + racesStatus["fixedValue"]
        row.append(fixedStatus)

        # ダイス平均
        diceAverage: float = (totalBaseStatus - fixedStatus) / racesStatus[
            "diceCount"
        ]
        row.append(diceAverage)

        # 備考
        if isAdventurer:
            row.append("※冒険者")

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

        # PC列のハイパーリンク
        pcIndex: int = header.index("PC") + 1
        pcTextFormat: dict = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # ダイス平均4.5を超える場合は赤文字
        if diceAverage > 4.5:
            diceAverageIndex: int = header.index("ダイス平均") + 1
            diceAverageTextFormat: dict = DefaultTextFormat.copy()
            diceAverageTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 1, "green": 0, "blue": 0}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, diceAverageIndex),
                    "format": {"textFormat": diceAverageTextFormat},
                }
            )

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

    # ダイス平均
    diceAverageIndex: int = header.index("ダイス平均") + 1
    startA1: str = utils.rowcol_to_a1(1, diceAverageIndex)
    endA1: str = utils.rowcol_to_a1(len(updateData), diceAverageIndex)
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}},
        }
    )

    # 部分的なフォーマットを設定
    Sheet.batch_format(formats)

    # 行列の固定
    Sheet.freeze(1, 2)

    # フィルター
    Sheet.set_basic_filter(1, 1, len(updateData), len(header))
