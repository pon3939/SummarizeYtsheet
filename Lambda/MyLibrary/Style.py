# -*- coding: utf-8 -*-

from dataclasses import dataclass

"""
流派
"""


@dataclass
class Style:
    """
    流派
    Attributes:
        Name str: 流派名
        Keywords list[str]: 検索キーワード
        Is20 bool: 2.0流派か
    """

    Name: str
    Keywords: list[str]
    Is20: bool = False

    def GetKeywordsRegexp(self) -> str:
        """
        流派を検索する正規表現を返す

        Returns:
            str: 流派を検索する正規表現
        """
        return "|".join(self.Keywords)
