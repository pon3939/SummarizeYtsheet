# -*- coding: utf-8 -*-


from datetime import datetime
from functools import singledispatch
from typing import Union

from boto3 import client
from mypy_boto3_dynamodb.client import DynamoDBClient
from pytz import timezone

"""
汎用関数
"""


def InitDb() -> DynamoDBClient:
    """DBに接続する"""

    return client("dynamodb", region_name="ap-northeast-1")


def ConvertToVerticalHeaders(horizontalHeaders: list[str]) -> list[str]:
    """

    ヘッダーを縦書き用の文字に変換する

    Args:
        horizontalHeader list[str]: 横書きヘッダー
    Returns:
        list[str]: 縦書きヘッダー
    """

    return list(
        map(
            lambda x: x.replace("ー", "｜")
            .replace("(", "︵")
            .replace(")", "︶"),
            horizontalHeaders,
        )
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


@ConvertDynamoDBToJson.register  # type: ignore
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
            convertedJson[key] = _ConvertDynamoDBToJsonByTypeKey(value)
        else:
            raise Exception("未対応の型です")

    return convertedJson


@ConvertDynamoDBToJson.register  # type: ignore
def _(dynamoDBData: list) -> list:
    """

    DynamoDBから取得したデータを適切な型に変換する

    Args:
        dynamoDBData list: DynamoDBから取得したデータ
    Returns:
        list: 変換後のJSON
    """
    return list(map(ConvertDynamoDBToJson, dynamoDBData))


def _ConvertDynamoDBToJsonByTypeKey(
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
        return list(map(_ConvertDynamoDBToJsonByTypeKey, value))

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
        convertedJson[key] = _ConvertJsonToDynamoDBByTypeKey(value)

    return convertedJson


def _ConvertJsonToDynamoDBByTypeKey(
    value: Union[str, int, float, dict, list]
) -> dict:
    """

    データをDynamoDBで扱える型に変換する

    Args:
        json dict: 変換するデータ
    Returns:
        dict: 変換後のデータ
    """
    # 適切な型に変換する
    if isinstance(value, str):
        # 文字列
        return {"S": value}
    elif isinstance(value, (int, float)):
        # 数値
        return {"N": str(value)}
    elif isinstance(value, dict):
        # 辞書
        return {"M": ConvertJsonToDynamoDB(value)}
    elif isinstance(value, list):
        # リスト
        return {
            "L": list(map(lambda x: _ConvertJsonToDynamoDBByTypeKey(x), value))
        }
    else:
        raise Exception("未対応の型です")


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

    Args:
        target datetime: 変換する日時
    Returns:
        str: 日時文字列
    """
    gmt = target
    if target.tzinfo is not None:
        gmt = target.astimezone(None).replace(tzinfo=None)

    return f"{gmt.isoformat(timespec='milliseconds')}Z"


def StrForDynamoDBToDateTime(target: str) -> datetime:
    """

    DynamoDBに登録された日時文字列からdatetimeを取得

    Args:
        target str: 日時文字列
    Returns:
        datetime: 日時
    """
    isoStr = target.removesuffix("Z")
    utc: datetime = datetime.fromisoformat(isoStr)
    return utc.astimezone(timezone("Asia/Tokyo"))


def MakeYtsheetUrl(id: str) -> str:
    """

    ゆとシートのURLを作成

    Args:
        id str: ゆとシートのID
    Returns:
        str: URL
    """
    return f"https://yutorize.2-d.jp/ytsheet/sw2.5/?id={id}"
