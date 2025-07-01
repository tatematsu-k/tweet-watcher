# Slack 連携設定手順

## 1. Slack App の作成

1. https://api.slack.com/apps から「Create New App」
2. App Name 例: tweet-watcher
3. ワークスペースを選択

## 2. Slash Command の登録

1. Features > Slash Commands > Create New Command
2. コマンド例: `/tweet-watcher`
3. Request URL: API Gateway のエンドポイント URL（例: `https://xxxx.execute-api.ap-northeast-1.amazonaws.com/Prod/settings`）
4. Short Description: 設定管理
5. Usage Hint: `setting [create|read|update|delete|help] ...`

## 3. 権限設定（OAuth & Permissions）

- `commands` 権限を追加
- 必要に応じて `chat:write` なども追加

## 4. App のインストール

- ワークスペースにインストール

## 5. 署名検証用情報の取得

- Basic Information > Signing Secret を控える
- Lambda の環境変数等で利用

## 6. Lambda/API Gateway 側の注意

- POST リクエストの Content-Type は `application/x-www-form-urlencoded`
- 署名検証（X-Slack-Signature, X-Slack-Request-Timestamp）を Lambda で実装推奨

## 7. コマンド例

- `/tweet-watcher setting create キーワード #slackチャンネル 2024-12-31`
- `/tweet-watcher setting read キーワード`
- `/tweet-watcher setting update キーワード #slackチャンネル 2025-01-01`
- `/tweet-watcher setting delete キーワード`
- `/tweet-watcher setting help`
