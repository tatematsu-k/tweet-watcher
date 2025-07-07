# 設計方針・指摘まとめ（tweet-watcher）

## 1. コマンド・API 設計

- Slack コマンドは `/tweet-watcher setting (create|read|update|delete|help)` 形式
- update/delete は id 指定のみ、id は短い英数字 6 桁
- create 時は id を返却
- update は id 指定でキーワード・終了日両方更新可能
- help コマンドで使い方を案内

## 2. テーブル設計

- TweetWacherSettingsTable の主キーは id（ユニーク・短い英数字 6 桁）
- keyword+slack_ch で GSI を作成し、検索・重複チェックに利用
- id は DynamoDB の主キーなのでユニーク制約が自動で効く

## 3. コード設計

- Integration 基底クラスで input/output を抽象化し、Slack 以外の拡張も容易に
  - 例：SlackIntegration, 今後の他チャットサービスや API 連携にも対応可能
  - lambda_handler や各ロジックは Integration 経由で入出力を統一
  - input の parse, output の build_response をインターフェイス化
- Repository レイヤー（SettingsRepository）で DynamoDB アクセスを集約
  - ストレージ操作を 1 箇所にまとめることで、ビジネスロジックと分離
  - DynamoDB 以外のストレージやテスト用モックへの差し替えも容易
  - API 層は Repository 経由でデータ操作することで責務分離・テスト容易化

## 4. その他

- コード・設計変更時は TODO.md やドキュメントも必ず更新
- Slack 連携手順は SLACK_SETTING.md にまとめる
- テストは pytest+moto で自動化、CI は GitHub Actions で実行

---

今後も設計・運用上の指摘や方針はこのファイルに追記していくこと。
