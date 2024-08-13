# -*- coding: utf-8 -*-

from json import loads

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import utils
from gspread.spreadsheet import Spreadsheet
from gspread.utils import ValueInputOption
from gspread.worksheet import CellFormat, Worksheet
from MyLibrary.CommonFunction import MakeYtsheetUrl, OpenSpreadsheet
from MyLibrary.Constant import SpreadSheet
from MyLibrary.Player import Player

"""
PLシートを更新
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
    worksheet: Worksheet = spreadsheet.worksheet("PL")

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
    header: "list[str]" = [
        "No.",
        "PL",
        "参加傾向",
        "1人目",
        "2人目",
        "参加",
        "GM",
        "参加+GM",
        "更新日時",
    ]
    subPcIndex: int = header.index("2人目")

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        row: list = []

        # No.
        no += 1
        row.append(no)

        # PL
        row.append(player.Name)

        # 参加傾向
        row.append(
            max(
                list(
                    map(
                        lambda x: x.ActiveStatus.GetStrForSpreadsheet(),
                        player.Characters,
                    )
                )
            )
        )

        # 1人目
        row.append(player.Characters[0].Name)

        # 2人目
        subPcName: str = (
            player.Characters[1].Name if len(player.Characters) > 1 else ""
        )
        row.append(subPcName)

        # 参加
        playerTimes: int = sum(
            list(map(lambda x: x.PlayerTimes, player.Characters))
        )
        row.append(playerTimes)

        # GM
        gameMasterTimes: int = max(
            list(map(lambda x: x.GameMasterTimes, player.Characters))
        )
        row.append(gameMasterTimes)

        # 参加+GM
        row.append(playerTimes + gameMasterTimes)

        # 更新日時
        row.append(player.UpdateTime)

        updateData.append(row)

        # 1人目列のハイパーリンク
        mainPcIndex: int = header.index("1人目") + 1
        rowIndex: int = updateData.index(row) + 1 + 1
        mainPcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
        mainPcTextFormat["link"] = {
            "uri": MakeYtsheetUrl(player.Characters[0].YtsheetId)
        }
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, mainPcIndex),
                "format": {"textFormat": mainPcTextFormat},
            }
        )

        # 2人目列のハイパーリンク
        if len(player.Characters) > 1:
            subPcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            subPcTextFormat["link"] = {
                "uri": MakeYtsheetUrl(player.Characters[1].YtsheetId)
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, subPcIndex + 1),
                    "format": {"textFormat": subPcTextFormat},
                }
            )

    # 合計行
    total: list = [None] * len(header)
    activeCountIndex: int = header.index("参加傾向")
    total[activeCountIndex - 1] = "合計"
    total[activeCountIndex] = list(
        map(lambda x: x[activeCountIndex], updateData)
    ).count(SpreadSheet.ACTIVE_STRING)

    total[subPcIndex] = list(
        map(lambda x: x[subPcIndex] != "", updateData)
    ).count(True)

    updateData.append(total)

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
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(header))
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
        1, 1, len(updateData) - 1, len(header)  # type: ignore
    )
