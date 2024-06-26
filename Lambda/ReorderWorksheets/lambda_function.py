# -*- coding: utf-8 -*-


from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread.spreadsheet import Spreadsheet
from gspread.worksheet import Worksheet
from MyLibrary.CommonFunction import OpenSpreadsheet

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
    spreadsheet: Spreadsheet = OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )

    reorderedSheets: list[Worksheet] = []
    reorderedSheets.append(spreadsheet.worksheet("使い方"))
    reorderedSheets.append(spreadsheet.worksheet("グラフ"))
    reorderedSheets.append(spreadsheet.worksheet("PL"))
    reorderedSheets.append(spreadsheet.worksheet("基本"))
    reorderedSheets.append(spreadsheet.worksheet("技能"))
    reorderedSheets.append(spreadsheet.worksheet("能力値"))
    reorderedSheets.append(spreadsheet.worksheet("戦闘特技"))
    reorderedSheets.append(spreadsheet.worksheet("名誉点・流派"))
    reorderedSheets.append(spreadsheet.worksheet("アビスカース"))
    reorderedSheets.append(spreadsheet.worksheet("一般技能"))

    # 並び替え
    spreadsheet.reorder_worksheets(reorderedSheets)
