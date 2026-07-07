# Changelog

## 0.1.0-dev — P1 Skeleton

- Projekt-Skeleton angelegt.
- Probe-Script erstellt.
- FastAPI Bridge-Skeleton erstellt.
- Unit-Tests für Config, Auth, Action-Mapping und Samsung-Client-Helfer erstellt.
- Keine Live-Kommandos gegen Soundbar oder Loxone ausgeführt.

## 0.1.0-dev — P4 Bridge Hardening

- `create_app(settings, client)` Factory für testbare FastAPI-App ergänzt.
- Routen auf dependency-injection-fähiges Router-Factory-Muster umgestellt.
- Status-Normalisierung ergänzt: `volume` wird Zahl, `muted` wird Boolean.
- Fake-Backend-Tests für `/health`, `/api/v1/status` und `/api/v1/volume/down` ergänzt.
- Verifiziert: `pytest -q` mit 13 Tests; `compileall` PASS.
- Keine echten Soundbar-Control-Kommandos, kein Docker/Portainer, keine Loxone-Änderung.

## 0.1.0-dev — Power Status

- `powerControl` ohne `power`-Parameter als read-only Statusabfrage ergänzt.
- `/api/v1/status` liefert `reachable`, `power`, `power_raw` und `power_state`.
- `/api/v1/power/state` und `/api/v1/power/state.txt` für Loxone-freundliche Auswertung ergänzt.
- Probe-Script testet standardmäßig `GET /`, `createAccessToken`, `getVolume`, `getMute` und `powerControl status`; Power-On/Off bleiben explizite Flags.
- Unit-Tests für Mapping `powerOn/powerOff/unknown/timeout` ergänzt.
- Live-Probe read-only: `powerControl status` lieferte `powerOff`, normalisiert zu `off` / `0`.
