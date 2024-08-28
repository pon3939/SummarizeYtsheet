# -*- coding: utf-8 -*-


from dataclasses import dataclass, field

from MyLibrary.CommonFunction import StrForDynamoDBToDateTime
from MyLibrary.PlayerCharacter import PlayerCharacter

"""
PL
"""


@dataclass
class Player:
    """
    PL
    """

    Name: str
    UpdateTime: str
    MaxExp: int
    MinimumExp: int

    # DBから取得したJSON
    CharacterJsons: list[dict]

    GameMasterTimes: int = 0

    Characters: list[PlayerCharacter] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        コンストラクタの後の処理
        """
        if len(self.CharacterJsons) == 0:
            # JSONからデコードされた場合
            self.Characters = list(
                map(
                    lambda x: (
                        PlayerCharacter(**x) if isinstance(x, dict) else x
                    ),
                    self.Characters,
                )
            )
        else:
            # 更新日時をスプレッドシートが理解できる形式に変換
            self.UpdateTime = StrForDynamoDBToDateTime(
                self.UpdateTime
            ).strftime("%Y/%m/%d %H:%M:%S")

            characters: list[PlayerCharacter] = list(
                map(
                    lambda x: PlayerCharacter(
                        Json=x,
                        PlayerName=self.Name,
                        MaxExp=self.MaxExp,
                        MinimumExp=self.MinimumExp,
                    ),
                    self.CharacterJsons,
                )
            )

            gameMasterScenarioKeys: list[str] = []
            for character in characters:
                gameMasterScenarioKeys.extend(character.GameMasterScenarioKeys)

                # 不要なので削除
                character.GameMasterScenarioKeys = []

            # 同一シナリオの重複を排除してGM回数を集計
            self.GameMasterTimes = len(set(gameMasterScenarioKeys))
            self.Characters = characters

            # 不要なので削除
            self.MaxExp = 0
            self.MinimumExp = 0
            self.CharacterJsons = []
