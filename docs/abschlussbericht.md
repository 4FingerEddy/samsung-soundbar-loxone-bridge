# Abschlussbericht

## Power-Status

- `powerControl` ohne `power`-Parameter: pass
- Mapping `powerOn -> on -> 1`: pass per Unit-Test
- Mapping `powerOff -> off -> 0`: pass per Unit-Test und Live-Probe
- Mapping `None/unknown -> unknown -> -1`: pass per Unit-Test
- Timeout/unreachable -> `unknown/-1`: pass per Unit-Test
- Loxone `power_state` lesbar: pass per `/api/v1/status`, `/api/v1/power/state`, `/api/v1/power/state.txt` Unit-/Route-Test

## Rohantwort Samsung

Live-Probe gegen lokalen Samsung IP-Control-Endpoint auf TCP 1516, Token redaktiert:

```json
{
  "jsonrpc": "2.0",
  "id": "10",
  "result": {
    "power": "powerOff"
  }
}
```

## Bewertung

- Lokal zuverlässig verfügbar: ja, im getesteten Zustand erreichbar und auswertbar
- Einschränkung bei Standby: möglich; Timeout/unreachable wird bewusst nicht als `off` interpretiert
- Empfohlener Loxone-Wert: `power_state`

## Mapping

- `powerOn` -> `on` -> `1`
- `powerOff` -> `off` -> `0`
- `null`, anderes Schema oder unbekannter Rohwert -> `unknown` -> `-1`
- Timeout/unreachable -> `unknown` -> `-1`, plus Fehlerobjekt
