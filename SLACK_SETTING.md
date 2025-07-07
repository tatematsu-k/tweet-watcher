# Slack 連携設定手順

## 1. Slack App の作成

1. [Slack API: Your Apps](https://api.slack.com/apps) で新規 App を作成
2. Bot ユーザーを追加

## 2. 必要な権限（OAuth Scopes）

- `chat:write`（チャンネルへのメッセージ送信）
- `commands`（スラッシュコマンド利用時）
- `channels:read`（パブリックチャンネル一覧取得、必要に応じて）
- `groups:read`（プライベートチャンネル一覧取得、必要に応じて）

## 3. Bot Token の取得

- App をワークスペースにインストールし、**Bot User OAuth Token**（`xoxb-...`）を取得

## 4. スラッシュコマンドの設定

- 例: `/tweet-watcher`
- リクエスト URL: API Gateway のエンドポイント（例: `https://xxxxxx.execute-api.ap-northeast-1.amazonaws.com/Prod/settings` など）

## 5. Secrets Manager への登録

- `scripts/setup_secrets.sh` を実行し、**SLACK_BOT_TOKEN** を登録
- 既存の場合は上書き確認プロンプトあり
