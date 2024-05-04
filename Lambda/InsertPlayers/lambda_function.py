# -*- coding: utf-8 -*-

from typing import Union

from aws_lambda_powertools.utilities.typing import LambdaContext
from myLibrary import commonFunction
from myLibrary.constant import tableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    BatchWriteItemOutputTypeDef,
    QueryOutputTypeDef,
    WriteRequestTypeDef,
)

"""
Playersに登録
"""


DynamoDb: Union[DynamoDBClient, None] = None


def lambda_handler(event: dict, context: LambdaContext):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    global DynamoDb

    seasonId: int = int(event["SeasonId"])
    players: list[dict] = event["Players"]

    DynamoDb = commonFunction.InitDb()
    newId: int = GetNewId(seasonId)
    insertPlayers(players, seasonId, newId)


def GetNewId(seasonId: int) -> int:
    """IDを採番する

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
        {":season_id": seasonId}
    )
    queryOptions: dict = {
        "TableName": tableName.PLAYERS,
        "ProjectionExpression": "id",
        "KeyConditionExpression": "season_id = :season_id ",
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
    maxId: dict = max(players, key=(lambda player: player["id"]))

    return int(maxId["id"]) + 1


def insertPlayers(players: "list[dict]", seasonId: int, newId: int):
    """Playersを挿入する

    Args:
        players: list[dict]: PC情報
        seasonId: int: シーズンID
        newId: int: ID
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    id: int = newId
    requestItems: list[WriteRequestTypeDef] = []
    for player in players:
        requestItem: WriteRequestTypeDef = {}
        requestItem["PutRequest"] = {"Item": {}}
        item: dict = {
            "season_id": seasonId,
            "id": id,
            "name": player["Name"],
            "characters": [
                {"ytsheet_id": player["YtsheetId"], "ytsheet_json": {}}
            ],
        }
        requestItem["PutRequest"]["Item"] = (
            commonFunction.ConvertJsonToDynamoDB(item)
        )
        requestItems.append(requestItem)
        id += 1

    response: BatchWriteItemOutputTypeDef = DynamoDb.batch_write_item(
        RequestItems={tableName.PLAYERS: requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = DynamoDb.batch_write_item(
            RequestItems=response["UnprocessedItems"]
        )
