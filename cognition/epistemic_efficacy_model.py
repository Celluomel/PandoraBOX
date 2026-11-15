"""
EpistemicEfficacyModel — the recursive crossing
====================================================
Per the reframed mission (an external analysis reviewing the v104
self-model flatline): don't "implement a strange loop" as an engineered
feedback circuit that looks self-referential. Instead, make PandoraBOX's own
cognitive activity become an object of cognition in a way that CAUSALLY
alters the activity that generated it. The concrete test given:

  Can the self-model predict something about PandoraBOX's own future
  behaviour, be wrong, observe the error, update itself, and
  subsequently behave differently?

v104's self-model update was purely reactive (affirm a belief on a
keyword match in generated text) — it never predicted anything
falsifiable, so there was nothing for it to be WRONG about. This module
is the missing piece, using the analysis's own worked example directly:

  self-model: "I am effective at resolving epistemic uncertainty"
       -> resolve_uncertainty is chosen
       -> self-model PREDICTS how much epistemic pressure should drop
       -> next cycle, the ACTUAL drop is observed
       -> meta-prediction error = |predicted - actual|
       -> small error -> affirm effectiveness; large error -> erode it
       -> effectiveness belief scales THIS SAME goal's future
          internal_alignment boost (workspace_competition.py) ->
          future arbitration genuinely changes -> new behaviour ->
          new observation -> next prediction

Ablatable exactly like InternalCognitiveState: efficacy_model=None
(default) reproduces prior behavior with zero contribution.

Deliberately NOT done here (avoiding "optimizing to look self-aware",
the analysis's explicit warning): no narrative text about this process
is generated or injected into any prompt. The belief update and the
scoring effect are the only outputs; nothing here writes a sentence
claiming self-awareness.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

PREDICTION_SCALE = 0.30      # confidence 0.5 -> predicts a 0.15 drop, matching
                              # the analysis's own worked example exactly
GOOD_PREDICTION_THRESHOLD = 0.05   # meta-error below this counts as "right"
MIN_MULTIPLIER = 0.4         # bounds on how much effectiveness belief can
MAX_MULTIPLIER = 1.6         # scale the goal's own alignment boost
EFFECTIVENESS_BELIEF_NAME = "effective_at_resolving_uncertainty"


@dataclass
class PendingPrediction:
    predicted_drop: float
    pressure_before: float
    made_at: float
    prediction_id: str
    source_cycle_id: str
    confidence_before: float
    competition_application: Optional[Dict[str, Any]] = None


class EpistemicEfficacyModel:
    """
    Owned by the organism (see get_epistemic_efficacy_model() below —
    same singleton pattern as InternalCognitiveState/UniversalConnector).
    Tracks ONE pending falsifiable prediction at a time, tied specifically
    to resolve_uncertainty (the one self-regulatory goal with real,
    already-verified production goal-creation machinery — same scoping
    choice made in internal_cognitive_state.py).
    """

    def __init__(self, self_concept: Any) -> None:
        self._sc = self_concept
        self._pending: Optional[PendingPrediction] = None
        self.history: list[Dict[str, Any]] = []
        self.last_application: Optional[Dict[str, Any]] = None
        self._ensure_belief_seeded()

    def _ensure_belief_seeded(self) -> None:
        try:
            if EFFECTIVENESS_BELIEF_NAME not in self._sc._beliefs:
                from cognition.self_concept import SelfBelief
                self._sc._beliefs[EFFECTIVENESS_BELIEF_NAME] = SelfBelief(
                    name=EFFECTIVENESS_BELIEF_NAME,
                    statement="I am effective at resolving epistemic uncertainty",
                    confidence=0.5,
                )
        except Exception as e:
            logger.debug(f"[EpistemicEfficacyModel] belief seed failed (non-fatal): {e}")

    def _confidence(self) -> float:
        try:
            return self._sc._beliefs[EFFECTIVENESS_BELIEF_NAME].confidence
        except Exception:
            return 0.5

    def observe_if_pending(self, current_pressure: float,
                           observation_cycle_id: Optional[str] = None) -> Optional[float]:
        """
        Call once per cycle, BEFORE this cycle's own prediction/scoring.
        If a prediction from a previous resolve_uncertainty win is
        pending, compare it against what actually happened and update
        the effectiveness belief. Returns the meta-prediction-error if an
        observation was made, else None.
        """
        if self._pending is None:
            return None
        actual_drop = self._pending.pressure_before - current_pressure
        meta_error = abs(self._pending.predicted_drop - actual_drop)

        try:
            if meta_error < GOOD_PREDICTION_THRESHOLD:
                self._sc.record_affirmation(EFFECTIVENESS_BELIEF_NAME)
            else:
                self._sc.record_violation(EFFECTIVENESS_BELIEF_NAME, context="meta-prediction error")
        except Exception as e:
            logger.debug(f"[EpistemicEfficacyModel] belief update failed (non-fatal): {e}")

        self.history.append({
            "t": time.time(), "prediction_id": self._pending.prediction_id,
            "source_cycle_id": self._pending.source_cycle_id,
            "observation_cycle_id": observation_cycle_id,
            "pressure_before": self._pending.pressure_before,
            "pressure_after": current_pressure,
            "confidence_before": self._pending.confidence_before,
            "predicted_drop": self._pending.predicted_drop,
            "actual_drop": actual_drop, "meta_error": meta_error,
            "confidence_after": self._confidence(),
            "competition_application": self._pending.competition_application,
        })
        self.history = self.history[-500:]
        self._pending = None
        return meta_error

    def record_prediction_if_winner(self, winner_name: str, winner_topic: str,
                                     current_pressure: float,
                                     source_cycle_id: Optional[str] = None) -> None:
        """Call once per cycle, AFTER the competition winner is known. If
        resolve_uncertainty won, the self-model makes ITS OWN falsifiable
        prediction about how effective that choice will be — genuinely
        derived from the current effectiveness belief, not a fixed
        constant, so a self-model that has learned it's less effective
        predicts smaller drops going forward. Checks name/topic, not id —
        a real GoalEngine goal's id is never literally "resolve_uncertainty",
        only its name/topic is (matching the same check used elsewhere,
        e.g. internal_cognitive_state.is_self_regulatory_goal)."""
        text = f"{winner_name or ''} {winner_topic or ''}".lower().replace(" ", "_")
        if "resolve_uncertainty" not in text:
            return
        if not (self.last_application
                and self.last_application.get("applied_to_final_focus") is True):
            # A prediction about efficacy is only justified when the
            # learned multiplier was actually applied to the selected goal.
            return
        predicted_drop = self._confidence() * PREDICTION_SCALE
        prediction_id = f"epistemic-{time.time_ns()}"
        self._pending = PendingPrediction(
            predicted_drop=predicted_drop, pressure_before=current_pressure,
            made_at=time.time(), prediction_id=prediction_id,
            source_cycle_id=str(source_cycle_id or prediction_id),
            confidence_before=self._confidence(),
            competition_application=(dict(self.last_application)
                                     if self.last_application else None),
        )

    def record_competition_application(self, *, cycle_id: str,
                                       candidate: Optional[Dict[str, Any]],
                                       final_focus: Optional[str]) -> None:
        """Record whether the learned multiplier reached the selected focus."""
        if candidate is None:
            self.last_application = {
                "cycle_id": str(cycle_id), "eligible_candidate_present": False,
                "applied_to_final_focus": False, "final_focus": final_focus,
            }
            return
        name = str(candidate.get("name") or "")
        final_focus_key = str(final_focus or "").lower().replace(" ", "_")
        candidate_name_key = name.lower().replace(" ", "_")
        selected = (candidate_name_key == final_focus_key
                    and candidate.get("efficacy_multiplier_applied") is not None)
        self.last_application = {
            "cycle_id": str(cycle_id), "eligible_candidate_present": True,
            "candidate_id": str(candidate.get("id") or "")[:120],
            "candidate_score": candidate.get("score"),
            "candidate_score_without_efficacy": candidate.get("score_without_efficacy"),
            "score_delta_from_efficacy": (
                candidate.get("score", 0.0) - candidate.get("score_without_efficacy", 0.0)
                if isinstance(candidate.get("score"), (int, float))
                and isinstance(candidate.get("score_without_efficacy"), (int, float))
                else None
            ),
            "multiplier": candidate.get("efficacy_multiplier_applied"),
            "internal_alignment_baseline": candidate.get("internal_alignment_baseline"),
            "internal_alignment_actual": candidate.get("internal_bias"),
            "final_focus": str(final_focus or "")[:160],
            "applied_to_final_focus": selected,
        }

    def effectiveness_multiplier(self) -> float:
        """
        Scales resolve_uncertainty's own internal_alignment boost
        (workspace_competition.py) — THE causal crossing: an updated
        self-model changes future scoring of the very goal it's about.
        confidence=0.5 (neutral, unlearned) -> multiplier=1.0 (no change
        from today's v102/v103 behavior). Bounded both directions.
        """
        conf = self._confidence()
        mult = 0.4 + conf * 1.2  # confidence 0.5->1.0, 0.05->0.46, 0.95->1.54
        return max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, mult))


_models: Dict[int, EpistemicEfficacyModel] = {}


def get_epistemic_efficacy_model(organism: Any) -> Optional[EpistemicEfficacyModel]:
    existing = getattr(organism, "_epistemic_efficacy_model", None)
    if existing is not None:
        return existing
    # self_concept lives on ai_system, not directly on organism — verified
    # attribute path (v91 used the same lookup: getattr(getattr(organism,
    # "ai_system", None), "self_concept", None)). Getting this wrong here
    # would make the model permanently no-op (sc always None) without
    # ever raising an error to reveal it — exactly the class of bug this
    # whole project keeps finding, caught before shipping this time by
    # checking the real attribute path instead of assuming one.
    sc = getattr(getattr(organism, "ai_system", None), "self_concept", None)
    if sc is None:
        sc = getattr(organism, "self_concept", None)  # fallback for test
                                                         # harnesses that
                                                         # attach it directly
    if sc is None:
        return None
    model = EpistemicEfficacyModel(sc)
    try:
        organism._epistemic_efficacy_model = model
    except Exception:
        pass
    return model
