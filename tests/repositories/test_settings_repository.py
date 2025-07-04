from unittest.mock import MagicMock, patch
from repositories.settings_repository import SettingsRepository

def test_put_get_delete_update():
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = SettingsRepository(table_name='TestSettingsTable')

        # put: ID生成とput_item呼び出し
        repo._generate_short_id = MagicMock(return_value='abc123')
        mock_table.get_item.return_value = {}  # ID重複なし
        repo.put('kw', 'ch', '2025-01-01T00:00:00Z')
        mock_table.put_item.assert_called_with(Item={
            'id': 'abc123',
            'keyword': 'kw',
            'slack_ch': 'ch',
            'end_at': '2025-01-01T00:00:00Z'
        })

        # get_by_id: get_item呼び出し
        repo.get_by_id('abc123')
        mock_table.get_item.assert_called_with(Key={'id': 'abc123'})

        # delete_by_id: delete_item呼び出し
        repo.delete_by_id('abc123')
        mock_table.delete_item.assert_called_with(Key={'id': 'abc123'})

        # update_by_id: update_item呼び出し
        repo.update_by_id('abc123', '2026-01-01T00:00:00Z', 'kw2')
        mock_table.update_item.assert_called_with(
            Key={'id': 'abc123'},
            UpdateExpression='SET end_at = :end_at, keyword = :keyword',
            ExpressionAttributeValues={':end_at': '2026-01-01T00:00:00Z', ':keyword': 'kw2'}
        )