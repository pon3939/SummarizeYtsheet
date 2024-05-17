# -*- coding: utf-8 -*-

from json import loads
from typing import Union

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
from MyLibrary.GeneralSkill import GeneralSkill
from MyLibrary.Player import Player

"""
一般技能シートを更新
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
        map(
            lambda x: Player(**loads(x)),
            event["Players"],
        )
    )

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("一般技能")

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
        "公式技能",
        "オリジナル技能",
    ]
    for officialGeneralSkillName in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES:
        headers.append(officialGeneralSkillName)

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            # 公式一般技能のレベル取得
            officialGeneralSkills: list[GeneralSkill] = list(
                filter(
                    lambda x: x.Name
                    in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES,
                    character.GeneralSkills,
                )
            )
            officialGeneralSkillLevels: list[Union[int, None]] = [None] * len(
                SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES
            )
            for officialGeneralSkill in officialGeneralSkills:
                officialGeneralSkillLevels[
                    SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES.index(
                        officialGeneralSkill.Name
                    )
                ] = officialGeneralSkill.Level

            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 公式技能
            row.append(
                "\n".join([x.getFormattedStr() for x in officialGeneralSkills])
            )

            # オリジナル技能
            row.append(
                "\n".join(
                    [
                        x.getFormattedStr()
                        for x in list(
                            filter(
                                lambda x: x.Name
                                not in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES,
                                character.GeneralSkills,
                            )
                        )
                    ]
                )
            )

            # 公式技能
            row += officialGeneralSkillLevels

            updateData.append(row)

            # PC列のハイパーリンク
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(
                        updateData.index(row) + 1 + 1, headers.index("PC") + 1
                    ),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notTotalColumnCount: int = len(headers) - len(
        SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES
    )
    total: list = [None] * notTotalColumnCount
    total[-1] = "合計"
    for officialGeneralSkillName in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES:
        total.append(
            list(
                map(
                    lambda x: x[headers.index(officialGeneralSkillName)]
                    is not None,
                    updateData,
                )
            ).count(True)
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

    # 縦書きヘッダー
    startA1 = utils.rowcol_to_a1(1, notTotalColumnCount + 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # ヘッダー以外
    startA1 = utils.rowcol_to_a1(2, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"verticalAlignment": "MIDDLE"},
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
