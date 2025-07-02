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

    def put(self, tweet_uid, tweet_url, slack_ch, notified_at=None):
        if notified_at is None:
            notified_at = datetime.now(timezone.utc).isoformat()
        self.table.put_item(Item={
            "tweet_uid": tweet_uid,
            "tweet_url": tweet_url,
            "slack_ch": slack_ch,
            "notified_at": notified_at
        })