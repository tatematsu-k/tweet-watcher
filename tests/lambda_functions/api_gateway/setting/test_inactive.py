import pytest
from lambda_functions.api_gateway.setting import inactive as inact_mod

class DummyIntegration:
    def build_response(self, message):
        return message

@pytest.fixture
def integration():
    return DummyIntegration()

def test_inactive_setting_success(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {"Item": {}}
        def update_publication_status_inactive_by_id(self, id):
            pass
    monkeypatch.setattr(inact_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = inact_mod.deactivate_setting(args, integration)
    assert "非アクティブにしました" in resp

def test_inactive_setting_param_error(monkeypatch, integration):
    class DummyRepo:
        pass
    monkeypatch.setattr(inact_mod, "SettingsRepository", lambda: DummyRepo())
    args = []
    resp = inact_mod.deactivate_setting(args, integration)
    assert "パラメータ数が正しくありません" in resp

def test_inactive_setting_not_found(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {}
    monkeypatch.setattr(inact_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = inact_mod.deactivate_setting(args, integration)
    assert "該当設定がありません" in resp

def test_inactive_setting_exception(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            raise Exception("fail")
    monkeypatch.setattr(inact_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = inact_mod.deactivate_setting(args, integration)
    assert "エラー" in resp