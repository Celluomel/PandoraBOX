"""Evidence ledger for capabilities discovered through the Body.

This module does not claim that a declared actuator is a learned skill. It
keeps the distinction explicit:

    hypothesis -> observed -> verified

Evidence is structural (Body observations, affordances and action outcomes),
not a list of situations or phrases. The ledger is deliberately small and
local so it can later be replaced by a richer evaluator without changing the
Body/Brain boundary.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional


class BodyCapabilityLearner:
    """Persist and score capability evidence received from a Body."""

    def __init__(self, path: str | Path = "data/persona/body_capabilities.json") -> None:
        self._path = Path(path)
        self._lock = RLock()
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            value = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                value.setdefault("capabilities", {})
                value.setdefault("skills", {})
                value.setdefault("recent_signals", [])
                return value
        except Exception:
            pass
        return {"version": 1, "capabilities": {}, "skills": {}, "recent_signals": []}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self._path)

    @staticmethod
    def _stable(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)[:2000]

    @staticmethod
    def _capability_key(value: Any) -> str:
        return str(value or "unknown").strip().lower().replace(" ", "_")[:120]

    def observe(self, observation: Any) -> Optional[Dict[str, Any]]:
        """Record one BodyObservation and return a workspace signal if useful.

        The input is intentionally duck-typed so this stays independent from
        the transport (local adapter, WebSocket bridge, or future robot).
        """
        value = getattr(observation, "value", None)
        kind = str(getattr(observation, "kind", "") or "")
        provenance = getattr(observation, "provenance", {}) or {}
        candidates = []
        if isinstance(value, dict):
            candidates.extend({"name": key, "state": item} for key, item in (value.get("capabilities") or {}).items())
            candidates.extend({"name": key, "state": item} for key, item in (value.get("affordances") or {}).items())
            outcome = value.get("outcome")
            if isinstance(outcome, dict):
                candidates.append({"name": value.get("action") or value.get("target"), "outcome": outcome})
        if isinstance(provenance, dict):
            declared = provenance.get("capabilities") or provenance.get("affordances")
            if isinstance(declared, dict):
                candidates.extend({"name": key, "state": item} for key, item in declared.items())
        if kind == "actuation_feedback" and not candidates:
            candidates.append({"name": getattr(observation, "subject", "body_action"), "outcome": value})
        if not candidates:
            return None

        now = time.time()
        emitted = []
        with self._lock:
            for candidate in candidates:
                name = self._capability_key(candidate.get("name"))
                if name == "unknown":
                    continue
                outcome = candidate.get("outcome")
                success = None
                if isinstance(outcome, dict):
                    status = str(outcome.get("kind") or outcome.get("status") or "").lower()
                    success = status in {"success", "succeeded", "executed", "complete", "completed"}
                    if status in {"failure", "failed", "blocked", "danger"}:
                        success = False
                state = candidate.get("state")
                fingerprint = hashlib.sha256(self._stable({"name": name, "state": state, "outcome": outcome}).encode()).hexdigest()[:16]
                record = self._data["capabilities"].setdefault(name, {
                    "name": name, "state": "hypothesis", "confidence": 0.2,
                    "observations": 0, "successes": 0, "failures": 0,
                    "last_evidence": 0.0, "evidence": [],
                })
                if fingerprint in record.get("evidence", []):
                    continue
                record["evidence"] = (record.get("evidence", []) + [fingerprint])[-12:]
                record["observations"] += 1
                record["last_evidence"] = now
                if state is not None:
                    record["declared_or_observed_state"] = state
                if success is True:
                    record["successes"] += 1
                elif success is False:
                    record["failures"] += 1
                trials = record["successes"] + record["failures"]
                if record["successes"] >= 3 and record["successes"] > record["failures"] * 2:
                    record["state"] = "verified"
                elif record["observations"] >= 1:
                    record["state"] = "observed"
                record["confidence"] = round(min(1.0, max(0.0, 0.2 + 0.15 * record["observations"] + (0.1 * record["successes"]) - (0.12 * record["failures"]))), 3)
                if record["state"] == "verified":
                    skill_id = f"body.{name}"
                    trials = record["successes"] + record["failures"]
                    skill = self._data["skills"].setdefault(skill_id, {
                        "skill_id": skill_id,
                        "capability": name,
                        "state": "candidate",
                        "preconditions": [],
                        "limits": [],
                        "generalization": 0.0,
                        "created_at": now,
                    })
                    skill["state"] = "verified"
                    skill["confidence"] = record["confidence"]
                    skill["evidence_count"] = record["observations"]
                    skill["successes"] = record["successes"]
                    skill["failures"] = record["failures"]
                    skill["generalization"] = round(record["successes"] / max(1, trials), 3)
                    skill["last_verified"] = now
                    # These are deliberately evidence-derived constraints,
                    # not a hand-written list of situations.
                    skill["preconditions"] = [{"capability": name, "observed_state": record.get("declared_or_observed_state")}]
                    skill["limits"] = [{"failure_count": record["failures"]}] if record["failures"] else []
                emitted.append({"name": name, "state": record["state"], "confidence": record["confidence"], "successes": record["successes"], "failures": record["failures"]})
            if not emitted:
                return None
            self._data["recent_signals"] = (self._data.get("recent_signals", []) + [{"at": now, "items": emitted}])[-20:]
            self._save()
        return {"items": emitted, "observed_at": now}

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._data, ensure_ascii=False))

    def verified_skills(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {
                key: dict(value) for key, value in self._data.get("skills", {}).items()
                if value.get("state") == "verified"
            }
