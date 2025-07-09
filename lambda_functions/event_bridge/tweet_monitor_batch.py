from repositories.settings_repository import SettingsRepository
from repositories.notifications_repository import NotificationsRepository
from repositories.x_credential_settings_repository import XCredentialSettingsRepository
import json
import urllib.request
import urllib.parse

# .env自動ロード（ローカル開発用）
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def get_twitter_client():
    """
    XCredentialSettingsRepositoryから利用可能な認証情報を取得し、Bearer Tokenを返す
    """
    credential_repo = XCredentialSettingsRepository()
    credential = credential_repo.get_available_credential()

    if not credential:
        raise Exception("利用可能なTwitter API認証情報が見つかりません")

    bearer_token = credential.get("bearer_token")
    if not bearer_token:
        raise Exception("Twitter API認証情報が不足しています")

    return bearer_token


def get_valid_settings():
    """
    DynamoDBから全ての設定を取得する
    """
    repo = SettingsRepository()
    return repo.list_valid_settings().get("Items", [])


def search_tweets_by_keyword(bearer_token, keyword, max_results=30, error_count=0):
    """
    指定キーワードでTwitter検索を行う（標準ライブラリで実装）
    """
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": keyword,
        "max_results": max_results,
        "tweet.fields": "public_metrics,created_at"
    }
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        full_url,
        headers={"Authorization": f"Bearer {bearer_token}"}
    )
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 429:
                print("Rate limit exceeded")
                return []
            data = json.load(res)
            return data.get("data", [])
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("Rate limit exceeded (HTTPError)")
            # レートリミット時の処理
            # 必要に応じてリトライやヘッダー参照
            if error_count < 2:
                print(f"[BatchWatcher] 新しい認証情報で再試行します (試行回数: {error_count + 1})")
                try:
                    new_bearer_token = get_twitter_client()
                    return search_tweets_by_keyword(new_bearer_token, keyword, max_results, error_count + 1)
                except Exception as retry_error:
                    print(f"[BatchWatcher] 再試行も失敗: {retry_error}")
                    return []
            else:
                print(f"[BatchWatcher] 最大試行回数に達しました (試行回数: {error_count + 1})")
                return []
        else:
            print(f"HTTPError: {e}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold):
    """
    like_count, retweet_countが閾値以上のツイートのみ抽出
    閾値がNoneの場合はその条件を無視
    """
    filtered = []
    for tweet in tweets:
        metrics = (
            tweet.public_metrics
            if hasattr(tweet, "public_metrics")
            else tweet.get("public_metrics", {})
        )
        like_count = metrics.get("like_count", 0)
        retweet_count = metrics.get("retweet_count", 0)
        like_ok = True if like_threshold is None else like_count >= like_threshold
        retweet_ok = (
            True if retweet_threshold is None else retweet_count >= retweet_threshold
        )
        if like_ok and retweet_ok:
            filtered.append(tweet)
    return filtered


def save_notifications_for_tweets(tweets, slack_ch, notifications_repo):
    """
    通知テーブルに未通知のツイートのみ保存する（重複防止）
    """
    for tweet in tweets:
        tweet_uid = str(tweet.id) if hasattr(tweet, "id") else tweet.get("id")
        tweet_url = f"https://twitter.com/i/web/status/{tweet_uid}"
        metrics = (
            tweet.public_metrics
            if hasattr(tweet, "public_metrics")
            else tweet.get("public_metrics", {})
        )
        like_count = metrics.get("like_count", 0)
        retweet_count = metrics.get("retweet_count", 0)
        if not notifications_repo.exists(tweet_uid, slack_ch):
            notifications_repo.put(
                tweet_uid, tweet_url, slack_ch, like_count, retweet_count
            )
            print(
                f"[BatchWatcher] 通知テーブルに保存: {tweet_uid} {tweet_url} {slack_ch} {like_count} {retweet_count}"
            )
        else:
            print(f"[BatchWatcher] 既に通知済み: {tweet_uid} {slack_ch}")


def process_setting_for_notification(setting, bearer_token, notifications_repo):
    """
    1つの設定に対してTwitter検索・閾値フィルタ・通知保存をまとめて実行
    設定ごとにlike/retweet_thresholdがあればそれを使う
    """
    keyword = setting.get("keyword")
    slack_ch = setting.get("slack_ch")
    like_threshold = setting.get("like_threshold")
    retweet_threshold = setting.get("retweet_threshold")
    # None許容: 0や""はint変換、未設定はNone
    like_threshold = (
        int(like_threshold)
        if like_threshold is not None and like_threshold != ""
        else None
    )
    retweet_threshold = (
        int(retweet_threshold)
        if retweet_threshold is not None and retweet_threshold != ""
        else None
    )
    print(
        f"[BatchWatcher] 検索キーワード: {keyword} (slack_ch: {slack_ch}) like_th: {like_threshold} rt_th: {retweet_threshold}"
    )
    tweets = search_tweets_by_keyword(bearer_token, keyword)
    print(f"[BatchWatcher] 検索結果: {tweets}")
    filtered_tweets = filter_tweets_by_thresholds(
        tweets, like_threshold, retweet_threshold
    )
    print(f"[BatchWatcher] 閾値通過ツイート: {filtered_tweets}")
    save_notifications_for_tweets(filtered_tweets, slack_ch, notifications_repo)


def lambda_handler(event, context):
    """
    Lambdaバッチのエントリポイント。全体の流れのみ記述。
    """
    try:
        bearer_token = get_twitter_client()
    except Exception as e:
        print(f"[BatchWatcher] {e}")
        return {"statusCode": 500, "body": str(e)}
    valid_settings = get_valid_settings()
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")
    notifications_repo = NotificationsRepository()
    for setting in valid_settings:
        process_setting_for_notification(setting, bearer_token, notifications_repo)
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}
