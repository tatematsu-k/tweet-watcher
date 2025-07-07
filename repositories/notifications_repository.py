import os
import boto3

class NotificationsRepository:
    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("NOTIFICATIONS_TABLE", "TweetWacherNotificationsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def exists(self, tweet_uid, slack_ch):
        resp = self.table.get_item(Key={"tweet_uid": tweet_uid, "slack_ch": slack_ch})
        return 'Item' in resp

    def put(self, tweet_uid, tweet_url, slack_ch, like_count, retweet_count, slack_message_ts=None):
        item = {
            "tweet_uid": tweet_uid,
            "tweet_url": tweet_url,
            "slack_ch": slack_ch,
            "like_count": like_count,
            "retweet_count": retweet_count
        }
        if slack_message_ts is not None:
            item["slack_message_ts"] = slack_message_ts
        self.table.put_item(Item=item)
