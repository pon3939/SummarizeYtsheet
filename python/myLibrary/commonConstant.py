# -*- coding: utf-8 -*-

"""
汎用定数
"""

# スプレッドシート全体に適用するテキストの書式
DEFAULT_TEXT_FORMAT: dict = {
    "fontFamily": "Meiryo",
}

# スプレッドシート全体に適用する書式
DEFAULT_FORMAT: dict = {
    "textFormat": DEFAULT_TEXT_FORMAT,
}

# ヘッダーに適用する書式
HEADER_DEFAULT_FORMAT: dict = {
    "horizontalAlignment": "CENTER",
}

# 戦闘技能
SKILLS: "list[dict]" = [
    {"key": "lvFig", "name": "ファイター"},
    {"key": "lvFen", "name": "フェンサー"},
    {"key": "lvGra", "name": "グラップラー"},
    {"key": "lvBat", "name": "バトルダンサー"},
    {"key": "lvSho", "name": "シューター"},
    {"key": "lvSco", "name": "スカウト"},
    {"key": "lvRan", "name": "レンジャー"},
    {"key": "lvSag", "name": "セージ"},
    {"key": "lvEnh", "name": "エンハンサー"},
    {"key": "lvBar", "name": "バード"},
    {"key": "lvAlc", "name": "アルケミスト"},
    {"key": "lvRid", "name": "ライダー"},
    {"key": "lvGeo", "name": "ジオマンサー"},
    {"key": "lvWar", "name": "ウォーリーダー"},
    {"key": "lvSor", "name": "ソーサラー"},
    {"key": "lvCon", "name": "コンジャラー"},
    {"key": "lvPri", "name": "プリースト"},
    {"key": "lvMag", "name": "マギテック"},
    {"key": "lvFai", "name": "フェアリーテイマー"},
    {"key": "lvDru", "name": "ドルイド"},
    {"key": "lvDem", "name": "デーモンルーラー"},
]

# ゆとシートから取得したJSONのキーのうち、各能力値に関係するもの
STATUS_KEYS: "list[dict]" = [
    # 器用
    {
        "name": "器用",
        "key": "dexterity",
        "htb": "sttBaseTec",
        "baseStatus": "sttBaseA",
        "increasedStatus": "sttGrowA",
        "additionalStatus": "sttAddA",
    },
    # 敏捷
    {
        "name": "敏捷",
        "key": "agility",
        "htb": "sttBaseTec",
        "baseStatus": "sttBaseB",
        "increasedStatus": "sttGrowB",
        "additionalStatus": "sttAddB",
    },
    # 筋力
    {
        "name": "筋力",
        "key": "strength",
        "htb": "sttBasePhy",
        "baseStatus": "sttBaseC",
        "increasedStatus": "sttGrowC",
        "additionalStatus": "sttAddC",
    },
    # 生命力
    {
        "name": "生命",
        "key": "vitality",
        "htb": "sttBasePhy",
        "baseStatus": "sttBaseD",
        "increasedStatus": "sttGrowD",
        "additionalStatus": "sttAddD",
    },
    # 知力1
    {
        "name": "知力",
        "key": "intelligence",
        "htb": "sttBaseSpi",
        "baseStatus": "sttBaseE",
        "increasedStatus": "sttGrowE",
        "additionalStatus": "sttAddE",
    },
    # 精神力
    {
        "name": "精神",
        "key": "mental",
        "htb": "sttBaseSpi",
        "baseStatus": "sttBaseF",
        "increasedStatus": "sttGrowF",
        "additionalStatus": "sttAddF",
    },
]
