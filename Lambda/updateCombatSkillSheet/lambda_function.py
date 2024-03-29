# -*- coding: utf-8 -*-


from typing import Union

from gspread import Spreadsheet, Worksheet, utils
from myLibrary import commonConstant, commonFunction, expStatus

"""
戦闘特技シートを更新
"""


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
    players: list[dict] = event["Players"]

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = commonFunction.OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("戦闘特技")

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
    headers: list[str] = [
        "No.",
        "PC",
        "参加傾向",
        "バトルダンサー",
        "Lv.1",
        "Lv.3",
        "Lv.5",
        "Lv.7",
        "Lv.9",
        "Lv.11",
        "Lv.13",
        "Lv.15",
        "自動取得",
    ]
    updateData.append(headers)
    formats: list[dict] = []
    for player in players:
        row: list = []

        # No.
        row.append(player["no"])

        # PC
        row.append(player["characterName"])

        # 参加傾向
        row.append(
            commonConstant.ENTRY_TREND_INACTIVE
            if player["expStatus"] == expStatus.ExpStatus.INACTIVE
            else commonConstant.ENTRY_TREND_ACTIVE
        )

        # バトルダンサー
        row.append(player["combatFeatsLv1bat"])

        # Lv.1
        row.append(player["combatFeatsLv1"])

        # Lv.3
        row.append(player["combatFeatsLv3"])

        # Lv.5
        row.append(player["combatFeatsLv5"])

        # Lv.7
        row.append(player["combatFeatsLv7"])

        # Lv.9
        row.append(player["combatFeatsLv9"])

        # Lv.11
        row.append(player["combatFeatsLv11"])

        # Lv.13
        row.append(player["combatFeatsLv13"])

        # Lv.15
        row.append(player["combatFeatsLv15"])

        # 自動取得
        for autoCombatFeat in player["autoCombatFeats"]:
            row.append(autoCombatFeat)

        updateData.append(row)

        # 書式設定
        rowIndex: int = updateData.index(row) + 1

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

        # 習得レベルに満たないものはグレーで表示
        grayOutStartIndex: Union[int, None] = None
        for i in range(3, 15, 2):
            if player["level"] < i:
                grayOutStartIndex = headers.index(f"Lv.{i}") + 1
                break

        if grayOutStartIndex is not None:
            grayOutEndIndex: int = headers.index("Lv.15") + 1
            grayOutTextFormat: dict = commonConstant.DEFAULT_TEXT_FORMAT.copy()
            grayOutTextFormat["foregroundColorStyle"] = {
                "rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}
            }
            startA1: str = utils.rowcol_to_a1(rowIndex, grayOutStartIndex)
            endA1: str = utils.rowcol_to_a1(rowIndex, grayOutEndIndex)
            formats.append(
                {
                    "range": f"{startA1}:{endA1}",
                    "format": {"textFormat": grayOutTextFormat},
                }
            )

            # バトルダンサー未習得もグレーで表示
            if player["skills"].get("lvBat", 0) == 0:
                battleDancerIndex: int = headers.index("バトルダンサー") + 1
                battleDancerA1: str = utils.rowcol_to_a1(rowIndex, battleDancerIndex)
                formats.append(
                    {
                        "range": f"{battleDancerA1}:{battleDancerA1}",
                        "format": {"textFormat": grayOutTextFormat},
                    }
                )

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(updateData, value_input_option="USER_ENTERED")

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), worksheet.col_count)
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

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData), worksheet.col_count  # type: ignore
    )
