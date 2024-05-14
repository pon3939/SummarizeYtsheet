# -*- coding: utf-8 -*-


"""
流派
"""


class Style:
    """
    流派
    Attributes:
        Name str: 流派名
        Keywords list[str]: 検索キーワード
        Is2.0 bool: 2.0流派か
    """

    def __init__(
        self, name: str, keywords: list[str], is20: bool = False
    ) -> None:
        """

        コンストラクタ

        Args:
            Name str: 流派名
            Keywords list[str]: 検索キーワード
            Is2.0 bool: 2.0流派か
        """
        self.Name: str = name
        self.Keywords: list[str] = keywords
        self.Is20: bool = is20

    def GetKeywordsRegexp(self) -> str:
        """
        流派を検索する正規表現を返す

        Returns:
            str: 流派を検索する正規表現
        """
        return "|".join(self.Keywords)
