from __future__ import annotations

import os
from dataclasses import dataclass


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    soundbar_host: str = ""
    soundbar_port: int = 1516
    soundbar_scheme: str = "https"
    soundbar_verify_ssl: bool = False
    soundbar_timeout_seconds: float = 5.0
    soundbar_retry_on_token_error: bool = True
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 8088
    bridge_auth_token: str = ""
    bridge_auth_mode: str = "query_or_header"
    log_level: str = "INFO"
    log_json: bool = False
    debug_endpoints: bool = False
    soundbar_mode_standard: str = "STANDARD"
    soundbar_mode_surround: str = "SURROUND"
    soundbar_mode_game: str = "GAME"
    soundbar_mode_adaptive: str = "ADAPTIVE"

    @property
    def soundbar_url(self) -> str:
        return f"{self.soundbar_scheme}://{self.soundbar_host}:{self.soundbar_port}/"

    @property
    def auth_required(self) -> bool:
        return bool(self.bridge_auth_token)


def load_settings() -> Settings:
    return Settings(
        soundbar_host=os.getenv("SOUNDBAR_HOST", ""),
        soundbar_port=int(os.getenv("SOUNDBAR_PORT", "1516")),
        soundbar_scheme=os.getenv("SOUNDBAR_SCHEME", "https"),
        soundbar_verify_ssl=env_bool("SOUNDBAR_VERIFY_SSL", False),
        soundbar_timeout_seconds=float(os.getenv("SOUNDBAR_TIMEOUT_SECONDS", "5")),
        soundbar_retry_on_token_error=env_bool("SOUNDBAR_RETRY_ON_TOKEN_ERROR", True),
        bridge_host=os.getenv("BRIDGE_HOST", "127.0.0.1"),
        bridge_port=int(os.getenv("BRIDGE_PORT", "8088")),
        bridge_auth_token=os.getenv("BRIDGE_AUTH_TOKEN", ""),
        bridge_auth_mode=os.getenv("BRIDGE_AUTH_MODE", "query_or_header"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_json=env_bool("LOG_JSON", False),
        debug_endpoints=env_bool("DEBUG_ENDPOINTS", False),
        soundbar_mode_standard=os.getenv("SOUNDBAR_MODE_STANDARD", "STANDARD"),
        soundbar_mode_surround=os.getenv("SOUNDBAR_MODE_SURROUND", "SURROUND"),
        soundbar_mode_game=os.getenv("SOUNDBAR_MODE_GAME", "GAME"),
        soundbar_mode_adaptive=os.getenv("SOUNDBAR_MODE_ADAPTIVE", "ADAPTIVE"),
    )


def assert_secure_binding(settings: Settings) -> None:
    allowed_auth_modes = {"query_or_header", "header_only", "query_only"}
    if settings.bridge_auth_mode not in allowed_auth_modes:
        raise RuntimeError(
            f"Invalid BRIDGE_AUTH_MODE {settings.bridge_auth_mode!r}. "
            f"Allowed values: {', '.join(sorted(allowed_auth_modes))}."
        )

    loopback_hosts = {"127.0.0.1", "::1", "localhost"}
    if not settings.bridge_auth_token and settings.bridge_host not in loopback_hosts:
        raise RuntimeError(
            "Refusing to start: BRIDGE_AUTH_TOKEN is empty while BRIDGE_HOST is "
            f"{settings.bridge_host!r}. Set a token or bind to loopback."
        )
