# Samsung Soundbar Loxone Bridge

A small local FastAPI bridge for controlling a Samsung Soundbar from Loxone Virtual HTTP Inputs/Outputs.

```text
Loxone Miniserver → Bridge HTTP API → Samsung Soundbar local JSON-RPC/IP-control API
```

The project is intentionally narrow: local LAN bridge, Docker-friendly deployment, simple HTTP endpoints for Loxone, and no cloud dependency for normal control.

## Status

- Verified target family: Samsung HW-Q935GF / Q930F style local IP-control API.
- Other Samsung models or firmware versions may need different sound-mode names or remote key codes.
- Power and some sound-mode actions are model-/firmware-dependent. They are included, but should be validated before automation.

## Security model

The bridge is intended for trusted local networks only.

- Do not expose it to the internet.
- Set a strong `BRIDGE_AUTH_TOKEN`.
- For non-loopback binding, the app refuses to start without a bridge token.
- Loxone usually needs query-token URLs; treat that token as local and rotatable.
- The Samsung AccessToken is generated and cached internally by the bridge. Users do not need to copy it into Loxone.

## Quickstart with Docker Compose

1. Copy the env example:

```bash
cp .env.example .env
```

2. Edit `.env`:

```text
SOUNDBAR_HOST=<your-soundbar-ip-or-dns>
BRIDGE_AUTH_TOKEN=<long-random-token>
```

You can generate a token locally with `deployment/token-generator.html`.

3. Start:

```bash
docker compose up -d --build
```

4. Check liveness:

```bash
curl http://127.0.0.1:8088/health
```

5. Check authenticated status only when the soundbar is reachable:

```bash
curl "http://127.0.0.1:8088/api/v1/loxone/status.txt?token=<your-bridge-token>"
```

The Loxone scalar status is backward-compatible and includes both the original values and power readback fields:

```text
ok=1
volume=7
muted=0
sound_mode_code=4
sound_mode_text=ADAPTIVE_PLUS
power_state=1
power=on
power_raw=powerOn
reachable=1
```

## Configuration

- `SOUNDBAR_HOST`: required; IP/DNS name of the soundbar.
- `SOUNDBAR_PORT`: default `1516`.
- `SOUNDBAR_SCHEME`: default `https`.
- `SOUNDBAR_VERIFY_SSL`: default `false`, because local Samsung endpoints commonly use self-signed certificates.
- `BRIDGE_HOST`: default `127.0.0.1` in app config; Docker examples bind `0.0.0.0` inside the container.
- `BRIDGE_PORT`: default `8088`.
- `BRIDGE_AUTH_TOKEN`: required for non-loopback deployments.
- `BRIDGE_AUTH_MODE`: `query_or_header`, `header_only`, or `query_only`.
- `DEBUG_ENDPOINTS`: default `false`; enable only temporarily.
- `SOUNDBAR_MODE_*`: override model-specific sound-mode strings.

## API endpoints

Unauthenticated:

- `GET /health`
- `GET /api/v1/health`

Authenticated:

- `GET /api/v1/ready`
- `GET /api/v1/status`
- `GET /api/v1/power/state`
- `GET /api/v1/power/state.txt`
- `GET /api/v1/loxone/status.txt`
- `GET|POST /api/v1/volume/up`
- `GET|POST /api/v1/volume/down`
- `GET|POST /api/v1/mute/toggle`
- `GET|POST /api/v1/woofer/up`
- `GET|POST /api/v1/woofer/down`
- `GET|POST /api/v1/source/earc`
- `GET|POST /api/v1/source/arc`
- `GET|POST /api/v1/source/hdmi1`
- `GET|POST /api/v1/source/hdmi2`
- `GET|POST /api/v1/source/din`
- `GET|POST /api/v1/source/bt`
- `GET|POST /api/v1/mode/standard`
- `GET|POST /api/v1/mode/surround`
- `GET|POST /api/v1/mode/game`
- `GET|POST /api/v1/mode/movie`
- `GET|POST /api/v1/mode/music`
- `GET|POST /api/v1/mode/clearvoice`
- `GET|POST /api/v1/mode/dtsvirtualx`
- `GET|POST /api/v1/mode/adaptive`
- `GET|POST /api/v1/power/on`
- `GET|POST /api/v1/power/off`

Debug endpoints are only registered when `DEBUG_ENDPOINTS=true`.

## Loxone

See `docs/loxone.md` and the XML templates in `deployment/templates/`.

## Portainer

See `deployment/GENERIC_PORTAINER_DEPLOYMENT.md` and `deployment/portainer-stack.image.yml`.

Host networking may be useful in some home-lab deployments, but it is not a universal best practice. Keep the bridge reachable only from the networks that need it.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## License

MIT. See `LICENSE`.
