# SummarizeYtsheet

ゆとシートからデータを集計してGoogleスプレッドシートを更新するよ

実行環境にはAWS Step Functionsを使用しているよ

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

AWS Step FunctionsのState間のPayloadサイズが最大256KBだから必要なデータのみ集計しているよ

### ReorderWorksheets

ワークシートのタブを並び替えるよ

### updateBasicDataSheet

基本シートを更新するよ

### updateSkillLeveSheet

技能シートを更新するよ

### updateStatusSheet

能力値シートを更新するよ

### updateCombatSkillSheet

能力値シートを更新するよ

### InsertPlayerCharacters

PlayerCharactersテーブルを登録するよ

## StepFunctions

### SummarizeYtsheet

ゆとシートからデータを集計してGoogleスプレッドシートを更新するよ  
Googleスプレッドシートの更新はUpdateYtsheetSpreadSheetを呼んでいるよ

### UpdateYtsheetSpreadSheet

Googleスプレッドシートを更新するよ
