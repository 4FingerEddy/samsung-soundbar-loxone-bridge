from __future__ import annotations

import re
import time
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from . import __version__
from .auth import is_authorized
from .config import Settings
from .models import build_actions
from .samsung_client import SamsungClientError, SamsungSoundbarClient


class SoundbarBackend(Protocol):
    last_success_at: float | None

    def call(self, method: str, params: dict[str, Any] | None = None): ...


def create_router(settings: Settings, client: SoundbarBackend) -> APIRouter:
    router = APIRouter()
    actions = build_actions(settings)

    def require_auth(request: Request, token: str | None = None, authorization: str | None = None) -> None:
        headers = dict(request.headers)
        if authorization:
            headers["authorization"] = authorization
        query_token = None if settings.bridge_auth_mode == "header_only" else token
        header_map = {} if settings.bridge_auth_mode == "query_only" else headers
        if not is_authorized(settings.bridge_auth_token, query_token=query_token, headers=header_map):
            raise HTTPException(status_code=401, detail="Unauthorized")

    @router.get("/health")
    @router.get("/api/v1/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "samsung-soundbar-bridge",
            "version": __version__,
            "backend": "local-jsonrpc",
        }

    @router.get("/api/v1/ready")
    def ready(request: Request, token: str | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_auth(request, token=token, authorization=authorization)
        try:
            result = client.call("getVolume")
            return {
                "ok": result.ok,
                "ready": result.ok,
                "local_api_reachable": result.status_code is not None,
                "token_available": True,
                "duration_ms": result.duration_ms,
            }
        except SamsungClientError as exc:
            raise bridge_error(exc) from exc

    @router.get("/api/v1/status")
    def status(request: Request, token: str | None = None, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_auth(request, token=token, authorization=authorization)
        out: dict[str, Any] = {
            "ok": True,
            "backend": "local-jsonrpc",
            "power": "unknown",
            "volume": None,
            "muted": None,
            "source": None,
            "sound_mode": None,
        }
        try:
            volume = client.call("getVolume")
            mute = client.call("getMute")
            out["volume"] = normalize_volume(volume.data)
            out["muted"] = normalize_mute(mute.data)
            try:
                sound_mode = client.call("soundModeControl")
                out["sound_mode"] = normalize_sound_mode(sound_mode.data)
                out["sound_mode_raw"] = result_payload(sound_mode.data)
                out["sound_mode_readback_ok"] = sound_mode.ok
            except SamsungClientError as exc:
                out["sound_mode_readback_ok"] = False
                out["sound_mode_error"] = {"type": exc.error_type, "message": str(exc), "retryable": exc.retryable}
            out["last_success_at"] = client.last_success_at
            return out
        except SamsungClientError as exc:
            raise bridge_error(exc) from exc

    @router.get("/api/v1/loxone/status.txt", response_class=PlainTextResponse)
    def loxone_status_txt(
        request: Request, token: str | None = None, authorization: str | None = Header(default=None)
    ) -> PlainTextResponse:
        require_auth(request, token=token, authorization=authorization)
        try:
            volume = client.call("getVolume")
            mute = client.call("getMute")
            sound_mode = client.call("soundModeControl")
            mode_text = normalize_sound_mode(sound_mode.data)
            body = loxone_status_text(
                normalize_volume(volume.data),
                normalize_mute(mute.data),
                sound_mode_code(mode_text),
                mode_text,
            )
            return PlainTextResponse(body)
        except SamsungClientError as exc:
            raise bridge_error(exc) from exc

    def action_response(action_name: str) -> dict[str, Any]:
        spec = actions[action_name]
        started = time.monotonic()
        try:
            result = client.call(spec.method, spec.params)
            duration_ms = result.duration_ms or int((time.monotonic() - started) * 1000)
            response = {
                "ok": result.ok,
                "action": spec.action,
                "backend": "local-jsonrpc",
                "duration_ms": duration_ms,
                "result": result.data,
            }
            if spec.method == "soundModeControl" and "soundMode" in spec.params:
                response["sent_sound_mode"] = spec.params["soundMode"]
                try:
                    readback = client.call("soundModeControl")
                    response["readback_sound_mode"] = normalize_sound_mode(readback.data)
                    response["readback_raw"] = result_payload(readback.data)
                    response["readback_ok"] = readback.ok
                except SamsungClientError as readback_exc:
                    response["readback_ok"] = False
                    response["readback_error"] = {
                        "type": readback_exc.error_type,
                        "message": str(readback_exc),
                        "retryable": readback_exc.retryable,
                    }
            return response
        except SamsungClientError as exc:
            raise bridge_error(exc) from exc

    def register(path: str, action_name: str) -> None:
        def endpoint(request: Request, token: str | None = None, authorization: str | None = Header(default=None)):
            require_auth(request, token=token, authorization=authorization)
            return action_response(action_name)

        endpoint.__name__ = "endpoint_" + action_name.replace(".", "_")
        router.add_api_route(path, endpoint, methods=["GET", "POST"])

    register("/api/v1/volume/up", "volume.up")
    register("/api/v1/volume/down", "volume.down")
    register("/api/v1/mute/toggle", "mute.toggle")
    register("/api/v1/woofer/up", "woofer.up")
    register("/api/v1/woofer/down", "woofer.down")
    register("/api/v1/source/earc", "source.earc")
    register("/api/v1/source/arc", "source.arc")
    register("/api/v1/source/hdmi1", "source.hdmi1")
    register("/api/v1/source/hdmi2", "source.hdmi2")
    register("/api/v1/source/din", "source.din")
    register("/api/v1/source/bt", "source.bt")
    register("/api/v1/mode/standard", "mode.standard")
    register("/api/v1/mode/surround", "mode.surround")
    register("/api/v1/mode/game", "mode.game")
    register("/api/v1/mode/movie", "mode.movie")
    register("/api/v1/mode/music", "mode.music")
    register("/api/v1/mode/clearvoice", "mode.clearvoice")
    register("/api/v1/mode/dtsvirtualx", "mode.dtsvirtualx")
    register("/api/v1/mode/adaptive", "mode.adaptive")
    register("/api/v1/power/on", "power.on")
    register("/api/v1/power/off", "power.off")

    if settings.debug_endpoints:
        @router.get("/api/v1/debug/soundmode/raw")
        def debug_soundmode_raw(
            request: Request, token: str | None = None, authorization: str | None = Header(default=None)
        ) -> dict[str, Any]:
            require_auth(request, token=token, authorization=authorization)
            try:
                result = client.call("soundModeControl")
                return {
                    "ok": result.ok,
                    "debug": True,
                    "method": "soundModeControl",
                    "sound_mode": normalize_sound_mode(result.data),
                    "result": result.data,
                    "duration_ms": result.duration_ms,
                }
            except SamsungClientError as exc:
                raise bridge_error(exc) from exc

        @router.get("/api/v1/debug/soundmode/set/{mode}")
        def debug_soundmode_set(
            mode: str,
            request: Request,
            token: str | None = None,
            authorization: str | None = Header(default=None),
        ) -> dict[str, Any]:
            require_auth(request, token=token, authorization=authorization)
            if not is_safe_sound_mode_candidate(mode):
                raise HTTPException(status_code=400, detail="Invalid sound mode candidate")
            try:
                result = client.call("soundModeControl", {"soundMode": mode})
                return {
                    "ok": result.ok,
                    "debug": True,
                    "method": "soundModeControl",
                    "sent_sound_mode": mode,
                    "result": result.data,
                    "duration_ms": result.duration_ms,
                }
            except SamsungClientError as exc:
                raise bridge_error(exc) from exc

    return router


def bridge_error(exc: SamsungClientError) -> HTTPException:
    return HTTPException(
        status_code=503 if exc.retryable else 502,
        detail={"type": exc.error_type, "message": str(exc), "retryable": exc.retryable},
    )


def result_payload(data: dict[str, Any] | None) -> Any:
    if not data:
        return None
    return data.get("result", data)


def normalize_volume(data: dict[str, Any] | None) -> int | float | None:
    payload = result_payload(data)
    if isinstance(payload, dict):
        value = payload.get("volume")
    else:
        value = payload
    return normalize_number(value)


def normalize_mute(data: dict[str, Any] | None) -> bool | None:
    payload = result_payload(data)
    if isinstance(payload, dict):
        value = payload.get("mute")
    else:
        value = payload
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "on", "yes"}:
            return True
        if lowered in {"false", "0", "off", "no"}:
            return False
    return None


def normalize_sound_mode(data: dict[str, Any] | None) -> str | None:
    payload = result_payload(data)
    if isinstance(payload, dict):
        for key in ("soundMode", "sound_mode", "mode", "currentSoundMode", "current_sound_mode"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(payload, str) and payload.strip():
        return payload.strip()
    return None


def is_safe_sound_mode_candidate(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9_+]{1,64}", value))


def normalize_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            try:
                return float(stripped)
            except ValueError:
                return None
    return None


SOUND_MODE_CODES: dict[str, int] = {
    "STANDARD": 1,
    "SURROUND": 2,
    "GAME": 3,
    "GAME_PRO": 3,
    "GAME_MODE_PRO": 3,
    "GAMEPRO": 3,
    "ADAPTIVE": 4,
    "ADAPTIVE_SOUND": 4,
    "ADAPTIVE_SOUND_PLUS": 4,
    "ADAPTIVE_PLUS": 4,
    "SMART": 4,
    "MOVIE": 5,
    "MUSIC": 6,
    "CLEARVOICE": 7,
    "DTS_VIRTUAL_X": 8,
}


def sound_mode_code(mode: str | None) -> int:
    if not mode:
        return 0
    return SOUND_MODE_CODES.get(mode.strip().upper(), 0)


def loxone_status_text(
    volume: int | float | None, muted: bool | None, mode_code: int = 0, mode_text: str | None = None
) -> str:
    ok = int(volume is not None and muted is not None)
    volume_value: int | float = volume if volume is not None else -1
    muted_value = 1 if muted is True else 0
    mode_value = (mode_text or "").replace("\r", " ").replace("\n", " ").strip()
    return (
        f"ok={ok}\n"
        f"volume={volume_value}\n"
        f"muted={muted_value}\n"
        f"sound_mode_code={mode_code}\n"
        f"sound_mode_text={mode_value}\n"
    )


def default_router() -> APIRouter:
    from .config import load_settings

    settings = load_settings()
    return create_router(settings, SamsungSoundbarClient(settings))
