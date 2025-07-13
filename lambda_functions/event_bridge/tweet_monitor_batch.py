from repositories.settings_repository import SettingsRepository
from repositories.notifications_repository import NotificationsRepository
from repositories.x_credential_settings_repository import XCredentialSettingsRepository
from integration.slack_integration import SlackIntegration
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

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


def fetch_tweets_from_twitter_api(bearer_token, keyword, max_results=30):
    """
    Twitter APIに1回だけリクエストし、結果を返す。エラー時は例外を投げる。
    """
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": keyword,
        "max_results": max_results,
        "tweet.fields": "public_metrics,created_at",
    }
    full_url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        full_url, headers={"Authorization": f"Bearer {bearer_token}"}
    )
    with urllib.request.urlopen(req) as res:
        if res.status == 429:
            raise urllib.error.HTTPError(
                full_url, 429, "Rate limit exceeded", res.headers, None
            )
        data = json.load(res)
        return data.get("data", [])


def search_tweets_by_keyword(bearer_token, keyword, max_results=30, max_retry=2):
    """
    指定キーワードでTwitter検索を行う。レートリミット時は認証情報を切り替えてリトライ。
    """
    for error_count in range(max_retry + 1):
        try:
            return fetch_tweets_from_twitter_api(bearer_token, keyword, max_results)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(
                    f"Rate limit exceeded (HTTPError) [{error_count+1}/{max_retry+1}]"
                )
                if error_count < max_retry:
                    try:
                        bearer_token = get_twitter_client()
                        continue
                    except Exception as retry_error:
                        print(f"[BatchWatcher] 認証情報切り替え失敗: {retry_error}")
                        return []
                else:
                    print(
                        f"[BatchWatcher] 最大試行回数に達しました (試行回数: {error_count + 1})"
                    )
                    return []
            else:
                print(f"HTTPError: {e}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
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


def save_notifications_for_tweets(
    tweets, slack_ch, notifications_repo, slack_integration=None
):
    """
    通知テーブルに未通知のツイートのみ保存し、Slack通知も送信する（重複防止）
    """
    if slack_integration is None:
        slack_integration = SlackIntegration()
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
            # Slack通知送信
            try:
                msg = f"新しいツイート: {tweet_url}\n👍 {like_count} 🔁 {retweet_count}"
                slack_integration.send_message(slack_ch, msg)
                print(f"[BatchWatcher] Slack通知送信: {slack_ch} {tweet_url}")
            except Exception as e:
                print(f"[BatchWatcher] Slack通知失敗: {e}")
        else:
            print(f"[BatchWatcher] 既に通知済み: {tweet_uid} {slack_ch}")


def process_setting_for_notification(
    setting, bearer_token, notifications_repo, slack_integration=None
):
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
    save_notifications_for_tweets(
        filtered_tweets, slack_ch, notifications_repo, slack_integration
    )
    # 正常に処理が終わったらlastExecutedTimeをJSTのISO8601で保存
    try:
        settings_repo = SettingsRepository()
        now_jst = datetime.now(timezone(timedelta(hours=9))).isoformat()
        settings_repo.update_last_executed_time_by_id(setting["id"], now_jst)
        print(f"[BatchWatcher] lastExecutedTime更新: {setting['id']} {now_jst}")
    except Exception as e:
        print(f"[BatchWatcher] lastExecutedTime更新失敗: {e}")


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
    slack_integration = SlackIntegration()

    # lastExecutedTimeがnull→古い順でソート
    def sort_key(setting):
        t = setting.get("lastExecutedTime")
        if not t:
            return (0, None)
        try:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
        except Exception:
            return (1, None)
        return (1, dt)

    valid_settings = sorted(valid_settings, key=sort_key)
    for setting in valid_settings:
        process_setting_for_notification(
            setting, bearer_token, notifications_repo, slack_integration
        )
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}
