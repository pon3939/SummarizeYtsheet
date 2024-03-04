# -*- coding: utf-8 -*-

from enum import IntEnum, auto

"""
経験点の状態を管理する列挙型
"""


class ExpStatus(IntEnum):
    """経験点の状態を管理する列挙型
    Attributes:
        ACTIVE: 下限以上、上限未満
        INACTIVE: 下限未満
        MAX: 上限
    """

    ACTIVE = auto()
    INACTIVE = auto()
    MAX = auto()
