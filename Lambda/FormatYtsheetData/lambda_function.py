# -*- coding: utf-8 -*-

from dataclasses import asdict
from json import dumps

from aws_lambda_powertools.utilities.typing import LambdaContext
from myLibrary import CommonFunction
from myLibrary.Constant import TableName
from myLibrary.Player import Player
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef

"""
プレイヤー情報を整形
"""


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    Returns:
        dict: 整形されたプレイヤー情報
    """

    environment: dict = event["Environment"]
    seasonId: int = int(environment["SeasonId"])
    levelCap: dict = event["LevelCap"]
    maxExp: int = int(levelCap["MaxExp"])
    minimumExp: int = int(levelCap["MinimumExp"])

    # ゆとシートのデータを取得
    players: "list[dict]" = GetPlayers(seasonId)

    return {
        "Players": list(
            map(
                lambda x: dumps(
                    asdict(
                        Player(
                            Name=x["name"],
                            UpdateTime=x["updateTime"],
                            MaxExp=maxExp,
                            MinimumExp=minimumExp,
                            CharacterJsons=x["characters"],
                        )
                    )
                ),
                players,
            )
        )
    }


def GetPlayers(seasonId: int) -> "list[dict]":
    """DBからプレイヤー情報を取得

    容量が大きいためStep Functionsでは対応不可

    Args:
        seasonId int: シーズンID

    Returns:
        list[dict]: プレイヤー情報
    """

    dynamodb: DynamoDBClient = CommonFunction.InitDb()
    response: QueryOutputTypeDef = dynamodb.query(
        TableName=TableName.PLAYERS,
        ProjectionExpression="id, character, update_time, name",
        KeyConditionExpression="season_id = :season_id",
        ExpressionAttributeValues=CommonFunction.ConvertJsonToDynamoDB(
            {":season_id": seasonId}
        ),
    )

    # ページ分割分を取得
    players: "list[dict]" = []
    while "LastEvaluatedKey" in response:
        players += response["Items"]
        response = dynamodb.query(
            TableName=TableName.PLAYERS,
            ProjectionExpression="id, character, update_time, name",
            KeyConditionExpression="season_id = :season_id",
            ExpressionAttributeValues=CommonFunction.ConvertJsonToDynamoDB(
                {":season_id": seasonId}
            ),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )

    players += response["Items"]

    return CommonFunction.ConvertDynamoDBToJson(players)
