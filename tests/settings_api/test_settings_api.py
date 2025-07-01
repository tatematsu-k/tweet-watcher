import os
import pytest
from moto import mock_dynamodb
import boto3

import settings_api.settings_api as sa

table_name = "SettingsTable"

@pytest.fixture(autouse=True)
def setup_dynamodb():
    with mock_dynamodb():
        # テーブル作成
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "keyword", "KeyType": "HASH"},
                {"AttributeName": "slack_ch", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "keyword", "AttributeType": "S"},
                {"AttributeName": "slack_ch", "AttributeType": "S"},
                {"AttributeName": "end_at", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        os.environ["SETTINGS_TABLE"] = table_name
        yield

def test_help_text():
    assert "使い方" in sa.help_text()

def test_create_and_read():
    # create
    res = sa.create_setting(["testkey", "#testch", "2025-01-01"])
    assert "登録しました" in res["body"]
    # duplicate
    res2 = sa.create_setting(["testkey", "#testch", "2025-01-01"])
    assert "既に登録済み" in res2["body"]
    # read
    res3 = sa.get_setting(["testkey"])
    assert "testkey" in res3["body"]
    assert "#testch" in res3["body"]

def test_update_and_delete():
    sa.create_setting(["testkey2", "#testch2", "2025-01-01"])
    # update
    res = sa.update_setting(["testkey2", "#testch2", "2026-01-01"])
    assert "更新しました" in res["body"]
    # delete
    res2 = sa.delete_setting(["testkey2", "#testch2"])
    assert "削除しました" in res2["body"]
    # delete not found
    res3 = sa.delete_setting(["testkey2", "#testch2"])
    assert "該当設定がありません" in res3["body"]
