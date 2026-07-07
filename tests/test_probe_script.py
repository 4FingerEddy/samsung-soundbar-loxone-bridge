import importlib.util
from pathlib import Path


def load_probe_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "probe_soundbar.py"
    spec = importlib.util.spec_from_file_location("probe_soundbar", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_extracts_and_masks_token():
    probe = load_probe_module()
    assert probe.extract_token({"result": {"AccessToken": "ABCDEF"}}) == "ABCDEF"
    assert probe.extract_token({"result": {"accessToken": "XYZ"}}) == "XYZ"
    assert probe.mask_token("ABCDEF") == "ABCD...***"


def test_probe_normalizes_power_status():
    probe = load_probe_module()

    assert probe.normalize_power_status({"result": {"power": "powerOn"}}) == {
        "power": "on",
        "power_raw": "powerOn",
        "power_state": 1,
    }
    assert probe.normalize_power_status({"result": {"power": "powerOff"}}) == {
        "power": "off",
        "power_raw": "powerOff",
        "power_state": 0,
    }
    assert probe.normalize_power_status({"result": {"power": "standby"}}) == {
        "power": "unknown",
        "power_raw": "standby",
        "power_state": -1,
    }
