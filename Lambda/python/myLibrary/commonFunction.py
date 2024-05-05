# -*- coding: utf-8 -*-


from datetime import datetime
from functools import singledispatch
from typing import Union

from boto3 import client
from google.oauth2 import service_account
from gspread import Client, Spreadsheet, authorize
from mypy_boto3_dynamodb.client import DynamoDBClient

"""
汎用関数
"""


def InitDb() -> DynamoDBClient:
    """DBに接続する"""

    return client("dynamodb", region_name="ap-northeast-1")


def OpenSpreadsheet(
    googleServiceAccount: dict, spreadsheetId: str
) -> Spreadsheet:
    """

    スプレッドシートを開く

    Args:
        googleServiceAccount str: スプレッドシートの認証情報
        spreadsheetId str: スプレッドシートのID
    """

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client: Client = authorize(credentials)
    return client.open_by_key(spreadsheetId)


def ConvertToVerticalHeader(horizontalHeader: str) -> str:
    """

    ヘッダーを縦書き用の文字に変換する

    Args:
        horizontalHeader str: 横書きヘッダー
    Returns:
        str: 縦書きヘッダー
    """

    return (
        horizontalHeader.replace("ー", "｜")
        .replace("(", "︵")
        .replace(")", "︶")
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
            convertedJson[key] = ConvertDynamoDBToJsonByTypeKey(value)
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


def ConvertDynamoDBToJsonByTypeKey(
    dynamoDBData: dict,
) -> Union[str, float, list, dict]:
    """

    DynamoDBから取得したデータを適切な型に変換する

    Args:
        dynamoDBData dict: DynamoDBから取得したデータ
    Returns:
        Union[str, float, list, dict]: 変換後のJSON
    """

    key = next(iter(dynamoDBData.keys()))
    value = next(iter(dynamoDBData.values()))
    if key == "S":
        # 文字列
        return value
    elif key == "N":
        # 数値
        return float(value)
    elif key == "M":
        # 辞書
        return ConvertDynamoDBToJson(value)
    elif key == "L":
        # リスト
        return list(map(ConvertDynamoDBToJsonByTypeKey, value))

    raise Exception("未対応の型です")


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
        elif isinstance(value, dict):
            # 辞書
            convertedJson[key] = {"M": ConvertJsonToDynamoDB(value)}
        elif isinstance(value, list):
            # 辞書のリスト
            convertedList: list[dict] = []
            for dictionary in value:
                convertedList.append({"M": ConvertJsonToDynamoDB(dictionary)})

            convertedJson[key] = {"L": convertedList}
        else:
            raise Exception("未対応の型です")

    return convertedJson


def GetCurrentDateTimeForDynamoDB() -> str:
    """

    DynamoDBに登録するための現在日時文字列を取得

    Returns:
        str: 現在日時文字列
    """

    return DateTimeToStrForDynamoDB(datetime.now())


def DateTimeToStrForDynamoDB(target: datetime) -> str:
    """

    DynamoDBに登録するための日時文字列を取得

    Returns:
        str: 日時文字列
    """
    gmt = target
    if target.tzinfo is not None:
        gmt = target.astimezone(None).replace(tzinfo=None)

    return f"{gmt.isoformat(timespec='milliseconds')}Z"
