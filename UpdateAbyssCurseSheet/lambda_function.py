# -*- coding: utf-8 -*-

from gspread import Worksheet, utils
from myLibrary import commonConstant, commonFunction

"""
アビスカースシートを更新
"""


# アビスカースを持っている時に表示する文字列
TRUE_STRING: str = "○"


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId: str = event["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: "list[dict]" = event["Players"]

    # スプレッドシートを開く
    worksheet: Worksheet = commonFunction.openSpreadsheet(
        googleServiceAccount, spreadsheetId, "アビスカース"
    )

    # 更新
    updateSheet(worksheet, players)


def updateSheet(worksheet: Worksheet, players: "list[dict]"):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[dict]: プレイヤー情報
    """

    updateData: list[list] = []

    # ヘッダー
    headers: "list[str]" = [
        "No.",
        "PC",
        "アビスカースの数",
    ]
    for abyssCurse in commonConstant.ABYSS_CURSES:
        headers.append(abyssCurse)

    updateData.append(headers)

    notTotalColumnCount: int = 2
    totalColumnCount: int = len(headers) - notTotalColumnCount
    total: list = ([None] * notTotalColumnCount) + ([0] * totalColumnCount)
    formats: "list[dict]" = []
    for player in players:
        row: list = []

        # アビスカースの情報を取得
        receivedCurses: list[str] = []
        receivedCursesString: str = ""
        for abyssCurse in commonConstant.ABYSS_CURSES:
            receivedCurse: str = ""
            if abyssCurse in player["abyssCurses"]:
                receivedCurse = TRUE_STRING
                receivedCursesString += abyssCurse
                total[headers.index(abyssCurse)] += 1

            receivedCurses.append(receivedCurse)

        # No.
        row.append(player["no"])

        # PC
        row.append(receivedCursesString + player["characterName"])

        # 数
        cursesCount: int = receivedCurses.count(TRUE_STRING)
        total[headers.index("アビスカースの数")] += cursesCount
        row.append(cursesCount)

        # 各アビスカース
        row.extend(receivedCurses)

        updateData.append(row)

        # PC列のハイパーリンク
        pcIndex: int = headers.index("PC") + 1
        rowIndex: int = updateData.index(row) + 1
        pcTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

    # 合計行
    total[notTotalColumnCount - 1] = "合計"
    updateData.append(total)

    # クリア
    worksheet.clear()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        commonConstant.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": commonConstant.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(1, 1, len(updateData) - 1, len(headers))
