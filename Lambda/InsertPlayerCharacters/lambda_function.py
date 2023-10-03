# -*- coding: utf-8 -*-

from boto3 import resource
from boto3.dynamodb.conditions import Attr, Equals

"""
PlayerCharactersに登録
"""

# PCテーブル
PlayerCharactersTable = None

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

    seasonId: dict = event["SeasonId"]
    playerCharacters: list[dict] = event["PlayerCharacters"]

    initDb()
    playerCharacterId: int = GetNewId(seasonId)
    insertPlayerCharacters(playerCharacters, seasonId, playerCharacterId)


def initDb():
    """DBに接続する"""

    global PlayerCharactersTable

    dynamoDb = resource("dynamodb", region_name=AWS_REGION)
    PlayerCharactersTable = dynamoDb.Table(TABLE_NAME)


def GetNewId(seasonId: int) -> int:
    """PCのIDを採番する

    現在の最大ID+1

    Args:
        seasonId int: シーズンID

    Returns:
        int: ID
    """
    global PlayerCharactersTable

    projectionExpression: str = "id"
    filterExpression: Equals = Attr("seasonId").eq(seasonId)
    response: dict = PlayerCharactersTable.scan(
        ProjectionExpression=projectionExpression,
        FilterExpression=filterExpression,
    )

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        response = PlayerCharactersTable.scan(
            ProjectionExpression=projectionExpression,
            ExclusiveStartKey=response["LastEvaluatedKey"],
            FilterExpression=filterExpression,
        )
    players.extend(response["Items"])

    if len(players) == 0:
        return 1

    maxPlayer = max(players, key=(lambda player: player["id"]))

    return maxPlayer["id"] + 1


def insertPlayerCharacters(
    playerCharacters: "list[dict]", seasonId: int, playerCharacterId: int
):
    """PCを挿入する

    Args:
        playerCharacters: list[dict]: シーズンID
        seasonId: int: シーズンID
        playerCharacterId: int: ID
    """
    global PlayerCharactersTable

    with PlayerCharactersTable.batch_writer() as writer:
        id = playerCharacterId
        for playerCharacter in playerCharacters:
            item = playerCharacter.copy()
            item.update(seasonId=seasonId, id=id)
            writer.put_item(Item=item)
            id += 1
