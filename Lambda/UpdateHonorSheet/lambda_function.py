# -*- coding: utf-8 -*-

from json import loads

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import utils
from gspread.spreadsheet import Spreadsheet
from gspread.utils import ValueInputOption
from gspread.worksheet import CellFormat, Worksheet
from MyLibrary.CommonFunction import (
    ConvertToVerticalHeader,
    MakeYtsheetUrl,
    OpenSpreadsheet,
)
from MyLibrary.Constant import SpreadSheet, SwordWorld
from MyLibrary.Player import Player

"""
名誉点・流派シートを更新
"""


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
    worksheet: Worksheet = spreadsheet.worksheet("名誉点・流派")

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
    headers: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "冒険者ランク",
        "累計名誉点",
        "加入数",
        "未加入",
        "2.0流派",
    ]
    for style in SwordWorld.STYLES:
        headers.append(style.Name)

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # 流派の情報を取得
            is20: bool = False
            learnedStyles: list[str] = []
            for style in SwordWorld.STYLES:
                learnedStyle: str = ""
                if style in character.Styles:
                    # 該当する流派に入門している
                    learnedStyle = SpreadSheet.TRUE_STRING
                    if style.Is20:
                        is20 = True

                learnedStyles.append(learnedStyle)

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 冒険者ランク
            row.append(character.AdventurerRank)

            # 累計名誉点
            row.append(character.TotalHonor)

            # 加入数
            learningCount: int = learnedStyles.count(SpreadSheet.TRUE_STRING)
            row.append(learningCount)

            # 未加入
            row.append(SpreadSheet.TRUE_STRING if learningCount == 0 else "")

            # 2.0流派
            row.append(SpreadSheet.TRUE_STRING if is20 else "")

            # 各流派
            row += learnedStyles

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1 + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notTotalColumnCount: int = 5
    total: list = [None] * notTotalColumnCount
    total[-1] = "合計"
    total.append(
        sum(
            list(
                map(
                    lambda x: (x[headers.index("加入数")]),
                    updateData,
                )
            )
        )
    )
    total.append(
        list(map(lambda x: x[headers.index("未加入")], updateData)).count(
            SpreadSheet.TRUE_STRING
        )
    )
    total.append(
        list(map(lambda x: x[headers.index("2.0流派")], updateData)).count(
            SpreadSheet.TRUE_STRING
        )
    )

    # 各流派
    total += list(
        map(
            lambda x: list(
                map(lambda y: y[headers.index(x.Name)], updateData)
            ).count(SpreadSheet.TRUE_STRING),
            SwordWorld.STYLES,
        )
    )
    updateData.append(total)

    # ヘッダーを追加
    displayHeaders: list[str] = list(
        map(
            lambda x: ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.insert(0, displayHeaders)

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
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 流派のヘッダー
    startA1 = utils.rowcol_to_a1(1, notTotalColumnCount + 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # ○
    startA1 = utils.rowcol_to_a1(2, headers.index("未加入") + 1)
    endA1: str = utils.rowcol_to_a1(len(updateData) - 1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"horizontalAlignment": "CENTER"},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )
