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

    @staticmethod
    def _goal_action_receipt(report: Any, executor: Any) -> dict[str, Any] | None:
        """Use the action report, or its explicit no-action reason, in cycle evidence."""
        if isinstance(report, dict):
            return report
        outcome = getattr(executor, "_last_tick_outcome", None)
        return outcome if isinstance(outcome, dict) else None

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
            from cognition.arbitration_learning       import ArbitrationLearningTracker
            self._self_concept_sync   = SelfConceptSynchronizer()
            self._persistent_exec_loop = PersistentExecutiveLoop()
            self._arbitration_learning = ArbitrationLearningTracker()
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
                try:
                    return_annotation = inspect.signature(bound_method).return_annotation
                    side_effect_only = (
                        return_annotation is None
                        or return_annotation is type(None)
                        or str(return_annotation) in {"None", "NoneType"}
                    )
                except (TypeError, ValueError):
                    side_effect_only = False

                @wraps(bound_method)
                def observed(*args, __bound=bound_method, __module=module_name,
                             __module_instance=module,
                             __method=method_name, __side_effect_only=side_effect_only,
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
                                metrics={"duration_ms": round(duration_ms, 2), "error_type": type(exc).__name__},
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
                        side_effect_only=(
                            __side_effect_only and observed_output is None
                        ),
                    )
                    try:
                        self._record_cycle_stage(
                            f"module_tick:{__module}.{__method}", "completed",
                            inputs=self._cycle_input_evidence(args, kwargs),
                            output=observed_output,
                            metrics={"duration_ms": round(duration_ms, 2)},
                            side_effect_only=(
                                __side_effect_only and observed_output is None
                            ),
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
                    "output_unverified" if quality in {"empty", "shape_only", "unknown"} else
                    "healthy"
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
                "type", "status", "success", "created", "verified",
                "outcome_status", "reason_code", "skipped",
                "source_thought_source", "source_thought_type", "source_concept_method",
                "drive_update", "need_scan",
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
            return summary
        if isinstance(value, (list, tuple, set)):
            return {"kind": type(value).__name__, "item_count": len(value)}
        if value is None:
            return {"kind": "none"}
        return {"kind": type(value).__name__}

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

    def _record_cycle_stage(
        self, stage: str, status: str, *, inputs: dict[str, Any] | None = None,
        output: Any = None, metrics: dict[str, Any] | None = None,
        side_effect_only: bool = False,
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
                    {"kind": "none", "quality": "side_effect_only" if side_effect_only else "empty"}
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
        metrics: dict[str, Any] | None = None, error_type: str | None = None,
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
                "output_ref": None,
                "output_summary": None,
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

    def _finish_cycle_evidence(self, status: str, error_type: str | None = None) -> None:
        lock = getattr(self, "_cycle_evidence_lock", None)
        if lock is None:
            return
        with lock:
            receipt = getattr(self, "_active_cycle_evidence", None)
            if receipt is None:
                return
            receipt["status"] = status
            receipt["finished_at"] = time.time()
            receipt["duration_ms"] = round((receipt["finished_at"] - receipt["started_at"]) * 1000, 2)
            if error_type:
                receipt["error_type"] = str(error_type)
            self._cycle_evidence.append(receipt)
            self._active_cycle_evidence = None
            self._active_cycle_thread_id = None

    def cycle_evidence_snapshot(self, limit: int = 5) -> dict[str, Any]:
        """Expose recent bounded causal receipts; semantic correctness is not inferred."""
        lock = getattr(self, "_cycle_evidence_lock", None)
        if lock is None:
            return {"retained": 0, "cycles": []}
        with lock:
            bounded_limit = max(0, min(int(limit), 10))
            cycles = list(self._cycle_evidence)[-bounded_limit:] if bounded_limit else []
            if self._active_cycle_evidence is not None:
                cycles.append(dict(self._active_cycle_evidence))
            return {
                "retained": len(self._cycle_evidence),
                "capacity": 40,
                "evidence_scope": "internal_cycle_execution_and_explicit_dataflow; semantic_quality_not_assessed",
                "cycles": json.loads(json.dumps(cycles, default=str)),
            }

    @staticmethod
    def _resolve_cycle_state_path() -> Path:
        """Per-process cycle-state file, keyed by PERSONA_NAME so master
        and Flux (which share data/persona for actual persona memory)
        stop racing on one counter file. See __init__ comment above."""
        try:
            from managers.settings_manager import get_persona_name
            suffix = (get_persona_name() or "lumina").strip().lower().replace(" ", "_")
        except Exception:
            suffix = "lumina"
        return Path(f"data/persona/internal_loop_state_{suffix or 'lumina'}.json")

    # ── Cycle-count persistence (bug fix v59) ───────────────────────────────────
    def _load_cycle_state(self) -> None:
        try:
            if self._cycle_state_path.exists():
                d = json.loads(self._cycle_state_path.read_text())
                restored = int(d.get("slow_cycle_count", 0))
                if restored > 0:
                    self._slow_cycle_count = restored
                    logger.info(
                        f"[InternalLoop] Restored slow_cycle_count={restored} "
                        f"from previous session (was resetting to 0 on every "
                        f"restart before this fix)"
                    )
                    return

            # One-time migration: this instance's own per-process file
            # doesn't exist yet (first run after the v116 fix above). Adopt
            # whatever the OLD shared file has, so switching to a per-
            # instance path doesn't itself look like a reset to whichever
            # process previously held the higher count.
            _legacy_path = Path("data/persona/internal_loop_state.json")
            if _legacy_path != self._cycle_state_path and _legacy_path.exists():
                d = json.loads(_legacy_path.read_text())
                restored = int(d.get("slow_cycle_count", 0))
                if restored > 0:
                    self._slow_cycle_count = restored
                    logger.info(
                        f"[InternalLoop] Migrated slow_cycle_count={restored} "
                        f"from legacy shared state file to per-instance "
                        f"{self._cycle_state_path.name}"
                    )
        except Exception as e:
            logger.warning(f"[InternalLoop] cycle-state load failed (starting at 0): {e}")

    def _save_cycle_state(self) -> None:
        try:
            self._cycle_state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._cycle_state_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({
                "slow_cycle_count": self._slow_cycle_count,
                "last_saved": time.time(),
            }))
            tmp.replace(self._cycle_state_path)
        except Exception as e:
            logger.debug(f"[InternalLoop] cycle-state save failed: {e}")

    def ensure_predictive_models(self):
        """Return shared predictive models, initializing them on demand.

        Streaming chat can begin before the background loop reaches its lazy
        initialization thresholds. Using this helper from both paths keeps
        the first interaction from silently skipping predictive cognition and
        prevents duplicate instances racing between the chat and loop threads.
        """
        with self._predictive_models_lock:
            organism = self._organism
            if getattr(self, "_consequence_model", None) is None:
                try:
                    from cognition.predictive_consequence_model import PredictiveConsequenceModel
                    self._consequence_model = PredictiveConsequenceModel(organism)
                    logger.info("[InternalLoop] PredictiveConsequenceModel ready ✅")
                except Exception as exc:
                    logger.warning("[InternalLoop] PredictiveConsequenceModel init failed: %s", exc)
                    self._consequence_model = None

            if getattr(self, "_world_self_dynamics", None) is None:
                ai_system = getattr(organism, "ai_system", None)
                if ai_system is not None:
                    try:
                        from cognition.world_self_dynamics_model import WorldSelfDynamicsModel
                        self._world_self_dynamics = WorldSelfDynamicsModel(organism, ai_system)
                        logger.info("[InternalLoop] WorldSelfDynamicsModel ready ✅")
                    except Exception as exc:
                        logger.warning("[InternalLoop] WorldSelfDynamicsModel init failed: %s", exc)
                        self._world_self_dynamics = None
            return (
                getattr(self, "_consequence_model", None),
                getattr(self, "_world_self_dynamics", None),
            )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop,
            name="LuminaInternalLoop",
            daemon=True,
        )
        self._thread.start()
        logger.info("[InternalLoop] Background thought loop started")

    def shutdown(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        planner = getattr(self, '_long_horizon_planner', None)
        if planner is not None and hasattr(planner, 'persist_now'):
            try:
                planner.persist_now()
            except Exception as exc:
                logger.debug("[InternalLoop] planner shutdown save failed: %s", exc)
        logger.info("[InternalLoop] Background thought loop stopped")

    def attach_vision(self, vision_manager) -> None:
        """Wire the StreamingVisionManager so the loop can do ambient perception."""
        self._vision_ref = vision_manager
        # Also attach to organism for brain bridge access
        try:
            o = getattr(self, '_o', None) or getattr(self, 'organism', None)
            if o is not None:
                o._vision_manager = vision_manager
        except Exception:
            pass
        logger.info("[InternalLoop] Vision manager attached for ambient perception")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        last_slow       = time.time()
        tension_active  = False   # hysteresis state — persists across fast cycles

        while self._running:
            fast_cycle_completed = False
            try:
                self._fast_cycle()
                self._last_fast_cycle_at = time.time()
                fast_cycle_completed = True

                now          = time.time()
                elapsed_slow = now - last_slow
                timer_due    = elapsed_slow >= SLOW_CYCLE_SECONDS

                # Tension-driven firing with hysteresis:
                # Activates when pressure crosses TENSION_ACTIVATE (0.80).
                # Only deactivates when pressure drops below TENSION_DEACTIVATE (0.60).
                # This prevents rapid on/off cycling when tension oscillates around
                # a single threshold (e.g. 0.79 → 0.81 → 0.78 → 0.82).
                tension_due = False
                if elapsed_slow >= MIN_SLOW_INTERVAL and not timer_due:
                    try:
                        _pressure = getattr(self._organism, '_v32_decision_pressure', {})
                        _tension  = _pressure.get('total', 0.0)

                        if not tension_active and _tension >= TENSION_ACTIVATE:
                            tension_active = True
                            logger.debug(
                                f"[InternalLoop] Tension threshold crossed — "
                                f"early firing activated (pressure={_tension:.2f})"
                            )
                        elif tension_active and _tension < TENSION_DEACTIVATE:
                            tension_active = False
                            logger.debug(
                                f"[InternalLoop] Tension subsided — "
                                f"early firing deactivated (pressure={_tension:.2f})"
                            )

                        tension_due = tension_active
                    except Exception:
                        pass

                if timer_due or tension_due:
                    self._slow_cycle()
                    last_slow = now

            except Exception as e:
                if not fast_cycle_completed:
                    self._fast_cycle_error_count += 1
                logger.error(f"[InternalLoop] Cycle error: {e}", exc_info=True)

            time.sleep(FAST_CYCLE_SECONDS)

    # ── Fast cycle (every 30s) ────────────────────────────────────────────────

    def _fast_cycle(self) -> None:
        """Lightweight maintenance: energy regeneration and emotion decay."""
        o = self._organism

        # Regenerate energy
        if hasattr(o, "energy"):
            o.energy.regenerate()

        # Decay emotional state toward baselines
        if hasattr(o, "ai_system") and hasattr(o.ai_system, "emotional_state"):
            try:
                o.ai_system.emotional_state.apply_time_decay()
            except Exception:
                pass   # don't crash the loop over a decay error

        # Decay curiosity
        if hasattr(o, "curiosity"):
            o.curiosity.decay_all()

        # Tick v2 modules
        if hasattr(o, 'self_model'):
            try:
                o.self_model.tick_load_decay(elapsed_secs=30.0)
            except Exception:
                pass
        if hasattr(o, 'attractors'):
            try:
                o.attractors.tick_return_force()
            except Exception:
                pass

        # ── v3: ThoughtStream tick → feed GlobalWorkspace ─────────────────
        if hasattr(o, 'thought_stream') and hasattr(o, 'workspace'):
            try:
                thought = o.thought_stream.tick()
                if thought:
                    o.workspace.broadcast(
                        source=f"thought.{thought.source}",
                        content=thought.content,
                        priority=thought.priority * 0.6,
                    )
                    # ── Curiosity→Goal converter (closes cognitive loop) ──
                    # A high-priority curiosity thought boosts the "understand" drive,
                    # converting contemplation into motivated exploration.
                    # Max 3 conversions per cycle (curiosity runaway guard).
                    _conversions = getattr(o, '_curiosity_goal_conversions', 0)
                    _energy_ok = hasattr(o, 'energy') and o.energy.level() >= 15.0
                    if (
                        thought.thought_type == "curiosity"
                        and thought.priority >= 0.55
                        and _conversions < 3
                        and hasattr(o, 'goal_ecology')
                        and _energy_ok
                    ):
                        try:
                            o.goal_ecology.record_satisfaction("understand", -0.15)  # increase urgency
                            o._curiosity_goal_conversions = _conversions + 1
                            logger.debug(
                                f"[InternalLoop] curiosity→goal: boosted 'understand' "
                                f"from thought p={thought.priority:.2f}"
                            )
                        except Exception:
                            pass
            except Exception as _te:
                pass

        # Reset per-cycle conversion counter each fast cycle
        if hasattr(o, '_curiosity_goal_conversions'):
            o._curiosity_goal_conversions = 0

        # ── v3: PredictiveMind uncertainty signal ─────────────────────────
        if hasattr(o, 'predictive_mind') and hasattr(o, 'workspace'):
            try:
                sig = o.predictive_mind.uncertainty_signal()
                if sig:
                    o.workspace.broadcast(
                        source=sig['source'],
                        content=sig['content'],
                        priority=sig['priority'],
                    )
            except Exception:
                pass

    # ── Slow cycle (every 2 minutes) ─────────────────────────────────────────

    def _slow_cycle(self) -> None:
        """Deeper inspection, reflection, and intention formation."""
        # Guard against concurrent calls from the background thread + ExecutionLayer.
        # acquire(blocking=False) returns False instantly if another thread holds it.
        _acquired = self._lock.acquire(blocking=False)
        if not _acquired:
            logger.debug("[InternalLoop] _slow_cycle skipped — already running")
            return
        try:
            self._slow_cycle_impl()
            if getattr(self, "_module_tick_log", None) is not None:
                # Some modules are created lazily during a cycle. Refresh after
                # it too, so the status snapshot reflects their current state
                # and the probes attach before their next invocation.
                self._refresh_module_tick_probes()
            self._last_slow_cycle_at = time.time()
            self._finish_cycle_evidence("completed")
        except Exception as exc:
            self._slow_cycle_error_count += 1
            self._last_slow_cycle_error_type = type(exc).__name__
            self._finish_cycle_evidence("failed", type(exc).__name__)
            raise
        finally:
            self._lock.release()

    def _slow_cycle_impl(self) -> None:
        """Inner body of the slow cycle (called under lock)."""
        self._refresh_module_tick_probes()
        self._slow_cycle_count += 1
        self._begin_cycle_evidence(self._slow_cycle_count)
        self._save_cycle_state()
        o = self._organism

        # ── v50: Resource economy tick ────────────────────────────────────────
        # Applies time-based recovery to cognitive_energy, social_energy,
        # attention.  Must run first so gate reads current values this cycle.
        try:
            _resource_economy = self._ensure_resource_economy()
            if _resource_economy is not None:
                _resource_economy.tick()
        except Exception as _re:
            logger.debug(f"[InternalLoop] ResourceEconomy error (non-fatal): {_re}")

        # ── v50: CognitiveBehaviorGate — lazy init on organism ────────────────
        try:
            if not hasattr(o, 'behavior_gate') or o.behavior_gate is None:
                from cognition.cognitive_behavior_gate import CognitiveBehaviorGate
                o.behavior_gate = CognitiveBehaviorGate(o)
                logger.info("[InternalLoop] CognitiveBehaviorGate ready ✅")
        except Exception as _bg:
            logger.debug(f"[InternalLoop] BehaviorGate init error (non-fatal): {_bg}")

        # ── v51: MotivationalField — unified drive + self-generated goals ─────
        # Integrates all pressure sources into a coherent drive vector every
        # 5 slow cycles.  Scans for self-originated needs every 20 slow cycles.
        try:
            if not hasattr(self, '_motivational_field'):
                self._motivational_field = None
            if self._motivational_field is None and self._slow_cycle_count > 2:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.motivational_field import MotivationalField
                    self._motivational_field = MotivationalField(o, _ai_sys)
                    logger.info("[InternalLoop] MotivationalField ready ✅")
            if self._motivational_field is not None:
                self._motivational_field.tick(self._slow_cycle_count)
        except Exception as _mf:
            logger.debug(f"[InternalLoop] MotivationalField error (non-fatal): {_mf}")

        # Initialize shared predictive models after the first slow cycle if no
        # response turn has requested them yet. Live turns call this same
        # idempotent helper immediately, so startup timing cannot skip them.
        if self._slow_cycle_count > 1:
            self.ensure_predictive_models()

        # ── v54: AspirationalSynthesisEngine — generative aspiration ──────────
        try:
            if not hasattr(self, '_aspiration_synthesis'):
                self._aspiration_synthesis = None
            if self._aspiration_synthesis is None and self._slow_cycle_count > 10:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.aspirational_synthesis_engine import AspirationalSynthesisEngine
                    self._aspiration_synthesis = AspirationalSynthesisEngine(o, _ai_sys)
                    logger.info("[InternalLoop] AspirationalSynthesisEngine ready ✅")
            if self._aspiration_synthesis is not None:
                self._aspiration_synthesis.tick(self._slow_cycle_count)
        except Exception as _ase:
            logger.debug(f"[InternalLoop] AspirationalSynthesis error (non-fatal): {_ase}")

        # ── v55: TemporalProjection — path simulation toward aspirations ───────
        try:
            if not hasattr(self, '_temporal_projection'):
                self._temporal_projection = None
            if self._temporal_projection is None and self._slow_cycle_count > 10:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.temporal_projection import TemporalProjection
                    self._temporal_projection = TemporalProjection(o, _ai_sys)
                    logger.info("[InternalLoop] TemporalProjection ready ✅")
            if self._temporal_projection is not None:
                self._temporal_projection.tick(self._slow_cycle_count)
        except Exception as _tp:
            logger.debug(f"[InternalLoop] TemporalProjection error (non-fatal): {_tp}")

        # ── v57: CrossLayerFeedback — upward causal loops ──────────────────────
        # Reads outputs from higher layers and writes to operating parameters
        # of lower layers, closing the feedback loops the downward stack missed.
        try:
            if not hasattr(self, '_cross_layer_feedback'):
                self._cross_layer_feedback = None
            if self._cross_layer_feedback is None and self._slow_cycle_count > 5:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys:
                    from cognition.cross_layer_feedback import CrossLayerFeedback
                    self._cross_layer_feedback = CrossLayerFeedback(o, _ai_sys)
                    logger.info("[InternalLoop] CrossLayerFeedback ready ✅")
            if self._cross_layer_feedback is not None:
                self._cross_layer_feedback.tick(self._slow_cycle_count)
        except Exception as _clf:
            logger.debug(f"[InternalLoop] CrossLayerFeedback error (non-fatal): {_clf}")

        # ── v59: GenerativeAspirationEngine — model-gap-driven aspiration ──────
        # Detects concepts that recur without being understood, unnoticed belief
        # tensions, and unexplained relational variance.  Generates aspirations
        # from gaps in the world model rather than from capability combinations.
        try:
            if not hasattr(self, '_generative_aspiration'):
                self._generative_aspiration = None
            if self._generative_aspiration is None and self._slow_cycle_count > 15:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.generative_aspiration_engine import GenerativeAspirationEngine
                    self._generative_aspiration = GenerativeAspirationEngine(o, _ai_sys)
                    logger.info("[InternalLoop] GenerativeAspirationEngine ready ✅")
            if self._generative_aspiration is not None:
                self._generative_aspiration.tick(self._slow_cycle_count)
        except Exception as _gae:
            logger.debug(f"[InternalLoop] GenerativeAspiration error (non-fatal): {_gae}")

        # ── v60: CausalMechanismModel ─────────────────────────────────────────
        try:
            if not hasattr(self, '_causal_mechanism'): self._causal_mechanism = None
            if self._causal_mechanism is None and self._slow_cycle_count > 20:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.causal_mechanism_model import CausalMechanismModel
                    self._causal_mechanism = CausalMechanismModel(o, _ai)
                    logger.info("[InternalLoop] CausalMechanismModel ready ✅")
            if self._causal_mechanism: self._causal_mechanism.tick(self._slow_cycle_count)
        except Exception as _cm:
            logger.debug(f"[InternalLoop] CausalMechanism error (non-fatal): {_cm}")

        # ── v61: LongHorizonPlanner ───────────────────────────────────────────
        try:
            if not hasattr(self, '_long_horizon_planner'): self._long_horizon_planner = None
            if self._long_horizon_planner is None and self._slow_cycle_count > 20:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.long_horizon_planner import LongHorizonPlanner
                    self._long_horizon_planner = LongHorizonPlanner(o, _ai)
                    logger.info("[InternalLoop] LongHorizonPlanner ready ✅")
            if self._long_horizon_planner: self._long_horizon_planner.tick(self._slow_cycle_count)
        except Exception as _lhp:
            logger.warning(
                "[InternalLoop] LongHorizonPlanner error (non-fatal): %s", _lhp
            )

        # ── v62: FluxMindModel ────────────────────────────────────────────────
        try:
            if not hasattr(self, '_flux_mind_model'): self._flux_mind_model = None
            if self._flux_mind_model is None and self._slow_cycle_count > 10:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.flux_mind_model import FluxMindModel
                    self._flux_mind_model = FluxMindModel(o, _ai)
                    logger.info("[InternalLoop] FluxMindModel ready ✅")
            if self._flux_mind_model: self._flux_mind_model.tick(self._slow_cycle_count)
        except Exception as _fmm:
            logger.debug(f"[InternalLoop] FluxMindModel error (non-fatal): {_fmm}")

        # ── v63: NarrativeCompression ─────────────────────────────────────────
        try:
            if not hasattr(self, '_narrative_compression'): self._narrative_compression = None
            if self._narrative_compression is None and self._slow_cycle_count > 10:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.narrative_compression import NarrativeCompression
                    self._narrative_compression = NarrativeCompression(o, _ai)
                    logger.info("[InternalLoop] NarrativeCompression ready ✅")
            if self._narrative_compression: self._narrative_compression.tick(self._slow_cycle_count)
        except Exception as _nc:
            logger.debug(f"[InternalLoop] NarrativeCompression error (non-fatal): {_nc}")

        # ── v64: MetaLearningAudit ────────────────────────────────────────────
        try:
            if not hasattr(self, '_meta_learning_audit'): self._meta_learning_audit = None
            if self._meta_learning_audit is None and self._slow_cycle_count > 10:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.meta_learning_audit import MetaLearningAudit
                    self._meta_learning_audit = MetaLearningAudit(o, _ai)
                    logger.info("[InternalLoop] MetaLearningAudit ready ✅")
            if self._meta_learning_audit: self._meta_learning_audit.tick(self._slow_cycle_count)
        except Exception as _mla:
            logger.debug(f"[InternalLoop] MetaLearningAudit error (non-fatal): {_mla}")

        # ── v65: StructuralCoupling ───────────────────────────────────────────
        try:
            if not hasattr(self, '_structural_coupling'): self._structural_coupling = None
            if self._structural_coupling is None and self._slow_cycle_count > 10:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.structural_coupling import StructuralCoupling
                    self._structural_coupling = StructuralCoupling(o, _ai)
                    logger.info("[InternalLoop] StructuralCoupling ready ✅")
            if self._structural_coupling: self._structural_coupling.tick(self._slow_cycle_count)
        except Exception as _sc:
            logger.debug(f"[InternalLoop] StructuralCoupling error (non-fatal): {_sc}")

        # ── v66: TemporalSelfProjection ───────────────────────────────────────
        try:
            if not hasattr(self, '_temporal_self_projection'): self._temporal_self_projection = None
            if self._temporal_self_projection is None and self._slow_cycle_count > 5:
                _ai = getattr(o, 'ai_system', None)
                if _ai:
                    from cognition.temporal_self_projection import TemporalSelfProjection
                    self._temporal_self_projection = TemporalSelfProjection(o, _ai)
                    logger.info("[InternalLoop] TemporalSelfProjection ready ✅")
            if self._temporal_self_projection: self._temporal_self_projection.tick(self._slow_cycle_count)
        except Exception as _tsp:
            logger.debug(f"[InternalLoop] TemporalSelfProjection error (non-fatal): {_tsp}")

        # Must be ready before SimpleThoughtEvaluator runs (fast cycle) so
        # record_hypothesis() is never dropped.  get_collector(organism) sets the
        # singleton; subsequent no-arg calls return the same instance.
        try:
            from cognition.emergence_metrics import get_collector as _gec
            _gec(o, str(getattr(o, '_data_dir', 'data/persona')))
        except Exception:
            pass
        o = self._organism

        logger.debug(f"[InternalLoop] Slow cycle #{self._slow_cycle_count}")

        # ── Governor: begin cycle — sets mode, budget, pressure snapshot ─────
        _gov_pressure  = getattr(o, '_v32_decision_pressure', {}).get('total', 0.5)
        _ai_sys_g      = getattr(o, 'ai_system', None)
        _ge_g          = getattr(_ai_sys_g, 'goal_engine', None)
        _gov_goal_count = len(getattr(_ge_g, '_goals', {})) if _ge_g else 0
        if self._governor:
            self._governor.begin_cycle(
                total_pressure = _gov_pressure,
                goal_count     = _gov_goal_count,
                cycle_number   = self._slow_cycle_count,
            )

        # 1. Recompute tensions from current state
        tensions = None
        if hasattr(o, "tension_engine") and hasattr(o, "_collect_tension_inputs"):
            try:
                inputs = o._collect_tension_inputs(
                    interaction_recency_seconds=o.seconds_since_interaction()
                )
                tensions = o.tension_engine.compute(**inputs)
                # Scanning for contradictions passively reduces coherence pressure
                # (even if unresolved, the act of inspection brings relief)
                if hasattr(o, 'pressure'):
                    o.pressure.satiate("coherence", 0.06)
            except Exception as e:
                logger.debug(f"[InternalLoop] Tension compute failed: {e}")

        # 2. Update goal ecology
        if tensions and hasattr(o, "goal_ecology"):
            try:
                energy_level = o.energy.level() if hasattr(o, "energy") else 80.0
                o.goal_ecology.update_from_tensions(
                    tensions,
                    energy_level=energy_level,
                    user_present=False,
                )
            except Exception as e:
                logger.debug(f"[InternalLoop] Goal ecology update failed: {e}")

        # 3. Homeostasis evaluation
        if hasattr(o, "homeostasis") and hasattr(o, "_collect_homeostasis_inputs"):
            try:
                h_inputs = o._collect_homeostasis_inputs()
                o.homeostasis.evaluate(**h_inputs)
            except Exception as e:
                logger.debug(f"[InternalLoop] Homeostasis eval failed: {e}")

        # 4. Periodic reflection (every N slow cycles)
        if self._slow_cycle_count % REFLECTION_EVERY_N == 0:
            self._reflection_cycle()

        # 5. Curiosity-driven intention — feeds workspace context only
        # (never triggers spontaneous output — that's the proactive system's job)
        if hasattr(o, "curiosity") and o.energy.curiosity_active():
            top = o.curiosity.top_topic()
            if top and hasattr(o, 'workspace'):
                try:
                    o.workspace.broadcast(
                        source="curiosity.intention",
                        content=f"Inner pull toward: {top}",
                        priority=0.35,
                    )
                except Exception:
                    pass
                logger.debug(f"[InternalLoop] Curiosity intention (workspace only): {top!r}")

        # ── v3: NarrativeIdentity sync (every 6th slow cycle ~12 min) ────
        if self._slow_cycle_count % 6 == 0 and hasattr(o, 'narrative_identity'):
            try:
                o.narrative_identity.sync_from_organism()
            except Exception as _ne:
                pass

        # ── v3: Memory Intrusion tick (every slow cycle) ──────────────────
        if hasattr(o, 'memory_intrusion'):
            try:
                o.memory_intrusion.tick()
            except Exception as _mi:
                pass

        # ── PressureSystem: autonomous drive buildup ──────────────────────
        if hasattr(o, 'pressure'):
            try:
                pressures = o.pressure.tick()
                dominant = max(pressures, key=pressures.get) if pressures else None
                if dominant and pressures[dominant] > 0.75:
                    logger.debug(
                        f"[InternalLoop] Pressure peak: {dominant}={pressures[dominant]:.2f}"
                    )
            except Exception as _pe:
                logger.debug(f"[InternalLoop] Pressure tick error: {_pe}")

        # ── V32: Phase 1 Decision Pressure + Workspace Competition ─────────
        # Every 2 slow cycles: compute pressure AND run workspace competition
        # to select the dominant cognitive focus (winner).
        if (self._phase1 and self._slow_cycle_count % 2 == 0
                and (not self._governor or self._governor.may_run('Phase1Pressure'))):
            try:
                # This loop consumes Phase 1 pressure/competition only. The
                # lightweight Phase 1 plan has no downstream consumer; action
                # execution is owned by GoalActionExecutor and its persistent
                # LongHorizonPlanner plan, so do not generate a duplicate.
                _cycle_result = self._phase1.enhanced_cycle(
                    None, include_advisory_plan=False,
                )
                pressure_result = _cycle_result.get('pressure', {})
                total_pressure  = pressure_result.get('total', 0.5)
                _phase1_competition_output = _cycle_result.get("competition", {})
                _phase1_competition_metrics = _phase1_competition_output.get("competition", {})
                _proposal_admission = _cycle_result.get("rejected_goal_suggestions", [])
                if _proposal_admission:
                    self._record_cycle_stage(
                        "goal_proposal_admission", "partial", output={
                            "rejected_count": len(_proposal_admission),
                            "rejections": _proposal_admission[:12],
                        },
                    )
                _phase1_evidence_ref = self._record_cycle_stage(
                    "phase1_competition", "completed", output=_phase1_competition_output,
                    metrics={
                        "total_pressure": float(total_pressure),
                        "candidate_count": int(_phase1_competition_metrics.get("total_candidates", 0) or 0),
                    },
                )
                self._record_cycle_stage(
                    "phase1_advisory_plan", "skipped_by_design",
                    inputs={"competition_output_ref": _phase1_evidence_ref},
                    output={"reason": "actions are planned by GoalActionExecutor/LongHorizonPlanner"},
                )

                # Log workspace winner — the dominant cognitive focus
                _winner = _cycle_result.get('winner')
                if _winner:
                    _arbitration_status = "no_candidate"
                    _arbitration_output = _winner
                    # Phase 4.1/4.2: Executive Arbitration — re-score top
                    # candidates via prospective prediction; override the
                    # raw-score winner if a runner-up predicts a
                    # meaningfully better outcome. Closes the gap where
                    # competition's all_candidates was computed and
                    # returned but nothing downstream ever read it
                    # (confirmed by reading core/phase1_integration.py —
                    # only `winner` was consumed).
                    try:
                        from cognition.executive_arbitration import arbitrate
                        if not hasattr(self, '_arbitration_runs'):
                            self._arbitration_runs      = 0
                            self._arbitration_overrides = 0
                            self._arbitration_skipped   = 0
                        # Fix: _cycle_result wraps compete()'s FULL raw output
                        # under its own 'competition' key — pass THAT raw
                        # output (already shaped {'winner':...,
                        # 'competition': {'all_candidates':...}}), not the
                        # outer _cycle_result, which would double-nest.
                        _raw_competition = _cycle_result.get('competition', {})
                        # Phase 4.x: sync existing subsystems' status into the
                        # shared WorkspaceState BEFORE arbitrating, so the
                        # multi-factor utility function in executive_
                        # arbitration.py has counterfactual/identity/goal/
                        # calibration terms to read, not just raw+predicted.
                        _gw = getattr(o, "workspace", None)
                        _ws_state = None
                        if _gw is not None:
                            try:
                                from cognition.workspace_state_sync import sync_workspace_state
                                sync_workspace_state(_gw, organism=o, internal_loop=self)
                                _ws_state = _gw.get_state()
                            except Exception as _sync_e:
                                logger.debug(f"[InternalLoop] workspace sync error (non-fatal): {_sync_e}")
                        _emo_v, _emo_a = None, None
                        try:
                            _emo = getattr(getattr(o, 'ai_system', None), 'emotional_state', None)
                            if _emo and hasattr(_emo, 'get_overall_valence_arousal'):
                                _emo_v, _emo_a = _emo.get_overall_valence_arousal()
                        except Exception:
                            pass
                        _arb = arbitrate(
                            _raw_competition, self._consequence_model,
                            self._world_self_dynamics,
                            workspace_state=_ws_state,
                            valence=_emo_v, arousal=_emo_a,
                        )
                        # Fix: this branch previously only logged (and only
                        # counted anything at all) when arbitration actually
                        # overrode the raw winner. On every other cycle —
                        # confirmed winner, or nothing to arbitrate — the
                        # module silently produced zero console output,
                        # making it look like arbitration wasn't running at
                        # all. It now logs (and counts) every run.
                        if _arb is None:
                            _arbitration_status = "no_arbitration_result"
                            self._arbitration_skipped += 1
                            logger.debug(
                                "[InternalLoop] ⚖️ Executive arbitration: "
                                "skipped (no candidates / no PCM data / "
                                "winner not goal-type)"
                            )
                        else:
                            _arbitration_status = "completed"
                            self._arbitration_runs += 1
                            # Phase 5.4: record this decision for later outcome
                            # review, regardless of override — learning from
                            # every goal-type decision, not just overrides,
                            # gives far more signal per unit of engagement.
                            if self._arbitration_learning is not None:
                                try:
                                    _ge = getattr(getattr(o, 'ai_system', None), 'goal_engine', None)
                                    self._arbitration_learning.record(
                                        _arb, self._slow_cycle_count, goal_engine=_ge
                                    )
                                except Exception as _al_e:
                                    logger.debug(f"[InternalLoop] arbitration learning record failed (non-fatal): {_al_e}")
                            if _arb.overridden:
                                self._arbitration_overrides += 1
                                logger.info(
                                    f"[InternalLoop] ⚖️ Executive arbitration: {_arb.reasoning}"
                                )
                                _winner = _arb.arbitrated_winner
                                _arbitration_output = _winner
                            else:
                                logger.info(
                                    f"[InternalLoop] ⚖️ Executive arbitration: {_arb.reasoning}"
                                )
                            _arbitration_output = {
                                "overridden": bool(_arb.overridden),
                                "winner": _winner,
                                "reason_ref": self._evidence_fingerprint(_arb.reasoning),
                            }
                    except Exception as _arb_e:
                        _arbitration_status = "failed"
                        logger.debug(f"[InternalLoop] arbitration error (non-fatal): {_arb_e}")
                    _arbitration_evidence_ref = self._record_cycle_stage(
                        "executive_arbitration", _arbitration_status,
                        inputs={"competition_output_ref": _phase1_evidence_ref},
                        output=_arbitration_output,
                    )

                    # A thought proposal becomes a persistent goal only if it
                    # survives workspace selection and executive arbitration.
                    # GoalEngine owns the write and confirms it from disk;
                    # merely scoring or broadcasting a proposal is not goal
                    # creation.
                    _selected_proposal = None
                    _commit_result = None
                    _winner_source = _winner.get("source_data", {}) if isinstance(_winner, dict) else {}
                    if isinstance(_winner_source, dict):
                        _selected_proposal = _winner_source.get("_goal_proposal")
                    if isinstance(_selected_proposal, dict):
                        if _selected_proposal.get("hypothesis_pending"):
                            _evaluator = getattr(self._phase1, "components", {}).get("thought_evaluator")
                            try:
                                _hypothesis = _evaluator._generate_hypothesis(
                                    str(_selected_proposal.get("origin_content") or ""),
                                    str(_selected_proposal.get("concept") or ""),
                                ) if _evaluator else ""
                            except Exception as _hypothesis_error:
                                logger.debug(
                                    "[InternalLoop] selected proposal hypothesis synthesis failed: %s",
                                    _hypothesis_error,
                                )
                                _hypothesis = ""
                            _selected_proposal["hypothesis"] = _hypothesis
                            _selected_proposal["hypothesis_pending"] = False
                        _selected_goal_engine = getattr(
                            getattr(o, "ai_system", None), "goal_engine", None
                        )
                        if _selected_goal_engine is not None:
                            try:
                                _commit = _selected_goal_engine.commit_selected_thought_proposal(
                                    _selected_proposal, self._slow_cycle_count
                                )
                            except Exception as _commit_error:
                                _commit = {"created": False, "verified": False, "reason": str(_commit_error)}
                            _commit_result = _commit
                            if _commit.get("created") and _commit.get("verified"):
                                _winner = dict(_winner)
                                _winner.update({
                                    "type": "goal",
                                    "id": _commit["id"],
                                    "name": _commit["topic"],
                                    "topic": _commit["topic"],
                                    "label": f"Persisted selected goal: {_commit['topic']}",
                                })
                                logger.info(
                                    "[InternalLoop] Selected proposal committed and read-back verified: "
                                    "goal=%s topic=%r",
                                    _commit["id"], _commit["topic"],
                                )
                            else:
                                logger.info(
                                    "[InternalLoop] Selected thought proposal was not committed: %s",
                                    _commit.get("reason", "not_verified"),
                                )
                    _commit_evidence_ref = self._record_cycle_stage(
                        "selected_proposal_commit",
                        "verified_commit" if isinstance(_commit_result, dict) and _commit_result.get("created") and _commit_result.get("verified")
                        else "rejected_or_unverified" if isinstance(_commit_result, dict)
                        else "no_selected_proposal",
                        inputs={"arbitrated_winner_ref": _arbitration_evidence_ref},
                        output=(
                            {"created": bool(_commit_result.get("created")),
                             "verified": bool(_commit_result.get("verified")),
                             "goal_id_ref": self._evidence_fingerprint(_commit_result.get("id")),
                             "topic_ref": self._evidence_fingerprint(_commit_result.get("topic")),
                             "source_thought_source": _commit_result.get("source_thought_source", ""),
                             "source_thought_type": _commit_result.get("source_thought_type", ""),
                             "source_concept_method": _commit_result.get("source_concept_method", "")}
                            if isinstance(_commit_result, dict) else None
                        ),
                    )
                    _proposal_focus_admitted = self._selected_proposal_commit_admitted(
                        _winner, _commit_result,
                    )
                    _proposal_focus_ref = self._record_cycle_stage(
                        "proposal_durable_focus_admission",
                        "admitted" if _proposal_focus_admitted else "rejected",
                        inputs={"selected_proposal_commit_ref": _commit_evidence_ref},
                        output={"admitted": _proposal_focus_admitted},
                    )
                    if isinstance(_selected_proposal, dict) and not _proposal_focus_admitted:
                        _winner = dict(_winner)
                        _winner["proposal_admission"] = "rejected"

                    _comp  = _cycle_result.get('competition', {}).get('competition', {})
                    _cands = _comp.get('total_candidates', 0)
                    _margin = _comp.get('winning_margin', 0)
                    if isinstance(_selected_proposal, dict) and not _proposal_focus_admitted:
                        logger.info(
                            "[InternalLoop] Workspace proposal rejected from focus: %s "
                            "| score=%.2f (from %s candidates, margin=%.2f)",
                            _winner.get("label", _winner.get("type", "?") + " | " + _winner.get("name", "?"))[:60],
                            float(_winner.get("score", 0) or 0), _cands, _margin,
                        )
                    else:
                        logger.info(
                            f"[InternalLoop] 🏆 Workspace winner: "
                            f"{_winner.get('label', _winner.get('type','?')+' | '+_winner.get('name','?'))[:60]} "
                            f"| score={_winner.get('score',0):.2f} "
                            f"(from {_cands} candidates, margin={_margin:.2f})"
                        )
                    # Store winner for other systems to read
                    _published_workspace_winner = self._workspace_focus_for_consumers(
                        _winner, _proposal_focus_admitted,
                    )
                    o._v32_workspace_winner = _published_workspace_winner
                    o._v32_workspace_winner_cycle = self._slow_cycle_count
                    _ws_state = self._publish_global_workspace_focus(
                        o, _published_workspace_winner,
                        getattr(self, "_long_horizon_planner", None),
                    ) or _ws_state
                    _winner_evidence_ref = self._record_cycle_stage(
                        "winner_published_to_workspace_state", "completed",
                        inputs={
                            "arbitration_output_ref": _arbitration_evidence_ref,
                            "proposal_focus_admission_ref": _proposal_focus_ref,
                        },
                        output={
                            "published_winner": _published_workspace_winner,
                            "raw_cycle_winner_ref": self._evidence_fingerprint(_winner),
                        },
                    )
                    o._v32_workspace_winner_evidence_ref = _winner_evidence_ref
                    o._v32_workspace_winner_evidence_cycle = self._slow_cycle_count

                    # ── WorkspaceBias: commit the focus as an ACTIVE, EMBEDDED
                    # commitment. This is what lets the focus BIAS downstream
                    # selection and be measured as OVERRIDDEN by real behaviour
                    # (instead of only being a prompt string the LLM may ignore).
                    if _proposal_focus_admitted:
                        try:
                            from cognition.workspace_bias import get_workspace_bias
                            get_workspace_bias(o, str(getattr(o, '_data_dir', 'data/persona'))).commit(
                                _winner, self._slow_cycle_count
                            )
                        except Exception as _wb_ce:
                            logger.debug(f"[InternalLoop] workspace-bias commit error (non-fatal): {_wb_ce}")
                    else:
                        logger.info(
                            "[InternalLoop] Rejected proposal remains a cycle observation; "
                            "durable workspace focus was not updated"
                        )
                    # Phase 4.x: also expose the full structured snapshot.
                    # Existing consumers of _v32_workspace_winner (a single
                    # string/dict) are untouched; new/updated consumers
                    # (e.g. cognitive_organism._build_prompt_additions) can
                    # read the richer object without a second sync pass.
                    if _ws_state is not None:
                        o._v32_workspace_state = _ws_state

                    # ── DecisionCommitmentLayer ──────────────────────────
                    # Record this decision and enforce temporal consistency.
                    # Lazy-init on first winner so organism is fully ready.
                    if _proposal_focus_admitted:
                        try:
                            if self._commitment_layer is None:
                                from cognition.decision_commitment import DecisionCommitmentLayer
                                self._commitment_layer = DecisionCommitmentLayer(
                                    o, data_dir=str(getattr(o, '_data_dir', 'data/persona'))
                                )
                                logger.info('[InternalLoop] DecisionCommitmentLayer ready ✅')
                            self._commitment_layer.tick(_winner, self._slow_cycle_count)
                        except Exception as _dcl_e:
                            logger.debug(f'[InternalLoop] CommitmentLayer error: {_dcl_e}')

                    # ── EmergenceMetricsCollector ────────────────────────────
                    try:
                        from cognition.emergence_metrics import get_collector
                        _emc = get_collector(o, str(getattr(o, '_data_dir', 'data/persona')))
                        if _emc:
                            _emc.tick(self._slow_cycle_count)
                    except Exception as _emc_e:
                        logger.debug(f'[InternalLoop] EmergenceMetrics error: {_emc_e}')

                    # Winning workspace arbitration establishes cognitive
                    # focus. It is not an executed effect; GoalActionExecutor
                    # records action feedback only after it actually runs.

                    # Refresh curiosity with winner topic — prevents monotonic decay.
                    # Fix: previously did _winner.get('name','').replace('_',' ')
                    # — feeding slug fragments like "curiosity_wonder_dont" straight
                    # back into curiosity.json, actively injecting noise topics.
                    # Now uses the clean 'topic' field; skips entirely if absent
                    # rather than falling back to slug-mangling.
                    if (
                        _proposal_focus_admitted
                        and hasattr(o, 'curiosity')
                        and _winner.get('type') in ('goal', 'thought')
                    ):
                        try:
                            _topic = _winner.get('topic', '')
                            if _topic and len(_topic) > 3:
                                o.curiosity.add_question(_topic, f"What can I learn about {_topic}?")
                        except Exception:
                            pass

                if not _winner:
                    _no_winner_ref = self._record_cycle_stage(
                        "executive_arbitration", "skipped_no_winner",
                        inputs={"competition_output_ref": _phase1_evidence_ref},
                    )
                    # An explicit empty arbitration result supersedes the last
                    # focus. Leaving the previous object in shared organism
                    # state lets prompt consumers keep presenting it forever
                    # and can make the action executor treat it as current.
                    self._record_cycle_stage(
                        "selected_proposal_commit", "no_winner",
                        inputs={"arbitrated_winner_ref": _no_winner_ref},
                    )
                    self._publish_empty_workspace_focus(
                        o, reason="no_candidate", status="no_winner",
                        inputs={"competition_output_ref": _phase1_evidence_ref},
                    )

                # Log high pressure
                if total_pressure > 0.7:
                    logger.info(
                        f"[InternalLoop] V32 High decision pressure: {total_pressure:.2f} "
                        f"({pressure_result.get('interpretation', 'UNKNOWN')})"
                    )

                # Store pressure for access by other systems
                o._v32_decision_pressure = pressure_result

            except Exception as _p1e:
                self._record_cycle_stage("phase1_competition", "failed", metrics={"error_type": type(_p1e).__name__})
                # A failed arbitration cannot authorize stale attention or
                # allow an unrelated old goal to be selected downstream.
                self._publish_empty_workspace_focus(
                    o, reason="phase1_failed", status="cleared_after_error",
                )
                logger.debug(f"[InternalLoop] Phase 1 pressure/workspace error: {_p1e}")
        elif self._phase1:
            self._record_cycle_stage(
                "phase1_competition",
                "skipped_governor" if self._slow_cycle_count % 2 == 0 else "skipped_cadence",
            )
        else:
            self._record_cycle_stage("phase1_competition", "unavailable")

        # ── GoalEngine: autonomous goal formation & maintenance ───────────
        # tick() now correctly reads pressures from organism.pressure and
        # topics from organism.semantic_memory — real goal emergence, not
        # injection. Goals form from identity traits × actual topics discussed.
        _ai_sys = getattr(o, 'ai_system', None)
        _ge = getattr(_ai_sys, 'goal_engine', None)
        if _ge is not None and (not self._governor or self._governor.may_run('GoalEngine')):
            try:
                _ge.tick()
                _get_tick_report = getattr(_ge, "get_last_tick_report", None)
                _goal_engine_report = _get_tick_report() if callable(_get_tick_report) else None
                _goal_engine_status = (
                    str(_goal_engine_report.get("status", "returned_without_receipt"))
                    if isinstance(_goal_engine_report, dict) else "returned_without_receipt"
                )
                _ge_active = len([g for g in _ge._goals.values() if g.status == "active"])
                _goal_engine_evidence_ref = self._record_cycle_stage(
                    "goal_engine_tick", _goal_engine_status,
                    output=_goal_engine_report or {"active_goal_count": _ge_active},
                )
                if self._governor:
                    self._governor.record('GoalEngine', _ge_active)

                # Inject active goal thoughts into GW for CCS + Observatory
                if hasattr(o, 'workspace'):
                    if _goal_engine_status == "failed":
                        self._record_cycle_stage(
                            "goal_thoughts_broadcast", "skipped_upstream_failure",
                            inputs={"goal_engine_output_ref": _goal_engine_evidence_ref},
                        )
                    else:
                        _goal_thoughts = _ge.get_goal_thoughts()
                        _broadcast_status, _broadcast_metrics = self._broadcast_goal_thoughts(
                            o.workspace, _goal_thoughts
                        )
                        self._record_cycle_stage(
                            "goal_thoughts_broadcast", _broadcast_status,
                            inputs={"goal_engine_output_ref": _goal_engine_evidence_ref},
                            output=_broadcast_metrics,
                        )
                else:
                    self._record_cycle_stage(
                        "goal_thoughts_broadcast", "unavailable",
                        inputs={"goal_engine_output_ref": _goal_engine_evidence_ref},
                    )
            except Exception as _ge_e:
                self._record_cycle_stage("goal_engine_tick", "failed", metrics={"error_type": type(_ge_e).__name__})
                logger.debug(f"[InternalLoop] Goal engine tick error: {_ge_e}")
        elif _ge is not None:
            self._record_cycle_stage("goal_engine_tick", "skipped_governor")
        else:
            self._record_cycle_stage("goal_engine_tick", "unavailable")

        # ── GoalActionExecutor: translate goals → concrete actions ───────────
        # Runs every _action_every_n slow cycles. Picks the highest-activation
        # goal and executes one action: memory_recall, web_search,
        # user_question, or self_question. Increments actions_taken so GEI rises.
        if self._slow_cycle_count % self._action_every_n == 0:
            try:
                # Lazy init — needs the organism reference
                if self._goal_action_executor is None:
                    from cognition.goal_action_executor import GoalActionExecutor
                    self._goal_action_executor = GoalActionExecutor(o)
                    logger.info("[InternalLoop] GoalActionExecutor ready ✅")

                _winner = getattr(o, "_v32_workspace_winner", None)
                winner_cycle = int(getattr(o, "_v32_workspace_winner_cycle", -10**9))
                winner_age = self._slow_cycle_count - winner_cycle
                decision_is_fresh = (
                    isinstance(_winner, dict)
                    and 0 <= winner_age <= 2
                )
                preferred_goal_id = (
                    str(_winner.get("id"))
                    if decision_is_fresh and _winner.get("type") == "goal" and _winner.get("id")
                    else None
                )
                # A fresh arbitration decision is authoritative. If attention
                # selected a thought/tension or a goal unavailable to the
                # executor, do not silently act on an unrelated older goal.
                _action_report = self._goal_action_executor.run_tick(
                    preferred_goal_id=preferred_goal_id,
                    selection_is_authoritative=decision_is_fresh,
                    cycle_id=self._slow_cycle_count,
                )
                _action_receipt = self._goal_action_receipt(
                    _action_report, self._goal_action_executor,
                )
                _previous_winner_ref = getattr(o, "_v32_workspace_winner_evidence_ref", None)
                _action_stage_status = (
                    str(_action_receipt.get("outcome_status", "completed"))
                    if isinstance(_action_receipt, dict) else "no_action_report"
                )
                self._record_cycle_stage(
                    "goal_action_executor", _action_stage_status,
                    inputs={
                        "winner_output_ref": _previous_winner_ref if decision_is_fresh else None,
                        "decision_fresh": decision_is_fresh,
                        "winner_age_cycles": winner_age,
                        "preferred_goal_id_ref": self._evidence_fingerprint(preferred_goal_id) if preferred_goal_id else None,
                    },
                    output=_action_receipt,
                )
                if _action_report and _action_report.get("success"):
                    logger.info(
                        f"[InternalLoop] ⚡ Goal action: "
                        f"{_action_report['action']} on "
                        f"'{_action_report['goal_topic'][:30]}' — "
                        f"{_action_report['result'][:60]}"
                    )
            except Exception as _ae:
                self._record_cycle_stage("goal_action_executor", "failed", metrics={"error_type": type(_ae).__name__})
                logger.debug(f"[InternalLoop] GoalActionExecutor error: {_ae}")
        else:
            self._record_cycle_stage("goal_action_executor", "skipped_cadence")

        # ── V32: Phase 1 Thread Resolution (prevent infinite loops) ───────
        # Every 10 slow cycles (~20 minutes), resolve stuck thought threads
        if self._phase1 and self._slow_cycle_count % 10 == 0:
            try:
                resolved, deferred = self._phase1.resolve_stuck_threads()
                if resolved > 0 or deferred > 0:
                    logger.info(
                        f"[InternalLoop] V32 Thread resolution: "
                        f"{resolved} resolved, {deferred} deferred"
                    )
            except Exception as _tr:
                logger.debug(f"[InternalLoop] Thread resolution error: {_tr}")

        # ── V33: Phase 2 Advanced Thought Evaluation (semantic) ───────────
        # Every 7 slow cycles (~14 minutes), evaluate thoughts with semantic analysis
        _phase2_eval_due = self._slow_cycle_count % 7 == 0
        _phase2_eval_allowed = (
            self._phase2 is not None
            and _phase2_eval_due
            and (not self._governor or self._governor.may_run('Phase2ThoughtEval'))
        )
        if self._phase2 is None:
            self._record_cycle_stage("phase2_advanced_evaluation", "unavailable")
        elif not _phase2_eval_due:
            self._record_cycle_stage(
                "phase2_advanced_evaluation", "skipped_cadence",
                metrics={"cycle": self._slow_cycle_count, "interval_cycles": 7},
            )
        elif not _phase2_eval_allowed:
            self._record_cycle_stage(
                "phase2_advanced_evaluation", "skipped_governor",
                metrics=self._phase2_governor_skip_metrics("Phase2ThoughtEval"),
            )
        else:
            try:
                evaluated_thoughts = self._phase2.evaluate_thoughts_advanced()
                _phase2_eval_ref = self._record_cycle_stage(
                    "phase2_advanced_evaluation",
                    "completed" if evaluated_thoughts else "no_candidates",
                    output={"evaluated_count": len(evaluated_thoughts or [])},
                )
                if evaluated_thoughts:
                    logger.info(
                        f"[InternalLoop] V33 Advanced evaluation: {len(evaluated_thoughts)} thoughts "
                        f"analyzed with semantic similarity"
                    )
                    
                    # Create/mutate goals from advanced evaluation
                    _goal_engine = getattr(
                        getattr(o, "ai_system", None), "goal_engine", None
                    )
                    mutations = self._phase2.create_and_mutate_goals(
                        evaluated_thoughts, goal_engine=_goal_engine
                    )
                    if (_goal_engine is not None
                            and hasattr(_goal_engine, "reload_from_disk") and any(
                        mutations.get(key)
                        for key in ("created_goals", "updated_goals", "merged_goals")
                    )):
                        _goal_engine.reload_from_disk()
                    
                    created = len(mutations.get('created_goals', []))
                    updated = len(mutations.get('updated_goals', []))
                    merged = len(mutations.get('merged_goals', []))
                    
                    if created or updated or merged:
                        logger.info(
                            f"[InternalLoop] V33 Goal mutations: "
                            f"{created} created, {updated} updated, {merged} merged"
                        )
                    self._record_cycle_stage(
                        "phase2_goal_mutation", "completed",
                        inputs={"evaluation_output_ref": _phase2_eval_ref},
                        output={
                            "created_count": created,
                            "updated_count": updated,
                            "merged_count": merged,
                        },
                    )
            except Exception as _ate:
                self._record_cycle_stage(
                    "phase2_advanced_evaluation", "failed",
                    metrics={"error_type": type(_ate).__name__},
                )
                logger.debug(f"[InternalLoop] Advanced thought evaluation error: {_ate}")

        # ── EventBus heartbeat: emit dominant drive state every slow cycle ─
        # This ensures the bus is active even between surprising interactions,
        # and gives the health monitor a non-zero baseline to evaluate.
        if hasattr(o, 'event_bus') and hasattr(o, 'pressure'):
            try:
                from core.cognitive_event_bus import DRIVE_SPIKE
                pressures = o.pressure.levels() if hasattr(o.pressure, 'levels') else {}
                if not pressures:
                    pressures = {
                        k: r.effective_pressure()
                        for k, r in getattr(o.pressure, 'reservoirs', {}).items()
                    }
                if pressures:
                    dominant = max(pressures, key=pressures.get)
                    dominant_level = pressures[dominant]
                    if dominant_level > 0.40:  # only emit if meaningfully active
                        o.event_bus.emit(DRIVE_SPIKE, {
                            "drive":   dominant,
                            "urgency": round(dominant_level, 3),
                            "source":  "internal_loop_heartbeat",
                        }, source="internal_loop")
            except Exception:
                pass

        # ── SleepCycleManager: phase tick + dispatch queued tasks ─────────
        if hasattr(o, 'sleep_cycle'):
            try:
                phase = o.sleep_cycle.tick()
                executed = o.sleep_cycle.run_pending()
                if executed:
                    logger.info(f"[InternalLoop] Sleep phase {phase.value}: ran {executed}")
            except Exception as _sc:
                logger.debug(f"[InternalLoop] SleepCycle tick error: {_sc}")

        # ── Identity batch processing (SLEEP phase preferred, fallback in slow cycle) ──
        # FIX: identity_queue was at 51 and never draining.
        # Root cause: priority=8 with skip_if_busy=True means it almost never
        # acquires the lock (BACKGROUND_PRIORITY_THRESHOLD=3, anything >= 3
        # uses non-blocking acquire). Changed to priority=2 (below threshold)
        # so it BLOCKS briefly and actually drains. In sleep/dream: priority=1
        # (highest urgency). Also run up to 2 drain passes per slow cycle when
        # queue is large, applying goal fitness mutation on high-dissonance items.
        try:
            sc_phase = getattr(getattr(o, 'sleep_cycle', None), 'phase', None)
            ai_sys   = getattr(o, 'ai_system', None)
            phase_val = sc_phase.value if sc_phase else 'unknown'
            if ai_sys:
                id_sys = getattr(ai_sys, 'identity_system', None)
                if id_sys and id_sys.pending_memory_count > 0:
                    from core.llm_scheduler import llm_scheduler
                    _in_rest_phase = phase_val in ('sleep', 'dream')
                    # Priority BELOW threshold → blocking acquire (actually drains)
                    _prio = 1 if _in_rest_phase else 2
                    # Large queue: attempt 2 passes per cycle
                    _passes = 2 if id_sys.pending_memory_count > 20 else 1
                    for _ in range(_passes):
                        with llm_scheduler.sync_slot(priority=_prio, skip_if_busy=False,
                                                     caller="identity_batch") as acq:
                            if acq:
                                id_sys.get_identity()
                                logger.debug(
                                    f"[InternalLoop] Identity batch drained "
                                    f"(phase={phase_val}), "
                                    f"{id_sys.pending_memory_count} still pending"
                                )
        except Exception as _ib:
            logger.debug(f"[InternalLoop] Identity batch error: {_ib}")

        # ── GW → Episodic Memory: persist high-priority broadcasts ───────────
        # Every slow cycle (~2 min), drain GW items with priority ≥ 0.60
        # that haven't been written to FAISS yet. This closes the gap between
        # the working memory (volatile) and episodic memory (persistent).
        try:
            ws  = getattr(o, 'workspace', None)
            ms  = getattr(getattr(o, 'ai_system', None), 'memory_system', None)
            if ws and ms:
                now   = time.time()
                since = getattr(self, '_last_gw_flush', 0.0)
                items = [i for i in ws.recent(32)
                         if getattr(i, 'priority', 0) >= 0.75   # raised from 0.60
                         and getattr(i, 'timestamp', 0) > since]
                _skip_sources = {'ambient_vision', 'curiosity.intention',
                                 'semantic_extractor', 'ambient_vision.faces'}
                for item in items[:4]:   # max 4 per cycle (was 6)
                    src  = getattr(item, 'source', 'workspace')
                    text = getattr(item, 'content', '')
                    if text and src not in _skip_sources:
                        ms.add_memory(
                            f"[GW/{src}] {text[:300]}",
                            impact_score = min(1.0, getattr(item, 'priority', 0.6)),
                            memory_type  = "cognitive_event",
                            valence      = "Neutral",
                            arousal      = "Medium",
                        )
                if items:
                    logger.debug(f"[InternalLoop] GW→Episodic: flushed {min(len(items),6)} items")
                self._last_gw_flush = now
        except Exception as _gw:
            logger.debug(f"[InternalLoop] GW→Episodic flush error: {_gw}")

        # ── ThoughtStream periodic flush to disk ─────────────────────────────
        try:
            ts = getattr(o, 'thought_stream', None)
            if ts and hasattr(ts, 'flush'):
                ts.flush()
        except Exception:
            pass

        # ── AutonomousReflectionEngine: LLM-based self-understanding ──────────
        # Runs background LLM calls (priority=3, skip_if_busy=True) to generate
        # novel linguistic comprehension of the system's own evolution.
        # Lazy-init after slow cycle 1 so ai_system is fully ready.
        try:
            if self._autonomous_reflection is None and self._slow_cycle_count > 1:
                from cognition.autonomous_reflection import AutonomousReflectionEngine
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    self._autonomous_reflection = AutonomousReflectionEngine(
                        organism  = o,
                        ai_system = _ai_sys,
                    )
                    logger.info("[InternalLoop] AutonomousReflectionEngine ready ✅")

            if self._autonomous_reflection is not None:
                # v43: Run passive confidence decay each slow cycle
                try:
                    self._autonomous_reflection._epistemic.decay_cycle()
                except Exception:
                    pass

                # v42: LLM-based self-interpretation (preemptible)
                # v49: propagate counterfactual mode flag if immune system is active
                if (hasattr(self, '_cognitive_immune')
                        and self._cognitive_immune is not None
                        and self._cognitive_immune.is_counterfactual_active()):
                    self._autonomous_reflection._immune_counterfactual_active = True
                elif hasattr(self._autonomous_reflection, '_immune_counterfactual_active'):
                    del self._autonomous_reflection._immune_counterfactual_active
                self._autonomous_reflection.tick(self._slow_cycle_count)

                # Phase 6.15 — self-description scan (self_description.py),
                # same cadence as AutonomousReflection per the spec's own
                # guidance ("call from the same slow-cycle path"). Cheap —
                # reads module-level constants, no LLM call — so no extra
                # cadence gating needed beyond piggybacking on this tick.
                try:
                    from cognition.self_description import get_self_description
                    _drifted = get_self_description().scan_known_components()
                    if _drifted:
                        logger.info(f"[InternalLoop] SelfDescription: {_drifted} component(s) drifted since last scan")
                except Exception as _sd_e:
                    logger.debug(f"[InternalLoop] SelfDescription scan failed (non-fatal): {_sd_e}")
        except Exception as _are:
            logger.debug(f"[InternalLoop] AutonomousReflection error (non-fatal): {_are}")

        # ── ProactiveOutreachEngine — reach out to users when relevant ─────────
        try:
            if self._proactive_outreach is None and self._slow_cycle_count > 5:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.proactive_outreach import ProactiveOutreachEngine
                    self._proactive_outreach = ProactiveOutreachEngine(
                        organism  = o,
                        ai_system = _ai_sys,
                    )
                    logger.info("[InternalLoop] ProactiveOutreachEngine ready ✅")
            if self._proactive_outreach is not None:
                self._proactive_outreach.tick(self._slow_cycle_count)
        except Exception as _poe:
            logger.debug(f"[InternalLoop] ProactiveOutreach error (non-fatal): {_poe}")

        # ── Phase 5.0: AutonomousCuriosityResolver — curiosity → goals ─────────
        # Was fully built (respects behavior_gate, avoids duplicate
        # promotion, bounded to 2 goals per check) but never instantiated
        # or called anywhere in the codebase until now.
        try:
            if self._autonomous_curiosity_resolver is None:
                from cognition.autonomous_curiosity_resolver import AutonomousCuriosityResolver
                self._autonomous_curiosity_resolver = AutonomousCuriosityResolver(o)
                logger.info("[InternalLoop] AutonomousCuriosityResolver ready ✅")
            self._autonomous_curiosity_resolver.tick(self._slow_cycle_count)
        except Exception as _acr_e:
            logger.debug(f"[InternalLoop] AutonomousCuriosityResolver error (non-fatal): {_acr_e}")

        # ── v46: Skill decay, emotional memory residue, preference decay ───
        try:
            sr = getattr(o, 'skill_registry', None)
            if sr:
                if hasattr(sr, 'maintenance_cycle'):
                    sr.maintenance_cycle(self._slow_cycle_count)
                else:
                    sr.decay_cycle()
        except Exception:
            pass
        try:
            em = getattr(o, 'emotional_memory', None)
            if em:
                em.slow_cycle_tick()
        except Exception:
            pass
        try:
            pe = getattr(o, 'preference_engine', None)
            if pe:
                pe.decay_cycle()
        except Exception:
            pass

        # ── v47: Resolution engine — intentional closure ───────────────────
        try:
            if not hasattr(self, '_resolution_engine'):
                self._resolution_engine = None
            if self._resolution_engine is None and self._slow_cycle_count > 3:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.resolution_engine import ResolutionEngine
                    self._resolution_engine = ResolutionEngine(o, _ai_sys)
                    logger.info("[InternalLoop] ResolutionEngine ready ✅")
            if self._resolution_engine is not None:
                self._resolution_engine.tick(self._slow_cycle_count)
        except Exception as _re:
            logger.debug(f"[InternalLoop] ResolutionEngine error (non-fatal): {_re}")

        # ── v47: Autonomous experimentation ───────────────────────────────
        try:
            if not hasattr(self, '_auto_experiment'):
                self._auto_experiment = None
            if self._auto_experiment is None and self._slow_cycle_count > 3:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.autonomous_experimentation import AutonomousExperimentationEngine
                    self._auto_experiment = AutonomousExperimentationEngine(o, _ai_sys)
                    logger.info("[InternalLoop] AutonomousExperimentationEngine ready ✅")
            if self._auto_experiment is not None:
                self._auto_experiment.tick(self._slow_cycle_count)
        except Exception as _ae:
            logger.debug(f"[InternalLoop] AutoExperiment error (non-fatal): {_ae}")

        # Proposal-driven Workspace capability experiment. This is deliberately
        # independent from chat and from the LLM-backed experimentation engine.
        try:
            if self._capability_development is None:
                from cognition.capability_development import CapabilityDevelopmentEngine
                self._capability_development = CapabilityDevelopmentEngine(o)
                logger.info("[InternalLoop] CapabilityDevelopmentEngine ready")
            self._capability_development.tick(self._slow_cycle_count)
        except Exception as _cde:
            logger.debug(f"[InternalLoop] Capability development error (non-fatal): {_cde}")

        # ── Multi-causal cognitive restructuring ──────────────────────────
        # Clusters persistent tensions and evaluates correction strategies in
        # the background. It never adds a generative call to the chat path.
        try:
            if self._cognitive_restructuring is None:
                self._cognitive_restructuring = getattr(o, "_cognitive_restructuring", None)
            if self._cognitive_restructuring is None:
                from cognition.cognitive_restructuring_engine import CognitiveRestructuringEngine
                self._cognitive_restructuring = CognitiveRestructuringEngine(o)
                logger.info("[InternalLoop] CognitiveRestructuringEngine ready ✅")
            self._cognitive_restructuring.tick(self._slow_cycle_count)
        except Exception as _cr:
            logger.debug(f"[InternalLoop] Cognitive restructuring error (non-fatal): {_cr}")

        # ── Phase 3.3: CounterfactualSimulator ───────────────────────────────
        # Retroactively evaluates the last 10 interactions against all
        # alternative action types using PCM and WSDM's existing k-NN
        # machinery. Gated by MIN_RECORDS_FOR_CF (15) and CF_INTERVAL_CYCLES
        # (5 consolidation cycles) — fires ~every 50 minutes, not every cycle.
        try:
            if not hasattr(self, '_counterfactual_sim'):
                self._counterfactual_sim = None
            if self._counterfactual_sim is None and self._slow_cycle_count > 15:
                from cognition.counterfactual_simulator import CounterfactualSimulator
                self._counterfactual_sim = CounterfactualSimulator(o)
                logger.info("[InternalLoop] CounterfactualSimulator ready ✅")
            if self._counterfactual_sim is not None:
                self._counterfactual_sim.tick(self._slow_cycle_count)
        except Exception as _cf_e:
            logger.debug(f"[InternalLoop] CounterfactualSimulator error (non-fatal): {_cf_e}")

        # ── Phase 3.5: IntrospectiveObserver ────────────────────────────────
        # Computes longitudinal observations from attention history,
        # personality history, calibration ECE, counterfactual patterns,
        # and emergence metrics. Runs every 10 consolidation cycles (~100 min).
        try:
            if not hasattr(self, '_introspective_observer'):
                self._introspective_observer = None
            if self._introspective_observer is None and self._slow_cycle_count > 20:
                from cognition.introspective_observer import IntrospectiveObserver
                self._introspective_observer = IntrospectiveObserver(o)
                logger.info("[InternalLoop] IntrospectiveObserver ready ✅")
            if self._introspective_observer is not None:
                self._introspective_observer.tick(self._slow_cycle_count)
        except Exception as _io_e:
            logger.debug(f"[InternalLoop] IntrospectiveObserver error (non-fatal): {_io_e}")

        # ── v47: Skill transfer links (every 60 slow cycles ≈ 2 hours) ────
        try:
            sr = getattr(o, 'skill_registry', None)
            if sr and self._slow_cycle_count % 60 == 0 and self._slow_cycle_count > 0:
                sr.generate_transfer_links()
        except Exception:
            pass

        # ── v48: Cognitive audit — self-directed development ──────────────
        # Reads five performance signals every ~80 min, detects sustained
        # underperformance, proposes a parameter calibration via LLM,
        # trials it for ~2 hours, then commits or reverts based on outcome.
        # One trial at a time.  Priority 3 / skip_if_busy — never blocks.
        try:
            if not hasattr(self, '_cognitive_audit'):
                self._cognitive_audit = None
            if self._cognitive_audit is None and self._slow_cycle_count > 5:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.cognitive_audit_engine import CognitiveAuditEngine
                    self._cognitive_audit = CognitiveAuditEngine(o, _ai_sys)
                    logger.info("[InternalLoop] CognitiveAuditEngine ready ✅")
            if self._cognitive_audit is not None:
                self._cognitive_audit.tick(self._slow_cycle_count)
        except Exception as _cae:
            logger.debug(f"[InternalLoop] CognitiveAudit error (non-fatal): {_cae}")

        # ── v49: Cognitive immune system — attractor detection ───────────────
        # Reads five ecology-level signals every ~60 min and triggers
        # counterfactual mode when self-reinforcing attractor patterns are
        # detected.  Coordinates with CognitiveAuditEngine (never runs
        # counterfactual while an audit trial is active).
        try:
            if not hasattr(self, '_cognitive_immune'):
                self._cognitive_immune = None
            if self._cognitive_immune is None and self._slow_cycle_count > 5:
                _ai_sys = getattr(o, 'ai_system', None)
                if _ai_sys and _llm_available(_ai_sys):
                    from cognition.cognitive_immune_system import CognitiveImmuneSystem
                    self._cognitive_immune = CognitiveImmuneSystem(o, _ai_sys)
                    logger.info("[InternalLoop] CognitiveImmuneSystem ready ✅")
            if self._cognitive_immune is not None:
                self._cognitive_immune.tick(self._slow_cycle_count)
        except Exception as _cis:
            logger.debug(f"[InternalLoop] CognitiveImmune error (non-fatal): {_cis}")

        # ── CognitiveStack decay tick ─────────────────────────────────────────
        # Without this, topic frames accumulate indefinitely. Each slow cycle
        # decays confidence and prunes stale frames so the stack stays current.
        try:
            from cognition.cognitive_stack import get_cognitive_stack
            get_cognitive_stack().tick()
        except Exception as _cs:
            logger.debug(f"[InternalLoop] CognitiveStack tick error (non-fatal): {_cs}")

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
                    metrics={"active_thread_count": len(active_threads) if hasattr(active_threads, "__len__") else -1},
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
                cde_ctx = CDEContext(
                    threads        = active_threads,
                    world_model    = wm_data,
                    beliefs        = beliefs,
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
                _cde_evidence_ref = self._record_cycle_stage(
                    "cognitive_dissonance_engine", "completed",
                    inputs={"thread_state_ref": _tte_evidence_ref},
                    output=active_threads,
                    metrics={"active_thread_count": len(active_threads) if hasattr(active_threads, "__len__") else -1},
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

                # Store on organism for CognitivePreProcessor to consume
                o._dominant_thought = result
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
                        for _t in self._tte.all_threads():
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
                        self._record_cycle_stage(
                            "phase2_narrative_synthesis",
                            "completed" if narrative else "no_narrative",
                            output={"narrative_present": bool(narrative)},
                        )
                        
                        if narrative:
                            logger.info(f"[InternalLoop] V33 Narrative: {narrative[:80]}...")
                            
                            # Broadcast to workspace
                            if hasattr(o, 'workspace'):
                                o.workspace.broadcast(
                                    source="v33.narrative_synthesizer",
                                    content=narrative,
                                    priority=0.65
                                )
                    except Exception as _ns:
                        self._record_cycle_stage(
                            "phase2_narrative_synthesis", "failed",
                            metrics={"error_type": type(_ns).__name__},
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
                            metrics={"error_type": type(_til).__name__},
                        )
                        logger.debug(f"[InternalLoop] Thread→Identity linking error: {_til}")


            except Exception as _tte_e:
                self._record_cycle_stage("thought_thread_cde_dts_chain", "failed", metrics={"error_type": type(_tte_e).__name__})
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
                        metrics={"error_type": type(_e4).__name__},
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
                report = self._thread_lifecycle_mgr.run()
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
                        metrics={"error_type": type(_e5).__name__},
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
        if (self._arbitration_learning
                and self._slow_cycle_count % 8 == 0
                and (not self._governor or self._governor.may_run('ARB_LEARN'))):
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
