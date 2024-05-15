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

            self.Characters = list(
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

            # 不要なので削除
            self.MaxExp = 0
            self.MinimumExp = 0
            self.CharacterJsons = []
