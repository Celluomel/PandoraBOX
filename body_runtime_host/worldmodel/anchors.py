"""Physical world memory — the three anchor families.

    * AnchorLieu         — remembered *places* (stable spatial references)
    * AnchorObjet        — remembered *objects* (identity + affordances)
    * AnchorTrajectoire  — remembered *trajectories* (action sequences + outcome)

Persistence is atomic (temp file + os.replace), matching the dashboard's
torn-read fix convention.  Anchors are *revised, optimized and reinforced*
by ``ConsolidationEngine``; this module only stores/queries/mutates them.
"""
from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import AnchorLieu, AnchorObjet, AnchorTrajectoire, BodyState, Observation, new_id

logger = logging.getLogger(__name__)

# Two places whose centres are closer than this (in world units) are the
# *same* place — they are merged instead of duplicated.
LIEU_MERGE_DISTANCE = 1.5
# Object anchors merge on exact id (objects carry stable ids in the scene).


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON atomically (temp file in same dir + os.replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class PhysicalMemory:
    """Thread-safe store of the body's physical-world anchors."""

    def __init__(self, save_path: str | Path = "data/body/worldmodel/anchors.json"):
        self.save_path = Path(save_path)
        self._lock = threading.RLock()
        self.lieux: Dict[str, AnchorLieu] = {}
        self.objets: Dict[str, AnchorObjet] = {}
        self.trajectories: Dict[str, AnchorTrajectoire] = {}
        self._load()

    # ── persistence ─────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if not self.save_path.exists():
                return
            payload = json.loads(self.save_path.read_text(encoding="utf-8"))
            with self._lock:
                for item in payload.get("lieux", []):
                    a = AnchorLieu.from_dict(item)
                    self.lieux[a.id] = a
                for item in payload.get("objets", []):
                    a = AnchorObjet.from_dict(item)
                    self.objets[a.id] = a
                for item in payload.get("trajectories", []):
                    a = AnchorTrajectoire.from_dict(item)
                    self.trajectories[a.id] = a
        except Exception as exc:
            logger.warning("[PhysicalMemory] failed to load %s: %s", self.save_path, exc)

    def save(self) -> None:
        with self._lock:
            payload = {
                "lieux": [a.as_dict() for a in self.lieux.values()],
                "objets": [a.as_dict() for a in self.objets.values()],
                "trajectories": [a.as_dict() for a in self.trajectories.values()],
            }
        try:
            atomic_write_json(self.save_path, payload)
        except Exception as exc:
            logger.warning("[PhysicalMemory] failed to save %s: %s", self.save_path, exc)

    def reset(self) -> None:
        with self._lock:
            self.lieux.clear()
            self.objets.clear()
            self.trajectories.clear()
        self.save()

    # ── lieux ───────────────────────────────────────────────────────────────

    def find_lieu(self, position: List[float], max_distance: float = LIEU_MERGE_DISTANCE) -> Optional[AnchorLieu]:
        best, best_d = None, None
        with self._lock:
            for a in self.lieux.values():
                d = math.dist(a.position[:2], position[:2])
                if best_d is None or d < best_d:
                    best, best_d = a, d
        if best is not None and best_d is not None and best_d <= max_distance:
            return best
        return None

    def upsert_lieu(
        self,
        label: str,
        position: List[float],
        orientation: float = 0.0,
        objects: Optional[List[str]] = None,
        affordances: Optional[Dict[str, float]] = None,
    ) -> AnchorLieu:
        existing = self.find_lieu(position)
        with self._lock:
            if existing is not None:
                a = existing
                if objects is not None:
                    for oid in objects:
                        if oid not in a.objects:
                            a.objects.append(oid)
                if affordances:
                    for k, v in affordances.items():
                        prev = a.affordances.get(k, 0.0)
                        a.affordances[k] = round(0.7 * prev + 0.3 * float(v), 4)
                a.visits += 1
                a.updated_at = _now()
                a.last_used_at = a.updated_at
                a.orientation = orientation
            else:
                a = AnchorLieu(
                    id=new_id("lieu"),
                    label=label or _place_label(position),
                    position=[float(v) for v in position[:3]] + [0.0] * (3 - min(3, len(position))),
                    orientation=orientation,
                    objects=list(objects or []),
                    affordances={str(k): float(v) for k, v in (affordances or {}).items()},
                )
                a.visits = 1
                self.lieux[a.id] = a
            self.lieux[a.id] = a
        return a

    # ── objets ──────────────────────────────────────────────────────────────

    def get_objet(self, object_id: str) -> Optional[AnchorObjet]:
        with self._lock:
            return self.objets.get(object_id)

    def upsert_objet(
        self,
        object_id: str,
        label: str,
        kind: str,
        position: List[float],
        props: Optional[Dict[str, Any]] = None,
        affordances: Optional[Dict[str, float]] = None,
    ) -> AnchorObjet:
        with self._lock:
            a = self.objets.get(object_id)
            if a is None:
                a = AnchorObjet(
                    id=object_id, label=label, kind=kind,
                    position=[float(v) for v in position[:3]],
                    props=dict(props or {}),
                    affordances={str(k): float(v) for k, v in (affordances or {}).items()},
                )
                self.objets[a.id] = a
            else:
                a.position = [float(v) for v in position[:3]]
                if kind:
                    a.kind = kind
                if props:
                    a.props.update(props)
                if affordances:
                    for k, v in affordances.items():
                        prev = a.affordances.get(k, 0.0)
                        a.affordances[k] = round(0.6 * prev + 0.4 * float(v), 4)
                a.updated_at = _now()
                a.last_used_at = a.updated_at
            self.objets[a.id] = a
        return a

    # ── trajectoires ────────────────────────────────────────────────────────

    def upsert_trajectory(
        self,
        label: str,
        positions: List[List[float]],
        actions: List[str],
        outcome: str,
        utility: float = 0.0,
        context_lieux: Optional[List[str]] = None,
        context_objets: Optional[List[str]] = None,
    ) -> AnchorTrajectoire:
        key = "|".join(actions)
        with self._lock:
            a = None
            for t in self.trajectories.values():
                if t.actions == actions:
                    a = t
                    break
            if a is None:
                a = AnchorTrajectoire(
                    id=new_id("traj"),
                    label=label or f"traj-{key[:24]}",
                    positions=[[float(v) for v in p] for p in positions],
                    actions=list(actions),
                    outcome=outcome,
                    context_lieux=list(context_lieux or []),
                    context_objets=list(context_objets or []),
                )
                self.trajectories[a.id] = a
            else:
                a.positions = [[float(v) for v in p] for p in positions] or a.positions
                a.outcome = outcome
                if context_lieux:
                    a.context_lieux = list(dict.fromkeys(a.context_lieux + context_lieux))[:12]
                if context_objets:
                    a.context_objets = list(dict.fromkeys(a.context_objets + context_objets))[:12]
            if outcome == "success":
                a.success_count += 1
            elif outcome in {"failure", "danger"}:
                a.fail_count += 1
            total = max(1, a.success_count + a.fail_count)
            a.utility = round(0.6 * a.utility + 0.4 * float(utility), 4)
            a.reliability = round(min(1.0, a.success_count / total * 0.7 + min(1.0, total / 5.0) * 0.3), 4)
            a.updated_at = _now()
            a.last_used_at = a.updated_at
            self.trajectories[a.id] = a
        return a

    # ── stats ───────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            def _agg(anchors):
                if not anchors:
                    return {"count": 0}
                return {
                    "count": len(anchors),
                    "avg_reliability": round(float(sum(a.reliability for a in anchors) / len(anchors)), 4),
                    "avg_utility": round(float(sum(a.utility for a in anchors) / len(anchors)), 4),
                    "stale": sum(1 for a in anchors if a.stale),
                }
            return {
                "lieux": _agg(list(self.lieux.values())),
                "objets": _agg(list(self.objets.values())),
                "trajectories": _agg(list(self.trajectories.values())),
            }

    def top_anchors(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Highest-reliability anchors per family (for the dashboard / Brain)."""
        with self._lock:
            def _top(anchors, limit=limit):
                ranked = sorted(anchors, key=lambda a: (a.reliability, a.utility), reverse=True)
                return [
                    {
                        "id": a.id, "label": a.label,
                        "reliability": round(a.reliability, 3),
                        "utility": round(a.utility, 3),
                    }
                    for a in ranked[:limit]
                ]
            return {
                "lieux": _top(list(self.lieux.values())),
                "objets": _top(list(self.objets.values())),
                "trajectories": _top(list(self.trajectories.values())),
            }


def _now() -> float:
    import time
    return time.time()


def _place_label(position: List[float]) -> str:
    return f"place({position[0]:.1f},{position[1]:.1f})"
