import pytest
from lambda_functions.api_gateway.setting import list as list_mod

class DummyIntegration:
    def build_response(self, message):
        return message

@pytest.fixture
def integration():
    return DummyIntegration()

def test_list_setting_active(monkeypatch, integration):
    class DummyRepo:
        def list_valid_settings(self):
            return {"Items": [{"id": "id1", "keyword": "kw", "slack_ch": "#ch"}]}
    monkeypatch.setattr(list_mod, "SettingsRepository", lambda: DummyRepo())
    args = []
    resp = list_mod.get_setting(args, integration)
    assert "アクティブな設定一覧" in resp

def test_list_setting_all(monkeypatch, integration):
    class DummyRepo:
        def list_all(self):
            return {"Items": [{"id": "id1", "keyword": "kw", "slack_ch": "#ch", "publication_status": "active"}]}
    monkeypatch.setattr(list_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["-a"]
    resp = list_mod.get_setting(args, integration)
    assert "全設定一覧" in resp

def test_list_setting_param_error(monkeypatch, integration):
    class DummyRepo:
        pass
    monkeypatch.setattr(list_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["foo"]
    resp = list_mod.get_setting(args, integration)
    assert "パラメータが正しくありません" in resp

def test_list_setting_exception(monkeypatch, integration):
    class DummyRepo:
        def list_valid_settings(self):
            raise Exception("fail")
    monkeypatch.setattr(list_mod, "SettingsRepository", lambda: DummyRepo())
    args = []
    resp = list_mod.get_setting(args, integration)
    assert "エラー" in resp