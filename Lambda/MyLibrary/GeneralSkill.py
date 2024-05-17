# -*- coding: utf-8 -*-

from dataclasses import dataclass

"""
一般技能
"""


@dataclass
class GeneralSkill:
    """
    一般技能
    Attributes:
        Names str: 名前
        Lv int: レベル
    """

    Name: str
    Level: int

    def getFormattedStr(self) -> str:
        """
        整形した一般技能情報を返す

        Returns:
            str: 整形した一般技能情報
        """
        return f"{self.Name} : {self.Level}"
