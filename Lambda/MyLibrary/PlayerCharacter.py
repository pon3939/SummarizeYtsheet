# -*- coding: utf-8 -*-

from dataclasses import dataclass
from json import loads
from re import Match, findall, search, sub
from typing import Union

from MyLibrary.CommonFunction import MakeYtsheetUrl
from MyLibrary.Constant import SwordWorld
from MyLibrary.ExpStatus import ExpStatus
from MyLibrary.GeneralSkill import GeneralSkill
from MyLibrary.Status import Status
from MyLibrary.Style import Style

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


@dataclass
class PlayerCharacter:
    """
    PC
    """

    def __init__(
        self,
        characterJson: dict,
        playerName: str,
        maxExp: int,
        minimumExp: int,
    ):
        """
        コンストラクタ

        characterJson dict: PC情報
        playerName str: 最終更新日時
        maxExp int: 最大経験点
        minimumExp int: 最小経験点
        """
        ytsheetJson: dict = loads(characterJson["ytsheet_json"])

        # 文字列
        self.YtsheetId: str = characterJson["ytsheet_id"]
        self.Race: str = ytsheetJson.get("race", "")
        self.Age: str = ytsheetJson.get("age", "")
        self.Gender: str = ytsheetJson.get("gender", "")
        self.Birth: str = ytsheetJson.get("birth", "")
        self.CombatFeatsLv1: str = ytsheetJson.get("combatFeatsLv1", "")
        self.CombatFeatsLv3: str = ytsheetJson.get("combatFeatsLv3", "")
        self.CombatFeatsLv5: str = ytsheetJson.get("combatFeatsLv5", "")
        self.CombatFeatsLv7: str = ytsheetJson.get("combatFeatsLv7", "")
        self.CombatFeatsLv9: str = ytsheetJson.get("combatFeatsLv9", "")
        self.CombatFeatsLv11: str = ytsheetJson.get("combatFeatsLv11", "")
        self.CombatFeatsLv13: str = ytsheetJson.get("combatFeatsLv13", "")
        self.CombatFeatsLv1bat: str = ytsheetJson.get("combatFeatsLv1bat", "")
        self.AdventurerRank: str = ytsheetJson.get("rank", "")

        # 数値
        self.Level: int = int(ytsheetJson.get("level", "0"))
        self.Exp: int = int(ytsheetJson.get("expTotal", "0"))
        self.GrowthTimes: int = int(ytsheetJson.get("historyGrowTotal", "0"))
        self.TotalHonor: int = int(ytsheetJson.get("historyHonorTotal", "0"))
        self.Hp: int = int(ytsheetJson.get("hpTotal", "0"))
        self.Mp: int = int(ytsheetJson.get("mpTotal", "0"))
        self.LifeResistance: int = int(ytsheetJson.get("vitResistTotal", "0"))
        self.SpiritResistance: int = int(
            ytsheetJson.get("mndResistTotal", "0")
        )
        self.MonsterKnowledge: int = int(ytsheetJson.get("monsterLore", "0"))
        self.Initiative: int = int(ytsheetJson.get("initiative", "0"))
        self.HistoryMoneyTotal: int = int(
            ytsheetJson.get("historyMoneyTotal", "0")
        )

        # 特殊な変数
        self.Sin: str = ytsheetJson.get("sin", "0")

        # PC名
        # フリガナを削除
        self.Name: str = sub(
            r"\|([^《]*)《[^》]*》",
            r"\1",
            ytsheetJson.get("characterName", ""),
        )
        if self.Name == "":
            # PC名が空の場合は二つ名を表示
            self.Name = ytsheetJson.get("aka", "")

        # 経験点の状態
        self.ActiveStatus: ExpStatus = ExpStatus.INACTIVE
        if self.Exp >= maxExp:
            self.ActiveStatus = ExpStatus.MAX
        elif self.Exp >= minimumExp:
            self.ActiveStatus = ExpStatus.ACTIVE

        # 信仰
        self.Faith: str = ytsheetJson.get("faith", "なし")
        if self.Faith == "その他の信仰":
            self.Faith = ytsheetJson.get("faithOther", self.Faith)

        # 自動取得
        self.AutoCombatFeats: list[str] = ytsheetJson.get(
            "combatFeatsAuto", ""
        ).split(",")

        # 技能レベル
        self.Skills: dict[str, int] = {}
        for skill in SwordWorld.SKILLS:
            skillLevel: int = int(ytsheetJson.get(skill, "0"))
            if skillLevel > 0:
                self.Skills[skill] = skillLevel

        # 各能力値
        self.Dexterity: Status = Status(
            int(ytsheetJson.get("sttBaseA", "0")),
            int(ytsheetJson.get("sttDex", "0")),
            int(ytsheetJson.get("sttAddA", "0")),
            int(ytsheetJson.get("sttEquipA", "0")),
        )
        self.Agility: Status = Status(
            int(ytsheetJson.get("sttBaseB", "0")),
            int(ytsheetJson.get("sttAgi", "0")),
            int(ytsheetJson.get("sttAddB", "0")),
            int(ytsheetJson.get("sttEquipB", "0")),
        )
        self.Strength: Status = Status(
            int(ytsheetJson.get("sttBaseC", "0")),
            int(ytsheetJson.get("sttStr", "0")),
            int(ytsheetJson.get("sttAddC", "0")),
            int(ytsheetJson.get("sttEquipC", "0")),
        )
        self.Vitality: Status = Status(
            int(ytsheetJson.get("sttBaseD", "0")),
            int(ytsheetJson.get("sttVit", "0")),
            int(ytsheetJson.get("sttAddD", "0")),
            int(ytsheetJson.get("sttEquipD", "0")),
        )
        self.Intelligence: Status = Status(
            int(ytsheetJson.get("sttBaseE", "0")),
            int(ytsheetJson.get("sttInt", "0")),
            int(ytsheetJson.get("sttAddE", "0")),
            int(ytsheetJson.get("sttEquipE", "0")),
        )
        self.Mental: Status = Status(
            int(ytsheetJson.get("sttBaseF", "0")),
            int(ytsheetJson.get("sttMnd", "0")),
            int(ytsheetJson.get("sttAddF", "0")),
            int(ytsheetJson.get("sttEquipF", "0")),
        )

        # 秘伝
        self.Styles: list[Style] = []
        mysticArtsNum: int = int(ytsheetJson.get("mysticArtsNum", "0"))
        for i in range(1, mysticArtsNum + 1):
            style: Union[Style, None] = _FindStyle(
                ytsheetJson.get(f"mysticArts{i}", "")
            )
            if style is not None and style not in self.Styles:
                self.Styles.append(style)

        # 秘伝魔法
        mysticMagicNum: int = int(ytsheetJson.get("mysticMagicNum", "0"))
        for i in range(1, mysticMagicNum + 1):
            style: Union[Style, None] = _FindStyle(
                ytsheetJson.get(f"mysticMagic{i}", "")
            )
            if style is not None and style not in self.Styles:
                self.Styles.append(style)

        # 名誉アイテム
        honorItemsNum: int = int(ytsheetJson.get("honorItemsNum", "0"))
        for i in range(1, honorItemsNum + 1):
            style: Union[Style, None] = _FindStyle(
                ytsheetJson.get(f"honorItem{i}", "")
            )
            if style is not None and style not in self.Styles:
                self.Styles.append(style)

        # 不名誉詳細
        disHonorItemsNum: int = int(ytsheetJson.get("dishonorItemsNum", "0"))
        for i in range(1, disHonorItemsNum + 1):
            style: Union[Style, None] = _FindStyle(
                ytsheetJson.get(f"dishonorItem{i}", "")
            )
            if style is not None and style not in self.Styles:
                self.Styles.append(style)

        # 武器
        self.AbyssCurses: list[str] = []
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

        # 重複を削除
        self.AbyssCurses = list(set(self.AbyssCurses))

        # 一般技能
        self.GeneralSkills: list[GeneralSkill] = []
        for i in range(1, int(ytsheetJson.get("commonClassNum", "0")) + 1):
            generalSkillName: str = ytsheetJson.get(f"commonClass{i}", "")
            generalSkillName = generalSkillName.removeprefix("|")
            if generalSkillName == "":
                continue

            # カッコの中と外で分離
            ytsheetGeneralSkills: list[str] = findall(
                r"[^(（《/]+",
                generalSkillName.removesuffix(")")
                .removesuffix("）")
                .removesuffix("》"),
            )
            for ytsheetGeneralSkill in ytsheetGeneralSkills:
                if ytsheetGeneralSkill in SwordWorld.PROSTITUTE_SKILL_NAME:
                    # 男娼と高級男娼を誤検知するので個別対応
                    generalSkillName = SwordWorld.PROSTITUTE_SKILL_NAME
                    break

                officialGeneralSkill: Union[str, None] = next(
                    filter(
                        lambda x: ytsheetGeneralSkill in x,
                        SwordWorld.OFFICIAL_GENERAL_SKILL_NAMES,
                    ),
                    None,
                )
                if officialGeneralSkill is not None:
                    # 公式一般技能は定数から正式名称を取得
                    generalSkillName = officialGeneralSkill
                    break

            self.GeneralSkills.append(
                GeneralSkill(
                    generalSkillName,
                    int(ytsheetJson.get(f"lvCommon{i}", "0")),
                )
            )

        # セッション履歴を集計
        self.GameMasterScenarioKeys: list[str] = []
        self.PlayerTimes: int = 0
        self.DiedTimes: int = 0
        historyNum: int = int(ytsheetJson.get("historyNum", "0"))
        for i in range(1, historyNum + 1):
            gameMaster: str = ytsheetJson.get(f"history{i}Gm", "")
            if gameMaster == "":
                continue

            # 参加、GM回数を集計
            if (
                gameMaster == playerName
                or gameMaster in _SELF_GAME_MASTER_NAMES
            ):
                # 複数PC所持PLのGM回数集計のため、シナリオごとに一意のキーを作成
                date: str = ytsheetJson.get(f"history{i}Date", "")
                count: int = len(
                    [
                        x
                        for x in self.GameMasterScenarioKeys
                        if x.startswith(date)
                    ]
                )

                # 重複を避けるため、同一日の場合は連番を付与
                self.GameMasterScenarioKeys.append(f"{date}_{count}")
            else:
                self.PlayerTimes += 1

            # 備考
            if search(_DIED_REGEXP, ytsheetJson.get(f"history{i}Note", "")):
                # 死亡回数を集計
                self.DiedTimes += 1

        # 経歴を1行ごとに分割
        freeNotes: list[str] = ytsheetJson.get("freeNote", "").split(
            "&lt;br&gt;"
        )

        self.Height: str = ""
        self.Weight: str = ""
        for freeNote in freeNotes:
            if "身長" in freeNote:
                height: str = sub(
                    r".*身長[^\d\.\|]*\|*[^\d\.\|]*([\d\.]+).*",
                    r"\1",
                    freeNote,
                )
                if height != freeNote:
                    self.Height = height

            if "背丈" in freeNote:
                height: str = sub(
                    r".*背丈[^\d\.\|]*\|*[^\d\.\|]*([\d\.]+).*",
                    r"\1",
                    freeNote,
                )
                if height != freeNote:
                    self.Height = height

            if "体重" in freeNote:
                weight: str = sub(
                    r".*体重[^\d\.\|]*\|*[^\d\.\|]*([\d\.]+).*",
                    r"\1",
                    freeNote,
                )
                if weight != freeNote:
                    self.Weight = weight

    def GetMinorRace(self) -> str:
        """

        マイナー種族を返却する

        Returns:
            str: マイナー種族
        """

        if "ナイトメア" in self.Race or "ウィークリング" in self.Race:
            # 特定種族はかっこをつけたまま返却
            return self.Race

        minorRaceMatch: Union[Match[str], None] = search(
            r"(?<=（)(.+)(?=）)", self.Race
        )
        if minorRaceMatch is None:
            # カッコなしなのでそのまま返却
            return self.Race

        # カッコの中身を返却
        return minorRaceMatch.group()

    def GetMajorRace(self) -> str:
        """

        メジャー種族を返却する

        Returns:
            str: メジャー種族
        """

        return sub(r"（.+）", "", self.Race)

    def IsVagrants(self) -> bool:
        """

        ヴァグランツかどうか

        Returns:
            bool: True ヴァグランツ
        """

        if self.Skills.get(SwordWorld.BATTLE_DANCER_LEVEL_KEY, 0) > 0 and any(
            list(
                map(
                    lambda x: self.CombatFeatsLv1bat.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv1.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 3:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv3.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 5:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv5.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 7:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv7.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 9:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv9.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 11:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv11.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        if self.Level < 13:
            return False

        if any(
            list(
                map(
                    lambda x: self.CombatFeatsLv13.startswith(x),
                    SwordWorld.VAGRANTS_COMBAT_SKILLS,
                )
            )
        ):
            return True

        return False

    def GetYtsheetUrl(self) -> str:
        """

        ゆとシートのURLを作成

        Args:
            id str: ゆとシートのID
        Returns:
            str: URL
        """
        return MakeYtsheetUrl(self.YtsheetId)

    def GetSkillLevel(self, key: str) -> int:
        """

        冒険者技能のレベルを返却

        Args:
            key str: 冒険者技能のキー
        Returns:
            int: 技能レベル
        """
        return self.Skills.get(key, 0)


def _FindStyle(string: str) -> Union[Style, None]:
    """

    引数が流派を表す文字列か調べ、一致する流派を返却する

    Args:
        string str: 確認する文字列

    Returns:
        Union[Style, None]: 存在する場合は流派、それ以外はNone
    """

    for style in SwordWorld.STYLES:
        if search(style.GetKeywordsRegexp(), string):
            return style

    return None


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
