import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from repositories.settings_repository import SettingsRepository
from tests.mock.dynamodb import setup_dynamodb_all_tables

TABLE_NAME = "TweetWacherSettingsTable"

@pytest.fixture(autouse=True)
def setup_dynamodb():
    with setup_dynamodb_all_tables():
        os.environ["SETTINGS_TABLE"] = TABLE_NAME
        yield

def test_put_get_delete_update():
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = SettingsRepository(table_name="TestTweetWacherSettingsTable")

        # put: ID生成とput_item呼び出し
        repo._generate_short_id = MagicMock(return_value="abc123")
        mock_table.get_item.return_value = {}  # ID重複なし
        result = repo.put("kw", "ch")
        mock_table.put_item.assert_called_with(
            Item={
                "id": "abc123",
                "keyword": "kw",
                "slack_ch": "ch",
                "publication_status": result["publication_status"],
            }
        )

        # get_by_id: get_item呼び出し
        repo.get_by_id("abc123")
        mock_table.get_item.assert_called_with(Key={"id": "abc123"})

        # delete_by_id: delete_item呼び出し
        repo.delete_by_id("abc123")
        mock_table.delete_item.assert_called_with(Key={"id": "abc123"})

        # update_keyword_by_id: update_item呼び出し
        repo.update_keyword_by_id("abc123", "kw2")
        mock_table.update_item.assert_called_with(
            Key={"id": "abc123"},
            UpdateExpression="SET keyword = :keyword",
            ExpressionAttributeValues={":keyword": "kw2"},
        )
