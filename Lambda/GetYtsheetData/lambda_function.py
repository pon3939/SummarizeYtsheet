# -*- coding: utf-8 -*-

from json import dumps, loads
from time import sleep

from aws_lambda_powertools.utilities.typing import LambdaContext
from myLibrary import CommonFunction
from myLibrary.Constant import TableName
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
    player: dict = CommonFunction.ConvertDynamoDBToJson(
        event["Players"][index]
    )

    updatePlayers(seasonId, player)


def updatePlayers(seasonId: int, player: dict):
    """PCを更新する

    Args:
        seasonId id: シーズンID
        player dict: プレイヤー情報
    """

    updateCharacters: list = []
    for ytsheetId in player["ytsheet_ids"]:
        ytsheetJson: dict = getYtsheetData(ytsheetId)

        # 不要なデータを削除
        ytsheetJson.pop("imageCompressed", None)

        character: dict = {
            "ytsheet_id": ytsheetId,
            "ytsheet_json": dumps(ytsheetJson, ensure_ascii=False),
        }
        updateCharacters.append(character)

    # 更新
    dynamoDb: DynamoDBClient = CommonFunction.InitDb()
    updateTime: str = CommonFunction.GetCurrentDateTimeForDynamoDB()
    dynamoDb.update_item(
        TableName=TableName.PLAYERS,
        Key=CommonFunction.ConvertJsonToDynamoDB(
            {"season_id": seasonId, "id": player["id"]}
        ),
        UpdateExpression="SET characters = :characters, "
        " update_time = :update_time",
        ExpressionAttributeValues=CommonFunction.ConvertJsonToDynamoDB(
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

    # ゆとシートにアクセス
    url: str = f"{CommonFunction.MakeYtsheetUrl(ytsheetId)}&mode=json"
    response: Response = get(url)

    # ステータスコード200以外は例外発生
    response.raise_for_status()

    # 連続リクエスト抑制
    sleep(5)

    return loads(response.text)
