"""Persistent, evidence-backed skill selection for the Body planner.

Skills are learned from Body outcomes, never inferred from a phrase or a
scenario name.  A skill may be selected only while its recorded preconditions
and limits are satisfied by the current snapshot.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional, Tuple


class BodySkillLibrary:
    """Store reusable Body skills and guard their use at execution time."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = RLock()
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            value = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                value.setdefault("version", 1)
                value.setdefault("skills", {})
                return value
        except Exception:
            pass
        return {"version": 1, "skills": {}}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    @staticmethod
    def _skill_id(step: Any) -> str:
        explicit = (getattr(step, "arguments", {}) or {}).get("skill_id")
        return str(explicit or f"body.{getattr(step, 'verb', 'unknown')}").strip().lower()

    @staticmethod
    def _capability_for(step: Any) -> str:
        return str(getattr(step, "verb", "") or "").strip().lower()

    @staticmethod
    def _preconditions(step: Any, snapshot: Any, body: Any) -> list[Dict[str, Any]]:
        capability = BodySkillLibrary._capability_for(step)
        required = {
            "navigate": "navigate",
            "grab": "gripper",
            "release": "gripper",
        }.get(capability, capability)
        return [{"capability": required, "minimum": 0.0001}] if required else []

    def _preconditions_ok(self, skill: Dict[str, Any], step: Any, snapshot: Any, body: Any) -> Tuple[bool, str]:
        capabilities = set(getattr(snapshot, "capabilities", []) or [])
        body_caps = getattr(body, "capabilities", {}) or {}
        for condition in skill.get("preconditions", []) or self._preconditions(step, snapshot, body):
            name = str(condition.get("capability") or "").strip()
            if name and name not in capabilities and float(body_caps.get(name, 0) or 0) <= float(condition.get("minimum", 0) or 0):
                return False, f"skill precondition not met: capability '{name}'"
        return True, ""

    def resolve(self, step: Any, snapshot: Any, body: Any, strict: bool = False) -> Tuple[Optional[Dict[str, Any]], str]:
        """Resolve a verified compatible skill, refusing unsafe reuse."""
        requested = (getattr(step, "arguments", {}) or {}).get("skill_id")
        capability = self._capability_for(step)
        with self._lock:
            candidates = []
            for skill in self._data.get("skills", {}).values():
                if skill.get("state") != "verified":
                    continue
                if requested and skill.get("skill_id") != str(requested):
                    continue
                if not requested and skill.get("capability") != capability:
                    continue
                candidates.append(skill)
            if not candidates:
                return None, "no verified compatible skill"
            skill = max(candidates, key=lambda item: (float(item.get("generalization", 0)), float(item.get("last_verified", 0))))
            limits = skill.get("limits", {}) or {}
            if isinstance(limits, list):
                limits = {str(item.get("name")): item.get("value") for item in limits if isinstance(item, dict) and item.get("name")}
            max_failures = limits.get("max_failures")
            if max_failures is not None and int(skill.get("failures", 0)) >= int(max_failures):
                return None, f"skill limit reached: {skill.get('skill_id')} failures"
            minimum = float(limits.get("min_generalization", 0.0) or 0.0)
            if float(skill.get("generalization", 0.0)) < minimum:
                return None, f"skill generalization below limit: {skill.get('skill_id')}"
            ok, reason = self._preconditions_ok(skill, step, snapshot, body)
            if not ok:
                return None, reason
            return dict(skill), f"verified skill selected: {skill.get('skill_id')}"

    def record_trial(self, step: Any, outcome: Any, snapshot: Any, body: Any) -> Dict[str, Any]:
        """Accumulate outcome evidence and promote only repeated successes."""
        skill_id = self._skill_id(step)
        capability = self._capability_for(step)
        kind = str(getattr(outcome, "kind", "") or "").lower()
        success = kind in {"success", "succeeded", "executed", "complete", "completed"}
        failure = kind in {"failure", "failed", "blocked", "danger"}
        with self._lock:
            skill = self._data["skills"].setdefault(skill_id, {
                "skill_id": skill_id, "capability": capability, "state": "candidate",
                "successes": 0, "failures": 0, "evidence_count": 0,
                "generalization": 0.0, "preconditions": self._preconditions(step, snapshot, body),
                "limits": {"max_failures": 3, "min_generalization": 0.60},
                "created_at": time.time(),
            })
            if success or failure:
                skill["evidence_count"] = int(skill.get("evidence_count", 0)) + 1
                skill["successes"] = int(skill.get("successes", 0)) + int(success)
                skill["failures"] = int(skill.get("failures", 0)) + int(failure)
                trials = int(skill["successes"]) + int(skill["failures"])
                skill["generalization"] = round(skill["successes"] / max(1, trials), 3)
                if skill["successes"] >= 3 and skill["generalization"] >= 0.60 and skill["failures"] < 3:
                    skill["state"] = "verified"
                elif skill["failures"] >= 3:
                    skill["state"] = "suspended"
                else:
                    skill["state"] = "candidate"
                skill["last_trial"] = time.time()
                self._save()
            return dict(skill)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._data, ensure_ascii=False))
