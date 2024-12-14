from dataclasses import dataclass

# -*- coding: utf-8 -*-


"""
能力値
"""


@dataclass
class Status:
    """
    能力値
    """

    Base: int

    # 装備の増強を除く合計値
    Point: int
    Additional: int
    Equipment: int

    def GetTotalStatus(self) -> int:
        """
        合計能力値を返す

        Returns:
            int: 合計能力値
        """
        return self.Point + self.Additional + self.Equipment
