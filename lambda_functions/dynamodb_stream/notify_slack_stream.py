import os
import boto3
from datetime import datetime, timezone
from integration.slack_integration import SlackIntegration


def lambda_handler(event, context):
    """
    DynamoDB Streamsの新規レコード追加をトリガーにSlack通知を送信し、notified_atとslack_message_tsを更新するLambda関数。
    多重実行防止も考慮。
    """
    print(
        f"[notify_slack_stream] Lambda関数開始: {datetime.now(timezone.utc).isoformat()}"
    )
    print(f"[notify_slack_stream] 受信したレコード数: {len(event.get('Records', []))}")

    table_name = os.environ.get("NOTIFICATIONS_TABLE", "TweetWacherNotificationsTable")
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    print(f"[notify_slack_stream] テーブル名: {table_name}")
    print(
        f"[notify_slack_stream] Slack Bot Token設定: {'あり' if slack_bot_token else 'なし'}"
    )

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    slack = SlackIntegration(bot_token=slack_bot_token)

    processed_count = 0
    skipped_count = 0

    for i, record in enumerate(event.get("Records", [])):
        print(
            f"[notify_slack_stream] レコード {i+1} 処理開始: eventName={record.get('eventName')}"
        )

        if record["eventName"] != "INSERT":
            print(
                f"[notify_slack_stream] レコード {i+1} スキップ: INSERT以外のイベント"
            )
            continue

        new_image = record["dynamodb"].get("NewImage", {})
        tweet_url = new_image.get("tweet_url", {}).get("S")
        slack_ch = new_image.get("slack_ch", {}).get("S")
        tweet_uid = new_image.get("tweet_uid", {}).get("S")
        notified_at = new_image.get("notified_at", {}).get("S")
        like_count = int(new_image.get("like_count", {}).get("N", 0)) if "like_count" in new_image else None
        retweet_count = int(new_image.get("retweet_count", {}).get("N", 0)) if "retweet_count" in new_image else None

        print(
            f"[notify_slack_stream] レコード {i+1} データ: tweet_uid={tweet_uid}, slack_ch={slack_ch}, tweet_url={tweet_url}, notified_at={notified_at}, like_count={like_count}, retweet_count={retweet_count}"
        )

        # 冪等性: すでにnotified_atが埋まっていればスキップ
        if notified_at:
            print(
                f"[notify_slack_stream] レコード {i+1} スキップ: 既に通知済み (notified_at={notified_at})"
            )
            skipped_count += 1
            continue

        try:
            # Slack通知送信（Bot方式、thread_tsは現状None）
            print(
                f"[notify_slack_stream] レコード {i+1} Slack通知送信開始: channel={slack_ch}"
            )
            # blocks形式でリッチ通知
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*新しいツイート通知*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*👍 いいね:* {like_count if like_count is not None else '-'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🔁 リツイート:* {retweet_count if retweet_count is not None else '-'}"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "ツイートを表示"},
                            "url": tweet_url
                        }
                    ]
                }
            ]
            ts = slack.send_message(slack_ch, "新しいツイート通知", blocks=blocks)
            print(f"[notify_slack_stream] レコード {i+1} Slack通知送信成功: ts={ts}")

            # notified_atとslack_message_tsを現在時刻・tsで更新
            now_iso = datetime.now(timezone.utc).isoformat()
            print(
                f"[notify_slack_stream] レコード {i+1} DynamoDB更新開始: notified_at={now_iso}, slack_message_ts={ts}"
            )

            table.update_item(
                Key={"tweet_uid": tweet_uid, "slack_ch": slack_ch},
                UpdateExpression="SET notified_at = :n, slack_message_ts = :ts",
                ExpressionAttributeValues={":n": now_iso, ":ts": ts},
            )
            print(f"[notify_slack_stream] レコード {i+1} DynamoDB更新成功")
            processed_count += 1

        except Exception as e:
            print(f"[notify_slack_stream] レコード {i+1} エラー: {str(e)}")
            raise e

    print(
        f"[notify_slack_stream] 処理完了: 処理済み={processed_count}, スキップ={skipped_count}"
    )
    return {
        "statusCode": 200,
        "body": (
            f"Notifications processed. Processed: {processed_count}, Skipped: {skipped_count}"
        ),
    }
