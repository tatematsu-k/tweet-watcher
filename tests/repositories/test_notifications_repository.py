import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from repositories.notifications_repository import NotificationsRepository
from tests.mock.dynamodb import setup_dynamodb_all_tables

TABLE_NAME = "TweetWacherNotificationsTable"

@pytest.fixture(autouse=True)
def setup_dynamodb():
    with setup_dynamodb_all_tables():
        os.environ["NOTIFICATIONS_TABLE"] = TABLE_NAME
        yield

def test_exists_and_put():
    # boto3.resourceのモック
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = NotificationsRepository(table_name="TestTable")

        # exists: アイテムが存在する場合
        mock_table.get_item.return_value = {
            "Item": {"tweet_uid": "1", "slack_ch": "ch"}
        }
        assert repo.exists("1", "ch") is True
        # exists: アイテムが存在しない場合
        mock_table.get_item.return_value = {}
        assert repo.exists("2", "ch") is False

        # put: put_itemが呼ばれること
        repo.put("3", "url", "ch", 123, 45, "2025-01-01T00:00:00Z")
        mock_table.put_item.assert_called_with(
            Item={
                "tweet_uid": "3",
                "tweet_url": "url",
                "slack_ch": "ch",
                "like_count": 123,
                "retweet_count": 45,
                "slack_message_ts": "2025-01-01T00:00:00Z",
            }
        )
