# -*- coding: utf-8 -*-

from typing import Union

from myLibrary import commonFunction
from myLibrary.constant import tableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    BatchWriteItemOutputTypeDef,
    QueryOutputTypeDef,
)

"""
PlayerCharactersに登録
"""

# PCテーブル
DynamoDb: Union[DynamoDBClient, None] = None


def lambda_handler(event, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    global DynamoDb

    seasonId: int = event["SeasonId"]
    playerCharacters: list[dict] = event["PlayerCharacters"]

    DynamoDb = commonFunction.InitDb()
    playerCharacterId: int = GetNewId(seasonId)
    insertPlayerCharacters(playerCharacters, seasonId, playerCharacterId)


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

    expressionAttributeValues: dict = commonFunction.ConvertJsonToDynamoDB(
        {":seasonId": seasonId}
    )
    queryOptions: dict = {
        "TableName": tableName.PLAYER_CHARACTERS,
        "ProjectionExpression": "id",
        "KeyConditionExpression": "seasonId = :seasonId",
        "ExpressionAttributeValues": expressionAttributeValues,
    }
    response: QueryOutputTypeDef = DynamoDb.query(**queryOptions)

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        queryOptions["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = DynamoDb.query(**queryOptions)
    players.extend(response["Items"])

    if len(players) == 0:
        return 1

    players = commonFunction.ConvertDynamoDBToJson(players)
    maxPlayer = max(players, key=(lambda player: player["id"]))

    return int(maxPlayer["id"]) + 1


def insertPlayerCharacters(
    playerCharacters: "list[dict]", seasonId: int, playerCharacterId: int
):
    """PCを挿入する

    Args:
        playerCharacters: list[dict]: PC情報
        seasonId: int: シーズンID
        playerCharacterId: int: ID
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    id = playerCharacterId
    requestItems = []
    for playerCharacter in playerCharacters:
        requestItem: dict = {}
        requestItem["PutRequest"] = {}
        item: dict = {
            "seasonId": seasonId,
            "id": id,
            "player": playerCharacter["player"],
            "url": playerCharacter["url"],
        }
        requestItem["PutRequest"]["Item"] = commonFunction.ConvertJsonToDynamoDB(item)
        requestItems.append(requestItem)
        id += 1

    response: BatchWriteItemOutputTypeDef = DynamoDb.batch_write_item(
        RequestItems={tableName.PLAYER_CHARACTERS: requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = DynamoDb.batch_write_item(RequestItems=response["UnprocessedItems"])
