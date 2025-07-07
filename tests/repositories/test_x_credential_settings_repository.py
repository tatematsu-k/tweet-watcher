import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from repositories.x_credential_settings_repository import XCredentialSettingsRepository
from tests.mock.dynamodb import setup_dynamodb_all_tables
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

TABLE_NAME = "TweetWacherXCredentialSettingsTable"

@pytest.fixture(autouse=True)
def setup_dynamodb():
    with setup_dynamodb_all_tables():
        os.environ["X_CREDENTIAL_SETTINGS_TABLE"] = TABLE_NAME
        yield

def test_list_all():
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = XCredentialSettingsRepository(table_name="TestTable")
        repo.list_all()
        mock_table.scan.assert_called_with()


def test_update_latelimit_reset_time():
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = XCredentialSettingsRepository(table_name="TestTable")
        bearer_token = "token123"
        latelimit_reset_time = 1710000000  # epoch秒
        iso8601_time = (
            datetime.fromtimestamp(latelimit_reset_time, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        repo.update_latelimit_reset_time(bearer_token, latelimit_reset_time)
        mock_table.update_item.assert_called_with(
            Key={"bearer_token": bearer_token},
            UpdateExpression="SET latelimit_reset_time = :latelimit_reset_time",
            ExpressionAttributeValues={":latelimit_reset_time": iso8601_time},
        )


def test_get_available_credential():
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        repo = XCredentialSettingsRepository(table_name="TestTable")
        now = datetime.now(timezone.utc)
        # latelimit_reset_timeがNone
        mock_table.scan.return_value = {
            "Items": [{"bearer_token": "a", "latelimit_reset_time": None}]
        }
        assert repo.get_available_credential()["bearer_token"] == "a"
        # latelimit_reset_timeが過去
        past = (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        mock_table.scan.return_value = {
            "Items": [{"bearer_token": "b", "latelimit_reset_time": past}]
        }
        assert repo.get_available_credential()["bearer_token"] == "b"
        # latelimit_reset_timeが未来
        future = (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        mock_table.scan.return_value = {
            "Items": [{"bearer_token": "c", "latelimit_reset_time": future}]
        }
        assert repo.get_available_credential() is None
        # latelimit_reset_timeが不正な値
        mock_table.scan.return_value = {
            "Items": [{"bearer_token": "d", "latelimit_reset_time": "invalid"}]
        }
        assert repo.get_available_credential() is None
