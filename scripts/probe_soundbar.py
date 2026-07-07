#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ProbeStep:
    name: str
    ok: bool
    http_status: int | None = None
    duration_ms: int | None = None
    data: Any = None
    error: str | None = None


def mask_token(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 4:
        return "***"
    return value[:4] + "...***"


def extract_token(data: dict[str, Any]) -> str | None:
    result = data.get("result")
    if isinstance(result, dict):
        return result.get("AccessToken") or result.get("accessToken")
    return data.get("AccessToken") or data.get("accessToken")


def normalize_power_status(data: dict[str, Any] | None) -> dict[str, Any]:
    raw: Any = None
    if isinstance(data, dict):
        payload = data.get("result", data)
        if isinstance(payload, dict):
            raw = payload.get("power")
        elif isinstance(payload, str):
            raw = payload
    if raw == "powerOn":
        return {"power": "on", "power_raw": raw, "power_state": 1}
    if raw == "powerOff":
        return {"power": "off", "power_raw": raw, "power_state": 0}
    return {"power": "unknown", "power_raw": raw, "power_state": -1}


def post_json(base_url: str, payload: dict[str, Any], timeout: float, insecure: bool) -> tuple[int, dict[str, Any] | None, int]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=body, headers={"Content-Type": "application/json", "Accept": "application/json"}, method="POST")
    context = ssl._create_unverified_context() if insecure else None
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw.strip() else {}
            return response.status, data, int((time.monotonic() - started) * 1000)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw.strip() else {"raw": raw}
        except json.JSONDecodeError:
            data = {"raw": raw}
        return exc.code, data, int((time.monotonic() - started) * 1000)


def run_probe(args: argparse.Namespace) -> list[ProbeStep]:
    base_url = f"{args.scheme}://{args.host}:{args.port}/"
    steps: list[ProbeStep] = []
    token: str | None = None

    if args.get_baseline:
        started = time.monotonic()
        try:
            context = ssl._create_unverified_context() if args.insecure else None
            with urllib.request.urlopen(base_url, timeout=args.timeout, context=context) as response:
                steps.append(ProbeStep("GET /", True, response.status, int((time.monotonic() - started) * 1000), {"server": response.headers.get("Server")}))
        except urllib.error.HTTPError as exc:
            # Expected for this Samsung endpoint: HTTP 400 on naked GET.
            steps.append(ProbeStep("GET /", exc.code == 400, exc.code, int((time.monotonic() - started) * 1000), {"server": exc.headers.get("Server")}))
        except Exception as exc:  # noqa: BLE001 - CLI probe should report all failures compactly
            steps.append(ProbeStep("GET /", False, None, int((time.monotonic() - started) * 1000), error=str(exc)))

    try:
        status, data, duration = post_json(base_url, {"jsonrpc": "2.0", "method": "createAccessToken", "id": 1}, args.timeout, args.insecure)
        token = extract_token(data or {})
        safe_data = dict(data or {})
        if token and isinstance(safe_data.get("result"), dict):
            if "AccessToken" in safe_data["result"]:
                safe_data["result"]["AccessToken"] = mask_token(token)
            if "accessToken" in safe_data["result"]:
                safe_data["result"]["accessToken"] = mask_token(token)
        steps.append(ProbeStep("createAccessToken", bool(token), status, duration, safe_data))
    except Exception as exc:  # noqa: BLE001
        steps.append(ProbeStep("createAccessToken", False, error=str(exc)))
        return steps

    for idx, method in enumerate(("getVolume", "getMute"), start=2):
        try:
            payload = {"jsonrpc": "2.0", "method": method, "id": idx, "params": {"AccessToken": token}}
            status, data, duration = post_json(base_url, payload, args.timeout, args.insecure)
            steps.append(ProbeStep(method, 200 <= status < 300, status, duration, data))
        except Exception as exc:  # noqa: BLE001
            steps.append(ProbeStep(method, False, error=str(exc)))

    try:
        payload = {"jsonrpc": "2.0", "method": "powerControl", "id": 10, "params": {"AccessToken": token}}
        status, data, duration = post_json(base_url, payload, args.timeout, args.insecure)
        normalized = normalize_power_status(data)
        steps.append(
            ProbeStep(
                "powerControl status",
                200 <= status < 300,
                status,
                duration,
                {"raw": data, "normalized": normalized},
            )
        )
    except Exception as exc:  # noqa: BLE001
        steps.append(ProbeStep("powerControl status", False, error=str(exc)))

    if args.test_volume_down:
        payload = {"jsonrpc": "2.0", "method": "remoteKeyControl", "id": 4, "params": {"AccessToken": token, "remoteKey": "VOL_DOWN"}}
        status, data, duration = post_json(base_url, payload, args.timeout, args.insecure)
        steps.append(ProbeStep("remoteKeyControl VOL_DOWN", 200 <= status < 300, status, duration, data))

    if args.test_power_off:
        payload = {"jsonrpc": "2.0", "method": "powerControl", "id": 11, "params": {"AccessToken": token, "power": "powerOff"}}
        status, data, duration = post_json(base_url, payload, args.timeout, args.insecure)
        steps.append(ProbeStep("powerControl powerOff", 200 <= status < 300, status, duration, data))

    if args.test_power_on:
        payload = {"jsonrpc": "2.0", "method": "powerControl", "id": 12, "params": {"AccessToken": token, "power": "powerOn"}}
        status, data, duration = post_json(base_url, payload, args.timeout, args.insecure)
        steps.append(ProbeStep("powerControl powerOn", 200 <= status < 300, status, duration, data))

    return steps


def steps_to_json(steps: list[ProbeStep]) -> dict[str, Any]:
    tests: dict[str, Any] = {}
    for step in steps:
        key = step.name.lower().replace(" /", "").replace(" ", "_").replace("/", "_")
        tests[key] = asdict(step)
    return {"ok": all(step.ok for step in steps if not step.name.startswith("remoteKeyControl")), "tests": tests}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Samsung Soundbar local IP-Control API. Control commands require explicit flags.")
    parser.add_argument("--host", required=True, help="Soundbar IP address or DNS name")
    parser.add_argument("--port", type=int, default=1516)
    parser.add_argument("--scheme", default="https")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification for local/self-signed Samsung endpoint")
    parser.add_argument("--get-baseline", action="store_true", default=True, help="Run naked GET / baseline; expected to return HTTP 400 on this API (default)")
    parser.add_argument("--skip-baseline", dest="get_baseline", action="store_false", help="Skip naked GET / baseline")
    parser.add_argument("--test-volume-down", action="store_true", help="Sends one real VOL_DOWN command. Requires separate operator approval.")
    parser.add_argument("--test-power-off", action="store_true", help="Sends one real powerOff command. Requires separate operator approval.")
    parser.add_argument("--test-power-on", action="store_true", help="Sends one real powerOn command. Requires separate operator approval.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    steps = run_probe(args)
    if args.json:
        print(json.dumps(steps_to_json(steps), indent=2, ensure_ascii=False))
    else:
        for step in steps:
            status = step.http_status if step.http_status is not None else "-"
            duration = f"{step.duration_ms}ms" if step.duration_ms is not None else "-"
            print(f"[{ 'PASS' if step.ok else 'FAIL' }] {step.name} status={status} duration={duration}")
            if step.error:
                print(f"  error: {step.error}")
            elif step.data is not None:
                print("  data:", json.dumps(step.data, ensure_ascii=False))
    return 0 if all(step.ok for step in steps if step.name != "remoteKeyControl VOL_DOWN") else 1


if __name__ == "__main__":
    sys.exit(main())
