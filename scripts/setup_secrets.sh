#!/bin/bash
set -e

# 必要に応じてAWS_PROFILEやAWS_REGIONを指定
# export AWS_PROFILE=your-profile
# export AWS_REGION=ap-northeast-1

echo "--- Slack シークレット登録 ---"
read -p "SLACK_BOT_TOKEN: " SLACK_BOT_TOKEN
read -p "SLACK_SIGNATURE: " SLACK_SIGNATURE

SLACK_SECRET_JSON=$(jq -n \
  --arg token "$SLACK_BOT_TOKEN" \
  --arg signature "$SLACK_SIGNATURE" \
  '{SLACK_BOT_TOKEN: $token, SLACK_SIGNATURE: $signature}')

if aws secretsmanager describe-secret --secret-id tweet-watcher/slack > /dev/null 2>&1; then
  read -p "tweet-watcher/slack は既に存在します。上書きしますか？ (y/N): " CONFIRM
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    aws secretsmanager put-secret-value --secret-id tweet-watcher/slack --secret-string "$SLACK_SECRET_JSON"
    echo "[OK] Slackシークレットを上書きしました: tweet-watcher/slack"
  else
    echo "[SKIP] Slackシークレットの上書きをスキップしました。"
  fi
else
  aws secretsmanager create-secret --name tweet-watcher/slack --secret-string "$SLACK_SECRET_JSON"
  echo "[OK] Slackシークレットを新規作成しました: tweet-watcher/slack"
fi

echo "--- Twitter(X) シークレット登録 ---"
read -p "TWITTER_CONSUMER_KEY: " TWITTER_CONSUMER_KEY
read -p "TWITTER_CONSUMER_SECRET: " TWITTER_CONSUMER_SECRET
read -p "TWITTER_ACCESS_TOKEN: " TWITTER_ACCESS_TOKEN
read -p "TWITTER_ACCESS_TOKEN_SECRET: " TWITTER_ACCESS_TOKEN_SECRET

TWITTER_SECRET_JSON=$(jq -n \
  --arg ckey "$TWITTER_CONSUMER_KEY" \
  --arg csecret "$TWITTER_CONSUMER_SECRET" \
  --arg atoken "$TWITTER_ACCESS_TOKEN" \
  --arg asecret "$TWITTER_ACCESS_TOKEN_SECRET" \
  '{TWITTER_CONSUMER_KEY: $ckey, TWITTER_CONSUMER_SECRET: $csecret, TWITTER_ACCESS_TOKEN: $atoken, TWITTER_ACCESS_TOKEN_SECRET: $asecret}')

if aws secretsmanager describe-secret --secret-id tweet-watcher/twitter > /dev/null 2>&1; then
  read -p "tweet-watcher/twitter は既に存在します。上書きしますか？ (y/N): " CONFIRM
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    aws secretsmanager put-secret-value --secret-id tweet-watcher/twitter --secret-string "$TWITTER_SECRET_JSON"
    echo "[OK] Twitter(X)シークレットを上書きしました: tweet-watcher/twitter"
  else
    echo "[SKIP] Twitter(X)シークレットの上書きをスキップしました。"
  fi
else
  aws secretsmanager create-secret --name tweet-watcher/twitter --secret-string "$TWITTER_SECRET_JSON"
  echo "[OK] Twitter(X)シークレットを新規作成しました: tweet-watcher/twitter"
fi

echo "---"
echo "Secretsの値は標準入力で安全に登録されました。"
echo "bash scripts/setup_secrets.sh"
