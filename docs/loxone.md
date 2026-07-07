# Loxone Integration

This bridge is designed for a local Loxone setup where Loxone sends simple HTTP requests to the bridge and the bridge talks to the Samsung Soundbar local IP-control API.

```text
Loxone Miniserver → Samsung Soundbar Bridge → Samsung Soundbar local API
```

Do **not** configure Loxone to talk directly to the Samsung JSON-RPC endpoint. Loxone should call the bridge.

## Required placeholders

Replace these values locally in your Loxone configuration:

- `REPLACE_WITH_BRIDGE_IP_PORT`, for example `192.0.2.20:8088`
- `REPLACE_WITH_BRIDGE_AUTH_TOKEN`, generated locally for your bridge

Do not commit or share the real bridge token.

## Status input

Use a Virtual HTTP Input polling the bridge status endpoint:

```text
http://REPLACE_WITH_BRIDGE_IP_PORT/api/v1/loxone/status.txt?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
```

The plaintext response is shaped for Loxone parsing:

```text
ok=1
volume=7
muted=0
sound_mode_code=1
sound_mode_text=STANDARD
```

For JSON-capable integrations, `/api/v1/status` also exposes the power status fields:

```text
http://REPLACE_WITH_BRIDGE_IP_PORT/api/v1/status?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
```

Relevant fields:

- `ok`: bridge status request succeeded
- `reachable`: Samsung local API was reachable for the power read
- `power`: normalized value, one of `on`, `off`, `unknown`
- `power_raw`: raw Samsung value, for example `powerOn` or `powerOff`
- `power_state`: numeric value for automation logic

Recommended Loxone mapping:

- `power_state = 1`: Soundbar on
- `power_state = 0`: Soundbar off
- `power_state = -1`: unknown, unsupported response, timeout, or unreachable

Do not treat `-1` as off. Deep standby, Wi-Fi sleep, routing problems, and a real off state can look identical from the network side.

## Power status input

If JSON parsing is inconvenient in Loxone, use the dedicated numeric endpoint:

```text
http://REPLACE_WITH_BRIDGE_IP_PORT/api/v1/power/state?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
```

It returns JSON like:

```json
{"ok":true,"reachable":true,"power":"on","power_raw":"powerOn","power_state":1}
```

For a very small Virtual HTTP Input, use the plain-text variant:

```text
http://REPLACE_WITH_BRIDGE_IP_PORT/api/v1/power/state.txt?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
```

Response body:

```text
1
```

Mapping:

- `1` = on
- `0` = off
- `-1` = unknown/error

Recommended starting values:

- Poll interval: 60 seconds
- Timeout: 3000 ms
- Allowed timeouts: 3

## Control output

Use a Virtual Output with base address:

```text
http://REPLACE_WITH_BRIDGE_IP_PORT
```

Each command uses a relative path such as:

```text
/api/v1/volume/down?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
/api/v1/volume/up?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
/api/v1/mute/toggle?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
/api/v1/source/earc?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
/api/v1/mode/adaptive?token=REPLACE_WITH_BRIDGE_AUTH_TOKEN
```

The repository includes importable template files under `deployment/templates/`:

- `VI_RK_Samsung_Soundbar_Status.template.xml`
- `VO_RK_Samsung_Soundbar_Bridge.template.xml`

## Security note

Loxone Virtual HTTP commands commonly use query parameters. That means the bridge token may appear in Loxone configuration and in local logs. Treat `BRIDGE_AUTH_TOKEN` as a local, rotatable token and keep the bridge LAN-only.

## Experimental/model-verified endpoints

Power and some sound-mode commands may vary by Samsung model and firmware. They are kept in the public bridge because they were verified for the original target setup, but public users should validate them carefully on their own device before automation.
