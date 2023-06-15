# -*- coding: utf-8 -*-


from google.oauth2 import service_account
from gspread import Client, Spreadsheet, Worksheet, authorize

"""
汎用関数
"""


def openSpreadsheet(
    googleServiceAccount: dict, spreadsheetId: str, worksheetName: str
) -> Worksheet:
    """

    スプレッドシートを開く

    Args:
        googleServiceAccount str: スプレッドシートの認証情報
        spreadsheetId str: スプレッドシートのID
        worksheetName str: シートの名前
    """
    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client: Client = authorize(credentials)

    # 基本シートを開く
    book: Spreadsheet = client.open_by_key(spreadsheetId)
    return book.worksheet(worksheetName)
