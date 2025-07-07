import pytest
from lambda_functions.api_gateway.setting import create

class DummyIntegration:
    def build_response(self, message):
        return message

@pytest.fixture
def integration():
    return DummyIntegration()

def test_create_setting_success(monkeypatch, integration):
    class DummyRepo:
        def put(self, keyword, slack_ch, like_threshold, retweet_threshold):
            return {"id": "dummyid", "publication_status": "active"}
    monkeypatch.setattr(create, "SettingsRepository", lambda: DummyRepo())
    args = ["keyword", "#ch", "10", "5"]
    resp = create.create_setting(args, integration)
    assert "登録しました" in resp
    assert "like閾値: 10" in resp
    assert "retweet閾値: 5" in resp

def test_create_setting_param_error(integration):
    args = ["keyword"]
    resp = create.create_setting(args, integration)
    assert "パラメータ数が正しくありません" in resp

def test_create_setting_exception(monkeypatch, integration):
    class DummyRepo:
        def put(self, *a, **kw):
            raise Exception("fail")
    monkeypatch.setattr(create, "SettingsRepository", lambda: DummyRepo())
    args = ["keyword", "#ch"]
    resp = create.create_setting(args, integration)
    assert "エラー" in resp