from datetime import datetime, timezone
from repositories.settings_repository import SettingsRepository

def lambda_handler(event, context):
    # 設定テーブルから有効な設定を列挙
    repo = SettingsRepository()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    valid_settings = repo.list_valid_settings(now_iso).get('Items', [])
    print(f"[BatchWatcher] 有効な設定: {valid_settings}")
    # TODO: 各設定ごとにX(Twitter)APIでキーワード検索
    # TODO: like_count, retweet_countで閾値フィルタ
    # TODO: 通知テーブルに新規tweetを保存（重複防止）
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}