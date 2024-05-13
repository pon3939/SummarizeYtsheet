# -*- coding: utf-8 -*-

from json import loads

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import Spreadsheet, Worksheet, utils
from myLibrary.CommonFunction import MakeYtsheetUrl, OpenSpreadsheet
from myLibrary.Constant import SpreadSheet, SwordWorld
from myLibrary.Player import Player

"""
アビスカースシートを更新
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
    worksheet: Worksheet = spreadsheet.worksheet("アビスカース")

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
        "アビスカースの数",
    ]
    for abyssCurse in SwordWorld.ABYSS_CURSES:
        headers.append(abyssCurse)

    notTotalColumnCount: int = 3
    totalColumnCount: int = len(headers) - notTotalColumnCount
    formats: "list[dict]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # アビスカースの情報を取得
            receivedCurses: list[str] = []
            receivedCursesString: str = ""
            for abyssCurse in SwordWorld.ABYSS_CURSES:
                receivedCurse: str = ""
                if abyssCurse in character.AbyssCurses:
                    receivedCurse = SpreadSheet.TRUE_STRING
                    receivedCursesString += abyssCurse

                receivedCurses.append(receivedCurse)

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(receivedCursesString + character.Name)

            # 参加傾向
            row.append(SpreadSheet.ENTRY_TREND[character.ActiveStatus])

            # 数
            cursesCount: int = receivedCurses.count(SpreadSheet.TRUE_STRING)
            row.append(cursesCount)

            # 各アビスカース
            row += receivedCurses

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    total: list = ([None] * notTotalColumnCount) + ([0] * totalColumnCount)
    total[notTotalColumnCount - 1] = "合計"
    totalIndex: int = headers.index("アビスカースの数")
    total[totalIndex] = sum(
        list(
            map(
                lambda x: x[totalIndex],
                updateData,
            )
        )
    )
    for abyssCurse in SwordWorld.ABYSS_CURSES:
        index: int = headers.index(abyssCurse)
        total[index] = list(map(lambda x: x[index], updateData)).count(
            SpreadSheet.TRUE_STRING
        )

    updateData.append(total)

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

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )
