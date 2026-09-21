"""Small persistent concept layer for embodied sensorimotor learning.

Concepts are inferred from structured observations and outcomes, not from a
fixed language dictionary. Spatial coordinates remain map-local; these records
capture reusable relations such as obstacle risk and successful reachability.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict


class EmbodiedConceptMemory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._concepts: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                self._concepts = value.get("concepts", value) if isinstance(value.get("concepts", value), dict) else {}
        except Exception:
            self._concepts = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"version": 1, "concepts": self._concepts}, indent=2, ensure_ascii=False), encoding="utf-8")

    def _observe(self, key: str, label: str, evidence: float) -> None:
        item = self._concepts.setdefault(key, {"label": label, "observations": 0, "positive": 0, "negative": 0, "confidence": 0.2, "last_seen": 0.0})
        item["observations"] += 1
        if evidence > 0:
            item["positive"] += 1
        elif evidence < 0:
            item["negative"] += 1
        item["confidence"] = round(min(0.99, 0.2 + (item["positive"] + item["negative"]) * 0.04 + abs(item["positive"] - item["negative"]) * 0.01), 3)
        item["last_seen"] = time.time()

    def learn(self, episode: Any) -> None:
        """Extract relational concepts from one completed episode."""
        before = episode.obs_before
        action = str(episode.action.type)
        outcome = str(episode.outcome.kind)
        reward = float(episode.reward)
        with self._lock:
            for obj in before.scene:
                kind = str(obj.kind or "object")
                self._observe(f"object:{kind}", f"Recognize {kind} as an embodied object", 1.0)
                if outcome in {"danger", "failure"} and kind == "obstacle":
                    self._observe("rule:avoid_obstacles", "Avoid obstacles when navigating", -1.0)
            if action in {"forward", "backward"} and outcome in {"danger", "failure"}:
                self._observe("rule:movement_collision_risk", "Movement can become unsafe near obstacles", -1.0)
            if action == "grab" and outcome == "success":
                self._observe("rule:reachable_target", "A reachable target can be grasped", 1.0)
            if action == "release" and outcome == "success":
                self._observe("rule:carry_to_goal", "Carrying an object to a goal completes a task", 1.0)
            self._observe(f"action:{action}", f"Understand the embodied action {action}", reward)
            if sum(int(v.get("observations", 0)) for v in self._concepts.values()) % 5 == 0:
                self._save()

    def snapshot(self, limit: int = 12) -> list[dict[str, Any]]:
        with self._lock:
            values = sorted(self._concepts.values(), key=lambda item: (float(item.get("confidence", 0)), int(item.get("observations", 0))), reverse=True)
            return [dict(item) for item in values[:limit]]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {"count": len(self._concepts), "top": self.snapshot(8)}
