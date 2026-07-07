from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.samsung_client import RpcResult, SamsungClientError


class FakeSoundbarClient:
    def __init__(self):
        self.calls: list[tuple[str, dict | None]] = []
        self.last_success_at = 1234567890.0

    def call(self, method: str, params: dict | None = None) -> RpcResult:
        self.calls.append((method, params))
        if method == "soundModeControl" and params is None:
            return RpcResult(True, method, 200, {"jsonrpc": "2.0", "result": {"soundMode": "SURROUND"}}, 10)
        if method == "getVolume":
            return RpcResult(True, method, 200, {"jsonrpc": "2.0", "result": {"volume": "7"}}, 11)
        if method == "getMute":
            return RpcResult(True, method, 200, {"jsonrpc": "2.0", "result": {"mute": False}}, 12)
        if method == "powerControl" and params is None:
            return RpcResult(True, method, 200, {"jsonrpc": "2.0", "result": {"power": "powerOn"}}, 9)
        return RpcResult(True, method, 200, {"jsonrpc": "2.0", "result": {"success": True}}, 13)


def test_status_normalizes_live_schema_to_plain_values():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    response = TestClient(app).get("/api/v1/status?token=secret")

    assert response.status_code == 200
    body = response.json()
    assert body["volume"] == 7
    assert body["muted"] is False
    assert body["reachable"] is True
    assert body["power"] == "on"
    assert body["power_raw"] == "powerOn"
    assert body["power_state"] == 1
    assert body["sound_mode"] == "SURROUND"
    assert body["sound_mode_raw"] == {"soundMode": "SURROUND"}
    assert body["sound_mode_readback_ok"] is True
    assert body["last_success_at"] == 1234567890.0
    assert fake.calls == [("powerControl", None), ("getVolume", None), ("getMute", None), ("soundModeControl", None)]


def test_power_state_endpoints_return_numeric_status_for_loxone():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    client = TestClient(app)

    response = client.get("/api/v1/power/state?token=secret")
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "reachable": True,
        "power": "on",
        "power_raw": "powerOn",
        "power_state": 1,
    }

    text = client.get("/api/v1/power/state.txt?token=secret")
    assert text.status_code == 200
    assert text.headers["content-type"].startswith("text/plain")
    assert text.text == "1\n"
    assert fake.calls == [("powerControl", None), ("powerControl", None)]


def test_status_keeps_other_values_when_power_status_times_out():
    class PowerTimeoutClient(FakeSoundbarClient):
        def call(self, method: str, params: dict | None = None) -> RpcResult:
            if method == "powerControl" and params is None:
                self.calls.append((method, params))
                raise SamsungClientError("Soundbar did not respond within timeout", "soundbar_timeout", retryable=True)
            return super().call(method, params)

    fake = PowerTimeoutClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    response = TestClient(app).get("/api/v1/status?token=secret")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["reachable"] is False
    assert body["power"] == "unknown"
    assert body["power_raw"] is None
    assert body["power_state"] == -1
    assert body["power_error"]["type"] == "soundbar_timeout"
    assert body["volume"] == 7
    assert body["muted"] is False


def test_status_returns_normalized_body_when_soundbar_unreachable():
    class UnreachableClient(FakeSoundbarClient):
        def call(self, method: str, params: dict | None = None) -> RpcResult:
            self.calls.append((method, params))
            raise SamsungClientError("connection refused", "soundbar_unreachable", retryable=True)

    fake = UnreachableClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    response = TestClient(app).get("/api/v1/status?token=secret")

    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "backend": "local-jsonrpc",
        "reachable": False,
        "power": "unknown",
        "power_raw": None,
        "power_state": -1,
        "error": {"type": "soundbar_unreachable", "message": "connection refused", "retryable": True},
    }


def test_loxone_scalar_status_endpoint_returns_numeric_text_values():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    client = TestClient(app)

    assert client.get("/api/v1/loxone/status.txt").status_code == 401
    response = client.get("/api/v1/loxone/status.txt?token=secret")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == (
        "ok=1\n"
        "volume=7\n"
        "muted=0\n"
        "sound_mode_code=2\n"
        "sound_mode_text=SURROUND\n"
        "power_state=1\n"
        "power=on\n"
        "power_raw=powerOn\n"
        "reachable=1\n"
    )
    assert fake.calls == [("powerControl", None), ("getVolume", None), ("getMute", None), ("soundModeControl", None)]


def test_loxone_scalar_status_keeps_volume_when_power_status_times_out():
    class PowerTimeoutClient(FakeSoundbarClient):
        def call(self, method: str, params: dict | None = None) -> RpcResult:
            if method == "powerControl" and params is None:
                self.calls.append((method, params))
                raise SamsungClientError("Soundbar did not respond within timeout", "soundbar_timeout", retryable=True)
            return super().call(method, params)

    fake = PowerTimeoutClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    response = TestClient(app).get("/api/v1/loxone/status.txt?token=secret")

    assert response.status_code == 200
    assert "volume=7\n" in response.text
    assert "power_state=-1\n" in response.text
    assert "power=unknown\n" in response.text
    assert "power_raw=\n" in response.text
    assert "reachable=0\n" in response.text
    assert fake.calls == [("powerControl", None), ("getVolume", None), ("getMute", None), ("soundModeControl", None)]



def test_action_endpoint_uses_fake_backend_and_requires_auth():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret"), client=fake)
    client = TestClient(app)

    assert client.get("/api/v1/volume/down").status_code == 401
    response = client.get("/api/v1/volume/down?token=secret")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["action"] == "volume.down"
    assert fake.calls == [("remoteKeyControl", {"remoteKey": "VOL_DOWN"})]


def test_mode_endpoint_uses_env_mapping_and_returns_readback():
    fake = FakeSoundbarClient()
    settings = Settings(bridge_auth_token="secret", soundbar_mode_game="GAME_PRO")
    app = create_app(settings=settings, client=fake)
    response = TestClient(app).get("/api/v1/mode/game?token=secret")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["action"] == "mode.game"
    assert body["sent_sound_mode"] == "GAME_PRO"
    assert body["readback_sound_mode"] == "SURROUND"
    assert body["readback_raw"] == {"soundMode": "SURROUND"}
    assert body["readback_ok"] is True
    assert fake.calls == [
        ("soundModeControl", {"soundMode": "GAME_PRO"}),
        ("soundModeControl", None),
    ]


def test_debug_soundmode_raw_requires_debug_flag():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret", debug_endpoints=False), client=fake)
    response = TestClient(app).get("/api/v1/debug/soundmode/raw?token=secret")

    assert response.status_code == 404
    assert fake.calls == []


def test_debug_soundmode_raw_returns_readback_when_enabled():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret", debug_endpoints=True), client=fake)
    response = TestClient(app).get("/api/v1/debug/soundmode/raw?token=secret")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["debug"] is True
    assert body["method"] == "soundModeControl"
    assert body["sound_mode"] == "SURROUND"
    assert body["result"] == {"jsonrpc": "2.0", "result": {"soundMode": "SURROUND"}}
    assert fake.calls == [("soundModeControl", None)]


def test_debug_soundmode_set_validates_mode_and_sends_candidate_when_enabled():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret", debug_endpoints=True), client=fake)
    client = TestClient(app)

    invalid = client.get("/api/v1/debug/soundmode/set/not-valid?token=secret")
    assert invalid.status_code == 400
    assert fake.calls == []

    response = client.get("/api/v1/debug/soundmode/set/GAME_PRO?token=secret")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["debug"] is True
    assert body["method"] == "soundModeControl"
    assert body["sent_sound_mode"] == "GAME_PRO"
    assert body["result"] == {"jsonrpc": "2.0", "result": {"success": True}}
    assert fake.calls == [("soundModeControl", {"soundMode": "GAME_PRO"})]


def test_health_does_not_touch_backend_or_expose_soundbar_address():
    fake = FakeSoundbarClient()
    app = create_app(settings=Settings(bridge_auth_token="secret", soundbar_host="192.0.2.10"), client=fake)
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "soundbar_host" not in body
    assert "soundbar_port" not in body
    assert fake.calls == []


def test_header_only_auth_mode_rejects_query_token_and_accepts_bearer_header():
    fake = FakeSoundbarClient()
    settings = Settings(bridge_auth_token="secret", bridge_auth_mode="header_only")
    app = create_app(settings=settings, client=fake)
    client = TestClient(app)

    assert client.get("/api/v1/volume/down?token=secret").status_code == 401

    response = client.get("/api/v1/volume/down", headers={"Authorization": "Bearer secret"})
    assert response.status_code == 200
    assert fake.calls == [("remoteKeyControl", {"remoteKey": "VOL_DOWN"})]
