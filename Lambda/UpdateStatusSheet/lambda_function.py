# -*- coding: utf-8 -*-


from json import loads
from re import sub

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import utils
from gspread.spreadsheet import Spreadsheet
from gspread.utils import ValueInputOption
from gspread.worksheet import CellFormat, Worksheet
from MyLibrary.CommonFunction import MakeYtsheetUrl, OpenSpreadsheet
from MyLibrary.Constant import SpreadSheet
from MyLibrary.Player import Player

"""
能力値シートを更新
"""

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
    "ディアボロ": {"diceCount": 10, "fixedValue": 12},
    "ドレイク": {"diceCount": 10, "fixedValue": 6},
    "バジリスク": {"diceCount": 9, "fixedValue": 6},
    "ダークトロール": {"diceCount": 10, "fixedValue": 6},
    "アルボル": {"diceCount": 10, "fixedValue": 3},
    "バーバヤガー": {"diceCount": 8, "fixedValue": 6},
    "ケンタウロス": {"diceCount": 10, "fixedValue": 6},
    "シザースコーピオン": {"diceCount": 10, "fixedValue": 6},
    "ドーン": {"diceCount": 10, "fixedValue": 6},
    "コボルド": {"diceCount": 10, "fixedValue": 0},
}


def lambda_handler(event: dict, context: LambdaContext):
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId: str = event["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: "list[Player]" = list(
        map(lambda x: Player(**loads(x)), event["Players"])
    )

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("能力値")

    # 更新
    UpdateSheet(worksheet, players)


def UpdateSheet(worksheet: Worksheet, players: "list[Player]"):
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
        "器用",
        "敏捷",
        "筋力",
        "生命",
        "知力",
        "精神",
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

    formats: list[CellFormat] = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # ダイス平均を計算
            racesStatus: dict = RACES_STATUSES[sub("（.*", "", character.Race)]
            diceAverage: float = (
                character.Dexterity.Base
                + character.Agility.Base
                + character.Strength.Base
                + character.Vitality.Base
                + character.Intelligence.Base
                + character.Mental.Base
                - racesStatus["fixedValue"]
            ) / racesStatus["diceCount"]

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 種族
            row.append(character.Race)

            # 器用
            row.append(
                character.Technic + character.Dexterity.GetTotalStatus()
            )

            # 敏捷
            row.append(character.Technic + character.Agility.GetTotalStatus())

            # 筋力
            row.append(
                character.Physical + character.Strength.GetTotalStatus()
            )

            # 生命
            row.append(
                character.Physical + character.Vitality.GetTotalStatus()
            )

            # 知力
            row.append(
                character.Spirit + character.Intelligence.GetTotalStatus()
            )

            # 精神
            row.append(character.Spirit + character.Mental.GetTotalStatus())

            # 成長
            row.append(character.GrowthTimes)

            # HP
            row.append(character.Hp)

            # MP
            row.append(character.Mp)

            # 生命抵抗力
            row.append(character.LifeResistance)

            # 精神抵抗力
            row.append(character.SpiritResistance)

            # 魔物知識
            row.append(character.MonsterKnowledge)

            # 先制力
            row.append(character.Initiative)

            # ダイス平均
            row.append(diceAverage)

            # 備考
            if character.Birth == "冒険者":
                row.append("※冒険者")

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1 + 1

            # PC列のハイパーリンク
            pcIndex: int = header.index("PC") + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

            # ダイス平均4.5を超える場合は赤文字
            if diceAverage > 4.5:
                diceAverageIndex: int = header.index("ダイス平均") + 1
                diceAverageTextFormat: dict = (
                    SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
                )
                diceAverageTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 1, "green": 0, "blue": 0}
                }
                formats.append(
                    {
                        "range": utils.rowcol_to_a1(
                            rowIndex, diceAverageIndex
                        ),
                        "format": {"textFormat": diceAverageTextFormat},
                    }
                )

    # ヘッダーを追加
    updateData.insert(0, header)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
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
    worksheet.set_basic_filter(
        1, 1, len(updateData), len(header)  # type: ignore
    )
