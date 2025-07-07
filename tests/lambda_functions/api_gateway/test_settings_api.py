import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)
from repositories.settings_repository import SettingsRepository
from lambda_functions.api_gateway import setting_api
from integration.integration_base import IntegrationBase
from integration.slack_integration import SlackIntegration
from tests.mock.dynamodb import setup_dynamodb_all_tables

TABLE_NAME = "TweetWacherSettingsTable"


@pytest.fixture(autouse=True)
def setup_dynamodb():
    with setup_dynamodb_all_tables():
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
