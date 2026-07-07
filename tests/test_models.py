from app.models import ACTIONS


def test_required_actions_exist():
    for name in ["volume.down", "volume.up", "mute.toggle", "source.earc", "mode.adaptive"]:
        assert name in ACTIONS


def test_volume_down_mapping_is_safe_first_control():
    spec = ACTIONS["volume.down"]
    assert spec.method == "remoteKeyControl"
    assert spec.params == {"remoteKey": "VOL_DOWN"}
