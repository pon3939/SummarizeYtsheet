# -*- coding: utf-8 -*-


from gspread import Worksheet, utils
from myLibrary import commonConstant, commonFunction

"""
技能シートを更新
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
    players: list[dict] = event["Players"]
    levelCap: dict = event["LevelCap"]
    maxExp: int = int(levelCap["MaxExp"])
    minimumExp: int = int(levelCap["MinimumExp"])

    # スプレッドシートを開く
    worksheet: Worksheet = commonFunction.OpenSpreadsheet(
        googleServiceAccount, spreadsheetId, "技能"
    )

    # 更新
    UpdateSheet(worksheet, players, maxExp, minimumExp)


def UpdateSheet(
    worksheet: Worksheet, players: "list[dict]", maxExp: int, minimumExp: int
):
    """

    シートを更新

    Args:
        worksheet Worksheet: シート
        players list[dict]: プレイヤー情報
        maxExp int: 経験点の上限
        minimumExp int: 経験点の下限
    """

    updateData: list[list] = []

    # ヘッダー
    headers: list[str] = [
        "No.",
        "PC",
        "信仰",
        "Lv",
        "経験点\nピンゾロ含む",
        "ピンゾロ",
    ]
    for skill in commonConstant.SKILLS:
        headers.append(skill["name"])

    # ヘッダーを縦書き用に変換
    displayHeader: list[str] = list(
        map(
            lambda x: commonFunction.ConvertToVerticalHeader(x),
            headers,
        )
    )
    updateData.append(displayHeader)

    skillColumnCount: int = len(commonConstant.SKILLS)
    notSkillColumnCount: int = len(headers) - skillColumnCount
    total: list = ([None] * notSkillColumnCount) + ([0] * skillColumnCount)
    formats: list[dict] = []
    for player in players:
        row: list = []

        # No.
        # JSONに変換するため、Decimalをintに変換
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 信仰
        row.append(player["faith"])

        # Lv
        row.append(player["level"])

        # 経験点
        row.append(player["exp"])

        # ピンゾロ
        row.append(player["fumbleExp"])

        # 技能レベル
        for skill in commonConstant.SKILLS:
            level = player["skills"].get(skill["key"], "")
            if level != "":
                # 合計を加算
                total[headers.index(skill["name"])] += 1

            row.append(level)

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

        # 経験点の文字色
        expIndex: int = headers.index("経験点\nピンゾロ含む") + 1
        expTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
        if player["exp"] >= maxExp:
            expTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 1, "green": 0, "blue": 0}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, expIndex),
                    "format": {"textFormat": expTextFormat},
                }
            )
        elif player["exp"] < minimumExp:
            expTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 0, "green": 0, "blue": 1}
            }
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, expIndex),
                    "format": {"textFormat": expTextFormat},
                }
            )

        # PC列のハイパーリンク
        pcIndex: int = headers.index("PC") + 1
        pcTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
        pcTextFormat["link"] = {"uri": player["url"]}
        formats.append(
            {
                "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                "format": {"textFormat": pcTextFormat},
            }
        )

    # 合計行
    total[notSkillColumnCount - 1] = "合計"
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

    # 技能レベルのヘッダー
    startA1: str = utils.rowcol_to_a1(1, notSkillColumnCount + 1)
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
    worksheet.set_basic_filter(1, 1, len(updateData) - 1, len(headers))
