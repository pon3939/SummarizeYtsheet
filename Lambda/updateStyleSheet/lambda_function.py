# -*- coding: utf-8 -*-

from gspread import Spreadsheet, Worksheet, utils
from myLibrary import commonConstant, commonFunction, expStatus

"""
流派シートを更新
"""


# 流派加入時に表示する文字列
TRUE_STRING: str = "○"


def lambda_handler(event: dict, context):
    """

    メイン処理

    Args:
        event dict: イベント
        context awslambdaric.lambda_context.LambdaContext: コンテキスト
    """

    # 入力
    environment: dict = event["Environment"]
    spreadsheetId: str = environment["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: "list[dict]" = event["Players"]

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = commonFunction.OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("流派")

    # 更新
    UpdateSheet(worksheet, players)


def UpdateSheet(worksheet: Worksheet, players: "list[dict]"):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[dict]: プレイヤー情報
    """

    updateData: list[list] = []

    # ヘッダー
    headers: "list[str]" = [
        "No.",
        "PC",
        "参加傾向",
        "2.0流派",
        "未加入",
        "加入数",
    ]
    for style in commonConstant.STYLES:
        headers.append(style["name"])

    # ヘッダーを縦書き用に変換
    displayHeaders: list[str] = list(
        map(
            lambda x: commonFunction.ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.append(displayHeaders)

    notTotalColumnCount: int = 3
    totalColumnCount: int = len(headers) - notTotalColumnCount
    total: list = ([None] * notTotalColumnCount) + ([0] * totalColumnCount)
    formats: "list[dict]" = []
    for player in players:
        row: list = []

        # 流派の情報を取得
        is20: bool = False
        learnedStyles: list[str] = []
        for style in commonConstant.STYLES:
            learnedStyle: str = ""
            if style["name"] in player["styles"]:
                # 該当する流派に入門している
                learnedStyle = TRUE_STRING
                total[headers.index(style["name"])] += 1
                if style["is20"]:
                    is20 = True

            learnedStyles.append(learnedStyle)

        # No.
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 参加傾向
        row.append(
            commonConstant.ENTRY_TREND_DEACTIVE
            if player["expStatus"] == expStatus.ExpStatus.DEACTIVE
            else commonConstant.ENTRY_TREND_ACTIVE
        )

        # 2.0流派
        is20String: str = ""
        if is20:
            is20String: str = TRUE_STRING
            total[headers.index("2.0流派")] += 1

        row.append(is20String)

        # 未加入
        notLearned: str = ""
        learningCount: int = learnedStyles.count(TRUE_STRING)
        if learningCount == 0:
            notLearned: str = TRUE_STRING
            total[headers.index("未加入")] += 1
        row.append(notLearned)

        # 加入数
        total[headers.index("加入数")] += learningCount
        row.append(learningCount)

        # 各流派
        row.extend(learnedStyles)

        updateData.append(row)

        # PC列のハイパーリンク
        pcIndex: int = headers.index("PC") + 1
        rowIndex: int = updateData.index(row) + 1
        pcTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

    # 合計行
    total[notTotalColumnCount - 1] = "合計"
    updateData.append(total)

    # クリア
    worksheet.clear()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(headers))
    worksheet.format(
        f"{startA1}:{endA1}",
        commonConstant.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": commonConstant.HEADER_DEFAULT_FORMAT,
        }
    )

    # 流派のヘッダー
    startA1: str = utils.rowcol_to_a1(1, notTotalColumnCount + 1)
    endA1: str = utils.rowcol_to_a1(1, len(headers))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": {"textRotation": {"vertical": True}},
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(headers)  # type: ignore
    )
