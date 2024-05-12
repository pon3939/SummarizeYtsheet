# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from itertools import chain
from json import loads
from re import Match, search, sub
from typing import Union
from unicodedata import normalize

from myLibrary.Constant import SwordWorld
from myLibrary.ExpStatus import ExpStatus
from myLibrary.Status import Status

"""
PC
"""

# 自分が開催したときのGM名
_SELF_GAME_MASTER_NAMES: "list[str]" = [
    "俺",
    "私",
    "自分",
]

# 死亡時の備考
_DIED_REGEXP: str = "死亡"

# ピンゾロの表記ゆれ対応
_FUMBLE_TITLES: "list[str]" = [
    "ファンブル",
    "50点",
    "ゾロ",
]

# 備考欄のピンゾロ回数表記ゆれ対応
_FUMBLE_COUNT_PREFIXES: "list[str]" = list(
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
                ],
            ),
            _FUMBLE_TITLES,
        )
    )
)


def _NormalizeString(string: str) -> str:
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


# ピンゾロの合計行の正規表現
_TotalFumbleRegexp: str = "|".join(list(map(_NormalizeString, _FUMBLE_TITLES)))

# ピンゾロの明細行の正規表現
_FumbleCountRegexps: "list[str]" = list(
    map(
        lambda x: rf"(?<={x})\d+",
        map(_NormalizeString, _FUMBLE_COUNT_PREFIXES),
    )
)


@dataclass
class PlayerCharacter:
    """
    PC
    """

    # DBから取得したJSON
    Json: dict

    PlayerName: str

    MaxExp: int
    MinimumExp: int

    YtsheetId: str = ""
    Race: str = ""
    Age: str = ""
    Gender: str = ""
    Birth: str = ""
    CombatFeatsLv1: str = ""
    CombatFeatsLv3: str = ""
    CombatFeatsLv5: str = ""
    CombatFeatsLv7: str = ""
    CombatFeatsLv9: str = ""
    CombatFeatsLv11: str = ""
    CombatFeatsLv13: str = ""
    CombatFeatsLv15: str = ""
    CombatFeatsLv1bat: str = ""
    AdventurerRank: str = ""
    Sin: str = ""
    Name: str = ""
    Faith: str = ""

    Level: int = 0
    Exp: int = 0
    GrowthTimes: int = 0
    TotalHonor: int = 0
    Hp: int = 0
    Mp: int = 0
    LifeResistance: int = 0
    SpiritResistance: int = 0
    MonsterKnowledge: int = 0
    Initiative: int = 0
    Technic: int = 0
    Physical: int = 0
    Spirit: int = 0
    GameMasterTimes: int = 0
    PlayerTimes: int = 0
    DiedTimes: int = 0
    FumbleExp: int = 0

    AutoCombatFeats: list[str] = field(default_factory=list)
    Styles: list[str] = field(default_factory=list)
    AbyssCurses: list[str] = field(default_factory=list)

    Skills: dict = field(default_factory=dict)

    ActiveStatus: ExpStatus = ExpStatus.ACTIVE

    Dexterity: Status = Status()
    Agility: Status = Status()
    Strength: Status = Status()
    Vitality: Status = Status()
    Intelligence: Status = Status()
    Mental: Status = Status()

    def __post_init__(self) -> None:
        """
        コンストラクタの後の処理
        """
        if self.Json == {}:
            # JSONからデコードされた場合など
            return

        ytsheetJson: dict = loads(self.Json["ytsheet_json"])

        # 文字列
        self.YtsheetId = self.Json["ytsheet_id"]
        self.Race = ytsheetJson.get("race", "")
        self.Age = ytsheetJson.get("age", "")
        self.Gender = ytsheetJson.get("gender", "")
        self.Birth = ytsheetJson.get("birth", "")
        self.CombatFeatsLv1 = ytsheetJson.get("combatFeatsLv1", "")
        self.CombatFeatsLv3 = ytsheetJson.get("combatFeatsLv3", "")
        self.CombatFeatsLv5 = ytsheetJson.get("combatFeatsLv5", "")
        self.CombatFeatsLv7 = ytsheetJson.get("combatFeatsLv7", "")
        self.CombatFeatsLv9 = ytsheetJson.get("combatFeatsLv9", "")
        self.CombatFeatsLv11 = ytsheetJson.get("combatFeatsLv11", "")
        self.CombatFeatsLv13 = ytsheetJson.get("combatFeatsLv13", "")
        self.CombatFeatsLv15 = ytsheetJson.get("combatFeatsLv15", "")
        self.CombatFeatsLv1bat = ytsheetJson.get("combatFeatsLv1bat", "")
        self.AdventurerRank = ytsheetJson.get("rank", "")

        # 数値
        self.Level = int(ytsheetJson.get("level", "0"))
        self.Exp = int(ytsheetJson.get("expTotal", "0"))
        self.GrowthTimes = int(ytsheetJson.get("historyGrowTotal", "0"))
        self.TotalHonor = int(ytsheetJson.get("historyHonorTotal", "0"))
        self.Hp = int(ytsheetJson.get("hpTotal", "0"))
        self.Mp = int(ytsheetJson.get("mpTotal", "0"))
        self.LifeResistance = int(ytsheetJson.get("vitResistTotal", "0"))
        self.SpiritResistance = int(ytsheetJson.get("mndResistTotal", "0"))
        self.MonsterKnowledge = int(ytsheetJson.get("monsterLore", "0"))
        self.Initiative = int(ytsheetJson.get("initiative", "0"))

        # 特殊な変数
        self.Sin = ytsheetJson.get("sin", "0")

        # PC名
        # フリガナを削除
        self.Name = sub(
            r"\|([^《]*)《[^》]*》",
            r"\1",
            ytsheetJson.get("characterName", ""),
        )
        if self.Name == "":
            # PC名が空の場合は二つ名を表示
            self.Name = ytsheetJson.get("aka", "")

        # 経験点の状態
        if self.Exp >= self.MaxExp:
            self.ActiveStatus = ExpStatus.MAX
        elif self.Exp < self.MinimumExp:
            self.ActiveStatus = ExpStatus.INACTIVE

        # 信仰
        self.Faith = ytsheetJson.get("faith", "なし")
        if self.Faith == "その他の信仰":
            self.Faith = ytsheetJson.get("faithOther", self.Faith)

        # 自動取得
        self.AutoCombatFeats = ytsheetJson.get("combatFeatsAuto", "").split(
            ","
        )

        # 技能レベル
        for skill in SwordWorld.SKILLS:
            skillLevel: int = int(ytsheetJson.get(skill, "0"))
            if skillLevel > 0:
                self.Skills[skill] = skillLevel

        # 各能力値
        self.Technic = int(ytsheetJson.get("sttBaseTec", "0"))
        self.Physical = int(ytsheetJson.get("sttBasePhy", "0"))
        self.Spirit = int(ytsheetJson.get("sttBaseSpi", "0"))

        self.Dexterity = Status(
            int(ytsheetJson.get("sttBaseA", "0")),
            int(ytsheetJson.get("sttGrowA", "0")),
            int(ytsheetJson.get("sttAddA", "0")),
        )
        self.Agility = Status(
            int(ytsheetJson.get("sttBaseB", "0")),
            int(ytsheetJson.get("sttGrowB", "0")),
            int(ytsheetJson.get("sttAddB", "0")),
        )
        self.Strength = Status(
            int(ytsheetJson.get("sttBaseC", "0")),
            int(ytsheetJson.get("sttGrowC", "0")),
            int(ytsheetJson.get("sttAddC", "0")),
        )
        self.Vitality = Status(
            int(ytsheetJson.get("sttBaseD", "0")),
            int(ytsheetJson.get("sttGrowD", "0")),
            int(ytsheetJson.get("sttAddD", "0")),
        )
        self.Intelligence = Status(
            int(ytsheetJson.get("sttBaseE", "0")),
            int(ytsheetJson.get("sttGrowE", "0")),
            int(ytsheetJson.get("sttAddE", "0")),
        )
        self.Mental = Status(
            int(ytsheetJson.get("sttBaseF", "0")),
            int(ytsheetJson.get("sttGrowF", "0")),
            int(ytsheetJson.get("sttAddF", "0")),
        )

        # 秘伝
        mysticArtsNum: int = int(ytsheetJson.get("mysticArtsNum", "0"))
        for i in range(1, mysticArtsNum + 1):
            style: str = _FindStyleFormalName(
                ytsheetJson.get(f"mysticArts{i}", "")
            )
            if style != "" and style not in self.Styles:
                self.Styles.append(style)

        # 名誉アイテム
        honorItemsNum: int = int(ytsheetJson.get("honorItemsNum", "0"))
        for i in range(1, honorItemsNum + 1):
            style: str = _FindStyleFormalName(
                ytsheetJson.get(f"honorItem{i}", "")
            )
            if style != "" and style not in self.Styles:
                self.Styles.append(style)

        # 不名誉詳細
        disHonorItemsNum: int = int(ytsheetJson.get("dishonorItemsNum", "0"))
        for i in range(1, disHonorItemsNum + 1):
            style: str = _FindStyleFormalName(
                ytsheetJson.get(f"dishonorItem{i}", "")
            )
            if style != "" and style not in self.Styles:
                self.Styles.append(style)

        # 武器
        weaponNum: int = int(ytsheetJson.get("weaponNum", "0"))
        for i in range(1, weaponNum + 1):
            self.AbyssCurses += _FindAbyssCurses(
                ytsheetJson.get(f"weapon{i}Name", "")
            )
            self.AbyssCurses += _FindAbyssCurses(
                ytsheetJson.get(f"weapon{i}Note", "")
            )

        # 鎧
        armourNum: int = int(ytsheetJson.get("armourNum", "0"))
        for i in range(1, armourNum + 1):
            self.AbyssCurses += _FindAbyssCurses(
                ytsheetJson.get(f"armour{i}Name", "")
            )
            self.AbyssCurses += _FindAbyssCurses(
                ytsheetJson.get(f"armour{i}Note", "")
            )

        # 所持品
        self.AbyssCurses += _FindAbyssCurses(ytsheetJson.get("items", ""))

        # セッション履歴を集計
        totalFumbleExp: int = 0
        fumbleCount: int = 0
        historyNum: int = int(ytsheetJson.get("historyNum", "0"))
        for i in range(1, historyNum + 1):
            gameMaster: str = ytsheetJson.get(f"history{i}Gm", "")
            if gameMaster == "":
                # GM名未記載の履歴からピンゾロのみのセッション履歴を探す
                normalizedTitle: str = _NormalizeString(
                    ytsheetJson.get(f"history{i}Title", "")
                )
                normalizedDate: str = _NormalizeString(
                    ytsheetJson.get(f"history{i}Date", "")
                )
                normalizedMember: str = _NormalizeString(
                    ytsheetJson.get(f"history{i}Member", "")
                )
                if (
                    search(_TotalFumbleRegexp, normalizedTitle)
                    or search(_TotalFumbleRegexp, normalizedDate)
                    or search(_TotalFumbleRegexp, normalizedMember)
                ):
                    totalFumbleExp += _CalculateFromString(
                        ytsheetJson.get(f"history{i}Exp", "0")
                    )
            else:
                # 参加、GM回数を集計
                if (
                    gameMaster == self.PlayerName
                    or gameMaster in _SELF_GAME_MASTER_NAMES
                ):
                    self.GameMasterTimes += 1
                else:
                    self.PlayerTimes += 1

                # 備考
                note: str = ytsheetJson.get(f"history{i}Note", "")
                if search(_DIED_REGEXP, note):
                    # 死亡回数を集計
                    self.DiedTimes += 1

                # ピンゾロ回数を集計
                normalizedNote: str = _NormalizeString(note)
                for fumbleCountRegexp in _FumbleCountRegexps:
                    fumbleCountMatch: Union[Match[str], None] = search(
                        fumbleCountRegexp, normalizedNote
                    )
                    if fumbleCountMatch is not None:
                        fumbleCount += int(fumbleCountMatch.group(0))
                        break

            # ピンゾロ経験点は最大値を採用する(複数の書き方で書かれていた場合、重複して集計してしまうため)
            self.FumbleExp = max(totalFumbleExp, fumbleCount * 50)

        # 不要なので削除
        self.PlayerName = ""
        self.MaxExp = 0
        self.MinimumExp = 0
        self.YtSheetJson = {}


def _CalculateFromString(string: str) -> int:
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


def _FindStyleFormalName(string: str) -> str:
    """

    引数が流派を表す文字列か調べ、流派の正式名称を返却する

    Args:
        string str: 確認する文字列

    Returns:
        str: 引数が流派を表す文字列の場合は流派名、それ以外は空文字
    """

    for style in SwordWorld.STYLES:
        if search(style.getKeywordsRegexp(), string):
            return style.Name

    return ""


def _FindAbyssCurses(string: str) -> "list[str]":
    """

    引数に含まれるアビスカースを返却する

    Args:
        string str: 確認する文字列

    Returns:
        list[str]: 引数に含まれるアビスカース
    """

    result: list[str] = []
    for abyssCurse in SwordWorld.ABYSS_CURSES:
        if abyssCurse in string:
            result.append(abyssCurse)

    return result
