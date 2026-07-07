# Troubleshooting

## `/health` geht, `/api/v1/ready` nicht

Bridge läuft, aber Soundbar ist nicht erreichbar oder API antwortet nicht. Prüfen: IP, VLAN/Routing, Soundbar Standby, IP Control in SmartThings.

## TLS-Fehler

Samsung lokaler Endpoint nutzt ein nicht vertrauenswürdiges Zertifikat. Für LAN-Betrieb ist `SOUNDBAR_VERIFY_SSL=false` vorgesehen.

## Tokenfehler

Bridge verwirft Token und versucht genau einmal Re-Auth. Tokens dürfen nie im Klartext geloggt werden.

## Source eARC geht nicht

Alternative Keys testen: `ARC`, `D_IN`. Ergebnisse dokumentieren.
