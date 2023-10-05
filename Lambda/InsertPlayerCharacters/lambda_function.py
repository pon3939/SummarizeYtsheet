# -*- coding: utf-8 -*-

from typing import Union

from boto3 import client
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    BatchWriteItemOutputTypeDef,
    ScanOutputTypeDef,
)

"""
PlayerCharactersに登録
"""

# PCテーブル
DynamoDb: Union[DynamoDBClient, None] = None

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# PCのテーブル名
TABLE_NAME: str = "PlayerCharacters"


def lambda_handler(event, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    seasonId: int = event["SeasonId"]
    playerCharacters: list[dict] = event["PlayerCharacters"]

    initDb()
    playerCharacterId: int = GetNewId(seasonId)
    insertPlayerCharacters(playerCharacters, seasonId, playerCharacterId)


def initDb():
    """DBに接続する"""

    global DynamoDb

    DynamoDb = client("dynamodb", region_name=AWS_REGION)


def GetNewId(seasonId: int) -> int:
    """PCのIDを採番する

    現在の最大ID+1

    Args:
        seasonId int: シーズンID

    Returns:
        int: ID
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    scanOptions: dict = {
        "TableName": "PlayerCharacters",
        "ProjectionExpression": "id",
        "FilterExpression": "seasonId = :seasonId",
        "ExpressionAttributeValues": {":seasonId": {"N": str(seasonId)}},
    }
    response: ScanOutputTypeDef = DynamoDb.scan(**scanOptions)

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        scanOptions["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = DynamoDb.scan(**scanOptions)
    players.extend(response["Items"])

    if len(players) == 0:
        return 1

    maxPlayer = max(players, key=(lambda player: int(player["id"]["N"])))

    return int(maxPlayer["id"]["N"]) + 1


def insertPlayerCharacters(
    playerCharacters: "list[dict]", seasonId: int, playerCharacterId: int
):
    """PCを挿入する

    Args:
        playerCharacters: list[dict]: シーズンID
        seasonId: int: シーズンID
        playerCharacterId: int: ID
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    id = playerCharacterId
    stringSeasonId = str(seasonId)
    requestItems = []
    for playerCharacter in playerCharacters:
        requestItem: dict = {}
        requestItem["PutRequest"] = {}
        requestItem["PutRequest"]["Item"] = {
            "seasonId": {"N": stringSeasonId},
            "id": {"N": str(id)},
            "player": {"S": playerCharacter["player"]},
            "url": {"S": playerCharacter["url"]},
        }
        requestItems.append(requestItem)
        id += 1

    response: BatchWriteItemOutputTypeDef = DynamoDb.batch_write_item(
        RequestItems={"PlayerCharacters": requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = DynamoDb.batch_write_item(
            RequestItems=response["UnprocessedItems"]
        )