"""Action policy — decision by anticipation (model-based).

The policy is *not* a separate black box.  It evaluates candidate actions by
imagining their consequences inside the learned latent dynamics
(``LatentWorldDynamics.rollout``) and picks the action whose imagined future
has the best expected value.  This is the "decision guided by anticipation"
principle: the agent chooses the action leading to the best *simulated*
future, not the one with the best immediate reward.

Counterfactual comparison: because the transition is action-conditioned,
evaluating two candidates from the *same* state isolates the causal effect
of each action (separation of correlation and causation).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from .dynamics import LatentWorldDynamics
from .types import Action

logger = logging.getLogger(__name__)


class Policy:
    def __init__(
        self,
        dynamics: LatentWorldDynamics,
        horizon: int = 8,
        risk_aversion: float = 0.25,
        exploration: float = 0.10,
    ):
        self.dyn = dynamics
        self.horizon = max(2, int(horizon))
        self.risk_aversion = float(risk_aversion)
        self.exploration = float(exploration)
        self._rng = np.random.default_rng(1234)
        # action -> running mean value (for stable tie-breaking / exploration)
        self._action_value: Dict[str, List[float]] = {}

    # ── evaluation ──────────────────────────────────────────────────────────

    def evaluate(self, s: np.ndarray, action: Any, prior: float = 0.0) -> Dict[str, Any]:
        """Imagined evaluation of one candidate action from state s.

        ``prior`` is an optional affordance-derived bonus (goal-directed
        exploration signal) added on top of the imagined value.
        """
        a = self._as_action(action)
        cf = self.dyn.counterfactual(s, a, self.horizon)
        values = np.asarray(cf.get("mean_value", 0.0))
        # risk term: penalise imagined variance (uncertainty in the future)
        states, vals = self.dyn.rollout(np.asarray(s, dtype="float32"), [a] * self.horizon, self.horizon)
        var = float(np.var(vals)) if len(vals) > 1 else 0.0
        score = float(cf["mean_value"]) - self.risk_aversion * var + float(prior)
        return {
            "action": a,
            "score": round(score, 5),
            "prior": round(float(prior), 5),
            "mean_imagined_value": round(float(cf["mean_value"]), 5),
            "terminal_value": round(cf["terminal_value"], 4),
            "imagined_variance": round(var, 6),
            "horizon": cf["horizon"],
        }

    def decide(
        self,
        s: np.ndarray,
        candidates: Sequence[Any],
        top_k: int = 3,
        prior: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Pick the best candidate by imagined rollout (with light exploration).

        ``prior`` maps action type -> bonus (affordance-guided exploration);
        it is a weak, decaying signal — the learned imagined value dominates
        as the model improves.
        """
        candidates = list(candidates)
        if not candidates:
            return {"action": None, "score": 0.0, "evaluations": [], "reason": "no candidates"}

        def _p(a: Any) -> float:
            if not prior:
                return 0.0
            return float(prior.get(self._action_key(a), 0.0))

        evaluations = [self.evaluate(s, a, prior=_p(a)) for a in candidates]
        # exploration: occasionally take a non-greedy action (softmax-ish)
        if self.exploration > 0 and self._rng.random() < self.exploration and len(candidates) > 1:
            scores = np.clip(np.asarray([e["score"] for e in evaluations], dtype="float32"), -5.0, 5.0)
            scores -= scores.max()
            p = np.exp(0.5 * scores)
            p /= p.sum()
            pick = int(self._rng.choice(len(candidates), p=p))
        else:
            pick = int(np.argmax([e["score"] for e in evaluations]))

        best = evaluations[pick]
        for e in evaluations:
            key = self._action_key(e["action"])
            buf = self._action_value.setdefault(key, [])
            buf.append(e["score"])
            if len(buf) > 50:
                buf.pop(0)

        ranked = sorted(evaluations, key=lambda e: e["score"], reverse=True)
        return {
            "action": best["action"],
            "score": best["score"],
            "chosen_index": pick,
            "evaluations": evaluations,
            "top_k": ranked[:top_k],
            "reason": "max imagined value" if pick == int(np.argmax([e["score"] for e in evaluations]))
                      else "exploration (non-greedy)",
        }

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _as_action(a: Any) -> Action:
        if isinstance(a, Action):
            return a
        if isinstance(a, dict):
            return Action.from_dict(a)
        if isinstance(a, str):
            return Action(type=a)
        return Action(type="wait")

    @staticmethod
    def _action_key(a: Any) -> str:
        if isinstance(a, Action):
            return a.type
        if isinstance(a, dict):
            return str(a.get("type", "wait"))
        return str(a)

    def action_value_history(self) -> Dict[str, float]:
        return {
            k: round(float(np.mean(v)), 4)
            for k, v in self._action_value.items()
            if v
        }
