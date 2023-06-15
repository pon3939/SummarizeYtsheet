# -*- coding: utf-8 -*-


from datetime import datetime
from json import loads
from re import escape, search

from boto3 import resource
from pytz import timezone

"""
プレイヤー情報を整形
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# DBコネクション
Dynamodb = None


# 自分が開催したときのGM名
SELF_GAME_MASTER_NAMES: "list[str]" = [
    "俺",
    "私",
    "私だ",
    "私だ。",
    "自分",
    "おれさま",
    "拙者",
    "我",
    "朕",
]

# 死亡時の備考
DIED_REGEXP: str = "|".join(list(map(escape, ["「死亡」", "(死亡)"])))


def lambda_handler(event: dict, context) -> dict:
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    Returns:
        dict: 整形されたプレイヤー情報
    """

    # ゆとシートのデータを取得
    players: "list[dict]" = getPlayers()

    # ゆとシートのデータを整形
    formattedPlayers: "list[dict]" = formatPlayers(players)

    return {"Players": formattedPlayers}


def getPlayers() -> "list[dict]":
    """DBからプレイヤー情報を取得

    容量が大きいためStep Functionsでは対応不可

    Returns:
        list[dict]: プレイヤー情報
    """
    global Dynamodb

    Dynamodb = resource("dynamodb", region_name=AWS_REGION)
    teble = Dynamodb.Table("Players")
    response: dict = teble.scan()

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        response = teble.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    players.extend(response["Items"])

    return players


def formatPlayers(players: "list[dict]") -> "list[dict]":
    """プレイヤー情報を整形

    State間のPayloadサイズは最大256KB

    Args:
        players dict[dict]: ゆとシートから取得したプレイヤー情報
    Returns:
        list[dict]: 整形されたプレイヤー情報
    """

    # idでソート
    players.sort(key=lambda player: player["id"])

    formattedPlayers: "list[dict]" = []
    no: int = 0
    for player in players:
        formatedPlayer: dict = {}
        ytsheetJson: dict = loads(player.get("ytsheetJson", r"{}"))

        # 文字列
        formatedPlayer["name"] = player.get("player", "")
        formatedPlayer["url"] = player.get("url", "")
        formatedPlayer["characterName"] = ytsheetJson.get("characterName", "")
        formatedPlayer["race"] = ytsheetJson.get("race", "")
        formatedPlayer["age"] = ytsheetJson.get("age", "")
        formatedPlayer["gender"] = ytsheetJson.get("gender", "")
        formatedPlayer["sin"] = ytsheetJson.get("sin", "0")

        # 数値

        # 特殊な変数
        # JSONに変換するため、Decimalをintに変換
        no += 1
        formatedPlayer["no"] = int(player.get("id", "-1"))
        formatedPlayer["faith"] = ytsheetJson.get("faith", "なし")

        # 更新日時をスプレッドシートが理解できる形式に変換
        formatedPlayer["updateTime"] = None
        strUpdatetime: str = player.get("updateTime")
        if strUpdatetime is not None:
            # UTCをJSTに変換
            utc: datetime = datetime.fromisoformat(
                strUpdatetime.replace("Z", "+00:00")
            )
            jst: datetime = utc.astimezone(timezone("Asia/Tokyo"))
            formatedPlayer["updateTime"] = jst.strftime("%Y/%m/%d %H:%M:%S")

        # セッション履歴を集計
        formatedPlayer["gameMasterTimes"] = 0
        formatedPlayer["playerTimes"] = 0
        formatedPlayer["diedTimes"] = 0
        historyNum: int = int(ytsheetJson.get("historyNum", "0"))
        for i in range(1, historyNum):
            gameMaster: str = ytsheetJson.get(f"history{i}Gm", "")
            if gameMaster == "":
                # GM名が空白の履歴は読み飛ばす
                continue

            # 参加、GM回数を集計
            if (
                gameMaster == formatedPlayer["name"]
                or gameMaster in SELF_GAME_MASTER_NAMES
            ):
                formatedPlayer["gameMasterTimes"] += 1
            else:
                formatedPlayer["playerTimes"] += 1

            # 死亡回数を集計
            note: str = ytsheetJson.get(f"history{i}Note", "")
            if search(DIED_REGEXP, note):
                formatedPlayer["diedTimes"] += 1

        formattedPlayers.append(formatedPlayer)

    return formattedPlayers
