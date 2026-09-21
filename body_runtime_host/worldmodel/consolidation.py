"""Memory consolidation — revision, optimization, reinforcement.

Implements the protocol from the spec:

    1. Compare prediction vs reality  -> prediction error
    2. Revise the anchors             -> reliability / utility / affordances
    3. Reinforce what survived        -> consolidate stable invariants
    4. Stabilise (stability/plasticity) -> high-reliability anchors move slowly

Stability/plasticity rule: the *effective* learning rate of an anchor is
scaled by (1 - reliability).  An anchor that has repeatedly proven reliable
is therefore hard to overwrite (stability), while a new/uncertain anchor
adapts quickly (plasticity).  This is the direct implementation of
"the new is integrated in dialogue with the past, not by brutal
replacement".
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from .anchors import PhysicalMemory
from .types import AnchorLieu, AnchorObjet, AnchorTrajectoire, Episode, Observation

logger = logging.getLogger(__name__)

# Base anchor learning rate.
ALPHA = 0.3
# An anchor older than this (seconds) with few uses is considered stale.
STALE_AFTER = 60 * 60 * 24 * 7  # 7 days
MIN_VISITS_FOR_STALE = 2


class ConsolidationEngine:
    def __init__(self, memory: PhysicalMemory, alpha: float = ALPHA):
        self.memory = memory
        self.alpha = float(alpha)

    # ── per-episode revision ────────────────────────────────────────────────

    def process_episode(
        self,
        episode: Episode,
        prediction_error: float,
        body_position: Optional[List[float]] = None,
        obs_after: Optional[Observation] = None,
    ) -> Dict[str, Any]:
        """Revise the anchors implicated by this single experience.

        Returns a short report (for the dashboard / Brain context).
        """
        report: Dict[str, Any] = {"revised": [], "reinforced": [], "revised_down": []}

        obs_before = episode.obs_before
        outcome_kind = episode.outcome.kind
        reward = episode.reward
        success = outcome_kind == "success"

        # 1) Object anchors: reinforce or revise affordances actually exercised.
        acted_obj_id = episode.action.target
        if acted_obj_id:
            obj = self.memory.get_objet(acted_obj_id)
            if obj is not None:
                obj.interactions += 1
                if success:
                    obj.successes += 1
                elif outcome_kind in {"failure", "danger"}:
                    obj.failures += 1
                act = episode.action.type
                prev = obj.affordances.get(act, 0.5)
                target = 1.0 if success else (0.2 if outcome_kind in {"failure", "danger"} else 0.5)
                eff = self._effective_alpha(obj.reliability)
                obj.affordances[act] = round(prev + eff * (target - prev), 4)
                obj.utility = round(obj.utility + self.alpha * (max(0.0, reward) - obj.utility) * 0.3, 4)
                # reliability tracks success rate, smoothed
                total = max(1, obj.successes + obj.failures)
                sr = obj.successes / total
                obj.reliability = round(0.7 * obj.reliability + 0.3 * sr, 4)
                obj.updated_at = time.time()
                obj.last_used_at = obj.updated_at
                tag = "reinforced" if success else "revised_down"
                report[tag].append(f"{obj.label}:{act}")

        # 2) Place anchors: reinforce the current place, lower it if dangerous.
        lieu = None
        if body_position:
            lieu = self.memory.find_lieu(list(body_position))
        if lieu is not None:
            if outcome_kind == "danger":
                self._downgrade(lieu, report)
            elif success:
                self._reinforce_lieu(lieu, reward, report)
            lieu.last_used_at = time.time()

        # 3) Trajectory anchor: reinforce / revise the action sequence.
        seq = [episode.action.type]
        traj = self.memory.upsert_trajectory(
            label=f"{episode.action.type}",
            positions=[(episode.action.params or {}).get("body_pos") or []],
            actions=seq,
            outcome=outcome_kind,
            utility=reward,
        )
        if outcome_kind == "success":
            report["reinforced"].append(traj.label)

        return report

    # ── background consolidation pass ───────────────────────────────────────

    def background_pass(self) -> Dict[str, Any]:
        """Periodic pass: mark stale anchors, prune nothing (intent-based).

        Anchors are never blindly deleted.  A stale anchor is *flagged* so it
        can be revisited (or merged) with intent, matching the user's
        preference for intent-based pruning over blind orphan deletion.
        """
        now = time.time()
        flagged = 0
        with self.memory._lock:
            for a in list(self.memory.lieux.values()) + list(self.memory.objets.values()) + list(self.memory.trajectories.values()):
                if not a.stale and (now - a.last_used_at) > STALE_AFTER and self._low_usage(a):
                    a.stale = True
                    a.updated_at = now
                    flagged += 1
        self.memory.save()
        return {"stale_flagged": flagged, "timestamp": now}

    # ── internal helpers ────────────────────────────────────────────────────

    def _effective_alpha(self, reliability: float) -> float:
        """Stability/plasticity: reliable anchors adapt slowly."""
        return self.alpha * max(0.05, 1.0 - float(reliability) * 0.8)

    def _low_usage(self, a: Any) -> bool:
        visits = getattr(a, "visits", 0) or getattr(a, "interactions", 0) or (getattr(a, "success_count", 0) + getattr(a, "fail_count", 0))
        return int(visits) < MIN_VISITS_FOR_STALE

    def _reinforce_lieu(self, lieu: AnchorLieu, reward: float, report: Dict[str, Any]) -> None:
        eff = self._effective_alpha(lieu.reliability)
        lieu.reliability = round(min(1.0, lieu.reliability + eff * 0.3), 4)
        lieu.utility = round(lieu.utility + self.alpha * max(0.0, reward) * 0.5, 4)
        lieu.updated_at = time.time()
        report["reinforced"].append(lieu.label)

    def _downgrade(self, lieu: AnchorLieu, report: Dict[str, Any]) -> None:
        eff = self._effective_alpha(lieu.reliability)
        lieu.reliability = round(max(0.05, lieu.reliability - eff * 0.4), 4)
        lieu.utility = round(max(-1.0, lieu.utility - self.alpha * 0.5), 4)
        lieu.updated_at = time.time()
        report["revised_down"].append(lieu.label)
