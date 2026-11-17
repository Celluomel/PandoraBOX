"""
cognition/meta_learning_audit.py  (v64)

Tracks whether CognitiveAuditEngine parameter adjustments actually
improved the signals they targeted.  Closes the self-modification loop.

Problem: v48 (CognitiveAuditEngine) adjusts parameters when signals
underperform.  But it never checks whether past adjustments worked.
A confirmed adjustment that produced no lasting improvement is treated
identically to one that genuinely fixed the signal.

MetaLearningAudit reads the CognitiveAuditEngine trial_log and for each
committed change, tracks the signal trajectory before and after the
commit over a longer window (META_WINDOW slow cycles).

If the signal recovered and held: the parameter was genuinely effective
  -> record as "effective", weight it higher in future proposals
If the signal recovered briefly then regressed: the parameter was a
  local fix but not structural
  -> record as "transient", lower weight in future proposals
If the signal did not recover: the parameter was wrong lever
  -> record as "ineffective", add to a do-not-repeat list

This data is fed back to CognitiveAuditEngine._generate_proposal() to
bias the LLM away from parameters that have a poor effectiveness record.
"""

from __future__ import annotations
import json, logging, os, tempfile, threading, time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

META_EVERY_N      = 50    # slow cycles between meta-audits
# Bug fix (v117): META_WINDOW was 40, identical to CognitiveAuditEngine's
# AUDIT_EVERY_N. Quantified: with the two constants equal, the evaluation
# window [commit_cycle, commit_cycle+META_WINDOW] always contains EXACTLY
# ONE audit snapshot, regardless of commit timing (verified for all 40
# possible cycle offsets). That collapses peak (best snapshot in window)
# and after_stable (last snapshot) to the same single value every time, so
# peak_improvement == improvement always — meaning the "transient" verdict
# (requires peak_improvement > 0.08 AND improvement < 0.03, i.e. the two
# must differ) could never actually fire. The three-way effective/
# transient/ineffective classification was silently a two-way one, missing
# exactly the "recovered briefly then regressed" case the docstring above
# says this module exists to catch. 3x guarantees >=3 snapshots in every
# window (verified), enough to actually observe a peak-then-regression.
META_WINDOW       = 120   # cycles after commit to evaluate (3x AUDIT_EVERY_N)
SAVE_PATH         = "data/persona/meta_learning_audit.json"


@dataclass
class ParameterEffectiveness:
    parameter:    str
    signal:       str          # which signal it targeted
    before:       float
    after_peak:   float        # best value reached post-commit
    after_stable: float        # value at META_WINDOW cycles post-commit
    verdict:      str          # "effective"|"transient"|"ineffective"
    commit_cycle: int
    evaluated_at: float = field(default_factory=time.time)
    baseline_source: str = "commit_snapshot"


class MetaLearningAudit:
    def __init__(self, organism: Any, ai_system: Any, path: str = SAVE_PATH):
        self._organism  = organism
        self._ai        = ai_system
        self._path      = Path(path)
        self._lock      = threading.Lock()
        self._worker_pending = False
        self._records:  List[ParameterEffectiveness] = []
        self._pending:  List[Dict] = []   # commits awaiting evaluation
        self._do_not_repeat: List[str] = []
        self._load()
        logger.info(
            f"[MetaLearningAudit] Init — "
            f"{len(self._records)} evaluations, "
            f"do_not_repeat={self._do_not_repeat}"
        )

    def tick(self, slow_cycle: int) -> Dict[str, Any]:
        if slow_cycle % META_EVERY_N != 0 or slow_cycle == 0:
            return {"outcome_status": "skipped", "reason_code": "meta_audit_cadence_not_due", "cycle": slow_cycle}
        with self._lock:
            if self._worker_pending:
                return {"outcome_status": "skipped", "reason_code": "meta_audit_already_running", "cycle": slow_cycle}
            self._worker_pending = True
        try:
            worker = threading.Thread(
                target=self._run_guarded, args=(slow_cycle,),
                daemon=True, name="mla-audit"
            )
            worker.start()
        except Exception:
            with self._lock:
                self._worker_pending = False
            logger.exception("[MetaLearningAudit] worker start failed")
            return {"outcome_status": "failed", "reason_code": "worker_start_failed", "cycle": slow_cycle}
        return {"outcome_status": "scheduled", "reason_code": "meta_audit_worker_started", "cycle": slow_cycle}

    def parameter_guidance(self) -> Dict[str, float]:
        """
        Returns weight multipliers for each parameter.
        CognitiveAuditEngine uses this to bias proposal generation.
        >1.0 = this parameter has been effective, prefer it
        <1.0 = this parameter has been ineffective, avoid it
        0.0  = do not repeat
        """
        guidance: Dict[str, float] = {}
        for param in self._do_not_repeat:
            guidance[param] = 0.0
        for rec in self._records:
            p = rec.parameter
            if p in guidance: continue
            if rec.verdict == "effective":
                guidance[p] = guidance.get(p, 1.0) * 1.25
            elif rec.verdict == "transient":
                guidance[p] = guidance.get(p, 1.0) * 0.80
            elif rec.verdict == "ineffective":
                guidance[p] = guidance.get(p, 1.0) * 0.50
        return guidance

    def status(self) -> Dict:
        by_verdict = {"effective":0,"transient":0,"ineffective":0}
        for r in self._records:
            by_verdict[r.verdict] = by_verdict.get(r.verdict, 0) + 1
        return {
            "total_evaluations": len(self._records),
            "by_verdict": by_verdict,
            "do_not_repeat": self._do_not_repeat,
            "pending_evaluation": len(self._pending),
        }

    def _run_guarded(self, slow_cycle: int) -> None:
        try:
            before_records = len(self._records)
            before_pending = len(self._pending)
            persisted = self._run(slow_cycle)
            outcome = {
                "outcome_status": "completed" if persisted else "failed",
                "reason_code": (
                    "state_persisted_effect_window_evaluated"
                    if persisted and len(self._records) > before_records else
                    "state_persisted_no_mature_effect_window"
                    if persisted else "state_persistence_failed"
                ),
                "evaluations_added": len(self._records) - before_records,
                "pending_count": len(self._pending),
                "pending_delta": len(self._pending) - before_pending,
            }
            self._record_async_completion(slow_cycle, outcome["outcome_status"], outcome)
        except Exception as exc:
            logger.debug(f"[MetaLearningAudit] _run error: {exc}")
            self._record_async_completion(
                slow_cycle, "failed", {"outcome_status": "failed", "reason_code": "meta_audit_error"},
                error_type=type(exc).__name__,
            )
        finally:
            with self._lock:
                self._worker_pending = False

    def _run(self, slow_cycle: int) -> bool:
        self._register_new_commits(slow_cycle)
        self._evaluate_matured(slow_cycle)
        return self._save()

    def _record_async_completion(
        self, slow_cycle: int, status: str, output: Dict[str, Any],
        *, error_type: Optional[str] = None,
    ) -> None:
        loop = getattr(self._organism, "_loop", None)
        recorder = getattr(loop, "record_async_cycle_stage", None)
        if callable(recorder):
            recorder(slow_cycle, "meta_learning_audit.worker", status,
                     output=output, error_type=error_type)

    def _register_new_commits(self, slow_cycle: int) -> None:
        """Register newly committed parameter changes for later evaluation."""
        loop = getattr(self._organism, '_loop', None)
        cae  = getattr(loop, '_cognitive_audit', None) if loop else None
        if not cae: return

        for trial in cae._state.trial_log:
            if trial.get("outcome") != "confirmed": continue
            if trial.get("committed") is not True: continue
            # Measure the long-term effect from the point the trial was
            # actually confirmed and committed. Starting at proposal time
            # mixes the temporary trial period into the post-commit window.
            commit_cycle = trial.get("evaluated_at_cycle") or trial.get("proposed_at_cycle", 0)
            baseline = trial.get("signal_at_eval")
            if baseline is None:
                # Older persisted trials predate signal_at_eval on commit.
                # Keep them auditable, but mark their baseline provenance.
                baseline = trial.get("signal_at_proposal")
                baseline_source = "legacy_proposal_baseline"
            else:
                baseline_source = "commit_snapshot"
            if baseline is None:
                logger.warning(
                    "[MetaLearningAudit] Skipping committed trial without a baseline: %s",
                    trial.get("parameter"),
                )
                continue
            # A matured evaluation leaves _pending and moves to _records.
            # Check both stores so every confirmed commit is evaluated once,
            # not re-registered on every later audit tick.
            already = any(
                str(item.get("parameter", "")) == str(trial.get("parameter", ""))
                and str(item.get("commit_cycle", "")) == str(commit_cycle)
                for item in [*self._pending, *(asdict(record) for record in self._records)]
            )
            if already: continue
            self._pending.append({
                "parameter":    trial.get("parameter", ""),
                "signal":       trial.get("dimension", ""),
                "before":       float(baseline),
                "baseline_source": baseline_source,
                "commit_cycle": commit_cycle,
                "eval_at":      commit_cycle + META_WINDOW,
            })
            logger.debug(
                f"[MetaLearningAudit] Registered for evaluation: "
                f"{trial.get('parameter')} targeting {trial.get('dimension')}"
            )

    def _evaluate_matured(self, slow_cycle: int) -> None:
        """Evaluate commits that have passed their META_WINDOW."""
        loop = getattr(self._organism, '_loop', None)
        cae  = getattr(loop, '_cognitive_audit', None) if loop else None
        if not cae: return

        remaining = []
        for pending in self._pending:
            if slow_cycle < pending["eval_at"]:
                remaining.append(pending)
                continue

            # Evaluate only measured snapshots captured after commit and
            # inside this trial's declared follow-up window. Never turn a
            # missing signal into a plausible-looking numeric default.
            signal = pending["signal"]
            before      = pending["before"]
            commit_cycle = pending["commit_cycle"]
            eval_at = pending["eval_at"]
            snapshots = [
                s for s in cae._state.snapshot_log
                if commit_cycle < s.get("slow_cycle", 0) <= eval_at
                and s.get(signal) is not None
                and (s.get("signal_status") or {}).get(signal) in {"measured", "measured_legacy_snapshot"}
            ]
            # At least two post-commit samples are required to assess a
            # sustained effect. Keep the pending item until evidence exists.
            if len(snapshots) < 2:
                remaining.append(pending)
                logger.info(
                    "[MetaLearningAudit] Deferring %s: %d measured post-commit samples, need 2",
                    pending["parameter"], len(snapshots),
                )
                continue

            values = [float(s[signal]) for s in snapshots]
            peak = max(values)
            current_val = sum(values[-2:]) / 2.0

            # Verdict
            improvement = current_val - before
            peak_improvement = peak - before
            if improvement > 0.08:
                verdict = "effective"
            elif peak_improvement > 0.08 and improvement < 0.03:
                verdict = "transient"
            else:
                verdict = "ineffective"
                param = pending["parameter"]
                # Add to do-not-repeat if ineffective twice
                ineffective_count = sum(
                    1 for r in self._records
                    if r.parameter == param and r.verdict == "ineffective"
                )
                if ineffective_count >= 1 and param not in self._do_not_repeat:
                    self._do_not_repeat.append(param)
                    logger.info(
                        f"[MetaLearningAudit] Added to do-not-repeat: {param}"
                    )

            rec = ParameterEffectiveness(
                parameter    = pending["parameter"],
                signal       = signal,
                before       = before,
                after_peak   = round(peak, 4),
                after_stable = round(current_val, 4),
                verdict      = verdict,
                commit_cycle = commit_cycle,
                baseline_source = pending.get("baseline_source", "legacy_unknown"),
            )
            with self._lock:
                self._records.append(rec)

            logger.info(
                f"[MetaLearningAudit] {pending['parameter']} → "
                f"{signal}: {verdict} "
                f"(before={before:.3f} peak={peak:.3f} stable={current_val:.3f})"
            )

        self._pending = remaining

    def _read_signal(self, signal: str, cae: Any) -> float:
        """
        Current value of a signal, averaged over the last 2 snapshots
        rather than a single point. v117: with only one sample, this
        reading is pure noise-sensitivity — "stable" in after_stable
        should mean more than one data point agreeing, especially now
        that the widened META_WINDOW above actually provides more than
        one snapshot to average over.
        """
        snapshots = cae._state.snapshot_log
        if not snapshots:
            return 0.5
        recent = snapshots[-2:]
        vals = [s.get(signal, 0.5) for s in recent]
        return sum(vals) / len(vals)

    def _save(self) -> bool:
        temp_path = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "records":        [asdict(r) for r in self._records],
                    "pending":        self._pending,
                    "do_not_repeat":  self._do_not_repeat,
                    "_meta": {"version":"v64","ts":time.time()},
                }
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(self._path.parent),
                prefix=f".{self._path.name}.", suffix=".tmp", delete=False,
            ) as f:
                temp_path = f.name
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self._path)
            return True
        except Exception as e:
            logger.warning("[MetaLearningAudit] state persistence failed: %s", e)
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            return False

    def _load(self) -> None:
        try:
            if not self._path.exists(): return
            data = json.loads(self._path.read_text())
            self._records = [
                ParameterEffectiveness(**{
                    k:v for k,v in r.items()
                    if k in ParameterEffectiveness.__dataclass_fields__
                })
                for r in data.get("records", [])
            ]
            self._pending       = data.get("pending", [])
            self._do_not_repeat = data.get("do_not_repeat", [])
        except Exception as e:
            logger.warning(f"[MetaLearningAudit] load error: {e}")
