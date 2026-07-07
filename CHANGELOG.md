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
