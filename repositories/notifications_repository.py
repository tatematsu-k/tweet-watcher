import os
import boto3
from datetime import datetime, timezone

class NotificationsRepository:
    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("NOTIFICATIONS_TABLE", "NotificationsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self, tweet_uid, slack_ch):
        resp = self.table.get_item(Key={"tweet_uid": tweet_uid, "slack_ch": slack_ch})
        return 'Item' in resp

    def put(self, tweet_uid, tweet_url, slack_ch, notified_at=None, slack_message_ts=None):
        if notified_at is None:
            notified_at = datetime.now(timezone.utc).isoformat()
        item = {
            "tweet_uid": tweet_uid,
            "tweet_url": tweet_url,
            "slack_ch": slack_ch,
            "notified_at": notified_at
        }
        if slack_message_ts is not None:
            item["slack_message_ts"] = slack_message_ts
        self.table.put_item(Item=item)