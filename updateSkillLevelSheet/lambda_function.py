# -*- coding: utf-8 -*-


from itertools import chain
from json import loads
from re import search
from unicodedata import normalize

from boto3 import resource
from google.oauth2 import service_account
from gspread import authorize, utils, worksheet

"""
技能シートを更新
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

# GoogleServiceAccountsテーブルのid
GOOGLE_SERVIE_ACCOUNT_ID: int = 1

# DBコネクション
Dynamodb = None

# 技能シート
Sheet: worksheet = None

# ピンゾロの表記ゆれ対応
FumbleTitles: "list[str]" = [
    "ファンブル",
    "50点",
    "ゾロ",
    "ソロ",
]

# 備考欄のピンゾロ回数表記ゆれ対応
FumbleCountPrefixes: "list[str]" = list(
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
            FumbleTitles,
        )
    )
)

# シート全体に適用するテキストの書式
DefaultTextFormat = {
    "fontFamily": "Meiryo",
}


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId = event["SpreadsheetId"]
    levelCap = event["LevelCap"]
    maxExp = int(levelCap["MaxExp"])
    minimumExp = int(levelCap["MinimumExp"])

    # 初期化
    init(spreadsheetId)

    # ゆとシートのデータを取得
    players = getPlayers()

    # 更新
    updateSheet(players, maxExp, minimumExp)


def init(spreadsheetId: str):
    """

    初期化

    Args:
        spreadsheetId str: スプレッドシートのID
    """
    global Dynamodb, Sheet

    Dynamodb = resource("dynamodb", region_name=AWS_REGION)

    # DBからスプレッドシートのIDを取得
    googleServiceAccounts = Dynamodb.Table("GoogleServiceAccounts")
    response = googleServiceAccounts.get_item(
        Key={"id": GOOGLE_SERVIE_ACCOUNT_ID}
    )
    googleServiceAccount = response["Item"]

    # サービスアカウントでスプレッドシートにログイン
    credentials = service_account.Credentials.from_service_account_info(
        googleServiceAccount["json"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = authorize(credentials)

    # 技能シートを開く
    book = client.open_by_key(spreadsheetId)
    Sheet = book.worksheet("技能")


def getPlayers():
    """DBからプレイヤー情報を取得

    容量が大きいためStep Functionsでは対応不可

    """
    global Dynamodb

    teble = Dynamodb.Table("Players")
    response = teble.scan()

    # ページ分割分を取得
    players = list()
    while "LastEvaluatedKey" in response:
        players.extend(response["Items"])
        response = teble.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    players.extend(response["Items"])

    # idでソート
    players.sort(key=lambda player: player["id"])

    return players


def updateSheet(players: "list[dict]", maxExp: int, minimumExp: int):
    """

    シートを更新

    Args:
        spreadsheetId str: スプレッドシートのID
        maxExp int: 経験点の上限
        minimumExp int: 経験点の下限
    """
    global Sheet

    totalFumbleRegexp = "|".join(list(map(normalizeString, FumbleTitles)))
    fumbleCountRegexps = list(
        map(
            lambda x: rf"(?<={x})\d+",
            map(normalizeString, FumbleCountPrefixes),
        )
    )

    updateData = []

    # ヘッダー
    headers = [
        "No.",
        "PC",
        "信仰",
        "Lv",
        "経験点\nピンゾロ含む",
        "ピンゾロ",
        "ファイター",
        "フェンサー",
        "グラップラー",
        "バトルダンサー",
        "シューター",
        "スカウト",
        "レンジャー",
        "セージ",
        "エンハンサー",
        "バード",
        "アルケミスト",
        "ライダー",
        "ジオマンサー",
        "ウォーリーダー",
        "ソーサラー",
        "コンジャラー",
        "プリースト",
        "マギテック",
        "フェアリーテイマー",
        "ドルイド",
        "デーモンルーラー",
    ]
    # 縦書きの伸ばし棒を置換
    displayHeader = list(
        map(
            lambda x: x.replace("ー", "｜"),
            headers,
        )
    )
    updateData.append(displayHeader)

    skills = [
        {"key": "lvFig", "index": headers.index("ファイター")},
        {"key": "lvFen", "index": headers.index("フェンサー")},
        {"key": "lvGra", "index": headers.index("グラップラー")},
        {"key": "lvBat", "index": headers.index("バトルダンサー")},
        {"key": "lvSho", "index": headers.index("シューター")},
        {"key": "lvSco", "index": headers.index("スカウト")},
        {"key": "lvRan", "index": headers.index("レンジャー")},
        {"key": "lvSag", "index": headers.index("セージ")},
        {"key": "lvEnh", "index": headers.index("エンハンサー")},
        {"key": "lvBar", "index": headers.index("バード")},
        {"key": "lvAlc", "index": headers.index("アルケミスト")},
        {"key": "lvRid", "index": headers.index("ライダー")},
        {"key": "lvGeo", "index": headers.index("ジオマンサー")},
        {"key": "lvWar", "index": headers.index("ウォーリーダー")},
        {"key": "lvSor", "index": headers.index("ソーサラー")},
        {"key": "lvCon", "index": headers.index("コンジャラー")},
        {"key": "lvPri", "index": headers.index("プリースト")},
        {"key": "lvMag", "index": headers.index("マギテック")},
        {"key": "lvFai", "index": headers.index("フェアリーテイマー")},
        {"key": "lvDru", "index": headers.index("ドルイド")},
        {"key": "lvDem", "index": headers.index("デーモンルーラー")},
    ]
    skillColumnCount = len(skills)
    notSkillColumnCount = len(headers) - skillColumnCount
    total = ([None] * notSkillColumnCount) + ([0] * skillColumnCount)
    formats = []
    for player in players:
        row = []
        ytsheetJson = loads(player["ytsheetJson"])

        # セッション履歴を集計
        historyNum = int(ytsheetJson["historyNum"])
        totalFumbleExp = 0
        fumbleCount = 0
        for i in range(1, historyNum):
            if f"history{i}Gm" not in ytsheetJson:
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
                # 備考からピンゾロ回数を集計
                normalizedNote = normalizeString(
                    ytsheetJson.get(f"history{i}Note", "")
                )
                for fumbleCountRegexp in fumbleCountRegexps:
                    fumbleCountMatch = search(
                        fumbleCountRegexp, normalizedNote
                    )
                    if fumbleCountMatch is not None:
                        fumbleCount += int(fumbleCountMatch.group(0))
                        break

        # ピンゾロ経験点は最大値を採用する(複数の書き方で書かれていた場合、重複して集計してしまうため)
        fumbleExp = max(totalFumbleExp, fumbleCount * 50)

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(int(player["id"]))

        # PC
        row.append(ytsheetJson["characterName"])

        # 信仰
        row.append(ytsheetJson.get("faith", "なし"))

        # Lv
        row.append(ytsheetJson["level"])

        # 経験点
        expTotal = int(ytsheetJson["expTotal"])
        row.append(expTotal)

        # ピンゾロ
        row.append(fumbleExp)

        # 技能レベル
        for skill in skills:
            level = ytsheetJson.get(skill["key"], "0")
            if level == "0":
                # 技能レベル0は表示しない
                level = None
            if level is not None:
                # 合計を加算
                total[skill["index"]] += 1
            row.append(level)

        updateData.append(row)

        # 書式設定
        rowIndex = updateData.index(row) + 1

        # 経験点の文字色
        expIndex = row.index(expTotal) + 1
        expTextFormat = DefaultTextFormat.copy()
        if expTotal >= maxExp:
            expTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 1, "green": 0, "blue": 0}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, expIndex),
                    "format": {"textFormat": expTextFormat},
                }
            )
        elif expTotal < minimumExp:
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
        pcIndex = row.index(ytsheetJson["characterName"]) + 1
        rowIndex = updateData.index(row) + 1
        pcTextFormat = DefaultTextFormat.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

    # 合計行
    total[notSkillColumnCount - 1] = "合計"
    updateData.append(total)

    # クリア
    Sheet.clear()

    # 更新
    Sheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(len(updateData), len(headers))
    Sheet.format(
        f"{startA1}:{endA1}",
        {
            "textFormat": {
                "fontFamily": "Meiryo",
            },
        },
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"horizontalAlignment": "CENTER"},
        }
    )

    # 技能レベルのヘッダー
    startA1 = utils.rowcol_to_a1(1, notSkillColumnCount + 1)
    endA1 = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # 部分的なフォーマットを設定
    Sheet.batch_format(formats)

    # 行列の固定
    Sheet.freeze(1, 2)

    # フィルター
    Sheet.set_basic_filter(1, 1, len(updateData) - 1, len(headers))


def normalizeString(string: str) -> str:
    """

    文字列を正規化

    Args:
        string str: 正規化する文字列

    Returns:
        str: 正規化した文字列
    """
    result = string.translate(
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
    result = normalize("NFKC", result)
    return result


def calculateFromString(string: str) -> int:
    """

    四則演算の文字列から解を求める

    Args:
        string str: 計算する文字列

    Returns:
        int: 解
    """
    notCalcRegexp = r"[^0-9\+\-\*\/\(\)]"
    if search(string, notCalcRegexp):
        # 四則演算以外の文字列が含まれる
        return 0

    return eval(string)
