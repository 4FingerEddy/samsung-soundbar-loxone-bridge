from pathlib import Path


def test_dockerfile_binds_uvicorn_from_bridge_host_and_port_env():
    dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")

    assert "--host \"${BRIDGE_HOST:-127.0.0.1}\"" in text
    assert "--port \"${BRIDGE_PORT:-8088}\"" in text
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"' not in text
