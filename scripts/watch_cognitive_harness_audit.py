"""Passively collect and compare Lumina cognitive-harness audit snapshots.

The watcher does not send chat turns or mutate cognitive state. It polls the
read-only /api/interface/cognitive-execution endpoint and appends compact,
redacted module/method/cycle evidence for later analysis.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:8080/api/interface/cognitive-execution"
DEFAULT_OUTPUT = ROOT / "logs" / "cognitive_harness_audit.jsonl"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def compact_snapshot(payload: dict[str, Any], endpoint: str) -> dict[str, Any]:
    """Keep only bounded, already-redacted audit fields from the API payload."""
    modules: dict[str, Any] = {}
    for name, raw in _mapping(payload.get("modules")).items():
        module = _mapping(raw)
        methods = {}
        for method_name, method_raw in _mapping(module.get("method_results")).items():
            method = _mapping(method_raw)
            methods[str(method_name)[:80]] = {
                key: method.get(key) for key in (
                    "tick_count", "error_count", "last_status", "last_error_type",
                    "last_tick_at", "last_duration_ms", "last_output",
                )
            }
        modules[str(name)[:100]] = {
            key: module.get(key) for key in (
                "tick_count", "skip_count", "error_count", "last_tick_at",
                "last_status", "last_error_type", "last_output", "state",
                "initialized", "observed_methods",
            )
        }
        modules[str(name)[:100]]["method_results"] = methods

    evidence = _mapping(payload.get("recent_cycle_evidence"))
    cycles = []
    raw_cycles = evidence.get("cycles")
    if isinstance(raw_cycles, list):
        for raw_cycle in raw_cycles[-5:]:
            cycle = _mapping(raw_cycle)
            stages = []
            raw_stages = cycle.get("stages")
            if isinstance(raw_stages, list):
                for raw_stage in raw_stages[-256:]:
                    stage = _mapping(raw_stage)
                    stages.append({
                        key: stage.get(key) for key in (
                            "stage", "status", "async_completion", "inputs",
                            "output_ref", "output_summary", "metrics", "error_type",
                        ) if key in stage
                    })
            cycles.append({
                key: cycle.get(key) for key in (
                    "cycle_id", "status", "started_at", "finished_at", "duration_ms",
                ) if key in cycle
            } | {"stages": stages})

    return {
        "schema": "lumina_cognitive_harness_audit_watch.v1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "available": bool(payload.get("available")),
        "loop_running": payload.get("loop_running"),
        "slow_cycle_count": payload.get("slow_cycle_count"),
        "module_tick_analysis": _mapping(payload.get("module_tick_analysis")),
        "modules": modules,
        "recent_cycle_evidence": {
            "retained": evidence.get("retained"),
            "cycles": cycles,
        },
        "interpretation_limit": payload.get("interpretation_limit"),
    }


def compare_snapshots(previous: dict[str, Any] | None,
                      current: dict[str, Any]) -> dict[str, Any]:
    """Report observed counter/output deltas, without inferring semantic quality."""
    old_modules = _mapping(previous.get("modules")) if previous else {}
    new_modules = _mapping(current.get("modules"))
    module_deltas: dict[str, Any] = {}
    for name, raw in new_modules.items():
        item = _mapping(raw)
        old = _mapping(old_modules.get(name))
        changes: dict[str, Any] = {}
        for field in ("tick_count", "skip_count", "error_count"):
            before, after = old.get(field, 0), item.get(field, 0)
            if isinstance(after, int) and isinstance(before, int):
                changes[field] = after - before
        method_deltas = {}
        old_methods = _mapping(old.get("method_results"))
        for method_name, method_raw in _mapping(item.get("method_results")).items():
            method = _mapping(method_raw)
            old_method = _mapping(old_methods.get(method_name))
            tick_delta = int(method.get("tick_count", 0) or 0) - int(old_method.get("tick_count", 0) or 0)
            error_delta = int(method.get("error_count", 0) or 0) - int(old_method.get("error_count", 0) or 0)
            if tick_delta or error_delta or not previous:
                method_deltas[method_name] = {
                    "tick_delta": tick_delta,
                    "error_delta": error_delta,
                    "last_status": method.get("last_status"),
                    "last_output_quality": _mapping(method.get("last_output")).get("quality"),
                }
        if any(changes.values()) or method_deltas or not previous:
            changes["methods"] = method_deltas
            changes["state"] = item.get("state")
            changes["last_output_quality"] = _mapping(item.get("last_output")).get("quality")
            module_deltas[name] = changes

    old_cycle = previous.get("slow_cycle_count") if previous else None
    new_cycle = current.get("slow_cycle_count")
    cycle_delta = (
        new_cycle - old_cycle
        if isinstance(new_cycle, int) and isinstance(old_cycle, int) else None
    )
    return {
        "cycle_delta": cycle_delta,
        "module_deltas": module_deltas,
        "new_errors": sum(max(0, data.get("error_count", 0)) for data in module_deltas.values()),
        "interpretation": "Execution and output-shape deltas only; semantic correctness requires scenario review.",
    }


def select_new_cycles(cycles: list[dict[str, Any]],
                      last_cycle_id: int | None) -> tuple[list[dict[str, Any]], int | None]:
    """Deduplicate retained cycle receipts and detect an in-process counter reset."""
    ids = [item.get("cycle_id") for item in cycles if isinstance(item.get("cycle_id"), int)]
    if not ids:
        return [], last_cycle_id
    if last_cycle_id is not None and max(ids) < last_cycle_id:
        last_cycle_id = None
    selected = [
        item for item in cycles
        if last_cycle_id is None or (
            isinstance(item.get("cycle_id"), int) and item["cycle_id"] > last_cycle_id
        )
    ]
    return selected, max(ids)


def fetch_snapshot(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"audit endpoint returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("audit endpoint returned a non-object JSON payload")
    return compact_snapshot(payload, url)


def run(url: str, output: Path, interval: float, timeout: float,
        once: bool = False) -> int:
    previous = None
    last_cycle_id: int | None = None
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"[cognitive-audit-watch] endpoint={url} output={output}", flush=True)
    while True:
        try:
            current = fetch_snapshot(url, timeout)
            delta = compare_snapshots(previous, current)
            cycles = current["recent_cycle_evidence"]["cycles"]
            new_cycles, newest_cycle_id = select_new_cycles(cycles, last_cycle_id)
            if last_cycle_id is not None and newest_cycle_id is not None and newest_cycle_id < last_cycle_id:
                # Lumina restarted and its in-memory cycle counter reset.
                previous = None
                delta = compare_snapshots(None, current)
            last_cycle_id = newest_cycle_id if newest_cycle_id is not None else last_cycle_id
            current["recent_cycle_evidence"]["cycles"] = new_cycles
            delta["cycle_receipt_count"] = len(new_cycles)
            delta["cycle_receipt_gap"] = max(
                0, (delta.get("cycle_delta") or 0) - len(new_cycles)
            )
            record = {"snapshot": current, "delta": delta}
            with output.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            analysis = current["module_tick_analysis"]
            print(
                "[cognitive-audit-watch] "
                f"cycle={current.get('slow_cycle_count')} "
                f"modules={analysis.get('executed_module_count')}/{analysis.get('module_count')} "
                f"ticks={analysis.get('total_ticks')} errors={analysis.get('total_errors')} "
                f"cycle_delta={delta['cycle_delta']} receipts={len(new_cycles)} "
                f"receipt_gap={delta['cycle_receipt_gap']} "
                f"changed_modules={len(delta['module_deltas'])}",
                flush=True,
            )
            previous = current
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
            print(f"[cognitive-audit-watch] endpoint unavailable: {type(exc).__name__}", file=sys.stderr, flush=True)
        if once:
            return 0 if previous is not None else 1
        time.sleep(max(2.0, interval))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--once", action="store_true", help="collect one snapshot then exit")
    args = parser.parse_args(argv)
    if args.interval <= 0 or args.timeout <= 0:
        parser.error("--interval and --timeout must be positive")
    try:
        return run(args.url, args.output, args.interval, args.timeout, args.once)
    except KeyboardInterrupt:
        print("\n[cognitive-audit-watch] stopped by operator", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
