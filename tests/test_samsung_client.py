from app.config import Settings
from app.samsung_client import SamsungSoundbarClient, extract_access_token, is_token_error, RpcResult


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
