# -*- coding: utf-8 -*-

from json import dumps, loads
from time import sleep

from aws_lambda_powertools.utilities.typing import LambdaContext
from MyLibrary.CommonFunction import (
    ConvertDynamoDBToJson,
    ConvertJsonToDynamoDB,
    GetCurrentDateTimeForDynamoDB,
    InitDb,
    MakeYtsheetUrl,
)
from MyLibrary.Constant import TableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from requests import Response, get

"""
ゆとシートからデータを取得
"""


def lambda_handler(event: dict, context: LambdaContext):
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    """

    seasonId: int = int(event["SeasonId"])
    index: int = event["Index"]
    player: dict = ConvertDynamoDBToJson(event["Players"][index])

    updatePlayers(seasonId, player)


def updatePlayers(seasonId: int, player: dict):
    """PCを更新する

    Args:
        seasonId id: シーズンID
        player dict: プレイヤー情報
    """

    updateCharacters: list = []
    for ytsheetId in player["ytsheet_ids"]:
        character: dict = {
            "ytsheet_id": ytsheetId,
            "ytsheet_json": dumps(
                getYtsheetData(ytsheetId), ensure_ascii=False
            ),
        }
        updateCharacters.append(character)

    # 更新
    dynamoDb: DynamoDBClient = InitDb()
    updateTime: str = GetCurrentDateTimeForDynamoDB()
    dynamoDb.update_item(
        TableName=TableName.PLAYERS,
        Key=ConvertJsonToDynamoDB({"season_id": seasonId, "id": player["id"]}),
        UpdateExpression="SET characters = :characters, "
        " update_time = :update_time",
        ExpressionAttributeValues=ConvertJsonToDynamoDB(
            {
                ":characters": updateCharacters,
                ":update_time": updateTime,
            }
        ),
    )


def getYtsheetData(ytsheetId: str) -> dict:
    """

    メイン処理

    Args:
        ytsheetId str: ゆとシートのID
    Returns:
        dict: ゆとシートから取得したデータ
    """

    # 連続リクエスト抑制
    sleep(5)

    # ゆとシートにアクセス
    url: str = f"{MakeYtsheetUrl(ytsheetId)}&mode=json"
    response: Response = get(url)

    # ステータスコード200以外は例外発生
    response.raise_for_status()

    return loads(response.text)
