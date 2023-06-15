# SummarizeYtsheet

ゆとシートからデータを集計してGoogleスプレッドシートを更新するよ

実行環境にはAWS Step Functionsを使用しているよ

## getYtsheetData

ゆとシートからデータを取得するよ

## FormatYtsheetData

ゆとシートから取得したデータをフォーマットするよ

AWS Step FunctionsのState間のPayloadサイズが最大256KBだから必要なデータのみ集計しているよ

## updateBasicDataSheet

基本シートを更新するよ

## updateSkillLeveSheet

技能シートを更新するよ

## updateStatusSheet

能力値シートを更新するよ

## updateCombatSkillSheet

能力値シートを更新するよ
