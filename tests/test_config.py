import pytest

from app.config import Settings, assert_secure_binding, env_bool


def test_default_settings_are_local_only_and_do_not_include_private_soundbar_ip():
    settings = Settings()

    assert settings.bridge_host == "127.0.0.1"
    assert settings.soundbar_host == ""
    assert settings.soundbar_url == "https://:1516/"


def test_assert_secure_binding_rejects_empty_token_on_non_loopback():
    settings = Settings(bridge_host="0.0.0.0", bridge_auth_token="")

    with pytest.raises(RuntimeError, match="BRIDGE_AUTH_TOKEN is empty"):
        assert_secure_binding(settings)


def test_assert_secure_binding_allows_loopback_without_token():
    assert_secure_binding(Settings(bridge_host="127.0.0.1", bridge_auth_token=""))
    assert_secure_binding(Settings(bridge_host="localhost", bridge_auth_token=""))


def test_assert_secure_binding_allows_non_loopback_with_token():
    assert_secure_binding(Settings(bridge_host="0.0.0.0", bridge_auth_token="secret"))


def test_env_bool():
    assert env_bool("THIS_VAR_DOES_NOT_EXIST", True) is True
