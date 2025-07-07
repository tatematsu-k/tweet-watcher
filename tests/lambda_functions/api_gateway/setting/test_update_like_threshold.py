import pytest
from lambda_functions.api_gateway.setting import update_like_threshold as ult_mod

class DummyIntegration:
    def build_response(self, message):
        return message

@pytest.fixture
def integration():
    return DummyIntegration()

def test_update_like_threshold_success(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {"Item": {}}
        def update_like_threshold_by_id(self, id, value):
            pass
    monkeypatch.setattr(ult_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "99"]
    resp = ult_mod.update_like_threshold(args, integration)
    assert "更新しました" in resp

def test_update_like_threshold_param_error(monkeypatch, integration):
    class DummyRepo:
        pass
    monkeypatch.setattr(ult_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = ult_mod.update_like_threshold(args, integration)
    assert "パラメータ数が正しくありません" in resp

def test_update_like_threshold_not_found(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {}
    monkeypatch.setattr(ult_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "99"]
    resp = ult_mod.update_like_threshold(args, integration)
    assert "該当設定がありません" in resp

def test_update_like_threshold_exception(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            raise Exception("fail")
    monkeypatch.setattr(ult_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1", "99"]
    resp = ult_mod.update_like_threshold(args, integration)
    assert "エラー" in resp