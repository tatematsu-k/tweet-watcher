import pytest
from lambda_functions.api_gateway.setting import update as update_mod

class DummyIntegration:
    def build_response(self, message):
        return message

@pytest.fixture
def integration():
    return DummyIntegration()

def test_update_setting_success(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {"Item": {}}
        def update_keyword_by_id(self, id, new_keyword):
            pass
    monkeypatch.setattr(update_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "newkw"]
    resp = update_mod.update_setting(args, integration)
    assert "更新しました" in resp

def test_update_setting_param_error(monkeypatch, integration):
    class DummyRepo:
        pass
    monkeypatch.setattr(update_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = update_mod.update_setting(args, integration)
    assert "パラメータ数が正しくありません" in resp

def test_update_setting_not_found(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {}
    monkeypatch.setattr(update_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "newkw"]
    resp = update_mod.update_setting(args, integration)
    assert "該当設定がありません" in resp

def test_update_setting_exception(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            raise Exception("fail")
    monkeypatch.setattr(update_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "newkw"]
    resp = update_mod.update_setting(args, integration)
    assert "エラー" in resp
