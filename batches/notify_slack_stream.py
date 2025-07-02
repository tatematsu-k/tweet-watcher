import os
import boto3
from datetime import datetime, timezone
from integration.slack_integration import SlackIntegration

def lambda_handler(event, context):
    """
    DynamoDB Streamsの新規レコード追加をトリガーにSlack通知を送信し、notified_atを更新するLambda関数。
    多重実行防止も考慮。
    """
    table_name = os.environ.get("NOTIFICATIONS_TABLE", "NotificationsTable")
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    slack = SlackIntegration(slack_webhook_url)

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
        # Slack通知送信
        slack.send_message(slack_ch, f"新しいツイート通知: {tweet_url}")
        # notified_atを現在時刻で更新
        now_iso = datetime.now(timezone.utc).isoformat()
        table.update_item(
            Key={"tweet_uid": tweet_uid, "slack_ch": slack_ch},
            UpdateExpression="SET notified_at = :n",
            ExpressionAttributeValues={":n": now_iso}
        )
    return {"statusCode": 200, "body": "Notifications processed."}
