# -*- coding: utf-8 -*-

from gspread import Worksheet, utils
from myLibrary import commonConstant, commonFunction

"""
基本シートを更新
"""


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId: str = event["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: "list[dict]" = event["Players"]

    # スプレッドシートを開く
    worksheet: Worksheet = commonFunction.openSpreadsheet(
        googleServiceAccount, spreadsheetId, "基本"
    )

    # 更新
    updateSheet(worksheet, players)


def updateSheet(worksheet: Worksheet, players: "list[dict]"):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[dict]: プレイヤー情報
    """

    updateData: list[list] = []

    # ヘッダー
    header: "list[str]" = [
        "No.",
        "PC",
        "PL",
        "種族",
        "年齢",
        "性別",
        "信仰",
        "穢れ",
        "参加",
        "GM",
        "死亡",
        "更新日時",
    ]
    updateData.append(header)

    totalDiedTimes: int = 0
    formats: "list[dict]" = []
    for player in players:
        row: list = []

        # No.
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # PL
        row.append(player["name"])

        # 種族
        row.append(player["race"])

        # 年齢
        row.append(player["age"])

        # 性別
        row.append(player["gender"])

        # 信仰
        row.append(player["faith"])

        # 穢れ
        row.append(player["sin"])

        # 参加
        row.append(player["playerTimes"])

        # GM
        row.append(player["gameMasterTimes"])

        # 死亡
        row.append(player["diedTimes"])

        # 更新日時
        row.append(player["updateTime"])

        updateData.append(row)

        # PC列のハイパーリンク
        pcIndex: int = header.index("PC") + 1
        rowIndex: int = updateData.index(row) + 1
        pcTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

        # 合計行を集計
        totalDiedTimes += player["diedTimes"]

    # 合計行
    total: list = [None] * len(header)
    diedIndex: int = header.index("死亡")
    total[diedIndex - 1] = "合計"
    total[diedIndex] = totalDiedTimes
    updateData.append(total)

    # クリア
    worksheet.clear()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        commonConstant.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": commonConstant.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(1, 1, len(updateData) - 1, len(header))
