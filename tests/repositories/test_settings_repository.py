from unittest.mock import MagicMock, patch
from repositories.settings_repository import SettingsRepository


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
                "lastExecutedTime": None,
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

        # update_last_executed_time_by_id: update_item呼び出し
        repo.update_last_executed_time_by_id("abc123", "2024-06-13T12:34:56+09:00")
        mock_table.update_item.assert_called_with(
            Key={"id": "abc123"},
            UpdateExpression="SET lastExecutedTime = :lastExecutedTime",
            ExpressionAttributeValues={":lastExecutedTime": "2024-06-13T12:34:56+09:00"},
        )
