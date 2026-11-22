"""Run Phase 0 prompts through a live Lumina HTTP chat and save evidence.

This is an opt-in diagnostic client, not a runtime phrase classifier. It saves
prompt/response pairs and redacted turn receipts so the baseline is reviewable.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests" / "baseline" / "phase0_cases.json"


def _get_receipt(client: httpx.Client, base_url: str, turn_id: str) -> dict[str, Any] | None:
    try:
        response = client.get(f"{base_url}/api/interface/cognitive-turns", timeout=8)
        response.raise_for_status()
        payload = response.json()
        for turn in payload.get("turns", []):
            if isinstance(turn, dict) and turn.get("turn_id") == turn_id:
                return turn
    except Exception:
        return None
    return None


def run_case(client: httpx.Client, base_url: str, case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    first_visible_ms = None
    answer: list[str] = []
    reasoning_chars = 0
    event_counts: Counter[str] = Counter()
    turn_id = ""
    terminal = "missing_terminal_event"
    http_status = 0
    with client.stream(
        "POST", f"{base_url}/api/interface/chat",
        json={"text": case["prompt"], "voice_mode": False},
        timeout=httpx.Timeout(180.0, connect=8.0),
    ) as response:
        http_status = response.status_code
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = str(event.get("type") or "unknown")
            event_counts[kind] += 1
            turn_id = turn_id or str(event.get("turn_id") or "")
            if kind == "delta":
                if first_visible_ms is None:
                    first_visible_ms = round((time.perf_counter() - started) * 1000, 2)
                answer.append(str(event.get("text") or ""))
            elif kind == "reasoning":
                reasoning_chars += len(str(event.get("text") or ""))
            elif kind in {"done", "error"}:
                terminal = kind
                break
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    receipt = _get_receipt(client, base_url, turn_id) if turn_id else None
    stages = {}
    pipeline = {}
    semantic = {}
    if receipt:
        pipeline = receipt.get("pipeline_integrity") or {}
        semantic = receipt.get("semantic_answer_validation") or {}
        stage_container = receipt.get("stages")
        if isinstance(stage_container, list) and stage_container:
            stage_container = stage_container[0]
        if isinstance(stage_container, dict):
            stages = {
                name: {
                    "status": value.get("status"),
                    "output_quality": value.get("output_quality"),
                    "consumes": value.get("consumes", []),
                }
                for name, value in stage_container.items()
                if isinstance(value, dict) and "status" in value
            }
    return {
        "case_id": case["id"],
        "class": case["class"],
        "language": case["language"],
        "prompt": case["prompt"],
        "http_status": http_status,
        "turn_id": turn_id or None,
        "terminal_event": terminal,
        "response": "".join(answer),
        "duration_ms": duration_ms,
        "time_to_first_visible_ms": first_visible_ms,
        "event_counts": dict(event_counts),
        "reasoning_chars_streamed": reasoning_chars,
        "reasoning_tokens_reported_by_chat_stream": None,
        "provider_call_log_file": "logs/llm_call_audit.jsonl",
        "pipeline_integrity": pipeline,
        "semantic_answer_validation": semantic,
        "stages": stages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--output", default="tests/baseline/phase0_2026-11-22.jsonl")
    parser.add_argument("--case", action="append", help="Run only this case ID; repeatable")
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N cases")
    args = parser.parse_args()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.case:
        wanted = set(args.case)
        cases = [case for case in cases if case.get("id") in wanted]
        unknown = wanted - {case.get("id") for case in cases}
        if unknown:
            parser.error("Unknown case IDs: " + ", ".join(sorted(unknown)))
    if args.limit > 0:
        cases = cases[:args.limit]
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    base_url = args.base_url.rstrip("/")
    with httpx.Client() as client, output.open("a", encoding="utf-8") as handle:
        status = client.get("http://127.0.0.1:8765/status", timeout=8).json()
        if not status.get("ready"):
            parser.error("Lumina Brain API is not ready")
        for index, case in enumerate(cases, 1):
            result = run_case(client, base_url, case)
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            print(json.dumps({
                "index": index, "total": len(cases), "case_id": case["id"],
                "turn_id": result["turn_id"], "terminal": result["terminal_event"],
                "duration_ms": result["duration_ms"], "ttft_ms": result["time_to_first_visible_ms"],
                "response_chars": len(result["response"]),
                "semantic_status": (result["semantic_answer_validation"] or {}).get("status"),
            }, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
