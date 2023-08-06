# -*- coding: utf-8 -*-

from enum import Enum, auto

"""
経験点の状態を管理する列挙型
"""


class ExpStatus(Enum):
    """経験点の状態を管理する列挙型
    Attributes:
        ACTIVE: 下限以上、上限未満
        DEACTIVE: 下限未満
        MAX: 上限
    """

    ACTIVE = auto()
    DEACTIVE = auto()
    MAX = auto()
