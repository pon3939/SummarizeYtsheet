# -*- coding: utf-8 -*-

from json import dumps, loads

from requests import Response, get

"""
ゆとシートからデータを取得
"""


def lambda_handler(event: dict, context) -> dict:
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    Returns:
        dict: ゆとシートから取得したデータ
    """

    index: int = event["index"] - 1
    player: dict = event["players"]["Items"][index]
    url: str = player["url"]["S"] + "&mode=json"
    id: int = player["id"]["N"]

    # ゆとシートにアクセス
    response: Response = get(url)

    # ステータスコード200以外は例外発生
    response.raise_for_status()

    ytsheetJson: dict = loads(response.text)

    # 不要なデータを削除
    ytsheetJson.pop("imageCompressed", None)

    return {"id": id, "ytsheetJson": dumps(ytsheetJson)}
