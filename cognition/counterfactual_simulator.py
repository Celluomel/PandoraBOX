"""
cognition/counterfactual_simulator.py  — Phase 3.3

CounterfactualSimulator: "What would have happened if I'd done X instead?"

Takes committed past interactions (ConsequenceRecords from PCM,
DynamicsRecords from WSDM) and retroactively queries PCM/WSDM's k-NN
prediction machinery against alternative action types, using the same
state_before / context_before vectors the actual interaction had.

Key design decisions:
  - Reuses PCM._predict() and WSDM._predict() directly — no new model.
    Both already accept arbitrary state vectors as input.
  - Weighted by calibrated confidence from Phase 3.1/3.2 (degrades
    gracefully to raw confidence before bins have filled).
  - Runs on consolidation cycle only, gated by MIN_RECORDS_FOR_CF and
    a minimum interval, because 7 action types × 10 interactions = 70
    k-NN lookups per trigger (cheap, but not free).
  - Does NOT modify PCM/WSDM — purely observational.
  - Primary output consumer: Phase 3.5 Introspective Observer.

Relationship to CognitiveImmuneSystem's "counterfactual mode":
  That is a defensive immune response to cognitive stagnation (inject
  opposing topics, bias toward disconfirmation). This is retroactive
  decision analysis ("was that action the best available?"). They are
  complementary and non-overlapping.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SAVE_PATH              = "data/persona/counterfactual_log.json"
MAX_LOG_ENTRIES        = 200     # keep last N completed queries
MIN_RECORDS_FOR_CF     = 15      # PCM records needed before simulator fires
MAX_RECENT_INTERACTIONS = 10     # how many past interactions to analyse per run
CF_INTERVAL_CYCLES     = 5       # consolidation cycles between runs (~50 min)
PCM_ENERGY_WEIGHT      = 0.55    # weight of PCM energy_delta in joint_score
WSDM_ENGAGEMENT_WEIGHT = 0.45    # weight of WSDM engagement_signal in joint_score
MIN_COUNTERFACTUAL_MARGIN = 0.02

ALL_ACTION_TYPES = [
    "philosophical", "technical", "emotional", "creative",
    "social", "analytical", "deep_reasoning",
]


@dataclass
class CounterfactualBranch:
    """One alternative action's predicted outcome for a past interaction."""
    action_type:        str
    pcm_energy_delta:   Optional[float]   # PCM predicted energy change
    pcm_confidence:     Optional[float]   # PCM raw confidence
    pcm_calibrated:     Optional[float]   # PCM calibrated confidence (None if uncal.)
    wsdm_engagement:    Optional[float]   # WSDM predicted engagement_signal
    wsdm_confidence:    Optional[float]   # WSDM raw confidence
    wsdm_calibrated:    Optional[float]   # WSDM calibrated confidence (None if uncal.)
    joint_score:        float             # composite ranking score
    was_actual:         bool = False      # True for the branch that actually happened
    score_basis:        List[str] = field(default_factory=list)
    ranking_eligible:   bool = False


@dataclass
class CounterfactualQuery:
    """One completed counterfactual analysis of a past interaction."""
    interaction_n:    int
    actual_action:    str
    actual_outcome:   str                                # positive/negative/neutral
    branches:         Dict[str, CounterfactualBranch]   # action_type -> branch
    best_alternative: Optional[str]      # highest joint_score non-actual branch
    actual_rank:      Optional[int]      # rank only when the comparison is meaningful
    worst_actual:     bool               # True if actual was lowest-scoring branch
    source_ref:       str = ""            # stable, content-free PCM record identity
    computed_at:      float = field(default_factory=time.time)
    evidence_status:  str = "model_prediction_only"
    ranking_status:   str = "not_ranked"
    ranking_margin:   Optional[float] = None


class CounterfactualSimulator:
    """
    Retroactively evaluates past interactions against alternative action
    types using PCM and WSDM's existing k-NN prediction machinery.
    """

    def __init__(self, organism: Any) -> None:
        self._organism = organism
        self._lock     = threading.Lock()
        self._run_guard = threading.Lock()
        self._schedule_lock = threading.Lock()
        self._run_pending = False
        self._log:     List[Dict] = []
        self._path     = Path(SAVE_PATH)
        self._last_run_cycle: int = -CF_INTERVAL_CYCLES  # fire on first eligible cycle
        self._calibration_engine = None
        self._load()

        try:
            from cognition.calibration_engine import CalibrationEngine
            self._calibration_engine = CalibrationEngine()
        except Exception as e:
            logger.debug(f"[CounterfactualSim] CalibrationEngine unavailable: {e}")

        logger.info(
            f"[CounterfactualSim] Initialised — {len(self._log)} past queries"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def tick(self, slow_cycle: int) -> Dict[str, Any]:
        """Called every slow cycle from InternalLoop. Runs analysis on
        consolidation cycles only, gated by interval and data readiness."""
        is_consolidation = (slow_cycle % 5 == 0 and slow_cycle > 0)
        if not is_consolidation:
            return self._tick_receipt(slow_cycle, "skipped", "not_consolidation_cycle")
        if slow_cycle - self._last_run_cycle < CF_INTERVAL_CYCLES:
            return self._tick_receipt(slow_cycle, "skipped", "interval_not_due")

        with self._schedule_lock:
            if self._run_pending:
                return self._tick_receipt(slow_cycle, "skipped", "analysis_already_running")
            self._run_pending = True
        try:
            threading.Thread(
                target=self._run_scheduled,
                args=(slow_cycle,),
                daemon=True,
                name="cf-simulator",
            ).start()
        except Exception:
            with self._schedule_lock:
                self._run_pending = False
            return self._tick_receipt(slow_cycle, "failed", "worker_start_failed")
        return self._tick_receipt(slow_cycle, "scheduled", "analysis_worker_started")

    @staticmethod
    def _tick_receipt(cycle: int, status: str, reason: str) -> Dict[str, Any]:
        return {
            "cycle": int(cycle),
            "outcome_status": status,
            "reason_code": reason,
            "worker_scheduled": status == "scheduled",
        }

    def _run_scheduled(self, slow_cycle: int) -> None:
        try:
            self._run(slow_cycle)
        finally:
            with self._schedule_lock:
                self._run_pending = False

    def recent_findings(self, n: int = 5) -> List[Dict]:
        """Return only counterfactuals with independently validated outcomes."""
        with self._lock:
            validated = [
                item for item in self._log
                if isinstance(item, dict)
                and item.get("evidence_status") == "outcome_validated"
            ]
            return list(validated[-n:])

    def recent_predictions(self, n: int = 5) -> List[Dict]:
        """Return model-only predictions for diagnostics, not as observed outcomes."""
        with self._lock:
            return list(self._log[-n:])

    def worst_actual_streak(self) -> int:
        """Number of consecutive independently outcome-validated worst choices."""
        with self._lock:
            return self._worst_actual_streak_locked()

    def _worst_actual_streak_locked(self) -> int:
        """Same logic as worst_actual_streak() but assumes self._lock is
        ALREADY held by the caller — never acquires it itself. Used by
        status() to avoid the exact re-entrant-lock deadlock found in
        TemporalProjection.status() earlier: a plain threading.Lock() is
        not reentrant, so a method holding it must never call another
        method that tries to acquire it again — that call blocks forever,
        and since it runs inside InternalLoop's single background thread
        (via tick() -> _run(), or via _fetch_all() in the dashboard's
        to_thread()), the entire background loop or the dashboard fetch
        hangs permanently with no exception and nothing in the logs."""
        streak = 0
        for entry in reversed(self._log):
            if (entry.get("evidence_status") == "outcome_validated"
                    and entry.get("worst_actual")):
                streak += 1
            else:
                break
        return streak

    def status(self) -> Dict:
        with self._lock:
            validated = [
                item for item in self._log
                if isinstance(item, dict)
                and item.get("evidence_status") == "outcome_validated"
            ]
            return {
                "total_queries": len(self._log),
                "worst_actual_streak": self._worst_actual_streak_locked(),
                "last_run_cycle": self._last_run_cycle,
                "recent": self._log[-3:] if self._log else [],
                "recent_validated": validated[-10:],
                "validated_query_count": len(validated),
            }

    # ── Core analysis ─────────────────────────────────────────────────────────

    def _run(self, slow_cycle: int) -> None:
        # A slow cycle can request another run before a previous background
        # analysis finishes. Serialize runs so they cannot append the same
        # PCM window concurrently.
        if not self._run_guard.acquire(blocking=False):
            return
        try:
            loop = getattr(self._organism, "_loop", None)
            if loop is None:
                return

            pcm  = getattr(loop, "_consequence_model", None)
            wsdm = getattr(loop, "_world_self_dynamics", None)

            if pcm is None:
                return
            if len(getattr(pcm, "_records", [])) < MIN_RECORDS_FOR_CF:
                return

            # Take the MAX_RECENT_INTERACTIONS most recent PCM records
            pcm_records = list(pcm._records)[-MAX_RECENT_INTERACTIONS:]
            wsdm_records = list(getattr(wsdm, "_records", []))

            with self._lock:
                processed_refs = {
                    str(item.get("source_ref") or "")
                    for item in self._log
                    if isinstance(item, dict) and item.get("source_ref")
                }

            # Build a lookup of WSDM records by interaction_n for fast pairing
            wsdm_by_n: Dict[int, Any] = {}
            for r in wsdm_records:
                n = getattr(r, "interaction_n", None)
                if n is not None:
                    wsdm_by_n[n] = r

            new_queries: List[CounterfactualQuery] = []
            for pcm_rec in pcm_records:
                source_ref = self._source_record_ref(pcm_rec)
                if source_ref in processed_refs:
                    continue
                query = self._analyse_interaction(pcm, wsdm, pcm_rec, wsdm_by_n)
                if query is not None:
                    query.source_ref = source_ref
                    new_queries.append(query)
                    processed_refs.add(source_ref)

            if new_queries:
                with self._lock:
                    for q in new_queries:
                        self._log.append(asdict(q))
                    if len(self._log) > MAX_LOG_ENTRIES:
                        self._log = self._log[-MAX_LOG_ENTRIES:]
                self._save()

                worst_streak = self.worst_actual_streak()
                logger.info(
                    f"[CounterfactualSim] Cycle {slow_cycle}: analysed "
                    f"{len(new_queries)} interactions. "
                    f"Worst-actual streak: {worst_streak}"
                )

            self._last_run_cycle = slow_cycle

        except Exception as e:
            logger.debug(f"[CounterfactualSim] _run error: {e}")
        finally:
            self._run_guard.release()

    @staticmethod
    def _source_record_ref(record: Any) -> str:
        """Stable hash for one persisted PCM interaction, without exposing text."""
        import hashlib
        import json

        payload = {
            "interaction_n": getattr(record, "interaction_n", 0),
            "recorded_at": getattr(record, "recorded_at", None),
            "response_hash": getattr(record, "response_hash", ""),
            "action_type": getattr(record, "action_type", ""),
            "state_before": getattr(record, "state_before", []),
            "outcome": getattr(record, "outcome", "unrated"),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]

    def _analyse_interaction(
        self,
        pcm:       Any,
        wsdm:      Optional[Any],
        pcm_rec:   Any,
        wsdm_by_n: Dict[int, Any],
    ) -> Optional[CounterfactualQuery]:
        """Build a CounterfactualQuery for one past interaction."""
        try:
            actual_action  = pcm_rec.action_type
            state_before   = pcm_rec.state_before
            actual_outcome = pcm_rec.outcome
            interaction_n  = getattr(pcm_rec, "interaction_n", 0)

            wsdm_rec      = wsdm_by_n.get(interaction_n)
            ctx_before    = (
                getattr(wsdm_rec, "context_before", None)
                if wsdm_rec else None
            )

            branches: Dict[str, CounterfactualBranch] = {}
            for action_type in ALL_ACTION_TYPES:
                branch = self._predict_branch(
                    pcm, wsdm, action_type, state_before, ctx_before,
                    was_actual=(action_type == actual_action),
                )
                branches[action_type] = branch

            # A PCM energy estimate is an internal resource-cost prediction,
            # not evidence that a conversational framing is better. Require
            # both that estimate and independent WSDM engagement data before
            # ranking alternatives. Missing engagement must not become a zero
            # score that wins ties by action-list order.
            ranked = sorted(
                (b for b in branches.values() if b.ranking_eligible),
                key=lambda b: b.joint_score,
                reverse=True,
            )
            actual_branch = next((b for b in ranked if b.was_actual), None)
            alternatives = [b for b in ranked if not b.was_actual]
            actual_rank = None
            best_alternative = None
            worst_actual = False
            ranking_status = "insufficient_prediction_evidence"
            ranking_margin = None
            if actual_branch is not None and alternatives:
                ranked_all = sorted(ranked, key=lambda b: b.joint_score, reverse=True)
                actual_rank = next(
                    i + 1 for i, branch in enumerate(ranked_all) if branch.was_actual
                )
                if any(
                    branch is not actual_branch
                    and abs(branch.joint_score - actual_branch.joint_score)
                    < MIN_COUNTERFACTUAL_MARGIN
                    for branch in ranked_all
                ):
                    actual_rank = None
                alternatives.sort(key=lambda b: b.joint_score, reverse=True)
                best_candidate = alternatives[0]
                runner_up_score = (
                    alternatives[1].joint_score if len(alternatives) > 1
                    else float("-inf")
                )
                margin_over_runner_up = best_candidate.joint_score - runner_up_score
                margin_over_actual = best_candidate.joint_score - actual_branch.joint_score
                ranking_margin = round(margin_over_actual, 5)
                if (margin_over_runner_up >= MIN_COUNTERFACTUAL_MARGIN
                        and margin_over_actual >= MIN_COUNTERFACTUAL_MARGIN):
                    best_alternative = best_candidate.action_type
                    ranking_status = "prediction_only_clear_alternative"
                else:
                    ranking_status = "prediction_only_no_clear_winner"
                    actual_rank = None

                lowest = ranked_all[-1]
                second_lowest = ranked_all[-2] if len(ranked_all) > 1 else None
                worst_actual = bool(
                    lowest.was_actual and second_lowest is not None
                    and second_lowest.joint_score - lowest.joint_score
                    >= MIN_COUNTERFACTUAL_MARGIN
                )

            return CounterfactualQuery(
                interaction_n    = interaction_n,
                actual_action    = actual_action,
                actual_outcome   = actual_outcome,
                branches         = branches,
                best_alternative = best_alternative,
                actual_rank      = actual_rank,
                worst_actual     = worst_actual,
                source_ref       = self._source_record_ref(pcm_rec),
                evidence_status  = "model_prediction_only",
                ranking_status   = ranking_status,
                ranking_margin   = ranking_margin,
            )

        except Exception as e:
            logger.debug(f"[CounterfactualSim] _analyse_interaction error: {e}")
            return None

    def _predict_branch(
        self,
        pcm:          Any,
        wsdm:         Optional[Any],
        action_type:  str,
        state_before: List[float],
        ctx_before:   Optional[List[float]],
        was_actual:   bool,
    ) -> CounterfactualBranch:
        """Get PCM and WSDM predictions for one hypothetical action type."""

        # ── PCM prediction ──────────────────────────────────────────────────
        pcm_energy   = None
        pcm_conf_raw = None
        pcm_conf_cal = None
        try:
            pcm_pred = pcm._predict(action_type, state_before)
            if pcm_pred is not None:
                pcm_energy   = round(float(pcm_pred.energy_delta), 4)
                pcm_conf_raw = round(float(pcm_pred.confidence), 4)
                if self._calibration_engine:
                    cal_val, is_cal = self._calibration_engine.calibrated_confidence(
                        "pcm", pcm_conf_raw
                    )
                    pcm_conf_cal = round(cal_val, 4) if is_cal else None
        except Exception as e:
            logger.debug(f"[CounterfactualSim] PCM predict error ({action_type}): {e}")

        # ── WSDM prediction ─────────────────────────────────────────────────
        wsdm_engage  = None
        wsdm_conf_raw = None
        wsdm_conf_cal = None
        try:
            wsdm_ready = (wsdm is not None and ctx_before is not None and
                          len(getattr(wsdm, "_records", [])) >= 6)
            if wsdm_ready:
                wsdm_pred = wsdm._predict(action_type, ctx_before)
                if wsdm_pred is not None:
                    engagement = wsdm_pred.world_deltas.get("engagement_signal")
                    wsdm_engage = round(float(engagement), 4) if engagement is not None else None
                    wsdm_conf_raw = round(float(wsdm_pred.confidence), 4)
                    if self._calibration_engine:
                        cal_val, is_cal = self._calibration_engine.calibrated_confidence(
                            "wsdm", wsdm_conf_raw
                        )
                        wsdm_conf_cal = round(cal_val, 4) if is_cal else None
        except Exception as e:
            logger.debug(f"[CounterfactualSim] WSDM predict error ({action_type}): {e}")

        # ── Joint score: weighted combination, calibrated where available ───
        eff_pcm_conf  = pcm_conf_cal if pcm_conf_cal is not None else (pcm_conf_raw or 0.5)
        eff_wsdm_conf = wsdm_conf_cal if wsdm_conf_cal is not None else (wsdm_conf_raw or 0.5)
        pcm_term  = (pcm_energy or 0.0)   * eff_pcm_conf  * PCM_ENERGY_WEIGHT
        wsdm_term = (wsdm_engage or 0.0)  * eff_wsdm_conf * WSDM_ENGAGEMENT_WEIGHT
        joint_score = round(pcm_term + wsdm_term, 5)

        return CounterfactualBranch(
            action_type    = action_type,
            pcm_energy_delta = pcm_energy,
            pcm_confidence   = pcm_conf_raw,
            pcm_calibrated   = pcm_conf_cal,
            wsdm_engagement  = wsdm_engage,
            wsdm_confidence  = wsdm_conf_raw,
            wsdm_calibrated  = wsdm_conf_cal,
            joint_score      = joint_score,
            was_actual        = was_actual,
            score_basis      = [
                source for source, value, confidence in (
                    ("pcm_energy", pcm_energy, pcm_conf_raw),
                    ("wsdm_engagement", wsdm_engage, wsdm_conf_raw),
                ) if value is not None and confidence is not None
            ],
            ranking_eligible = (
                pcm_energy is not None and pcm_conf_raw is not None
                and wsdm_engage is not None and wsdm_conf_raw is not None
            ),
        )

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._path.exists():
                d = json.loads(self._path.read_text())
                self._log = d.get("queries", [])
        except Exception as e:
            logger.debug(f"[CounterfactualSim] load error: {e}")

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"queries": self._log, "last_written": time.time()}
            _tmp = self._path.with_suffix(".json.tmp")
            _tmp.write_text(json.dumps(payload, indent=2))
            _tmp.replace(self._path)
        except Exception as e:
            logger.debug(f"[CounterfactualSim] save error: {e}")
