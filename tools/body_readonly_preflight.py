#!/usr/bin/env python3
"""Read-only VENTUNO/Body HTTP preflight. NEVER sends actuator commands.

Usage:
  python tools/body_readonly_preflight.py --url http://ROBOT_IP:PORT --samples 5
  python tools/body_readonly_preflight.py --url http://ROBOT_IP:PORT --output preflight.json

Only GET /sensors is used. A passing result does NOT authorize actuation.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def validate_frame(payload: object, received_at: float, max_age: float = 5.0) -> dict:
    errors = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["sensor payload is not a JSON object"]}
    stamp = payload.get("timestamp")
    try:
        timestamp = float(stamp)
        if stamp is None or not math.isfinite(timestamp):
            raise ValueError("missing or nonfinite timestamp")
        age = received_at - timestamp
        if not (0.0 <= age <= max_age):
            errors.append("sensor timestamp is stale or future-dated")
    except (TypeError, ValueError, OverflowError):
        age = None
        errors.append("sensor timestamp missing or invalid")
    position = payload.get("position")
    if not isinstance(position, (list, tuple)) or len(position) < 3:
        errors.append("position must contain at least three coordinates")
    else:
        try:
            if not all(math.isfinite(float(v)) for v in position[:3]):
                errors.append("position contains nonfinite coordinates")
        except (TypeError, ValueError, OverflowError):
            errors.append("position contains invalid coordinates")
    try:
        orientation = float(payload["orientation"])
        if not math.isfinite(orientation):
            errors.append("orientation is nonfinite")
    except (KeyError, TypeError, ValueError, OverflowError):
        errors.append("orientation missing or invalid")
    objects = payload.get("objects")
    if objects is not None and not isinstance(objects, list):
        errors.append("objects must be a list")
    return {
        "valid": not errors,
        "errors": errors,
        "sensor_age_s": round(age, 3) if age is not None else None,
        "object_count": len(objects) if isinstance(objects, list) else None,
    }


def run(url: str, samples: int, timeout: float, token: str = "") -> dict:
    url = url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise ValueError("--url must use http:// or https://")
    if samples < 1 or samples > 100:
        raise ValueError("--samples must be 1..100")
    results = []
    for index in range(samples):
        started = time.time()
        request = Request(
            url + "/sensors",
            headers={"Accept": "application/json", **(
                {"Authorization": "Bearer " + token} if token else {}
            )},
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read(2_000_000).decode("utf-8"))
            received = time.time()
            check = validate_frame(payload, received)
            check.update({"sample": index + 1, "latency_ms": round((received - started) * 1000, 1)})
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            check = {"sample": index + 1, "valid": False,
                     "errors": [f"sensor GET failed: {type(exc).__name__}"],
                     "latency_ms": round((time.time() - started) * 1000, 1)}
        results.append(check)
    return {
        "mode": "read_only", "actuation_attempted": False,
        "samples": results, "passed": all(item["valid"] for item in results),
        "note": "Sensor readiness only; not motor, e-stop, latency-under-load, or physical safety certification.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Robot HTTP gateway base URL")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()
    try:
        report = run(args.url, args.samples, args.timeout, os.getenv("ROBOT_TOKEN", ""))
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
