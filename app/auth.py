from __future__ import annotations

import hmac
from typing import Mapping


def mask_secret(value: str | None, keep: int = 4) -> str | None:
    if value is None:
        return None
    if len(value) <= keep:
        return "***"
    return value[:keep] + "...***"


def extract_bearer_token(headers: Mapping[str, str]) -> str | None:
    for key, value in headers.items():
        if key.lower() == "authorization":
            parts = value.strip().split(None, 1)
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
    return None


def is_authorized(expected_token: str, query_token: str | None = None, headers: Mapping[str, str] | None = None) -> bool:
    if not expected_token:
        return True
    candidates = []
    if query_token:
        candidates.append(query_token)
    if headers:
        bearer = extract_bearer_token(headers)
        if bearer:
            candidates.append(bearer)
    return any(hmac.compare_digest(expected_token, candidate) for candidate in candidates)
