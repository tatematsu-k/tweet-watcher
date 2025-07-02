import pytest
from unittest.mock import MagicMock, patch
from repositories.notifications_repository import NotificationsRepository

def test_exists_and_put():
    # boto3.resourceのモック
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = NotificationsRepository(table_name='TestTable')

        # exists: アイテムが存在する場合
        mock_table.get_item.return_value = {'Item': {'tweet_uid': '1', 'slack_ch': 'ch'}}
        assert repo.exists('1', 'ch') is True
        # exists: アイテムが存在しない場合
        mock_table.get_item.return_value = {}
        assert repo.exists('2', 'ch') is False

        # put: put_itemが呼ばれること
        repo.put('3', 'url', 'ch', '2025-01-01T00:00:00Z')
        mock_table.put_item.assert_called_with(Item={
            'tweet_uid': '3',
            'tweet_url': 'url',
            'slack_ch': 'ch',
            'notified_at': '2025-01-01T00:00:00Z'
        })
