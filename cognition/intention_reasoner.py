"""Structured, inspectable reasoning for committed cognitive intentions.

This module records concise deliberation summaries, not hidden token-level
model reasoning. It records available operation hypotheses and preserves the
evidence, uncertainty and sequence the planner actually used. Until outcomes
are independently measured per planner operation, it does not transfer broad
conversation-class dynamics into operation-specific predictions.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SAVE_PATH = "data/persona/reasoning_episodes.json"
MAX_EPISODES = 200

# These are transparent fallback heuristics, not learned performance data.
# WSDM records interaction-level conversational classes and broad state deltas;
# it does not contain matched outcomes for these planner operations. Mapping
# e.g. ``memory_recall`` to ``analytical`` would transfer unrelated evidence.
OPERATION_PRIORS = {
    "memory_recall": (0.02, 0.025, 0.38),
    "self_question": (0.05, 0.040, 0.34),
    "bisociative_hypothesis": (0.07, 0.050, 0.28),
    "web_search": (0.08, 0.065, 0.32),
    "user_question": (0.03, 0.060, 0.42),
}


@dataclass
class ReasoningEvidence:
    source: str
    claim: str
    confidence: float


@dataclass
class ReasoningHypothesis:
    operation: str
    statement: str
    expected_cost: float
    expected_gain: float
    confidence: float
    score: float
    evidence_source: str


@dataclass
class ReasoningEpisode:
    id: str
    intention_id: str
    question: str
    evidence: List[ReasoningEvidence]
    hypotheses: List[ReasoningHypothesis]
    selected_operation: str
    recommended_sequence: List[str]
    conclusion: str
    decision_rationale: str
    confidence: float
    uncertainties: List[str]
    confidence_semantics: str = (
        "uncalibrated decision-support score from operation priors; not probability"
    )
    status: str = "decided"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    outcomes: List[Dict[str, Any]] = field(default_factory=list)
    initial_confidence: float = 0.0


class IntentionReasoner:
    """Record candidate operations and learn only from measured effects."""

    def __init__(self, organism: Any, path: str = SAVE_PATH):
        self._organism = organism
        self._path = Path(path)
        self._lock = RLock()
        self._episodes: Dict[str, ReasoningEpisode] = {}
        self._load()

    def deliberate(self, goal: Any, operations: List[str]) -> ReasoningEpisode:
        goal_id = str(getattr(goal, "id", "unknown"))
        topic = str(getattr(goal, "topic", "an unresolved goal"))
        origin = str(getattr(goal, "origin", "unknown"))
        context = self._read_context()

        evidence = [
            ReasoningEvidence(
                source="goal_engine",
                claim=f"The active goal originates from {origin} and concerns: {topic}",
                confidence=float(getattr(goal, "priority", 0.5)),
            )
        ]
        if context:
            evidence.extend([
                ReasoningEvidence(
                    source="resource_economy",
                    claim=f"Current cognitive energy is {context[0]:.2f}",
                    confidence=1.0,
                ),
                ReasoningEvidence(
                    source="relational_state",
                    claim=f"Current user trust context is {context[5]:.2f}",
                    confidence=0.8,
                ),
            ])

        hypotheses = [self._evaluate(operation, context) for operation in operations]

        # Recall is an evidential prerequisite, not merely another competing
        # tactic. Keep it first; preserve the caller's declared order otherwise.
        sequence: List[str] = []
        if "memory_recall" in operations:
            sequence.append("memory_recall")
        sequence.extend(operation for operation in operations if operation not in sequence)

        selected = sequence[0] if sequence else operations[0]
        selected_hypothesis = next(
            item for item in hypotheses if item.operation == selected
        )
        mean_confidence = sum(item.confidence for item in hypotheses) / max(1, len(hypotheses))
        uncertainties: List[str] = []
        uncertainties.append(
            "No independently measured outcomes are matched to these planner operations; declared operation order is used"
        )
        uncertainties.append(
            "Decision-support scores use unvalidated operation priors; they are not calibrated probabilities"
        )
        if mean_confidence < 0.5:
            uncertainties.append("The decision-support score is low and is not a calibrated probability")

        rationale = (
            f"Begin with {selected} as the evidential prerequisite; then retain the "
            "planner's declared operation order because matched, independently measured "
            "outcomes are not available for ranking alternatives."
        )
        episode = ReasoningEpisode(
            id=f"reason-{uuid.uuid4().hex[:12]}",
            intention_id=f"goal:{goal_id}",
            question=f"Which sequence is most likely to make grounded progress on: {topic}?",
            evidence=evidence,
            hypotheses=hypotheses,
            selected_operation=selected,
            recommended_sequence=sequence,
            conclusion=f"Use the ordered strategy: {' -> '.join(sequence)}",
            decision_rationale=rationale,
            confidence=round(mean_confidence, 3),
            uncertainties=uncertainties,
            initial_confidence=round(mean_confidence, 3),
        )
        with self._lock:
            self._episodes[episode.id] = episode
            self._prune()
            self._save_locked()
        logger.info(
            "[IntentionReasoner] %s | support_score_uncalibrated=%.2f | %s",
            episode.intention_id, episode.confidence, episode.conclusion,
        )
        self._broadcast(
            "intention_reasoner",
            f"[IntentionDecision] goal='{topic[:60]}'; selected={selected}; "
            f"sequence={' -> '.join(sequence)}; support_score_uncalibrated={episode.confidence:.2f}",
            0.58,
        )
        if uncertainties:
            self._broadcast(
                "intention_reasoner.uncertainty",
                f"[ReasoningUncertainty] goal='{topic[:60]}'; {uncertainties[0][:120]}",
                0.64,
            )
        return episode

    def record_outcome(
        self, episode_id: str, operation: str, success: bool, result: str,
        *, effect_measured: bool = False,
    ) -> Optional[ReasoningEpisode]:
        """Record an action receipt; validate the reasoning only with a measured effect."""
        with self._lock:
            episode = self._episodes.get(episode_id)
            if episode is None:
                return None
            if effect_measured and episode.initial_confidence <= 0.0:
                episode.initial_confidence = episode.confidence
            episode.outcomes.append({
                "operation": operation,
                "success": bool(success) if effect_measured else None,
                "execution_success": bool(success),
                "effect_measured": bool(effect_measured),
                "result": str(result)[:240],
                "observed_at": time.time(),
            })
            episode.updated_at = time.time()
            episode.status = (
                ("validated" if success else "revision_needed")
                if effect_measured else "outcome_unverified"
            )
            episode.evidence.append(ReasoningEvidence(
                source="measured_outcome" if effect_measured else "action_execution_receipt",
                claim=(
                    (f"Measured effect: {operation} succeeded: " if success else f"Measured effect: {operation} failed: ")
                    if effect_measured else
                    (f"Execution receipt: {operation} completed; target effect was not measured: "
                     if success else
                     f"Execution receipt: {operation} failed; target effect was not measured: ")
                ) + str(result)[:150],
                confidence=1.0 if effect_measured else 0.5,
            ))
            measured_outcomes = [
                item for item in episode.outcomes if item.get("effect_measured") is True
            ]
            if measured_outcomes:
                successes = sum(1 for item in measured_outcomes if item.get("success"))
                total = len(measured_outcomes)
                observed_reliability = (successes + 1.0) / (total + 2.0)
                episode.confidence = round(
                    max(0.1, min(0.95,
                        episode.initial_confidence * 0.65 + observed_reliability * 0.35
                    )),
                    3,
                )
            self._save_locked()
        self._broadcast(
            "intention_reasoner.outcome" if effect_measured else "intention_reasoner.execution_receipt",
            f"[ReasoningOutcome] intention={episode.intention_id}; "
            f"operation={operation}; execution={'success' if success else 'failure'}; "
            f"effect={'measured' if effect_measured else 'unverified'}",
            0.54 if success and effect_measured else 0.62,
        )
        return episode

    def update_decision(
        self,
        episode_id: str,
        rationale: str,
        uncertainties: List[str],
        status: str,
    ) -> Optional[ReasoningEpisode]:
        """Synchronize the recorded reasoning with the planner's operative decision."""
        with self._lock:
            episode = self._episodes.get(episode_id)
            if episode is None:
                return None
            episode.decision_rationale = str(rationale)[:500]
            episode.uncertainties = list(dict.fromkeys(uncertainties))[:6]
            episode.status = status
            episode.updated_at = time.time()
            self._save_locked()
            return episode

    def get(self, episode_id: str) -> Optional[ReasoningEpisode]:
        return self._episodes.get(episode_id)

    def latest_summary(self) -> str:
        if not self._episodes:
            return ""
        episode = max(self._episodes.values(), key=lambda item: item.updated_at)
        uncertainty = episode.uncertainties[0] if episode.uncertainties else "none material"
        return (
            f"[Reasoning] {episode.conclusion}. Confidence={episode.confidence:.2f}; "
            f"uncertainty: {uncertainty}."
        )

    def _broadcast(self, source: str, content: str, priority: float) -> None:
        """Publish a compact reasoning artifact to the shared workspace."""
        try:
            workspace = getattr(self._organism, "workspace", None)
            if workspace is not None and hasattr(workspace, "broadcast"):
                workspace.broadcast(
                    source=source,
                    content=content[:240],
                    priority=max(0.0, min(0.75, priority)),
                )
        except Exception as exc:
            logger.debug("[IntentionReasoner] workspace broadcast failed: %s", exc)

    def _read_context(self) -> Optional[List[float]]:
        try:
            loop = getattr(self._organism, "_loop", None)
            model = getattr(loop, "_world_self_dynamics", None) if loop else None
            return model.read_state() if model is not None else None
        except Exception as exc:
            logger.debug("[IntentionReasoner] context unavailable: %s", exc)
            return None

    def _evaluate(
        self, operation: str, context: Optional[List[float]]
    ) -> ReasoningHypothesis:
        cost, gain, confidence = OPERATION_PRIORS.get(operation, (0.06, 0.03, 0.25))
        source = "unvalidated_operation_prior"

        score = ((gain + 0.02) * confidence) / max(cost, 0.01)
        return ReasoningHypothesis(
            operation=operation,
            statement=(
                f"Heuristic prior only: {operation} is an available step; "
                "its effect on the intention has not been measured"
            ),
            expected_cost=round(cost, 4),
            expected_gain=round(gain, 4),
            confidence=round(confidence, 3),
            score=round(score, 4),
            evidence_source=source,
        )

    def _prune(self) -> None:
        if len(self._episodes) <= MAX_EPISODES:
            return
        oldest = sorted(self._episodes.values(), key=lambda item: item.updated_at)
        for episode in oldest[:len(self._episodes) - MAX_EPISODES]:
            self._episodes.pop(episode.id, None)

    def _save_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "episodes": {key: asdict(value) for key, value in self._episodes.items()},
            "_meta": {"version": "v1", "updated_at": time.time()},
        }
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            migrated = False
            for key, value in raw.get("episodes", {}).items():
                value["evidence"] = [ReasoningEvidence(**item) for item in value.get("evidence", [])]
                value["hypotheses"] = [
                    ReasoningHypothesis(**item) for item in value.get("hypotheses", [])
                ]
                value.setdefault("initial_confidence", value.get("confidence", 0.0))
                outcomes = value.get("outcomes", [])
                legacy_outcomes = [
                    item for item in outcomes
                    if isinstance(item, dict) and "effect_measured" not in item
                ]
                if legacy_outcomes:
                    for item in legacy_outcomes:
                        item["execution_success"] = item.get("success")
                        item["success"] = None
                        item["effect_measured"] = False
                    for evidence in value["evidence"]:
                        if evidence.source == "verified_outcome":
                            evidence.source = "action_execution_receipt"
                            evidence.confidence = min(float(evidence.confidence), 0.5)
                            evidence.claim = (
                                "Legacy action execution receipt; effect was not measured: "
                                + str(evidence.claim)[:150]
                            )
                    value["status"] = "outcome_unverified"
                    initial = float(value.get("initial_confidence", 0.0) or 0.0)
                    if initial > 0.0:
                        value["confidence"] = initial
                    migrated = True
                self._episodes[key] = ReasoningEpisode(**value)
            if migrated:
                with self._lock:
                    self._save_locked()
                logger.info(
                    "[IntentionReasoner] Migrated legacy action outcomes to unverified execution receipts"
                )
        except Exception as exc:
            logger.warning("[IntentionReasoner] load failed: %s", exc)
