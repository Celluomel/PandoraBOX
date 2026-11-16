"""
cognition/cognitive_audit_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CognitiveAuditEngine (v48) — self-directed development.

The gap this closes
────────────────────
v47 (AutonomousExperimentationEngine) tests behavioural hypotheses against
interaction outcomes.

That's learning from interactions.  What v47 cannot do is look at the
cognitive architecture itself and ask:

  "A measured outcome is below its target across repeated audits.
   Is there a parameter with a validated causal link to that outcome?"

That is self-directed development: observe self → find weakness →
propose change → experiment → measure → retain.

Architecture
────────────
  CognitiveAuditEngine collects diagnostic signals every AUDIT_EVERY_N slow
  cycles (~80 min). It currently has no validated performance targets:

    1. epistemic_grounding_rate — compatibility screen over reflection outputs;
       not an independent truth check.
       Source: AutonomousReflectionEngine._epistemic._recent_grounding_rate()

    2. question_resolution_rate — resolved / (resolved + unresolvable), where
       "resolved" is assigned from the answering LLM's self-reported confidence.
       Source: ResolutionEngine._state

    3. mean_skill_depth — average depth score across known skills; depth is
       derived from practice-count thresholds, not a direct ability test.
       Source: SkillRegistry._skills

  Mean belief confidence is retained as a descriptive diagnostic only. Without
  matching confidence values to independently verified correctness, raising
  average confidence is not evidence of better calibration or reasoning.
  Experiment confirmation and resolution rates are also descriptive; neither
  establishes the cognitive quality of the underlying hypotheses.

  These values remain descriptive until independent, predeclared outcome
  measures are implemented. No deficit or self-tuning proposal is currently
  authorized from them.

Proposal generation
────────────────────
  An LLM call (temperature 0.50, deliberate) receives the underperforming
  signal and only parameters with an explicitly validated causal mapping to
  that signal. If no such parameter exists, the engine records that limitation
  and does not mutate a live module global. Code independently enforces the
  mapping, parameter bounds, and maximum change.

  The proposed change is applied immediately to the live module globals
  (no restart required) and written to data/persona/cognitive_params.json
  under "trial".

Trial evaluation
────────────────
  After TRIAL_DURATION_CYCLES slow cycles the engine re-reads the
  underperforming signal:
    - Improved by ≥ CONFIRM_THRESHOLD → proposal committed permanently.
      The parameter value is written to cognitive_params.json "params"
      and the module global is left at the new value.
    - Degraded by ≥ DISCONFIRM_THRESHOLD → proposal reverted.
      Module global is reset to prior value.
    - Otherwise → inconclusive; reverted (conservative default).

  All trials, outcomes, and committed changes are logged.

Cognitive parameter space
─────────────────────────
  Only six parameters are currently tunable.  Each has hard bounds to
  prevent runaway self-modification:

    resolve_every_n        int   [5, 50]    default 15
    generate_every_n       int   [10, 60]   default 25
    decay_rate_base        float [0.002, 0.025]  default 0.008
    grounding_boost        float [0.010, 0.080]  default 0.030
    curiosity_halflife_hrs float [12.0, 96.0]    default 48.0
    reflection_every_n     int   [3, 15]    default 6

  These map to module-level constants that the audit engine writes at
  runtime via Python module-namespace mutation — no restart required.

Safety constraints
──────────────────
  - MAX_PARAM_CHANGE_PCT = 0.30 (30% max per trial, in either direction)
  - ONE trial at a time — a new proposal cannot start while one is active
  - Parameters revert on inconclusive outcomes (conservative default)
  - Full audit history persisted to cognitive_params.json
  - All changes are human-readable and auditable
  - LLM priority = 3, skip_if_busy — audit never blocks interaction

What PandoraBOX can truthfully say about v48
─────────────────────────────────────────
  "My cognitive audit identified underperformance in [signal], proposed
   a calibration change to [parameter], tested it for [N] slow cycles,
   and the [confirmed/reverted] outcome [was committed/was discarded]."

  That is a precise, accurate description of what happened.  Nothing
  more is claimed.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from cognition.cognitive_organism import CognitiveOrganism

logger = logging.getLogger(__name__)

# ── Timing ────────────────────────────────────────────────────────────────────
AUDIT_EVERY_N           = 40   # slow cycles between audits (~80 min)
TRIAL_DURATION_CYCLES   = 60   # slow cycles a trial runs before evaluation (~2 hrs)

# ── Thresholds for outcome classification ────────────────────────────────────
CONFIRM_THRESHOLD       = 0.10  # signal must improve by ≥10% of target to confirm
DISCONFIRM_THRESHOLD    = 0.05  # signal degraded by ≥5% of target to disconfirm

# ── Signal targets (the values we are aiming for) ─────────────────────────────
SIGNAL_TARGETS = {
    # Intentionally empty: the current observations are diagnostics, not
    # independently verified measures of cognitive quality.
}

# ── Cognitive parameter space (name → (default, min, max, type)) ──────────────
PARAM_SPACE: Dict[str, Tuple[Any, Any, Any, type]] = {
    "resolve_every_n":        (15,   5,    50,   int),
    "generate_every_n":       (25,   10,   60,   int),
    "decay_rate_base":        (0.008, 0.002, 0.025, float),
    "grounding_boost":        (0.030, 0.010, 0.080, float),
    "curiosity_halflife_hrs": (48.0,  12.0,  96.0,  float),
    "reflection_every_n":     (6,    3,    15,   int),
}

# ── Module paths for live global mutation ────────────────────────────────────
# Maps param name → (module_path, global_name)
PARAM_MODULE_MAP: Dict[str, Tuple[str, str]] = {
    "resolve_every_n":        ("cognition.resolution_engine",            "RESOLVE_EVERY_N"),
    "generate_every_n":       ("cognition.autonomous_experimentation",   "GENERATE_EVERY_N"),
    "decay_rate_base":        ("cognition.epistemic_integrity_engine",   "DECAY_RATE_BASE"),
    "grounding_boost":        ("cognition.epistemic_integrity_engine",   "GROUNDING_BOOST"),
    "curiosity_halflife_hrs": ("cognition.curiosity_engine",             "CURIOSITY_HALFLIFE_HOURS"),
    "reflection_every_n":     ("core.internal_loop",                     "REFLECTION_EVERY_N"),
}

# A parameter may only be trialed against a signal it can directly affect.
# Frequency knobs can alter sample volume, but do not establish a causal
# improvement in confirmation/resolution rates or verified skill depth.
# No parameter is currently safe to tune against these aggregate metrics.
# In particular, changing confidence weights to raise mean belief confidence
# would optimize confidence, not correctness. Add a mapping only after a
# predeclared outcome measure establishes the causal link.
SIGNAL_PARAMETER_MAP: Dict[str, Tuple[str, ...]] = {}

MAX_AUDIT_LOG   = 50
MAX_TRIAL_LOG   = 30


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class SignalSnapshot:
    """One audit's worth of performance readings."""
    slow_cycle:                    int
    timestamp:                     float
    signal_status:                 Dict[str, str] = field(default_factory=dict)
    signal_sample_count:           Dict[str, int] = field(default_factory=dict)
    epistemic_grounding_rate:      Optional[float] = None
    experiment_confirmation_rate:  Optional[float] = None
    experiment_resolution_rate:    Optional[float] = None
    question_resolution_rate:     Optional[float] = None
    mean_skill_depth:              Optional[float] = None
    belief_confidence_mean:        Optional[float] = None

    def as_dict(self) -> Dict[str, Optional[float]]:
        return {
            "epistemic_grounding_rate":     self.epistemic_grounding_rate,
            "experiment_confirmation_rate": self.experiment_confirmation_rate,
            "experiment_resolution_rate":    self.experiment_resolution_rate,
            "question_resolution_rate":     self.question_resolution_rate,
            "mean_skill_depth":             self.mean_skill_depth,
            "belief_confidence_mean":       self.belief_confidence_mean,
        }

    def deficit(self) -> Dict[str, float]:
        """Return measured gaps only; unavailable signals are not zeroes."""
        d = {}
        for name, target in SIGNAL_TARGETS.items():
            current = getattr(self, name, None)
            if current is not None:
                d[name] = current - target
        return d

    def worst_signal(self) -> Optional[str]:
        """Name of the most underperforming signal, or None if all on target."""
        gaps = self.deficit()
        if not gaps:
            return None
        worst = min(gaps, key=gaps.get)
        if gaps[worst] < 0:
            return worst
        return None


@dataclass
class DevelopmentProposal:
    """One proposed cognitive parameter change, with trial tracking."""
    dimension:           str    # underperforming signal name
    signal_at_proposal:  float  # signal value when proposal was made
    signal_target:       float  # target value for that signal
    parameter:           str    # which param to change
    prior_value:         Any    # value before change
    proposed_value:      Any    # new value to trial
    rationale:           str    # LLM-generated explanation
    proposed_at_cycle:   int
    proposed_at_time:    float  = field(default_factory=time.time)
    outcome:             str    = "pending"   # "confirmed"|"disconfirmed"|"inconclusive"|"pending"
    signal_at_eval:      Optional[float] = None
    signal_sample_count_at_eval: int = 0
    evaluated_at_cycle:  int    = 0
    committed:           bool   = False


@dataclass
class AuditState:
    """Persisted state for the CognitiveAuditEngine."""
    last_audit_cycle:    int               = 0
    snapshot_log:        List[Dict]        = field(default_factory=list)
    active_trial:        Optional[Dict]    = None   # serialised DevelopmentProposal
    trial_log:           List[Dict]        = field(default_factory=list)
    committed_params:    Dict[str, Any]    = field(default_factory=dict)
    # Keep proposal attempts separate from completed trials. A skipped or
    # invalid proposal is not a trial, but must remain inspectable.
    proposal_attempt_log: List[Dict]       = field(default_factory=list)
    last_proposal_attempt: Optional[Dict]  = None
    proposal_attempt_total: int            = 0
    # track consecutive underperformance per signal (key → count)
    consecutive_under:   Dict[str, int]    = field(default_factory=dict)


# ── Engine ────────────────────────────────────────────────────────────────────

class CognitiveAuditEngine:
    """
    Monitors cognitive performance signals, proposes parameter calibrations,
    and evaluates whether those calibrations improved the underperforming signal.

    Usage (from InternalThoughtLoop slow cycle):
        cae = CognitiveAuditEngine(organism, ai_system)
        cae.tick(slow_cycle_count)
    """

    def __init__(
        self,
        organism:   "CognitiveOrganism",
        ai_system:  Any,
        path:       str = "data/persona/cognitive_params.json",
    ) -> None:
        self._organism  = organism
        self._ai        = ai_system
        self._path      = Path(path)
        self._state     = AuditState()
        self._lock      = threading.Lock()
        self._trial_evaluation_in_progress = False
        self._audit_in_progress = False
        self._process_started_at = time.time()
        self._proposal_attempt_status = "not_started"
        self._proposal_attempt_detail = ""
        self._load()
        self._recover_incompatible_active_trial()
        self._apply_committed_params()
        logger.info(
            f"[CognitiveAudit] Initialised — "
            f"{len(self._state.trial_log)} past trials, "
            f"{len(self._state.committed_params)} committed params"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def tick(self, slow_cycle: int) -> Dict[str, Any]:
        """Called every slow cycle from InternalThoughtLoop."""
        try:
            # 1. Evaluate any active trial first
            trial_to_evaluate = None
            with self._lock:
                raw_trial = self._state.active_trial
                if raw_trial:
                    trial = DevelopmentProposal(**raw_trial)
                    if slow_cycle - trial.proposed_at_cycle >= TRIAL_DURATION_CYCLES:
                        post_trial_samples = [
                            item for item in self._state.snapshot_log
                            if item.get("slow_cycle", 0) > trial.proposed_at_cycle
                            and item.get(trial.dimension) is not None
                            and (item.get("signal_status") or {}).get(trial.dimension)
                            in {"measured", "measured_legacy_snapshot"}
                        ]
                        if len(post_trial_samples) >= 2 and not self._trial_evaluation_in_progress:
                            self._trial_evaluation_in_progress = True
                            trial_to_evaluate = trial
                        elif self._trial_evaluation_in_progress:
                            return self._tick_receipt(slow_cycle, "skipped", "trial_evaluation_running")
                elif self._trial_evaluation_in_progress:
                    return self._tick_receipt(slow_cycle, "skipped", "trial_evaluation_running")

            if trial_to_evaluate is not None:
                try:
                    threading.Thread(
                        target=self._evaluate_trial_once,
                        args=(trial_to_evaluate, slow_cycle),
                        daemon=True,
                        name="cae-evaluate",
                    ).start()
                except Exception:
                    with self._lock:
                        self._trial_evaluation_in_progress = False
                    raise
                return self._tick_receipt(slow_cycle, "scheduled", "trial_evaluation_started")

            # 2. Run audit on schedule
            if slow_cycle % AUDIT_EVERY_N != 0 or slow_cycle == 0:
                return self._tick_receipt(slow_cycle, "skipped", "audit_cadence_not_due")

            with self._lock:
                if self._audit_in_progress:
                    return self._tick_receipt(slow_cycle, "skipped", "audit_already_running")
                self._audit_in_progress = True

            try:
                threading.Thread(
                    target=self._run_audit_scheduled,
                    args=(slow_cycle,),
                    daemon=True,
                    name="cae-audit",
                ).start()
            except Exception:
                with self._lock:
                    self._audit_in_progress = False
                raise
            return self._tick_receipt(slow_cycle, "scheduled", "audit_worker_started")

        except Exception as e:
            logger.debug(f"[CognitiveAudit] tick error (non-fatal): {e}")
            return self._tick_receipt(slow_cycle, "failed", "worker_start_failed")

    @staticmethod
    def _tick_receipt(cycle: int, status: str, reason: str) -> Dict[str, Any]:
        return {
            "cycle": int(cycle),
            "outcome_status": status,
            "reason_code": reason,
            "worker_scheduled": status == "scheduled",
        }

    def _run_audit_scheduled(self, slow_cycle: int) -> None:
        with self._lock:
            snapshots_before = len(self._state.snapshot_log)
            attempts_before = self._state.proposal_attempt_total
            trials_before = len(self._state.trial_log)
        try:
            self._run_audit(slow_cycle)
            with self._lock:
                snapshot_delta = len(self._state.snapshot_log) - snapshots_before
                attempt_delta = self._state.proposal_attempt_total - attempts_before
                trial_delta = len(self._state.trial_log) - trials_before
                last_cycle = int(self._state.last_audit_cycle)
                active_trial = bool(self._state.active_trial)
                proposal_status = str(
                    (self._state.last_proposal_attempt or {}).get("status", "none")
                )
            status = "completed" if last_cycle == int(slow_cycle) and snapshot_delta else "no_output"
            self._record_async_completion(
                slow_cycle,
                status,
                {
                    "snapshot_delta": snapshot_delta,
                    "proposal_attempt_delta": attempt_delta,
                    "trial_delta": trial_delta,
                    "active_trial": active_trial,
                    "proposal_status": proposal_status,
                    "last_audit_cycle": last_cycle,
                },
            )
        except Exception as exc:
            self._record_async_completion(
                slow_cycle, "failed", {"snapshot_delta": 0}, type(exc).__name__
            )
            logger.exception("[CognitiveAudit] scheduled worker failed")
        finally:
            with self._lock:
                self._audit_in_progress = False

    def _record_async_completion(
        self, slow_cycle: int, status: str, metrics: Dict[str, Any],
        error_type: Optional[str] = None,
    ) -> None:
        organism = getattr(self, "_organism", None)
        loop = getattr(organism, "_loop", None)
        recorder = getattr(loop, "record_async_cycle_stage", None)
        if callable(recorder):
            try:
                recorder(
                    slow_cycle,
                    "cognitive_audit_worker",
                    status,
                    output=metrics,
                    metrics=metrics,
                    error_type=error_type,
                )
            except Exception as exc:
                logger.debug("[CognitiveAudit] completion receipt unavailable: %s", exc)

    def status_summary(self) -> Dict[str, Any]:
        """Returns a human-readable status snapshot for UI/logging."""
        with self._lock:
            snap = self._state.snapshot_log[-1] if self._state.snapshot_log else {}
            trial = self._state.active_trial
            total_audits = len(self._state.snapshot_log)
            total_trials = len(self._state.trial_log)
            last_proposal_attempt = dict(self._state.last_proposal_attempt or {})
            latest_audit_cycle = int(self._state.last_audit_cycle or 0)
            confirmed_trials = sum(
                1 for t in self._state.trial_log if t.get("outcome") == "confirmed"
            )
        try:
            snapshot_timestamp = float(snap.get("timestamp")) if snap else None
        except (TypeError, ValueError, OverflowError):
            snapshot_timestamp = None
        snapshot_age = (
            max(0.0, time.time() - snapshot_timestamp)
            if snapshot_timestamp is not None else None
        )
        try:
            proposal_timestamp = float(last_proposal_attempt.get("timestamp"))
        except (TypeError, ValueError, OverflowError):
            proposal_timestamp = None
        proposal_age = (
            max(0.0, time.time() - proposal_timestamp)
            if proposal_timestamp is not None else None
        )
        attempt_cycle = last_proposal_attempt.get("slow_cycle")
        process_started_at = getattr(self, "_process_started_at", None)
        attempt_scope = (
            "unavailable" if not last_proposal_attempt else
            "persisted_or_unknown" if proposal_timestamp is None else
            "current_process" if isinstance(process_started_at, (int, float))
            and proposal_timestamp >= process_started_at else
            "persisted_or_unknown" if not isinstance(process_started_at, (int, float)) else
            "persisted_before_process"
        )
        attempt_relation = (
            "no_attempt" if not last_proposal_attempt else
            "same_as_latest_audit" if attempt_cycle == latest_audit_cycle else
            "older_than_latest_audit" if isinstance(attempt_cycle, int)
            and attempt_cycle < latest_audit_cycle else
            "cycle_unknown"
        )
        worst = None
        worst_actionable = None
        measured: Dict[str, float] = {}
        if snap:
            try:
                last_snapshot = SignalSnapshot(**{
                    k: v for k, v in snap.items()
                    if k in SignalSnapshot.__dataclass_fields__
                })
                worst = last_snapshot.worst_signal()
                measured = last_snapshot.deficit()
                actionable = {
                    name: gap for name, gap in measured.items()
                    if name in SIGNAL_PARAMETER_MAP and gap < 0
                }
                if actionable:
                    worst_actionable = min(actionable, key=actionable.get)
            except Exception:
                pass
        return {
            "last_snapshot": snap,
            "last_snapshot_age_seconds": round(snapshot_age, 1) if snapshot_age is not None else None,
            "last_snapshot_process_scope": (
                "current_process" if snapshot_timestamp is not None
                and isinstance(process_started_at, (int, float))
                and snapshot_timestamp >= process_started_at
                else "persisted_or_unknown" if snap else "unavailable"
            ),
            "last_audit_cycle": self._state.last_audit_cycle,
            "total_audits": total_audits,
            "total_trials": total_trials + (1 if trial else 0),
            "completed_trials": total_trials,
            "confirmed_trials": confirmed_trials,
            "worst_signal_now": worst,
            "worst_actionable_signal_now": worst_actionable,
            "non_actionable_signals": sorted(
                set(SIGNAL_TARGETS) - set(SIGNAL_PARAMETER_MAP)
            ),
            "measured_signal_count": len(measured),
            "unavailable_signals": sorted(set(SIGNAL_TARGETS) - set(measured)),
            "signal_measurement_status": self._snapshot_signal_status(snap),
            "signal_sample_count": (
                dict(snap.get("signal_sample_count", {})) if isinstance(snap, dict) else {}
            ),
            "descriptive_metrics": {
                name: {
                    "value": snap.get(name) if isinstance(snap, dict) else None,
                    "sample_count": (snap.get("signal_sample_count") or {}).get(name, 0)
                    if isinstance(snap, dict) else 0,
                    "status": (snap.get("signal_status") or {}).get(name, "unavailable")
                    if isinstance(snap, dict) else "unavailable",
                }
                for name in (
                    "epistemic_grounding_rate",
                    "experiment_confirmation_rate",
                    "experiment_resolution_rate",
                    "question_resolution_rate",
                    "mean_skill_depth",
                    "belief_confidence_mean",
                )
            },
            "performance_target_count": len(SIGNAL_TARGETS),
            "performance_target_status": (
                "none_validated" if not SIGNAL_TARGETS else "active"
            ),
            "active_trial": trial,
            "trial_evaluation_in_progress": getattr(self, "_trial_evaluation_in_progress", False),
            "proposal_attempt_count": int(self._state.proposal_attempt_total),
            "last_proposal_attempt": last_proposal_attempt,
            "last_proposal_attempt_age_seconds": (
                round(proposal_age, 1) if proposal_age is not None else None
            ),
            "last_proposal_attempt_process_scope": attempt_scope,
            "last_proposal_attempt_audit_relation": attempt_relation,
            "committed_params": dict(self._state.committed_params),
            "consecutive_under": dict(self._state.consecutive_under),
        }

    @staticmethod
    def _snapshot_signal_status(snapshot: Dict[str, Any]) -> Dict[str, str]:
        """Explain whether each diagnostic metric was measured or absent."""
        recorded = snapshot.get("signal_status", {}) if isinstance(snapshot, dict) else {}
        result = {}
        for name in (
            "epistemic_grounding_rate",
            "experiment_confirmation_rate",
            "experiment_resolution_rate",
            "question_resolution_rate",
            "mean_skill_depth",
            "belief_confidence_mean",
        ):
            status = recorded.get(name) if isinstance(recorded, dict) else None
            if status:
                result[name] = str(status)[:48]
            elif snapshot.get(name) is not None:
                result[name] = "measured_legacy_snapshot"
            else:
                result[name] = "legacy_snapshot_without_diagnostic"
        return result

    def prompt_fragment(self) -> str:
        """Returns a short status string for optional prompt injection."""
        if not self._state.committed_params:
            return ""
        parts = [f"{k}={v}" for k, v in self._state.committed_params.items()]
        return f"[CognitiveAudit] Committed calibrations: {', '.join(parts)}"

    # ── Audit cycle ───────────────────────────────────────────────────────────

    def _run_audit(self, slow_cycle: int) -> None:
        proposal_dimension = ""
        try:
            snapshot = self._read_signals(slow_cycle)

            with self._lock:
                self._state.snapshot_log.append(asdict(snapshot))
                if len(self._state.snapshot_log) > MAX_AUDIT_LOG:
                    self._state.snapshot_log = self._state.snapshot_log[-MAX_AUDIT_LOG:]
                self._state.last_audit_cycle = slow_cycle

            self._update_consecutive_underperformance(snapshot)

            # Only generate a proposal when there's no active trial
            if self._state.active_trial:
                logger.debug("[CognitiveAudit] Skipping proposal — trial already active")
                self._save()
                return

            deficits = snapshot.deficit()
            actionable_deficits = {
                name: gap for name, gap in deficits.items()
                if name in SIGNAL_PARAMETER_MAP and gap < 0
            }
            worst = min(actionable_deficits, key=actionable_deficits.get) if actionable_deficits else None
            if worst is None:
                unsupported = [
                    name for name, gap in deficits.items()
                    if gap < 0 and name not in SIGNAL_PARAMETER_MAP
                ]
                if unsupported:
                    self._record_proposal_attempt(
                        slow_cycle,
                        unsupported[0],
                        "no_causally_mapped_parameter",
                        "Underperforming signal has no validated parameter mapping; no live parameter was changed.",
                    )
                    logger.info(
                        "[CognitiveAudit] No justified tuning parameter for: %s",
                        ", ".join(unsupported),
                    )
                elif deficits:
                    logger.info("[CognitiveAudit] ✅ All measurable actionable signals on target")
                else:
                    logger.info(
                        "[CognitiveAudit] No validated performance targets; "
                        "descriptive diagnostics retained, no tuning permitted"
                    )
                self._save()
                return

            # Require TWO consecutive under-target readings before proposing
            if self._state.consecutive_under.get(worst, 0) < 2:
                logger.info(
                    f"[CognitiveAudit] {worst} underperforming "
                    f"(count={self._state.consecutive_under.get(worst,0)}), "
                    f"watching for next cycle"
                )
                self._save()
                return

            # Generate and activate a trial
            value = snapshot.as_dict()[worst]
            target = SIGNAL_TARGETS[worst]
            proposal_dimension = worst
            self._proposal_attempt_status = "requesting_proposal"
            self._proposal_attempt_detail = ""
            proposal = self._generate_proposal(worst, value, target, slow_cycle)
            if proposal:
                self._activate_trial(proposal)
                self._record_proposal_attempt(
                    slow_cycle, worst, "trial_activated",
                    f"parameter={proposal.parameter}",
                )
                logger.info(
                    f"[CognitiveAudit] 🔬 Trial activated: {worst} "
                    f"({value:.3f} < {target:.2f}) → "
                    f"{proposal.parameter} {proposal.prior_value} → {proposal.proposed_value}"
                )
            else:
                self._record_proposal_attempt(
                    slow_cycle, worst,
                    self._proposal_attempt_status,
                    self._proposal_attempt_detail,
                )

            self._save()

        except Exception as e:
            if proposal_dimension:
                self._record_proposal_attempt(
                    slow_cycle, proposal_dimension, "audit_error", str(e)[:240],
                )
            logger.debug(f"[CognitiveAudit] _run_audit error (non-fatal): {e}")

    def _record_proposal_attempt(
        self, slow_cycle: int, dimension: str, status: str, detail: str = "",
    ) -> None:
        """Persist why a persistent underperforming signal did or did not trial."""
        attempt = {
            "slow_cycle": int(slow_cycle),
            "timestamp": time.time(),
            "dimension": str(dimension)[:80],
            "status": str(status)[:48],
            "detail": str(detail)[:240],
        }
        with self._lock:
            self._state.last_proposal_attempt = attempt
            self._state.proposal_attempt_log.append(attempt)
            self._state.proposal_attempt_total += 1
            if len(self._state.proposal_attempt_log) > MAX_AUDIT_LOG:
                self._state.proposal_attempt_log = self._state.proposal_attempt_log[-MAX_AUDIT_LOG:]
        self._save()

    def _update_consecutive_underperformance(self, snapshot: SignalSnapshot) -> None:
        deficits = snapshot.deficit()
        with self._lock:
            # Discard persisted streaks from proxy metrics. They cannot justify
            # an automatic parameter trial under the current evidence contract.
            for name in list(self._state.consecutive_under):
                if name not in SIGNAL_TARGETS:
                    self._state.consecutive_under.pop(name, None)
            # A missing sample breaks a consecutive run. Keeping the previous
            # count across an unavailable interval lets one old under-target
            # reading combine with a much later reading and falsely satisfy
            # the two-audit confirmation requirement.
            for name in SIGNAL_TARGETS:
                if name not in deficits:
                    self._state.consecutive_under[name] = 0
                    continue
                gap = deficits[name]
                if gap < 0:
                    self._state.consecutive_under[name] = (
                        self._state.consecutive_under.get(name, 0) + 1
                    )
                else:
                    self._state.consecutive_under[name] = 0

    # ── Signal reading ────────────────────────────────────────────────────────

    def _read_signals(self, slow_cycle: int) -> SignalSnapshot:
        snap = SignalSnapshot(slow_cycle=slow_cycle, timestamp=time.time())
        status = snap.signal_status

        # 1. Epistemic grounding rate
        try:
            ar = getattr(self._organism, '_loop', None)
            ar = getattr(ar, '_autonomous_reflection', None) if ar else None
            if ar and hasattr(ar, '_epistemic'):
                epistemic = ar._epistemic
                snap.epistemic_grounding_rate = epistemic._recent_grounding_rate()
                grounding_log = getattr(getattr(epistemic, "_state", None), "grounding_log", [])
                grounding_samples = [
                    record for record in grounding_log
                    if record.get("measurement_status") == "measured"
                    and record.get("measurement_source")
                    and record.get("grounded") is not None
                ][-10:]
                snap.signal_sample_count["epistemic_grounding_rate"] = len(grounding_samples)
                status["epistemic_grounding_rate"] = (
                    "measured" if snap.epistemic_grounding_rate is not None else "no_observations"
                )
            else:
                status["epistemic_grounding_rate"] = "source_unavailable"
        except Exception as exc:
            status["epistemic_grounding_rate"] = f"read_error:{type(exc).__name__}"

        # 2. Experiment confirmation rate
        try:
            loop = getattr(self._organism, '_loop', None)
            ae = getattr(loop, '_auto_experiment', None) if loop else None
            if ae and hasattr(ae, '_state'):
                completed = [
                    item for item in getattr(ae._state, "experiment_log", [])
                    if item.get("outcome") in {"confirmed", "disconfirmed", "inconclusive"}
                ][-10:]
                snap.signal_sample_count["experiment_confirmation_rate"] = len(completed)
                snap.signal_sample_count["experiment_resolution_rate"] = len(completed)
                if completed:
                    snap.experiment_confirmation_rate = sum(
                        1 for item in completed if item.get("outcome") == "confirmed"
                    ) / len(completed)
                    snap.experiment_resolution_rate = sum(
                        1 for item in completed
                        if item.get("outcome") in {"confirmed", "disconfirmed"}
                    ) / len(completed)
                    status["experiment_confirmation_rate"] = "measured"
                    status["experiment_resolution_rate"] = "measured"
                else:
                    status["experiment_confirmation_rate"] = "no_observations"
                    status["experiment_resolution_rate"] = "no_observations"
            else:
                status["experiment_confirmation_rate"] = "source_unavailable"
                status["experiment_resolution_rate"] = "source_unavailable"
        except Exception as exc:
            status["experiment_confirmation_rate"] = f"read_error:{type(exc).__name__}"
            status["experiment_resolution_rate"] = f"read_error:{type(exc).__name__}"

        # 3. Question resolution rate
        try:
            loop = getattr(self._organism, '_loop', None)
            re = getattr(loop, '_resolution_engine', None) if loop else None
            if re and hasattr(re, '_state'):
                conclusive = [
                    item for item in getattr(re._state, "resolution_log", [])
                    if item.get("outcome") in {"resolved", "unresolvable"}
                ][-10:]
                snap.signal_sample_count["question_resolution_rate"] = len(conclusive)
                if conclusive:
                    snap.question_resolution_rate = sum(
                        1 for item in conclusive if item.get("outcome") == "resolved"
                    ) / len(conclusive)
                    status["question_resolution_rate"] = "measured"
                else:
                    status["question_resolution_rate"] = "no_observations"
            else:
                status["question_resolution_rate"] = "source_unavailable"
        except Exception as exc:
            status["question_resolution_rate"] = f"read_error:{type(exc).__name__}"

        # 4. Mean skill depth
        try:
            sr = getattr(self._organism, 'skill_registry', None)
            skills = getattr(getattr(sr, '_state', None), 'skills', {})
            if skills:
                depths = [s.get('depth', 0) for s in skills.values()]
                snap.mean_skill_depth = sum(depths) / len(depths)
                snap.signal_sample_count["mean_skill_depth"] = len(depths)
                status["mean_skill_depth"] = "measured"
            elif sr is not None:
                status["mean_skill_depth"] = "no_observations"
            else:
                status["mean_skill_depth"] = "source_unavailable"
        except Exception as exc:
            status["mean_skill_depth"] = f"read_error:{type(exc).__name__}"

        # 5. Belief confidence mean
        try:
            sc = getattr(self._ai, 'self_concept', None)
            # Try multiple access paths
            if sc is None:
                ts = getattr(self._organism, 'thought_system', None)
                sc = getattr(ts, 'self_concept', None) if ts else None
            if sc and hasattr(sc, '_beliefs') and sc._beliefs:
                confs = [b.confidence for b in sc._beliefs.values()]
                snap.belief_confidence_mean = sum(confs) / len(confs)
                snap.signal_sample_count["belief_confidence_mean"] = len(confs)
                status["belief_confidence_mean"] = "measured"
            elif sc is not None:
                status["belief_confidence_mean"] = "no_observations"
            else:
                status["belief_confidence_mean"] = "source_unavailable"
        except Exception as exc:
            status["belief_confidence_mean"] = f"read_error:{type(exc).__name__}"

        def _fmt(value: Optional[float]) -> str:
            return f"{value:.2f}" if value is not None else "n/a"

        logger.debug(
            f"[CognitiveAudit] Signals @ cycle {slow_cycle}: "
            f"grounding={_fmt(snap.epistemic_grounding_rate)} "
            f"exp_conf={_fmt(snap.experiment_confirmation_rate)} "
            f"exp_resolved={_fmt(snap.experiment_resolution_rate)} "
            f"q_res={_fmt(snap.question_resolution_rate)} "
            f"skill_depth={_fmt(snap.mean_skill_depth)} "
            f"belief_conf={_fmt(snap.belief_confidence_mean)}"
        )
        return snap

    # ── Proposal generation ───────────────────────────────────────────────────

    def _generate_proposal(
        self,
        dimension: str,
        current_value: float,
        target: float,
        slow_cycle: int,
    ) -> Optional[DevelopmentProposal]:
        """Ask the LLM to propose a specific parameter calibration."""
        self._proposal_attempt_status = "proposal_failed"
        self._proposal_attempt_detail = "No proposal response was produced."
        allowed_parameters = SIGNAL_PARAMETER_MAP.get(dimension, ())
        if not allowed_parameters:
            self._proposal_attempt_status = "no_causally_mapped_parameter"
            self._proposal_attempt_detail = (
                f"No validated tunable parameter directly maps to signal {dimension}."
            )
            return None
        current_params = self._current_params()

        # Build the parameter change bounds description
        param_desc_lines = []
        for pname in allowed_parameters:
            default, pmin, pmax, ptype = PARAM_SPACE[pname]
            cur = current_params.get(pname, default)
            param_desc_lines.append(
                f"  {pname}: current={cur}, range=[{pmin},{pmax}], type={ptype.__name__}"
            )
        param_desc = "\n".join(param_desc_lines)

        # v64: MetaLearningAudit — bias away from parameters with poor effectiveness
        guidance_note = ""
        try:
            loop = getattr(self._organism, '_loop', None)
            mla  = getattr(loop, '_meta_learning_audit', None) if loop else None
            if mla:
                guidance = mla.parameter_guidance()
                do_not   = [p for p, w in guidance.items() if w == 0.0]
                low_eff  = [p for p, w in guidance.items() if 0 < w < 0.6]
                high_eff = [p for p, w in guidance.items() if w > 1.1]
                parts = []
                if do_not:  parts.append(f"DO NOT use: {do_not}")
                if low_eff: parts.append(f"LOW effectiveness history: {low_eff}")
                if high_eff: parts.append(f"HIGH effectiveness history: {high_eff}")
                if parts:
                    guidance_note = "\nHISTORICAL EFFECTIVENESS:\n" + "\n".join(parts) + "\n"
        except Exception:
            pass

        prompt = f"""You are the cognitive self-calibration layer of an adaptive AI system.

UNDERPERFORMING SIGNAL
  name:    {dimension}
  current: {current_value:.3f}
  target:  {target:.2f}
  deficit: {current_value - target:.3f}

VALIDATED CANDIDATE PARAMETERS FOR THIS SIGNAL
{param_desc}
{guidance_note}
TASK
Select one parameter only from the validated candidate list to improve {dimension}.
Reason concisely (2 sentences max).
The change must stay within the stated range.
Change magnitude must not exceed 30% of current value.

Respond ONLY in JSON (no markdown, no preamble):
{{
  "parameter": "<param_name>",
  "proposed_value": <number>,
  "rationale": "<2-sentence explanation>"
}}"""

        response = self._llm_call(prompt, caller="cognitive_audit")
        if not response:
            return None

        try:
            # Strip any accidental markdown fences
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(clean)
            pname = data.get("parameter", "")
            if pname not in allowed_parameters or pname not in PARAM_SPACE:
                self._proposal_attempt_status = "parameter_signal_mismatch"
                self._proposal_attempt_detail = (
                    f"Parameter {pname!r} is not causally mapped to signal {dimension}."
                )
                logger.warning(
                    "[CognitiveAudit] Rejected parameter/signal mismatch: %s -> %s",
                    dimension, pname,
                )
                return None

            default, pmin, pmax, ptype = PARAM_SPACE[pname]
            prior = current_params.get(pname, default)
            raw   = data.get("proposed_value", prior)

            # Clamp to bounds
            proposed = ptype(max(pmin, min(pmax, raw)))

            # Enforce max-change-pct
            if prior != 0:
                change_pct = abs(proposed - prior) / abs(prior)
                if change_pct > 0.30:
                    # Clamp to 30%
                    direction = 1 if proposed > prior else -1
                    proposed = ptype(prior + direction * abs(prior) * 0.30)
                    proposed = ptype(max(pmin, min(pmax, proposed)))

            if proposed == prior:
                self._proposal_attempt_status = "no_parameter_change"
                self._proposal_attempt_detail = f"Proposal left {pname} unchanged."
                logger.debug(f"[CognitiveAudit] Proposal resulted in no change for {pname}")
                return None

            self._proposal_attempt_status = "proposal_created"
            self._proposal_attempt_detail = f"parameter={pname}"
            return DevelopmentProposal(
                dimension           = dimension,
                signal_at_proposal  = current_value,
                signal_target       = target,
                parameter           = pname,
                prior_value         = prior,
                proposed_value      = proposed,
                rationale           = data.get("rationale", ""),
                proposed_at_cycle   = slow_cycle,
            )

        except Exception as e:
            self._proposal_attempt_status = "invalid_response"
            self._proposal_attempt_detail = str(e)[:240]
            logger.debug(f"[CognitiveAudit] Proposal parse failed: {e} | raw={response[:200]}")
            return None

    # ── Trial management ──────────────────────────────────────────────────────

    def _activate_trial(self, proposal: DevelopmentProposal) -> None:
        """Apply proposed value to live module global and record trial."""
        self._set_module_global(proposal.parameter, proposal.proposed_value)
        with self._lock:
            self._state.active_trial = asdict(proposal)
        self._save()

    def _evaluate_trial(self, trial: DevelopmentProposal, slow_cycle: int) -> bool:
        """Re-read the signal and determine whether the trial improved it."""
        try:
            snapshot = self._read_signals(slow_cycle)
            with self._lock:
                self._state.snapshot_log.append(asdict(snapshot))
                if len(self._state.snapshot_log) > MAX_AUDIT_LOG:
                    self._state.snapshot_log = self._state.snapshot_log[-MAX_AUDIT_LOG:]
                trial_snapshots = [
                    item for item in self._state.snapshot_log
                    if item.get("slow_cycle", 0) > trial.proposed_at_cycle
                    and item.get(trial.dimension) is not None
                    and (item.get("signal_status") or {}).get(trial.dimension)
                    in {"measured", "measured_legacy_snapshot"}
                ]
            trial.signal_sample_count_at_eval = len(trial_snapshots)
            signal_values = [float(item[trial.dimension]) for item in trial_snapshots]
            # Require two distinct post-proposal audit snapshots and evaluate
            # their mean; a single lucky/noisy reading cannot commit a change.
            signal_now = (
                sum(signal_values[-2:]) / 2.0
                if len(signal_values) >= 2 else None
            )
            target     = trial.signal_target
            prior      = trial.signal_at_proposal

            # Missing data cannot confirm or disconfirm a live parameter trial.
            if signal_now is None:
                outcome = "inconclusive"
            else:
                # Δ as fraction of target (normalised)
                delta = signal_now - prior
                if delta >= CONFIRM_THRESHOLD * target:
                    outcome = "confirmed"
                elif delta <= -DISCONFIRM_THRESHOLD * target:
                    outcome = "disconfirmed"
                else:
                    outcome = "inconclusive"

            trial.outcome           = outcome
            trial.signal_at_eval    = signal_now
            trial.evaluated_at_cycle = slow_cycle

            if outcome == "confirmed":
                self._commit_trial(trial)
                logger.info(
                    f"[CognitiveAudit] ✅ Confirmed: {trial.parameter} "
                    f"{trial.prior_value} → {trial.proposed_value} "
                    f"({trial.dimension}: {prior:.3f} → {signal_now:.3f})"
                )
            else:
                self._revert_trial(trial)
                evaluated_text = f"{signal_now:.3f}" if signal_now is not None else "unavailable"
                logger.info(
                    f"[CognitiveAudit] ↩ {outcome.capitalize()}: {trial.parameter} "
                    f"reverted to {trial.prior_value} "
                    f"({trial.dimension}: {prior:.3f} → {evaluated_text})"
                )

            with self._lock:
                self._state.trial_log.append(asdict(trial))
                if len(self._state.trial_log) > MAX_TRIAL_LOG:
                    self._state.trial_log = self._state.trial_log[-MAX_TRIAL_LOG:]
                self._state.active_trial = None
                # Reset consecutive underperformance for this signal so we don't
                # immediately re-propose after a revert.
                self._state.consecutive_under[trial.dimension] = 0

            self._save()
            return True

        except Exception as e:
            logger.debug(f"[CognitiveAudit] _evaluate_trial error (non-fatal): {e}")
            with self._lock:
                self._state.active_trial = None
            self._revert_trial(trial)
            self._save()
            return False

    def _evaluate_trial_once(self, trial: DevelopmentProposal, slow_cycle: int) -> None:
        """Run one trial evaluation and always release the single-flight guard."""
        with self._lock:
            trials_before = len(self._state.trial_log)
            committed_before = dict(self._state.committed_params)
        try:
            evaluated = bool(self._evaluate_trial(trial, slow_cycle))
            with self._lock:
                trial_delta = len(self._state.trial_log) - trials_before
                latest = dict(self._state.trial_log[-1]) if trial_delta and self._state.trial_log else {}
                committed_after = dict(self._state.committed_params)
            self._record_async_completion(
                slow_cycle,
                "completed" if evaluated and trial_delta else "failed",
                {
                    "trial_delta": trial_delta,
                    "dimension": trial.dimension,
                    "outcome": str(latest.get("outcome", "not_recorded")),
                    "signal_sample_count": int(latest.get("signal_sample_count_at_eval", 0) or 0),
                    "committed": bool(latest.get("committed", False)),
                    "committed_parameter_changed": committed_after != committed_before,
                },
                None if evaluated and trial_delta else "trial_result_not_recorded",
            )
        except Exception as exc:
            self._record_async_completion(
                slow_cycle,
                "failed",
                {"trial_delta": 0, "dimension": trial.dimension},
                type(exc).__name__,
            )
            logger.exception("[CognitiveAudit] trial evaluation worker failed")
        finally:
            with self._lock:
                self._trial_evaluation_in_progress = False

    def _commit_trial(self, trial: DevelopmentProposal) -> None:
        """Persist confirmed parameter change to committed_params."""
        trial.committed = True
        with self._lock:
            self._state.committed_params[trial.parameter] = trial.proposed_value
        # Module global is already at proposed_value — leave it.

    def _revert_trial(self, trial: DevelopmentProposal) -> None:
        """Restore the module global to the prior value."""
        self._set_module_global(trial.parameter, trial.prior_value)

    # ── Module global mutation ────────────────────────────────────────────────

    def _set_module_global(self, param: str, value: Any) -> None:
        """Mutate the live module-level constant for a cognitive parameter."""
        if param not in PARAM_MODULE_MAP:
            return
        mod_path, global_name = PARAM_MODULE_MAP[param]
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            setattr(mod, global_name, value)
            logger.debug(
                f"[CognitiveAudit] Set {mod_path}.{global_name} = {value}"
            )
        except Exception as e:
            logger.debug(f"[CognitiveAudit] Could not set {param}: {e}")

    def _apply_committed_params(self) -> None:
        """On startup, restore all previously committed parameter changes."""
        for param, value in self._state.committed_params.items():
            self._set_module_global(param, value)
            logger.info(f"[CognitiveAudit] Restored committed param: {param}={value}")

    # ── Current parameter snapshot ────────────────────────────────────────────

    def _current_params(self) -> Dict[str, Any]:
        """Read loaded live parameter values without importing subsystems.

        Importing a ``cognition.*`` submodule can execute the package
        ``__init__`` and initialize the full AI/memory stack. Parameters for
        modules not loaded in this process are still at their declared
        defaults; a committed override is handled above.
        """
        result = {}
        for pname, (default, pmin, pmax, ptype) in PARAM_SPACE.items():
            # First, use committed value if present
            if pname in self._state.committed_params:
                result[pname] = self._state.committed_params[pname]
                continue
            # Otherwise read from module
            if pname in PARAM_MODULE_MAP:
                mod_path, global_name = PARAM_MODULE_MAP[pname]
                mod = sys.modules.get(mod_path)
                if mod is not None:
                    result[pname] = getattr(mod, global_name, default)
                    continue
            result[pname] = default
        return result

    # ── LLM ──────────────────────────────────────────────────────────────────

    def _llm_call(self, prompt: str, caller: str = "cognitive_audit") -> Optional[str]:
        from core.llm_scheduler import llm_scheduler
        result = ""
        with llm_scheduler.sync_slot(
            priority     = 3,
            skip_if_busy = True,
            caller       = caller,
            wait_seconds = 5.0,
        ) as acquired:
            if not acquired:
                self._proposal_attempt_status = "llm_slot_busy"
                self._proposal_attempt_detail = "No LLM slot became available within the bounded 5 s wait."
                return None
            try:
                # CognitiveAuditEngine runs inside EnhancedAISystem, whose
                # get_response(user_input, ...) is the full conversational
                # path. Calibration proposals are an internal, bounded task:
                # send them to the configured model adapter directly, just as
                # DreamSynthesis and NarrativeCompression do. Calling the
                # facade with `messages=` raises TypeError and silently leaves
                # the audit collecting snapshots forever without a single
                # proposal or trial.
                llm = getattr(self._ai, "llm", None)
                if llm is None or not callable(getattr(llm, "get_response", None)):
                    self._proposal_attempt_status = "llm_unavailable"
                    self._proposal_attempt_detail = "EnhancedAISystem has no usable LLM adapter."
                    return None
                result = llm.get_response(
                    messages    = [{"role": "user", "content": prompt}],
                    max_tokens  = 200,
                    temperature = 0.50,
                ) or ""
            except Exception as e:
                self._proposal_attempt_status = "llm_error"
                self._proposal_attempt_detail = str(e)[:240]
                logger.debug(f"[CognitiveAudit] LLM failed: {e}")
                return None
        if not result:
            self._proposal_attempt_status = "empty_llm_response"
            self._proposal_attempt_detail = "The LLM slot was acquired but returned no proposal text."
        return result or None

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._path.exists():
                with open(self._path) as f:
                    data = json.load(f)
                proposal_attempt_log = data.get("proposal_attempt_log") or []
                self._state = AuditState(
                    last_audit_cycle   = data.get("last_audit_cycle", 0),
                    snapshot_log       = data.get("snapshot_log", []),
                    active_trial       = data.get("active_trial"),
                    trial_log          = data.get("trial_log", []),
                    committed_params   = data.get("committed_params", {}),
                    proposal_attempt_log = proposal_attempt_log,
                    last_proposal_attempt = data.get("last_proposal_attempt"),
                    proposal_attempt_total = int(data.get(
                        "proposal_attempt_total", len(proposal_attempt_log),
                    )),
                    consecutive_under  = data.get("consecutive_under", {}),
                )
                # Historical streaks came from proxy metrics and cannot justify
                # automatic tuning under the current evidence contract.
                self._state.consecutive_under = {}
        except Exception as e:
            logger.warning(f"[CognitiveAudit] Load failed (using defaults): {e}")

    def _recover_incompatible_active_trial(self) -> None:
        """Rollback a persisted trial whose parameter cannot affect its signal."""
        raw = self._state.active_trial
        if not raw:
            return
        dimension = str(raw.get("dimension", ""))
        parameter = str(raw.get("parameter", ""))
        if parameter in SIGNAL_PARAMETER_MAP.get(dimension, ()):
            return

        trial = dict(raw)
        trial.update({
            "outcome": "rejected_causal_mismatch",
            "signal_at_eval": None,
            "evaluated_at_cycle": int(self._state.last_audit_cycle or 0),
            "committed": False,
        })
        prior_value = trial.get("prior_value")
        if parameter in PARAM_MODULE_MAP and prior_value is not None:
            self._set_module_global(parameter, prior_value)

        with self._lock:
            self._state.trial_log.append(trial)
            if len(self._state.trial_log) > MAX_TRIAL_LOG:
                self._state.trial_log = self._state.trial_log[-MAX_TRIAL_LOG:]
            self._state.active_trial = None
            self._state.consecutive_under[dimension] = 0
            attempt = {
                "slow_cycle": int(self._state.last_audit_cycle or 0),
                "timestamp": time.time(),
                "dimension": dimension[:80],
                "status": "trial_reverted_causal_mismatch",
                "detail": (
                    f"Restored {parameter}={prior_value}; no validated causal mapping to {dimension}."
                ),
            }
            self._state.last_proposal_attempt = attempt
            self._state.proposal_attempt_log.append(attempt)
            self._state.proposal_attempt_total += 1
            if len(self._state.proposal_attempt_log) > MAX_AUDIT_LOG:
                self._state.proposal_attempt_log = self._state.proposal_attempt_log[-MAX_AUDIT_LOG:]
        logger.warning(
            "[CognitiveAudit] Rolled back persisted trial with unsupported mapping: %s -> %s",
            dimension, parameter,
        )
        self._save()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "last_audit_cycle":  self._state.last_audit_cycle,
                    "snapshot_log":      self._state.snapshot_log,
                    "active_trial":      self._state.active_trial,
                    "trial_log":         self._state.trial_log,
                    "committed_params":  self._state.committed_params,
                    "proposal_attempt_log": self._state.proposal_attempt_log,
                    "last_proposal_attempt": self._state.last_proposal_attempt,
                    "proposal_attempt_total": self._state.proposal_attempt_total,
                    "consecutive_under": self._state.consecutive_under,
                    "_meta": {
                        "written_at":    time.time(),
                        "module":        "cognitive_audit_engine",
                        "version":       "v48",
                    },
                }
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.debug(f"[CognitiveAudit] Save failed: {e}")
