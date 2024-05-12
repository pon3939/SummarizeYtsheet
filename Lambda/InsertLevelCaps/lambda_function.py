# -*- coding: utf-8 -*-

from datetime import datetime
from zoneinfo import ZoneInfo

from aws_lambda_powertools.utilities.typing import LambdaContext
from myLibrary import CommonFunction
from myLibrary.Constant import TableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    BatchWriteItemOutputTypeDef,
    WriteRequestTypeDef,
)

"""
level_capsに登録
"""


def lambda_handler(event: dict, context: LambdaContext):
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    """

    seasonId: int = int(event["SeasonId"])
    levelCaps: list[dict[str, str]] = event["LevelCaps"]

    insertLevelCaps(levelCaps, seasonId)


def insertLevelCaps(
    levelCaps: "list[dict[str, str]]",
    seasonId: int,
):
    """レベルキャップを挿入する

    Args:
        levelCaps: list[dict[str, str]]: レベルキャップ
        seasonId: int: シーズンID
    """

    dynamoDb: DynamoDBClient = CommonFunction.InitDb()

    requestItems: list[WriteRequestTypeDef] = []
    for levelCap in levelCaps:
        # JSTをGMTに変換
        startDatetimeInJst: datetime = datetime.strptime(
            levelCap["startDatetime"], r"%Y/%m/%d"
        ).replace(tzinfo=ZoneInfo("Asia/Tokyo"))

        requestItem: WriteRequestTypeDef = {}
        requestItem["PutRequest"] = {"Item": {}}
        item: dict = {
            "season_id": seasonId,
            "start_datetime"
            "": CommonFunction.DateTimeToStrForDynamoDB(startDatetimeInJst),
            "max_exp": levelCap["maxExp"],
            "minimum_Exp": levelCap["minimumExp"],
        }
        requestItem["PutRequest"]["Item"] = (
            CommonFunction.ConvertJsonToDynamoDB(item)
        )
        requestItems.append(requestItem)

    response: BatchWriteItemOutputTypeDef = dynamoDb.batch_write_item(
        RequestItems={TableName.LEVEL_CAPS: requestItems}
    )

    while response["UnprocessedItems"] != {}:
        response = dynamoDb.batch_write_item(
            RequestItems=response["UnprocessedItems"]
        )
