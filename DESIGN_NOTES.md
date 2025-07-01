# 設計方針・指摘まとめ（tweet-watcher）

## 1. コマンド・API 設計

- Slack コマンドは `/tweet-watcher setting (create|read|update|delete|help)` 形式
- update/delete は id 指定のみ、id は短い英数字 6 桁
- create 時は id を返却
- update は id 指定でキーワード・終了日両方更新可能
- help コマンドで使い方を案内

## 2. テーブル設計

- SettingsTable の主キーは id（ユニーク・短い英数字 6 桁）
- keyword+slack_ch で GSI を作成し、検索・重複チェックに利用
- id は DynamoDB の主キーなのでユニーク制約が自動で効く

## 3. コード設計

- Integration 基底クラスで input/output を抽象化し、Slack 以外の拡張も容易に
- SettingsRepository で DynamoDB アクセスを集約
- parse_end_at 等の共通処理は common 配下に分離

## 4. その他

- コード・設計変更時は TODO.md やドキュメントも必ず更新
- Slack 連携手順は SLACK_SETTING.md にまとめる
- テストは pytest+moto で自動化、CI は GitHub Actions で実行

---

今後も設計・運用上の指摘や方針はこのファイルに追記していくこと。
