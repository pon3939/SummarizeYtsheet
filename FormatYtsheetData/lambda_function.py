# -*- coding: utf-8 -*-


from datetime import datetime
from itertools import chain
from json import loads
from re import escape, search
from unicodedata import normalize

from boto3 import resource
from myLibrary import commonConstant
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

# ピンゾロの表記ゆれ対応
FUMBLE_TITLES: "list[str]" = [
    "ファンブル",
    "50点",
    "ゾロ",
    "ソロ",
]

# 備考欄のピンゾロ回数表記ゆれ対応
FUMBLE_COUNT_PREFIXES: "list[str]" = list(
    chain.from_iterable(
        map(
            lambda x: map(
                lambda y: x + y,
                [
                    "",
                    r"\(",
                    ":",
                    r"\*",
                    r"\+",
                    "s",
                ],
            ),
            FUMBLE_TITLES,
        )
    )
)


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

    totalFumbleRegexp: str = "|".join(
        list(map(normalizeString, FUMBLE_TITLES))
    )
    fumbleCountRegexps: "list[str]" = list(
        map(
            lambda x: rf"(?<={x})\d+",
            map(normalizeString, FUMBLE_COUNT_PREFIXES),
        )
    )

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
        formatedPlayer["level"] = int(ytsheetJson.get("level", "0"))
        formatedPlayer["exp"] = int(ytsheetJson.get("expTotal", "0"))

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

        # 技能レベル
        for skill in commonConstant.SKILLS:
            formatedPlayer[skill["key"]] = int(
                ytsheetJson.get(skill["key"], "0")
            )

        # セッション履歴を集計
        formatedPlayer["gameMasterTimes"] = 0
        formatedPlayer["playerTimes"] = 0
        formatedPlayer["diedTimes"] = 0
        totalFumbleExp: int = 0
        fumbleCount: int = 0
        historyNum: int = int(ytsheetJson.get("historyNum", "0"))
        for i in range(1, historyNum):
            gameMaster: str = ytsheetJson.get(f"history{i}Gm", "")
            if gameMaster == "":
                # GM名未記載の履歴からピンゾロのみのセッション履歴を探す
                normalizedTitle = normalizeString(
                    ytsheetJson.get(f"history{i}Title", "")
                )
                normalizedDate = normalizeString(
                    ytsheetJson.get(f"history{i}Date", "")
                )
                normalizedMember = normalizeString(
                    ytsheetJson.get(f"history{i}Member", "")
                )
                if (
                    search(totalFumbleRegexp, normalizedTitle)
                    or search(totalFumbleRegexp, normalizedDate)
                    or search(totalFumbleRegexp, normalizedMember)
                ):
                    totalFumbleExp += calculateFromString(
                        ytsheetJson.get(f"history{i}Exp", "0")
                    )
            else:
                # 参加、GM回数を集計
                if (
                    gameMaster == formatedPlayer["name"]
                    or gameMaster in SELF_GAME_MASTER_NAMES
                ):
                    formatedPlayer["gameMasterTimes"] += 1
                else:
                    formatedPlayer["playerTimes"] += 1

                # 備考
                note: str = ytsheetJson.get(f"history{i}Note", "")
                if search(DIED_REGEXP, note):
                    # 死亡回数を集計
                    formatedPlayer["diedTimes"] += 1

                # ピンゾロ回数を集計
                normalizedNote = normalizeString(note)
                for fumbleCountRegexp in fumbleCountRegexps:
                    fumbleCountMatch = search(
                        fumbleCountRegexp, normalizedNote
                    )
                    if fumbleCountMatch is not None:
                        fumbleCount += int(fumbleCountMatch.group(0))
                        break

            # ピンゾロ経験点は最大値を採用する(複数の書き方で書かれていた場合、重複して集計してしまうため)
            formatedPlayer["fumbleExp"] = max(totalFumbleExp, fumbleCount * 50)

        formattedPlayers.append(formatedPlayer)

    return formattedPlayers


def normalizeString(string: str) -> str:
    """

    文字列を正規化

    Args:
        string str: 正規化する文字列

    Returns:
        str: 正規化した文字列
    """
    result: str = string.translate(
        str.maketrans(
            {
                "一": "1",
                "二": "2",
                "三": "3",
                "四": "4",
                "五": "5",
                "六": "6",
                "七": "7",
                "八": "8",
                "九": "9",
                "十": "10",
            }
        )
    )
    result: str = normalize("NFKC", result)
    return result


def calculateFromString(string: str) -> int:
    """

    四則演算の文字列から解を求める

    Args:
        string str: 計算する文字列

    Returns:
        int: 解
    """
    notCalcRegexp: str = r"[^0-9\+\-\*\/\(\)]"
    if search(string, notCalcRegexp):
        # 四則演算以外の文字列が含まれる
        return 0

    return eval(string)
