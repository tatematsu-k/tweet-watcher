import os
import boto3
from datetime import datetime, timezone

class XCredentialSettingsRepository:
    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("X_CREDENTIAL_SETTINGS_TABLE", "TweetWacherXCredentialSettingsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def list_all(self):
        return self.table.scan()

    def update_latelimit_reset_time(self, bearer_token, latelimit_reset_time):
        # UTCのエポック秒をISO8601形式に変換
        iso8601_time = datetime.fromtimestamp(latelimit_reset_time, tz=timezone.utc).isoformat().replace('+00:00', 'Z')

        return self.table.update_item(
            Key={"bearer_token": bearer_token},
            UpdateExpression="SET latelimit_reset_time = :latelimit_reset_time",
            ExpressionAttributeValues={":latelimit_reset_time": iso8601_time}
        )

    def get_available_credential(self):
        """
        list_allを取得してlatelimit_reset_timeがnullか現在時刻より前のものを一つ取得
        """
        response = self.list_all()
        items = response.get('Items', [])

        current_time = datetime.now(timezone.utc)

        for item in items:
            latelimit_reset_time = item.get('latelimit_reset_time')

            # latelimit_reset_timeがnullの場合
            if latelimit_reset_time is None:
                return item

            # latelimit_reset_timeが現在時刻より前の場合
            try:
                reset_time = datetime.fromisoformat(latelimit_reset_time.replace('Z', '+00:00'))
                if reset_time.tzinfo is None:
                    reset_time = reset_time.replace(tzinfo=timezone.utc)
                if reset_time < current_time:
                    return item
            except (ValueError, AttributeError):
                # 日時形式が不正な場合は無視して次のアイテムをチェック
                continue

        return None
