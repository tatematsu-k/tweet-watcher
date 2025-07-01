from datetime import datetime, timezone
from repositories.settings_repository import SettingsRepository
from repositories.notifications_repository import NotificationsRepository
import os
import tweepy
# .env自動ロード（ローカル開発用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_thresholds():
    """
    環境変数からLIKE/RETWEETの閾値を取得する
    """
    like_threshold = int(os.environ.get("LIKE_THRESHOLD", "10"))
    retweet_threshold = int(os.environ.get("RETWEET_THRESHOLD", "5"))
    return like_threshold, retweet_threshold

def get_twitter_client():
    """
    環境変数から認証情報を取得し、Tweepyクライアントを生成する
    """
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise Exception("Twitter API認証情報が不足しています")
    return tweepy.Client(bearer_token=bearer_token)

def get_valid_settings():
    """
    DynamoDBから有効な設定（end_atが未来）を取得する
    """
    repo = SettingsRepository()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    return repo.list_valid_settings(now_iso).get('Items', [])

def search_tweets_by_keyword(client, keyword, max_results=30):
    """
    指定キーワードでTwitter検索を行う
    """
    try:
        tweets = client.search_recent_tweets(query=keyword, max_results=max_results, tweet_fields=["public_metrics", "created_at"])
        return tweets.data if tweets and tweets.data else []
    except Exception as e:
        print(f"[BatchWatcher] Twitter検索失敗: {e}")
        return []

def filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold):
    """
    like_count, retweet_countが閾値以上のツイートのみ抽出
    """
    filtered = []
    for tweet in tweets:
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else tweet.get('public_metrics', {})
        like_count = metrics.get('like_count', 0)
        retweet_count = metrics.get('retweet_count', 0)
        if like_count >= like_threshold and retweet_count >= retweet_threshold:
            filtered.append(tweet)
    return filtered

def save_notifications_for_tweets(tweets, slack_ch, notifications_repo):
    """
    通知テーブルに未通知のツイートのみ保存する（重複防止）
    """
    for tweet in tweets:
        tweet_uid = str(tweet.id) if hasattr(tweet, 'id') else tweet.get('id')
        tweet_url = f"https://twitter.com/i/web/status/{tweet_uid}"
        if not notifications_repo.exists(tweet_uid, slack_ch):
            notifications_repo.put(tweet_uid, tweet_url, slack_ch)
            print(f"[BatchWatcher] 通知テーブルに保存: {tweet_uid} {tweet_url} {slack_ch}")
        else:
            print(f"[BatchWatcher] 既に通知済み: {tweet_uid} {slack_ch}")

def process_setting_for_notification(setting, client, like_threshold, retweet_threshold, notifications_repo):
    """
    1つの設定に対してTwitter検索・閾値フィルタ・通知保存をまとめて実行
    """
    keyword = setting.get("keyword")
    slack_ch = setting.get("slack_ch")
    print(f"[BatchWatcher] 検索キーワード: {keyword} (slack_ch: {slack_ch})")
    tweets = search_tweets_by_keyword(client, keyword)
    print(f"[BatchWatcher] 検索結果: {tweets}")
    filtered_tweets = filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold)
    print(f"[BatchWatcher] 閾値通過ツイート: {filtered_tweets}")
    save_notifications_for_tweets(filtered_tweets, slack_ch, notifications_repo)

def lambda_handler(event, context):
    """
    Lambdaバッチのエントリポイント。全体の流れのみ記述。
    """
    like_threshold, retweet_threshold = get_thresholds()
    print(f"[BatchWatcher] LIKE閾値: {like_threshold}, RT閾値: {retweet_threshold}")
    try:
        client = get_twitter_client()
    except Exception as e:
        print(f"[BatchWatcher] {e}")
        return {"statusCode": 500, "body": str(e)}
    valid_settings = get_valid_settings()
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")
    notifications_repo = NotificationsRepository()
    for setting in valid_settings:
        process_setting_for_notification(setting, client, like_threshold, retweet_threshold, notifications_repo)
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}
