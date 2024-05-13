# -*- coding: utf-8 -*-


from json import loads
from typing import Union

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import Spreadsheet, Worksheet, utils
from myLibrary.CommonFunction import MakeYtsheetUrl, OpenSpreadsheet
from myLibrary.Constant import SpreadSheet
from myLibrary.Player import Player

"""
戦闘特技シートを更新
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
    worksheet: Worksheet = spreadsheet.worksheet("戦闘特技")

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
    headers: list[str] = [
        "No.",
        "PC",
        "参加傾向",
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

            # バトルダンサー
            row.append(character.CombatFeatsLv1bat)

            # Lv.1
            row.append(character.CombatFeatsLv1)

            # Lv.3
            row.append(character.CombatFeatsLv3)

            # Lv.5
            row.append(character.CombatFeatsLv5)

            # Lv.7
            row.append(character.CombatFeatsLv7)

            # Lv.9
            row.append(character.CombatFeatsLv9)

            # Lv.11
            row.append(character.CombatFeatsLv11)

            # Lv.13
            row.append(character.CombatFeatsLv13)

            # Lv.15
            row.append(character.CombatFeatsLv15)

            # 自動取得
            for autoCombatFeat in character.AutoCombatFeats:
                row.append(autoCombatFeat)

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1

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

            # 習得レベルに満たないものはグレーで表示
            grayOutStartIndex: Union[int, None] = None
            for level in range(3, 15, 2):
                if character.Level < level:
                    grayOutStartIndex = headers.index(f"Lv.{level}") + 1
                    break

            if grayOutStartIndex is not None:
                grayOutEndIndex: int = headers.index("Lv.15") + 1
                grayOutTextFormat: dict = (
                    SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
                )
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

                # バトルダンサー未習得もグレーで表示
                if character.Skills.get("lvBat", 0) == 0:
                    battleDancerIndex: int = (
                        headers.index("バトルダンサー") + 1
                    )
                    battleDancerA1: str = utils.rowcol_to_a1(
                        rowIndex, battleDancerIndex
                    )
                    formats.append(
                        {
                            "range": f"{battleDancerA1}:{battleDancerA1}",
                            "format": {"textFormat": grayOutTextFormat},
                        }
                    )

    # ヘッダーを追加
    updateData.insert(0, headers)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), worksheet.col_count)
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

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData), worksheet.col_count  # type: ignore
    )
