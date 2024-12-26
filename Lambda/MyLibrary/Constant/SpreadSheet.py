# -*- coding: utf-8 -*-

"""
スプレッドシート関係の定数
"""

# スプレッドシート全体に適用するテキストの書式
DEFAULT_TEXT_FORMAT: dict = {
    "fontFamily": "Meiryo",
}

# スプレッドシート全体に適用する書式
DEFAULT_FORMAT: dict = {
    "verticalAlignment": "MIDDLE",
    "textFormat": DEFAULT_TEXT_FORMAT,
}

# ヘッダーに適用する書式
DEFAULT_HEADER_FORMAT: dict = {
    "horizontalAlignment": "CENTER",
    "verticalAlignment": "BOTTOM",
    "textRotation": {"vertical": False},
}

# Trueのときに表示する文字列
TRUE_STRING: str = "○"
