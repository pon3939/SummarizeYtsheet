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
    "textFormat": DEFAULT_TEXT_FORMAT,
}

# ヘッダーに適用する書式
HEADER_DEFAULT_FORMAT: dict = {
    "horizontalAlignment": "CENTER",
    "textRotation": {"vertical": False},
}

# Trueのときに表示する文字列
TRUE_STRING: str = "○"

# アクティブのときに表示する文字列
ACTIVE_STRING: str = "アクティブ"
