from repositories.settings_repository import SettingsRepository
from repositories.notifications_repository import NotificationsRepository
from repositories.x_credential_settings_repository import XCredentialSettingsRepository
# .env自動ロード（ローカル開発用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import tweepy

def get_twitter_client():
    """
    XCredentialSettingsRepositoryから利用可能な認証情報を取得し、Tweepyクライアントを生成する
    """
    credential_repo = XCredentialSettingsRepository()
    credential = credential_repo.get_available_credential()

    if not credential:
        raise Exception("利用可能なTwitter API認証情報が見つかりません")

    bearer_token = credential.get('bearer_token')
    if not bearer_token:
        raise Exception("Twitter API認証情報が不足しています")

    return tweepy.Client(bearer_token=bearer_token)

def get_valid_settings():
    """
    DynamoDBから全ての設定を取得する
    """
    repo = SettingsRepository()
    return repo.list_valid_settings().get('Items', [])

def search_tweets_by_keyword(client, keyword, max_results=30, error_count=0):
    """
    指定キーワードでTwitter検索を行う
    """
    try:
        tweets = client.search_recent_tweets(query=keyword, max_results=max_results, tweet_fields=["public_metrics", "created_at"])
        return tweets.data if tweets and tweets.data else []
    except tweepy.TooManyRequests as e:
        print(f"[BatchWatcher] Twitter検索失敗 (429 Rate Limit): {e}")
        # Twitter APIのレート制限ヘッダーを表示
        if hasattr(e, 'response') and e.response is not None:
            headers = e.response.headers
            print("[BatchWatcher] Rate Limit Headers:")
            print(f"  x-rate-limit-limit: {headers.get('x-rate-limit-limit', 'N/A')}")
            print(f"  x-rate-limit-remaining: {headers.get('x-rate-limit-remaining', 'N/A')}")
            print(f"  x-rate-limit-reset: {headers.get('x-rate-limit-reset', 'N/A')}")
            print(f"  retry-after: {headers.get('retry-after', 'N/A')}")

            # x-rate-limit-resetヘッダーを取得して認証情報のリセット時間を更新
            reset_time = headers.get('x-rate-limit-reset')
            if reset_time:
                try:
                    reset_time_int = int(reset_time)
                    # 現在使用中のbearer_tokenを取得してリセット時間を更新
                    credential_repo = XCredentialSettingsRepository()
                    credential = credential_repo.get_available_credential()
                    if credential and credential.get('bearer_token'):
                        credential_repo.update_latelimit_reset_time(credential['bearer_token'], reset_time_int)
                        print(f"[BatchWatcher] レート制限リセット時間を更新: {reset_time_int}")
                except (ValueError, TypeError) as parse_error:
                    print(f"[BatchWatcher] リセット時間の解析に失敗: {parse_error}")

        # エラー回数が2以下なら再帰的に再試行
        if error_count < 2:
            print(f"[BatchWatcher] 新しい認証情報で再試行します (試行回数: {error_count + 1})")
            try:
                new_client = get_twitter_client()
                return search_tweets_by_keyword(new_client, keyword, max_results, error_count + 1)
            except Exception as retry_error:
                print(f"[BatchWatcher] 再試行も失敗: {retry_error}")
                return []
        else:
            print(f"[BatchWatcher] 最大試行回数に達しました (試行回数: {error_count + 1})")
            return []
    except Exception as e:
        print(f"[BatchWatcher] Twitter検索失敗: {e}")
        return []

def filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold):
    """
    like_count, retweet_countが閾値以上のツイートのみ抽出
    閾値がNoneの場合はその条件を無視
    """
    filtered = []
    for tweet in tweets:
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else tweet.get('public_metrics', {})
        like_count = metrics.get('like_count', 0)
        retweet_count = metrics.get('retweet_count', 0)
        like_ok = True if like_threshold is None else like_count >= like_threshold
        retweet_ok = True if retweet_threshold is None else retweet_count >= retweet_threshold
        if like_ok and retweet_ok:
            filtered.append(tweet)
    return filtered

def save_notifications_for_tweets(tweets, slack_ch, notifications_repo):
    """
    通知テーブルに未通知のツイートのみ保存する（重複防止）
    """
    for tweet in tweets:
        tweet_uid = str(tweet.id) if hasattr(tweet, 'id') else tweet.get('id')
        tweet_url = f"https://twitter.com/i/web/status/{tweet_uid}"
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else tweet.get('public_metrics', {})
        like_count = metrics.get('like_count', 0)
        retweet_count = metrics.get('retweet_count', 0)
        if not notifications_repo.exists(tweet_uid, slack_ch):
            notifications_repo.put(tweet_uid, tweet_url, slack_ch, like_count, retweet_count)
            print(f"[BatchWatcher] 通知テーブルに保存: {tweet_uid} {tweet_url} {slack_ch} {like_count} {retweet_count}")
        else:
            print(f"[BatchWatcher] 既に通知済み: {tweet_uid} {slack_ch}")

def process_setting_for_notification(setting, client, notifications_repo):
    """
    1つの設定に対してTwitter検索・閾値フィルタ・通知保存をまとめて実行
    設定ごとにlike/retweet_thresholdがあればそれを使う
    """
    keyword = setting.get("keyword")
    slack_ch = setting.get("slack_ch")
    like_threshold = setting.get("like_threshold")
    retweet_threshold = setting.get("retweet_threshold")
    # None許容: 0や""はint変換、未設定はNone
    like_threshold = int(like_threshold) if like_threshold is not None and like_threshold != "" else None
    retweet_threshold = int(retweet_threshold) if retweet_threshold is not None and retweet_threshold != "" else None
    print(f"[BatchWatcher] 検索キーワード: {keyword} (slack_ch: {slack_ch}) like_th: {like_threshold} rt_th: {retweet_threshold}")
    tweets = search_tweets_by_keyword(client, keyword)
    print(f"[BatchWatcher] 検索結果: {tweets}")
    filtered_tweets = filter_tweets_by_thresholds(tweets, like_threshold, retweet_threshold)
    print(f"[BatchWatcher] 閾値通過ツイート: {filtered_tweets}")
    save_notifications_for_tweets(filtered_tweets, slack_ch, notifications_repo)

def lambda_handler(event, context):
    """
    Lambdaバッチのエントリポイント。全体の流れのみ記述。
    """
    try:
        client = get_twitter_client()
    except Exception as e:
        print(f"[BatchWatcher] {e}")
        return {"statusCode": 500, "body": str(e)}
    valid_settings = get_valid_settings()
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")
    notifications_repo = NotificationsRepository()
    for setting in valid_settings:
        process_setting_for_notification(setting, client, notifications_repo)
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}
