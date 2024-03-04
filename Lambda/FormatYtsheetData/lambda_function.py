# -*- coding: utf-8 -*-


from datetime import datetime
from itertools import chain
from json import loads
from re import search, sub
from typing import Union
from unicodedata import normalize

from myLibrary import commonConstant, commonFunction, expStatus
from myLibrary.constant import tableName
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef
from pytz import timezone

"""
プレイヤー情報を整形
"""

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
DIED_REGEXP: str = "死亡"

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

    environment: dict = event["Environment"]
    seasonId: int = int(environment["SeasonId"])
    levelCap: dict = event["LevelCap"]
    maxExp: int = int(levelCap["MaxExp"])
    minimumExp: int = int(levelCap["MinimumExp"])

    # ゆとシートのデータを取得
    players: "list[dict]" = GetPlayers(seasonId)

    # ゆとシートのデータを整形
    formattedPlayers: "list[dict]" = FormatPlayers(players, maxExp, minimumExp)

    return {"Players": formattedPlayers}


def GetPlayers(seasonId: int) -> "list[dict]":
    """DBからプレイヤー情報を取得

    容量が大きいためStep Functionsでは対応不可

    Args:
        seasonId int: シーズンID

    Returns:
        list[dict]: プレイヤー情報
    """

    dynamodb: DynamoDBClient = commonFunction.InitDb()
    expressionAttributeValues: dict = commonFunction.ConvertJsonToDynamoDB(
        {":seasonId": seasonId}
    )
    queryOptions: dict = {
        "TableName": tableName.PLAYER_CHARACTERS,
        "ProjectionExpression": "id, player, updateTime, #url, ytsheetJson",
        "ExpressionAttributeNames": {"#url": "url"},
        "KeyConditionExpression": "seasonId = :seasonId",
        "ExpressionAttributeValues": expressionAttributeValues,
    }
    response: QueryOutputTypeDef = dynamodb.query(**queryOptions)

    # ページ分割分を取得
    players: "list[dict]" = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        queryOptions["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = dynamodb.query(**queryOptions)
    players.extend(response["Items"])

    # 使いやすいようにフォーマット
    return commonFunction.ConvertDynamoDBToJson(players)


def FormatPlayers(players: "list[dict]", maxExp: int, minimumExp: int) -> "list[dict]":
    """プレイヤー情報を整形

    State間のPayloadサイズは最大256KB

    Args:
        players dict[dict]: ゆとシートから取得したプレイヤー情報
        maxExp int: 経験点の上限
        minimumExp int: 経験点の下限
    Returns:
        list[dict]: 整形されたプレイヤー情報
    """

    totalFumbleRegexp: str = "|".join(list(map(NormalizeString, FUMBLE_TITLES)))
    fumbleCountRegexps: "list[str]" = list(
        map(
            lambda x: rf"(?<={x})\d+",
            map(NormalizeString, FUMBLE_COUNT_PREFIXES),
        )
    )

    # idでソート
    players.sort(key=lambda player: player["id"])

    formattedPlayers: "list[dict]" = []
    no: int = 0
    for player in players:
        formattedPlayer: dict = {}
        ytsheetJson: dict = loads(player.get("ytsheetJson", r"{}"))

        # 文字列
        formattedPlayer["name"] = player.get("player", "")
        formattedPlayer["url"] = player.get("url", "")
        formattedPlayer["race"] = ytsheetJson.get("race", "")
        formattedPlayer["age"] = ytsheetJson.get("age", "")
        formattedPlayer["gender"] = ytsheetJson.get("gender", "")
        formattedPlayer["birth"] = ytsheetJson.get("birth", "")
        formattedPlayer["combatFeatsLv1"] = ytsheetJson.get("combatFeatsLv1", "")
        formattedPlayer["combatFeatsLv3"] = ytsheetJson.get("combatFeatsLv3", "")
        formattedPlayer["combatFeatsLv5"] = ytsheetJson.get("combatFeatsLv5", "")
        formattedPlayer["combatFeatsLv7"] = ytsheetJson.get("combatFeatsLv7", "")
        formattedPlayer["combatFeatsLv9"] = ytsheetJson.get("combatFeatsLv9", "")
        formattedPlayer["combatFeatsLv11"] = ytsheetJson.get("combatFeatsLv11", "")
        formattedPlayer["combatFeatsLv13"] = ytsheetJson.get("combatFeatsLv13", "")
        formattedPlayer["combatFeatsLv15"] = ytsheetJson.get("combatFeatsLv15", "")
        formattedPlayer["combatFeatsLv1bat"] = ytsheetJson.get("combatFeatsLv1bat", "")
        formattedPlayer["adventurerRank"] = ytsheetJson.get("rank", "")

        # 数値
        formattedPlayer["level"] = int(ytsheetJson.get("level", "0"))
        exp = int(ytsheetJson.get("expTotal", "0"))
        formattedPlayer["exp"] = exp
        formattedPlayer["growthTimes"] = int(ytsheetJson.get("historyGrowTotal", "0"))
        formattedPlayer["totalHonor"] = int(ytsheetJson.get("historyHonorTotal", "0"))
        formattedPlayer["hp"] = int(ytsheetJson.get("hpTotal", "0"))
        formattedPlayer["mp"] = int(ytsheetJson.get("mpTotal", "0"))
        formattedPlayer["lifeResistance"] = int(ytsheetJson.get("vitResistTotal", "0"))
        formattedPlayer["spiritResistance"] = int(
            ytsheetJson.get("mndResistTotal", "0")
        )
        formattedPlayer["monsterKnowledge"] = int(ytsheetJson.get("monsterLore", "0"))
        formattedPlayer["initiative"] = int(ytsheetJson.get("initiative", "0"))

        # 特殊な変数
        formattedPlayer["sin"] = ytsheetJson.get("sin", "0")

        # No
        no += 1
        formattedPlayer["no"] = no

        # PC名
        # フリガナを削除
        characterName: str = ytsheetJson.get("characterName", "")
        characterName = sub(r"\|([^《]*)《[^》]*》", r"\1", characterName)
        if characterName == "":
            # PC名が空の場合は二つ名を表示
            characterName = ytsheetJson.get("aka", "")

        formattedPlayer["characterName"] = characterName

        # 経験点の状態
        formattedPlayer["expStatus"] = expStatus.ExpStatus.ACTIVE.value
        if exp >= maxExp:
            formattedPlayer["expStatus"] = expStatus.ExpStatus.MAX.value
        elif exp < minimumExp:
            formattedPlayer["expStatus"] = expStatus.ExpStatus.INACTIVE.value

        # 信仰
        faith = ytsheetJson.get("faith", "なし")
        if faith == "その他の信仰":
            faith = ytsheetJson.get("faithOther", faith)

        formattedPlayer["faith"] = faith

        # 自動取得
        formattedPlayer["autoCombatFeats"] = ytsheetJson.get(
            "combatFeatsAuto", ""
        ).split(",")

        # 更新日時をスプレッドシートが理解できる形式に変換
        formattedPlayer["updateTime"] = None
        strUpdateTime: Union[str, None] = player.get("updateTime")
        if strUpdateTime is not None:
            # UTCをJSTに変換
            utc: datetime = datetime.fromisoformat(strUpdateTime)
            jst: datetime = utc.astimezone(timezone("Asia/Tokyo"))
            formattedPlayer["updateTime"] = jst.strftime("%Y/%m/%d %H:%M:%S")

        # 技能レベル
        formattedPlayer["skills"] = {}
        for skill in commonConstant.SKILLS:
            skillLevel: int = int(ytsheetJson.get(skill["key"], "0"))
            if skillLevel > 0:
                formattedPlayer["skills"][skill["key"]] = skillLevel

        # 各能力値
        formattedPlayer["technic"] = int(ytsheetJson.get("sttBaseTec", "0"))
        formattedPlayer["physical"] = int(ytsheetJson.get("sttBasePhy", "0"))
        formattedPlayer["spirit"] = int(ytsheetJson.get("sttBaseSpi", "0"))
        for statusKey in commonConstant.STATUS_KEYS:
            status = {}
            status["baseStatus"] = int(ytsheetJson.get(statusKey["baseStatus"], "0"))
            status["increasedStatus"] = int(
                ytsheetJson.get(statusKey["increasedStatus"], "0")
            )
            status["additionalStatus"] = int(
                ytsheetJson.get(statusKey["additionalStatus"], "0")
            )
            formattedPlayer[statusKey["key"]] = status

        # 流派を初期化
        formattedPlayer["styles"] = []

        # 秘伝
        mysticArtsNum: int = int(ytsheetJson.get("mysticArtsNum", "0"))
        for i in range(1, mysticArtsNum + 1):
            style: str = FindStyleFormalName(ytsheetJson.get(f"mysticArts{i}", ""))
            if style != "" and style not in formattedPlayer["styles"]:
                formattedPlayer["styles"].append(style)

        # 名誉アイテム
        honorItemsNum: int = int(ytsheetJson.get("honorItemsNum", "0"))
        for i in range(1, honorItemsNum + 1):
            style: str = FindStyleFormalName(ytsheetJson.get(f"honorItem{i}", ""))
            if style != "" and style not in formattedPlayer["styles"]:
                formattedPlayer["styles"].append(style)

        # 不名誉詳細
        disHonorItemsNum: int = int(ytsheetJson.get("dishonorItemsNum", "0"))
        for i in range(1, disHonorItemsNum + 1):
            style: str = FindStyleFormalName(ytsheetJson.get(f"dishonorItem{i}", ""))
            if style != "" and style not in formattedPlayer["styles"]:
                formattedPlayer["styles"].append(style)

        # アビスカースを初期化
        formattedPlayer["abyssCurses"] = []

        # 武器
        weaponNum: int = int(ytsheetJson.get("weaponNum", "0"))
        for i in range(1, weaponNum + 1):
            formattedPlayer["abyssCurses"].extend(
                FindAbyssCurses(ytsheetJson.get(f"weapon{i}Name", ""))
            )
            formattedPlayer["abyssCurses"].extend(
                FindAbyssCurses(ytsheetJson.get(f"weapon{i}Note", ""))
            )

        # 鎧
        armourNum: int = int(ytsheetJson.get("armourNum", "0"))
        for i in range(1, armourNum + 1):
            formattedPlayer["abyssCurses"].extend(
                FindAbyssCurses(ytsheetJson.get(f"armour{i}Name", ""))
            )
            formattedPlayer["abyssCurses"].extend(
                FindAbyssCurses(ytsheetJson.get(f"armour{i}Note", ""))
            )

        # 所持品
        formattedPlayer["abyssCurses"].extend(
            FindAbyssCurses(ytsheetJson.get("items", ""))
        )

        # セッション履歴を集計
        formattedPlayer["gameMasterTimes"] = 0
        formattedPlayer["playerTimes"] = 0
        formattedPlayer["diedTimes"] = 0
        totalFumbleExp: int = 0
        fumbleCount: int = 0
        historyNum: int = int(ytsheetJson.get("historyNum", "0"))
        for i in range(1, historyNum + 1):
            gameMaster: str = ytsheetJson.get(f"history{i}Gm", "")
            if gameMaster == "":
                # GM名未記載の履歴からピンゾロのみのセッション履歴を探す
                normalizedTitle = NormalizeString(
                    ytsheetJson.get(f"history{i}Title", "")
                )
                normalizedDate = NormalizeString(ytsheetJson.get(f"history{i}Date", ""))
                normalizedMember = NormalizeString(
                    ytsheetJson.get(f"history{i}Member", "")
                )
                if (
                    search(totalFumbleRegexp, normalizedTitle)
                    or search(totalFumbleRegexp, normalizedDate)
                    or search(totalFumbleRegexp, normalizedMember)
                ):
                    totalFumbleExp += CalculateFromString(
                        ytsheetJson.get(f"history{i}Exp", "0")
                    )
            else:
                # 参加、GM回数を集計
                if (
                    gameMaster == formattedPlayer["name"]
                    or gameMaster in SELF_GAME_MASTER_NAMES
                ):
                    formattedPlayer["gameMasterTimes"] += 1
                else:
                    formattedPlayer["playerTimes"] += 1

                # 備考
                note: str = ytsheetJson.get(f"history{i}Note", "")
                if search(DIED_REGEXP, note):
                    # 死亡回数を集計
                    formattedPlayer["diedTimes"] += 1

                # ピンゾロ回数を集計
                normalizedNote = NormalizeString(note)
                for fumbleCountRegexp in fumbleCountRegexps:
                    fumbleCountMatch = search(fumbleCountRegexp, normalizedNote)
                    if fumbleCountMatch is not None:
                        fumbleCount += int(fumbleCountMatch.group(0))
                        break

            # ピンゾロ経験点は最大値を採用する(複数の書き方で書かれていた場合、重複して集計してしまうため)
            formattedPlayer["fumbleExp"] = max(totalFumbleExp, fumbleCount * 50)

        formattedPlayers.append(formattedPlayer)

    return formattedPlayers


def NormalizeString(string: str) -> str:
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


def CalculateFromString(string: str) -> int:
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


def FindStyleFormalName(string: str) -> str:
    """

    引数が流派を表す文字列か調べ、流派の正式名称を返却する

    Args:
        string str: 確認する文字列

    Returns:
        str: 引数が流派を表す文字列の場合は流派名、それ以外は空文字
    """

    for style in commonConstant.STYLES:
        if search(style["keywordRegexp"], string):
            return style["name"]

    return ""


def FindAbyssCurses(string: str) -> "list[str]":
    """

    引数に含まれるアビスカースを返却する

    Args:
        string str: 確認する文字列

    Returns:
        list[str]: 引数に含まれるアビスカース
    """

    result: list[str] = []
    for abyssCurse in commonConstant.ABYSS_CURSES:
        if abyssCurse in string:
            result.append(abyssCurse)

    return result
