# -*- coding: utf-8 -*-

"""
汎用定数
"""

# AWSのリージョン
AWS_REGION: str = "ap-northeast-1"

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
    "textRotation": {"vertical": False},
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
        "htb": "technic",
        "baseStatus": "sttBaseA",
        "increasedStatus": "sttGrowA",
        "additionalStatus": "sttAddA",
    },
    # 敏捷
    {
        "name": "敏捷",
        "key": "agility",
        "htb": "technic",
        "baseStatus": "sttBaseB",
        "increasedStatus": "sttGrowB",
        "additionalStatus": "sttAddB",
    },
    # 筋力
    {
        "name": "筋力",
        "key": "strength",
        "htb": "physical",
        "baseStatus": "sttBaseC",
        "increasedStatus": "sttGrowC",
        "additionalStatus": "sttAddC",
    },
    # 生命力
    {
        "name": "生命",
        "key": "vitality",
        "htb": "physical",
        "baseStatus": "sttBaseD",
        "increasedStatus": "sttGrowD",
        "additionalStatus": "sttAddD",
    },
    # 知力1
    {
        "name": "知力",
        "key": "intelligence",
        "htb": "spirit",
        "baseStatus": "sttBaseE",
        "increasedStatus": "sttGrowE",
        "additionalStatus": "sttAddE",
    },
    # 精神力
    {
        "name": "精神",
        "key": "mental",
        "htb": "spirit",
        "baseStatus": "sttBaseF",
        "increasedStatus": "sttGrowF",
        "additionalStatus": "sttAddF",
    },
]

# 流派
STYLES: "list[dict]" = [
    {
        "name": "イーヴァル狂闘術",
        "keywordRegexp": "|".join(
            [
                "イーヴァル",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ミハウ式流円闘技",
        "keywordRegexp": "|".join(
            [
                "ミハウ",
            ]
        ),
        "is20": False,
    },
    {
        "name": "カスロット豪砂拳・バタス派",
        "keywordRegexp": "|".join(["カスロット", "バタス"]),
        "is20": False,
    },
    {
        "name": "マカジャハット・プロ・グラップリング",
        "keywordRegexp": "|".join(
            [
                "マカジャハット",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ナルザラント柔盾活用術",
        "keywordRegexp": "|".join(
            [
                "ナルザラント",
            ]
        ),
        "is20": False,
    },
    {
        "name": "アースト強射術",
        "keywordRegexp": "|".join(
            [
                "アースト",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ヒアデム魔力流転操撃",
        "keywordRegexp": "|".join(
            [
                "ヒアデム",
            ]
        ),
        "is20": False,
    },
    {
        "name": "古モルガナンシン王国式戦域魔導術",
        "keywordRegexp": "|".join(
            [
                "モルガナンシン",
                "モルガナシン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ダイケホーン双霊氷法",
        "keywordRegexp": "|".join(
            [
                "ダイケホーン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "スホルテン騎乗戦技",
        "keywordRegexp": "|".join(
            [
                "スホルテン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "アードリアン流古武道・メルキアノ道場",
        "keywordRegexp": "|".join(["アードリアン", "メルキアノ"]),
        "is20": False,
    },
    {
        "name": "エルエレナ惑乱操布術",
        "keywordRegexp": "|".join(
            [
                "エルエレナ",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ファイラステン古流ヴィンド派(双剣の型)",
        "keywordRegexp": "|".join(["ファイラステン", "ヴィンド"]),
        "is20": False,
    },
    {
        "name": "クウェラン闇弓術改式",
        "keywordRegexp": "|".join(
            [
                "クウェラン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ヴァルト式戦場剣殺法",
        "keywordRegexp": "|".join(
            [
                "ヴァルト",
            ]
        ),
        "is20": False,
    },
    {
        "name": "ガオン無双獣投術",
        "keywordRegexp": "|".join(
            [
                "ガオン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "聖戦士ローガン鉄壁の型",
        "keywordRegexp": "|".join(
            [
                "ローガン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "クーハイケン強竜乗法",
        "keywordRegexp": "|".join(
            [
                "クーハイケン",
            ]
        ),
        "is20": False,
    },
    {
        "name": "キルガリー双刃戦舞闘技",
        "keywordRegexp": "|".join(
            [
                "キルガリー",
            ]
        ),
        "is20": False,
    },
    {
        "name": "エステル式ポール舞闘術",
        "keywordRegexp": "|".join(["エステル", "ポール"]),
        "is20": False,
    },
    {
        "name": "銛王ナイネルガの伝承",
        "keywordRegexp": "|".join(
            [
                "ナイネルガ",
            ]
        ),
        "is20": False,
    },
    {
        "name": "死骸銃遊戯",
        "keywordRegexp": "|".join(
            [
                "死骸銃",
            ]
        ),
        "is20": False,
    },
    {
        "name": "対奈落教会議・奈落反転神術",
        "keywordRegexp": "|".join(
            [
                "奈落",
            ]
        ),
        "is20": False,
    },
    {
        "name": "「七色のマナ」式召異魔法術・魔使影光学理論",
        "keywordRegexp": "|".join(["式召異", "魔使影"]),
        "is20": False,
    },
    {
        "name": "七色のマナ：魔法行使法学派",
        "keywordRegexp": "|".join(["七色のマナ：", "七色のマナ:", "魔法行使"]),
        "is20": False,
    },
    {
        "name": "アゴウ重槌破闘術",
        "keywordRegexp": "|".join(
            [
                "アゴウ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "岩流斧闘術アズラック派",
        "keywordRegexp": "|".join(
            [
                "アズラック",
            ]
        ),
        "is20": True,
    },
    {
        "name": "リシバル集団運槍術",
        "keywordRegexp": "|".join(
            [
                "リシバル",
            ]
        ),
        "is20": True,
    },
    {
        "name": "イーリー流幻闘道化術",
        "keywordRegexp": "|".join(
            [
                "イーリー",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ギルヴァン流愚人剣",
        "keywordRegexp": "|".join(
            [
                "ギルヴァン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ネレホーサ舞剣術",
        "keywordRegexp": "|".join(
            [
                "ネレホーサ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ドーザコット潜弓道",
        "keywordRegexp": "|".join(
            [
                "ドーザコット",
            ]
        ),
        "is20": True,
    },
    {
        "name": "マルガ＝ハーリ天地銃剣術",
        "keywordRegexp": "|".join(
            [
                "マルガ",
                "ハーリ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ライロック魔刃術",
        "keywordRegexp": "|".join(
            [
                "ライロック",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ルシェロイネ魔導術",
        "keywordRegexp": "|".join(
            [
                "ルシェロイネ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "クラウゼ流一刀魔王剣",
        "keywordRegexp": "|".join(
            [
                "クラウゼ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ベネディクト流紳士杖道",
        "keywordRegexp": "|".join(
            [
                "ベネディクト",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ハーデン鷹爪流投擲術",
        "keywordRegexp": "|".join(
            [
                "ハーデン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "エイントゥク十字弓道場",
        "keywordRegexp": "|".join(
            [
                "エイントゥク",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ジアンブリック攻盾法",
        "keywordRegexp": "|".join(
            [
                "ジアンブリック",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ルキスラ銀鱗隊護衛術",
        "keywordRegexp": "|".join(
            [
                "ルキスラ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ティルダンカル古代光魔党",
        "keywordRegexp": "|".join(
            [
                "ティルダンカル",
            ]
        ),
        "is20": True,
    },
    {
        "name": "カサドリス戦奏術",
        "keywordRegexp": "|".join(
            [
                "カサドリス",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ファルネアス重装馬闘技",
        "keywordRegexp": "|".join(
            [
                "ファルネアス",
            ]
        ),
        "is20": True,
    },
    {
        "name": "タマフ＝ダツエ流浪戦瞳",
        "keywordRegexp": "|".join(
            [
                "タマフ",
                "ダツエ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ドバルス螺旋運手",
        "keywordRegexp": "|".join(
            [
                "ドバルス",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ニルデスト流実戦殺法",
        "keywordRegexp": "|".join(
            [
                "ニルデスト",
            ]
        ),
        "is20": True,
    },
    {
        "name": "オーロンセシーレ中隊軽装突撃術",
        "keywordRegexp": "|".join(
            [
                "オーロンセシーレ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ラステンルフト双盾護身術",
        "keywordRegexp": "|".join(
            [
                "ラステンルフト",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ホプレッテン機動重弩弓法",
        "keywordRegexp": "|".join(
            [
                "ホプレッテン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "エイスンアデアル召喚術",
        "keywordRegexp": "|".join(
            [
                "エイスンアデアル",
            ]
        ),
        "is20": True,
    },
    {
        "name": "眠り猫流擬態術",
        "keywordRegexp": "|".join(
            [
                "眠り猫",
            ]
        ),
        "is20": True,
    },
    {
        "name": "カンフォーラ博物学派",
        "keywordRegexp": "|".join(
            [
                "カンフォーラ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "不死者討滅武技バニシングデス",
        "keywordRegexp": "|".join(
            [
                "バニシングデス",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ダルポン流下克戦闘術",
        "keywordRegexp": "|".join(
            [
                "ダルボン",
                "ダルポン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ヴェルクンスト砦建築一党",
        "keywordRegexp": "|".join(
            [
                "ヴェルクンスト",
            ]
        ),
        "is20": True,
    },
    {
        "name": "神速確勝ボルンの精髄",
        "keywordRegexp": "|".join(
            [
                "ボルン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "バルナッド英雄庭流派・封神舞踏剣",
        "keywordRegexp": "|".join(
            [
                "バルナッド",
            ]
        ),
        "is20": True,
    },
    {
        "name": "森の吹き矢使いたち",
        "keywordRegexp": "|".join(
            [
                "吹き矢",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ウォーディアル流竜騎神槍",
        "keywordRegexp": "|".join(
            [
                "ウォーディアル",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ギルツ屠竜輝剛拳",
        "keywordRegexp": "|".join(
            [
                "ギルツ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ガドハイ狩猟術",
        "keywordRegexp": "|".join(
            [
                "ガドハイ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ソソ破皇戦槌術",
        "keywordRegexp": "|".join(
            [
                "ソソ",
            ]
        ),
        "is20": True,
    },
    {
        "name": "バルカン流召精術",
        "keywordRegexp": "|".join(
            [
                "バルカン",
            ]
        ),
        "is20": True,
    },
    {
        "name": "ジーズドルフ騎竜術",
        "keywordRegexp": "|".join(
            [
                "ジーズドルフ",
            ]
        ),
        "is20": True,
    },
]

# アビスカース
ABYSS_CURSES: "list[str]" = [
    "自傷の",
    "嘆きの",
    "優しき",
    "差別の",
    "脆弱な",
    "無謀な",
    "重い",
    "難しい",
    "軟弱な",
    "病弱な",
    "過敏な",
    "陽気な",
    "たどたどしい",
    "代弁する",
    "施しは受けない",
    "死に近い",
    "おしゃれな",
    "マナを吸う",
    "鈍重な",
    "定まらない",
    "錯乱の",
    "足絡みの",
    "滑り落ちる",
    "悪臭放つ",
    "醜悪な",
    "唸る",
    "ふやけた",
    "古傷の",
    "まばゆい",
    "栄光なき",
    "正直者の",
    "乗り物酔いの",
    "碧を厭う",
    "我慢できない",
    "つきまとう",
    "のろまな",
]

# 参加傾向のセルの値
ENTRY_TREND_ACTIVE: str = "アクティブ"
ENTRY_TREND_INACTIVE: str = ""
