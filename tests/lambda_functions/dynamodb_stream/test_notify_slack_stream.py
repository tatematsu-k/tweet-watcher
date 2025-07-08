import os
from unittest.mock import patch, MagicMock
from lambda_functions.dynamodb_stream import notify_slack_stream


def make_stream_event(tweet_uid, tweet_url, slack_ch, notified_at=None):
    new_image = {
        "tweet_uid": {"S": tweet_uid},
        "tweet_url": {"S": tweet_url},
        "slack_ch": {"S": slack_ch},
    }
    if notified_at:
        new_image["notified_at"] = {"S": notified_at}
    return {"Records": [{"eventName": "INSERT", "dynamodb": {"NewImage": new_image}}]}


@patch("lambda_functions.dynamodb_stream.notify_slack_stream.SlackIntegration")
@patch("boto3.resource")
def test_notify_and_update(mock_boto3_resource, mock_slack_integration):
    # モック準備
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table
    mock_slack = MagicMock()
    mock_slack.send_message.return_value = "12345.6789"
    mock_slack_integration.return_value = mock_slack
    os.environ["NOTIFICATIONS_TABLE"] = "TweetWacherNotificationsTable"
    os.environ["SLACK_BOT_TOKEN"] = "dummy"

    event = make_stream_event("uid1", "https://x.com/1", "C12345")
    result = notify_slack_stream.lambda_handler(event, None)

    # blocks形式の呼び出しに合わせて修正
    expected_blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*新しいツイート通知*"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*👍 いいね:* -"},
                {"type": "mrkdwn", "text": "*🔁 リツイート:* -"},
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "ツイートを表示"},
                    "url": "https://x.com/1",
                }
            ],
        },
    ]
    mock_slack.send_message.assert_called_once_with(
        "C12345", "新しいツイート通知", blocks=expected_blocks
    )
    mock_table.update_item.assert_called_once()
    args, kwargs = mock_table.update_item.call_args
    assert kwargs["ExpressionAttributeValues"][":ts"] == "12345.6789"
    assert result["statusCode"] == 200


@patch("lambda_functions.dynamodb_stream.notify_slack_stream.SlackIntegration")
@patch("boto3.resource")
def test_idempotency(mock_boto3_resource, mock_slack_integration):
    # notified_atが既に埋まっている場合は何もしない
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table
    mock_slack = MagicMock()
    mock_slack_integration.return_value = mock_slack
    os.environ["NOTIFICATIONS_TABLE"] = "TweetWacherNotificationsTable"
    os.environ["SLACK_BOT_TOKEN"] = "dummy"

    event = make_stream_event(
        "uid2", "https://x.com/2", "C12345", notified_at="2024-07-01T00:00:00Z"
    )
    result = notify_slack_stream.lambda_handler(event, None)

    mock_slack.send_message.assert_not_called()
    mock_table.update_item.assert_not_called()
    assert result["statusCode"] == 200
