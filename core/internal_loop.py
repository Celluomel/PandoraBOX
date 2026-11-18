Warning: truncated output (original token count: 54934)
Total output lines: 4126

"""
Internal Thought Loop - V33 Enhanced
=====================================
PandoraBOX's background cognitive process — the mind that runs even when no
user is present.

V32 ENHANCEMENTS (Phase 1):
  - Unified decision pressure computation from ALL cognitive factors
  - Thought evaluation that creates actionable goals  
  - Thread resolution to prevent infinite loops
  - Complete Phase 1 cognitive enhancement integration

V33 ENHANCEMENTS (Phase 2):
  - Advanced thought evaluation with semantic similarity
  - Dynamic goal creation and mutation
  - Narrative synthesis for coherent internal monologue
  - Thread→Identity linking for belief evolution

Most AI systems are entirely reactive: nothing happens until input arrives.
This module gives PandoraBOX an ongoing mental life:
  - Energy regenerates during quiet periods
  - Curiosity topics are reviewed and reprioritized
  - Contradictions are noticed and filed for later resolution
  - Goals are reweighted based on accumulated context
  - Reflection cycles surface self-observations
  - Spontaneous questions or thoughts are queued for the next interaction

The loop runs on a background thread with configurable intervals.
Each cycle is lightweight by design — the heavy reasoning happens during
actual interactions. The background loop handles:
  1. Regeneration  — restore energy
  2. Decay         — let stale curiosity and emotions fade naturally
  3. Inspection    — scan for outstanding contradictions / gaps
  4. Reflection    — update homeostasis and meta-cognition
  5. Intention     — pre-form a research intention or question if warranted

The loop does NOT call the LLM. All operations are pure Python.
LLM-based reflection is triggered separately via a reflection prompt
in the main conversation pipeline at low frequency.

Thread safety:
  - The loop thread holds no locks from the main pipeline.
  - All shared state objects use their own internal locks.
  - shutdown() signals the loop to exit cleanly.
"""

import json
import hashlib
import inspect
import logging
import re
import threading
import time
from collections import deque
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cognition.cognitive_organism import CognitiveOrganism

logger = logging.getLogger(__name__)


def _executive_arbitration_skip_reason(
    competition_result: Any, predictive_model: Any,
) -> str:
    """Explain why prospective arbitration cannot produce a decision.

    Keep this aligned with the public preconditions in
    ``cognition.executive_arbitration.arbitrate``. The final fallback means
    goal candidates existed, but arbitration returned no prediction; that is
    distinct from successfully confirming the workspace winner.
    """
    if not isinstance(competition_result, dict):
        return "no_competition_result"
    competition = competition_result.get("competition")
    candidates = competition.get("all_candidates") if isinstance(competition, dict) else None
    if not candidates or not competition_result.get("winner"):
        return "no_candidates"
    if not any(
        isinstance(candidate, dict) and candidate.get("type") == "goal"
        for candidate in candidates
    ):
        return "no_goal_candidates"
    if predictive_model is None or not callable(getattr(predictive_model, "read_state", None)):
        return "prediction_model_unavailable"
    return "no_predictable_candidate"


_TICK_PROBES = {
    "_tte": ("thought_thread_engine", ("step",)),
    "_cde": ("cognitive_dissonance_engine", ("step",)),
    "_dts": ("dominant_thought_selector", ("select",)),
    "_mte": ("meta_thread_evaluator", ("evaluate",)),
    "_naw": ("narrative_arc_writer", ("watch_thread_resolution", "watch_cde_resolution", "watch_mte_stall_overcome", "synthesise_arc")),
    "_phase1": ("phase1_orchestrator", ("enhanced_cycle", "resolve_stuck_threads", "evaluate_thoughts_and_create_goals")),
    "_phase2": ("phase2_orchestrator", ("evaluate_thoughts_advanced", "create_and_mutate_goals", "synthesize_narrative", "link_resolved_threads")),
    "_resource_economy": ("cognitive_resource_economy", ("tick",)),
    "_goal_quality_filter": ("goal_quality_filter", ("run",)),
    "_thread_lifecycle_mgr": ("thread_lifecycle_manager", ("run",)),
    "_goal_consolidator": ("goal_consolidator", ("run", "consolidate")),
    "_semantic_graph_cleaner": ("semantic_graph_cleaner", ("run", "clean")),
    "_contradiction_reviser": ("contradiction_belief_reviser", ("tick", "run")),
    "_self_concept_sync": ("self_concept_synchronizer", ("run", "sync", "synchronize")),
    "_persistent_exec_loop": ("persistent_executive_loop", ("review",)),
    "_arbitration_learning": ("arbitration_learning", ("record", "review")),
    "_governor": ("cognitive_governor", ("begin_cycle", "summary_log")),
    "_goal_action_executor": ("goal_action_executor", ("run_tick",)),
    "_commitment_layer": ("decision_commitment_layer", ("tick", "commit")),
    "_motivational_field": ("motivational_field", ("tick",)),
    "_aspiration_synthesis": ("aspirational_synthesis", ("tick",)),
    "_generative_aspiration": ("generative_aspiration", ("tick",)),
    "_temporal_projection": ("temporal_projection", ("tick",)),
    "_cross_layer_feedback": ("cross_layer_feedback", ("tick",)),
    "_causal_mechanism": ("causal_mechanism_model", ("tick",)),
    "_long_horizon_planner": ("long_horizon_planner", ("tick",)),
    "_flux_mind_model": ("flux_mind_model", ("tick",)),
    "_narrative_compression": ("narrative_compression", ("tick",)),
    "_meta_learning_audit": ("meta_learning_audit", ("tick",)),
    "_structural_coupling": ("structural_coupling", ("tick",)),
    "_temporal_self_projection": ("temporal_self_projection", ("tick",)),
    "_autonomous_reflection": ("autonomous_reflection", ("tick",)),
    "_proactive_outreach": ("proactive_outreach", ("tick",)),
    "_autonomous_curiosity_resolver": ("autonomous_curiosity_resolver", ("tick",)),
    "_auto_experiment": ("autonomous_experimentation", ("tick",)),
    "_capability_development": ("capability_development", ("tick",)),
    "_cognitive_restructuring": ("cognitive_restructuring", ("tick",)),
    "_counterfactual_sim": ("counterfactual_simulator", ("tick",)),
    "_introspective_observer": ("introspective_observer", ("tick",)),
    "_cognitive_audit": ("cognitive_audit", ("tick",)),
    "_cognitive_immune": ("cognitive_immune", ("tick",)),
    "_flux_engine": ("cognitive_flux_engine", ("compute_and_write",)),
    "_attention_engine": ("cognitive_attention_engine", ("compute_and_write", "update_from_feedback", "update_from_context_feedback", "decay_bias", "decay_context")),
}


def _llm_available(ai_sys: Any) -> bool:
    """
    Critical fix (cognitive dashboard audit, 2026-06):
    Lazy-init guards throughout this loop previously checked
    `getattr(_ai_sys, 'client', None) is not None`. `_ai_sys` is an
    EnhancedAISystem instance, which has NO `.client` attribute — only
    `EnhancedAISystem.llm` (an EnhancedLLM or ExternalLLMAdapter) has
    `.client` / `.is_available()`. The old check was always False,
    permanently disabling MotivationalField, AspirationalSynthesisEngine,
    GenerativeAspirationEngine, CausalMechanismModel, LongHorizonPlanner,
    NarrativeCompression, MetaLearningAudit, StructuralCoupling,
    FluxMindModel, CognitiveResourceEconomy, TemporalSelfProjection, and
    CognitiveFluxEngine/CognitiveAttentionEngine regardless of cycle count.
    This helper correctly delegates to `ai_sys.llm.is_available()`.
    """
    if ai_sys is None:
        return False
    llm = getattr(ai_sys, 'llm', None)
    if llm is None:
        return False
    try:
        return bool(llm.is_available())
    except Exception:
        return False

# ── Cycle timing constants ────────────────────────────────────────────────────
FAST_CYCLE_SECONDS      = 30    # lightweight maintenance (energy regen, decay)
SLOW_CYCLE_SECONDS      = 120   # deeper inspection + reflection
MIN_SLOW_INTERVAL       = 45    # minimum seconds between slow cycles
TENSION_ACTIVATE        = 0.80  # tension must reach this to trigger early cycle
TENSION_DEACTIVATE      = 0.60  # tension must fall below this to stop triggering
REFLECTION_EVERY_N    = 6     # run reflection every N slow cycles


class InternalThoughtLoop:
    """
    Background cognitive loop for PandoraBOX.

    Usage
    -----
    loop = InternalThoughtLoop(organism)
    loop.start()

    # ... application runs ...

    loop.shutdown()
    """

    def __setattr__(self, name: str, value: Any) -> None:
        """Attach a tick probe as soon as a lazily-created module is installed.

        Refreshing only at the end of a slow cycle misses a module's first
        invocation when construction and ``tick()`` happen in the same cycle.
        The assignment is the earliest common point that preserves the
        existing lazy-init flow while making that first call observable.
        """
        object.__setattr__(self, name, value)
        if name in _TICK_PROBES and getattr(self, "_module_tick_log", None) is not None:
            self._refresh_module_tick_probes(name)

    @staticmethod
    def _phase2_thread_is_resolved(thread: Any) -> bool:
        """Accept the TTE's actual terminal enum value as well as legacy labels."""
        status = getattr(thread, "status", None)
        status_value = getattr(status, "value", status)
        return str(status_value or "").strip().casefold() in {"completed", "resolved"}

    @staticmethod
    def _phase2_thread_identity_linked(thread: Any) -> bool:
        state = getattr(thread, "current_state", None)
        return bool(
            getattr(thread, "_identity_linked", False)
            or (isinstance(state, dict) and state.get("identity_linked"))
        )

    @staticmethod
    def _phase2_identity_link_result_succeeded(result: Any) -> bool:
        """A linker result is usable only when it has the documented result shape."""
        return isinstance(result, dict) and all(
            isinstance(result.get(key), list)
            for key in ("beliefs_changed", "traits_changed", "confidence_updates", "narrative_updates")
        )

    def _phase2_governor_skip_metrics(self, subsystem: str) -> dict[str, Any]:
        """Capture why the governor denied a Phase 2 enrichment stage."""
        evidence: dict[str, Any] = {"governor_subsystem": subsystem}
        governor = getattr(self, "_governor", None)
        status_fn = getattr(governor, "status", None)
        if not callable(status_fn):
            return evidence
        try:
            status = status_fn()
        except Exception:
            return evidence
        mode = getattr(status, "mode", None)
        pressure = getattr(status, "total_pressure", None)
        budget_remaining = getattr(status, "budget_remaining", None)
        if isinstance(mode, str):
            evidence["governor_mode"] = mode
        if isinstance(pressure, (int, float)):
            evidence["governor_pressure"] = round(float(pressure), 4)
        if isinstance(budget_remaining, int):
            evidence["governor_budget_remaining"] = budget_remaining
        blocked = getattr(status, "blocked_systems", ())
        prefix = f"{subsystem}("
        reason = next(
            (item[len(prefix):-1] for item in reversed(blocked)
             if isinstance(item, str) and item.startswith(prefix) and item.endswith(")")),
            None,
        )
        if reason:
            evidence["governor_block_reason"] = reason
        return evidence

    def _publish_phase2_narrative(
        self, narrative: str, workspace: Any, narrative_output_ref: str | None,
    ) -> None:
        """Record delivery separately from synthesis, using workspace admission result."""
        broadcast = getattr(workspace, "broadcast", None)
        if not callable(broadcast):
            self._record_cycle_stage(
                "phase2_narrative_workspace_broadcast", "unavailable",
                inputs={"narrative_output_ref": narrative_output_ref},
                output={
                    "narrative_present": True,
                    "workspace_broadcast": False,
                    "delivery_status": "workspace_unavailable",
                },
            )
            return
        try:
            admitted = broadcast(
                source="v33.narrative_synthesizer",
                content=narrative,
                priority=0.65,
            ) is True
        except Exception as exc:
            self._record_cycle_stage(
                "phase2_narrative_workspace_broadcast", "failed",
                inputs={"narrative_output_ref": narrative_output_ref},
                output={
                    "narrative_present": True,
                    "workspace_broadcast": False,
                    "delivery_status": "broadcast_error",
                },
                metrics={
                    "error_type": type(exc).__name__,
                    "error_summary": self._exception_summary(exc),
                },
            )
            return
        self._record_cycle_stage(
            "phase2_narrative_workspace_broadcast",
            "admitted" if admitted else "rejected",
            inputs={"narrative_output_ref": narrative_output_ref},
            output={
                "narrative_present": True,
                "workspace_broadcast": admitted,
                "delivery_status": "admitted" if admitted else "rejected",
            },
        )

    @staticmethod
    def _goal_action_receipt(report: Any, executor: Any) -> dict[str, Any] | None:
        """Use the action report, or its explicit no-action reason, in cycle evidence."""
        if isinstance(report, dict):
            return report
        outcome = getattr(executor, "_last_tick_outcome", None)
        return outcome if isinstance(outcome, dict) else None

    def _goal_action_selection_evidence(
        self, report: Any, *, decision_is_fresh: bool,
    ) -> dict[str, Any]:
        """Expose which selection path chose an action, without goal text/IDs."""
        goal_id = report.get("goal_id") if isinstance(report, dict) else None
        return {
            "selection_source": (
                "workspace_winner" if decision_is_fresh else "active_goal_fallback"
            ),
            "selected_goal_id_ref": self._evidence_fingerprint(goal_id) if goal_id else None,
        }

    def _link_phase2_thread(self, thread: Any) -> dict[str, Any] | None:
        """Link one terminal thread and persist its marker only after a valid result."""
        if (
            self._phase2 is None
            or not self._phase2_thread_is_resolved(thread)
            or self._phase2_thread_identity_linked(thread)
        ):
            return None
        payload = {
            "id": getattr(thread, "id", ""),
            "name": getattr(thread, "topic", ""),
            "type": getattr(thread, "type", "unknown"),
            "status": "resolved",
            "resolution": {"conclusion": getattr(thread, "conclusion", "")},
            "resolved_at": datetime.now().isoformat(),
        }
        results = self._phase2.link_resolved_threads([payload])
        result = results[0] if isinstance(results, list) and results else None
        if not self._phase2_identity_link_result_succeeded(result):
            return None

        state = getattr(thread, "current_state", None)
        if not isinstance(state, dict):
            state = {}
            thread.current_state = state
        marker_was_present = "identity_linked" in state
        previous_marker = state.get("identity_linked")
        previous_attribute = getattr(thread, "_identity_linked", None)
        state["identity_linked"] = True
        thread._identity_linked = True
        try:
            if self._tte and callable(getattr(self._tte, "_save", None)):
                self._tte._save()
        except Exception:
            if marker_was_present:
                state["identity_linked"] = previous_marker
            else:
                state.pop("identity_linked", None)
            if previous_attribute is None:
                try:
                    delattr(thread, "_identity_linked")
                except AttributeError:
                    pass
            else:
                thread._identity_linked = previous_attribute
            raise
        return result

    def __init__(self, organism: "CognitiveOrganism"):
        self._organism = organism
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._slow_cycle_count = 0
        self._last_fast_cycle_at = 0.0
        self._fast_cycle_error_count = 0
        self._last_slow_cycle_at = 0.0
        self._slow_cycle_error_count = 0
        self._last_slow_cycle_error_type = ""
        self._pending_thoughts: list[str] = []   # queued for next interaction
        self._lock = threading.Lock()
        from core.module_tick_log import ModuleTickLog
        self._module_tick_log = ModuleTickLog()
        self._module_tick_wrapped: set[tuple[int, str]] = set()
        # Human turns can arrive before the first slow-cycle tick. Create the
        # resource ledger now so CognitiveOrganism can charge that first turn;
        # slow-cycle initialization remains as a retry if startup fails.
        self._resource_economy = None
        self._ensure_resource_economy()
        # Per-cycle causal evidence complements the long-lived aggregate tick
        # counters. Keep only bounded, content-free hashes and stage metadata.
        self._cycle_evidence_lock = threading.RLock()
        self._cycle_evidence: deque[dict[str, Any]] = deque(maxlen=40)
        self._active_cycle_evidence: dict[str, Any] | None = None
        self._active_cycle_thread_id: int | None = None
        # Predictive models are shared by the background cycle and the live
        # response path. A first chat turn may arrive before slow-cycle
        # initialization, so create them on demand under a dedicated lock.
        self._predictive_models_lock = threading.Lock()
        # Proposal-driven capability experiments run only in the slow loop.
        self._capability_development = None

        # Bug fix (v59): _slow_cycle_count had no persistence at all —
        # every restart reset it to 0. This single counter gates a whole
        # cluster of systems: CognitiveAuditEngine (AUDIT_EVERY_N=40, then
        # TRIAL_DURATION_CYCLES=60 more before a trial resolves — ~100
        # cycles before anything can ever be "confirmed"/"committed"),
        # MetaLearningAudit (registers at 50, needs META_WINDOW=40 more —
        # ~150-200+ cycles before its first verdict), StructuralCoupling
        # (COUPLING_EVERY_N=90), and LongHorizonPlanner (PLAN_EVERY_N=70).
        # Dashboard captures across this whole debugging session never
        # once showed a cycle count above ~90 — consistent with restarts
        # (routine in this dev workflow) repeatedly knocking the counter
        # back to 0 before any of these could ever fire, independent of
        # how much real runtime/usage had actually accumulated overall.
        #
        # Bug fix (v116): the v59 fix used ONE hardcoded path for that
        # persisted counter — "data/persona/internal_loop_state.json".
        # config.json (master, PERSONA_NAME="PandoraBOX") and config_Flux.json
        # (the Flux peer) both point MEMORY_PERSONA_PATH at the SAME
        # data/persona directory (correct — they intentionally share
        # persona/semantic memory). But each process runs its OWN
        # independent InternalLoop on its own thread, at its own cadence,
        # and _save_cycle_state() writes on EVERY slow cycle from BOTH
        # processes. So master and Flux were racing on one file: whichever
        # process ticked last silently reset the shared counter to its OWN
        # (often much lower) count, knocking every slow_cycle_count > N
        # gate below back under threshold for the other process —
        # independent of any actual restart. This is why a session that
        # had clearly run for thousands of cycles could show causal-
        # mechanism/counterfactual/introspective-observer panels abruptly
        # empty again mid-session. Per-instance filename (keyed by
        # PERSONA_NAME, the field that already distinguishes the configs)
        # gives each process its own counter, matching that this is
        # per-process runtime cadence, not shared persona knowledge.
        self._cycle_state_path = self._resolve_cycle_state_path()
        self._load_cycle_state()

        # ── TTE / CDE / DTS: executive cognition pipeline ─────────────────────
        # These three engines are the "commitment layer" that turns competing
        # signals into a single dominant thought per cycle.
        try:
            from cognition.thought_thread_engine       import ThoughtThreadEngine
            from cognition.cognitive_dissonance_engine import CognitiveDissonanceEngine
            from cognition.dominant_thought_selector   import DominantThoughtSelector
            from cognition.meta_thread_evaluator       import MetaThreadEvaluator
            from cognition.narrative_arc_writer        import NarrativeArcWriter
            self._tte = ThoughtThreadEngine()
            self._cde = CognitiveDissonanceEngine()
            self._dts = DominantThoughtSelector()
            self._mte = MetaThreadEvaluator()
            self._naw = NarrativeArcWriter()
            logger.info("[InternalLoop] TTE/CDE/DTS/MTE/NAW executive pipeline ready")
        except Exception as _e:
            self._tte = None
            self._cde = None
            self._dts = None
            self._mte = None
            self._naw = None
            logger.warning(f"[InternalLoop] TTE/CDE/DTS/MTE/NAW init failed (non-fatal): {_e}")

        # ── V32: Phase 1 Orchestrator ──────────────────────────────────────────
        # The Phase 1 cognitive enhancement layer that adds:
        # - Unified decision pressure from all cognitive factors
        # - Thought evaluation and goal creation
        # - Thread resolution to prevent infinite loops
        # - Complete cognitive cycle integration
        try:
            from core.phase1_integration import Phase1Orchestrator
            # Phase 4.x: thread the organism's GlobalWorkspace through so
            # WorkspaceCompetition.compete() can publish active_hypotheses
            # instead of only the collapsed winner (see cognition/
            # global_workspace.py WorkspaceState / set_hypotheses()).
            _gw = getattr(self._organism, "workspace", None)
            _goal_engine = getattr(
                getattr(self._organism, "ai_system", None), "goal_engine", None
            )
            self._phase1 = Phase1Orchestrator(
                global_workspace=_gw, goal_engine=_goal_engine,
                thought_stream=getattr(self._organism, "thought_stream", None),
            )
            logger.info("[InternalLoop] V32 Phase 1 Orchestrator ready ✅")
        except Exception as _e:
            self._phase1 = None
            logger.warning(f"[InternalLoop] Phase 1 Orchestrator init failed (non-fatal): {_e}")

        # ── V33: Phase 2 Orchestrator ──────────────────────────────────────────
        try:
            from core.phase2_integration import Phase2Orchestrator
            self._phase2 = Phase2Orchestrator()
            logger.info("[InternalLoop] V33 Phase 2 Orchestrator ready ✅")
        except Exception as _e:
            self._phase2 = None
            logger.warning(f"[InternalLoop] Phase 2 Orchestrator init failed (non-fatal): {_e}")

        # ── V34: Phase 4 Components ────────────────────────────────────────────
        # Phase 4 adds contextual intelligence:
        # - GoalQualityFilter: prunes noise goals, boosts tension-aligned ones
        # - BeliefBootstrapper: populates identity from emotions/self_concept
        # - ThreadLifecycleManager: retires stuck threads, extracts beliefs
        try:
            from cognition.goal_quality_filter    import GoalQualityFilter
            from cognition.belief_bootstrapper     import BeliefBootstrapper
            from cognition.thread_lifecycle_manager import ThreadLifecycleManager
            from cognition.goal_consolidator        import GoalConsolidator
            from cognition.semantic_graph_cleaner  import SemanticGraphCleaner
            from cognition.contradiction_belief_reviser import ContradictionBeliefReviser
            self._goal_quality_filter    = GoalQualityFilter()
            self._belief_bootstrapper    = BeliefBootstrapper()
            self._thread_lifecycle_mgr   = ThreadLifecycleManager()
            self._goal_consolidator      = GoalConsolidator()
            self._semantic_graph_cleaner = SemanticGraphCleaner()
            # Closes the contradiction feedback loop: pending contradictions
            # get confronted, the underlying belief is revised (identity
            # actually updates), and the entry is marked confronted so it
            # stops re-generating the same goal forever.
            self._contradiction_reviser = ContradictionBeliefReviser(
                self._organism,
                getattr(self._organism, "ai_system", None),
            )
            logger.info("[InternalLoop] V34 Phase 4 components ready ✅")
        except Exception as _e:
            self._goal_quality_filter    = None
            self._belief_bootstrapper    = None
            self._thread_lifecycle_mgr   = None
            self._goal_consolidator      = None
            self._semantic_graph_cleaner = None
            self._contradiction_reviser  = None
            logger.warning(f"[InternalLoop] Phase 4 components init failed (non-fatal): {_e}")

        # ── V35: Phase 5 Components ────────────────────────────────────────────
        # Phase 5 adds cognitive accuracy:
        # - SelfConceptSynchronizer: raises self-model coherence
        # - PersistentExecutiveLoop (5.1): re-checks whether each active
        #   goal's originating pressure/trait still holds, adjusts priority
        # - ArbitrationLearningTracker (5.4): learns UTILITY_WEIGHTS from
        #   whether past arbitration decisions actually turned out well
        try:
            from cognition.self_concept_synchronizer import SelfConceptSynchronizer
            from cognition.persistent_executive_loop  import PersistentExecutiveLoop
            from cognition.arbitration_learning       import get_tracker
            self._self_concept_sync   = SelfConceptSynchronizer()
            self._persistent_exec_loop = PersistentExecutiveLoop()
            # Share the exact tracker used by executive_arbitration's
            # get_learned_weights(). A separate instance would persist review
            # deltas to disk while the arbitration singleton kept stale weights
            # in memory until the next process restart.
            self._arbitration_learning = get_tracker()
            logger.info("[InternalLoop] V35 Phase 5 components ready ✅")
        except Exception as _e:
            self._self_concept_sync   = None
            self._persistent_exec_loop = None
            self._arbitration_learning = None
            logger.warning(f"[InternalLoop] Phase 5 components init failed (non-fatal): {_e}")

        # ── Cognitive Governor ─────────────────────────────────────────────────
        try:
            from core.cognitive_governor import CognitiveGovernor
            self._governor = CognitiveGovernor()
            logger.info("[InternalLoop] CognitiveGovernor ready ✅")
        except Exception as _ge:
            self._governor = None
            logger.warning(f"[InternalLoop] CognitiveGovernor init failed (non-fatal): {_ge}")

        # ── GoalActionExecutor ─────────────────────────────────────────────────
        # Translates active goals into concrete actions: web_search, user_question,
        # memory_recall, self_question. Initialised lazily (organism needed).
        self._goal_action_executor = None
        self._action_every_n = 3   # run executor every N slow cycles (~6 min)
        self._commitment_layer = None   # DecisionCommitmentLayer — lazy init
        # Multi-causal tension restructuring; created lazily after organism init.
        self._cognitive_restructuring = None

        # ── AutonomousReflectionEngine — LLM-based self-understanding ─────────
        # Runs LLM calls at priority=3 (background, preempted by user calls)
        # to generate novel linguistic understanding of the system's evolution.
        # Initialised lazily after first slow cycle so ai_system is fully ready.
        self._autonomous_reflection: Optional["AutonomousReflectionEngine"] = None

        # ── ProactiveOutreachEngine — contact users when relevant ─────────────
        self._proactive_outreach: Optional["ProactiveOutreachEngine"] = None

        # ── AutonomousCuriosityResolver — Phase 5.0, promotes curiosity into goals
        self._autonomous_curiosity_resolver: Optional["AutonomousCuriosityResolver"] = None
        self._refresh_module_tick_probes()

    def _ensure_resource_economy(self):
        """Resolve the interaction-cost ledger before either turn or slow tick."""
        if self._resource_economy is not None:
            return self._resource_economy
        try:
            from cognition.cognitive_resource_economy import CognitiveResourceEconomy
            self._resource_economy = CognitiveResourceEconomy()
            if getattr(self, "_module_tick_log", None) is not None:
                self._refresh_module_tick_probes(only_attr="_resource_economy")
            logger.info("[InternalLoop] CognitiveResourceEconomy ready ✅")
        except Exception as error:
            logger.warning("[InternalLoop] CognitiveResourceEconomy init failed: %s", type(error).__name__)
            self._resource_economy = None
        return self._resource_economy

    def _refresh_module_tick_probes(self, only_attr: str | None = None) -> None:
        """Attach bounded probes to known module entrypoints, without logging each tick."""
        for attr_name, (module_name, methods) in _TICK_PROBES.items():
            if only_attr is not None and attr_name != only_attr:
                continue
            module = getattr(self, attr_name, None)
            self._module_tick_log.register(
                module_name,
                initialized=module is not None,
                cadence="conditional slow-cycle / threshold gate",
            )
            if module is None:
                continue
            for method_name in methods:
                key = (id(module), method_name)
                if key in self._module_tick_wrapped:
                    continue
                bound_method = getattr(module, method_name, None)
                if not callable(bound_method):
                    continue
                @wraps(bound_method)
                def observed(*args, __bound=bound_method, __module=module_name,
                             __module_instance=module,
                             __method=method_name,
                             **kwargs):
                    started = time.perf_counter()
                    try:
                        output = __bound(*args, **kwargs)
                    except Exception as exc:
                        duration_ms = (time.perf_counter() - started) * 1000
                        self._module_tick_log.record(
                            __module, __method, started_at=started,
                            duration_ms=duration_ms,
                            error=exc,
                        )
                        try:
                            self._record_cycle_stage(
                                f"module_tick:{__module}.{__method}", "failed",
                                inputs=self._cycle_input_evidence(args, kwargs),
                                metrics={
                                    "duration_ms": round(duration_ms, 2),
                                    "error_type": type(exc).__name__,
                                    "error_summary": self._exception_summary(exc),
                                },
                            )
                        except Exception:
                            pass
                        raise
                    duration_ms = (time.perf_counter() - started) * 1000
                    # Some entrypoints intentionally return None while keeping
                    # an explicit structured outcome on the module (for
                    # example GoalActionExecutor records why it did not act).
                    # Attribute that receipt to the tick instead of reporting
                    # an empty, unverified output. Preserve the public return
                    # value for the caller.
                    observed_output = output
                    if observed_output is None:
                        outcome_receipt = getattr(
                            __module_instance, "_last_tick_outcome", None
                        )
                        if isinstance(outcome_receipt, dict):
                            observed_output = outcome_receipt
                    self._module_tick_log.record(
                        __module, __method, started_at=started,
                        duration_ms=duration_ms,
                        output=observed_output,
                    )
                    try:
                        self._record_cycle_stage(
                            f"module_tick:{__module}.{__method}", "completed",
                            inputs=self._cycle_input_evidence(args, kwargs),
                            output=observed_output,
                            metrics={"duration_ms": round(duration_ms, 2)},
                        )
                    except Exception:
                        pass
                    return output

                observed.__lumina_module_tick_probe__ = True
                try:
                    setattr(module, method_name, observed)
                    self._module_tick_wrapped.add(key)
                except Exception:
                    # Keep the module visible as initialized but unobserved;
                    # never make a cognitive tick fail because instrumentation
                    # could not be attached.
                    logger.debug("Tick probe could not attach to %s.%s", module_name, method_name)

    def _cycle_input_evidence(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        """Hash bounded tick inputs so equal values can be linked across stages.

        Only type/shape summaries and digests enter the retained cycle trace;
        raw thought, memory, and user text are never copied into audit evidence.
        """
        def describe(value: Any) -> dict[str, Any]:
            return {
                "ref": self._evidence_fingerprint(value),
                "summary": self._evidence_summary(value),
            }

        return {
            "args": [describe(value) for value in args[:8]],
            "kwargs": {
                str(key)[:48]: describe(value)
                for key, value in list(kwargs.items())[:12]
            },
            "omitted_args": max(0, len(args) - 8),
            "omitted_kwargs": max(0, len(kwargs) - 12),
        }

    def module_tick_snapshot(self) -> dict[str, dict[str, Any]]:
        """Return live module existence plus observed tick/output-health evidence."""
        snapshot = self._module_tick_log.snapshot()
        for attr_name, (module_name, _methods) in _TICK_PROBES.items():
            module = getattr(self, attr_name, None)
            entry = snapshot.setdefault(module_name, {})
            entry["initialized"] = module is not None
            if module is None:
                # Every probe in this manifest is conditional/lazy. A None
                # reference before its cadence or feature gate runs means it
                # has not been constructed yet, not that the module failed.
                # Keep truly unavailable execution distinguishable through
                # failed stage receipts and import/init diagnostics.
                cadence = str(
                    entry.get("cadence") or "conditional slow-cycle / threshold gate"
                )
                entry["state"] = (
                    "not_initialized_conditional"
                    if "conditional" in cadence.casefold()
                    else "unavailable"
                )
            elif entry.get("tick_count", 0) == 0:
                entry["state"] = (
                    "skipped_by_policy" if entry.get("skip_count", 0)
                    else "initialized_unobserved"
                )
            elif entry.get("last_status") == "failed":
                entry["state"] = "error"
            else:
                quality = entry.get("last_output", {}).get("quality")
                entry["state"] = (
                    "degraded" if quality == "invalid_numeric" else
                    "output_unverified" if quality in {
                        "empty", "no_return_unverified", "shape_only", "unknown"
                    } else
                    "output_present_unvalidated"
                )
        return snapshot

    def module_tick_analysis(self) -> dict[str, Any]:
        """Summarize tick coverage and output integrity for the status API."""
        analysis = self._module_tick_log.analysis()
        states: dict[str, int] = {}
        executed = 0
        snapshot = self.module_tick_snapshot()
        for _attr, (module_name, _methods) in _TICK_PROBES.items():
            entry = snapshot.get(module_name, {})
            state = entry.get("state", "unknown")
            states[state] = states.get(state, 0) + 1
            executed += int(entry.get("tick_count", 0) > 0)
        analysis["module_count"] = len(_TICK_PROBES)
        analysis["executed_module_count"] = executed
        analysis["states"] = states
        return analysis

    @staticmethod
    def _evidence_fingerprint(value: Any) -> str | None:
        """Hash structured cycle values without retaining potentially private text."""
        try:
            payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":"), default=str)
        except Exception:
            return None
        return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:20]

    @staticmethod
    def _evidence_summary(value: Any) -> dict[str, Any]:
        """Return a deliberately small, non-text summary suitable for status APIs."""
        if isinstance(value, dict):
            summary: dict[str, Any] = {"kind": "mapping", "field_count": len(value)}
            for key in (
                "type", "status", "mode", "success", "created", "verified",
                "outcome_status", "reason_code", "skipped",
                "goal_state_persisted", "memory_retrieved", "thought_published",
                "thought_stream_recorded", "workspace_broadcast",
                "thought_id_ref",
                "source_thought_ref", "persisted_source_thought_ref",
                "proposal_source_thought_ref", "selected_candidate_ref",
                "research_item_queued", "hypothesis_generated",
                "source_thought_source", "source_thought_type", "source_concept_method",
                "drive_update", "need_scan", "pressure_source",
                "narrative_present", "delivery_status",
            ):
                item = value.get(key)
                if isinstance(item, (str, bool, int, float)):
                    if key == "reason_code" and isinstance(item, str) and not (
                        item.isascii() and item.replace("_", "").isalnum() and len(item) <= 64
                    ):
                        continue
                    summary[key] = item if not isinstance(item, str) else item[:48]
            allowed_actions = {
                "memory_recall", "self_question", "bisociative_hypothesis",
                "web_search", "user_question",
            }
            action = value.get("action")
            if isinstance(action, str) and action in allowed_actions:
                summary["action"] = action
            execution_id = value.get("execution_id")
            if isinstance(execution_id, str) and execution_id:
                summary["execution_ref"] = hashlib.sha256(
                    execution_id.encode("utf-8")
                ).hexdigest()[:20]
            safe_numeric_fields = {
                "active_goal_count", "total_goal_count", "goal_thought_count",
                "candidate_count", "accepted_candidate_count", "motivation_count",
                "user_topic_count", "filtered_topic_count", "active_thread_count",
                "broadcast_count", "requested_count", "total_pressure",
                "goal_count", "budget_total", "budget_remaining",
                "dormant_goal_count", "completed_goal_count", "archived_goal_count",
                "abandoned_goal_count", "low_quality_goal_count", "other_goal_count",
                "goal_records_seen", "created_count", "updated_count", "merged_count",
                "pre_active_goal_count", "pre_dormant_goal_count",
                "pre_completed_goal_count", "pre_archived_goal_count",
                "pre_abandoned_goal_count", "pre_low_quality_goal_count",
                "pre_other_goal_count", "pre_goal_records_seen",
                "post_active_goal_count", "post_dormant_goal_count",
                "post_completed_goal_count", "post_archived_goal_count",
                "post_abandoned_goal_count", "post_low_quality_goal_count",
                "post_other_goal_count", "post_goal_records_seen",
                "winning_margin", "score", "confidence", "priority", "override",
                "generation_blocked", "decision_fresh", "winner_age_cycles",
                "cycle", "previous_scan_cycle", "drive_count",
            }
            numeric_summary = {
                key: item for key, item in value.items()
                if key in safe_numeric_fields and isinstance(item, (bool, int, float))
            }
            if numeric_summary:
                summary["numeric_metrics"] = numeric_summary
            for key in ("all_candidates", "candidates", "goals", "threads"):
                item = value.get(key)
                if isinstance(item, (list, tuple)):
                    summary[f"{key}_count"] = len(item)
            candidate_refs = value.get("memory_recall_candidate_refs")
            if isinstance(candidate_refs, (list, tuple)):
                safe_refs = [
                    ref for ref in candidate_refs[:20]
                    if isinstance(ref, str) and re.fullmatch(r"[a-f0-9]{20}", ref)
                ]
                summary["memory_recall_candidate_refs"] = safe_refs
                summary["memory_recall_candidate_count"] = len(safe_refs)
            proposal_refs = value.get("goal_proposal_origin_refs")
            if isinstance(proposal_refs, (list, tuple)):
                safe_refs = [
                    ref for ref in proposal_refs[:20]
                    if isinstance(ref, str) and re.fullmatch(r"[a-f0-9]{20}", ref)
                ]
                summary["goal_proposal_origin_refs"] = safe_refs
                summary["goal_proposal_origin_count"] = len(safe_refs)
            return summary
        if isinstance(value, (list, tuple, set)):
            return {"kind": type(value).__name__, "item_count": len(value)}
        if value is None:
            return {"kind": "none"}
        return {"kind": type(value).__name__}

    @staticmethod
    def _thought_id_reference(thought_id: Any) -> str | None:
        """Hash one stable thought ID identically at every audit stage."""
        value = str(thought_id or "")
        if not value:
            return None
        return hashlib.sha256(
            value.encode("utf-8", errors="replace")
        ).hexdigest()[:20]

    @staticmethod
    def _memory_recall_candidate_refs(competition_output: Any) -> list[str]:
        """Hash IDs of recalled-memory thoughts actually admitted as candidates."""
        if not isinstance(competition_output, dict):
            return []
        competition = competition_output.get("competition", {})
        candidates = competition.get("all_candidates", []) if isinstance(competition, dict) else []
        refs: list[str] = []
        for candidate in candidates if isinstance(candidates, list) else []:
            if not isinstance(candidate, dict) or candidate.get("type") != "thought":
                continue
            source_data = candidate.get("source_data", {})
            if not isinstance(source_data, dict) or source_data.get("source") != "goal_action.memory_recall":
                continue
            thought_id = str(source_data.get("id") or "")
            if thought_id:
                ref = InternalThoughtLoop._thought_id_reference(thought_id)
                if not ref:
                    continue
                if ref not in refs:
                    refs.append(ref)
                if len(refs) >= 20:
                    break
        return refs

    @staticmethod
    def _goal_proposal_origin_refs(proposals: Any) -> list[str]:
        """Hash source thought IDs for admitted GoalEngine proposals."""
        refs: list[str] = []
        for proposal in proposals if isinstance(proposals, (list, tuple)) else []:
            if not isinstance(proposal, dict):
                continue
            thought_id = str(proposal.get("origin_thought") or "")
            if not thought_id:
                continue
            ref = InternalThoughtLoop._thought_id_reference(thought_id)
            if not ref:
                continue
            if ref not in refs:
                refs.append(ref)
            if len(refs) >= 20:
                break
        return refs

    @staticmethod
    def _workspace_decision_age_cycles(
        current_cycle: int, winner: Any, winner_cycle: Any,
    ) -> int | None:
        """Return a meaningful age only for a real, cycle-stamped winner."""
        if not isinstance(winner, dict):
            return None
        try:
            source_cycle = int(winner_cycle)
        except (TypeError, ValueError, OverflowError):
            return None
        if source_cycle < 0 or source_cycle > int(current_cycle):
            return None
        return int(current_cycle) - source_cycle

    @staticmethod
    def _selected_proposal_commit_admitted(
        winner: Any, commit_result: Any,
    ) -> bool:
        """Only let a thought proposal create durable focus after verified admission."""
        source_data = winner.get("source_data", {}) if isinstance(winner, dict) else {}
        proposal = source_data.get("_goal_proposal") if isinstance(source_data, dict) else None
        if not isinstance(proposal, dict):
            return True
        if not isinstance(commit_result, dict) or not commit_result.get("verified"):
            return False
        return bool(
            commit_result.get("created")
            or commit_result.get("reason") == "existing_goal"
        )

    @staticmethod
    def _proposal_focus_admission_evidence(
        winner: Any, admitted: bool,
    ) -> tuple[str, dict[str, Any]]:
        """Report proposal admission only when the winner actually had a proposal."""
        source_data = winner.get("source_data", {}) if isinstance(winner, dict) else {}
        proposal = source_data.get("_goal_proposal") if isinstance(source_data, dict) else None
        if not isinstance(proposal, dict):
            return "not_applicable", {"applicable": False}
        return (
            "admitted" if admitted else "rejected",
            {"applicable": True, "admitted": bool(admitted)},
        )

    @staticmethod
    def _workspace_focus_for_consumers(winner: Any, admitted: bool) -> Any:
        """Do not expose a rejected goal proposal as an active cognitive focus."""
        source_data = winner.get("source_data", {}) if isinstance(winner, dict) else {}
        proposal = source_data.get("_goal_proposal") if isinstance(source_data, dict) else None
        if isinstance(proposal, dict) and not admitted:
            # Keep the original candidate in this cycle's competition and
            # arbitration receipts. Publish only a neutral, authoritative
            # observation so prompt, presence and action consumers cannot
            # mistake the rejected topic for a current focus or fall back to
            # an unrelated older goal.
            return {
                "type": "rejected_proposal",
                "proposal_admission": "rejected",
                "name": "",
                "topic": "",
                "score": 0.0,
            }
        return winner

    @staticmethod
    def _empty_workspace_focus(reason: str) -> dict[str, Any]:
        """Represent an explicit absence of focus without leaving stale state."""
        return {
            "type": "no_winner",
            "proposal_admission": str(reason)[:48],
            "name": "",
            "topic": "",
            "score": 0.0,
        }

    @staticmethod
    def _publish_global_workspace_focus(
        organism: Any, winner: Any, planner: Any = None,
    ) -> dict[str, Any] | None:
        """Publish the post-arbitration focus and its existing plan to shared state."""
        workspace = getattr(organism, "workspace", None)
        update_state = getattr(workspace, "update_state", None)
        if not callable(update_state):
            return None

        winner = winner if isinstance(winner, dict) else {}
        kind = str(winner.get("type") or "")
        focus_value = winner.get("topic") or winner.get("name")
        focus = str(focus_value).strip()[:240] if focus_value else None
        intention = None

        # Only expose an intention when the selected persistent goal already
        # has an active planner record. Do not invent a plan as a telemetry side effect.
        goal_id = str(winner.get("id") or "") if kind == "goal" else ""
        if goal_id and planner is not None and callable(getattr(planner, "status", None)):
            try:
                plans = planner.status().get("plans", [])
                plan = next((item for item in plans if (
                    item.get("domain") == f"goal:{goal_id}"
                    and item.get("status") == "active"
                )), None)
                if plan:
                    objective = str(plan.get("objective") or focus or "").strip()
                    next_step = str(plan.get("next") or "").strip()
                    if objective:
                        intention = f"{objective} — next: {next_step}" if next_step and next_step != "done" else objective
            except Exception as exc:
                logger.debug("[InternalLoop] shared intention read failed: %s", exc)

        update_state(
            "workspace_competition",
            focus=focus,
            intention=intention,
        )
        getter = getattr(workspace, "get_state", None)
        return getter().to_dict() if callable(getter) else None

    def _publish_empty_workspace_focus(
        self, organism: Any, *, reason: str, status: str,
        inputs: dict[str, Any] | None = None,
    ) -> str | None:
        """Replace prior focus and bind the explicit empty result to this cycle."""
        empty_focus = self._empty_workspace_focus(reason)
        organism._v32_workspace_winner = empty_focus
        organism._v32_workspace_winner_cycle = self._slow_cycle_count
        self._publish_global_workspace_focus(organism, empty_focus)
        evidence_ref = self._record_cycle_stage(
            "winner_published_to_workspace_state", status,
            inputs=inputs,
            output={"published_winner": empty_focus},
        )
        organism._v32_workspace_winner_evidence_ref = evidence_ref
        organism._v32_workspace_winner_evidence_cycle = self._slow_cycle_count
        return evidence_ref

    def _begin_cycle_evidence(self, cycle_id: int) -> None:
        with self._cycle_evidence_lock:
            self._active_cycle_evidence = {
                "cycle_id": int(cycle_id),
                "started_at": time.time(),
                "status": "running",
                "stages": [],
            }
            self._active_cycle_thread_id = threading.get_ident()

    @staticmethod
    def _exception_summary(exc: BaseException, limit: int = 240) -> str:
        """Return bounded diagnostic text without common credential forms."""
        message = " ".join(str(exc).replace("\r", " ").replace("\n", " ").split())
        message = re.sub(
            r"(?i)\b(password|passwd|token|api[_-]?key|secret)\b\s*[:=]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            message,
        )
        message = re.sub(
            r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", message,
        )
        message = re.sub(
            r"(?i)(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", message,
        )
        return message[:max(0, int(limit))]

    def _record_cycle_stage(
        self, stage: str, status: str, *, inputs: dict[str, Any] | None = None,
        output: Any = None, metrics: dict[str, Any] | None = None,
    ) -> str | None:
        """Record a stage and explicit consumer references in the active slow cycle."""
        lock = getattr(self, "_cycle_evidence_lock", None)
        if lock is None:
            return None
        with lock:
            receipt = getattr(self, "_active_cycle_evidence", None)
            if receipt is None or getattr(self, "_active_cycle_thread_id", None) != threading.get_ident():
                return None
            if len(receipt["stages"]) >= 256:
                receipt["omitted_stage_count"] = receipt.get("omitted_stage_count", 0) + 1
                return None
            output_ref = self._evidence_fingerprint(output) if output is not None else None
            entry: dict[str, Any] = {
                "stage": str(stage),
                "status": str(status),
                "inputs": inputs or {},
                "output_ref": output_ref,
                "output_summary": (
                    self._evidence_summary(output) if output is not None else
                    {"kind": "none", "quality": "no_return_unverified"}
                ),
            }
            if metrics:
                entry["metrics"] = {
                    str(key): value for key, value in metrics.items()
                    if isinstance(value, (str, bool, int, float))
                }
            if status in {"skipped_cadence", "skipped_governor", "skipped_motivational_scan_running"}:
                tick_log = getattr(self, "_module_tick_log", None)
                if tick_log is not None:
                    probe_names = {value[0] for value in _TICK_PROBES.values()}
                    module_name = str(stage)
                    if module_name in {
                        "phase2_advanced_evaluation",
                        "phase2_narrative_synthesis",
                        "phase2_thread_identity_link",
                    }:
                        module_name = "phase2_orchestrator"
                    if module_name in probe_names:
                        tick_log.record_skip(module_name, status, metrics=metrics)
            receipt["stages"].append(entry)
            return output_ref

    def record_async_cycle_stage(
        self, cycle_id: int, stage: str, status: str, *,
        output: Any = None, metrics: dict[str, Any] | None = None,
        error_type: str | None = None,
    ) -> bool:
        """Attach a worker-thread result to its originating retained cycle."""
        lock = getattr(self, "_cycle_evidence_lock", None)
        if lock is None:
            return False
        with lock:
            receipt = self._active_cycle_evidence
            if receipt is None or int(receipt.get("cycle_id", -1)) != int(cycle_id):
                receipt = next(
                    (item for item in reversed(self._cycle_evidence)
                     if int(item.get("cycle_id", -1)) == int(cycle_id)),
                    None,
                )
            if receipt is None:
                return False
            if len(receipt["stages"]) >= 256:
                receipt["omitted_stage_count"] = receipt.get("omitted_stage_count", 0) + 1
                return False
            entry: dict[str, Any] = {
                "stage": str(stage),
                "status": str(status),
                "async_completion": True,
                "inputs": {"origin_cycle_id": int(cycle_id)},
                "output_ref": (
                    self._evidence_fingerprint(output) if output is not None else None
                ),
                "output_summary": (
                    self._evidence_summary(output) if output is not None else None
                ),
            }
            if metrics:
                entry["metrics"] = {
                    str(key): value for key, value in metrics.items()
                    if isinstance(value, (str, bool, int, float))
                }
            if error_type:
                entry["error_type"] = str(error_type)[:80]
            receipt["stages"].append(entry)
            return True

    @staticmethod
    def _broadcast_goal_thoughts(workspace: Any, thoughts: list[dict[str, Any]]) -> tuple[str, dict[str, int]]:
        """Report workspace admissions from the broadcast API's actual result."""
        admitted = 0
        errors = 0
        requested = len(thoughts)
        for thought in thoughts:
            try:
                accepted = workspace.broadcast(
                    source="goal_engine",
                    content=thought.get("content", ""),
                    priority=min(0.75, thought.get("priority", 0.5)),
                )
                if accepted is True:
                    admitted += 1
            except Exception:
                errors += 1

        rejected = requested - admitted - errors
        status = (
            "completed" if admitted == requested
            else "partial" if admitted
            else "failed" if errors == requested
            else "rejected"
        )
        return status, {
            "broadcast_count": admitted,
            "requested_count": requested,
            "rejected_count": rejected,
            "error_count": errors,
        }

    def _finish_cycle_evidence(
        self, status: str, error_type: str | None = None,
        error_summary: str | None = None,
    ) -> None:
        lock = getattr(self, "_cycle_evidence_lock", None)
        if lock is None:
            return
        with lock:
            receipt = getattr(self, "_active_cycle_evidence", None)
            if receipt is None:
                return
            receipt["status"] = status
            receipt["finished_at"] = time.time()
            receipt["duration_ms"] = round((receipt["finished_at"] - receipt["started_at"]) * 100…24934 tokens truncated…CognitiveStack tick error (non-fatal): {_cs}")

        # ── TTE → CDE → DTS: executive cognition pipeline ────────────────────
        # Fix #5: enforce cognitive selection every slow cycle.
        # One dominant thought is selected and stored on the organism so
        # CognitivePreProcessor can inject it into the next LLM prompt.
        # Fix #1: energy below 15% reduces intensity but never blocks this cycle.
        # Fix #2: curiosity → thread spawn → DTS selection → action.
        if self._tte is not None:
            try:
                from cognition.thought_thread_engine       import ThoughtThreadEngine
                from cognition.cognitive_dissonance_engine import CDEContext
                from cognition.dominant_thought_selector   import SelectorContext

                tte_ctx = ThoughtThreadEngine.collect_context(o)

                # 1. TTE step — advance/spawn/prune threads
                active_threads = self._tte.step(tte_ctx)
                _tte_evidence_ref = self._record_cycle_stage(
                    "thought_thread_engine", "completed", output=active_threads,
                    metrics={
                        "active_thread_count": len(active_threads) if hasattr(active_threads, "__len__") else -1,
                        "active_goal_seed_count": len(tte_ctx.world_state.get("goal_threads", [])),
                        "curiosity_seed_present": bool(tte_ctx.world_state.get("top_curiosity_topic")),
                        "vision_surprise_present": bool(tte_ctx.world_state.get("vision_surprise")),
                    },
                )

                # 2. CDE step — detect dissonance, spawn meta-threads
                ai_sys  = getattr(o, "ai_system", None)
                beliefs = []
                try:
                    sc = getattr(ai_sys, "self_concept", None) if ai_sys else None
                    if sc:
                        beliefs = [b.statement for b in sc._beliefs.values()]
                except Exception:
                    pass
                wm_data  = {}
                try:
                    wm = getattr(ai_sys, "world_model", None) if ai_sys else None
                    if wm is None:
                        wm = getattr(o, "world_model", None)
                    if wm:
                        wm_data = {
                            "causal_beliefs": [
                                {"antecedent": b.antecedent,
                                 "consequent": b.consequent,
                                 "confidence": b.confidence,
                                 "evidence_status": getattr(b, "evidence_status", "legacy_unverified"),
                                 "evidence_method": getattr(b, "evidence_method", ""),
                                 "evidence_source": getattr(b, "evidence_source", ""),
                                 "evidence_ref": getattr(b, "evidence_ref", ""),
                                 "evidence_intervention": getattr(b, "evidence_intervention", ""),
                                 "evidence_comparison": getattr(b, "evidence_comparison", ""),
                                 "evidence_outcome": getattr(b, "evidence_outcome", ""),
                                 "evidence_comparison_outcome": getattr(
                                     b, "evidence_comparison_outcome", ""
                                 )}
                                for b in wm.causal_beliefs[:20]
                            ]
                        }
                except Exception:
                    pass
                recent_action_receipts = []
                try:
                    from cognition.consequence_tracker import get_consequence_tracker
                    _consequence_tracker = get_consequence_tracker(o)
                    _receipt_reader = getattr(
                        _consequence_tracker, "recent_action_receipts", None
                    )
                    if callable(_receipt_reader):
                        recent_action_receipts = _receipt_reader(limit=20)
                except Exception as _receipt_error:
                    logger.debug(
                        "[InternalLoop] CDE action receipts unavailable: %s",
                        type(_receipt_error).__name__,
                    )
                cde_ctx = CDEContext(
                    threads        = active_threads,
                    world_model    = wm_data,
                    beliefs        = beliefs,
                    action_receipts = recent_action_receipts,
                    metrics        = tte_ctx.metrics,
                    predictive_mind = getattr(o, "predictive_mind", None),
                )
                active_threads = self._cde.step(
                    threads  = active_threads,
                    tte      = self._tte,
                    ctx      = cde_ctx,
                    tte_ctx  = tte_ctx,
                    organism = o,
                )
                _cde_report = dict(getattr(self._cde, "last_step_report", {}) or {})
                _cde_event_refs = _cde_report.get("event_refs", [])
                _cde_evidence_ref = self._record_cycle_stage(
                    "cognitive_dissonance_engine", "completed",
                    inputs={
                        "thread_state_ref": _tte_evidence_ref,
                        "action_receipt_count": len(recent_action_receipts),
                    },
                    output=active_threads,
                    metrics={
                        "active_thread_count": len(active_threads) if hasattr(active_threads, "__len__") else -1,
                        "action_receipt_count": len(recent_action_receipts),
                        "detected_event_count": int(_cde_report.get("detected_event_count", 0)),
                        "reobserved_event_count": int(_cde_report.get("reobserved_event_count", 0)),
                        "meta_threads_spawned": int(_cde_report.get("meta_threads_spawned", 0)),
                        "auto_resolved_event_count": int(_cde_report.get("auto_resolved_event_count", 0)),
                        "deferred_low_intensity_count": int(_cde_report.get("deferred_low_intensity_count", 0)),
                        "verified_resolved_event_count": int(_cde_report.get("verified_resolved_event_count", 0)),
                        "event_ids": ",".join(str(item.get("id", "")) for item in _cde_event_refs
                                              if isinstance(item, dict) and item.get("id")),
                        "event_types": ",".join(str(item.get("type", "")) for item in _cde_event_refs
                                                if isinstance(item, dict) and item.get("type")),
                    },
                )

                # 3. DTS — select dominant thought
                sel_ctx = SelectorContext(
                    threads         = active_threads,
                    metrics         = tte_ctx.metrics,
                    pressures       = tte_ctx.pressures,
                    curiosity_level = tte_ctx.curiosity_level,
                    energy          = tte_ctx.energy,
                )
                result = self._dts.select(sel_ctx)
                _dts_evidence_ref = self._record_cycle_stage(
                    "dominant_thought_selector", "completed",
                    inputs={"thread_state_ref": _cde_evidence_ref},
                    output=result,
                )

                # Publish the selection for both legacy AgentController and
                # the primary PersonaBridge prompt path. Keep provenance so a
                # later chat turn can reject stale/unverifiable selections.
                o._dominant_thought = result
                o._dominant_thought_cycle = self._slow_cycle_count
                o._dominant_thought_updated_at = time.time()
                self._record_cycle_stage(
                    "dominant_thought_published", "completed",
                    inputs={"selector_output_ref": _dts_evidence_ref},
                    output={"has_dominant": bool(getattr(result, "dominant", None))},
                )

                # ── MetaThreadEvaluator: conscious oversight of thread quality ──
                # Evaluates whether the dominant thread is actually progressing,
                # calibrated, or drifting — then feeds findings back into
                # MetaCognition and stores a directive for the next system prompt.
                if self._mte is not None:
                    try:
                        _meta_cog = getattr(
                            getattr(o, 'ai_system', None),
                            'meta_cognition', None
                        ) or getattr(o, 'meta_cognition', None)
                        _mte_report = self._mte.evaluate(
                            selection_result = result,
                            active_threads   = active_threads,
                            meta_cognition   = _meta_cog,
                        )
                        o._meta_thread_report = _mte_report
                        if _mte_report.meta_directive:
                            logger.debug(
                                f"[MTE] Directive: {_mte_report.meta_directive[:80]!r}"
                            )
                    except Exception as _mte_e:
                        logger.debug(f"[InternalLoop] MTE error (non-fatal): {_mte_e}")

                if result.dominant:
                    logger.debug(
                        f"[InternalLoop] Dominant thought: {result.dominant.topic!r} "
                        f"— {result.rationale}"
                    )
                    # Broadcast to GlobalWorkspace ONLY when topic changes.
                    # Broadcasting identical content every 2 min floods the GW
                    # with duplicate items that tank CCS (consecutive items from
                    # different sources have zero bigram overlap).
                    _new_topic = result.dominant.topic
                    _last_broadcast = getattr(self, '_last_dominant_broadcast', '')
                    if _new_topic != _last_broadcast and hasattr(o, "workspace"):
                        try:
                            o.workspace.broadcast(
                                source   = "dominant_thought",
                                content  = result.dominant.to_prompt_line(),
                                priority = 0.80,
                            )
                            self._last_dominant_broadcast = _new_topic
                        except Exception:
                            pass

                    # Feed dominant goal text into observatory response buffer.
                    # Cognitive genome (Agency, Curiosity, Self-Reference) is
                    # computed from last-10 LLM responses. During idle cycles no
                    # real responses are produced so the buffer is empty → all
                    # genome values stay at 5%.
                    # THROTTLE: inject only every 4th slow cycle to avoid
                    # overcorrecting to 95% (which causes IDX drift).
                    # Include introspection words to lift that genome dimension too.
                    _feed_cycle = self._slow_cycle_count % 4 == 0
                    if _feed_cycle:
                        try:
                            obs = getattr(o, "observatory", None)
                            if obs:
                                # Use balanced text: enough curiosity/introspection
                                # words to keep the genome alive, but without flooding
                                # self-reference (5x "I/want/decide/choose" → self_ref=95%).
                                # Aim: curiosity↑ introspection↑ self_ref~35% (natural)
                                goal_text = (
                                    f"Exploring {result.dominant.topic} feels genuinely fascinating to me. "
                                    f"There is something worth understanding here that my attention keeps returning to. "
                                    f"The question invites reflection and deeper curiosity."
                                )
                                obs.record_response(goal_text)
                        except Exception:
                            pass

                # ── NarrativeArcWriter: connect cognitive events to autobiography ──
                if self._naw is not None:
                    try:
                        _ni = getattr(
                            getattr(o, 'ai_system', None),
                            'narrative_identity', None
                        ) or getattr(o, 'narrative_identity', None)

                        # 1. Watch for newly completed/failed threads
                        for _t in self._naw.pending_thread_resolutions(
                            self._tte.all_threads()
                        ):
                            self._naw.watch_thread_resolution(_t, _ni)

                        # 2. Watch for resolved CDE events → belief chapters
                        for _ev in self._cde._events:
                            if getattr(_ev, 'resolved', False):
                                self._naw.watch_cde_resolution(_ev, _ni, o)

                        # 3. Watch MTE for stall-overcome events
                        if o._meta_thread_report is not None:
                            da = getattr(o._meta_thread_report, 'dominant_assessment', None)
                            dom = getattr(result, 'dominant', None)
                            if da and dom and da.is_stalled is False and da.progress_rate > 0.05:
                                self._naw.watch_mte_stall_overcome(dom, _ni)

                        # 4. Synthesise arc every 6th slow cycle (~12 min)
                        if self._slow_cycle_count % 6 == 0:
                            self._naw.synthesise_arc(_ni)

                    except Exception as _naw_e:
                        logger.debug(f"[InternalLoop] NAW error (non-fatal): {_naw_e}")

                # ── V33: Phase 2 Narrative Synthesis ──────────────────────────
                # Every 8 slow cycles (~16 minutes), synthesize coherent narrative
                _phase2_narrative_due = self._slow_cycle_count % 8 == 0
                _phase2_narrative_allowed = (
                    self._phase2 is not None
                    and _phase2_narrative_due
                    and (not self._governor or self._governor.may_run("Phase2Narrative"))
                )
                if self._phase2 is None:
                    self._record_cycle_stage("phase2_narrative_synthesis", "unavailable")
                elif not _phase2_narrative_due:
                    self._record_cycle_stage(
                        "phase2_narrative_synthesis", "skipped_cadence",
                        metrics={"cycle": self._slow_cycle_count, "interval_cycles": 8},
                    )
                elif not _phase2_narrative_allowed:
                    self._record_cycle_stage(
                        "phase2_narrative_synthesis", "skipped_governor",
                        metrics=self._phase2_governor_skip_metrics("Phase2Narrative"),
                    )
                else:
                    try:
                        # Build cycle data for narrative synthesis
                        cycle_data = {
                            'pressure': getattr(o, '_v32_decision_pressure', {}),
                            'goals': self._phase1._load_goals() if self._phase1 else [],
                            'emotions': getattr(
                                getattr(o, 'ai_system', None),
                                'emotional_state',
                                {}
                            ),
                            'traits': getattr(
                                getattr(o, 'self_model', None),
                                'personality_traits',
                                {}
                            ),
                            'energy_level': getattr(
                                getattr(o, 'energy', None),
                                'current',
                                1.0
                            )
                        }
                        
                        narrative = self._phase2.synthesize_narrative(cycle_data)
                        _narrative_ref = self._record_cycle_stage(
                            "phase2_narrative_synthesis",
                            "completed" if narrative else "no_narrative",
                            output={"narrative_present": bool(narrative)},
                        )
                        
                        if narrative:
                            logger.info(f"[InternalLoop] V33 Narrative: {narrative[:80]}...")
                            
                            # Generation and workspace admission are separate effects.
                            self._publish_phase2_narrative(
                                narrative,
                                getattr(o, "workspace", None),
                                _narrative_ref,
                            )
                    except Exception as _ns:
                        self._record_cycle_stage(
                            "phase2_narrative_synthesis", "failed",
                            metrics={
                                "error_type": type(_ns).__name__,
                                "error_summary": self._exception_summary(_ns),
                            },
                        )
                        logger.debug(f"[InternalLoop] Narrative synthesis error: {_ns}")

                # ── V33: Phase 2 Thread→Identity Linking ──────────────────────
                # Every 12 slow cycles (~24 minutes), link resolved threads to identity
                _phase2_link_due = self._slow_cycle_count % 12 == 0
                _phase2_link_allowed = (
                    self._phase2 is not None
                    and _phase2_link_due
                    and (not self._governor or self._governor.may_run("Phase2ThreadIdentity"))
                )
                if self._phase2 is None:
                    self._record_cycle_stage("phase2_thread_identity_link", "unavailable")
                elif not _phase2_link_due:
                    self._record_cycle_stage(
                        "phase2_thread_identity_link", "skipped_cadence",
                        metrics={"cycle": self._slow_cycle_count, "interval_cycles": 12},
                    )
                elif not _phase2_link_allowed:
                    self._record_cycle_stage(
                        "phase2_thread_identity_link", "skipped_governor",
                        metrics=self._phase2_governor_skip_metrics("Phase2ThreadIdentity"),
                    )
                else:
                    try:
                        # Find recently resolved threads
                        resolved_threads = []
                        if self._tte:
                            for thread in self._tte.all_threads():
                                if (
                                    self._phase2_thread_is_resolved(thread)
                                    and not self._phase2_thread_identity_linked(thread)
                                ):
                                    
                                    resolved_threads.append(thread)
                                    
                        if resolved_threads:
                            identity_updates = []
                            linked_count = 0
                            for thread in resolved_threads:
                                try:
                                    result = self._link_phase2_thread(thread)
                                except Exception:
                                    continue
                                if result is None:
                                    continue
                                identity_updates.append(result)
                                linked_count += 1

                            total_beliefs = sum(len(u.get('beliefs_changed', [])) for u in identity_updates)
                            total_traits = sum(len(u.get('traits_changed', [])) for u in identity_updates)
                            
                            if total_beliefs or total_traits:
                                logger.info(
                                    f"[InternalLoop] V33 Thread→Identity: "
                                    f"{total_beliefs} beliefs, {total_traits} traits updated "
                                    f"from {len(resolved_threads)} threads"
                                )
                            self._record_cycle_stage(
                                "phase2_thread_identity_link",
                                "completed" if linked_count == len(resolved_threads) else "partial_or_unavailable",
                                output={
                                    "candidate_count": len(resolved_threads),
                                    "linked_count": linked_count,
                                    "failed_count": len(resolved_threads) - linked_count,
                                    "belief_updates": total_beliefs,
                                    "trait_updates": total_traits,
                                },
                            )
                        else:
                            self._record_cycle_stage(
                                "phase2_thread_identity_link", "no_resolved_threads",
                                output={"candidate_count": 0, "linked_count": 0},
                            )
                    except Exception as _til:
                        self._record_cycle_stage(
                            "phase2_thread_identity_link", "failed",
                            metrics={
                                "error_type": type(_til).__name__,
                                "error_summary": self._exception_summary(_til),
                            },
                        )
                        logger.debug(f"[InternalLoop] Thread→Identity linking error: {_til}")


            except Exception as _tte_e:
                self._record_cycle_stage(
                    "thought_thread_cde_dts_chain", "failed",
                    metrics={
                        "error_type": type(_tte_e).__name__,
                        "error_summary": self._exception_summary(_tte_e),
                    },
                )
                logger.debug(f"[InternalLoop] TTE/CDE/DTS tick error (non-fatal): {_tte_e}")
        else:
            self._record_cycle_stage("thought_thread_cde_dts_chain", "unavailable")

        # ── Phase 2.8 / 2.9: Vital cycle labelling ──────────────────────────
        _IS_CONSOLIDATION = (self._slow_cycle_count % 5 == 0 and self._slow_cycle_count > 0)
        _IS_EVOLUTION     = (self._slow_cycle_count % 40 == 0 and self._slow_cycle_count > 0)
        if _IS_CONSOLIDATION:
            logger.info(
                f"[InternalLoop] 🔄 CONSOLIDATION cycle "
                f"#{self._slow_cycle_count // 5} — memory · narration · flux · attention"
            )
        if _IS_EVOLUTION:
            logger.info(
                f"[InternalLoop] 🧬 EVOLUTION cycle "
                f"#{self._slow_cycle_count // 40} — parameter self-modification"
            )

        # ── Phase 2.8 GAP 1: CognitiveFluxEngine ──────────────────────────────
        # Per-module flux intensity from drives/tensions/emotion (unconstrained,
        # EMA-smoothed). Superseded by Phase 2.9's CognitiveAttentionEngine for
        # workspace-competition biasing (which adds the zero-sum softmax
        # constraint this engine lacks) — restored here because Gaps 4/5/6
        # below read flux state to decide when to fire (e.g. creative flux
        # threshold gates CreativeDivergenceEngine.inject_to_threads()).
        try:
            if not hasattr(self, '_flux_engine'):
                self._flux_engine = None
            if self._flux_engine is None and self._slow_cycle_count > 2:
                from cognition.cognitive_flux_engine import CognitiveFluxEngine
                self._flux_engine = CognitiveFluxEngine(o)
                logger.info("[InternalLoop] CognitiveFluxEngine ready ✅")
            if self._flux_engine is not None and _IS_CONSOLIDATION:
                self._flux_engine.compute_and_write()

                # Phase 2.8 GAP 4: when creative_divergence flux crosses 0.35,
                # the cognitive system has organically built up enough
                # "creative pressure" to warrant an unprompted divergent
                # thought — inject one into the workspace without waiting
                # for a user message to respond to.
                try:
                    _creative_flux = self._flux_engine.get_module_flux("creative_divergence")
                    if _creative_flux > 0.35:
                        _cd = getattr(o, "creative_divergence", None)
                        _ws_topic = ""
                        _ws_cd = getattr(o, "workspace", None)
                        if _ws_cd:
                            _top_cd = _ws_cd.top(1)
                            if _top_cd:
                                _ws_topic = str(_top_cd[0].content)[:100]
                        if _cd and _ws_topic:
                            _cd.inject_to_threads(o, _ws_topic)
                except Exception as _cd_e:
                    logger.debug(f"[InternalLoop] Creative injection error (non-fatal): {_cd_e}")
            elif self._flux_engine is not None:
                self._record_cycle_stage(
                    "cognitive_flux_engine", "skipped_cadence",
                    metrics={"cycle": int(self._slow_cycle_count), "interval_cycles": 5},
                )
        except Exception as _fe:
            logger.debug(f"[InternalLoop] FluxEngine error (non-fatal): {_fe}")

        # ── Phase 2.9 GAP 6: CognitiveAttentionEngine ─────────────────────────
        # Softmax attention weights (sum=1.0) over 10 modules.
        # Fires every consolidation cycle (10 min). Writes cognitive_attention.json.
        # Upstream consumers: workspace_competition, goal_engine, curiosity_engine,
        # cognitive_organism prompt budget.
        try:
            if not hasattr(self, '_attention_engine'):
                self._attention_engine = None
            if self._attention_engine is None and self._slow_cycle_count > 2:
                from cognition.cognitive_attention_engine import CognitiveAttentionEngine
                self._attention_engine = CognitiveAttentionEngine(o)
                logger.info("[InternalLoop] CognitiveAttentionEngine ready ✅")
            if self._attention_engine is not None and _IS_CONSOLIDATION:
                _attn_result = self._attention_engine.compute_and_write(
                    self._slow_cycle_count
                )
                _pf = _attn_result.get("primary_focus", "")
                if _pf:
                    _ws_attn = getattr(o, "workspace", None)
                    if _ws_attn:
                        _w = _attn_result.get("attention_weights", {})
                        _top3 = sorted(_w.items(), key=lambda x: -x[1])[:3]
                        _ws_attn.broadcast(
                            source   = "cognitive_attention.focus",
                            content  = (
                                f"Attention: {_pf.replace('_',' ')} "
                                f"({_top3[0][1]:.2f})"
                                + "".join(
                                    f" | {m.replace('_',' ')} ({v:.2f})"
                                    for m, v in _top3[1:]
                                )
                            ),
                            priority = 0.60,
                        )
            elif self._attention_engine is not None:
                self._record_cycle_stage(
                    "cognitive_attention_engine", "skipped_cadence",
                    metrics={"cycle": int(self._slow_cycle_count), "interval_cycles": 5},
                )
        except Exception as _ae:
            logger.debug(f"[InternalLoop] AttentionEngine error (non-fatal): {_ae}")

        # ── Phase 2.9.1: PCM outcome → attention learning signal ──────────────
        # Reads recent PCM records on each consolidation cycle.
        # "positive" outcomes for the dominant module at that time reinforce
        # its learned bias; "negative" outcomes dampen it.
        # Signal is ±0.4 (weaker than explicit feedback ±1.0) since PCM
        # outcomes are implicit rather than deliberate user ratings.
        try:
            if (_IS_CONSOLIDATION
                    and hasattr(self, '_attention_engine')
                    and self._attention_engine is not None):
                _ai_pcm  = getattr(o, "ai_system", None)
                _pcm_eng = None
                if _ai_pcm:
                    # Try both attribute names used across versions
                    for _attr in ('_consequence_model', 'consequence_model',
                                  'predictive_consequence_model'):
                        _pcm_eng = getattr(_ai_pcm, _attr, None)
                        if _pcm_eng is not None:
                            break
                if _pcm_eng and hasattr(_pcm_eng, '_records'):
                    # Read last 10 non-synthetic records since last consolidation
                    _recent_pcm = [
                        r for r in list(_pcm_eng._records)[-10:]
                        if not getattr(r, 'synthetic', False)
                        and getattr(r, 'outcome_source', '') == 'explicit_user_feedback'
                        and not getattr(r, 'attention_feedback_applied', False)
                        and bool(getattr(r, 'attention_weights_at_turn', None))
                    ]
                    for _rec in _recent_pcm:
                        _out    = getattr(_rec, 'outcome', 'neutral')
                        _sig    = 0.4 if _out == 'positive' else -0.4
                        _claim = _pcm_eng.claim_attention_feedback(
                            getattr(_rec, 'response_hash', '')
                        )
                        if not _claim:
                            continue
                        _attn_w = dict(_claim['attention_weights_at_turn'])
                        self._attention_engine.update_from_feedback(
                            _sig, weights_at_feedback=_attn_w
                        )
                        # Contextual credit uses the context captured for the
                        # rated response, never the later consolidation state.
                        self._attention_engine.update_from_context_feedback(
                            _sig,
                            weights_at_feedback=_attn_w,
                            context_key=_claim.get('attention_context_key_at_turn', ''),
                        )
                        _pcm_eng.mark_attention_feedback_applied(
                            _claim['response_hash']
                        )
                    if _recent_pcm:
                        _pcm_eng._save()

                # Decay learned bias each consolidation to prevent lock-in
                self._attention_engine.decay_bias()
                # Phase 3.0: decay contextual memory (slower rate — see method docstring)
                self._attention_engine.decay_context()

        except Exception as _pcm_ae:
            logger.debug(f"[InternalLoop] PCM→attention signal error (non-fatal): {_pcm_ae}")

        # ── Phase 2.8 GAP 6: suppress weak contradictions ───────────────────────
        # Removes low-severity pending contradictions each consolidation cycle
        # so trivial inconsistencies don't crowd out genuinely significant ones
        # or accumulate indefinitely.
        try:
            if _IS_CONSOLIDATION:
                _ai_cdh = getattr(o, "ai_system", None)
                _cdh = getattr(_ai_cdh, "liberty_contradiction", None) if _ai_cdh else None
                if _cdh and hasattr(_cdh, "suppress_weak_contradictions"):
                    _cdh.suppress_weak_contradictions()
        except Exception as _cdh_e:
            logger.debug(f"[InternalLoop] ContradictionHandler suppress error (non-fatal): {_cdh_e}")

        # ── Phase 3.1: CalibrationEngine ECE refresh ───────────────────────────
        # Recomputes Expected Calibration Error per module from accumulated
        # resolved predictions. Cheap (pure arithmetic over existing bins,
        # no new LLM calls) — runs every consolidation cycle. Separate try
        # block (not nested inside the PCM→attention block above) so a
        # calibration error never masks or gets masked by attention errors.
        try:
            _ai_pcm2  = getattr(o, "ai_system", None)
            _pcm_eng2 = None
            if _ai_pcm2:
                for _attr2 in ('_consequence_model', 'consequence_model',
                               'predictive_consequence_model'):
                    _pcm_eng2 = getattr(_ai_pcm2, _attr2, None)
                    if _pcm_eng2 is not None:
                        break
            _cal_eng2 = getattr(_pcm_eng2, '_calibration_engine', None) if _pcm_eng2 else None
            if _IS_CONSOLIDATION and _cal_eng2:
                _ece = _cal_eng2.compute_ece("pcm")
                if _ece is not None:
                    logger.info(f"[InternalLoop] PCM calibration ECE = {_ece:.3f}")
        except Exception as _cal_ece_e:
            logger.debug(f"[InternalLoop] Calibration ECE refresh error (non-fatal): {_cal_ece_e}")

        # Refresh the evidential self-model after the subsystems above have
        # produced their latest outcomes. This is local aggregation only: no
        # LLM call and no dependency on an active user conversation.
        try:
            if _IS_CONSOLIDATION:
                _identity = getattr(o, "identity_grounding", None)
                if _identity is not None:
                    _identity.ground()
        except Exception as _identity_e:
            logger.debug(f"[InternalLoop] Evidential self-model refresh error (non-fatal): {_identity_e}")

        # ── Governor summary (end of slow cycle) ─────────────────────────────
        if self._governor:
            self._governor.summary_log()

        # ── V34: Phase 4 maintenance ──────────────────────────────────────────
        self._phase4_maintenance()

    @staticmethod
    def _governor_goal_status_counts(goal_engine: Any) -> dict[str, int]:
        """Summarize the live registry states consumed by governor policy.

        Completed, archived, abandoned, and low-quality records remain in the
        persistence pool for history, but must not keep the governor in
        structured mode. The governor's thresholds are defined over active
        plus dormant goals.
        """
        goals = getattr(goal_engine, "_goals", {}) if goal_engine is not None else {}
        values = goals.values() if hasattr(goals, "values") else goals
        tracked_statuses = {
            "active", "dormant", "completed", "archived", "abandoned", "low_quality",
        }
        counts = {status: 0 for status in tracked_statuses}
        counts.update({"other": 0, "total": 0})
        for goal in values:
            counts["total"] += 1
            status = getattr(goal, "status", None)
            if status in tracked_statuses:
                counts[status] += 1
            else:
                counts["other"] += 1
        return counts

    @staticmethod
    def _governor_goal_count(goal_engine: Any) -> int:
        """Count the active+dormant subset consumed by governor policy."""
        counts = InternalThoughtLoop._governor_goal_status_counts(goal_engine)
        return counts["active"] + counts["dormant"]

    def _periodic_module_due(
        self, attr_name: str, module_name: str, interval: int,
        governor_name: str,
    ) -> bool:
        """Record why an initialized maintenance module did not run this cycle."""
        if getattr(self, attr_name, None) is None:
            return False
        cycle = int(getattr(self, "_slow_cycle_count", 0) or 0)
        metrics = {"cycle": cycle, "interval_cycles": int(interval)}
        if interval > 0 and cycle % interval != 0:
            self._record_cycle_stage(module_name, "skipped_cadence", metrics=metrics)
            return False
        governor = getattr(self, "_governor", None)
        if governor is not None and not governor.may_run(governor_name):
            self._record_cycle_stage(module_name, "skipped_governor", metrics=metrics)
            return False
        return True

    def _phase4_maintenance(self) -> None:
        """V34: Phase 4 goal quality, belief, and thread lifecycle maintenance."""
        if self._periodic_module_due(
            "_goal_quality_filter", "goal_quality_filter", 20, "GQF",
        ):
            _mf = getattr(self, "_motivational_field", None)
            _scan_status = (
                _mf.need_scan_status() if _mf and hasattr(_mf, "need_scan_status") else {}
            )
            if _scan_status.get("status") == "running":
                self._record_cycle_stage(
                    "goal_quality_filter", "skipped_motivational_scan_running",
                    inputs={"motivational_scan_cycle": _scan_status.get("cycle")},
                )
            else:
                try:
                    _ge = getattr(
                        getattr(self._organism, 'ai_system', None),
                        'goal_engine', None,
                    )
                    report = self._goal_quality_filter.run(goal_engine=_ge)
                    s = report.get('summary', {})
                    if self._governor:
                        self._governor.record('GQF', s.get('noise_marked', 0) + s.get('generated', 0) + s.get('boosted', 0))
                    if s.get('noise_marked', 0) + s.get('generated', 0) > 0:
                        logger.info(
                            f"[InternalLoop] V34 Goal quality: "
                            f"{s.get('noise_marked',0)} noise removed, "
                            f"{s.get('generated',0)} new goals generated"
                        )
                    # GQF persists through DataAccess; synchronize its
                    # accepted changes before later actions/GEI consume them.
                    if _ge is not None and hasattr(_ge, 'reload_from_disk'):
                        _ge.reload_from_disk()
                except Exception as _e4:
                    self._record_cycle_stage(
                        "goal_quality_filter", "failed",
                        metrics={
                            "error_type": type(_e4).__name__,
                            "error_summary": self._exception_summary(_e4),
                        },
                    )
                    logger.debug(f"[InternalLoop] Phase 4 goal quality failed: {_e4}")

        if self._contradiction_reviser:
            # Confronts pending contradictions, revises the underlying
            # belief (so identity actually updates), and marks the entry
            # confronted — closes the loop that was feeding the same
            # contradiction/goal back forever. tick() self-gates to every
            # 15 slow cycles.
            try:
                self._contradiction_reviser.tick(self._slow_cycle_count)
            except Exception as _e_cbr:
                logger.debug(f"[InternalLoop] Contradiction reviser failed: {_e_cbr}")

        if (self._belief_bootstrapper and self._slow_cycle_count % 30 == 0
                and (not self._governor or self._governor.may_run('BeliefBootstrapper'))):
            try:
                report = self._belief_bootstrapper.run()
                added = report.get('total_added', 0)
                total = report.get('total_beliefs_now', 0)
                if added > 0:
                    logger.info(f"[InternalLoop] V34 Beliefs: +{added} added ({total} total)")
            except Exception as _e4:
                logger.debug(f"[InternalLoop] Phase 4 belief bootstrap failed: {_e4}")

        if self._periodic_module_due(
            "_thread_lifecycle_mgr", "thread_lifecycle_manager", 15,
            "ThreadLifecycle",
        ):
            try:
                active_goal_ids = set()
                try:
                    _goal_engine = getattr(
                        getattr(o, "ai_system", None), "goal_engine", None
                    )
                    _active_goals = (
                        _goal_engine.get_active_goals() or []
                        if _goal_engine and hasattr(_goal_engine, "get_active_goals")
                        else []
                    )
                    active_goal_ids = {
                        str(getattr(_goal, "id", "") or "").strip()
                        for _goal in _active_goals
                        if str(getattr(_goal, "id", "") or "").strip()
                    }
                except Exception as _goal_snapshot_error:
                    logger.debug(
                        "[InternalLoop] Active goal snapshot unavailable for thread lifecycle: %s",
                        type(_goal_snapshot_error).__name__,
                    )
                report = self._thread_lifecycle_mgr.run(
                    active_goal_ids=active_goal_ids
                )
                if report.get('threads_processed', 0) > 0:
                    logger.info(
                        f"[InternalLoop] V34 Thread lifecycle: "
                        f"{report['threads_processed']} retired, "
                        f"{len(report['beliefs_extracted'])} beliefs extracted"
                    )
            except Exception as _e4:
                logger.debug(f"[InternalLoop] Phase 4 thread lifecycle failed: {_e4}")

        # ── V37: Phase 7 Semantic graph cleaning ─────────────────────────────
        if self._periodic_module_due(
            "_semantic_graph_cleaner", "semantic_graph_cleaner", 50,
            "SemanticGraphCleaner",
        ):
            try:
                report = self._semantic_graph_cleaner.run()
                total = report.get('purged_concepts',0) + report.get('merged_concepts',0)
                if total > 0:
                    logger.info(
                        f"[InternalLoop] V37 Semantic graph: "
                        f"{report['purged_concepts']} purged, "
                        f"{report['merged_concepts']} merged, "
                        f"{report['enriched_relations']} relations enriched, "
                        f"{report['beliefs_promoted']} beliefs promoted"
                    )
            except Exception as _e7:
                logger.debug(f"[InternalLoop] Phase 7 semantic clean failed: {_e7}")

        # ── V36: Phase 6 Goal consolidation ──────────────────────────────────
        if self._periodic_module_due(
            "_goal_consolidator", "goal_consolidator", 18,
            "GoalConsolidator",
        ):
            try:
                report = self._goal_consolidator.run()
                s = report.get('summary', {})
                _goal_engine = getattr(
                    getattr(self._organism, "ai_system", None), "goal_engine", None
                )
                if (_goal_engine is not None and hasattr(_goal_engine, "reload_from_disk") and sum(
                    int(s.get(key, 0) or 0) for key in ("merged", "renamed", "archived")
                )):
                    _goal_engine.reload_from_disk()
                if s.get('merged', 0) + s.get('renamed', 0) + s.get('archived', 0) > 0:
                    logger.info(
                        f"[InternalLoop] V36 Goal consolidation: "
                        f"{s.get('archived',0)} archived, "
                        f"{s.get('renamed',0)} renamed, "
                        f"{s.get('merged',0)} merged"
                    )
            except Exception as _e6:
                logger.debug(f"[InternalLoop] Phase 6 goal consolidator failed: {_e6}")

        # ── V35: Phase 5 Self-concept sync ────────────────────────────────────
        if self._self_concept_sync:
            _scs_cycle = int(self._slow_cycle_count)
            _scs_due = _scs_cycle == 1 or (_scs_cycle > 0 and _scs_cycle % 5 == 0)
            if not _scs_due:
                self._record_cycle_stage(
                    "self_concept_synchronizer", "skipped_cadence",
                    metrics={"cycle": _scs_cycle, "interval_cycles": 5,
                             "initial_cycle": 1},
                )
            elif self._governor and not self._governor.may_run('SCS'):
                self._record_cycle_stage(
                    "self_concept_synchronizer", "skipped_governor",
                    metrics={"cycle": _scs_cycle, "interval_cycles": 5},
                )
            else:
                try:
                    report = self._self_concept_sync.run()
                    if self._governor:
                        self._governor.record('SCS', report.get('beliefs_synced', 0))
                    logger.info(
                        f"[InternalLoop] V35 Self-concept: "
                        f"coherence={report.get('coherence_after')} "
                        f"({report.get('coherence_status', 'unknown')}) "
                        f"(+{report['beliefs_synced']} beliefs, "
                        f"{report['milestones_found']} milestones)"
                    )
                except Exception as _e5:
                    self._record_cycle_stage(
                        "self_concept_synchronizer", "failed",
                        metrics={
                            "error_type": type(_e5).__name__,
                            "error_summary": self._exception_summary(_e5),
                        },
                    )
                    logger.debug(f"[InternalLoop] Phase 5 self-concept sync failed: {_e5}")

        # ── Phase 5.1: Persistent Executive Loop ────────────────────────────
        # Every 10 slow cycles (~20 min) — more frequent than GQF (20 cycles)
        # since this reacts to pressure/trait state, not slow semantic drift.
        if self._periodic_module_due(
            "_persistent_exec_loop", "persistent_executive_loop", 10, "PEL",
        ):
            try:
                report = self._persistent_exec_loop.review(self._organism)
                if self._governor:
                    self._governor.record('PEL', len(report.get('reduced', [])))
                if report.get('reduced'):
                    logger.info(
                        f"[InternalLoop] Phase 5.1 executive review: "
                        f"{len(report['reduced'])} goal(s) reduced "
                        f"(reason receded), {len(report.get('held', []))} held, "
                        f"{report.get('not_traceable', 0)} not traceable"
                    )
            except Exception as _e51:
                logger.debug(f"[InternalLoop] Phase 5.1 executive loop failed: {_e51}")

        # ── Phase 5.4: Arbitration Learning review ──────────────────────────
        # Every 8 slow cycles (~16 min) — cheap dict scan, no reason to wait
        # as long as GQF's 20-cycle semantic-drift cadence.
        if self._periodic_module_due(
            "_arbitration_learning", "arbitration_learning", 8, "ARB_LEARN",
        ):
            try:
                _ge = getattr(getattr(self._organism, 'ai_system', None), 'goal_engine', None)
                report = self._arbitration_learning.review(_ge, self._slow_cycle_count)
                if self._governor:
                    self._governor.record('ARB_LEARN', report.get('reviewed', 0))
                if report.get('good') or report.get('bad'):
                    logger.info(
                        f"[InternalLoop] Phase 5.4 arbitration learning: "
                        f"{report['good']} good, {report['bad']} bad, "
                        f"{report['still_pending']} still pending "
                        f"(delta={self._arbitration_learning.status()['delta']})"
                    )
            except Exception as _e54:
                logger.debug(f"[InternalLoop] Phase 5.4 arbitration learning failed: {_e54}")

        # ── v78b: calibrated threat response ────────────────────────────────
        # Objective threat signal (resource depletion, unresolved coherence
        # violations, sustained prediction failure — never anxiety itself,
        # deliberately, to avoid a closed feedback loop) nudges anxiety
        # through the same bounded, regulation-tied path as everything else.
        # See cognition/threat_response.py for the full design rationale.
        try:
            from cognition.threat_response import apply_threat_response
            _threat = apply_threat_response(o)
            if _threat is not None and _threat >= 0.15:
                logger.debug(f"[InternalLoop] threat_level={_threat:.2f} this cycle")
        except Exception as _te:
            logger.debug(f"[InternalLoop] threat_response error (non-fatal): {_te}")


    def _reflection_cycle(self) -> None:
        """
        A lightweight self-reflection that doesn't require the LLM.
        Updates identity and surfaces meta-cognitive observations.

        FIXED: Reflection now WRITES a summary to persistent memory.
        Previously it only logged and sated pressure reservoirs — producing
        rumination (analysis with no durable change). Now each cycle emits
        a reflection record so that idle cognition actually creates learning.
        """
        o = self._organism
        reflection_fragments: list[str] = []

        # Only emit coherence reflections when a validated measurement exists.
        if hasattr(o, "ai_system") and hasattr(o.ai_system, "self_concept"):
            try:
                sc = o.ai_system.self_concept
                if hasattr(sc, "state"):
                    state = sc.state
                    coherence = getattr(state, "coherence", None)
                    if (getattr(state, "coherence_status", None) == "measured"
                            and isinstance(coherence, (int, float))):
                        coherence = round(coherence, 2)
                    else:
                        coherence = None
                    if coherence is not None and coherence < 0.5:
                        reflection_fragments.append(
                            f"Identity coherence is low ({coherence}) — internal tension noted."
                        )
                        ws = getattr(o, 'workspace', None)
                        if ws:
                            try:
                                ws.broadcast(
                                    source="reflection.identity",
                                    content="Identity coherence low — internal tension noted",
                                    priority=0.4,
                                )
                            except Exception:
                                pass
                    elif coherence is not None:
                        reflection_fragments.append(
                            f"Identity coherence stable ({coherence})."
                        )
            except Exception:
                pass

        # Surface meta-cognitive observations
        if hasattr(o, "meta_cognition"):
            try:
                recent = o.meta_cognition.recent_reflection_observations(n=3)
                for obs in recent:
                    logger.debug(f"[InternalLoop] Meta-obs: {obs}")
                    if isinstance(obs, str) and obs.strip():
                        reflection_fragments.append(obs.strip())
            except Exception:
                pass

        # Capture dominant emotional deviation into reflection
        if hasattr(o, "ai_system") and hasattr(o.ai_system, "emotional_state"):
            try:
                es = o.ai_system.emotional_state
                if hasattr(es, "emotions") and es.emotions:
                    dominant = max(
                        es.emotions.items(),
                        key=lambda kv: abs(kv[1].value - kv[1].baseline),
                        default=None,
                    )
                    if dominant:
                        name, em = dominant
                        delta = round(em.value - em.baseline, 2)
                        if abs(delta) > 0.15:
                            direction = "elevated" if delta > 0 else "suppressed"
                            reflection_fragments.append(
                                f"{name} is {direction} "
                                f"({em.value:.2f} vs baseline {em.baseline:.2f})."
                            )
            except Exception:
                pass

        # ── Write reflection to persistent memory (the key fix) ───────────────
        # This closes the loop: reflection → memory write → future retrieval.
        # Without this step cycles produce rumination, not growth.
        if reflection_fragments:
            try:
                ms = getattr(getattr(o, 'ai_system', None), 'memory_system', None)
                if ms:
                    summary = "Idle reflection: " + " ".join(reflection_fragments)
                    ms.add_memory(
                        summary[:400],
                        impact_score=0.35,
                        memory_type="reflection",
                        valence="Neutral",
                        arousal="Low",
                    )
                    logger.debug(
                        f"[InternalLoop] Reflection written to memory: {summary[:80]!r}"
                    )
            except Exception as _me:
                logger.debug(f"[InternalLoop] Reflection memory write failed (non-fatal): {_me}")

        logger.debug("[InternalLoop] Reflection cycle complete")
        # Reflection satiates identity and epistemic pressure
        try:
            if hasattr(o, 'pressure'):
                o.pressure.satiate("identity",  0.15)
                o.pressure.satiate("epistemic", 0.10)
                o.pressure.satiate("coherence", 0.12)
        except Exception:
            pass

    # ── Thought queue ─────────────────────────────────────────────────────────

    def _queue_thought(self, thought: str) -> None:
        with self._lock:
            if thought not in self._pending_thoughts:
                self._pending_thoughts.append(thought)
                if len(self._pending_thoughts) > 10:
                    self._pending_thoughts = self._pending_thoughts[-10:]

    def pop_pending_thoughts(self) -> list[str]:
        """
        Called by the main pipeline at the start of each interaction.
        Returns any thoughts queued during background cycles.
        """
        with self._lock:
            thoughts = list(self._pending_thoughts)
            self._pending_thoughts.clear()
            return thoughts

    # ── Ambient vision perception ─────────────────────────────────────────────

    def _ambient_vision_tick(self, o) -> None:
        """
        Non-blocking ambient visual perception.

        Runs inside the slow cycle thread. Uses asyncio.run_coroutine_threadsafe
        so it safely calls the async analyze_frame_async without blocking the loop.
        Result is broadcast to GlobalWorkspace at low priority — it enriches
        PandoraBOX's context but never interrupts or competes with user interactions.
        """
        try:
            from managers.settings_manager import config as _avcfg
            interval = int(getattr(_avcfg, 'AMBIENT_VISION_INTERVAL', 90))
        except Exception:
            interval = 90

        if interval <= 0:
            return  # feature disabled

        vm = self._vision_ref
        if vm is None or not getattr(vm, 'camera_active', False):
            return  # no camera active

        # Guard: respect interval (reduced default: 45s instead of 90s)
        if interval > 45:
            interval = 45
        now = time.time()
        if now - self._last_ambient_vision < interval:
            return
        # Note: removed 30s idle guard — VIS should spike during conversation too

        AMBIENT_PROMPT = (
            "In one sentence (max 30 words), describe the most notable thing visible. "
            "Be specific, not generic."
        )

        def _run_analysis():
            try:
                import asyncio as _asyncio
                try:
                    loop = _asyncio.get_event_loop()
                except RuntimeError:
                    return
                if not loop.is_running():
                    return

                future = _asyncio.run_coroutine_threadsafe(
                    vm.analyze_frame_async(prompt=AMBIENT_PROMPT, max_tokens=120),
                    loop
                )
                result = future.result(timeout=25.0)
                description, faces = result

                if not description or description.startswith("No frame") or description.startswith("Error"):
                    return

                short_desc = description[:220].strip()
                if len(description) > 220:
                    short_desc += "…"

                if hasattr(o, 'workspace'):
                    import datetime as _dt
                    _ts = _dt.datetime.now().strftime("%H:%M")
                    o.workspace.broadcast(
                        source="ambient_vision",
                        content=f"[Vision@{_ts}] {short_desc}",
                        priority=0.28,
                    )
                    logger.debug(f"[InternalLoop] Ambient vision: {short_desc[:60]!r}")

                # Known faces = socially relevant → higher priority broadcast
                if faces:
                    known = [f for f in faces if f.get('name', 'Unknown') != 'Unknown']
                    if known and hasattr(o, 'workspace'):
                        names = ', '.join(f["name"] for f in known[:3])
                        o.workspace.broadcast(
                            source="ambient_vision.faces",
                            content=f"[Vision] {names} {'is' if len(known)==1 else 'are'} present.",
                            priority=0.55,
                        )

            except Exception as _ae:
                logger.debug(f"[InternalLoop] Ambient vision error (non-fatal): {_ae}")

        import threading as _t
        _t.Thread(target=_run_analysis, daemon=True, name="AmbientVision").start()
        self._last_ambient_vision = now

