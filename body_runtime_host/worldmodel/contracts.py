"""Validated, transport-safe contracts for Brain <-> Body planning.

These contracts describe intent and evidence; they do not grant actuator
authority.  The Body validates a plan against a fresh local snapshot before a
future task executor may act on it.
"""
from __future__ import annotations

import time
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .types import new_id


def _predicate_list(value: Any) -> List[Dict[str, Any]]:
    """Normalize LLM-produced predicate fields without trusting their shape."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return []
    if not isinstance(value, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            normalized.append(item)
        elif isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    normalized.append(parsed)
            except (TypeError, json.JSONDecodeError):
                continue
    return normalized


def _mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}
    return {}


PLAN_STATES = {
    "draft", "validating", "ready", "executing", "observing", "evaluating",
    "replanning", "recovery", "paused", "completed", "cancelled", "expired", "rejected",
}


@dataclass
class PlanStep:
    step_id: str
    verb: str
    target: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[Dict[str, Any]] = field(default_factory=list)
    postconditions: List[Dict[str, Any]] = field(default_factory=list)
    max_retries: int = 3

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Dict[str, Any], index: int = 0) -> "PlanStep":
        return cls(
            step_id=str(value.get("step_id") or f"step-{index + 1}"),
            verb=str(value.get("verb") or "").strip().lower(),
            target=str(value.get("target") or "").strip(),
            arguments=_mapping(value.get("arguments")),
            preconditions=_predicate_list(value.get("preconditions")),
            postconditions=_predicate_list(value.get("postconditions")),
            max_retries=max(0, min(10, int(value.get("max_retries", 3) or 3))),
        )


@dataclass
class BodyPlan:
    objective: str
    steps: List[PlanStep]
    source: str = "user"
    required_capabilities: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    plan_id: str = field(default_factory=lambda: new_id("plan"))
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600.0)
    state: str = "draft"
    current_step_index: int = 0
    step_attempts: Dict[str, int] = field(default_factory=dict)
    last_error: str = ""
    selected_skills: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    skill_resolution: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.as_dict() for step in self.steps]
        return data

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "BodyPlan":
        raw_steps = list(value.get("steps") or [])
        return cls(
            plan_id=str(value.get("plan_id") or new_id("plan")),
            objective=str(value.get("objective") or "").strip(),
            source=str(value.get("source") or "user"),
            required_capabilities=[str(item) for item in value.get("required_capabilities") or []],
            constraints=_mapping(value.get("constraints")),
            steps=[PlanStep.from_dict(item, index) for index, item in enumerate(raw_steps) if isinstance(item, dict)],
            created_at=float(value.get("created_at") or time.time()),
            expires_at=float(value.get("expires_at") or (time.time() + 600.0)),
            state=str(value.get("state") or "draft"),
            current_step_index=max(0, int(value.get("current_step_index") or 0)),
            step_attempts={str(key): int(count) for key, count in dict(value.get("step_attempts") or {}).items()},
            last_error=str(value.get("last_error") or ""),
            selected_skills={str(key): dict(item) for key, item in dict(value.get("selected_skills") or {}).items() if isinstance(item, dict)},
            skill_resolution=dict(value.get("skill_resolution") or {}),
        )


@dataclass
class BodySnapshot:
    source: str
    frame: str
    pose: Dict[str, float]
    objects: List[Dict[str, Any]]
    capabilities: List[str]
    reliability: float
    snapshot_id: str = field(default_factory=lambda: new_id("snap"))
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["age_ms"] = int(max(0.0, time.time() - self.timestamp) * 1000)
        return data


@dataclass
class ActionResult:
    plan_id: str
    step_id: str
    action_id: str
    status: str
    outcome: str
    snapshot_id: str
    reward: float = 0.0
    prediction_error: float = 0.0
    requires_replan: bool = False
    timestamp: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
