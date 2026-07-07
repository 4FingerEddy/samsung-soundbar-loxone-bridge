from app.auth import extract_bearer_token, is_authorized, mask_secret


def test_mask_secret():
    assert mask_secret("abcdef") == "abcd...***"
    assert mask_secret("abc") == "***"


def test_bearer_and_query_auth():
    assert extract_bearer_token({"Authorization": "Bearer secret"}) == "secret"
    assert is_authorized("secret", query_token="secret")
    assert is_authorized("secret", headers={"Authorization": "Bearer secret"})
    assert not is_authorized("secret", query_token="wrong")
