# -*- coding: utf-8 -*-

from json import loads

from aws_lambda_powertools.utilities.typing import LambdaContext
from gspread import utils
from gspread.spreadsheet import Spreadsheet
from gspread.utils import ValueInputOption
from gspread.worksheet import CellFormat, Worksheet
from MyLibrary.CommonFunction import MakeYtsheetUrl, OpenSpreadsheet
from MyLibrary.Constant import SpreadSheet
from MyLibrary.Player import Player

"""
基本シートを更新
"""


def lambda_handler(event: dict, context: LambdaContext):
    """

    メイン処理

    Args:
        event dict: イベント
        context LambdaContext: コンテキスト
    """

    # 入力
    spreadsheetId: str = event["SpreadsheetId"]
    googleServiceAccount: dict = event["GoogleServiceAccount"]
    players: "list[Player]" = list(
        map(lambda x: Player(**loads(x)), event["Players"])
    )

    # スプレッドシートを開く
    spreadsheet: Spreadsheet = OpenSpreadsheet(
        googleServiceAccount, spreadsheetId
    )
    worksheet: Worksheet = spreadsheet.worksheet("基本")

    # 更新
    UpdateSheet(worksheet, players)


def UpdateSheet(worksheet: Worksheet, players: "list[Player]"):
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
        "参加傾向",
        "PL",
        "種族",
        "種族\nマイナーチェンジ除く",
        "年齢",
        "性別",
        "身長",
        "体重",
        "信仰",
        "穢れ",
        "参加",
        "GM",
        "参加+GM",
        "ガメル",
        "死亡",
    ]

    formats: "list[CellFormat]" = []
    no: int = 0
    for player in players:
        for character in player.Characters:
            row: list = []

            # No.
            no += 1
            row.append(no)

            # PC
            row.append(character.Name)

            # 参加傾向
            row.append(character.ActiveStatus.GetStrForSpreadsheet())

            # PL
            row.append(player.Name)

            # 種族
            row.append(character.GetMinorRace())

            # 種族(マイナーチェンジ除く)
            row.append(character.GetMajorRace())

            # 年齢
            row.append(character.Age)

            # 性別
            row.append(character.Gender)

            # 身長
            row.append(character.Height)

            # 体重
            row.append(character.Weight)

            # 信仰
            row.append(character.Faith)

            # 穢れ
            row.append(character.Sin)

            # 参加
            playerTimes: int = character.PlayerTimes
            row.append(playerTimes)

            # GM
            gameMasterTimes: int = character.GameMasterTimes
            row.append(gameMasterTimes)

            # 参加+GM
            row.append(playerTimes + gameMasterTimes)

            # ガメル
            row.append(character.HistoryMoneyTotal)

            # 死亡
            row.append(character.DiedTimes)

            updateData.append(row)

            # PC列のハイパーリンク
            pcIndex: int = header.index("PC") + 1
            rowIndex: int = updateData.index(row) + 1 + 1
            pcTextFormat: dict = SpreadSheet.DEFAULT_TEXT_FORMAT.copy()
            pcTextFormat["link"] = {"uri": MakeYtsheetUrl(character.YtsheetId)}
            formats.append(
                {
                    "range": utils.rowcol_to_a1(rowIndex, pcIndex),
                    "format": {"textFormat": pcTextFormat},
                }
            )

    # 合計行
    total: list = [None] * len(header)
    activeCountIndex: int = header.index("参加傾向")
    total[activeCountIndex - 1] = "合計"
    total[activeCountIndex] = list(
        map(lambda x: x[activeCountIndex], updateData)
    ).count(SpreadSheet.ACTIVE_STRING)
    headerIndex: int = header.index("死亡")
    total[headerIndex] = sum(
        list(
            map(
                lambda x: (x[headerIndex]),
                updateData,
            )
        )
    )
    updateData.append(total)

    # ヘッダーを追加
    updateData.insert(0, header)

    # クリア
    worksheet.clear()
    worksheet.clear_basic_filter()

    # 更新
    worksheet.update(
        updateData, value_input_option=ValueInputOption.user_entered
    )

    # 書式設定
    # 全体
    startA1: str = utils.rowcol_to_a1(1, 1)
    endA1: str = utils.rowcol_to_a1(len(updateData), len(header))
    worksheet.format(
        f"{startA1}:{endA1}",
        SpreadSheet.DEFAULT_FORMAT,
    )

    # ヘッダー
    startA1 = utils.rowcol_to_a1(1, 1)
    endA1 = utils.rowcol_to_a1(1, len(header))
    formats.append(
        {
            "range": f"{startA1}:{endA1}",
            "format": SpreadSheet.HEADER_DEFAULT_FORMAT,
        }
    )

    # 部分的なフォーマットを設定
    worksheet.batch_format(formats)

    # 行列の固定
    worksheet.freeze(1, 2)

    # フィルター
    worksheet.set_basic_filter(
        1, 1, len(updateData) - 1, len(header)  # type: ignore
    )
