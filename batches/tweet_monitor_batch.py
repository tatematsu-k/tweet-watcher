from datetime import datetime, timezone
from repositories.settings_repository import SettingsRepository
import os
import tweepy

def get_thresholds():
    like_threshold = int(os.environ.get("LIKE_THRESHOLD", "10"))
    retweet_threshold = int(os.environ.get("RETWEET_THRESHOLD", "5"))
    return like_threshold, retweet_threshold

def get_twitter_client():
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise Exception("Twitter API認証情報が不足しています")
    return tweepy.Client(bearer_token=bearer_token)

def get_valid_settings():
    repo = SettingsRepository()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    return repo.list_valid_settings(now_iso).get('Items', [])

def search_tweets_by_keyword(client, keyword, max_results=10):
    try:
        tweets = client.search_recent_tweets(query=keyword, max_results=max_results, tweet_fields=["public_metrics", "created_at"])
        return tweets.data if tweets and tweets.data else []
    except Exception as e:
        print(f"[BatchWatcher] Twitter検索失敗: {e}")
        return []

def filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold):
    filtered = []
    for tweet in tweets:
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else tweet.get('public_metrics', {})
        like_count = metrics.get('like_count', 0)
        retweet_count = metrics.get('retweet_count', 0)
        if like_count >= like_threshold and retweet_count >= retweet_threshold:
            filtered.append(tweet)
    return filtered

def lambda_handler(event, context):
    # 閾値取得
    like_threshold, retweet_threshold = get_thresholds()
    print(f"[BatchWatcher] LIKE閾値: {like_threshold}, RT閾値: {retweet_threshold}")

    # Twitterクライアント取得
    try:
        client = get_twitter_client()
    except Exception as e:
        print(f"[BatchWatcher] {e}")
        return {"statusCode": 500, "body": str(e)}

    # 有効な設定取得
    valid_settings = get_valid_settings()
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")

    # 各設定ごとにキーワード検索
    for setting in valid_settings:
        keyword = setting.get("keyword")
        slack_ch = setting.get("slack_ch")
        print(f"[BatchWatcher] 検索キーワード: {keyword} (slack_ch: {slack_ch})")
        tweets = search_tweets_by_keyword(client, keyword)
        print(f"[BatchWatcher] 検索結果: {tweets}")
        filtered_tweets = filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold)
        print(f"[BatchWatcher] 閾値通過ツイート: {filtered_tweets}")
        # TODO: 通知テーブルに新規tweetを保存（重複防止）

    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}