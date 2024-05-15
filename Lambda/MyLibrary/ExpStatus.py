# -*- coding: utf-8 -*-

from enum import IntEnum, auto

from MyLibrary.Constant import SpreadSheet

"""
経験点の状態を管理する列挙型
"""


class ExpStatus(IntEnum):
    """経験点の状態を管理する列挙型
    Attributes:
        INACTIVE: 下限未満
        ACTIVE: 下限以上、上限未満
        MAX: 上限
    """

    INACTIVE = auto()
    ACTIVE = auto()
    MAX = auto()

    def GetStrForSpreadsheet(self) -> str:
        """

            スプレッドシート表示用文字列を返す

        Returns:
            str: 表示用文字列
        """
        if self >= ExpStatus.ACTIVE:
            return SpreadSheet.ACTIVE_STRING

        return ""
