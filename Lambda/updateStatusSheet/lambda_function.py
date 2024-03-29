# -*- coding: utf-8 -*-


from re import sub

from gspread import Spreadsheet, Worksheet, utils
from myLibrary import commonConstant, commonFunction, expStatus

"""
能力値シートを更新
"""

# ダイスの期待値
DICE_EXPECTED_VALUE: float = 3.5

# 初期作成時に振るダイスの数と能力増加分
RACES_STATUSES: dict = {
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
    "スプリガン": {"diceCount": 8, "fixedValue": 0},
    "アビスボーン": {"diceCount": 9, "fixedValue": 6},
    "ハイマン": {"diceCount": 8, "fixedValue": 0},
    "フロウライト": {"diceCount": 11, "fixedValue": 12},
    "ダークドワーフ": {"diceCount": 9, "fixedValue": 12},
}


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    environment: dict = event["Environment"]
    spreadsheetId: str = environment["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: list[dict] = event["Players"]

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = commonFunction.OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("能力値")

    # 更新
    UpdateSheet(worksheet, players)


def UpdateSheet(worksheet: Worksheet, players: "list[dict]"):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[Player]: プレイヤー情報
    """

    updateData: list[list] = []

    # ヘッダー
    header: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "種族",
    ]
    statusHeaders: list[str] = []
    for statusKey in commonConstant.STATUS_KEYS:
        statusName: str = statusKey["name"]
        statusHeaders.append(statusName)
    header.extend(statusHeaders)
    header.extend(
        [
            "成長",
            "HP",
            "MP",
            "生命抵抗力",
            "精神抵抗力",
            "魔物知識",
            "先制力",
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
        for statusKey in commonConstant.STATUS_KEYS:
            status: dict = player[statusKey["key"]]
            htb: int = player[statusKey["htb"]]
            baseStatus: int = htb + status["baseStatus"]
            statusPoint: int = baseStatus + status["increasedStatus"]
            statusPoint += status["additionalStatus"]
            expectedHtb += htb
            totalBaseStatus += baseStatus
            statuses.append(statusPoint)

        # 初期能力期待値を計算
        isAdventurer: bool = player["birth"] == "冒険者"
        if isAdventurer:
            expectedHtb = int(DICE_EXPECTED_VALUE * 2 * 6)

        race: str = player["race"]

        # 希少種とナイトメアの種族名は整形
        racesStatus: dict = RACES_STATUSES[sub("（.*", "", race)]

        # No.
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 参加傾向
        row.append(
            commonConstant.ENTRY_TREND_INACTIVE
            if player["expStatus"] == expStatus.ExpStatus.INACTIVE
            else commonConstant.ENTRY_TREND_ACTIVE
        )

        # 種族
        row.append(race)

        # 各能力値
        row.extend(statuses)

        # 成長
        row.append(player["growthTimes"])

        # HP
        row.append(player["hp"])

        # MP
        row.append(player["mp"])

        # 生命抵抗力
        row.append(player["lifeResistance"])

        # 精神抵抗力
        row.append(player["spiritResistance"])

        # 魔物知識
        row.append(player["monsterKnowledge"])

        # 先制力
        row.append(player["initiative"])

        # ダイス平均
        diceAverage: float = (
            totalBaseStatus - expectedHtb - racesStatus["fixedValue"]
        ) / racesStatus["diceCount"]
        row.append(diceAverage)

        # 備考
        if isAdventurer:
            row.append("※冒険者")

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

        # PC列のハイパーリンク
        pcIndex: int = header.index("PC") + 1
        pcTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
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
            diceAverageTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
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
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        commonConstant.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": commonConstant.HEADER_DEFAULT_FORMAT,
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
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(1, 1, len(updateData), len(header))  # type: ignore
