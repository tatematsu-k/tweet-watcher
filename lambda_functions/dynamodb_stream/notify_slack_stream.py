import os
import boto3
from datetime import datetime, timezone
from integration.slack_integration import SlackIntegration

def lambda_handler(event, context):
    """
    DynamoDB Streamsの新規レコード追加をトリガーにSlack通知を送信し、notified_atとslack_message_tsを更新するLambda関数。
    多重実行防止も考慮。
    """
    table_name = os.environ.get("NOTIFICATIONS_TABLE", "TweetWacherNotificationsTable")
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    slack = SlackIntegration(bot_token=slack_bot_token)

    for record in event.get("Records", []):
        if record["eventName"] != "INSERT":
            continue
        new_image = record["dynamodb"].get("NewImage", {})
        tweet_url = new_image.get("tweet_url", {}).get("S")
        slack_ch = new_image.get("slack_ch", {}).get("S")
        tweet_uid = new_image.get("tweet_uid", {}).get("S")
        notified_at = new_image.get("notified_at", {}).get("S")
        # 冪等性: すでにnotified_atが埋まっていればスキップ
        if notified_at:
            continue
        # Slack通知送信（Bot方式、thread_tsは現状None）
        ts = slack.send_message(slack_ch, f"新しいツイート通知: {tweet_url}")
        # notified_atとslack_message_tsを現在時刻・tsで更新
        now_iso = datetime.now(timezone.utc).isoformat()
        table.update_item(
            Key={"tweet_uid": tweet_uid, "slack_ch": slack_ch},
            UpdateExpression="SET notified_at = :n, slack_message_ts = :ts",
            ExpressionAttributeValues={":n": now_iso, ":ts": ts}
        )
    return {"statusCode": 200, "body": "Notifications processed."}
