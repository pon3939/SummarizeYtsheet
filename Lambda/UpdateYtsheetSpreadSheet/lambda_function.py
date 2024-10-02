# -*- coding: utf-8 -*-


from re import sub
from time import sleep
from typing import Union

from aws_lambda_powertools.utilities.typing import LambdaContext
from google.oauth2 import service_account
from gspread import utils
from gspread.auth import authorize
from gspread.client import Client
from gspread.spreadsheet import Spreadsheet
from gspread.utils import ValueInputOption
from gspread.worksheet import CellFormat, Worksheet
from MyLibrary.CommonFunction import (
    ConvertDynamoDBToJson,
    ConvertJsonToDynamoDB,
    ConvertToVerticalHeader,
    InitDb,
    MakeYtsheetUrl,
)
from MyLibrary.Constant import SpreadSheet, SwordWorld, TableName
from MyLibrary.ExpStatus import ExpStatus
from MyLibrary.GeneralSkill import GeneralSkill
from MyLibrary.Player import Player
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef

"""
スプレッドシートを更新
"""
# 初期作成時に振るダイスの数と能力増加分
RACES_STATUSES: dict = {
    "人間": {"diceCount": 12, "fixedValue": 0},
    "エルフ": {"diceCount": 11, "fixedValue": 0},
    "ドワーフ": {"diceCount": 10, "fixedValue": 12},
    "タビット": {"diceCount": 9, "fixedValue": 6},
    "ルーンフォーク": {"diceCount": 10, "fixedValue": 0},
    "ナイトメア": {"diceCount": 10, "fixedValue": 0},
    "リカント": {"diceCount": 8, "fixedValue": 9},
    "リルドラケン": {"diceCount": 10, "fixedValue": 6},
    "グラスランナー": {"diceCount": 10, "fixedValue": 12},
    "メリア": {"diceCount": 7, "fixedValue": 6},
    "ティエンス": {"diceCount": 10, "fixedValue": 6},
    "レプラカーン": {"diceCount": 11, "fixedValue": 0},
    "ウィークリング": {"diceCount": 12, "fixedValue": 3},
    "ソレイユ": {"diceCount": 9, "fixedValue": 6},
    "アルヴ": {"diceCount": 8, "fixedValue": 12},
    "シャドウ": {"diceCount": 10, "fixedValue": 0},
    "スプリガン": {"diceCount": 8, "fixedValue": 0},
    "アビスボーン": {"diceCount": 9, "fixedValue": 6},
    "ハイマン": {"diceCount": 8, "fixedValue": 0},
    "フロウライト": {"diceCount": 11, "fixedValue": 12},
    "ダークドワーフ": {"diceCount": 9, "fixedValue": 12},
    "ディアボロ": {"diceCount": 10, "fixedValue": 12},
    "ドレイク": {"diceCount": 10, "fixedValue": 6},
    "バジリスク": {"diceCount": 9, "fixedValue": 6},
    "ダークトロール": {"diceCount": 10, "fixedValue": 6},
    "アルボル": {"diceCount": 10, "fixedValue": 3},
    "バーバヤガー": {"diceCount": 8, "fixedValue": 6},
    "ケンタウロス": {"diceCount": 10, "fixedValue": 6},
    "シザースコーピオン": {"diceCount": 10, "fixedValue": 6},
    "ドーン": {"diceCount": 10, "fixedValue": 6},
    "コボルド": {"diceCount": 10, "fixedValue": 0},
    "ドレイクブロークン": {"diceCount": 10, "fixedValue": 6},
    "ラミア": {"diceCount": 10, "fixedValue": 0},
    "ラルヴァ": {"diceCount": 9, "fixedValue": 6},
}


def lambda_handler(event: dict, context: LambdaContext) -> None:
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    Returns:
        dict: 整形されたプレイヤー情報
    """
    interval: int = 10

    # 入力
    environment: dict = event["Environment"]
    seasonId: int = int(environment["SeasonId"])
    spreadsheetId: str = environment["SpreadsheetId"]
    levelCap: dict = event["LevelCap"]
    maxExp: int = int(levelCap["MaxExp"])
    minimumExp: int = int(levelCap["MinimumExp"])
    googleServiceAccount: dict = event["GoogleServiceAccount"]

    # ゆとシートのデータを取得
    players: "list[Player]" = LoadPlayers(seasonId, maxExp, minimumExp)

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )

    # シート並び替え
    ReorderSheets(spreadsheet)

    sleep(interval)

    # PLシート
    UpdatePlayerSheet(spreadsheet, players)

    sleep(interval)

    # 基本シート
    UpdateBasicSheet(spreadsheet, players)

    sleep(interval)

    # 技能シート
    UpdateCombatSkillSheet(spreadsheet, players)

    sleep(interval)

    # 能力値シート
    UpdateStatusSheet(spreadsheet, players)

    sleep(interval)

    # 戦闘特技シート
    UpdateAbilitySheet(spreadsheet, players)

    sleep(interval)

    # 名誉点・流派シート
    UpdateHonorSheet(spreadsheet, players)

    sleep(interval)

    # アビスカースシート
    UpdateAbyssCurseSheet(spreadsheet, players)

    sleep(interval)

    # 一般技能シート
    UpdateGeneralSkillSheet(spreadsheet, players)


def LoadPlayers(seasonId: int, maxExp: int, minimumExp: int) -> list[Player]:
    """DBからプレイヤー情報を取得

    Args:
        seasonId int: シーズンID
        maxExp int: 最大経験点
        minimumExp int: 最小経験点

    Returns:
        list[Player]: プレイヤー情報
    """

    dynamodb: DynamoDBClient = InitDb()
    projectionExpression: str = "id, characters, update_time, #name"
    expressionAttributeNames: dict = {"#name": "name"}
    keyConditionExpression: str = "season_id = :season_id"
    expressionAttributeValues: dict = ConvertJsonToDynamoDB(
        {":season_id": seasonId}
    )
    response: QueryOutputTypeDef = dynamodb.query(
        TableName=TableName.PLAYERS,
        ProjectionExpression=projectionExpression,
        ExpressionAttributeNames=expressionAttributeNames,
        KeyConditionExpression=keyConditionExpression,
        ExpressionAttributeValues=expressionAttributeValues,
    )

    # ページ分割分を取得
    players: list[dict] = []
    while "LastEvaluatedKey" in response:
        players += response["Items"]
        response = dynamodb.query(
            TableName=TableName.PLAYERS,
            ProjectionExpression=projectionExpression,
            ExpressionAttributeNames=expressionAttributeNames,
            KeyConditionExpression=keyConditionExpression,
            ExpressionAttributeValues=expressionAttributeValues,
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )

    players += response["Items"]

    return list(
        map(
            lambda x: Player(
                x["name"],
                x["update_time"],
                maxExp,
                minimumExp,
                x["characters"],
            ),
            ConvertDynamoDBToJson(players),
        )
    )


def OpenSpreadsheet(
    googleServiceAccount: dict, spreadsheetId: str
) -> Spreadsheet:
    """

    スプレッドシートを開く

    Args:
        googleServiceAccount str: スプレッドシートの認証情報
        spreadsheetId str: スプレッドシートのID
    Returns:
        Spreadsheet: スプレッドシート
    """

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client: Client = authorize(credentials)
    return client.open_by_key(spreadsheetId)


def ReorderSheets(spreadsheet: Spreadsheet) -> None:
    """シートを並び替える

    Args:
        spreadsheet Spreadsheet: スプレッドシート
    """

    # 並び替え
    spreadsheet.reorder_worksheets(
        [
            spreadsheet.worksheet("使い方"),
            spreadsheet.worksheet("グラフ"),
            spreadsheet.worksheet("PL"),
            spreadsheet.worksheet("基本"),
            spreadsheet.worksheet("技能"),
            spreadsheet.worksheet("能力値"),
            spreadsheet.worksheet("戦闘特技"),
            spreadsheet.worksheet("名誉点・流派"),
            spreadsheet.worksheet("アビスカース"),
            spreadsheet.worksheet("一般技能"),
        ]
    )


def UpdatePlayerSheet(spreadsheet: Spreadsheet, players: list[Player]) -> None:
    """PLシートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("PL")
    updateData: list[list] = []

    # ヘッダー
    header: list[str] = [
        "No.",
        "PL",
        "参加傾向",
        "1人目",
        "2人目",
        "参加",
        "GM",
        "参加+GM",
        "更新日時",
    ]
    subPcIndex: int = header.index("2人目")

    formats: list[CellFormat] = []
    no: int = 0
    for player in players:
        row: list = []

        # No.
        no += 1
        row.append(no)

        # PL
        row.append(player.Name)

        # 参加傾向
        row.append(
            max(
                list(
                    map(
                        lambda x: x.ActiveStatus.GetStrForSpreadsheet(),
                        player.Characters,
                    )
                )
            )
        )

        # 1人目
        row.append(player.Characters[0].Name)

        # 2人目
        subPcName: str = (
            player.Characters[1].Name if len(player.Characters) > 1 else ""
        )
        row.append(subPcName)

        # 参加
        playerTimes: int = sum(
            list(map(lambda x: x.PlayerTimes, player.Characters))
        )
        row.append(playerTimes)

        # GM
        gameMasterTimes: int = player.GameMasterTimes
        row.append(gameMasterTimes)

        # 参加+GM
        row.append(playerTimes + gameMasterTimes)

        # 更新日時
        row.append(player.UpdateTime)

        updateData.append(row)

        # 1人目列のハイパーリンク
        mainPcIndex: int = header.index("1人目") + 1
        rowIndex: int = updateData.index(row) + 1 + 1
        mainPcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
        mainPcTextFormat["link"] = {
            "uri": MakeYtsheetUrl(player.Characters[0].YtsheetId)
        }
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, mainPcIndex),
                "format": {"textFormat": mainPcTextFormat},
            }
        )

        # 2人目列のハイパーリンク
        if len(player.Characters) > 1:
            subPcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            subPcTextFormat["link"] = {
                "uri": MakeYtsheetUrl(player.Characters[1].YtsheetId)
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, subPcIndex + 1),
                    "format": {"textFormat": subPcTextFormat},
                }
            )

    # 合計行
    total: list = [None] * len(header)
    activeCountIndex: int = header.index("参加傾向")
    total[activeCountIndex - 1] = "合計"
    total[activeCountIndex] = list(
        map(lambda x: x[activeCountIndex], updateData)
    ).count(SpreadSheet.ACTIVE_STRING)

    total[subPcIndex] = list(
        map(lambda x: x[subPcIndex] != "", updateData)
    ).count(True)

    updateData.append(total)

    # ヘッダーを追加
    updateData.insert(0, header)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(header)  # type: ignore
    )


def UpdateBasicSheet(spreadsheet: Spreadsheet, players: list[Player]) -> None:
    """基本シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("基本")
    updateData: list[list] = []

    # ヘッダー
    header: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "PL",
        "種族",
        "種族\nマイナーチェンジ除く",
        "年齢",
        "性別",
        "身長",
        "体重",
        "信仰",
        "ヴァグランツ",
        "穢れ",
        "参加",
        "GM",
        "参加+GM",
        "ガメル",
        "死亡",
    ]

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # PL
            row.append(player.Name)

            # 種族
            row.append(character.GetMinorRace())

            # 種族(マイナーチェンジ除く)
            row.append(character.GetMajorRace())

            # 年齢
            row.append(character.Age)

            # 性別
            row.append(character.Gender)

            # 身長
            row.append(character.Height)

            # 体重
            row.append(character.Weight)

            # 信仰
            row.append(character.Faith)

            # ヴァグランツ
            row.append(
                SpreadSheet.TRUE_STRING if character.IsVagrants() else ""
            )

            # 穢れ
            row.append(character.Sin)

            # 参加
            playerTimes: int = character.PlayerTimes
            row.append(playerTimes)

            # GM
            gameMasterTimes: int = character.GameMasterTimes
            row.append(gameMasterTimes)

            # 参加+GM
            row.append(playerTimes + gameMasterTimes)

            # ガメル
            row.append(character.HistoryMoneyTotal)

            # 死亡
            row.append(character.DiedTimes)

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = header.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1 + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    total: list = [None] * len(header)
    activeCountIndex: int = header.index("参加傾向")
    total[activeCountIndex - 1] = "合計"
    total[activeCountIndex] = list(
        map(lambda x: x[activeCountIndex], updateData)
    ).count(SpreadSheet.ACTIVE_STRING)

    VagrantsIndex: int = header.index("ヴァグランツ")
    total[VagrantsIndex] = list(
        map(lambda x: x[VagrantsIndex], updateData)
    ).count(SpreadSheet.TRUE_STRING)

    diedIndex: int = header.index("死亡")
    total[diedIndex] = sum(
        list(
            map(
                lambda x: (x[diedIndex]),
                updateData,
            )
        )
    )
    updateData.append(total)

    # ヘッダーを追加
    updateData.insert(0, header)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(header)  # type: ignore
    )


def UpdateCombatSkillSheet(
    spreadsheet: Spreadsheet, players: list[Player]
) -> None:
    """技能シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("技能")
    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "信仰",
        "Lv",
        "経験点\nピンゾロ含む",
        "ピンゾロ",
    ]
    for skill in SwordWorld.SKILLS.values():
        headers.append(skill)

    formats: list[CellFormat] = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 信仰
            row.append(character.Faith)

            # Lv
            row.append(character.Level)

            # 経験点
            row.append(character.Exp)

            # ピンゾロ
            row.append(character.FumbleExp)

            # 技能レベル
            for skill in SwordWorld.SKILLS:
                row.append(character.Skills.get(skill, ""))

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1 + 1

            # 経験点の文字色
            expIndex: int = headers.index("経験点\nピンゾロ含む") + 1
            expTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            if character.ActiveStatus == ExpStatus.MAX:
                expTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 1, "green": 0, "blue": 0}
                }
                formats.append(
                    {
                        "range": utils.rowcol_to_a1(rowIndex, expIndex),
                        "format": {"textFormat": expTextFormat},
                    }
                )
            elif character.ActiveStatus == ExpStatus.INACTIVE:
                expTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 0, "green": 0, "blue": 1}
                }
                formats.append(
                    {
                        "range": utils.rowcol_to_a1(rowIndex, expIndex),
                        "format": {"textFormat": expTextFormat},
                    }
                )

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notSkillColumnCount: int = len(headers) - len(SwordWorld.SKILLS)
    total: list = [None] * notSkillColumnCount
    total[-1] = "合計"
    total += list(
        map(
            lambda x: list(
                map(lambda y: y[headers.index(x)] != "", updateData)
            ).count(True),
            SwordWorld.SKILLS.values(),
        )
    )
    updateData.append(total)

    # ヘッダーを縦書き用に変換
    displayHeader: list[str] = list(
        map(
            lambda x: ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.insert(0, displayHeader)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 技能レベルのヘッダー
    startA1: str = utils.rowcol_to_a1(1, notSkillColumnCount + 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )


def UpdateStatusSheet(spreadsheet: Spreadsheet, players: list[Player]) -> None:
    """能力値シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("能力値")
    updateData: list[list] = []

    # ヘッダー
    header: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "種族",
        "器用",
        "敏捷",
        "筋力",
        "生命",
        "知力",
        "精神",
        "成長",
        "HP",
        "MP",
        "生命抵抗力",
        "精神抵抗力",
        "魔物知識",
        "先制力",
        "ダイス平均",
        "備考",
    ]

    formats: list[CellFormat] = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # ダイス平均を計算
            racesStatus: dict = RACES_STATUSES[sub("（.*", "", character.Race)]
            diceAverage: float = (
                character.Dexterity.Base
                + character.Agility.Base
                + character.Strength.Base
                + character.Vitality.Base
                + character.Intelligence.Base
                + character.Mental.Base
                - racesStatus["fixedValue"]
            ) / racesStatus["diceCount"]

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 種族
            row.append(character.GetMinorRace())

            # 器用
            row.append(
                character.Technic + character.Dexterity.GetTotalStatus()
            )

            # 敏捷
            row.append(character.Technic + character.Agility.GetTotalStatus())

            # 筋力
            row.append(
                character.Physical + character.Strength.GetTotalStatus()
            )

            # 生命
            row.append(
                character.Physical + character.Vitality.GetTotalStatus()
            )

            # 知力
            row.append(
                character.Spirit + character.Intelligence.GetTotalStatus()
            )

            # 精神
            row.append(character.Spirit + character.Mental.GetTotalStatus())

            # 成長
            row.append(character.GrowthTimes)

            # HP
            row.append(character.Hp)

            # MP
            row.append(character.Mp)

            # 生命抵抗力
            row.append(character.LifeResistance)

            # 精神抵抗力
            row.append(character.SpiritResistance)

            # 魔物知識
            row.append(character.MonsterKnowledge)

            # 先制力
            row.append(character.Initiative)

            # ダイス平均
            row.append(diceAverage)

            # 備考
            if character.Birth == "冒険者":
                row.append("※冒険者")

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1 + 1

            # PC列のハイパーリンク
            pcIndex: int = header.index("PC") + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

            # ダイス平均4.5を超える場合は赤文字
            if diceAverage > 4.5:
                diceAverageIndex: int = header.index("ダイス平均") + 1
                diceAverageTextFormat: dict = (
                    SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
                )
                diceAverageTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 1, "green": 0, "blue": 0}
                }
                formats.append(
                    {
                        "range": utils.rowcol_to_a1(
                            rowIndex, diceAverageIndex
                        ),
                        "format": {"textFormat": diceAverageTextFormat},
                    }
                )

    # ヘッダーを追加
    updateData.insert(0, header)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # ダイス平均
    diceAverageIndex: int = header.index("ダイス平均") + 1
    startA1: str = utils.rowcol_to_a1(1, diceAverageIndex)
    endA1: str = utils.rowcol_to_a1(len(updateData), diceAverageIndex)
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData), len(header)  # type: ignore
    )


def UpdateAbilitySheet(
    spreadsheet: Spreadsheet, players: list[Player]
) -> None:
    """戦闘特技シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("戦闘特技")
    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "バトルダンサー",
        "Lv.1",
        "Lv.3",
        "Lv.5",
        "Lv.7",
        "Lv.9",
        "Lv.11",
        "Lv.13",
        "Lv.15",
        "自動取得",
    ]

    formats: list[CellFormat] = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # バトルダンサー
            row.append(character.CombatFeatsLv1bat)

            # Lv.1
            row.append(character.CombatFeatsLv1)

            # Lv.3
            row.append(character.CombatFeatsLv3)

            # Lv.5
            row.append(character.CombatFeatsLv5)

            # Lv.7
            row.append(character.CombatFeatsLv7)

            # Lv.9
            row.append(character.CombatFeatsLv9)

            # Lv.11
            row.append(character.CombatFeatsLv11)

            # Lv.13
            row.append(character.CombatFeatsLv13)

            # Lv.15
            row.append(character.CombatFeatsLv15)

            # 自動取得
            for autoCombatFeat in character.AutoCombatFeats:
                row.append(autoCombatFeat)

            updateData.append(row)

            # 書式設定
            rowIndex: int = updateData.index(row) + 1 + 1

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

            # 習得レベルに満たないものはグレーで表示
            grayOutStartIndex: Union[int, None] = None
            for level in range(3, 15, 2):
                if character.Level < level:
                    grayOutStartIndex = headers.index(f"Lv.{level}") + 1
                    break

            if grayOutStartIndex is not None:
                grayOutEndIndex: int = headers.index("Lv.15") + 1
                grayOutTextFormat: dict = (
                    SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
                )
                grayOutTextFormat["foregroundColorStyle"] = {
                    "rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}
                }
                startA1: str = utils.rowcol_to_a1(rowIndex, grayOutStartIndex)
                endA1: str = utils.rowcol_to_a1(rowIndex, grayOutEndIndex)
                formats.append(
                    {
                        "range": f"{startA1}:{endA1}",
                        "format": {"textFormat": grayOutTextFormat},
                    }
                )

                # バトルダンサー未習得もグレーで表示
                if character.Skills.get("lvBat", 0) == 0:
                    battleDancerIndex: int = (
                        headers.index("バトルダンサー") + 1
                    )
                    battleDancerA1: str = utils.rowcol_to_a1(
                        rowIndex, battleDancerIndex
                    )
                    formats.append(
                        {
                            "range": f"{battleDancerA1}:{battleDancerA1}",
                            "format": {"textFormat": grayOutTextFormat},
                        }
                    )

    # ヘッダーを追加
    updateData.insert(0, headers)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), worksheet.col_count)
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData), worksheet.col_count  # type: ignore
    )


def UpdateHonorSheet(spreadsheet: Spreadsheet, players: list[Player]) -> None:
    """名誉点・流派シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("名誉点・流派")
    updateData: list[list] = []

    # ヘッダー
    headers: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "冒険者ランク",
        "累計名誉点",
        "加入数",
        "未加入",
        "2.0流派",
    ]
    for style in SwordWorld.STYLES:
        headers.append(style.Name)

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # 流派の情報を取得
            is20: bool = False
            learnedStyles: list[str] = []
            for style in SwordWorld.STYLES:
                learnedStyle: str = ""
                if style in character.Styles:
                    # 該当する流派に入門している
                    learnedStyle = SpreadSheet.TRUE_STRING
                    if style.Is20:
                        is20 = True

                learnedStyles.append(learnedStyle)

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 冒険者ランク
            row.append(character.AdventurerRank)

            # 累計名誉点
            row.append(character.TotalHonor)

            # 加入数
            learningCount: int = learnedStyles.count(SpreadSheet.TRUE_STRING)
            row.append(learningCount)

            # 未加入
            row.append(SpreadSheet.TRUE_STRING if learningCount == 0 else "")

            # 2.0流派
            row.append(SpreadSheet.TRUE_STRING if is20 else "")

            # 各流派
            row += learnedStyles

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1 + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notTotalColumnCount: int = 5
    total: list = [None] * notTotalColumnCount
    total[-1] = "合計"
    total.append(
        sum(
            list(
                map(
                    lambda x: (x[headers.index("加入数")]),
                    updateData,
                )
            )
        )
    )
    total.append(
        list(map(lambda x: x[headers.index("未加入")], updateData)).count(
            SpreadSheet.TRUE_STRING
        )
    )
    total.append(
        list(map(lambda x: x[headers.index("2.0流派")], updateData)).count(
            SpreadSheet.TRUE_STRING
        )
    )

    # 各流派
    total += list(
        map(
            lambda x: list(
                map(lambda y: y[headers.index(x.Name)], updateData)
            ).count(SpreadSheet.TRUE_STRING),
            SwordWorld.STYLES,
        )
    )
    updateData.append(total)

    # ヘッダーを追加
    displayHeaders: list[str] = list(
        map(
            lambda x: ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.insert(0, displayHeaders)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 流派のヘッダー
    startA1 = utils.rowcol_to_a1(1, notTotalColumnCount + 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # ○
    startA1 = utils.rowcol_to_a1(2, headers.index("未加入") + 1)
    endA1: str = utils.rowcol_to_a1(len(updateData) - 1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"horizontalAlignment": "CENTER"},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )


def UpdateAbyssCurseSheet(
    spreadsheet: Spreadsheet, players: list[Player]
) -> None:
    """アビスカースシートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("アビスカース")
    updateData: list[list] = []

    # ヘッダー
    headers: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "アビスカースの数",
    ]
    for abyssCurse in SwordWorld.ABYSS_CURSES:
        headers.append(abyssCurse)

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # アビスカースの情報を取得
            receivedCurses: list[str] = []
            receivedCursesString: str = ""
            for abyssCurse in SwordWorld.ABYSS_CURSES:
                receivedCurse: str = ""
                if abyssCurse in character.AbyssCurses:
                    receivedCurse = SpreadSheet.TRUE_STRING
                    receivedCursesString += abyssCurse

                receivedCurses.append(receivedCurse)

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(receivedCursesString + character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 数
            cursesCount: int = receivedCurses.count(SpreadSheet.TRUE_STRING)
            row.append(cursesCount)

            # 各アビスカース
            row += receivedCurses

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = headers.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1 + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    total: list = [None] * 3
    total[-1] = "合計"
    total.append(
        sum(
            list(
                map(
                    lambda x: x[headers.index("アビスカースの数")],
                    updateData,
                )
            )
        )
    )
    for abyssCurse in SwordWorld.ABYSS_CURSES:
        total.append(
            list(
                map(lambda x: x[headers.index(abyssCurse)], updateData)
            ).count(SpreadSheet.TRUE_STRING)
        )

    updateData.append(total)

    # ヘッダーを追加
    updateData.insert(0, headers)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # ○
    startA1 = utils.rowcol_to_a1(
        2, len(headers) - len(SwordWorld.ABYSS_CURSES) + 1
    )
    endA1: str = utils.rowcol_to_a1(len(updateData) - 1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"horizontalAlignment": "CENTER"},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )


def UpdateGeneralSkillSheet(
    spreadsheet: Spreadsheet, players: list[Player]
) -> None:
    """一般技能シートを更新

    Args:
        spreadsheet Spreadsheet: スプレッドシート
        players list[Player]: PL情報
    """

    worksheet: Worksheet = spreadsheet.worksheet("一般技能")
    updateData: list[list] = []

    # ヘッダー
    headers: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "公式技能",
        "オリジナル技能",
    ]
    for officialGeneralSkillName in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES:
        headers.append(officialGeneralSkillName)

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            # 公式一般技能のレベル取得
            officialGeneralSkills: list[GeneralSkill] = list(
                filter(
                    lambda x: x.Name
                    in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES,
                    character.GeneralSkills,
                )
            )
            officialGeneralSkillLevels: list[Union[int, None]] = [None] * len(
                SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES
            )
            for officialGeneralSkill in officialGeneralSkills:
                officialGeneralSkillLevels[
                    SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES.index(
                        officialGeneralSkill.Name
                    )
                ] = officialGeneralSkill.Level

            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # 公式技能
            row.append(
                "\n".join([x.getFormattedStr() for x in officialGeneralSkills])
            )

            # オリジナル技能
            row.append(
                "\n".join(
                    [
                        x.getFormattedStr()
                        for x in list(
                            filter(
                                lambda x: x.Name
                                not in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES,
                                character.GeneralSkills,
                            )
                        )
                    ]
                )
            )

            # 公式技能
            row += officialGeneralSkillLevels

            updateData.append(row)

            # PC列のハイパーリンク
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(
                        updateData.index(row) + 1 + 1, headers.index("PC") + 1
                    ),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    notTotalColumnCount: int = len(headers) - len(
        SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES
    )
    total: list = [None] * notTotalColumnCount
    total[-1] = "合計"
    for officialGeneralSkillName in SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES:
        total.append(
            list(
                map(
                    lambda x: x[headers.index(officialGeneralSkillName)]
                    is not None,
                    updateData,
                )
            ).count(True)
        )

    updateData.append(total)

    # ヘッダーを追加
    displayHeaders: list[str] = list(
        map(
            lambda x: ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.insert(0, displayHeaders)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 縦書きヘッダー
    startA1 = utils.rowcol_to_a1(1, notTotalColumnCount + 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # ヘッダー以外
    startA1 = utils.rowcol_to_a1(2, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"verticalAlignment": "MIDDLE"},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )
