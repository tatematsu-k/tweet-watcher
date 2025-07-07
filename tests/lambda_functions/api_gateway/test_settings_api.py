import os
import sys
import pytest
from moto import mock_dynamodb
import boto3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from repositories.settings_repository import SettingsRepository
from lambda_functions.api_gateway import settings_api
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
                {"AttributeName": "keyword", "AttributeType": "S"},
                {"AttributeName": "slack_ch", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "keyword-index",
                "KeySchema": [
                    {"AttributeName": "keyword", "KeyType": "HASH"},
                    {"AttributeName": "slack_ch", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }],
            BillingMode="PAY_PER_REQUEST"
        )
        os.environ["SETTINGS_TABLE"] = TABLE_NAME
        yield

# SettingsRepository CRUD
def test_put_and_get_by_id():
    repo = SettingsRepository(TABLE_NAME)
    id = repo.put("keyword1", "C12345")
    got = repo.get_by_id(id)
    assert got["Item"]["keyword"] == "keyword1"
    assert got["Item"]["slack_ch"] == "C12345"

def test_update_keyword_by_id():
    repo = SettingsRepository(TABLE_NAME)
    id = repo.put("k1", "C1")
    repo.update_keyword_by_id(id, "k2")
    got = repo.get_by_id(id)
    assert got["Item"]["keyword"] == "k2"

def test_delete_by_id():
    repo = SettingsRepository(TABLE_NAME)
    id = repo.put("k1", "C1")
    repo.delete_by_id(id)
    got = repo.get_by_id(id)
    assert "Item" not in got

def test_query_by_keyword():
    repo = SettingsRepository(TABLE_NAME)
    repo.put('k1', 'C1')
    repo.put('k1', 'C2')
    resp = repo.query_by_keyword("k1")
    items = resp.get("Items", [])
    assert len(items) == 2
    slack_chs = {item["slack_ch"] for item in items}
    assert slack_chs == {"C1", "C2"}

# settings_api lambda_handler (Slackコマンド形式)
def test_lambda_handler_create_read_update_delete():
    # create
    event = {"body": "text=setting+create+kw+CH"}
    resp = settings_api.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    assert "登録しました" in resp["body"]
    # read
    event = {"body": "text=setting+read+kw"}
    resp = settings_api.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    assert "設定一覧" in resp["body"]
    # update
    id = resp["body"].split("id: ")[-1].strip(")") if "id: " in resp["body"] else None
    if id:
        event = {"body": f"text=setting+update+{id}+kw2"}
        resp = settings_api.lambda_handler(event, None)
        assert resp["statusCode"] == 200
        assert "更新しました" in resp["body"]
        # delete
        event = {"body": f"text=setting+delete+{id}"}
        resp = settings_api.lambda_handler(event, None)
        assert resp["statusCode"] == 200
        assert "削除しました" in resp["body"]

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
    resp = slack.build_response("ok")
    assert resp["statusCode"] == 200
    assert resp["body"] == "ok"
