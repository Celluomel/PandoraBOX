"""Bounded passive observations of Global Workspace activity.

This engine currently has no intervention mechanism or capability-specific
outcome measure. It can describe Workspace score changes, but it cannot use
those observations to verify that the organism acquired or exercised a
capability. Capability verification must remain unset until that causal
measurement path exists.
"""

from __future__ import annotations

import copy
import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

BASELINE_STEPS = 3
TRIAL_STEPS = 6


class CapabilityDevelopmentEngine:
    """Run a reversible Workspace observability experiment in the slow loop."""

    def __init__(self, organism: Any, path: str = "data/persona/capability_development.json"):
        self._organism = organism
        self._path = Path(path)
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {
            "proposal": None,
            "experiment": None,
            "verified_capability": None,
            "history": [],
        }
        self._load()

    def start(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Accept one experiment proposal and begin a fresh baseline."""
        with self._lock:
            existing = self._state.get("experiment")
            if existing and existing.get("status") in {"baseline", "running", "provisionally_verified", "stabilizing"}:
                raise ValueError("A capability experiment is already active.")
            prior_state = copy.deepcopy(self._state)
            now = time.time()
            proposal_copy = dict(proposal)
            proposal_copy["status"] = "accepted"
            proposal_copy["accepted_at"] = now
            experiment = {
                "id": str(uuid.uuid4()),
                "proposal_id": proposal_copy.get("id"),
                "title": proposal_copy.get("title", "Capability development"),
                "subsystem": "workspace",
                "status": "baseline",
                "baseline": [],
                "trials": [],
                "baseline_score": None,
                "trial_score": None,
                "result": None,
                "started_at": now,
                "updated_at": now,
                "max_baseline_steps": BASELINE_STEPS,
                "max_trial_steps": TRIAL_STEPS,
            }
            self._state["proposal"] = proposal_copy
            self._state["experiment"] = experiment
            self._state["verified_capability"] = None
            if not self._save():
                self._state = prior_state
                raise RuntimeError("Capability experiment was not persisted; start was rolled back.")
            return self.snapshot()

    def tick(self, slow_cycle: int) -> Dict[str, Any]:
        """Advance one observation and return its effect/persistence receipt."""
        if slow_cycle < 1:
            return {"outcome_status": "skipped", "effect_status": "invalid_cycle", "persisted": None}
        prior_state = None
        try:
            with self._lock:
                experiment = self._state.get("experiment")
                if not experiment or experiment.get("status") not in {"baseline", "running"}:
                    return {
                        "outcome_status": "skipped",
                        "effect_status": "no_active_experiment",
                        "experiment_status": experiment.get("status") if experiment else "not_started",
                        "persisted": None,
                    }
                prior_state = copy.deepcopy(self._state)
                phase = experiment["status"]
                before = self._observe()
                observed_change = None
                if phase == "baseline":
                    experiment["baseline"].append(before)
                    if len(experiment["baseline"]) >= experiment["max_baseline_steps"]:
                        experiment["baseline_score"] = round(self._mean_score(experiment["baseline"]), 4)
                        experiment["status"] = "running"
                        logger.info("[CapabilityExperiment] baseline complete: %.3f", experiment["baseline_score"])
                    effect_status = "baseline_observed"
                else:
                    after = self._observe()
                    trial = {
                        "step": len(experiment["trials"]) + 1,
                        "slow_cycle": slow_cycle,
                        "admitted": None,
                        "intervention_status": "not_applied",
                        "before": before,
                        "after": after,
                        "score": round(after["score"], 4),
                        "delta": round(after["score"] - before["score"], 4),
                        "timestamp": time.time(),
                    }
                    experiment["trials"].append(trial)
                    experiment["updated_at"] = time.time()
                    if len(experiment["trials"]) >= experiment["max_trial_steps"]:
                        self._finish_initial_locked(experiment)
                        effect_status = "observations_completed_capability_unverified"
                        observed_change = experiment.get("result", {}).get("observed_change")
                    else:
                        effect_status = "trial_observed_no_intervention"

                persisted = self._save()
                if not persisted:
                    self._state = prior_state
                    return {
                        "outcome_status": "persistence_failed",
                        "effect_status": "state_update_rolled_back",
                        "experiment_id": experiment.get("id"),
                        "phase": phase,
                        "persisted": False,
                    }
                return {
                    "outcome_status": "completed",
                    "effect_status": effect_status,
                    "experiment_id": experiment.get("id"),
                    "phase": phase,
                    "experiment_status": experiment.get("status"),
                    "baseline_count": len(experiment.get("baseline", [])),
                    "trial_count": len(experiment.get("trials", [])),
                    "observed_change": observed_change,
                    "capability_status": "unverified",
                    "persisted": True,
                }
        except Exception as exc:
            logger.debug("[CapabilityExperiment] tick failed: %s", exc)
            if prior_state is not None:
                with self._lock:
                    self._state = prior_state
            return {
                "outcome_status": "error",
                "effect_status": "state_update_rolled_back" if prior_state is not None else "no_state_change",
                "error_type": type(exc).__name__,
                "persisted": None,
            }

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state, ensure_ascii=False))

    def _observe(self) -> Dict[str, Any]:
        workspace = getattr(self._organism, "workspace", None)
        summary = workspace.summary() if workspace and hasattr(workspace, "summary") else {}
        sources = summary.get("sources", []) if isinstance(summary, dict) else []
        diversity = float(summary.get("diversity", 0.0) or 0.0) if isinstance(summary, dict) else 0.0
        total = float(summary.get("total_items", 0) or 0) if isinstance(summary, dict) else 0.0
        # A bounded composite signal: source diversity plus a saturated activity term.
        score = max(0.0, min(1.0, 0.7 * diversity + 0.3 * min(total / 10.0, 1.0)))
        return {"score": round(score, 4), "diversity": round(diversity, 4), "total_items": int(total), "sources": list(sources)[:20]}

    @staticmethod
    def _mean_score(observations) -> float:
        return sum(float(item.get("score", 0.0)) for item in observations) / max(1, len(observations))

    def _finish_initial_locked(self, experiment: Dict[str, Any]) -> None:
        baseline = float(experiment.get("baseline_score") or 0.0)
        trials = experiment.get("trials", [])
        trial_score = sum(float(item.get("score", 0.0)) for item in trials) / max(1, len(trials))
        admitted_values = [item.get("admitted") for item in trials if item.get("admitted") is not None]
        admitted = sum(1 for value in admitted_values if value)
        observed_change = trial_score - baseline
        experiment["trial_score"] = round(trial_score, 4)
        experiment["result"] = {
            "baseline_score": round(baseline, 4),
            "trial_score": round(trial_score, 4),
            "observed_change": round(observed_change, 4),
            "admitted_trials": admitted if admitted_values else None,
            "trial_count": len(trials),
            "evidence_scope": "passive_workspace_observation",
            "causal_attribution": "not_established",
            "verification_blocker": (
                "No capability intervention or intervention receipt was recorded; "
                "workspace activity change cannot verify a capability."
            ),
            "evidence": (
                "Observed workspace diversity/activity changed across time. "
                "No intervention was applied, so this is descriptive evidence only."
            ),
            "confirmation": "not_verifiable_without_intervention",
        }
        experiment["status"] = "observational_only"
        experiment["completed_at"] = time.time()
        self._state["verified_capability"] = None
        self._state["history"].append(dict(experiment))
        self._state["history"] = self._state["history"][-20:]
        logger.info(
            "[CapabilityExperiment] observational-only: baseline=%.3f trials=%.3f change=%+.3f",
            baseline, trial_score, observed_change,
        )

    def _load(self) -> None:
        try:
            if self._path.exists():
                value = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    self._state.update(value)
                    migrated = bool(self._state.get("verified_capability"))
                    experiment = self._state.get("experiment")
                    # Historical versions promoted passive score changes into
                    # capabilities. Demote those claims on load; their stored
                    # measurements remain available as observations.
                    if experiment and experiment.get("status") in {
                        "provisionally_verified", "stabilizing", "verified",
                    }:
                        experiment["status"] = "observational_only"
                        result = experiment.get("result")
                        if not isinstance(result, dict):
                            result = {}
                            experiment["result"] = result
                        result["confirmation"] = "not_verifiable_without_intervention"
                        result["evidence_scope"] = "passive_workspace_observation"
                        result["causal_attribution"] = "not_established"
                        result["verification_blocker"] = (
                            "Legacy capability status came from passive workspace observations, "
                            "not a recorded capability intervention."
                        )
                        migrated = True
                    for historical in self._state.get("history", []):
                        if isinstance(historical, dict) and historical.get("status") in {
                            "provisionally_verified", "stabilizing", "verified",
                        }:
                            historical["status"] = "observational_only"
                            result = historical.get("result")
                            if not isinstance(result, dict):
                                result = {}
                                historical["result"] = result
                            result["confirmation"] = "not_verifiable_without_intervention"
                            result["evidence_scope"] = "passive_workspace_observation"
                            result["causal_attribution"] = "not_established"
                            result["verification_blocker"] = (
                                "Legacy capability status came from passive workspace observations, "
                                "not a recorded capability intervention."
                            )
                            migrated = True
                    self._state["verified_capability"] = None
                    if migrated:
                        self._save()
        except Exception as exc:
            logger.warning("[CapabilityExperiment] load failed: %s", exc)

    def _save(self) -> bool:
        """Atomically persist state and confirm it on disk."""
        temp = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            with self._lock:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                expected = json.loads(json.dumps(self._state, ensure_ascii=False))
            temp.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self._path)
            saved = json.loads(self._path.read_text(encoding="utf-8"))
            if saved != expected:
                return False
            return True
        except Exception as exc:
            logger.warning("[CapabilityExperiment] save failed: %s", type(exc).__name__)
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
            return False
