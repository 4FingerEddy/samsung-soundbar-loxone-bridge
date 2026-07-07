from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ModeSettings(Protocol):
    soundbar_mode_standard: str
    soundbar_mode_surround: str
    soundbar_mode_game: str
    soundbar_mode_adaptive: str


@dataclass(frozen=True)
class ActionSpec:
    action: str
    method: str
    params: dict[str, Any]


ACTIONS: dict[str, ActionSpec] = {
    "volume.up": ActionSpec("volume.up", "remoteKeyControl", {"remoteKey": "VOL_UP"}),
    "volume.down": ActionSpec("volume.down", "remoteKeyControl", {"remoteKey": "VOL_DOWN"}),
    "mute.toggle": ActionSpec("mute.toggle", "remoteKeyControl", {"remoteKey": "MUTE"}),
    "woofer.up": ActionSpec("woofer.up", "remoteKeyControl", {"remoteKey": "WOOFER_PLUS"}),
    "woofer.down": ActionSpec("woofer.down", "remoteKeyControl", {"remoteKey": "WOOFER_MINUS"}),
    "source.earc": ActionSpec("source.earc", "inputSelectControl", {"inputSource": "E_ARC"}),
    "source.arc": ActionSpec("source.arc", "inputSelectControl", {"inputSource": "ARC"}),
    "source.hdmi1": ActionSpec("source.hdmi1", "inputSelectControl", {"inputSource": "HDMI_IN1"}),
    "source.hdmi2": ActionSpec("source.hdmi2", "inputSelectControl", {"inputSource": "HDMI_IN2"}),
    "source.din": ActionSpec("source.din", "inputSelectControl", {"inputSource": "D_IN"}),
    "source.bt": ActionSpec("source.bt", "inputSelectControl", {"inputSource": "BT"}),
    "mode.standard": ActionSpec("mode.standard", "soundModeControl", {"soundMode": "STANDARD"}),
    "mode.surround": ActionSpec("mode.surround", "soundModeControl", {"soundMode": "SURROUND"}),
    "mode.game": ActionSpec("mode.game", "soundModeControl", {"soundMode": "GAME"}),
    "mode.movie": ActionSpec("mode.movie", "soundModeControl", {"soundMode": "MOVIE"}),
    "mode.music": ActionSpec("mode.music", "soundModeControl", {"soundMode": "MUSIC"}),
    "mode.clearvoice": ActionSpec("mode.clearvoice", "soundModeControl", {"soundMode": "CLEARVOICE"}),
    "mode.dtsvirtualx": ActionSpec("mode.dtsvirtualx", "soundModeControl", {"soundMode": "DTS_VIRTUAL_X"}),
    "mode.adaptive": ActionSpec("mode.adaptive", "soundModeControl", {"soundMode": "ADAPTIVE"}),
    # Exact power values must be verified against the real device before production use.
    "power.on": ActionSpec("power.on", "powerControl", {"power": "powerOn"}),
    "power.off": ActionSpec("power.off", "powerControl", {"power": "powerOff"}),
}


def build_actions(settings: ModeSettings) -> dict[str, ActionSpec]:
    actions = dict(ACTIONS)
    actions.update(
        {
            "mode.standard": ActionSpec(
                "mode.standard", "soundModeControl", {"soundMode": settings.soundbar_mode_standard}
            ),
            "mode.surround": ActionSpec(
                "mode.surround", "soundModeControl", {"soundMode": settings.soundbar_mode_surround}
            ),
            "mode.game": ActionSpec("mode.game", "soundModeControl", {"soundMode": settings.soundbar_mode_game}),
            "mode.adaptive": ActionSpec(
                "mode.adaptive", "soundModeControl", {"soundMode": settings.soundbar_mode_adaptive}
            ),
        }
    )
    return actions
