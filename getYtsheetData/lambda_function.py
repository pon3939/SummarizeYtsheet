# -*- coding: utf-8 -*-

from requests import get

"""
ゆとシートからデータを取得
"""


def lambda_handler(event, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    index = event["index"] - 1
    player = event["players"]["Items"][index]
    url = player["url"]["S"] + "&mode=json"
    id = player["id"]["N"]

    # ゆとシートにアクセス
    response = get(url)

    # ステータスコード200以外は例外発生
    response.raise_for_status()

    ytsheetJson = response.text

    return {"id": id, "ytsheetJson": ytsheetJson}
