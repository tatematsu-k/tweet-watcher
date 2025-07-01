# TODO: tweet-watcher 開発タスク

## 1. SAM プロジェクトの初期セットアップ

- [x] SAM テンプレート（template.yaml）の設計
- [x] 必要なリソース（Lambda, API Gateway, EventBridge, DynamoDB, IAM ロールなど）の定義

## 2. DynamoDB テーブル設計・作成

- [x] 設定テーブル
  - [x] 属性: キーワード(string), slack ch(string), 終了日時(datetime)
- [x] 通知テーブル
  - [x] 属性: tweet_url(string), tweet_uid(string), notified_at(datetime), slack ch(string)
- [x] DynamoDB Streams の有効化（通知テーブル）

## 3. API Gateway + Lambda（設定テーブル CRUD 用 API）

- [x] Slack コマンドから API Gateway 経由で設定テーブルの CRUD 操作
- [x] Lambda で CRUD ロジック実装
- [x] API Gateway のエンドポイント設計
- [x] Slack コマンドのリクエスト検証

## 4. EventBridge + Lambda（定期実行バッチ）

- [x] EventBridge で 15 分間隔のスケジュールイベント作成
- [x] Lambda で以下の処理を実装
  - [ ] 設定テーブルから有効な設定を列挙
  - [ ] 各設定ごとに X（Twitter）API でキーワード検索
    - [ ] like_count, retweet_count で閾値フィルタ
  - [ ] 通知テーブルに新規 tweet を保存（重複防止）

## 5. DynamoDB Streams + Lambda（通知 →Slack）

- [ ] 通知テーブルの新規レコード追加をトリガー
- [ ] Lambda で Slack 通知送信
- [ ] 通知送信後、notified_at を更新
- [ ] 多重実行防止ロジック

## 6. Slack 連携

- [ ] Slack App の作成・設定
- [ ] 必要な権限・Webhook/Token の取得
- [ ] Slack 通知・コマンド連携の実装

## 7. デプロイ環境整備

- [ ] sam build / sam deploy の Makefile または MCP コマンド化
- [ ] samconfig.toml の整備
- [ ] 環境変数・Secrets 管理

## 8. README.md 整備

- [ ] システム構成図
- [ ] 各リソース・Lambda の役割説明
- [ ] デプロイ手順・ローカル開発手順
- [ ] Slack 連携手順

---

- [ ] 必要に応じて追加リソース（S3, Secrets Manager 等）を検討
- [ ] テストコード（unit/integration）も随時追加
- [ ] コード・構成の変更は PR 作成 →Slack 報告（tatematsu 宛メンション）
