# -*- coding: utf-8 -*-


from json import loads

from boto3 import resource
from google.oauth2 import service_account
from gspread import authorize, utils, worksheet

"""
能力値シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# ダイスの期待値
DICE_EXPECTED_VALUE: float = 3.5

# DBコネクション
Dynamodb = None

# 能力値シート
Sheet: worksheet = None

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

    # 能力値シートを開く
    book = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("能力値")


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

    # ゆとシートから取得したJSONのキーのうち、各能力値に関係するもの
    statusKeys = [
        # 器用
        {
            "htb": "sttBaseTec",
            "baseStatus": "sttBaseA",
            "increasedStatus": "sttGrowA",
            "additionalStatus": "sttAddA",
        },
        # 敏捷
        {
            "htb": "sttBaseTec",
            "baseStatus": "sttBaseB",
            "increasedStatus": "sttGrowB",
            "additionalStatus": "sttAddB",
        },
        # 筋力
        {
            "htb": "sttBasePhy",
            "baseStatus": "sttBaseC",
            "increasedStatus": "sttGrowC",
            "additionalStatus": "sttAddC",
        },
        # 生命力
        {
            "htb": "sttBasePhy",
            "baseStatus": "sttBaseD",
            "increasedStatus": "sttGrowD",
            "additionalStatus": "sttAddD",
        },
        # 知力
        {
            "htb": "sttBaseSpi",
            "baseStatus": "sttBaseE",
            "increasedStatus": "sttGrowE",
            "additionalStatus": "sttAddE",
        },
        # 精神力
        {
            "htb": "sttBaseSpi",
            "baseStatus": "sttBaseF",
            "increasedStatus": "sttGrowF",
            "additionalStatus": "sttAddF",
        },
    ]

    # 初期作成時に振るダイスの数と能力増加分
    racesStatuses = {
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

    updateData = []

    # ヘッダー
    header = [
        "No.",
        "PC",
        "種族",
        "器用",
        "敏捷",
        "筋力",
        "生命",
        "知力",
        "精神",
        "器用詳細",
        "敏捷詳細",
        "筋力詳細",
        "生命詳細",
        "知力詳細",
        "精神詳細",
        "成長",
        "初期能力値合計",
        "初期能力期待値",
        "期待値との差",
        "初期作成時に振る\nダイスの数",
        "初期能力固定値分",
        "ダイス平均",
        "備考",
    ]
    updateData.append(header)

    formats = []
    for player in players:
        row = []
        ytsheetJson = loads(player["ytsheetJson"])

        # 各能力値を集計
        expectedHtb = 0
        totalBaseStatus = 0
        statuses = []
        statusTexts = []
        for statusKey in statusKeys:
            htb = int(ytsheetJson.get(statusKey["htb"], "0"))
            baseStatus = htb + int(
                ytsheetJson.get(statusKey["baseStatus"], "0")
            )
            increasedStatus = int(
                ytsheetJson.get(statusKey["increasedStatus"], "0")
            )
            additionalStatus = int(
                ytsheetJson.get(statusKey["additionalStatus"], "0")
            )
            status = baseStatus + increasedStatus
            statusText = f"{baseStatus}+{increasedStatus}"
            if additionalStatus > 0:
                # 増強分が存在する場合のみ詳細に表示する
                status += additionalStatus
                statusText += f"+{additionalStatus}"
            expectedHtb += htb
            totalBaseStatus += baseStatus
            statuses.append(status)
            statusTexts.append(statusText)

        # 初期能力期待値を計算
        isAdventurer = ytsheetJson.get("birth") == "冒険者"
        if isAdventurer:
            expectedHtb = DICE_EXPECTED_VALUE * 2 * 6

        race = ytsheetJson.get("race")
        raceKey = race
        if "ナイトメア" in raceKey:
            raceKey = "ナイトメア"
        elif "ウィークリング" in raceKey:
            raceKey = "ウィークリング"

        racesStatus = racesStatuses[raceKey]
        expectedStatus = (
            expectedHtb
            + DICE_EXPECTED_VALUE * racesStatus["diceCount"]
            + racesStatus["fixedValue"]
        )

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(int(player["id"]))

        # PC
        row.append(ytsheetJson["characterName"])

        # 種族
        row.append(race)

        # 各能力値
        row.extend(statuses)
        row.extend(statusTexts)

        # 成長
        row.append(ytsheetJson.get("historyGrowTotal", 0))

        # 初期能力値合計
        row.append(totalBaseStatus)

        # 初期能力期待値
        row.append(expectedStatus)

        # 期待値との差
        row.append(totalBaseStatus - expectedStatus)

        # 初期作成時に振るダイスの数
        row.append(racesStatus["diceCount"])

        # 初期能力固定値分
        fixedStatus = expectedHtb + racesStatus["fixedValue"]
        row.append(fixedStatus)

        # ダイス平均
        diceAverage = (totalBaseStatus - fixedStatus) / racesStatus[
            "diceCount"
        ]
        row.append(diceAverage)

        # 備考
        if isAdventurer:
            row.append("※冒険者")

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

        # ダイス平均4.5を超える場合は赤文字
        if diceAverage > 4.5:
            diceAverageIndex = row.index(diceAverage) + 1
            rowIndex = updateData.index(row) + 1
            diceAverageTextFormat = DefaultTextFormat.copy()
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

    # ダイス平均
    diceAverageIndex = header.index("ダイス平均") + 1
    startA1 = utils.rowcol_to_a1(1, diceAverageIndex)
    endA1 = utils.rowcol_to_a1(len(updateData), diceAverageIndex)
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
