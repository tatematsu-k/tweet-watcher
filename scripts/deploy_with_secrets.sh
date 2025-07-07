#!/bin/bash
set -e

# 必要に応じてAWS_PROFILEやAWS_REGIONを指定
# export AWS_PROFILE=your-profile
# export AWS_REGION=ap-northeast-1

# Slackシークレット取得
SLACK_SECRET=$(aws secretsmanager get-secret-value --secret-id tweet-watcher/slack --query 'SecretString' --output text)
SLACK_SIGNATURE=$(echo "$SLACK_SECRET" | jq -r .SLACK_SIGNATURE)
SLACK_BOT_TOKEN=$(echo "$SLACK_SECRET" | jq -r .SLACK_BOT_TOKEN)

# Twitterシークレット取得
TWITTER_SECRET=$(aws secretsmanager get-secret-value --secret-id tweet-watcher/twitter --query 'SecretString' --output text)
TWITTER_BEARER_TOKEN=$(echo "$TWITTER_SECRET" | jq -r .TWITTER_BEARER_TOKEN)

# デプロイ用ビルドディレクトリ作成
rm -rf build
mkdir build
rsync -av --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' lambda_functions/ build/lambda_functions/
rsync -av --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' integration/ build/integration/
rsync -av --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' repositories/ build/repositories/
cp template.yaml samconfig.toml build/
touch build/__init__.py

# Layer用ディレクトリ・zip作成
mkdir -p build/layer/python
pip install -r requirements-prod.txt -t build/layer/python
cd build/layer
zip -r ../lib-layer.zip python
cd ../

# 必要な値が取得できているかチェック
if [ -z "$SLACK_SIGNATURE" ] || [ -z "$SLACK_BOT_TOKEN" ]; then
  echo "[ERROR] Slackシークレットが取得できませんでした。setup_secrets.shで登録済みか確認してください。"
  exit 1
fi
if [ -z "$TWITTER_BEARER_TOKEN" ]; then
  echo "[ERROR] Twitterシークレットが取得できませんでした。setup_secrets.shで登録済みか確認してください。"
  exit 1
fi

echo "[INFO] sam build ..."
sam build --use-container -t template.yaml

echo "[INFO] sam deploy ..."
PARAMS=(
  ParameterKey=SlackSigningSecret,ParameterValue=$SLACK_SIGNATURE
  ParameterKey=SlackBotToken,ParameterValue=$SLACK_BOT_TOKEN
  ParameterKey=TwitterBearerToken,ParameterValue=$TWITTER_BEARER_TOKEN
)
echo "[DEBUG] PARAMS: ${PARAMS[@]}"
sam deploy -t template.yaml --parameter-overrides "${PARAMS[@]}" "$@"

cd ..

echo "[OK] デプロイ完了"

find lambda_functions/ -name '__pycache__' -type d -exec rm -rf {} +
find integration/ -name '__pycache__' -type d -exec rm -rf {} +
find repositories/ -name '__pycache__' -type d -exec rm -rf {} +
