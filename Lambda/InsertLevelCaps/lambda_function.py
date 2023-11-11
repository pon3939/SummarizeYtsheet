# -*- coding: utf-8 -*-

from datetime import datetime

from myLibrary import commonFunction
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import BatchWriteItemOutputTypeDef

"""
LevelCapsに登録
"""

# レベルキャップのテーブル名
TABLE_NAME: str = "LevelCaps"


def lambda_handler(event, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    seasonId: int = event["seasonId"]
    levelCaps: list[dict[str, str]] = event["levelCaps"]

    insertLevelCaps(levelCaps, seasonId)


def insertLevelCaps(
    levelCaps: "list[dict[str, str]]",
    seasonId: int,
):
    """PCを挿入する

    Args:
        levelCaps: list[dict[str, str]]: レベルキャップ
        seasonId: int: シーズンID
    """

    dynamoDb: DynamoDBClient = commonFunction.InitDb()

    requestItems = []
    for levelCap in levelCaps:
        # JSTをGMTに変換
        startDatetimeInJst: datetime = datetime.strptime(
            f'{levelCap["startDatetime"]}+09:00', r"%Y/%m/%d%z"
        )
        startDatetimeInGmt: datetime = startDatetimeInJst.astimezone(None)

        requestItem: dict = {}
        requestItem["PutRequest"] = {}
        item: dict = {
            "seasonId": seasonId,
            "startDatetime": startDatetimeInGmt.strftime(
                r"%Y-%m-%dT%H:%M:%S.%fZ"  # ISO 8601
            ),
            "maxExp": levelCap["maxExp"],
            "minimumExp": levelCap["minimumExp"],
        }
        requestItem["PutRequest"]["Item"] = commonFunction.ConvertJsonToDynamoDB(item)
        requestItems.append(requestItem)

    response: BatchWriteItemOutputTypeDef = dynamoDb.batch_write_item(
        RequestItems={TABLE_NAME: requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = dynamoDb.batch_write_item(RequestItems=response["UnprocessedItems"])
