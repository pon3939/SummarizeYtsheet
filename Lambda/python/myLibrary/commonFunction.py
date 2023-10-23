# -*- coding: utf-8 -*-


from functools import singledispatch

from google.oauth2 import service_account
from gspread import Client, Spreadsheet, Worksheet, authorize

"""
汎用関数
"""


def OpenSpreadsheet(
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


def ConvertToVerticalHeader(horizontalHeader: str) -> str:
    """

    ヘッダーを縦書き用の文字に変換する

    Args:
        horizontalHeader str: 横書きヘッダー
    Returns:
        str: 縦書きヘッダー
    """

    return (
        horizontalHeader.replace("ー", "｜").replace("(", "︵").replace(")", "︶")
    )


@singledispatch
def ConvertDynamoDBToJson(dynamoDBData):
    """

    DynamoDBから取得したデータを適切な型に変換する
    未対応の型の場合、例外を発生させる

    Args:
        dynamoDBData: DynamoDBから取得したデータ
    """
    raise Exception("未対応の型です")


@ConvertDynamoDBToJson.register
def _(dynamoDBData: dict) -> dict:
    """

    DynamoDBから取得したデータを適切な型に変換する

    Args:
        dynamoDBData dict: DynamoDBから取得したデータ
    Returns:
        dict: 変換後のJSON
    """

    convertedJson: dict = {}
    for key, value in dynamoDBData.items():
        if isinstance(value, dict):
            # 適切な型に変換する
            valuesKey = next(iter(value.keys()))
            valuesValue = next(iter(value.values()))
            if valuesKey == "S":
                # 文字列
                convertedJson[key] = valuesValue
            elif valuesKey == "N":
                # 数値
                convertedJson[key] = float(valuesValue)
            else:
                raise Exception("未対応の型です")

        elif isinstance(value, list):
            # 各要素を再度変換する
            convertedJson[key] = ConvertDynamoDBToJson(value)

        else:
            raise Exception("未対応の型です")

    return convertedJson


@ConvertDynamoDBToJson.register
def _(dynamoDBData: list) -> list:
    """

    DynamoDBから取得したデータを適切な型に変換する

    Args:
        dynamoDBData list: DynamoDBから取得したデータ
    Returns:
        list: 変換後のJSON
    """
    return list(map(ConvertDynamoDBToJson, dynamoDBData))


def ConvertJsonToDynamoDB(json: dict) -> dict:
    """

    データをDynamoDBで扱える型に変換する

    Args:
        json dict: 変換するデータ
    Returns:
        dict: 変換後のデータ
    """
    convertedJson: dict = {}
    for key, value in json.items():
        # 適切な型に変換する
        if isinstance(value, str):
            # 文字列
            convertedJson[key] = {"S": value}
        elif isinstance(value, (int, float)):
            # 数値
            convertedJson[key] = {"N": str(value)}
        else:
            raise Exception("未対応の型です")

    return convertedJson
