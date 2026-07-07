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
