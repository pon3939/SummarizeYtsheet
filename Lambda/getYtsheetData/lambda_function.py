# -*- coding: utf-8 -*-

from datetime import datetime
from json import dumps, loads

from myLibrary import commonFunction
from myLibrary.constant import tableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from requests import Response, get

"""
ゆとシートからデータを取得
"""


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    seasonId: int = int(event["SeasonId"])
    index: int = event["index"] - 1
    player: dict = commonFunction.ConvertDynamoDBToJson(
        event["players"]["Items"][index]
    )
    url: str = player["url"] + "&mode=json"
    playerCharacterId: int = player["id"]

    ytsheetJson: dict = getYtsheetData(url)
    updatePlayerCharacter(seasonId, playerCharacterId, ytsheetJson)


def getYtsheetData(url: str):
    """

    メイン処理

    Args:
        url str: ゆとシートのURL
    Returns:
        dict: ゆとシートから取得したデータ
    """

    # ゆとシートにアクセス
    response: Response = get(url)

    # ステータスコード200以外は例外発生
    response.raise_for_status()

    return loads(response.text)


def updatePlayerCharacter(seasonId: int, playerCharacterId: int, ytsheetJson: dict):
    """PCを更新する

    Args:
        id list[dict]: PCのID
        ytsheetJson int: ゆとシートから取得したデータ
    """

    # 不要なデータを削除
    ytsheetJson.pop("imageCompressed", None)

    # 更新
    DynamoDb: DynamoDBClient = commonFunction.InitDb()
    expressionAttributeValues: dict = commonFunction.ConvertJsonToDynamoDB(
        {
            ":ytsheetJson": dumps(ytsheetJson, ensure_ascii=False),
            ":updateTime": datetime.now().isoformat(),
        }
    )
    key: dict = commonFunction.ConvertJsonToDynamoDB(
        {"seasonId": seasonId, "id": playerCharacterId}
    )
    updateOptions: dict = {
        "TableName": tableName.PLAYER_CHARACTERS,
        "Key": key,
        "UpdateExpression": "SET ytsheetJson = :ytsheetJson, updateTime = :updateTime",
        "ExpressionAttributeValues": expressionAttributeValues,
    }
    DynamoDb.update_item(**updateOptions)
