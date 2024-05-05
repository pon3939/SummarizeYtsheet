# -*- coding: utf-8 -*-

from typing import Union

from aws_lambda_powertools.utilities.typing import LambdaContext
from myLibrary import commonFunction
from myLibrary.constant import indexName, tableName
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
    maxId: int = GetMaxId(seasonId)
    putPlayers(players, seasonId, maxId)


def GetMaxId(seasonId: int) -> int:
    """IDの最大値を取得する

    Args:
        seasonId int: シーズンID

    Returns:
        int: 最大ID
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    projectionExpression: str = "id"
    KeyConditionExpression: str = "season_id = :season_id"
    expressionAttributeValues: dict = commonFunction.ConvertJsonToDynamoDB(
        {":season_id": seasonId}
    )
    response: QueryOutputTypeDef = DynamoDb.query(
        TableName=tableName.PLAYERS,
        ProjectionExpression=projectionExpression,
        KeyConditionExpression=KeyConditionExpression,
        ExpressionAttributeValues=expressionAttributeValues,
    )

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        response = DynamoDb.query(
            TableName=tableName.PLAYERS,
            ProjectionExpression=projectionExpression,
            KeyConditionExpression=KeyConditionExpression,
            ExpressionAttributeValues=expressionAttributeValues,
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
    players.extend(response["Items"])

    if len(players) == 0:
        return 0

    players = commonFunction.ConvertDynamoDBToJson(players)
    maxId: dict = max(players, key=(lambda player: player["id"]))

    return int(maxId["id"])


def putPlayers(players: "list[dict]", seasonId: int, maxId: int):
    """Playersを挿入する

    Args:
        players: list[dict]: PC情報
        seasonId: int: シーズンID
        maxId: int: 既存IDの最大値
    """
    global DynamoDb

    if DynamoDb is None:
        raise Exception("DynamoDBが初期化されていません")

    id: int = maxId
    requestItems: list[WriteRequestTypeDef] = []
    for player in players:
        # プレイヤー名で存在チェック
        queryResult: QueryOutputTypeDef = DynamoDb.query(
            TableName=tableName.PLAYERS,
            ProjectionExpression="id",
            IndexName=indexName.PLAYERS_SEASON_ID_NAME,
            KeyConditionExpression="season_id = :season_id AND #name = :name",
            ExpressionAttributeNames={"#name": "name"},
            ExpressionAttributeValues=commonFunction.ConvertJsonToDynamoDB(
                {":season_id": seasonId, ":name": player["Name"]}
            ),
        )
        existsPlayers: list[dict] = commonFunction.ConvertDynamoDBToJson(
            queryResult["Items"]
        )

        newPlayerCharacter = {
            "ytsheet_id": player["YtsheetId"],
            "ytsheet_json": {},
        }
        if len(existsPlayers) > 0:
            # 更新
            DynamoDb.update_item(
                TableName=tableName.PLAYERS,
                Key=commonFunction.ConvertJsonToDynamoDB(
                    {"season_id": seasonId, "id": existsPlayers[0]["id"]}
                ),
                UpdateExpression="SET characters = "
                " list_append(characters, :new_character), "
                " update_time = :update_time",
                ExpressionAttributeValues=commonFunction.ConvertJsonToDynamoDB(
                    {
                        ":new_character": [newPlayerCharacter],
                        ":update_time": (
                            commonFunction.GetCurrentDateTimeForDynamoDB()
                        ),
                    }
                ),
            )
            continue

        # 新規作成
        id += 1
        newPlayer: dict = {
            "season_id": seasonId,
            "id": id,
            "name": player["Name"],
            "characters": [newPlayerCharacter],
            "update_time": commonFunction.GetCurrentDateTimeForDynamoDB(),
        }
        requestItem: WriteRequestTypeDef = {}
        requestItem["PutRequest"] = {"Item": {}}
        requestItem["PutRequest"]["Item"] = (
            commonFunction.ConvertJsonToDynamoDB(newPlayer)
        )
        requestItems.append(requestItem)

    if len(requestItems) == 0:
        return

    response: BatchWriteItemOutputTypeDef = DynamoDb.batch_write_item(
        RequestItems={tableName.PLAYERS: requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = DynamoDb.batch_write_item(
            RequestItems=response["UnprocessedItems"]
        )
