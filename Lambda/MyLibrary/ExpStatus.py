# -*- coding: utf-8 -*-

from enum import IntEnum, auto

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
