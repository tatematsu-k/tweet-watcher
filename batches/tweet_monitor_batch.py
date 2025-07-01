from datetime import datetime, timezone
from repositories.settings_repository import SettingsRepository
import os
import tweepy

def lambda_handler(event, context):
    # 閾値を環境変数から取得
    like_threshold = int(os.environ.get("LIKE_THRESHOLD", "10"))
    retweet_threshold = int(os.environ.get("RETWEET_THRESHOLD", "5"))
    print(f"[BatchWatcher] LIKE閾値: {like_threshold}, RT閾値: {retweet_threshold}")

    # Twitter API認証情報を環境変数から取得
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        print("[BatchWatcher] Twitter API認証情報が不足しています")
        return {"statusCode": 500, "body": "Twitter API認証情報が不足しています"}

    client = tweepy.Client(bearer_token=bearer_token)

    # 設定テーブルから有効な設定を列挙
    repo = SettingsRepository()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    valid_settings = repo.list_valid_settings(now_iso).get('Items', [])
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")

    # 各設定ごとにキーワード検索
    for setting in valid_settings:
        keyword = setting.get("keyword")
        slack_ch = setting.get("slack_ch")
        print(f"[BatchWatcher] 検索キーワード: {keyword} (slack_ch: {slack_ch})")
        # Twitter APIで検索（例: 直近1日分、最大10件）
        try:
            tweets = client.search_recent_tweets(query=keyword, max_results=10, tweet_fields=["public_metrics", "created_at"])
            print(f"[BatchWatcher] 検索結果: {tweets.data}")
        except Exception as e:
            print(f"[BatchWatcher] Twitter検索失敗: {e}")

    # TODO: like_count, retweet_countで閾値フィルタ
    # TODO: 通知テーブルに新規tweetを保存（重複防止）
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}