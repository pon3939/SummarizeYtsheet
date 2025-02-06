# SummarizeYtsheet

[AWS SAM に移行済み](https://github.com/pon3939/SummarizeCharacterSheets)

ゆとシートからデータを集計して Google スプレッドシートを更新するよ

実行環境には AWS Step Functions を使用しているよ

## Lambda

デバッグ環境構築

```bash
cd Lambda
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -t python
```

### getYtsheetData

ゆとシートからデータを取得するよ

### FormatYtsheetData

ゆとシートから取得したデータをフォーマットするよ

AWS Step Functions の State 間の Payload サイズが最大 256KB だから必要なデータのみ集計しているよ

### UpdateYtsheetSpreadSheet

スプレッドシートを更新するよ

### InsertPlayerCharacters

PlayerCharacters テーブルを登録するよ

### InsertLevelCaps

LevelCaps テーブルを登録するよ

## StepFunctions

### SummarizeYtsheet

ゆとシートからデータを集計して Google スプレッドシートを更新するよ
Google スプレッドシートの更新は UpdateYtsheetSpreadSheet を呼んでいるよ

### UpdateYtsheetSpreadSheet

Google スプレッドシートを更新するよ
