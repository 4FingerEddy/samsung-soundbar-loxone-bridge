from app.config import Settings
from app.samsung_client import (
    RpcResult,
    SamsungClientError,
    SamsungSoundbarClient,
    extract_access_token,
    is_token_error,
    normalize_power_result,
)


def test_extract_access_token_variants():
    assert extract_access_token({"result": {"AccessToken": "ABC"}}) == "ABC"
    assert extract_access_token({"result": {"accessToken": "DEF"}}) == "DEF"


def test_build_payload_includes_token_and_redaction():
    client = SamsungSoundbarClient(Settings())
    client._access_token = "TOKEN123456"
    payload = client.build_payload("getVolume")
    assert payload["params"]["AccessToken"] == "TOKEN123456"
    redacted = client.redact_payload(payload)
    assert redacted["params"]["AccessToken"] == "TOKE...***"


def test_token_error_detection():
    assert is_token_error(RpcResult(False, "x", 401, None, 1))
    assert is_token_error(RpcResult(False, "x", 200, {"error": {"message": "bad token"}}, 1))


def test_normalize_power_result_maps_known_and_unknown_values():
    assert normalize_power_result({"jsonrpc": "2.0", "result": {"power": "powerOn"}}) == {
        "power": "on",
        "power_raw": "powerOn",
        "power_state": 1,
    }
    assert normalize_power_result({"result": {"power": "powerOff"}}) == {
        "power": "off",
        "power_raw": "powerOff",
        "power_state": 0,
    }
    assert normalize_power_result({"result": {"power": "standby"}}) == {
        "power": "unknown",
        "power_raw": "standby",
        "power_state": -1,
    }
    assert normalize_power_result({"result": {}}) == {
        "power": "unknown",
        "power_raw": None,
        "power_state": -1,
    }


def test_get_power_calls_power_control_without_power_parameter():
    class FakePowerClient(SamsungSoundbarClient):
        def __init__(self):
            super().__init__(Settings())
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params))
            return RpcResult(True, method, 200, {"result": {"power": "powerOn"}}, 5)

    client = FakePowerClient()

    assert client.get_power() == {"power": "on", "power_raw": "powerOn", "power_state": 1}
    assert client.calls == [("powerControl", None)]


def test_get_power_timeout_returns_unreachable_unknown_state():
    class TimeoutPowerClient(SamsungSoundbarClient):
        def call(self, method, params=None):
            raise SamsungClientError("Soundbar did not respond within timeout", "soundbar_timeout", retryable=True)

    assert TimeoutPowerClient(Settings()).get_power() == {
        "power": "unknown",
        "power_raw": None,
        "power_state": -1,
        "reachable": False,
        "ok": False,
        "error": {
            "type": "soundbar_timeout",
            "message": "Soundbar did not respond within timeout",
            "retryable": True,
        },
    }
