import pytest
from lambda_functions.api_gateway.setting import delete as del_mod


class DummyIntegration:
    def build_response(self, message):
        return message


@pytest.fixture
def integration():
    return DummyIntegration()


def test_delete_setting_success(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {"Item": {}}

        def delete_by_id(self, id):
            pass

    monkeypatch.setattr(del_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = del_mod.delete_setting(args, integration)
    assert "削除しました" in resp


def test_delete_setting_param_error(monkeypatch, integration):
    class DummyRepo:
        pass

    monkeypatch.setattr(del_mod, "SettingsRepository", lambda: DummyRepo())
    args = []
    resp = del_mod.delete_setting(args, integration)
    assert "パラメータ数が正しくありません" in resp


def test_delete_setting_not_found(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            return {}

    monkeypatch.setattr(del_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = del_mod.delete_setting(args, integration)
    assert "該当設定がありません" in resp


def test_delete_setting_exception(monkeypatch, integration):
    class DummyRepo:
        def get_by_id(self, id):
            raise Exception("fail")

    monkeypatch.setattr(del_mod, "SettingsRepository", lambda: DummyRepo())
    args = ["id1"]
    resp = del_mod.delete_setting(args, integration)
    assert "エラー" in resp
