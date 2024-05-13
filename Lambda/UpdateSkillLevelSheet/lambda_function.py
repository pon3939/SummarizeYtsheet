# -*- coding: utf-8 -*-

from json import loads

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import Spreadsheet, Worksheet, utils
from myLibrary.CommonFunction import (
    ConvertToVerticalHeader,
    MakeYtsheetUrl,
    OpenSpreadsheet,
)
from myLibrary.Constant import SpreadSheet, SwordWorld
from myLibrary.ExpStatus import ExpStatus
from myLibrary.Player import Player

"""
技能シートを更新
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
    worksheet: Worksheet = spreadsheet.worksheet("技能")

    # 更新
    UpdateSheet(worksheet, players)


def UpdateSheet(worksheet: Worksheet, players: "list[Player]"):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[dict]: プレイヤー情報
    """

    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "信仰",
        "Lv",
        "経験点\nピンゾロ含む",
        "ピンゾロ",
    ]
    for skill in SwordWorld.SKILLS.values():
        headers.append(skill)

    formats: list[dict] = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(SpreadSheet.ENTRY_TREND[character.ActiveStatus])

            # 信仰
            row.append(character.Faith)

            # Lv
            row.append(character.Level)

            # 経験点
            row.append(character.Exp)

            # ピンゾロ
            row.append(character.FumbleExp)

            # 技能レベル
            for skill in SwordWorld.SKILLS:
                row.append(character.Skills.get(skill, ""))

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1

            # 経験点の文字色
            expIndex: int = headers.index("経験点\nピンゾロ含む") + 1
            expTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            if character.ActiveStatus == ExpStatus.MAX:
                expTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 1, "green": 0, "blue": 0}
                }
                formats.append(
                    {
                        "range": utils.rowcol_to_a1(rowIndex, expIndex),
                        "format": {"textFormat": expTextFormat},
                    }
                )
            elif character.ActiveStatus == ExpStatus.INACTIVE:
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
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notSkillColumnCount: int = len(headers) - len(SwordWorld.SKILLS)
    total: list = [None] * notSkillColumnCount
    total[-1] = "合計"
    total += list(
        map(
            lambda x: list(
                map(lambda y: y[headers.index(x)] != "", updateData)
            ).count(True),
            SwordWorld.SKILLS.values(),
        )
    )
    updateData.append(total)

    # ヘッダーを縦書き用に変換
    displayHeader: list[str] = list(
        map(
            lambda x: ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.insert(0, displayHeader)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
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
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )
