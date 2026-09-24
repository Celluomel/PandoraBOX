"""Persistent, validation-first plan ledger owned by the Body.

This deliberately stops before actuation.  It establishes the auditable
contract used by the later TaskGraph executor: accepted plans, snapshots and
event transitions survive restart and are visible to the Brain/UI.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .contracts import ActionResult, BodyPlan, BodySnapshot, PLAN_STATES


class BodyPlanRuntime:
    def __init__(self, data_dir: Path) -> None:
        self._lock = threading.RLock()
        self._data_dir = Path(data_dir)
        self._active_path = self._data_dir / "active_plan.json"
        self._plans_path = self._data_dir / "plans.jsonl"
        self._actions_path = self._data_dir / "actions.jsonl"
        self._active: Optional[BodyPlan] = self._restore_active()
        self._latest_snapshot: Optional[BodySnapshot] = None

    def _restore_active(self) -> Optional[BodyPlan]:
        try:
            raw = json.loads(self._active_path.read_text(encoding="utf-8"))
            plan = BodyPlan.from_dict(raw)
            return plan if plan.state not in {"completed", "cancelled", "expired", "rejected"} else None
        except Exception:
            return None

    def _append(self, path: Path, event: Dict[str, Any]) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _persist_active(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        if self._active is None:
            self._active_path.unlink(missing_ok=True)
            return
        temp = self._active_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._active.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self._active_path)

    def record_snapshot(self, snapshot: BodySnapshot) -> None:
        with self._lock:
            self._latest_snapshot = snapshot

    def submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        plan = BodyPlan.from_dict(payload)
        errors = self._validate_shape(plan)
        with self._lock:
            snapshot = self._latest_snapshot
            if not errors and snapshot is not None:
                errors.extend(self._validate_against_snapshot(plan, snapshot))
            elif not errors:
                errors.append("no Body snapshot is available yet")
            if errors:
                plan.state = "rejected"
                result = {"accepted": False, "plan": plan.as_dict(), "errors": errors}
                self._append(self._plans_path, {"event": "rejected", "at": time.time(), **result})
                return result
            if self._active and self._active.state not in {"completed", "cancelled", "rejected"}:
                return {"accepted": False, "errors": ["another plan already owns the Body plan lease"], "plan": self._active.as_dict()}
            plan.state = "ready"
            self._active = plan
            self._persist_active()
            result = {"accepted": True, "plan": plan.as_dict(), "snapshot_id": snapshot.snapshot_id}
            self._append(self._plans_path, {"event": "accepted", "at": time.time(), **result})
            return result

    @staticmethod
    def _validate_shape(plan: BodyPlan) -> list[str]:
        errors: list[str] = []
        if not plan.objective:
            errors.append("objective is required")
        if not plan.steps:
            errors.append("at least one ordered step is required")
        if plan.state not in PLAN_STATES:
            errors.append("invalid plan state")
        if plan.expires_at <= time.time():
            errors.append("plan is already expired")
        seen: set[str] = set()
        for step in plan.steps:
            if step.step_id in seen:
                errors.append(f"duplicate step_id: {step.step_id}")
            seen.add(step.step_id)
            if not step.verb:
                errors.append(f"step {step.step_id} has no verb")
        return errors

    @staticmethod
    def _validate_against_snapshot(plan: BodyPlan, snapshot: BodySnapshot) -> list[str]:
        errors: list[str] = []
        objects = {str(item.get("id")) for item in snapshot.objects}
        capability_set = set(snapshot.capabilities)
        missing = sorted(set(plan.required_capabilities) - capability_set)
        if missing:
            errors.append("missing capabilities: " + ", ".join(missing))
        for step in plan.steps:
            if step.target and step.target not in objects and step.target not in {"goal", "self"}:
                errors.append(f"step {step.step_id} references unknown target: {step.target}")
        return errors

    def cancel(self, plan_id: str, reason: str = "cancelled by operator") -> Dict[str, Any]:
        with self._lock:
            if self._active is None or self._active.plan_id != plan_id:
                return {"ok": False, "error": "active plan not found"}
            self._active.state = "cancelled"
            result = {"ok": True, "plan": self._active.as_dict(), "reason": reason}
            self._append(self._plans_path, {"event": "cancelled", "at": time.time(), **result})
            self._active = None
            self._persist_active()
            return result

    def record_action(self, result: ActionResult) -> Dict[str, Any]:
        """Append an auditable result; execution will call this in Phase 1."""
        with self._lock:
            if self._latest_snapshot is None or result.snapshot_id != self._latest_snapshot.snapshot_id:
                return {"ok": False, "error": "action result must reference the current Body snapshot"}
            self._append(self._actions_path, {"event": "action_result", **result.as_dict()})
            return {"ok": True, "action": result.as_dict()}

    def active_plan(self) -> Optional[BodyPlan]:
        with self._lock:
            return self._active

    def expire_if_needed(self) -> Optional[Dict[str, Any]]:
        """Terminate an overdue lease before it can emit another action."""
        with self._lock:
            plan = self._active
            if plan is None or plan.expires_at > time.time():
                return None
            plan.state = "expired"
            result = {"plan": plan.as_dict(), "reason": "plan deadline elapsed"}
            self._append(self._plans_path, {"event": "expired", "at": time.time(), **result})
            self._active = None
            self._persist_active()
            return result

    def begin_execution(self) -> None:
        with self._lock:
            if self._active and self._active.state == "ready":
                self._active.state = "executing"
                self._persist_active()
                self._append(self._plans_path, {"event": "execution_started", "at": time.time(), "plan": self._active.as_dict()})

    def advance(self, step_id: str, snapshot_id: str) -> Dict[str, Any]:
        with self._lock:
            plan = self._active
            if plan is None or plan.state not in {"ready", "executing", "observing"}:
                return {"ok": False, "error": "no executable active plan"}
            if plan.current_step_index >= len(plan.steps) or plan.steps[plan.current_step_index].step_id != step_id:
                return {"ok": False, "error": "step is no longer current"}
            plan.current_step_index += 1
            plan.last_error = ""
            plan.state = "completed" if plan.current_step_index >= len(plan.steps) else "executing"
            result = {"ok": True, "snapshot_id": snapshot_id, "plan": plan.as_dict()}
            self._append(self._plans_path, {"event": "step_completed", "at": time.time(), "step_id": step_id, **result})
            self._persist_active()
            return result

    def record_step_failure(self, step_id: str, snapshot_id: str, description: str) -> Dict[str, Any]:
        with self._lock:
            plan = self._active
            if plan is None or plan.current_step_index >= len(plan.steps):
                return {"ok": False, "error": "no active step"}
            step = plan.steps[plan.current_step_index]
            if step.step_id != step_id:
                return {"ok": False, "error": "step is no longer current"}
            attempts = int(plan.step_attempts.get(step_id, 0)) + 1
            plan.step_attempts[step_id] = attempts
            plan.last_error = description
            plan.state = "recovery" if attempts > step.max_retries else "executing"
            result = {"ok": True, "attempts": attempts, "snapshot_id": snapshot_id, "plan": plan.as_dict()}
            self._append(self._plans_path, {"event": "step_failed", "at": time.time(), "step_id": step_id, "description": description, **result})
            self._persist_active()
            return result

    def resume_after_recovery(self, step_id: str, snapshot_id: str, description: str) -> Dict[str, Any]:
        with self._lock:
            plan = self._active
            if plan is None or plan.state != "recovery":
                return {"ok": False, "error": "plan is not recovering"}
            if plan.current_step_index >= len(plan.steps) or plan.steps[plan.current_step_index].step_id != step_id:
                return {"ok": False, "error": "step is no longer current"}
            plan.state = "executing"
            plan.last_error = description
            result = {"ok": True, "snapshot_id": snapshot_id, "plan": plan.as_dict()}
            self._append(self._plans_path, {"event": "recovery_completed", "at": time.time(), "step_id": step_id, **result})
            self._persist_active()
            return result

    def payload(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "active_plan": self._active.as_dict() if self._active else None,
                "latest_snapshot": self._latest_snapshot.as_dict() if self._latest_snapshot else None,
                "execution": "task_graph",
                "note": "Plans execute locally against fresh Body snapshots; every action and transition is persisted.",
            }
