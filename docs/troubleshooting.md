# Troubleshooting

## `/health` geht, `/api/v1/ready` nicht

Bridge läuft, aber Soundbar ist nicht erreichbar oder API antwortet nicht. Prüfen: IP, VLAN/Routing, Soundbar Standby, IP Control in SmartThings.

## TLS-Fehler

Samsung lokaler Endpoint nutzt ein nicht vertrauenswürdiges Zertifikat. Für LAN-Betrieb ist `SOUNDBAR_VERIFY_SSL=false` vorgesehen.

## Tokenfehler

Bridge verwirft Token und versucht genau einmal Re-Auth. Tokens dürfen nie im Klartext geloggt werden.

## Power status returns `power_state = -1`, but `/health` works

Likely causes:

- Soundbar is unreachable from the bridge.
- Soundbar is in deep standby or Wi-Fi sleep.
- `powerControl` status is unsupported or returns a different schema.

What to do:

- Check `/api/v1/ready` with a valid token.
- Run `scripts/probe_soundbar.py --host <SOUNDBAR_IP> --port 1516 --insecure`.
- Do not map timeout/unreachable to `off`; keep it as `unknown`/`-1`.

## `power = unknown`, but `reachable = true`

The Samsung API responded, but not with the expected `powerOn` or `powerOff` value. Keep and document `power_raw`, then extend the mapping only after verifying the raw response on the target model/firmware.

## Timeout bei Power-Status

Nicht als `off` werten. Tiefer Standby, schlafendes WLAN, VLAN/Routing und echte Off-Zustände können von außen gleich aussehen. Wake/CEC, Netzwerkpfad und Soundbar-Standby-Verhalten prüfen.

## Loxone sieht Power-Status nicht

Prüfen:

- URL exakt: `/api/v1/status`, `/api/v1/power/state`, oder `/api/v1/power/state.txt`
- Token-Platzhalter ersetzt
- JSON-Pfad bzw. Text-Parsing korrekt
- Direkter Browser/curl-Test gegen die Bridge funktioniert

## Source eARC geht nicht

Alternative Keys testen: `ARC`, `D_IN`. Ergebnisse dokumentieren.
