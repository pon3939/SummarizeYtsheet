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

    Base: int = 0
    Increased: int = 0
    Additional: int = 0

    def GetTotalStatus(self) -> int:
        """
        合計能力値を返す

        Returns:
            int: 合計能力値
        """
        return self.Base + self.Increased + self.Additional
