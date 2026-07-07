from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
import ssl
from dataclasses import dataclass
from typing import Any

from .auth import mask_secret
from .config import Settings


class SamsungClientError(RuntimeError):
    def __init__(self, message: str, error_type: str = "samsung_client_error", retryable: bool = False):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


@dataclass
class RpcResult:
    ok: bool
    method: str
    status_code: int | None
    data: dict[str, Any] | None
    duration_ms: int


class SamsungSoundbarClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token: str | None = None
        self._next_id = 1
        self._lock = threading.Lock()
        self.last_success_at: float | None = None

    def build_payload(self, method: str, params: dict[str, Any] | None = None, include_token: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": self._next_id}
        self._next_id += 1
        merged = dict(params or {})
        if include_token:
            if not self._access_token:
                raise SamsungClientError("Access token missing", "token_missing", retryable=True)
            merged.setdefault("AccessToken", self._access_token)
        if merged:
            payload["params"] = merged
        return payload

    def redact_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        clone = json.loads(json.dumps(payload))
        params = clone.get("params")
        if isinstance(params, dict):
            for key in ("AccessToken", "accessToken"):
                if key in params:
                    params[key] = mask_secret(str(params[key]))
        return clone

    def _ssl_context(self):
        if self.settings.soundbar_verify_ssl:
            return None
        return ssl._create_unverified_context()

    def post_json(self, payload: dict[str, Any]) -> RpcResult:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.settings.soundbar_url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(
                req,
                timeout=self.settings.soundbar_timeout_seconds,
                context=self._ssl_context(),
            ) as response:
                raw = response.read().decode("utf-8", errors="replace")
                data = json.loads(raw) if raw.strip() else {}
                duration_ms = int((time.monotonic() - started) * 1000)
                self.last_success_at = time.time()
                return RpcResult(True, str(payload.get("method")), response.status, data, duration_ms)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            data = None
            try:
                data = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError:
                data = {"raw": raw}
            duration_ms = int((time.monotonic() - started) * 1000)
            return RpcResult(False, str(payload.get("method")), exc.code, data, duration_ms)
        except TimeoutError as exc:
            raise SamsungClientError(str(exc), "soundbar_timeout", retryable=True) from exc
        except OSError as exc:
            raise SamsungClientError(str(exc), "soundbar_unreachable", retryable=True) from exc

    def create_access_token(self) -> str:
        with self._lock:
            payload = {"jsonrpc": "2.0", "method": "createAccessToken", "id": self._next_id}
            self._next_id += 1
            result = self.post_json(payload)
            if not result.ok or not result.data:
                raise SamsungClientError("createAccessToken failed", "token_create_failed", retryable=True)
            token = extract_access_token(result.data)
            if not token:
                raise SamsungClientError("createAccessToken response did not contain a token", "token_missing_in_response", retryable=False)
            self._access_token = token
            return token

    def call(self, method: str, params: dict[str, Any] | None = None) -> RpcResult:
        with self._lock:
            if not self._access_token:
                # Avoid nested lock by doing the token payload inline.
                payload = {"jsonrpc": "2.0", "method": "createAccessToken", "id": self._next_id}
                self._next_id += 1
                token_result = self.post_json(payload)
                if not token_result.ok or not token_result.data:
                    raise SamsungClientError("createAccessToken failed", "token_create_failed", retryable=True)
                token = extract_access_token(token_result.data)
                if not token:
                    raise SamsungClientError("createAccessToken response did not contain a token", "token_missing_in_response", retryable=False)
                self._access_token = token
            payload = self.build_payload(method, params=params, include_token=True)
            result = self.post_json(payload)
            if is_token_error(result) and self.settings.soundbar_retry_on_token_error:
                self._access_token = None
                token_payload = {"jsonrpc": "2.0", "method": "createAccessToken", "id": self._next_id}
                self._next_id += 1
                token_result = self.post_json(token_payload)
                token = extract_access_token(token_result.data or {})
                if not token:
                    raise SamsungClientError("Access token rejected after retry", "token_error", retryable=True)
                self._access_token = token
                payload = self.build_payload(method, params=params, include_token=True)
                result = self.post_json(payload)
            return result


def extract_access_token(data: dict[str, Any]) -> str | None:
    result = data.get("result")
    if isinstance(result, dict):
        token = result.get("AccessToken") or result.get("accessToken")
        if token:
            return str(token)
    token = data.get("AccessToken") or data.get("accessToken")
    if token:
        return str(token)
    return None


def is_token_error(result: RpcResult) -> bool:
    if result.status_code in {401, 403}:
        return True
    data = result.data or {}
    err = data.get("error") if isinstance(data, dict) else None
    if isinstance(err, dict):
        message = str(err.get("message", "")).lower()
        code = str(err.get("code", "")).lower()
        return "token" in message or "auth" in message or code in {"401", "403"}
    return False
