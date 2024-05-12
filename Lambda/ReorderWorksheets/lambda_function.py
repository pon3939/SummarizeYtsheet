# -*- coding: utf-8 -*-


from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import Spreadsheet, Worksheet
from myLibrary import CommonFunction

"""
シートを並び替え
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

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = CommonFunction.OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )

    reorderedSheets: list[Worksheet] = []
    reorderedSheets.append(spreadsheet.worksheet("使い方"))
    reorderedSheets.append(spreadsheet.worksheet("グラフ"))
    reorderedSheets.append(spreadsheet.worksheet("基本"))
    reorderedSheets.append(spreadsheet.worksheet("技能"))
    reorderedSheets.append(spreadsheet.worksheet("能力値"))
    reorderedSheets.append(spreadsheet.worksheet("戦闘特技"))
    reorderedSheets.append(spreadsheet.worksheet("名誉点・流派"))
    reorderedSheets.append(spreadsheet.worksheet("アビスカース"))

    # 並び替え
    spreadsheet.reorder_worksheets(reorderedSheets)
