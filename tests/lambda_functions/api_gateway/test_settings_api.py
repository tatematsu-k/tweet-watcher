import os
import sys
import pytest
from unittest.mock import patch
from moto import mock_dynamodb
import boto3

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)
from repositories.settings_repository import SettingsRepository
from lambda_functions.api_gateway import setting_api
from integration.integration_base import IntegrationBase
from integration.slack_integration import SlackIntegration

TABLE_NAME = "TweetWacherSettingsTable"


@pytest.fixture(autouse=True)
def setup_dynamodb():
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "publication_status", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "publication_status-index",
                    "KeySchema": [
                        {"AttributeName": "publication_status", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        os.environ["SETTINGS_TABLE"] = TABLE_NAME
        yield


# SettingsRepository CRUD
def test_put_and_get_by_id():
    repo = SettingsRepository(TABLE_NAME)
    result = repo.put("keyword1", "C12345")
    id = result["id"]
    got = repo.get_by_id(id)
    assert got["Item"]["keyword"] == "keyword1"
    assert got["Item"]["slack_ch"] == "C12345"


def test_update_keyword_by_id():
    repo = SettingsRepository(TABLE_NAME)
    result = repo.put("k1", "C1")
    id = result["id"]
    repo.update_keyword_by_id(id, "k2")
    got = repo.get_by_id(id)
    assert got["Item"]["keyword"] == "k2"


def test_delete_by_id():
    repo = SettingsRepository(TABLE_NAME)
    result = repo.put("k1", "C1")
    id = result["id"]
    repo.delete_by_id(id)
    got = repo.get_by_id(id)
    assert "Item" not in got


# IntegrationBase, SlackIntegration
class DummyIntegration(IntegrationBase):
    def parse_input(self, event):
        return event

    def build_response(self, message):
        return message


def test_integration_base_abstract():
    dummy = DummyIntegration()
    assert dummy.parse_input("x") == "x"
    assert dummy.build_response("y") == "y"


def test_slack_integration_methods():
    slack = SlackIntegration()
    event = {"body": "text=setting+help"}
    args = slack.parse_input(event)
    assert isinstance(args, list)
    resp = setting_api.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    assert "使い方" in resp["body"]
