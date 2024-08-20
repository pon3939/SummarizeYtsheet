# -*- coding: utf-8 -*-

from MyLibrary.Style import Style

"""
SW2.5関係の定数
"""

# 戦闘技能
BATTLE_DANCER_LEVEL_KEY: str = "lvBat"
SKILLS: dict[str, str] = {
    "lvFig": "ファイター",
    "lvFen": "フェンサー",
    "lvGra": "グラップラー",
    BATTLE_DANCER_LEVEL_KEY: "バトルダンサー",
    "lvSho": "シューター",
    "lvSco": "スカウト",
    "lvRan": "レンジャー",
    "lvSag": "セージ",
    "lvEnh": "エンハンサー",
    "lvBar": "バード",
    "lvAlc": "アルケミスト",
    "lvRid": "ライダー",
    "lvGeo": "ジオマンサー",
    "lvWar": "ウォーリーダー",
    "lvSor": "ソーサラー",
    "lvCon": "コンジャラー",
    "lvPri": "プリースト",
    "lvMag": "マギテック",
    "lvFai": "フェアリーテイマー",
    "lvDru": "ドルイド",
    "lvDem": "デーモンルーラー",
    "lvPhy": "フィジカルマスター",
}

# 流派
STYLES: "list[Style]" = [
    Style("イーヴァル狂闘術", ["イーヴァル"]),
    Style("ミハウ式流円闘技", ["ミハウ"]),
    Style("カスロット豪砂拳・バタス派", ["カスロット", "バタス"]),
    Style("マカジャハット・プロ・グラップリング", ["マカジャハット"]),
    Style("ナルザラント柔盾活用術", ["ナルザラント"]),
    Style("アースト強射術", ["アースト"]),
    Style("ヒアデム魔力流転操撃", ["ヒアデム"]),
    Style("古モルガナンシン王国式戦域魔導術", ["モルガナンシン"]),
    Style("ダイケホーン双霊氷法", ["ダイケホーン"]),
    Style("スホルテン騎乗戦技", ["スホルテン"]),
    Style(
        "アードリアン流古武道・メルキアノ道場", ["アードリアン", "メルキアノ"]
    ),
    Style("エルエレナ惑乱操布術", ["エルエレナ"]),
    Style("ファイラステン古流ヴィンド派(双剣の型)", ["ファイラステン"]),
    Style("クウェラン闇弓術改式", ["クウェラン"]),
    Style("ヴァルト式戦場剣殺法", ["ヴァルト"]),
    Style("ガオン無双獣投術", ["ガオン"]),
    Style("聖戦士ローガン鉄壁の型", ["ローガン"]),
    Style("クーハイケン強竜乗法", ["クーハイケン"]),
    Style(
        "七色のマナ：魔法行使法学派",
        ["七色のマナ：", "七色のマナ:", "魔法行使"],
    ),
    Style("キルガリー双刃戦舞闘技", ["キルガリー"]),
    Style("エステル式ポール舞闘術", ["エステル", "ポール"]),
    Style("銛王ナイネルガの伝承", ["ナイネルガ"]),
    Style("死骸銃遊戯", ["死骸銃"]),
    Style("対奈落教会議・奈落反転神術", ["奈落"]),
    Style("「七色のマナ」式召異魔法術・魔使影光学理論", ["式召異", "魔使影"]),
    Style("アルショニ軽身跳闘法", ["アルショニ"]),
    Style("ノーザンファング鉱士削岩闘法", ["ノーザンファング"]),
    Style("キングスレイ式近接銃撃術", ["キングスレイ"]),
    Style("ネルネアニン騎獣調香術", ["ネルネアニン"]),
    Style("オルフィード式蒸発妖精術", ["オルフィード"]),
    Style("フィノア派森羅導術", ["フィノア"]),
    Style("アゴウ重槌破闘術", ["アゴウ"], True),
    Style("岩流斧闘術アズラック派", ["アズラック"], True),
    Style("リシバル集団運槍術", ["リシバル"], True),
    Style("イーリー流幻闘道化術", ["イーリー"], True),
    Style("ギルヴァン流愚人剣", ["ギルヴァン"], True),
    Style("ネレホーサ舞剣術", ["ネレホーサ"], True),
    Style("ドーザコット潜弓道", ["ドーザコット"], True),
    Style("マルガ＝ハーリ天地銃剣術", ["マルガ", "ハーリ"], True),
    Style("ライロック魔刃術", ["ライロック"], True),
    Style("ルシェロイネ魔導術", ["ルシェロイネ"], True),
    Style("クラウゼ流一刀魔王剣", ["クラウゼ"], True),
    Style("ベネディクト流紳士杖道", ["ベネディクト"], True),
    Style("ハーデン鷹爪流投擲術", ["ハーデン"], True),
    Style("エイントゥク十字弓道場", ["エイントゥク"], True),
    Style("ジアンブリック攻盾法", ["ジアンブリック"], True),
    Style("ルキスラ銀鱗隊護衛術", ["ルキスラ"], True),
    Style("ティルダンカル古代光魔党", ["ティルダンカル"], True),
    Style("カサドリス戦奏術", ["カサドリス"], True),
    Style("ファルネアス重装馬闘技", ["ファルネアス"], True),
    Style("タマフ＝ダツエ流浪戦瞳", ["タマフ", "ダツエ"], True),
    Style("ドバルス螺旋運手", ["ドバルス"], True),
    Style("ニルデスト流実戦殺法", ["ニルデスト"], True),
    Style("オーロンセシーレ中隊軽装突撃術", ["オーロンセシーレ"], True),
    Style("ラステンルフト双盾護身術", ["ラステンルフト"], True),
    Style("ホプレッテン機動重弩弓法", ["ホプレッテン"], True),
    Style("エイスンアデアル召喚術", ["エイスンアデアル"], True),
    Style("眠り猫流擬態術", ["眠り猫"], True),
    Style("カンフォーラ博物学派", ["カンフォーラ"], True),
    Style("不死者討滅武技バニシングデス", ["バニシングデス"], True),
    Style("ダルポン流下克戦闘術", ["ダルボン", "ダルポン"], True),
    Style("ヴェルクンスト砦建築一党", ["ヴェルクンスト"], True),
    Style("神速確勝ボルンの精髄", ["ボルン"], True),
    Style("バルナッド英雄庭流派・封神舞踏剣", ["バルナッド"], True),
    Style("森の吹き矢使いたち", ["吹き矢"], True),
    Style("ウォーディアル流竜騎神槍", ["ウォーディアル"], True),
    Style("ギルツ屠竜輝剛拳", ["ギルツ"], True),
    Style("ガドハイ狩猟術", ["ガドハイ"], True),
    Style("ソソ破皇戦槌術", ["ソソ"], True),
    Style("バルカン流召精術", ["バルカン"], True),
    Style("ジーズドルフ騎竜術", ["ジーズドルフ"], True),
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

# 一般技能
PROSTITUTE_SKILL_NAME: str = "プロスティチュート(娼婦/男娼)"
OFFICIAL_GENERAL_SKILL_NAMES: "list[str]" = [
    "アーマラー(防具職人)",
    "インベンター(発明家)",
    "ウィーバー(織り子)",
    "ウィッチドクター(祈祷師)",
    "ウェイター/ウェイトレス(給仕)",
    "ウェザーマン(天候予報士)",
    "ウェポンスミス(武器職人)",
    "ウッドクラフトマン(木工職人)",
    "エンジニア(機関士)",
    "オーサー(作家)",
    "オフィシャル(役人)",
    "ガーデナー(庭師)",
    "カーペンター(大工)",
    "カラーマン(絵具師)",
    "キースミス(鍵屋)",
    "クレリック(聖職者)",
    "グレイブキーパー(墓守)",
    "コーチマン(御者)",
    "コーティザン(高級娼婦/男娼)",
    "コック(料理人)",
    "コンポーザー(作曲家)",
    "サージョン(外科医)",
    "シグナルマン(信号士)",
    "シューメイカー(靴職人)",
    "ジュエラー(宝飾師)",
    "シンガー(歌手)",
    "スカラー(学生/学者)",
    "スカルプター(彫刻家)",
    "スクライブ(筆写人)",
    "セイラー(水夫/船乗り)",
    "ソルジャー(兵士)",
    "タワーマン(高所作業員)",
    "ダンサー(踊り子)",
    "ツアーガイド(旅先案内人)",
    "ディスティラー((蒸留)酒造家)",
    "テイマー(調教師)",
    "テイラー(仕立て屋)",
    "ドクター(医者)",
    "ドラッグメイカー(薬剤師)",
    "ナース(看護師)",
    "ナビゲーター(航海士)",
    "ノーブル(貴族)",
    "ハーズマン(牧童)",
    "バーバー(髪結い/理髪師)",
    "ハウスキーパー(家政婦(夫))",
    "バトラー(執事)",
    "パヒューマー(調香師)",
    "パフォーマー(芸人)",
    "ハンター(狩人)",
    "ファーマー(農夫)",
    "フィッシャーマン(漁師)",
    "フォーチュンテラー(占い師)",
    "ブラックスミス(鍛冶師)",
    "ブルワー(醸造家)",
    "プレスティディジテイター(手品師)",
    PROSTITUTE_SKILL_NAME,
    "ペインター(絵師)",
    "ベガー(物乞い)",
    "ヘラルディスト(紋章学者)",
    "ボーンカーバー(骨細工師)",
    "マーチャント(商人)",
    "マイナー(鉱夫)",
    "ミートパッカー(精肉業者)",
    "ミッドワイフ(産婆)",
    "ミュージシャン(演奏家)",
    "メーソン(石工)",
    "ライブラリアン(司書)",
    "ランバージャック(木こり)",
    "リペアラー(復元師)",
    "リンギスト(通訳)",
    "レイバー(肉体労働者)",
    "レザーワーカー(皮革職人)",
    "エクスプローラー(探検家)",
    "エンチャンター(付与術師)",
    "オラトール(雄弁家)",
    "カートグラファー(地図屋)",
    "ギャングスタ(ギャング)",
    "ギャンブラー(賭博師)",
    "ストーリーテラー(語り部)",
    "ディテクティヴ(探偵)",
    "マネージャー(元締め)",
    "マナアプレイザー(魔力鑑定士)",
    "フォレストガイド(森林案内人)",
    "アーティストマネージャー(芸能補佐)",
    "チーフタン(族長)",
    "ピアインスペクター(橋脚点検士)",
    "プロスペクター(山師)",
    "マリンアニマルトレーナー(海獣調教師)",
]

# ヴァグランツ戦闘特技
VAGRANTS_COMBAT_SKILLS: "list[str]" = [
    "追い打ち",
    "抵抗強化",
    "カニングキャスト",
    "クイックキャスト",
    "シールドバッシュ",
    "シャドウステップ",
    "捨て身攻撃",
    "露払い",
    "乱撃",
    "クルードテイク",
    "掠め取り",
]
