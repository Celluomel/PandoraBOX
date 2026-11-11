"""
MemoryBreadthAudit — Phase 6.6
================================
Compares retrieval widening against a later independently validated
outcome. It remains unmeasured until PredictiveMind provides outcome
labels in the same domain as its prediction. The former error signal
compared user-intent labels with response-register labels, so those
legacy samples are retained but excluded from evidence.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_PENDING = 200
REVIEW_DELAY_TURNS = 1   # compare against the very next prediction — this
                          # question is about immediate disambiguation, not
                          # a delayed outcome like a goal's actions_taken


class MemoryBreadthAudit:
    def __init__(self, path: str = "data/persona/memory_breadth_audit.json") -> None:
        self._path = Path(path)
        self._lock = Lock()
        self._pending: List[Dict[str, Any]] = []
        self._widened_deltas: List[float] = []
        self._baseline_deltas: List[float] = []
        self._legacy_unvalidated = {"pending": [], "widened": [], "baseline": []}
        self._turn_counter = 0
        self._load()
        logger.info("[MemoryBreadthAudit] initialised")

    def record_and_review(self, widened: bool, predictive_mind: Any) -> Dict[str, Any]:
        """
        Single entry point, called once per turn from persona_bridge.py
        right where the retrieval-widening decision is made. Combines
        record (this turn's decision) + review (checking any turn at
        least REVIEW_DELAY_TURNS old) so the caller doesn't need to
        thread a turn_id through — the counter here IS the turn clock.
        """
        report = {"reviewed": 0, "still_pending": 0, "status": "unmeasured"}
        if predictive_mind is None or not hasattr(predictive_mind, "summary"):
            return report
        try:
            pm_summary = predictive_mind.summary()
            validated_count = int(pm_summary.get("validated_predictions", 0) or 0)
            measurement_status = pm_summary.get("accuracy_status")
        except Exception:
            return report
        if validated_count <= 0 or measurement_status != "measured":
            # Do not treat absent outcome labels as zero error and do not
            # complete stale pending observations from the legacy metric.
            report["still_pending"] = len(self._pending)
            return report
        if not hasattr(predictive_mind, "recent_error_level"):
            return report
        current_error = predictive_mind.recent_error_level()
        if current_error is None:
            report["still_pending"] = len(self._pending)
            return report

        with self._lock:
            self._turn_counter += 1
            this_turn = self._turn_counter
            self._pending.append({
                "widened": widened,
                "pre_error_level": current_error,
                "turn_id": this_turn,
            })
            if len(self._pending) > MAX_PENDING:
                self._pending = self._pending[-MAX_PENDING:]

            due = [p for p in self._pending
                   if this_turn - p["turn_id"] >= REVIEW_DELAY_TURNS]
            still_pending = [p for p in self._pending if p not in due]

        for entry in due:
            report["reviewed"] += 1
            delta = entry["pre_error_level"] - current_error  # positive = improved
            if entry["widened"]:
                self._widened_deltas.append(delta)
                self._widened_deltas = self._widened_deltas[-100:]
            else:
                self._baseline_deltas.append(delta)
                self._baseline_deltas = self._baseline_deltas[-100:]

        with self._lock:
            self._pending = still_pending
            report["still_pending"] = len(still_pending)

        if report["reviewed"]:
            report["status"] = "measured"
            self._save()
        return report

    def summary(self) -> Dict[str, Any]:
        """
        Only samples collected with independent outcome labels are active.
        Old proxy-derived data is reported as excluded legacy metadata.
        """
        def _avg(xs: List[float]) -> Optional[float]:
            return round(sum(xs) / len(xs), 4) if xs else None

        widened_avg = _avg(self._widened_deltas)
        baseline_avg = _avg(self._baseline_deltas)
        gap = (
            round(widened_avg - baseline_avg, 4)
            if widened_avg is not None and baseline_avg is not None else None
        )
        return {
            "widened_samples": len(self._widened_deltas),
            "baseline_samples": len(self._baseline_deltas),
            "widened_avg_error_delta": widened_avg,
            "baseline_avg_error_delta": baseline_avg,
            "gap": gap,  # positive gap = widening correlates with more improvement
            "measurement_status": "measured" if self._widened_deltas or self._baseline_deltas else "unmeasured_no_independent_outcome_labels",
            "legacy_unvalidated_samples_excluded": {
                key: len(values) for key, values in self._legacy_unvalidated.items()
            },
        }

    # ── persistence ──────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "measurement_schema": "independent_outcome_v1",
                    "pending":          self._pending,
                    "widened_deltas":   self._widened_deltas,
                    "baseline_deltas":  self._baseline_deltas,
                    "legacy_unvalidated_excluded": self._legacy_unvalidated,
                }
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"[MemoryBreadthAudit] save failed (non-fatal): {e}")

    def _load(self) -> None:
        try:
            if not self._path.exists():
                return
            data = json.loads(self._path.read_text())
            with self._lock:
                if data.get("measurement_schema") == "independent_outcome_v1":
                    self._pending = data.get("pending", [])
                    self._widened_deltas = data.get("widened_deltas", [])
                    self._baseline_deltas = data.get("baseline_deltas", [])
                    self._legacy_unvalidated = data.get("legacy_unvalidated_excluded", self._legacy_unvalidated)
                else:
                    # Preserve old file contents, but do not present results
                    # gathered from the invalid proxy as evidence.
                    self._legacy_unvalidated = {
                        "pending": data.get("pending", []),
                        "widened": data.get("widened_deltas", []),
                        "baseline": data.get("baseline_deltas", []),
                    }
        except Exception as e:
            logger.warning(f"[MemoryBreadthAudit] load failed (non-fatal): {e}")


_audit: Optional[MemoryBreadthAudit] = None


def get_memory_breadth_audit() -> MemoryBreadthAudit:
    global _audit
    if _audit is None:
        _audit = MemoryBreadthAudit()
    return _audit
