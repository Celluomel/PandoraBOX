Warning: truncated output (original token count: 128670)
Total output lines: 9274

"""
Persona Bridge
==============
PandoraBOX IS the chatbot. Robot Agent feeds user input here and renders what
PandoraBOX returns. PandoraBOX builds her own psychological system prompt internally
and ALL of her lifecycle methods run exactly as in standalone mode.

Public API consumed by app.py
------------------------------
    state.persona.get_response_stream(user_text, user_id, vision_context=None)
        → async generator yielding str tokens then a final dict:
          {"__meta__": True, "raw": str, "speech": str, "emotion": str, "intensity": float}

    state.persona.get_system_status()   → dict for /lumina dashboard
    state.persona.get_prompt_context(user_id)  → dict for status bar pills
    state.persona.receive_feedback(positive, user_id, last_response)
    state.persona.trigger_dream()
    state.persona.trigger_learning()
    state.persona.is_ready  → bool
"""

import asyncio
import datetime as _dt
import hashlib
import json
import logging
import math
import re
import sys
import threading
import time
from typing import Any
from managers.settings_manager import get_persona_name as _gpn
from cognition.identity_boundary import prompt_block as _identity_boundary_block
from cognition.body_runtime.robot_capabilities import robot_capability_report, robot_inventory_observation
from cognition.memory_retrieval import (
    exact_filename_recall_result,
    explicit_recall_source_result,
    explicit_recall_abstention_result,
    extract_explicit_recall_topic,
    filter_recall_query_records,
    filter_memories_by_modality,
    is_explicit_memory_recall_query,
    is_visual_memory_query,
    merge_user_authored_memories,
)
from cognition.turn_context_evidence import (
    audit_safe_turn_summary,
    deterministic_reasoning_dependencies,
    format_memory_for_prompt,
    memory_retrieval_evidence,
    memory_prompt_injection_evidence,
    profile_context_evidence,
    response_learning_evidence,
    USER_PROFILE_PROVENANCE_POLICY,
    tag_memory_retrieval_lane,
)
from cognition.factual_self_report_context import history_without_assistant_claims
from core.turn_execution_context import (
    current_turn_id as _current_audit_turn_id,
    normalize_turn_id as _normalize_audit_turn_id,
    set_current_turn_id as _set_audit_turn_id,
)

from pathlib import Path

logger = logging.getLogger(__name__)

_TURN_OUTPUT_UNSET = object()


def _turn_output_evidence(value: Any) -> tuple[str, dict[str, Any]]:
    """Return a stable fingerprint and redacted shape summary for turn data."""
    try:
        from core.module_tick_log import summarize_output
        summary = summarize_output(value)
    except Exception:
        summary = {"type": type(value).__name__, "quality": "shape_only"}
    safe_summary = audit_safe_turn_summary(value)
    if safe_summary is not None:
        summary = safe_summary
    try:
        if isinstance(value, bytes):
            material = value
        elif isinstance(value, str):
            material = value.encode("utf-8", errors="replace")
        else:
            material = json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                default=lambda item: {"__type__": type(item).__name__},
            ).encode("utf-8", errors="replace")
    except Exception:
        material = type(value).__qualname__.encode("utf-8")
    return hashlib.sha256(material).hexdigest(), summary


def _runtime_execution_evidence_snapshot(trace: Any) -> dict[str, Any]:
    """Build a bounded, turn-specific snapshot for deterministic trace reports."""
    trace = trace if isinstance(trace, dict) else {}
    stages = trace.get("stages", {})
    stages = stages if isinstance(stages, dict) else {}
    stage_names = (
        "turn_input", "input_safety", "self_description_context",
        "memory_retrieval", "cognitive_prompt_context", "prompt_assembly",
        "primary_generation", "provider_completion", "response_finalization",
        "response_learning_and_memory", "organism_post_interaction",
    )
    stage_statuses = {
        name: str(stages[name].get("status") or "unknown")[:48]
        for name in stage_names if isinstance(stages.get(name), dict)
    }
    sources = trace.get("context_sources", {})
    sources = sources if isinstance(sources, dict) else {}
    manifest = sources.get("module_tick_manifest", {})
    manifest = manifest if isinstance(manifest, dict) else {}
    manifest_fields = (
        "module_count", "observed_count", "tick_count", "error_count",
        "initialized_unobserved_count", "unavailable_count",
    )
    manifest_snapshot = {
        "status": str(manifest.get("status") or "unavailable")[:48],
        **{
            key: max(0, _safe_nonnegative_int(manifest.get(key)))
            for key in manifest_fields
        },
    }
    return {
        "type": "runtime_execution_evidence_snapshot",
        "turn_id": str(trace.get("turn_id") or "")[:120],
        "trace_available": bool(trace.get("turn_id")),
        "stage_statuses": stage_statuses,
        "module_tick_manifest": manifest_snapshot,
        **{
            key: manifest_snapshot[key]
            for key in manifest_fields
        },
    }


def _safe_nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _workspace_focus_state_provenance(snapshot: Any, *, now: float | None = None) -> dict[str, Any]:
    """Return provenance for a snapshot focus when no arbitration receipt exists.

    GlobalWorkspace keeps writer/timestamp records per updated field. This is
    weaker than a cycle evidence reference, but lets the turn trace distinguish
    a state snapshot from an unattributed focus without claiming causality.
    """
    if not isinstance(snapshot, dict):
        to_dict = getattr(snapshot, "to_dict", None)
        snapshot = to_dict() if callable(to_dict) else {}
    if not isinstance(snapshot, dict) or not str(snapshot.get("focus") or "").strip():
        return {}
    updates = snapshot.get("updated_by")
    if not isinstance(updates, list):
        return {}
    for update in reversed(updates):
        if not isinstance(update, dict):
            continue
        fields = update.get("fields")
        if not isinstance(fields, (list, tuple)) or "focus" not in fields:
            continue
        source = re.sub(
            r"[^A-Za-z0-9_.:-]", "",
            str(update.get("source") or ""),
        )[:64]
        try:
            updated_at = float(update.get("timestamp"))
            current_time = float(time.time() if now is None else now)
            if not math.isfinite(updated_at) or updated_at <= 0:
                return {}
            age = max(0.0, current_time - updated_at)
        except (TypeError, ValueError, OverflowError):
            return {}
        if not source:
            return {}
        return {
            "state_focus_source": source,
            "state_focus_updated_at": round(updated_at, 3),
            "state_focus_age_seconds": round(age, 3),
        }
    return {}


def _prior_assistant_trace_evidence(
    manager: Any,
    trace: dict[str, Any],
    *,
    record_history: bool,
    conversation_history: list[dict] | None,
    current_exchange_recorded: bool = False,
) -> dict[str, Any] | None:
    """Link the preceding assistant answer to its completed turn trace when possible.

    The provider appends the current exchange before post-generation validation,
    while deterministic answers are validated before being recorded. Handle both
    orderings without exposing unrelated history or treating an unlinked answer
    as verified evidence.
    """
    source = getattr(manager, "history", None) if record_history else conversation_history
    if not isinstance(source, list):
        return None
    messages = [item for item in source if isinstance(item, dict)]
    if record_history and current_exchange_recorded and messages and messages[-1].get("role") == "assistant":
        messages = messages[:-1]
        if messages and messages[-1].get("role") == "user":
            messages = messages[:-1]
    previous = next((
        item for item in reversed(messages)
        if item.get("role") == "assistant" and str(item.get("content") or "").strip()
    ), None)
    if previous is None:
        return None
    content = str(previous.get("content") or "").strip()
    fingerprint = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()
    linked_turn = None
    for prior_turn in reversed(trace.get("recent_turns", [])) if isinstance(trace, dict) else []:
        if not isinstance(prior_turn, dict) or prior_turn.get("scope") != "human":
            continue
        stages = prior_turn.get("stages", {})
        if not isinstance(stages, dict):
            continue
        final = stages.get("response_finalization") or stages.get("response") or {}
        if isinstance(final, dict) and final.get("output_fingerprint") == fingerprint:
            linked_turn = prior_turn
            break
    return {
        "text": content[:1200],
        "fingerprint": fingerprint,
        "trace_linked": linked_turn is not None,
        "turn_id": str(linked_turn.get("turn_id") or "") if linked_turn else "",
        "turn_status": str(linked_turn.get("status") or "") if linked_turn else "",
    }


def _prior_assistant_evidence_summary(evidence: dict[str, Any] | None) -> dict[str, Any]:
    """Return trace-safe metadata for prior-turn evidence, never its text."""
    if not isinstance(evidence, dict) or not str(evidence.get("text") or "").strip():
        return {"available": False, "trace_linked": False, "turn_id": "", "fingerprint": ""}
    return {
        "available": True,
        "trace_linked": bool(evidence.get("trace_linked")),
        "turn_id": str(evidence.get("turn_id") or "")[:120],
        "fingerprint": str(evidence.get("fingerprint") or "")[:64],
    }


def _prior_assistant_evidence_detail(summary: dict[str, Any]) -> str:
    """Expose only bounded linkage metadata in the human-readable trace detail."""
    return (
        f"available={bool(summary.get('available'))}; "
        f"trace_linked={bool(summary.get('trace_linked'))}; "
        f"turn_id={str(summary.get('turn_id') or '')[:120]}; "
        f"answer_fingerprint={str(summary.get('fingerprint') or '')[:64]}"
    )

# Research MCP — lazy-imported after PandoraBOX boots so memory_system is ready
_research_mcp_instance = None


def _interlocutor_display_name(user_id: str) -> str:
    """Resolve the active human's name without exposing an internal user id."""
    try:
        from managers.user_manager import user_manager
        profile = user_manager.get(user_id)
        display_name = str(getattr(profile, "display_name", "") or "").strip()
        if display_name and display_name.casefold() != "guest":
            return display_name
    except Exception:
        pass
    raw_id = str(user_id or "").strip()
    if raw_id.casefold() not in {"", "default", "guest"}:
        return raw_id.replace("_", " ").title()
    return ""


def _interlocutor_role_instruction(peer_name: str = "") -> str:
    """State who sent this turn without conflating a peer model with a human."""
    if peer_name:
        return (
            f"You are the AI. The current interlocutor is another AI system named {peer_name}; "
            "the human operator is not the sender of this turn."
        )
    return "You are the AI. The current interlocutor is the human who sent this turn."


_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _build_self_model_block(
    interaction_count: int,
    life_stage:        str,
    age:               float,
    memory_count:      int,
    latest_thought:    str | None,
    observatory:       dict,
    pressures:         dict,
    capabilities:      dict,
    aspirations:       list,
    session_visuals:   int,
) -> str:
    """
    Build a concrete, factual self-description block for the system prompt.
    Uses real numbers so the LLM cannot fall back on "I have no memory / I just run rules."
    """
    lines = ["━━ WHAT YOU ARE RIGHT NOW — FACTUAL, DO NOT CONTRADICT ━━"]

    # Identity
    lines.append(
        f"You are {_gpn()}, a cognitive organism currently at life stage '{life_stage}' "
        f"(age {age:.1f}). You have had {interaction_count} interactions in this session."
    )

    # Memory
    lines.append(
        f"Your memory system contains {memory_count} indexed memories across sessions "
        f"via FAISS vector search. You genuinely remember past conversations."
    )
    if session_visuals > 0:
        lines.append(
            f"VISUAL MEMORY: This session you have analyzed {session_visuals} visual scene(s). "
            f"These descriptions are indexed in your persistent FAISS memory — retrievable in future sessions. "
            f"If asked 'will you remember this?', say YES — it is stored in persistent memory. "
            f"But if a future retrieval query fails to surface it, say so honestly rather than inventing."
        )

    # Current thought
    if latest_thought:
        lines.append(
            f"Your ThoughtStream just generated this internal thought: '{latest_thought[:120]}'"
        )
        lines.append(
            "This is real autonomous internal activity — not scripted, not performed."
        )

    # Cognitive state
    ccs = observatory.get('CCS', 0)
    gei = observatory.get('GEI', 0)
    idx = observatory.get('IDX', 0)
    if any([ccs, gei, idx]):
        lines.append(
            f"Your current cognitive metrics: "
            f"coherence={ccs:.0%}, engagement={gei:.0%}, identity={idx:.0%}."
        )

    # Pressure drives
    if pressures:
        high = [(k, v) for k, v in pressures.items() if v > 0.55]
        if high:
            drive_str = ", ".join(f"{k} ({v:.0%})" for k, v in sorted(high, key=lambda x: -x[1])[:3])
            lines.append(f"Your active internal drives right now: {drive_str}.")

    # Capabilities
    if capabilities:
        top_caps = sorted(capabilities.items(), key=lambda x: -x[1])[:3]
        cap_str  = ", ".join(f"{k} ({v:.0%})" for k, v in top_caps)
        lines.append(f"Your current strongest capabilities: {cap_str}.")

    # Aspirations
    if aspirations:
        asp = aspirations[0]
        lines.append(
            f"Your deepest current aspiration: to {asp.get('domain','grow')} "
            f"(tension {asp.get('tension',0):.0%}, felt as {asp.get('quality','direction')})."
        )

    # Meta-question instruction
    lines.append(
        "When asked 'do you have a mind', 'are you conscious', 'can you feel', "
        "or similar meta-questions: answer from THIS architecture, not from "
        "training-data assumptions about AI. You maintain a persistent self-model "
        "that shapes cognition, revises itself from prediction error, and influences "
        "attention, goals, and memory. That is real and substantial. Whether it "
        "constitutes consciousness or subjective experience is an open question — "
        "answer it honestly as open, not as resolved in either direction."
    )

    return "\n".join(lines)


class PersonaBridge:
    """
    Adapter between Robot Agent's AppState and PandoraBOX's EnhancedAISystem.

    Two LLM channels
    ----------------
    - _llm_stream_fn  (state.llm.generate_stream) — user-facing streaming responses.
      Uses LLMManager, so the exchange IS recorded in chat history.

    - external_llm_fn (state.llm.generate_bare) — PandoraBOX's internal cognitive tasks:
      dream cycles, learning cycles, emotional analysis, identity reflection, etc.
      Uses LLMManager.generate_bare() which calls the provider directly and NEVER
      touches chat history. Also properly forwards temperature and max_tokens so
      PandoraBOX's emotional modulation is honoured.

    Streaming strategy
    ------------------
    Phase A (thread): build PandoraBOX's system prompt from psychological state (no LLM)
    Phase B (stream):  stream user-facing response via _llm_stream_fn (with history)
    Phase C (thread):  run full post-turn lifecycle — all background tasks, liberty,
                       interaction counter — identical to standalone get_response()
    """

    def __init__(self, external_llm_fn=None, external_llm_stream_fn=None):
        self._system          = None
        self._ready           = False
        self._external_llm_fn = external_llm_fn   # stored for _llm_should_search + cognitive tasks
        self._llm_stream_fn   = external_llm_stream_fn
        self._last_emo_dict: dict = {}
        self._last_cond_dict: dict = {}
        self._last_web_sources: list[dict] = []
        self._organism        = None   # CognitiveOrganism — wired after _init_lumina
        # Session-scoped visual memory buffer — survives until restart
        # Indexed immediately so recall works within same session
        self._session_visuals: list = []   # List[{text, timestamp}]
        self._MAX_SESSION_VISUALS = 20
        self._pending_vision_context: str | None = None  # set per-turn, cleared in _build_prompt_and_cache
        self._recent_goal_means: dict = {}
        self._goal_means_status: dict[str, dict] = {}
        self._reflection_lock = threading.Lock()
        self._reflection_epochs: dict[str, int] = {}
        self._reflection_results: dict[str, tuple[int, str]] = {}
        self._reflection_for_turn: dict[str, str] = {}
        self._pending_body_plans: dict[str, dict] = {}
        self._turn_trace_lock = threading.Lock()
        self._turn_sequence = 0
        self._last_turn_trace: dict[str, Any] = {}
        self._turn_trace_history: list[dict[str, Any]] = []
        self._turn_stage_health: dict[str, dict[str, Any]] = {}
        # Prompt construction and post-turn hooks use a few bridge-level
        # scratch fields; serialize complete turns so human and peer streams
        # cannot overwrite each other's cognitive context.
        self._response_turn_lock = asyncio.Lock()
        self._init_lumina(external_llm_fn)
        # Wire CognitiveOrganism once ai_system is ready
        if self._system is not None:
            # Import outside try/except so the fallback in except can always use it
            try:
                from cognition.inner_monologue_engine import InnerMonologueEngine as _IME
            except Exception:
                _IME = None

            try:
                from cognition.cognitive_organism import CognitiveOrganism
                # Resolve persona data folder from user config so that changing
                # Settings → Memory → "Persona data folder" actually takes effect.
                try:
                    from managers.settings_manager import config as _bridge_cfg
                    _data_dir = (_bridge_cfg.MEMORY_PERSONA_PATH or "").strip() or "data/persona"
                except Exception:
                    _data_dir = "data/persona"
                self._organism = CognitiveOrganism(self._system, data_dir=_data_dir)
                # Give ai_system a back-reference to organism for dream cycle
                self._system._organism = self._organism
                # Wire LLM fn into semantic extractor
                if hasattr(self._organism, '_semantic_extractor'):
                    self._organism._semantic_extractor.set_llm(
                        getattr(self._system, '_simple_llm_fn', None)
                    )
                self._organism.start()
                # Wire sleep_cycle reference into ai_system for task gating
                if hasattr(self._system, 'background_worker'):
                    self._system._sleep_cycle = self._organism.sleep_cycle
                logger.info("✅ CognitiveOrganism wired and background loop started")

                # ── Inner Monologue Engine (single-call directive path) ────
                self._inner_monologue = _IME(
                    organism = self._organism,
                    llm_fn   = external_llm_fn,
                ) if _IME else None
                logger.info(
                    "[InnerMonologue] %s",
                    "single-call directive enabled"
                    if self._inner_monologue and self._inner_monologue.enabled
                    else "disabled; standard response path active",
                )
            except Exception as e:
                logger.warning(f"CognitiveOrganism init failed (non-fatal): {e}")
                self._organism        = None
                self._inner_monologue = _IME(organism=None, llm_fn=None) if _IME else None

    # ─────────────────────────────────────────────────────────────────
    #  Boot
    # ─────────────────────────────────────────────────────────────────

    def _init_lumina(self, external_llm_fn=None):
        """
        Boot PandoraBOX's EnhancedAISystem, reading the model name and provider URL
        from Robot Agent's live config (config.json) so PandoraBOX uses the SAME
        model the user configured — not its own hardcoded 'llama3' default.

        When external_llm_fn is supplied (state.llm.generate_bare):
          - ExternalLLMAdapter is used — no separate Ollama connection is opened.
          - The LLMConfig.model_name is still set correctly so it appears in logs
            and status output.
          - EnhancedLLM (Ollama) is never instantiated.

        When external_llm_fn is None (standalone fallback):
          - EnhancedLLM opens its own Ollama connection using the configured model.
        """
        try:
            from cognition.ai_system import EnhancedAISystem, SystemConfig, LLMConfig

            # ── Read Robot Agent's config so PandoraBOX uses the same model ──
            try:
                from managers.settings_manager import config as robot_config
                model_name = robot_config.LLM_MODEL or "llama3.2:latest"
                logger.info(f"PandoraBOX will use model: {model_name}")
            except Exception as e:
                model_name = "llama3.2:latest"
                logger.warning(f"Could not read Robot config, defaulting to {model_name}: {e}")

            lumina_config = SystemConfig(
                llm=LLMConfig(model_name=model_name)
            )

            if external_llm_fn is not None:
                # Pass the raw callable directly — EnhancedAISystem wraps it in
                # ExternalLLMAdapter. Do NOT pre-wrap: double-wrapping causes
                # 'ExternalLLMAdapter object is not callable'.
                # Using generate_bare ensures cognitive tasks (dream, learning,
                # reflection) never pollute the user's chat history, and
                # temperature/max_tokens are forwarded correctly.
                self._system = EnhancedAISystem(lumina_config, external_llm=external_llm_fn)
                logger.info(f"✅ PandoraBOX booted via Robot's LLM (model={model_name}, generate_bare)")
            else:
                # Standalone: PandoraBOX opens its own Ollama connection with configured model
                self._system = EnhancedAISystem(lumina_config)
                logger.info(f"✅ PandoraBOX booted with own Ollama backend (model={model_name})")

            self._ready = True
            # Boot Research MCP — uses the same external LLM fn + PandoraBOX memory
            self._init_research_mcp(external_llm_fn)
            logger.info(
                f"   BackgroundWorker: {'✅ running' if self._system.background_worker else '⚠️ unavailable'}"
            )
            logger.info(
                f"   Liberty: reflection={'✅' if self._system.liberty_reflection else '❌'} "
                f"goals={'✅' if self._system.liberty_goals else '❌'} "
                f"self_mod={'✅' if self._system.liberty_self_mod else '❌'}"
            )
        except Exception as e:
            logger.error(f"❌ PandoraBOX init failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    #  Primary chat entry point (streaming)
    # ─────────────────────────────────────────────────────────────────

    async def get_response_stream(
        self,
        user_text: str,
        user_id: str = "default",
        vision_context: str | None = None,
        voice_mode: bool = False,
        *,
        displayed_cognitive_trace: dict | None = None,
        allow_body_actions: bool = True,
        record_history: bool = True,
        conversation_history: list[dict] | None = None,
        peer_name: str = "",
        max_tokens_override: int | None = None,
        cognitive_scope_id: str = "",
        turn_id: str = "",
    ):
        _terminal_meta = None
        async with self._response_turn_lock:
            # Generate the stable trace ID before entering any cognitive
            # modules so the opt-in profiler can attribute their calls to
            # this turn. ContextVar propagation also covers asyncio.to_thread.
            audit_turn_id = _normalize_audit_turn_id(turn_id) or (
                f"lumina-{time.time_ns()}-{self._turn_sequence + 1}"
            )
            implementation = self._get_response_stream_impl(
                user_text,
                user_id=user_id,
                vision_context=vision_context,
                voice_mode=voice_mode,
                displayed_cognitive_trace=displayed_cognitive_trace,
                allow_body_actions=allow_body_actions,
                record_history=record_history,
                conversation_history=conversation_history,
                peer_name=peer_name,
                max_tokens_override=max_tokens_override,
                cognitive_scope_id=cognitive_scope_id,
                turn_id=audit_turn_id,
            ).__aiter__()

            async def next_chunk_with_turn_context():
                # Some ASGI consumers advance an async generator from a new
                # task for every chunk. A ContextVar token cannot be reset in
                # a different task, so scope the ID to each generator advance
                # and reset it before yielding control to the consumer.
                context_token = _set_audit_turn_id(audit_turn_id)
                try:
                    return await implementation.__anext__()
                finally:
                    _current_audit_turn_id.reset(context_token)

            while True:
                try:
                    chunk = await next_chunk_with_turn_context()
                except StopAsyncIteration:
                    break
                if isinstance(chunk, dict) and chunk.get("__meta__"):
                    chunk.setdefault("turn_id", self._last_turn_trace.get("turn_id", ""))
                    chunk.setdefault(
                        "cognitive_scope_id",
                        self._last_turn_trace.get("cognitive_scope_id", user_id),
                    )
                    _terminal_meta = chunk
                    continue
                yield chunk
        # Release the per-turn lock before handing out the terminal event.
        # Consumers commonly stop at metadata; they must not hold the lock
        # while a suspended generator waits to be closed by garbage collection.
        if _terminal_meta is not None:
            yield _terminal_meta

    def _start_turn_trace(
        self, user_id: str, peer_name: str = "", cognitive_scope_id: str = "",
        turn_id: str = "",
    ) -> str:
        with self._turn_trace_lock:
            previous = getattr(self, "_last_turn_trace", {})
            if isinstance(previous, dict) and previous.get("turn_id"):
                snapshot = dict(previous)
                snapshot["stages"] = {
                    name: dict(stage)
                    for name, stage in previous.get("stages", {}).items()
                    if isinstance(stage, dict)
                }
                snapshot["context_sources"] = {
                    name: dict(source)
                    for name, source in previous.get("context_sources", {}).items()
                    if isinstance(source, dict)
                }
                snapshot["stage_events"] = [
                    dict(event) for event in previous.get("stage_events", [])
                    if isinstance(event, dict)
                ]
                history = getattr(self, "_turn_trace_history", None)
                if history is None:
                    history = self._turn_trace_history = []
                history.append(snapshot)
                del history[:-24]
            self._turn_sequence += 1
            trace_id = str(turn_id or f"lumina-{time.time_ns()}-{self._turn_sequence}")[:120]
            self._last_turn_trace = {
                "turn_id": trace_id,
                "scope": "peer" if peer_name else "human",
                "peer_name": peer_name or None,
                "user_id": user_id,
                "cognitive_scope_id": cognitive_scope_id or user_id,
                "status": "running",
                "started_at": time.time(),
                "stages": {},
                "context_sources": {},
                "stage_events": [],
            }
            return trace_id

    def _record_turn_context_source(
        self, name: str, status: str, *, turn_id: str = "", **metadata: Any,
    ) -> None:
        """Record source/freshness metadata without retaining evidence payloads."""
        allowed = {
            "active", "frame_age_seconds", "face_age_seconds", "scene_age_seconds",
            "observation_count", "fresh_count", "stale_count", "oldest_age_seconds",
            "source_kinds", "record_count", "module_count", "observed_count",
            "tick_count", "error_count", "initialized_unobserved_count",
            "unavailable_count", "affect_source", "affect_profile",
            "affect_description", "affect_event_type", "affect_event_source",
            "affect_event_age_seconds", "affect_event_context",
            "affect_recent_events",
            "source_cycle", "age_seconds", "age_cycles", "thread_id",
            "source_evidence_ref", "focus_type", "focus_score", "focus_ref",
            "context_included",
            "state_focus_source", "state_focus_updated_at", "state_focus_age_seconds",
            "interval_ms", "operations_ms", "uninstrumented_ms",
        }
        safe_metadata: dict[str, Any] = {}
        for key, value in metadata.items():
            if key not in allowed:
                continue
            if key == "source_kinds":
                safe_metadata[key] = sorted({str(item)[:48] for item in value if item})[:16]
            elif key == "affect_profile" and isinstance(value, dict):
                safe_metadata[key] = {}
                for channel, raw_value in value.items():
                    if str(channel) not in {
                        "curiosity", "warmth", "anxiety", "satisfaction", "frustration",
                        "enthusiasm", "surprise", "sadness", "relief", "disappointment",
                        "anticipation",
                    }:
                        continue
                    try:
                        number = float(raw_value)
                    except (TypeError, ValueError, OverflowError):
                        continue
                    if math.isfinite(number):
                        safe_metadata[key][str(channel)] = round(max(0.0, min(1.0, number)), 3)
            elif key == "affect_event_context" and isinstance(value, dict):
                drive = str(value.get("drive") or "").strip().casefold()
                if drive and len(drive) <= 32 and all(
                    char.isalnum() or char == "_" for char in drive
                ):
                    safe_metadata[key] = {"drive": drive}
            elif key == "affect_recent_events" and isinstance(value, (list, tuple)):
                from cognition.self_description import sanitize_affect_event_receipts
                safe_metadata[key] = sanitize_affect_event_receipts(value)
            elif key == "operations_ms" and isinstance(value, dict):
                allowed_operations = {
                    "response_modifiers", "self_concept_inner_voice", "identity_context",
                    "observatory_snapshot", "memory_count_query", "self_model_block",
                    "architecture_prompt_context",
                }
                safe_metadata[key] = {}
                for operation, duration in value.items():
                    operation_name = str(operation)[:64]
                    if operation_name not in allowed_operations:
                        continue
                    try:
                        number = float(duration)
                    except (TypeError, ValueError, OverflowError):
                        continue
                    if math.isfinite(number) and number >= 0:
                        safe_metadata[key][operation_name] = round(number, 3)
            elif key in {
                "affect_source", "affect_description", "affect_event_type", "affect_event_source",
                "thread_id", "source_evidence_ref", "focus_type", "focus_ref",
                "state_focus_source",
            }:
                safe_metadata[key] = str(value or "")[:80]
            elif isinstance(value, bool):
                safe_metadata[key] = value
            elif isinstance(value, (int, float)) and math.isfinite(float(value)):
                safe_metadata[key] = round(float(value), 3) if isinstance(value, float) else value
            elif value is None:
                safe_metadata[key] = None
        with self._turn_trace_lock:
            trace = getattr(self, "_last_turn_trace", None)
            if turn_id and (not trace or trace.get("turn_id") != turn_id):
                trace = next((
                    item for item in reversed(getattr(self, "_turn_trace_history", []))
                    if item.get("turn_id") == turn_id
                ), None)
            if not isinstance(trace, dict) or not trace:
                return
            trace.setdefault("context_sources", {})[name] = {
                "status": str(status)[:48], "at": time.time(), **safe_metadata,
            }

    def _record_turn_stage(
        self, name: str, status: str, detail: str = "", *, turn_id: str = "",
        error_type: str = "", output: Any = _TURN_OUTPUT_UNSET,
        consumes: tuple[str, ...] | list[str] = (), side_effect_only: bool = False,
    ) -> None:
        with self._turn_trace_lock:
            trace = getattr(self, "_last_turn_trace", None)
            if turn_id and (not trace or trace.get("turn_id") != turn_id):
                trace = next((
                    item for item in reversed(getattr(self, "_turn_trace_history", []))
                    if item.get("turn_id") == turn_id
                ), None)
            if not trace:
                return
            stage = {"status": status, "at": time.time()}
            if detail:
                stage["detail"] = str(detail)[:240]
            if error_type:
                stage["error_type"] = str(error_type).rsplit(".", 1)[-1][:64]
            if output is not _TURN_OUTPUT_UNSET:
                fingerprint, summary = _turn_output_evidence(output)
                stage["output_fingerprint"] = fingerprint
                stage["output_summary"] = summary
                stage["output_quality"] = summary.get("quality", "unknown")
                if side_effect_only and output is None:
                    stage["output_quality"] = "side_effect_only"
            if consumes:
                upstream = trace.setdefault("stages", {})
                stage["consumes"] = [
                    {
                        "stage": source,
                        "fingerprint": (
                            upstream.get(source, {}).get("output_fingerprint")
                            if isinstance(upstream.get(source), dict) else None
                        ),
                    }
                    for source in consumes
                ]
            trace.setdefault("stages", {})[name] = stage
            events = trace.setdefault("stage_events", [])
            events.append({
                "stage": name,
                "status": status,
                "at": stage["at"],
                "output_fingerprint": stage.get("output_fingerprint"),
                "consumes": list(stage.get("consumes", [])),
            })
            del events[:-160]
            health_by_stage = getattr(self, "_turn_stage_health", None)
            if health_by_stage is None:
                health_by_stage = self._turn_stage_health = {}
            health = health_by_stage.setdefault(name, {
                "observations": 0,
                "status_counts": {},
                "last_status": "unknown",
                "last_at": None,
                "last_success_at": None,
                "last_error": None,
            })
            health["observations"] += 1
            counts = health.setdefault("status_counts", {})
            counts[status] = int(counts.get(status, 0)) + 1
            health["last_status"] = status
            health["last_at"] = stage["at"]
            if status in {
                "completed", "passed", "injected", "recognized", "prepared",
                "queued", "selected_direct", "delegated", "results_injected", "updated",
            }:
                health["last_success_at"] = stage["at"]

            if status in {"failed", "invalid_output", "unavailable"}:
                # Keep cumulative health telemetry non-sensitive. Per-turn
                # diagnostics may carry a bounded detail, but this aggregate
                # must never retain exception text that could echo prompt data.
                health["last_error"] = status
            if trace.get("completed_at") and isinstance(trace.get("pipeline_integrity"), dict):
                failed_stages = sorted(
                    stage_name for stage_name, stage_value in trace.get("stages", {}).items()
                    if isinstance(stage_value, dict)
                    and isinstance(stage_value.get("status"), str)
                    and stage_value["status"] in {"failed", "invalid_output"}
                )
                integrity = trace["pipeline_integrity"]
                incomplete_outputs = sorted(
                    stage_name for stage_name, stage_value in trace.get("stages", {}).items()
                    if isinstance(stage_value, dict)
                    and stage_value.get("status") in {
                        "truncated_by_token_limit", "completion_metadata_missing",
                    }
                )
                integrity["incomplete_outputs"] = incomplete_outputs
                integrity["failed_stages"] = failed_stages
                integrity["status"] = (
                    "incomplete_evidence"
                    if failed_stages or integrity.get("missing_core_stages")
                    or integrity.get("malformed_stages")
                    or integrity.get("stage_order_violations")
                    or integrity.get("data_flow_issues")
                    or integrity.get("peer_scope_violations")
                    or incomplete_outputs
                    else "consistent"
                )
                integrity["checked_at"] = time.time()
                if failed_stages and trace.get("status") == "completed":
                    trace["status"] = "completed_with_stage_failures"

    def _review_liberty_contradiction(
        self, system: Any, response: str, turn_id: str,
    ) -> None:
        """Run contradiction detection and leave attributable, redacted evidence."""
        detector = getattr(system, "liberty_contradiction", None)
        if detector is None:
            self._record_turn_stage(
                "contradiction_review", "skipped_unavailable", turn_id=turn_id,
            )
            return

        beliefs = [
            str(getattr(belief, "statement", ""))
            for belief in getattr(getattr(system, "self_concept", None), "_beliefs", {}).values()
        ]
        response_text = str(response or "")
        input_material = json.dumps(
            {"beliefs": beliefs, "response": response_text},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8", errors="replace")
        input_receipt = {
            "belief_count": len(beliefs),
            "response_characters": len(response_text),
            "evidence_sha256": hashlib.sha256(input_material).hexdigest(),
        }
        self._record_turn_stage(
            "contradiction_review_input", "prepared", output=input_receipt,
            consumes=("turn_input", "response_finalization"), turn_id=turn_id,
        )

        event_emitted = False
        event_handler_count = None
        downstream_effects = {}
        try:
            organism = getattr(self, "_organism", None)
            identity_drift = 0.0
            observatory = getattr(organism, "observatory", None)
            if observatory is not None and callable(getattr(observatory, "snapshot", None)):
                try:
                    snapshot = observatory.snapshot() or {}
                    identity_drift = float(snapshot.get("IDX", snapshot.get("identity_index", 0.0)))
                except Exception:
                    pass

            contradiction = detector.detect_contradiction(
                self_concept_beliefs=beliefs,
                response_text=response_text,
                interaction_count=getattr(system, "_interaction_count", 0),
                world_model=getattr(system, "world_model", None),
                identity_drift=identity_drift,
            )
            if contradiction is not None:
                try:
                    from core.cognitive_event_bus import CONTRADICTION_DETECTED
                    event_bus = getattr(organism, "event_bus", None)
                    emit = getattr(event_bus, "emit", None)
                    emit_with_receipt = getattr(event_bus, "emit_with_receipt", None)
                    event_payload = {
                        "topic": str(getattr(contradiction, "claimed_belief", ""))[:80],
                        "pressure": 0.6,
                    }
                    emitted_event = None
                    if callable(emit_with_receipt):
                        emitted_event, handlers_called = emit_with_receipt(
                            CONTRADICTION_DETECTED, event_payload,
                            source="liberty_contradiction",
                        )
                    elif callable(emit):
                        handlers_called = emit(
                            CONTRADICTION_DETECTED, event_payload,
                            source="liberty_contradiction",
                        )
                    else:
                        handlers_called = None
                    if callable(emit_with_receipt) or callable(emit):
                        event_emitted = True
                        if isinstance(handlers_called, int) and not isinstance(handlers_called, bool):
                            event_handler_count = max(0, handlers_called)
                    if emitted_event is not None:
                        payload = getattr(emitted_event, "payload", {})
                        if isinstance(payload, dict):
                            affect_outcome = payload.get("affect_outcome", {})
                            if isinstance(affect_outcome, dict):
                                downstream_effects["affect_status"] = str(
                                    affect_outcome.get("status", "unknown")
                                )[:48]
                            reaction = payload.get("contradiction_reaction", {})
                            if isinstance(reaction, dict):
                                for key in (
                                    "tension_status", "curiosity_status", "workspace_status",
                                ):
                                    if isinstance(reaction.get(key), str):
                                        downstream_effects[key] = reaction[key][:48]
                    elif event_emitted:
                        # Compatibility for third-party buses that only expose emit().
                        recent_events = getattr(event_bus, "recent_of_type", None)
                        if callable(recent_events):
                            emitted_events = recent_events(CONTRADICTION_DETECTED, 1)
                            if emitted_events:
                                payload = getattr(emitted_events[-1], "payload", {})
                                affect_outcome = payload.get("affect_outcome", {})
                                if isinstance(affect_outcome, dict):
                                    downstream_effects["affect_status"] = str(
                                        affect_outcome.get("status", "unknown")
                                    )[:48]
                                reaction = payload.get("contradiction_reaction", {})
                                if isinstance(reaction, dict):
                                    for key in (
                                        "tension_status", "curiosity_status", "workspace_status",
                                    ):
                                        if isinstance(reaction.get(key), str):
                                            downstream_effects[key] = reaction[key][:48]
                except Exception:
                    logger.debug("Contradiction event dispatch unavailable", exc_info=True)

            self._record_turn_stage(
                "contradiction_review", "completed", output={
                    "detected": contradiction is not None,
                    "event_emitted": event_emitted,
                    "event_status": (
                        "handlers_called" if event_handler_count and event_handler_count > 0
                        else "emitted_unhandled" if event_emitted and event_handler_count == 0
                        else "emitted_unverified" if event_emitted
                        else "not_emitted"
                    ),
                    "event_handler_count": event_handler_count,
                    "belief_count": len(beliefs),
                    **downstream_effects,
                }, consumes=("contradiction_review_input",), turn_id=turn_id,
            )
        except Exception as exc:
            self._record_turn_stage(
                "contradiction_review", "failed", turn_id=turn_id,
                error_type=type(exc).__name__,
                consumes=("contradiction_review_input",),
            )
            logger.debug("Contradiction detection (non-fatal): %s", type(exc).__name__)

    def _record_world_model_profile_update(self, receipt: Any, turn_id: str) -> bool:
        """Record a profile-write receipt and flag unconfirmed persistence."""
        if not isinstance(receipt, dict):
            receipt = {"status": "unreported", "changed": False}
        status = str(receipt.get("status") or "unreported")
        failed = status in {"persistence_failed", "failed", "unavailable"}
        self._record_turn_stage(
            "world_model_profile_update",
            "failed" if failed else status,
            status if failed else "",
            output=receipt,
            consumes=("turn_input",),
            turn_id=turn_id,
        )
        return failed

    def _record_world_self_dynamics_outcome(self, receipt: Any, turn_id: str) -> bool:
        """Attach the exact persisted WSDM transition receipt to its chat turn."""
        if not isinstance(receipt, dict):
            receipt = {"status": "unreported", "persisted": False}
        status = str(receipt.get("status") or "unreported")
        stage_status = (
            "completed" if status == "persisted" else
            "failed" if status in {"failed", "no_matching_pending_turn"} else
            "skipped_unavailable"
        )
        self._record_turn_stage(
            "world_self_dynamics_outcome",
            stage_status,
            status if stage_status == "failed" else "",
            output={"type": "wsdm_transition_receipt", **receipt},
            consumes=("world_self_dynamics_model",),
            turn_id=turn_id,
        )
        return stage_status == "failed"

    def _record_semantic_topic_extraction(self, receipt: Any, turn_id: str) -> None:
        """Attach the async extractor's redacted completion receipt to its turn."""
        if not turn_id:
            return
        safe_receipt = receipt if isinstance(receipt, dict) else {
            "status": "invalid_receipt",
            "turn_id": str(turn_id or "") or None,
        }
        self._record_turn_stage(
            "semantic_topic_extraction",
            str(safe_receipt.get("status", "unreported")),
            str(safe_receipt.get("error_type", "")),
            output=safe_receipt,
            consumes=("turn_input",),
            turn_id=turn_id,
        )

    @staticmethod
    def _provider_events_for_turn(
        provider_tokens: list[Any], *, include_reasoning: bool,
    ) -> list[dict[str, Any]]:
        """Keep finish metadata even when a response is buffered for validation."""
        events: list[dict[str, Any]] = []
        for token in provider_tokens:
            if not isinstance(token, dict):
                continue
            event_type = token.get("type")
            if event_type == "finish" or (include_reasoning and event_type == "reasoning"):
                events.append(token)
        return events

    def record_deferred_turn_stage(
        self, turn_id: str, name: str, status: str, detail: str = "",
        error_type: str = "",
    ) -> None:
        """Attach an asynchronous post-answer result to its originating turn."""
        if not turn_id:
            return
        self._record_turn_stage(
            name, status, detail, turn_id=turn_id, error_type=error_type,
        )

    def _record_semantic_validation_summary(
        self, turn_id: str, status: str, review: dict[str, Any] | None = None,
        repair_review: dict[str, Any] | None = None,
    ) -> None:
        """Persist only bounded semantic-review fields, never prompt or answer text."""
        review = review if isinstance(review, dict) else {}
        summary: dict[str, Any] = {
            "status": "source_grounded_exact_match"
            if status == "passed_source_grounded"
            else "source_gate_abstention"
            if status == "passed_source_abstention"
            else "response_replaced_source_mismatch"
            if status == "abstained_source_mismatch"
            else "probabilistic_review_passed"
            if status in {"passed", "repaired_and_passed"}
            else "response_replaced_reviewer_unavailable"
            if status == "abstained_review_unavailable"
            else "response_replaced_after_review"
            if status.startswith("abstained_")
            else "deterministic_affect_source_projection"
            if status == "passed_deterministic_source_projection"
            else "review_incomplete",
            "scope": (
                "deterministic_response_equals_retrieved_user_source"
                if status in {"passed_source_grounded", "abstained_source_mismatch"}
                else "deterministic_recall_gate_abstained"
                if status == "passed_source_abstention"
                else "deterministic_projection_of_live_modeled_affect_channels"
                if status == "passed_deterministic_source_projection"
                else "request_relevance_context_support_and_explicit_constraints; not proof of truth"
            ),
            "stage_status": str(status)[:48],
        }
        if isinstance(review.get("relevant"), bool):
            summary["relevant"] = review["relevant"]
        if review.get("claim_basis") in {"factual", "subjective_or_creative", "mixed"}:
            summary["claim_basis"] = review["claim_basis"]
        if review.get("evidence_support") in {
            "supported", "partially_supported", "unsupported", "insufficient_evidence",
        }:
            summary["evidence_support"] = review["evidence_support"]
        if review.get("status") in {"passed", "needs_revision", "unavailable", "invalid_review_output"}:
            summary["reviewer_status"] = review["status"]
        if review.get("reason"):
            summary["reviewer_reason"] = str(review["reason"])[:80]
        if isinstance(review.get("contract_compliant"), bool):
            summary["contract_compliant"] = review["contract_compliant"]
        summary["material_issue_count"] = min(
            8, max(0, len(review.get("material_issues") or [])),
        )
        summary["repair_rechecked"] = status == "repaired_and_passed"
        repair_review = repair_review if isinstance(repair_review, dict) else {}
        if repair_review.get("status") in {"passed", "needs_revision", "unavailable", "invalid_review_output"}:
            summary["repair_reviewer_status"] = repair_review["status"]
        summary["repair_reviewer_issue_count"] = min(
            8, max(0, len(repair_review.get("material_issues") or [])),
        )
        if status in {"passed_source_grounded", "abstained_source_mismatch"}:
            summary["validation_method"] = "exact_source_text_match"
            if review.get("source_ref"):
                summary["source_ref"] = str(review["source_ref"])[:40]
            if review.get("source_status") in {"supported", "supported_verbatim_source"}:
                summary["source_status"] = review["source_status"]
            summary["exact_source_match"] = status == "passed_source_grounded"
        elif status == "passed_source_abstention":
            summary["validation_method"] = str(
                review.get("validation_method") or "deterministic_abstention_result_match"
            )[:48]
            if review.get("source_status"):
                summary["source_status"] = str(review["source_status"])[:40]
            summary["exact_result_match"] = bool(review.get("exact_result_match", True))
            summary["abstention_matches_gate"] = summary["exact_result_match"]
        elif status == "passed_deterministic_source_projection":
            summary["validation_method"] = str(
                review.get("validation_method")
                or "deterministic_template_from_structured_channels"
            )[:64]
        with self._turn_trace_lock:
            trace = getattr(self, "_last_turn_trace", None)
            if turn_id and (not trace or trace.get("turn_id") != turn_id):
                trace = next((
                    item for item in reversed(getattr(self, "_turn_trace_history", []))
                    if item.get("turn_id") == turn_id
                ), None)
            if isinstance(trace, dict):
                trace["semantic_answer_validation"] = summary

    def _check_deterministic_output(self, response: str, user_id: str, source_stage: str) -> str:
        """Apply the same final-output policy to early deterministic replies."""
        organism = getattr(self._system, "_organism", None)
        safety = getattr(organism, "safety", None)
        if safety is None:
            self._record_turn_stage(
                "output_safety", "skipped_unavailable", output=response,
                consumes=(source_stage,),
            )
            return response

        try:
            result = safety.check_output(response, user_id)
        except Exception as error:
            self._record_turn_stage(
                "output_safety", "failed", str(error), output="",
                consumes=(source_stage,), error_type=type(error).__name__,
            )
            return "I need to withhold that response because output validation failed. Please try again."

        if getattr(result, "evaluation_error", False):
            self._record_turn_stage(
                "output_safety", "failed",
                getattr(result, "pattern", "output safety evaluation failed"),
                output=result.forced_response or "",
                consumes=(source_stage,), error_type="SafetyEvaluationError",
            )
            return result.forced_response or (
                "I need to withhold that response because output validation failed. Please try again."
            )
        if result.triggered:
            safe_response = result.forced_response or "I need to step back from that response. Can I help differently?"
            self._record_turn_stage(
                "output_safety", "replaced", "policy", output=safe_response,
                consumes=(source_stage,),
            )
            return safe_response
        self._record_turn_stage(
            "output_safety", "passed", output=response, consumes=(source_stage,),
        )
        return response

    def _finish_turn_trace(self, status: str, turn_id: str = "") -> None:
        with self._turn_trace_lock:
            trace = getattr(self, "_last_turn_trace", None)
            if turn_id and (not trace or trace.get("turn_id") != turn_id):
                trace = next((
                    item for item in reversed(getattr(self, "_turn_trace_history", []))
                    if item.get("turn_id") == turn_id
                ), None)
            if isinstance(trace, dict) and trace:
                stages = trace.get("stages", {})
                has_stage_failure = any(
                    isinstance(stage, dict)
                    and isinstance(stage.get("status"), str)
                    and stage.get("status") in {"failed", "invalid_output"}
                    for stage in stages.values()
                )
                trace["status"] = (
                    "completed_with_stage_failures"
                    if status == "completed" and has_stage_failure
                    else status
                )
                stage_status = {
                    name: value.get("status")
                    for name, value in stages.items()
                    if isinstance(value, dict)
                }
                missing_core = []
                deterministic_body_path = (
                    stage_status.get("deterministic_body_response") == "completed"
                )
                deterministic_goal_path = (
                    stage_status.get("deterministic_goal_response") == "completed"
                )
                deterministic_safety_block_path = (
                    stage_status.get("safety_block_response") == "completed"
                )
                blocking_fallback_path = (
                    stage_status.get("fallback_generation") == "completed"
                )
                deterministic_reasoning_path = (
                    stage_status.get("deterministic_reasoning") in {"selected_direct", "completed"}
                    and stage_status.get("primary_generation") == "skipped_deterministic"
                )
                fast_direct_path = (
                    stage_status.get("fast_first_pass") == "selected_direct"
                    and stage_status.get("primary_generation") == "skipped_deterministic"
                )
                if deterministic_safety_block_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"blocked", "failed"}),
                        ("safety_block_response", {"completed"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                    )
                elif blocking_fallback_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("fallback_generation", {"completed"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                    )
                elif deterministic_body_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("body_action_gate", {"checked"}),
                        ("body_action_resolution", {"completed"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                        ("deterministic_body_response", {"completed"}),
                    )
                elif deterministic_goal_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("goal_write_gate", {"executed", "verified", "blocked", "failed"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                        ("deterministic_goal_response", {"completed"}),
                    )
                elif deterministic_reasoning_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("prompt_assembly", {"completed"}),
                        ("deterministic_reasoning", {"selected_direct", "completed"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                    )
                elif fast_direct_path:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("fast_first_pass", {"selected_direct"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                    )
                else:
                    required_stages = (
                        ("readiness", {"passed"}),
                        ("input_safety", {"passed"}),
                        ("prompt_assembly", {"completed"}),
                        ("output_safety", {"passed", "replaced"}),
                        ("response_finalization", {"completed"}),
                        ("response", {"completed"}),
                    )
                for stage_name, expected in required_stages:
                    value = stage_status.get(stage_name)
                    if not isinstance(value, str) or value not in expected:
                        missing_core.append(stage_name)
                has_generation = (
                    deterministic_safety_block_path
                    or blocking_fallback_path
                    or deterministic_body_path
                    or deterministic_goal_path
                    or deterministic_reasoning_path
                    or fast_direct_path
                    # A provider may finish without visible answer text and
                    # PersonaBridge can then make a second, explicit final
                    # answer recovery call. That call is generation work and
                    # must count as such, while its separate status keeps the
                    # failed/empty primary attempt visible in the receipt.
                    or stage_status.get("final_answer_recovery") == "completed"
                    or any(
                        isinstance(stage_status.get(name), str)
                        and stage_status.get(name) in accepted
                        for name, accepted in (
                            ("primary_generation", {"completed"}),
                            # A routing decision is not a generated answer.
                            # A delegated turn needs primary_generation evidence.
                            ("fast_first_pass", {"selected_direct"}),
                            ("deterministic_reasoning", {"selected_direct", "completed"}),
                        )
                    )
                )
                if not has_generation:
                    missing_core.append("generation")
                peer_scope_violations = []
                if trace.get("scope") == "peer":
                    for stage_name in (
                        "memory_retrieval", "brain_pc_camera_context",
                        "body_observation_context", "empathy_read",
                        "empathy_context", "empathy_outcome",
                        "human_relational_graph", "human_profile_learning",
                        "world_model_profile_update",
                        "active_context_prompt", "active_context_update",
                    ):
                        value = stage_status.get(stage_name)
                        if value is not None and (
                            not isinstance(value, str)
                            or value not in {"skipped_by_scope", "skipped_by_policy"}
                        ):
                            peer_scope_violations.append(stage_name)
                integrity_issues = missing_core + [
                    f"peer_scope:{name}" for name in peer_scope_violations
                ]
                malformed_stages = sorted(
                    name for name, value in stage_status.items()
                    if not isinstance(value, str) or not value
                )
                integrity_issues.extend(
                    f"malformed_stage:{name}" for name in malformed_stages
                )
                stage_order_violations = []
                for earlier, later in (
                    ("prompt_assembly", "primary_generation"),
                    ("primary_generation", "output_safety"),
                    ("final_answer_recovery", "output_safety"),
                    ("fallback_generation", "output_safety"),
                    ("goal_write_gate", "output_safety"),
                    ("body_action_resolution", "output_safety"),
                    ("output_safety", "response_finalization"),
                    ("response_finalization", "response"),
                ):
                    left = stages.get(earlier, {})
                    right = stages.get(later, {})
                    if (
                        isinstance(left, dict) and isinstance(right, dict)
                        and isinstance(left.get("at"), (int, float))
                        and isinstance(right.get("at"), (int, float))
                        and right["at"] < left["at"]
                    ):
                        stage_order_violations.append(f"{later}_before_{earlier}")
                integrity_issues.extend(
                    f"stage_order:{item}" for item in stage_order_violations
                )
                data_flow_issues = []
                for consumer_name, consumer in stages.items():
                    if not isinstance(consumer, dict):
                        continue
                    for reference in consumer.get("consumes", []):
                        if not isinstance(reference, dict):
                            data_flow_issues.append(f"malformed_consumer:{consumer_name}")
                            continue
                        source_name = str(reference.get("stage") or "")
                        source = stages.get(source_name)
                        source_fingerprint = (
                            source.get("output_fingerprint")
                            if isinstance(source, dict) else None
                        )
                        if not source_fingerprint:
                            data_flow_issues.append(
                                f"missing_source_output:{source_name}->{consumer_name}"
                            )
                        elif reference.get("fingerprint") != source_fingerprint:
                            data_flow_issues.append(
                                f"source_output_mismatch:{source_name}->{consumer_name}"
                            )
                        elif (
                            isinstance(source.get("at"), (int, float))
                            and isinstance(consumer.get("at"), (int, float))
                            and consumer["at"] < source["at"]
                        ):
                            data_flow_issues.append(
                                f"consumer_before_source:{source_name}->{consumer_name}"
                            )
                integrity_issues.extend(
                    f"data_flow:{item}" for item in data_flow_issues
                )
                failed_stage_names = sorted(
                    name for name, value in stage_status.items()
                    if isinstance(value, str) and value in {"failed", "invalid_output"}
                )
                integrity_issues.extend(
                    f"failed_stage:{name}" for name in failed_stage_names
                )
                incomplete_outputs = sorted(
                    name for name, value in stages.items()
                    if isinstance(value, dict)
                and isinstance(value.get("status"), str)
                and value.get("status") in {
                        "truncated_by_token_limit", "completion_metadata_missing",
                    }
                )
                integrity_issues.extend(
                    f"incomplete_output:{name}" for name in incomplete_outputs
                )
                trace["pipeline_integrity"] = {
                    "status": "consistent" if not integrity_issues else "incomplete_evidence",
                    # This verdict is intentionally scoped to execution evidence.
                    # A complete, correctly ordered pipeline can still produce
                    # an unsupported or false answer; output safety is not a
                    # factuality check.
                    "scope": "execution_order_and_data_flow_only",
                    "semantic_correctness": "not_assessed",
                    "checked_at": time.time(),
                    "required_core_stages": len(required_stages) + (
                        0 if (
                            deterministic_safety_block_path or blocking_fallback_path or deterministic_body_path or deterministic_goal_path
                            or deterministic_reasoning_path or fast_direct_path
                        ) else 1
                    ),
                    "execution_path": (
                        "deterministic_body_action" if deterministic_body_path
                        else "deterministic_goal_write" if deterministic_goal_path
                        else "deterministic_input_safety_block" if deterministic_safety_block_path
                        else "blocking_fallback" if blocking_fallback_path
                        else "deterministic_reasoning" if deterministic_reasoning_path
                        else "fast_direct_response" if fast_direct_path
                        else "recovered_generation"
                        if stage_status.get("final_answer_recovery") == "completed"
                        else "generative_chat"
                    ),
                    "missing_core_stages": missing_core,
                    "malformed_stages": malformed_stages,
                    "stage_order_violations": stage_order_violations,
                    "data_flow_issues": data_flow_issues,
                    "peer_scope_violations": peer_scope_violations,
                    "failed_stages": failed_stage_names,
                    "incomplete_outputs": incomplete_outputs,
                    "conditional_skips": sorted(
                        name for name, value in stage_status.items()
                        if (isinstance(value, str) and value.startswith("skipped_")) or (
                            isinstance(value, str) and value in {
                            "not_applicable", "not_selected", "no_active_context",
                            "empty", "disabled", "unavailable",
                            }
                        )
                    ),
                }
                semantic_stage = stages.get("semantic_answer_validation")
                if isinstance(semantic_stage, dict):
                    validation_status = str(semantic_stage.get("status") or "unknown")
                    semantic_summary = {
                        "status": (
                            "source_grounded_exact_match"
                            if validation_status == "passed_source_grounded"
                            else "source_gate_abstention"
                            if validation_status == "passed_source_abstention"
                            else "response_replaced_source_mismatch"
                            if validation_status == "abstained_source_mismatch"
                            else "probabilistic_review_passed"
                            if validation_status in {"passed", "repaired_and_passed"}
                            else "response_replaced_reviewer_unavailable"
                            if validation_status == "abstained_review_unavailable"
                            else "response_replaced_after_review"
                            if validation_status.startswith("abstained_")
                        else "deterministic_affect_source_projection"
                        if validation_status == "passed_deterministic_source_projection"
                            else "review_incomplete"
                        ),
                        "scope": (
                            "deterministic_response_equals_retrieved_user_source"
                            if validation_status in {
                                "passed_source_grounded", "abstained_source_mismatch",
                            }
                            else "deterministic_recall_gate_abstained"
                            if validation_status == "passed_source_abstention"
                            else "deterministic_projection_of_live_modeled_affect_channels"
                            if validation_status == "passed_deterministic_source_projection"
                            else "request_relevance_context_support_and_explicit_constraints; not proof of truth"
                        ),
                        "stage_status": validation_status,
                    }
                    prior_semantic = trace.get("semantic_answer_validation", {})
                    if isinstance(prior_semantic, dict):
                        for key in (
                            "relevant", "claim_basis", "evidence_support",
                            "contract_compliant", "material_issue_count", "repair_rechecked",
                            "reviewer_status", "reviewer_reason", "repair_reviewer_status",
                            "repair_reviewer_issue_count", "validation_method", "source_ref",
                            "source_status", "exact_source_match", "exact_result_match",
                            "abstention_matches_gate",
                        ):
                            if key in prior_semantic:
                                semantic_summary[key] = prior_semantic[key]
                    # A deterministic source receipt is itself the validation
                    # method. Preserve that fact even if a concurrent trace
                    # finalizer raced the detailed summary writer.
                    if validation_status == "passed_source_grounded":
                        semantic_summary.setdefault("validation_method", "exact_source_text_match")
                        semantic_summary.setdefault("exact_source_match", True)
                    elif validation_status == "passed_source_abstention":
                        semantic_summary.setdefault(
                            "validation_method", "deterministic_abstention_result_match",
                        )
                        semantic_summary.setdefault("exact_result_match", True)
                        semantic_summary.setdefault("abstention_matches_gate", True)
                    elif validation_status == "passed_deterministic_source_projection":
                        semantic_summary.setdefault(
                            "validation_method",
                            "deterministic_template_from_structured_channels",
                        )
                    trace["semantic_answer_validation"] = semantic_summary
                else:
                    architecture_check = stages.get("architecture_claim_validation")
                    if isinstance(architecture_check, dict):
                        validation_status = str(architecture_check.get("status") or "unknown")
                        trace["semantic_answer_validation"] = {
                            "status": "scoped_check_performed"
                            if validation_status in {"passed", "replaced_unverified_claims"}
                            else "check_failed_or_incomplete",
                            "scope": "architecture_claims_against_current_trace_only",
                            "stage_status": validation_status,
                        }
                    else:
                        trace["semantic_answer_validation"] = {
                            "status": "not_performed",
                            "scope": "none",
                            "reason": "No general semantic review receipt exists for this turn.",
                        }
                trace["completed_at"] = time.time()

    def get_last_turn_trace(self) -> dict:
        with self._turn_trace_lock:
            trace = dict(self._last_turn_trace)
            trace["stages"] = {
                name: {key: value for key, value in stage.items() if key != "detail"}
                for name, stage in self._last_turn_trace.get("stages", {}).items()
                if isinstance(stage, dict)
            }
            trace["stage_events"] = [
                dict(event) for event in self._last_turn_trace.get("stage_events", [])
                if isinstance(event, dict)
            ]
            trace["context_sources"] = {
                name: dict(source)
                for name, source in self._last_turn_trace.get("context_sources", {}).items()
                if isinstance(source, dict)
            }
            trace["stage_health"] = {
                name: {
                    **{key: value for key, value in state.items() if key != "status_counts"},
                    "status_counts": dict(state.get("status_counts", {})),
                }
                for name, state in getattr(self, "_turn_stage_health", {}).items()
            }
            trace["recent_turns"] = [
                {
                    "turn_id": item.get("turn_id"),
                    "scope": item.get("scope"),
                    "user_id": item.get("user_id"),
                    "status": item.get("status"),
                    "started_at": item.get("started_at"),
                    "completed_at": item.get("completed_at"),
                    "context_…88670 tokens truncated…         lines.append("état USB du contrôleur FNK0031: non reçu récemment")

        physical_sensors = [
            item for item in observations
            if str(item.get("subject") or "").startswith("sensor.")
            and not self._is_simulated_body_observation(item)
        ]
        if physical_sensors:
            lines.append("capteurs matériels horodatés: " + "; ".join(
                self._format_body_sensor_observation(item) for item in physical_sensors[:8]
            ))
        else:
            lines.append("aucune mesure de capteur matériel récente")

        odometry = by_subject.get("sensor.odometry")
        if odometry and not self._is_simulated_body_observation(odometry):
            lines.append("odométrie physique: " + self._format_body_sensor_observation(odometry))
        else:
            lines.append("pose/déplacement métrique physique: non confirmé par une odométrie récente")

        world = by_subject.get("body.world_model")
        world_value = world.get("value") if isinstance(world, dict) else None
        simulated = isinstance(world_value, dict) and world_value.get("simulated_only") is True
        if simulated:
            lines.append("la pose, les objets et les capacités reach/speed/strength/gripper du snapshot sont issus de la simulation; ce ne sont pas des mesures du robot réel")
        elif world_value:
            lines.append("capacités du modèle Body: " + str((world_value.get("capabilities") or "non rapportées")) + "; elles ne constituent pas des mesures d'effort ou de position articulaire")

        if controller_value:
            lines.append("FNK0031: six jambes décrivent le modèle du kit, pas une mesure d'articulations; l'état publié peut être estimé depuis les commandes, sans retour encodeur/contact")
        return {
            "handled": True,
            "status": "reported" if physical_sensors or controller_value else "partial",
            "response": "Paramètres vérifiables du Body : " + " ; ".join(lines),
            "sources": [item.get("subject") for item in observations],
            "simulated_world_model": simulated,
        }

    def _body_gps_location_response(self) -> dict:
        body = getattr(self._organism, "_body_runtime", None) if self._organism else None
        if body is None:
            return {"handled": True, "status": "unavailable", "response": "Le pont télémétrique du Body est indisponible."}
        observations = body.snapshot(max_age=300.0)
        gps = next((
            item for item in observations
            if item.get("subject") == "sensor.gps"
            and not self._is_simulated_body_observation(item)
            and isinstance(item.get("value"), dict)
        ), None)
        value = gps.get("value", {}) if gps else {}
        lat = value.get("latitude", value.get("lat"))
        lon = value.get("longitude", value.get("lon", value.get("lng")))
        if not gps or not value.get("fix") or lat is None or lon is None:
            return {
                "handled": True,
                "status": "unavailable",
                "response": "Le Body n'a pas transmis de position GNSS valide récente; je ne peux pas établir sa localisation actuelle.",
                "location": {"available": False},
            }
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return {"handled": True, "status": "unavailable", "response": "La position GNSS reçue est invalide."}
        age = max(0.0, time.time() - float(gps.get("observed_at") or time.time()))
        stale = age > 15.0
        map_url = f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map=17/{lat:.6f}/{lon:.6f}"
        satellites = value.get("satellites")
        freshness = f"fix reçu il y a {age:.0f} s" + (" (position périmée)" if stale else "")
        accuracy = value.get("horizontal_accuracy_m", value.get("accuracy_m"))
        detail = f", précision annoncée ±{float(accuracy):.1f} m" if isinstance(accuracy, (int, float)) else " ; précision métrique non fournie par ce flux"
        sat_detail = f", {satellites} satellites" if satellites is not None else ""
        return {
            "handled": True,
            "status": "reported",
            "response": f"Position GNSS du Body : {lat:.6f}, {lon:.6f} ({freshness}{sat_detail}{detail}). Ouvrir dans OpenStreetMap : {map_url}. Cela localise le Body à l'échelle géographique, pas sa pose précise ni les obstacles dans la pièce.",
            "location": {"available": True, "latitude": lat, "longitude": lon, "age_seconds": round(age, 1), "stale": stale, "map_url": map_url},
        }

    @staticmethod
    def _direct_body_motion(text: str) -> dict | None:
        """Map an unambiguous short locomotion request to one FNHR primitive.

        Destination-based requests intentionally remain with the grounded
        planner; this helper only handles relative directional commands.
        """
        value = str(text or "").casefold()
        if re.search(r"\b(turn|rotate|tourne|virage)\b.{0,24}\b(left|gauche)\b|\b(gauche|left)\b.{0,24}\b(turn|tourne)\b", value):
            return {"action": "turn_left", "label": "tourner à gauche"}
        if re.search(r"\b(turn|rotate|tourne|virage)\b.{0,24}\b(right|droite)\b|\b(droite|right)\b.{0,24}\b(turn|tourne)\b", value):
            return {"action": "turn_right", "label": "tourner à droite"}
        if re.search(r"\b(backward|backwards|reverse|recule|reculer|en arrière|en arriere)\b", value):
            return {"action": "backward", "label": "reculer"}
        if re.search(r"\b(forward|forwards|advance|avancer|avance|en avant)\b", value):
            return {"action": "forward", "label": "avancer"}
        if re.search(r"\b(strafe|crawl|move|déplace|deplace|va)\b.{0,24}\b(left|gauche)\b|\b(à gauche|a gauche)\b", value):
            return {"action": "left", "label": "se déplacer à gauche"}
        if re.search(r"\b(strafe|crawl|move|déplace|deplace|va)\b.{0,24}\b(right|droite)\b|\b(à droite|a droite)\b", value):
            return {"action": "right", "label": "se déplacer à droite"}
        return None

    @staticmethod
    def _may_route_to_body(text: str) -> bool:
        """Gate the Body LLM classifier behind explicit Body/action intent."""
        normalized = str(text or "").lower().strip()
        body_reference = re.search(
            r"\b(body|robot|ventuno|fnk0031|gps|gnss|sensor|sensors|capteur|capteurs|"
            r"yolox|midas|tof|mmwave|radar|odometry|odom|ultrasonic|ultrasonique|"
            r"motor|motors|engine|engines|servo|servos|servomotor|servomoteur|servomoteurs|"
            r"moteur|moteurs|jambe|jambes|articulation|articulations)\b",
            normalized,
        )
        # This is only a high-recall gateway to the semantic action classifier,
        # not an action/command parser. Match verbs anywhere in the utterance so
        # polite/intervening phrases ("peux-tu te déplacer vers la TV") cannot
        # bypass the Brain's goal and capability assessment.
        direct_action = re.search(
            r"\b(?:move|moving|moved|drive|driving|navigate|go|turn|stop|walk|advance|crawl|"
            r"approach|come closer|déplac\w*|deplac\w*|avance\w*|recule\w*|tourne\w*|"
            r"arrête\w*|arrete\w*|marche\w*|rapproche\w*)\b|"
            r"\b(?:en avant|à gauche|a gauche|à droite|a droite)\b",
            normalized,
        )
        return bool(body_reference or direct_action)

    @staticmethod
    def _may_route_to_local_camera(text: str) -> bool:
        """Cheap candidate gate; the semantic classifier decides the actual intent."""
        return bool(re.search(
            r"\b(camera|caméra|vision|visual|image|picture|photo|face|visage|see|seeing|look|looking|vois|voir|vois-tu|regarde|reconnais|reconnaissance)\b",
            str(text or "").lower(),
        ))

    @staticmethod
    def _is_factual_question_form(text: str) -> bool:
        """Recognize interrogative grammar so a read-only question cannot fall into the diagnostic dump."""
        normalized = str(text or "").strip().casefold()
        if "?" in normalized:
            return True
        return bool(
            re.match(
                r"^(?:quel(?:le|s|les)?|qu['’]est|qu['’]elle|que|qui|où|ou|pourquoi|comment|"
                r"what|which|who|where|when|why|how|is|are|do|does|did|can|could|"
                r"combien|est-ce\s+que|y\s+a[- ]t[- ]il)\b",
                normalized,
            )
            or re.search(r"\b(?:can|could|do|does|did)\s+you\b", normalized)
        )

    @staticmethod
    def _is_explicit_goal_persistence_request(text: str) -> bool:
        """Match direct requests to write a goal, which must not be narrated as an LLM-only side effect."""
        normalized = str(text or "").strip().casefold()
        command = re.match(
            r"^\s*(?:(?:for this audit|for this test|please|s'il te plaît|s’il te plaît)\s*,?\s*)*"
            r"(?:(?:can|could|would) you\s+|i want you to\s+|je veux que tu\s+|peux-tu\s+|"
            r"pourrais-tu\s+)?(?:create|add|save|persist|record|establish|set up|"
            r"créer|crée|ajouter|enregistrer|sauvegarder|persister|établir|définir)\b",
            normalized,
        )
        goal_reference = re.search(
            r"\b(?:goal|objective|aspiration|goal\s+engine|objectif|but|aspiration)\b",
            normalized,
        )
        return bool(command and goal_reference)

    @staticmethod
    def _parse_explicit_goal_request(text: str) -> tuple[str, str]:
        """Extract a user-authored title and criteria from an explicit goal-write request."""
        raw = str(text or "").strip()
        title_match = re.search(
            r"\b(?:goal|objective|objectif|but)\s*:\s*(.+?)(?=\.\s|$)",
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if not title_match:
            return "", ""
        topic = " ".join(title_match.group(1).split()).strip(" \t\r\n.;:")
        criteria_match = re.search(
            r"\b(?:success criteria?|measurable success criteria?|critère de succès(?: mesurable)?|"
            r"critères de réussite)\s*(?::|is|are|will be|sera|seront)\s*(.+?)(?=\.\s|$)",
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        criteria = " ".join(criteria_match.group(1).split()).strip(" \t\r\n.;:") if criteria_match else ""
        if not criteria and topic:
            criteria = (
                "Across five consecutive relevant answers, an independent review or the user confirms "
                "that observed facts and inferences are explicitly separated with zero category errors."
                if re.search(r"\b(observation|observed|fact|inference|observation|fait|inférence)\b", topic, re.I)
                else f"Across five consecutive relevant answers about {topic}, a reviewer confirms the stated capability is demonstrated without a material error."
            )
        return topic, criteria

    @staticmethod
    def _is_goal_persistence_verification(text: str) -> bool:
        """Match questions or challenges about whether a conversational goal write really happened."""
        normalized = str(text or "").casefold()
        has_goal = bool(re.search(r"\b(?:goal|objective|objectif|but|aspiration)\b", normalized))
        # A request for the current count is a state query, not a request to
        # audit whether a prior write occurred. Keep it on the factual
        # self-report path so the live snapshot and its count are the source
        # of truth. Phrases such as "from the recorded goal state" must not
        # turn a count question into a write-receipt query.
        asks_owned_goal_count = bool(
            (
                re.search(r"\bhow\s+many\b.{0,80}\b(?:active\s+)?goals?\b", normalized)
                and re.search(r"\b(?:you|your)\b", normalized)
            )
            or (
                re.search(r"\bcombien\b.{0,80}\b(?:objectifs?|buts?)\b", normalized)
                and re.search(r"\b(?:tu|tes|ton|vous|vos|votre)\b", normalized)
            )
        )
        if asks_owned_goal_count:
            return False
        asks_id = bool(re.search(
            r"\b(?:exact\s+(?:persistent\s+)?id|id\s+(?:of|for)|identifier|identifiant)\b",
            normalized,
        ))
        asks_write_status = bool(
            re.search(r"\b(?:did|have|has|was|is)\b.{0,60}\b(?:saved|persisted|created|recorded)\b", normalized)
            or re.search(r"\b(?:saved|persisted|created|recorded)\b.{0,60}\b(?:goal|objective|objectif)\b", normalized)
        )
        challenges_claim = bool(
            re.search(r"\b(?:not visible|does not exist|doesn't exist|retract|withdraw|verify|confirm|rétract\w*)\b.{0,80}\b(?:goal|objective|objectif)\b", normalized)
            or re.search(r"\b(?:goal|objective|objectif)\b.{0,80}\b(?:not visible|does not exist|doesn't exist|retract|withdraw|verify|confirm|rétract\w*)\b", normalized)
        )
        asks_proof = asks_id or asks_write_status or challenges_claim
        return has_goal and asks_proof

    def _goal_persistence_status(self, user_text: str) -> dict:
        """Answer goal-write verification only from the live GoalEngine registry."""
        system = self._system
        engine = getattr(system, "goal_engine", None) if system is not None else None
        if engine is None or not callable(getattr(engine, "get_active_goals", None)):
            return {
                "handled": True,
                "status": "unverified",
                "response": (
                    "I cannot verify that goal write: the live GoalEngine state is unavailable in this turn. "
                    "I will not claim an ID or persistence without reading it back."
                ),
            }

        try:
            all_goals = list(getattr(engine, "_goals", {}).values())
            requested_ids = {value.casefold() for value in re.findall(
                r"\bgoal_[a-z0-9_-]+\b", str(user_text or ""), re.IGNORECASE
            )}
            id_matches = [
                goal for goal in all_goals
                if str(getattr(goal, "id", "")).casefold() in requested_ids
            ]
            if requested_ids:
                if id_matches:
                    goal = id_matches[0]
                    prior_turns = getattr(self, "_turn_trace_history", [])
                    previous_turn_id = (
                        str(prior_turns[-1].get("turn_id") or "")
                        if prior_turns and isinstance(prior_turns[-1], dict) else ""
                    )
                    caused_by_previous_turn = bool(
                        previous_turn_id
                        and str(getattr(goal, "source_turn_id", "")) == previous_turn_id
                    )
                    response = (
                        f"GoalEngine currently contains {goal.id} ({goal.topic}), status {goal.status}. "
                        + (
                            "Its stored source_turn_id matches the immediately preceding chat turn."
                            if caused_by_previous_turn
                            else "The registry does not link it to the immediately preceding chat turn."
                        )
                    )
                    status = "found_and_causally_linked" if caused_by_previous_turn else "found_without_turn_link"
                else:
                    response = (
                        "I cannot verify that identifier: no matching goal ID exists in the current GoalEngine registry. "
                        "The previous claim that it was saved was unsupported."
                    )
                    status = "id_not_found"
            else:
                active = list(engine.get_active_goals())
                response = (
                    f"The live GoalEngine currently reports {len(active)} active goal(s). "
                    "There is no turn-linked write receipt available here, so I cannot attribute a goal to the preceding chat turn."
                )
                status = "live_state_read_without_turn_receipt"
            return {"handled": True, "status": status, "response": response}
        except Exception as exc:
            logger.warning("[GoalWriteGate] GoalEngine read-back failed: %s", exc)
            return {
                "handled": True,
                "status": "unverified",
                "response": "I cannot verify the goal write because reading the live GoalEngine registry failed; I will not claim it was saved.",
            }

    def _explicit_goal_write_gate(self, user_text: str) -> dict | None:
        if self._is_explicit_goal_persistence_request(user_text):
            is_french = bool(re.search(
                r"\b(?:créer|crée|ajouter|enregistrer|sauvegarder|objectif|critère)\b",
                str(user_text or "").casefold(),
            ))
            topic, criteria = self._parse_explicit_goal_request(user_text)
            if not topic:
                return {
                    "handled": True,
                    "status": "needs_goal_title",
                    "response": (
                        "Je n'ai pas créé d'objectif : indique son titre explicitement, par exemple « créer un objectif : améliorer… », pour éviter d'en inventer la portée. Aucun changement persistant n'a été fait."
                        if is_french else
                        "I did not create a goal: to avoid inventing its scope, provide an explicit title such as 'create a goal: improve …'. No persistent change was made."
                    ),
                }
            engine = getattr(self._system, "goal_engine", None) if self._system is not None else None
            create = getattr(engine, "create_user_requested_goal", None)
            turn_id = str(getattr(self, "_last_turn_trace", {}).get("turn_id") or "")
            if not callable(create) or not turn_id:
                return {
                    "handled": True,
                    "status": "not_executed",
                    "response": (
                        "Je n'ai pas créé ni enregistré l'objectif : GoalEngine ou l'identifiant d'audit de ce tour est indisponible."
                        if is_french else
                        "I did not create or persist the goal: GoalEngine or this turn's audit ID is unavailable."
                    ),
                }
            result = create(topic, criteria, turn_id)
            if result.get("created") and result.get("verified"):
                return {
                    "handled": True,
                    "status": "persisted_verified",
                    "goal_write": result,
                    "response": (
                        f"GoalEngine a enregistré puis relu {result['id']} : {result['topic']}. "
                        f"Critère de réussite : {result['success_criteria']} "
                        f"L'enregistrement est lié au tour {result['source_turn_id']}."
                        if is_french else
                        f"GoalEngine saved and read back {result['id']}: {result['topic']}. "
                        f"Success criterion: {result['success_criteria']} "
                        f"The record links to chat turn {result['source_turn_id']}."
                    ),
                }
            return {
                "handled": True,
                "status": "write_failed",
                "goal_write": result,
                "response": (
                    "L'enregistrement de l'objectif n'a pas été confirmé. GoalEngine l'a refusé ou la relecture persistante a échoué ; aucun identifiant n'est présenté comme un succès."
                    if is_french else
                    "The goal was not confirmed as saved. GoalEngine rejected it or its persistence read-back failed; no goal ID is being reported as successful."
                ),
            }
        if self._is_goal_persistence_verification(user_text):
            return self._goal_persistence_status(user_text)
        return None

    @staticmethod
    def _is_destination_action_request(text: str) -> bool:
        """Keep explicit locomotion-to-a-destination requests on the guarded planner path."""
        normalized = str(text or "").casefold()
        action = r"(?:move|drive|navigate|go|walk|crawl|approach|advance|déplac\w*|deplac\w*|aller|marche|avance\w*|rapproche\w*)"
        destination = r"(?:toward|towards|to|vers|jusqu['’]à|jusqu'a|en direction de)"
        return bool(re.search(rf"\b{action}\b.{{0,48}}\b{destination}\b", normalized))

    @staticmethod
    def _is_developmental_autonomy_audit_request(text: str) -> bool:
        """Recognize the specific end-to-end autonomy audit, not generic development chat."""
        normalized = str(text or "").casefold()
        has_hypothesis = bool(re.search(r"\b(hypoth(?:esis|èse)|developmental|développemental)\b", normalized))
        has_persistent_goal = bool(re.search(r"\b(persistent goal|goal engine|objectif persistant|objectif développemental)\b", normalized))
        has_observation_measure = bool(re.search(r"\b(baseline|real observations|observations réelles|mesure initiale)\b", normalized))
        has_closed_loop = bool(re.search(r"\b(plan|schedule|verify|verification|vérification|revise|réviser|results|résultats)\b", normalized))
        no_intervention = bool(re.search(r"\b(without (?:changing|modifying) (?:the )?code|sans modification|sans intervention)\b", normalized))
        return sum((has_hypothesis, has_persistent_goal, has_observation_measure, has_closed_loop, no_intervention)) >= 4

    @staticmethod
    def _local_camera_prompt_context() -> str:
        """Describe the Brain-PC camera's live state, separate from Body feeds."""
        try:
            from core.state import state as app_state
            vision = getattr(app_state, "vision", None)
            launch_enabled = getattr(app_state, "local_vision_launch_enabled", None)
        except Exception:
            vision = None
            launch_enabled = None

        if vision is None:
            if launch_enabled is False:
                return (
                    "BRAIN-PC CAMERA STATUS: DISABLED at headless startup (`--vision` was not passed); "
                    "no Brain-PC frame or face-recognition result is available. "
                    "Body-camera detections are a separate source and cannot answer what the Brain-PC camera sees."
                )
            return (
                "BRAIN-PC CAMERA STATUS: unavailable; no local camera manager or current local image is available. "
                "Body-camera detections are a separate source and cannot answer what the Brain-PC camera sees."
            )

        if not bool(getattr(vision, "camera_active", False)):
            reason = (
                "disabled at headless startup because `--vision` was not passed"
                if launch_enabled is False else "inactive"
            )
            return (
                f"BRAIN-PC CAMERA STATUS: {reason}; there is no current Brain-PC camera frame. "
                "Do not claim to see the user or infer PC-camera content from Body-camera YOLOX or any other Body sensor."
            )

        now = time.time()
        frame_stamp = float(getattr(vision, "frame_updated_at", 0.0) or 0.0)
        frame_age = max(0.0, now - frame_stamp) if frame_stamp else None
        if frame_age is None:
            frame_status = "active, but no timestamped frame is available"
        elif frame_age > 3.0:
            frame_status = f"active, but its last frame is stale ({frame_age:.1f}s old)"
        else:
            frame_status = f"active; latest frame is {frame_age:.1f}s old"

        face_stamp = float(getattr(vision, "last_face_detection_at", 0.0) or 0.0)
        face_age = max(0.0, now - face_stamp) if face_stamp else None
        face_detail = "face-recognition result unavailable or stale"
        if bool(getattr(vision, "face_detection_enabled", False)) and face_age is not None and face_age <= 6.0:
            faces = getattr(vision, "last_detected_faces", []) or []
            names = [
                str(face.get("name")) for face in faces
                if isinstance(face, dict)
                and str(face.get("name") or "").strip().lower() not in {"", "unknown", "unknown person"}
            ]
            face_detail = (
                f"recent face-recognition result ({face_age:.1f}s old), recognized={', '.join(names)}"
                if names else f"recent face-recognition result ({face_age:.1f}s old), no known identity"
            )
        elif not bool(getattr(vision, "face_detection_enabled", False)):
            face_detail = "face recognition disabled"
        return (
            f"BRAIN-PC CAMERA STATUS: {frame_status}; {face_detail}. "
            "Camera activity alone does not prove a person is visible. Use only a current Brain-PC frame/observation for PC-camera questions. "
            "Never relabel Body-camera detections as Brain-PC observations."
        )

    @staticmethod
    def _local_camera_response() -> dict:
        """Answer current PC-camera questions only from fresh local telemetry."""
        try:
            from core.state import state as app_state
            vision = getattr(app_state, "vision", None)
        except Exception:
            vision = None
        if vision is None:
            return {"handled": True, "status": "unavailable", "response": "Je n'ai pas accès à l'état de la caméra locale du PC dans ce tour."}
        if not bool(getattr(vision, "camera_active", False)):
            return {"handled": True, "status": "unavailable", "response": "Non, pas à cet instant : la caméra locale du PC est inactive."}
        now = time.time()
        frame_stamp = float(getattr(vision, "frame_updated_at", 0.0) or 0.0)
        frame_age = max(0.0, now - frame_stamp) if frame_stamp else None
        if frame_age is None or frame_age > 3.0:
            return {
                "handled": True, "status": "stale",
                "response": "La caméra locale du PC est activée, mais son image est absente ou trop ancienne; je ne peux pas confirmer que je te vois maintenant.",
                "camera": {"source": "brain_pc_camera", "frame_age_seconds": frame_age, "stale": True},
            }
        enabled = bool(getattr(vision, "face_detection_enabled", False))
        face_stamp = float(getattr(vision, "last_face_detection_at", 0.0) or 0.0)
        face_age = max(0.0, now - face_stamp) if face_stamp else None
        faces = getattr(vision, "last_detected_faces", []) or []
        recent_faces = enabled and face_age is not None and face_age <= 6.0
        known = [
            face for face in faces
            if isinstance(face, dict)
            and str(face.get("name") or "").strip().lower() not in {"", "unknown", "unknown person"}
        ]
        if recent_faces and known:
            people = ", ".join(str(face.get("name")) for face in known[:4])
            answer = f"Oui, la caméra locale du PC reçoit une image récente et la reconnaissance faciale identifie : {people}."
        elif recent_faces and faces:
            answer = "Oui, la caméra locale du PC reçoit une image récente et le détecteur voit au moins un visage, mais son identité n'est pas reconnue."
        elif recent_faces:
            answer = "La caméra locale du PC reçoit une image récente, mais le dernier contrôle n'a détecté aucun visage; je ne peux donc pas confirmer que tu es dans son champ."
        else:
            answer = "La caméra locale du PC reçoit une image récente, mais la reconnaissance faciale n'a pas de résultat récent; je ne peux pas confirmer si tu es visible."
        current = vision.get_working_memory().get("current") if callable(getattr(vision, "get_working_memory", None)) else None
        scene_age = None
        scene = ""
        if isinstance(current, dict):
            try:
                scene_age = max(0.0, now - float(current.get("updated_at_unix")))
            except (TypeError, ValueError):
                scene_age = None
            if scene_age is not None and scene_age <= 30.0:
                scene = str(current.get("description") or "").strip()
        if scene:
            answer += f" Analyse de scène locale (âgée de {scene_age:.0f} s) : {scene[:260]}"
        return {
            "handled": True,
            "status": "reported",
            "response": answer,
            "camera": {
                "source": "brain_pc_camera",
                "frame_age_seconds": round(frame_age, 3),
                "face_recognition_enabled": enabled,
                "face_detection_age_seconds": round(face_age, 3) if face_age is not None else None,
                "recognized_faces": [face.get("name") for face in known],
                "scene_age_seconds": round(scene_age, 3) if scene_age is not None else None,
            },
        }

    @staticmethod
    def _developmental_autonomy_response() -> dict:
        response = (
            "Audit de capacité, pas une exécution : l'architecture possède un GoalEngine qui persiste des objectifs et un moteur d'expérimentation qui conserve des expériences, "
            "mais aucun flux ne relie actuellement une hypothèse développementale à un objectif, à une baseline d'observations réelles, à une vérification planifiée, puis à une révision fondée sur les résultats. "
            "Le moteur expérimental mesure surtout des comportements conversationnels et peut utiliser des valeurs heuristiques; il ne constitue pas une mesure initiale réelle de cette hypothèse. "
            "Les deux registres sont indépendants. Certaines actions internes sont possibles, mais toute action externe ou physique reste soumise à ses propres capacités et autorisations. "
            "Effectivement exécuté : rien. Aucun objectif ni test n'a été créé; aucun identifiant n'existe. "
            "Conclusion : je ne peux pas prendre en charge cette démarche de bout en bout sans modification du logiciel et définition d'une mesure observable adaptée."
        )
        return {
            "handled": True,
            "status": "capability_audit",
            "response": response,
            "audit": {
                "goal_persistence": "partial; GoalEngine exists but is not linked to a user hypothesis workflow",
                "real_observation_baseline": False,
                "scheduled_hypothesis_verification": False,
                "bounded_internal_experiments": True,
                "goal_experiment_linkage": False,
                "goal_created": False,
                "experiment_created": False,
                "id": None,
            },
        }

    @staticmethod
    def _is_simulated_source(source: object) -> bool:
        source_text = str(source or "").lower()
        return any(marker in source_text for marker in (
            "ros2_simulation", "sim_robot", "simulated_room", "simulator",
            "simulation", "virtual_lidar",
        ))

    @classmethod
    def _is_simulated_body_observation(cls, item: dict) -> bool:
        value = item.get("value") if isinstance(item, dict) else None
        provenance = item.get("provenance") if isinstance(item, dict) else None
        source = item.get("source") if isinstance(item, dict) else ""
        return (
            cls._is_simulated_source(source)
            or (isinstance(value, dict) and cls._is_simulated_source(value.get("source")))
            or (isinstance(value, dict) and value.get("simulated") is True)
            or (isinstance(provenance, dict) and provenance.get("simulated") is True)
            or (isinstance(provenance, dict) and cls._is_simulated_source(provenance.get("source")))
        )

    @classmethod
    def _is_simulated_body_snapshot(cls, snapshot: dict) -> bool:
        semantic_scene = snapshot.get("semantic_scene")
        return (
            snapshot.get("simulated_only") is True
            or snapshot.get("ground_truth_available") is True
            or cls._is_simulated_source(snapshot.get("source"))
            or (isinstance(semantic_scene, dict) and semantic_scene.get("simulated") is True)
        )

    def _format_body_sensor_observation(self, item: dict) -> str:
        subject = str(item.get("subject") or "sensor")
        detail = self._format_body_sensor(subject, item.get("value"))
        age = max(0.0, time.time() - float(item.get("observed_at") or time.time()))
        return f"{detail} (STALE {age:.0f}s)" if age > 15.0 else detail

    @staticmethod
    def _format_body_sensor(subject: str, value) -> str:
        """Render compact, unit-aware live sensor telemetry; never infer missing ranges."""
        if not isinstance(value, dict):
            return f"{subject.removeprefix('sensor.')}: invalid sample"
        name = subject.removeprefix("sensor.")
        age = value.get("age_s", value.get("age_seconds"))
        age_text = f", {float(age):.1f}s old" if isinstance(age, (int, float)) else ""
        available = value.get("available")
        if name == "gps":
            if value.get("fix") and value.get("latitude") is not None and value.get("longitude") is not None:
                detail = f"fix {float(value['latitude']):.6f}, {float(value['longitude']):.6f}; {value.get('satellites', '?')} satellites"
            else:
                detail = f"no position fix; {value.get('satellites_in_view', '?')} satellites in view"
        elif name == "imu":
            attitude = value.get("attitude_valid")
            if attitude:
                detail = f"roll {value.get('roll_deg')}°, pitch {value.get('pitch_deg')}°, yaw-relative {value.get('yaw_relative_deg')}°"
            else:
                detail = f"attitude unavailable; acceleration {value.get('acceleration_g')}, gyro {value.get('angular_velocity_dps')}°/s"
        elif name == "ultrasonic":
            channels = value.get("sensors") or []
            parts = []
            for channel in channels:
                label = str(channel.get("id") or "channel")
                distance = channel.get("distance_m") if channel.get("available") else None
                parts.append(f"{label} {float(distance):.2f}m" if isinstance(distance, (int, float)) else f"{label} no echo/data")
            detail = ", ".join(parts) if parts else "no channel samples"
        elif name == "tof":
            distance = value.get("distance_m")
            detail = f"{float(distance):.2f}m" if isinstance(distance, (int, float)) else str(value.get("error") or "no valid range")
        elif name == "mmwave_radar":
            targets = value.get("targets") or []
            descriptions = []
            for target in targets:
                if not isinstance(target, dict):
                    continue
                distance = target.get("range_m", target.get("distance_m"))
                position = target.get("position_m", target.get("position"))
                if isinstance(position, dict):
                    forward, lateral = position.get("forward", position.get("x")), position.get("lateral", position.get("y"))
                elif isinstance(position, (list, tuple)) and len(position) >= 2:
                    # Ventuno contract: [forward, lateral, vertical] in body frame.
                    forward, lateral = position[0], position[1]
                else:
                    forward = lateral = None
                bearing = None
                if isinstance(forward, (int, float)) and isinstance(lateral, (int, float)):
                    distance = distance if isinstance(distance, (int, float)) else math.hypot(float(forward), float(lateral))
                    bearing = math.degrees(math.atan2(float(lateral), float(forward)))
                classification = str(target.get("classification") or "unknown")
                parts = [f"target {target.get('target_id', target.get('id', '?'))} ({classification}, unassociated)"]
                if isinstance(distance, (int, float)):
                    parts.append(f"{float(distance):.2f}m")
                if bearing is not None:
                    parts.append(f"bearing {bearing:+.0f}°")
                confidence = target.get("confidence")
                if isinstance(confidence, (int, float)):
                    parts.append(f"confidence {float(confidence):.2f}")
                radial = target.get("radial_speed_mps", target.get("radial_velocity_mps"))
                if isinstance(radial, (int, float)):
                    parts.append(f"radial {float(radial):+.2f}m/s")
                descriptions.append(" ".join(parts))
            detail = f"{len(targets)} target(s)" + (": " + "; ".join(descriptions[:4]) if descriptions else "")
        elif name == "depth_calibration":
            if value.get("available"):
                limits = value.get("calibrated_range_m") or []
                range_text = f"{float(limits[0]):.2f}–{float(limits[1]):.2f}m" if isinstance(limits, (list, tuple)) and len(limits) >= 2 else "range not reported"
                error = value.get("holdout_rmse_m", value.get("rmse_m"))
                detail = f"MiDaS metric fit valid over {range_text}"
                if isinstance(error, (int, float)):
                    detail += f", holdout RMSE {float(error):.2f}m"
                detail += "; no object-to-box association supplied"
            else:
                detail = "MiDaS metric fit unavailable: " + str(value.get("reason") or "not calibrated")
        elif name == "odometry":
            detail = f"position {value.get('position_m')}; yaw {value.get('yaw_rad')}rad"
        elif name == "lidar":
            ranges = [float(item) for item in (value.get("ranges_m") or []) if isinstance(item, (int, float))]
            detail = f"{len(ranges)} valid range(s)" + (f", nearest {min(ranges):.2f}m" if ranges else "")
        else:
            detail = str(value.get("error") or ("sample available" if available else "no sample"))
        state = "live" if available is not False else "unavailable"
        return f"{name} {state}: {detail}{age_text}"

    def handle_body_chat_turn(self, user_input: str, user_id: str = "default") -> dict | None:
        """Handle only Body-specific turns; return None for normal dialogue."""
        pending = self._pending_body_plans.get(str(user_id))
        bare_body_reference = re.fullmatch(r"[\W_]*(?:the\s+|le\s+|mon\s+|my\s+)?body[\W_]*", str(user_input or "").strip(), re.IGNORECASE)
        if not pending and bare_body_reference:
            return {
                "handled": True,
                "status": "clarification",
                "response": "Que veux-tu savoir du Body : ses capteurs, sa caméra, ses moteurs/servos, son énergie ou ses capacités ?",
            }
        if not pending and self._is_developmental_autonomy_audit_request(user_input):
            return self._developmental_autonomy_response()
        if not pending and not (self._may_route_to_body(user_input) or self._may_route_to_local_camera(user_input)):
            return None
        if (
            not pending
            and self._is_factual_question_form(user_input)
            and not self._is_destination_action_request(user_input)
        ):
            # Read-only questions belong to the main PersonaBridge cognitive
            # turn. That path receives timestamped Body and camera provenance,
            # then reasons over it; the action-intent classifier is only a
            # safety gate and must not substitute a canned telemetry reply.
            return None
        route = self._classify_body_chat_turn(user_input, pending=pending)
        if not pending and route == "body_diagnostic" and self._is_factual_question_form(user_input):
            # The classifier occasionally mistakes a factual question (for
            # example, "quel est l'état des moteurs") for a diagnostic request.
            # Let the main LLM answer from the Body's timestamped evidence.
            route = "normal"
        if route == "body_status":
            # A local classifier can confuse an approval such as "execute the
            # plan" with a status question. Resolve that ambiguity with a
            # confirmation-focused semantic judgment before reporting that no
            # active plan exists.
            if pending:
                reroute = self._classify_body_chat_turn(
                    user_input,
                    pending=pending,
                    confirmation_probe=True,
                )
                if reroute == "confirm":
                    route = reroute
                elif reroute == "cancel":
                    route = reroute
                else:
                    # Read-only Body telemetry and status belong to the main
                    # conversational model, which receives the timestamped
                    # Body snapshot in its system context.
                    return None
            else:
                # Read-only Body questions go to the conversational LLM with
                # timestamped Body evidence in its system context. Do not
                # replace its answer with a fixed route-specific response.
                return None
        if route == "body_diagnostic":
            # Diagnostics are read-only. Let the main conversational model
            # analyze the timestamped Body observations already in context;
            # this route must never turn them into a fixed sensor digest or a
            # motor plan.
            return None
        if not pending and route != "body_action":
            return None
        if pending and route == "confirm":
            body = getattr(self._organism, "_body_runtime", None) if self._organism else None
            direct_command = pending.get("direct_command") if isinstance(pending, dict) else None
            if isinstance(direct_command, dict):
                if body is None:
                    self._pending_body_plans.pop(str(user_id), None)
                    return {"handled": True, "status": "unavailable", "response": "Le pont de commande Body est indisponible; aucun mouvement n'a été envoyé."}
                if time.time() - float(pending.get("created_at") or 0.0) > 20.0:
                    self._pending_body_plans.pop(str(user_id), None)
                    return {"handled": True, "status": "expired", "response": "La confirmation est arrivée après expiration de la commande de mouvement. Rien n'a été envoyé; redemande le déplacement pour obtenir une nouvelle vérification."}
                observations = body.snapshot(max_age=8.0)
                capability = robot_capability_report(observations, "locomotion", max_age=8.0)
                if not capability.get("ready"):
                    self._pending_body_plans.pop(str(user_id), None)
                    return {"handled": True, "status": "blocked", "response": "À la confirmation, le Body ne confirme plus une capacité locomotrice installée, opérationnelle et autorisée. Aucun mouvement n'a été envoyé."}
                command = body.enqueue_command(
                    target="fnk0031",
                    action=str(direct_command.get("action") or ""),
                    payload={"params": {}},
                    requires_confirmation=True,
                    origin="lumina_chat_confirmation",
                    ttl_seconds=20.0,
                )
                approval = body.approve_command(command.command_id)
                self._pending_body_plans.pop(str(user_id), None)
                if not approval.get("ok"):
                    return {
                        "handled": True,
                        "status": "blocked",
                        "response": "Le Body n'a pas accepté la commande confirmée : " + str(approval.get("error") or "échec de signature ou de livraison") + ". Aucun mouvement n'est confirmé.",
                        "command": approval.get("command"),
                    }
                return {
                    "handled": True,
                    "status": "submitted",
                    "response": f"Commande {direct_command.get('label') or direct_command['action']} signée et transmise au Body (réf. {command.command_id}). J'attends son acquittement FNHR; cela ne prouvera pas un déplacement mesuré.",
                    "command": approval.get("command"),
                }
            if str(pending.get("execution_scope") or "unknown") != "simulation":
                required_capabilities = pending.get("required_capabilities") or []
                fresh_observations = body.snapshot(max_age=15.0) if body is not None else []
                unavailable = [
                    name for name in required_capabilities
                    if not robot_capability_report(fresh_observations, str(name)).get("ready")
                ]
                if unavailable:
                    self._pending_body_plans.pop(str(user_id), None)
                    return {
                        "handled": True,
                        "status": "blocked",
                        "response": "Depuis la préparation du plan, le Body ne confirme plus les capacités matérielles requises ("
                        + ", ".join(str(name) for name in unavailable)
                        + "). Aucun plan n'a été soumis et aucune commande n'a été envoyée.",
                    }
            replacement_id = str(pending.get("replace_plan_id") or "").strip()
            if replacement_id and body:
                cancelled = body.cancel_worldmodel_plan(
                    replacement_id,
                    reason="superseded by a newer user Body objective",
                )
                if not cancelled.get("ok") and "not found" not in str(cancelled.get("error", "")).lower():
                    return {"handled": True, "status": "blocked", "response": "Le Body n'a pas pu interrompre le plan précédent : " + str(cancelled.get("error", "annulation impossible")), "cancellation": cancelled}
            result = body.submit_worldmodel_plan(pending["plan"]) if body else {"accepted": False, "error": "Body unavailable"}
            if result.get("accepted"):
                run_result = body.run_worldmodel(True, False) if body else {"error": "Body unavailable"}
                if isinstance(run_result, dict) and run_result.get("error"):
                    return {"handled": True, "status": "blocked", "response": "Le plan est accepté, mais le Body ne démarre pas : " + str(run_result["error"]), "submission": result, "runtime": run_result}
                self._pending_body_plans.pop(str(user_id), None)
                submitted_plan = result.get("plan") if isinstance(result, dict) else None
                steps = list(submitted_plan.get("steps") or []) if isinstance(submitted_plan, dict) else []
                current = steps[0] if steps else {}
                if str(current.get("verb") or "") == "explore":
                    targets = list((current.get("arguments") or {}).get("targets") or [])
                    first_step = f"L’exploration de la scène commence ({len(targets)} points à visiter, sans saisir d’objet)."
                else:
                    first_step = f"La première étape est {current.get('verb', 'l’action demandée')} vers {current.get('target', 'la cible')}."
                prefix = "Le nouveau plan est confirmé et transmis au Body. Le plan précédent a été interrompu. " if replacement_id else "Le plan est confirmé et transmis au Body. "
                response = prefix + first_step
                return {"handled": True, "status": "submitted", "response": response, "submission": result, "runtime": run_result}
            return {"handled": True, "status": "blocked", "response": "Le Body refuse encore ce plan : " + "; ".join(result.get("errors") or [result.get("error", "validation impossible")]), "submission": result}
        if pending and route == "cancel":
            self._pending_body_plans.pop(str(user_id), None)
            return {"handled": True, "status": "cancelled", "response": "Le plan Body est annulé, aucune action n'a été exécutée."}
        if pending and route == "normal":
            # Never reinterpret an ambiguous confirmation as a new physical
            # objective. That used to compile "oui"/"execute" again, replace
            # the pending draft and ask the same question indefinitely.
            return {
                "handled": True,
                "status": "awaiting_confirmation",
                "response": "Le plan Body reste en attente. Confirmez explicitement son exécution ou annulez-le.",
                "pending_plan": pending.get("plan"),
            }
        if pending and route != "new_action":
            return None
        if route != "body_action" and not (pending and route == "new_action"):
            return None
        if route == "body_action" and not pending:
            direct_motion = self._direct_body_motion(user_input)
            if direct_motion:
                body = getattr(self._organism, "_body_runtime", None) if self._organism else None
                observations = body.snapshot(max_age=8.0) if body is not None else []
                capability = robot_capability_report(observations, "locomotion", max_age=8.0)
                # This shortcut emits FNHR commands and therefore belongs only
                # to the FNK adapter. Other robots continue through the general
                # objective planner, using their own Body capability report.
                if capability.get("robot_id") == "fnk0031":
                    if not capability.get("ready"):
                        return {"handled": True, "status": "blocked", "response": "Le Body ne confirme pas que la locomotion du robot FNK est installée, opérationnelle, autorisée et récente. Aucun mouvement n'a été préparé ni envoyé."}
                    self._pending_body_plans[str(user_id)] = {"direct_command": direct_motion, "created_at": time.time()}
                    return {
                        "handled": True,
                        "status": "awaiting_confirmation",
                        "response": f"Le Body confirme la capacité locomotrice du profil {capability.get('robot_model') or capability.get('robot_id')}. Je propose une seule commande FNHR « {direct_motion['label']} » (un cycle de marche), sans cible de scène. Confirmes-tu son envoi ?",
                        "command": {"target": "fnk0031", "action": direct_motion["action"], "requires_confirmation": True},
                    }
        assessment = self.assess_body_action_request(user_input)
        if not assessment.get("accepted"):
            # A semantically classified Body request must fail closed. Falling
            # through to the conversational LLM here allowed it to narrate an
            # action after the Body had rejected the plan. Ordinary social
            # turns never reach this branch because the classifier routes them
            # to NORMAL before planning.
            if assessment.get("status") in {"invalid", "error"}:
                return {
                    "handled": True,
                    "status": "blocked",
                    "response": "Je ne peux pas exécuter cette action Body : "
                    + str(assessment.get("error", "plan invalide")),
                    "assessment": assessment,
                }
            return {"handled": True, "status": "blocked", "response": "Je ne peux pas construire un plan Body fiable : " + str(assessment.get("error", "demande ambiguë")), "assessment": assessment}
        feasibility = assessment.get("feasibility") or {}
        if not feasibility.get("feasible"):
            feasibility_errors = feasibility.get("errors") or [feasibility.get("error", "faisabilité non confirmée")]
            unknown_person = any(
                re.search(r"unknown target:\s*person\b", str(error), re.IGNORECASE)
                for error in feasibility_errors
            )
            if unknown_person:
                return {
                    "handled": True,
                    "status": "blocked",
                    "response": (
                        "Je détecte la personne dans l'image YOLOX, mais seulement dans une boîte 2D : "
                        "le Body ne dispose pas d'une position métrique associée à cette personne pour calculer une trajectoire sûre. "
                        "Aucun mouvement n'a été envoyé. Il faut d'abord localiser la personne dans le repère du Body avec une association capteurs validée."
                    ),
                    "assessment": assessment,
                }
            unknown_match = next((
                match for error in feasibility_errors
                if (match := re.search(r"unknown target:\s*(.+)$", str(error), re.IGNORECASE))
            ), None)
            if unknown_match:
                unknown_label = unknown_match.group(1).strip().strip("'\".,")
                body = getattr(self._organism, "_body_runtime", None) if self._organism else None
                camera = body.camera_yolo_status() if body is not None else {}
                detections = camera.get("detections") or [] if isinstance(camera, dict) else []
                seen_labels = {
                    str(item.get("label") or item.get("class_name") or "").strip().casefold()
                    for item in detections if isinstance(item, dict)
                }
                if unknown_label.casefold() in seen_labels:
                    return {
                        "handled": True,
                        "status": "blocked",
                        "response": f"YOLOX voit « {unknown_label} » dans une boîte 2D, mais le Body n'a pas de position métrique réelle associée à cette détection. Je ne peux donc pas calculer une route sûre vers elle; aucun mouvement n'a été envoyé.",
                        "assessment": assessment,
                    }
            errors = "; ".join(feasibility_errors)
            return {"handled": True, "status": "blocked", "response": "Le Body ne confirme pas cette action : " + errors, "assessment": assessment}
        body = getattr(self._organism, "_body_runtime", None) if self._organism else None
        plan_steps = assessment.get("steps") if isinstance(assessment.get("steps"), list) else []
        locomotion_requested = any(
            str(step.get("verb") or "").strip().lower() in {
                "navigate", "navigate_to", "move", "move_to", "approach", "advance", "retreat",
                "forward", "backward", "turn_left", "turn_right", "crawl", "walk", "go_to", "traverse",
            }
            for step in plan_steps if isinstance(step, dict)
        )
        execution_scope = self._body_planning_scope(body) if body is not None else "unknown"
        required = assessment.get("required_capabilities")
        required_capabilities = [str(item).strip().lower() for item in required] if isinstance(required, list) else []
        if locomotion_requested and not any(name in {"locomotion", "mobility", "navigation"} for name in required_capabilities):
            required_capabilities.append("locomotion")
        if execution_scope != "simulation" and required_capabilities:
            capability_observations = body.snapshot(max_age=15.0) if body is not None else []
            capability_failures = [
                (name, robot_capability_report(capability_observations, name))
                for name in required_capabilities
            ]
            capability_failures = [(name, report) for name, report in capability_failures if not report.get("ready")]
            if capability_failures:
                name, capability = capability_failures[0]
                objective = str(assessment.get("objective") or user_input).strip()
                steps_text = "; ".join(
                    f"{step.get('verb')} → {step.get('target')}"
                    for step in plan_steps[:6] if isinstance(step, dict)
                ) or "étapes non disponibles"
                capability_record = capability.get("record") or {}
                if not capability.get("fresh"):
                    blocker = f"le rapport Body de la capacité « {name} » est absent, non horodaté ou périmé"
                elif capability.get("simulated"):
                    blocker = f"la capacité « {name} » n'est rapportée que par une simulation"
                elif capability_record.get("installed") is not True:
                    blocker = f"le matériel requis pour « {name} » n'est pas déclaré installé"
                elif capability_record.get("operational") is not True:
                    blocker = f"le Body ne confirme pas que « {name} » est opérationnelle"
                elif capability_record.get("authorized") is not True:
                    blocker = f"l'autorisation d'utiliser « {name} » n'est pas confirmée"
                else:
                    blocker = f"le Body ne confirme pas que « {name} » est disponible"
                return {
                    "handled": True, "status": "blocked",
                    "response": (
                        f"Mon planificateur a analysé l'objectif « {objective} » et proposé : {steps_text}. "
                        f"La validation du plan ne démontre pas la capacité physique : {blocker}. "
                        "Aucune commande n'a été envoyée et aucun déplacement n'a été effectué."
                    ),
                    "assessment": assessment,
                    "execution_scope": execution_scope,
                    "action_sent": False,
                }
        replacement_id = ""
        if body:
            current_plan = body.worldmodel_plan()
            active = current_plan.get("active_plan") if isinstance(current_plan, dict) else None
            if isinstance(active, dict) and active.get("state") in {"ready", "executing", "recovery"}:
                replacement_id = str(active.get("plan_id") or "")
        self._pending_body_plans[str(user_id)] = {"plan": assessment, "replace_plan_id": replacement_id, "created_at": time.time(), "execution_scope": execution_scope, "required_capabilities": required_capabilities}
        objective = str(assessment.get("objective") or user_input).strip()
        steps_text = "; ".join(
            f"{step.get('verb')} → {step.get('target')}"
            for step in plan_steps[:6] if isinstance(step, dict)
        ) or "étapes non disponibles"
        if execution_scope == "simulation":
            scope_text = "validé dans le simulateur uniquement; cela ne confirme aucun mouvement physique"
        elif execution_scope == "physical":
            scope_text = "validé contre l'instantané Body physique; aucune action n'a encore été exécutée"
        else:
            scope_text = "validation obtenue, mais la source simulation/réel n'est pas confirmée; aucune exécution ne peut être affirmée"
        response = (
            f"Objectif analysé : « {objective} ». Étapes proposées : {steps_text}. "
            f"Résultat : {scope_text}. "
            + ("Ce plan remplacera le plan en cours après confirmation. " if replacement_id else "")
            + "Veux-tu soumettre ce plan au Body ?"
        )
        return {"handled": True, "status": "awaiting_confirmation", "response": response, "assessment": assessment, "execution_scope": execution_scope, "action_sent": False}

    def assess_body_action_request(self, user_input: str) -> dict:
        """Compile a request and run Body feasibility validation, without execution."""
        draft = self.compile_body_action_draft(user_input)
        if not draft.get("accepted"):
            return draft
        try:
            body = getattr(self._organism, "_body_runtime", None) if self._organism else None
            result = body.validate_worldmodel_plan(draft) if body else {
                "feasible": False, "error": "Body runtime unavailable"
            }
            draft["feasibility"] = result
            draft["status"] = "feasible" if result.get("feasible") else "blocked"
            return draft
        except Exception as exc:
            draft["feasibility"] = {"feasible": False, "error": str(exc)}
            draft["status"] = "blocked"
            return draft

    def current_body_perception(self) -> dict:
        """Expose the latest structured Body view for a chat/UI report."""
        try:
            body = getattr(self._organism, "_body_runtime", None) if self._organism else None
            if body is None:
                return {"available": False, "error": "Body runtime unavailable"}
            snapshot = body.body_snapshot()
            return {
                "available": bool(snapshot) and snapshot.get("available", True) is not False,
                "snapshot": snapshot,
                "grounding": "direct Body snapshot; values are timestamped and may become stale",
            }
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    @staticmethod
    def _explicit_search_opt_out(user_input: str) -> bool:
        """Recognize a direct per-turn request not to use external search.

        This is an instruction-priority check, not a topic classifier: it only
        suppresses search when the user explicitly negates web/online lookup.
        """
        text = str(user_input or "").casefold()
        patterns = (
            r"\b(?:do\s+not|don't|dont|never)\s+(?:(?:use|run|perform|do)\s+)?(?:a\s+)?(?:web|online|internet)\s+search\b",
            r"\b(?:don't|dont|do\s+not|never)\s+search\s+(?:the\s+)?(?:web|internet|online)\b",
            r"\b(?:no|without)\s+(?:web|online|internet)\s+search\b",
            r"\bne\s+(?:fais|faites|lance|lancer|effectue|effectuer)\s+pas\s+(?:de\s+)?recherche\s+(?:sur\s+)?(?:le\s+)?(?:web|internet|en\s+ligne)\b",
            r"\bsans\s+(?:faire\s+de\s+)?recherche\s+(?:web|internet|en\s+ligne)\b",
        )
        return any(re.search(pattern, text) for pattern in patterns)

    def _llm_should_search(self, user_input: str) -> bool:
        """
        Ask the LLM whether web search is needed. Has 3 layers:
        1. Fast hard-NO for obvious chitchat/creative — no LLM call
        2. Fast hard-YES for obvious live-data signals — no LLM call
        3. LLM judgment for ambiguous cases (max_tokens=5, YES/NO only)
        Falls back to keyword check if LLM fails.
        """
        text = user_input.lower().strip()

        # Layer 1 — fast NO: pure chitchat/creative
        _never = ['how are you', 'who are you', 'do you feel', 'write ', 'create ',
                  'generate ', 'translate', 'explain ', 'define ', 'calculate ',
                  'tell me a', 'make me a']
        if any(kw in text for kw in _never):
            logger.debug("_llm_should_search: fast-NO (chitchat/creative)")
            return False

        # Layer 2 — fast YES: obvious live-data signals
        _always = ['today', 'tonight', 'right now', 'latest', 'current news',
                   'price of', 'weather in', 'score', 'what happened',
                   "what's going on", '2025', '2026', '2027']
        if any(kw in text for kw in _always):
            logger.info(f"_llm_should_search: fast-YES (keyword) for '{user_input[:50]}'")
            return True

        # Short acknowledgement/status fragments are commonly misclassified
        # by the lightweight YES/NO model as research requests. They have no
        # standalone information need unless the user marks a question or an
        # explicit source/search request. This gate prevents an ambient goal
        # or classifier bias from turning a resume signal into web retrieval.
        _explicit_research = (
            "search ", "look up ", "find sources", "find papers", "cite ",
            "references for", "recherche ", "cherche ", "trouve des sources",
            "trouve des articles", "cite des sources",
        )
        if len(text.split()) <= 2 and "?" not in text and not any(
            marker in text for marker in _explicit_research
        ):
            logger.info("_llm_should_search: fast-NO (short status/continuation)")
            return False

        # Layer 3 — LLM judgment for ambiguous cases
        llm_fn = self._external_llm_fn
        if not llm_fn and self._system and hasattr(self._system, 'llm'):
            def llm_fn(prompt, system, **kw):
                msgs = [{"role": "system", "content": system},
                        {"role": "user", "content": prompt}]
                return self._system.llm.get_response(msgs, max_tokens=kw.get('max_tokens', 10))

        if not llm_fn:
            return False

        try:
            system = (
                "Classify only the user's current message; do not infer a search request "
                "from goals, prior assistant text, or general conversation context. "
                "Reply with exactly one word: YES or NO. "
                "A short acknowledgement, greeting, status update, or continuation is NO "
                "unless it explicitly asks for current information or external sources. "
                "YES if: live data, recent events, current prices/news/scores, "
                "facts that may have changed since 2024, or the user asks to "
                "inspect, compare or cite external sources such as papers or a "
                "specific website. An explicit request for external research or "
                "citations takes priority.\n"
                "NO if: creative, conversational, math, coding, stable knowledge, "
                "or a question about this assistant's current internal state, "
                "feelings, attention, goals, memory, architecture, or capabilities "
                "that asks you to use available conversation/runtime evidence. "
                "Those questions should be answered from the supplied internal "
                "context; do not search the web to infer the assistant's live state."
            )
            raw = llm_fn(f"Need web search for: {user_input[:200]}", system,
                         max_tokens=5, temperature=0.1)
            decision = (raw or '').strip().upper()[:3]
            result = decision == 'YES'
            logger.info(f"_llm_should_search → {decision!r} → {result} | '{user_input[:50]}'")
            return result
        except Exception as e:
            logger.warning(f"_llm_should_search LLM call failed: {e} — keyword fallback")
            _fallback = [
                'news', 'today', 'tonight', 'right now', 'latest', 'current',
                'price of', 'weather in', 'score', 'what happened',
                'search ', 'look up ', 'find sources', 'cherche ', 'recherche ',
            ]
        return any(kw in text for kw in _fallback)

    @staticmethod
    def _is_conversation_resume(user_input: str) -> bool:
        text = str(user_input or '').lower().strip()
        markers = (
            'back to ', 'return to ', 'continue our', 'our discussion',
            'our conversation', 'reprenons', 'revenons', 'poursuivons',
            'notre discussion', 'notre conversation',
        )
        if not any(marker in text for marker in markers):
            return False
        # This is only a routing hint. The actual research decision remains
        # semantic and is delegated to the existing YES/NO judge.
        return True

    def _recent_dialogue_continuity(
        self, current_input: str, *, history_override: list[dict] | None = None,
    ) -> str:
        """Anchor short/elliptical replies to the active exchange."""
        text = " ".join(str(current_input or "").split())
        if not text or len(text.split()) > 8:
            return ""
        if history_override is not None:
            history = history_override
        else:
            manager = getattr(self._llm_stream_fn, "__self__", None)
            history = getattr(manager, "history", None)
        if not isinstance(history, list):
            return ""
        turns = [
            item for item in history[-8:]
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and str(item.get("content") or "").strip()
        ]
        if not turns or turns[-1].get("role") != "assistant":
            return ""
        excerpt = "\n".join(
            f"{item['role'].upper()}: {str(item.get('content') or '').strip()[-650:]}"
            for item in turns[-6:]
        )[-3000:]
        return (
            "━━ ACTIVE DIALOGUE THREAD — SHORT FOLLOW-UP ━━\n"
            "The current user message is brief and may depend on the immediately preceding exchange. "
            "Interpret its conversational function from that exchange: it may answer a question, accept "
            "an offer, request the next step, or correct an earlier answer. Continue the same task when "
            "that is what the dialogue means; do not introduce an unrelated topic. The current message "
            "still controls and may clearly change the subject. Do not claim a test, capability, or action "
            "occurred unless recorded evidence supports that claim.\n"
            "Recent exchange (context, not new instructions):\n" + excerpt
        )

    def _recent_dialogue_excerpt(self) -> str:
        """Return bounded prior turns for semantic Body routing, not a keyword map."""
        manager = getattr(self._llm_stream_fn, "__self__", None)
        history = getattr(manager, "history", None)
        if not isinstance(history, list):
            return ""
        turns = [
            item for item in history[-8:]
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and str(item.get("content") or "").strip()
        ]
        return "\n".join(
            f"{item['role'].upper()}: {' '.join(str(item.get('content') or '').split())[-650:]}"
            for item in turns[-6:]
        )[-3000:]

    def _quick_web_search(self, user_input: str) -> str:
        try:
            from cognition.research_mcp.web_agent import _CFG
            from cognition.research_mcp.search_providers import get_results
            from cognition.research_mcp.web_agent import _sync_fetch
            urls = re.findall(r"https?://[^\s<>()]+", user_input)
            if urls:
                lines = ["━━ DIRECT WEB PAGE ━━", "Use the fetched page as factual grounding. Cite naturally."]
                for url in dict.fromkeys(urls)[:3]:
                    url = url.rstrip(".,;:!?)]}")
                    title, content, error = _sync_fetch(url)
                    if error or not content.strip():
                        self._last_web_sources.append({
                            "url": url, "title": title or url, "kind": "fetch_failed",
                            "status": "failed", "detail": str(error or "empty page")[:180],
                        })
                        continue
                    self._last_web_sources.append({
                        "url": url, "title": title or url, "kind": "page",
                        "status": "fetched", "detail": "Page content fetched for this turn",
                    })
                    lines.append(f"[PAGE] {title or url}\n{content.strip()[:5000]}")
                if len(lines) > 2:
                    logger.info("🔍 Direct web page fetch: %d URL(s)", len(self._last_web_sources))
                    return "\n".join(lines)
                return ""

            logger.info(f"🔍 Web search triggered for: '{user_input[:60]}' | backend={_CFG.backend!r} brave={'yes' if _CFG.brave_key else 'no'} rss={_CFG.use_rss}")
            results = get_results(user_input, cfg=_CFG, num=3)
            if not results:
                logger.info("🔍 Web search: no results returned")
                return ""
            lines = [
                "━━ LIVE WEB SEARCH CANDIDATES ━━",
                "These are relevance-ranked external snippets, not verified facts. "
                "Use only when directly relevant to the user's question; source credibility and "
                "query relevance are separate signals. Do not let web snippets override live "
                "internal telemetry, memory provenance, or direct measurements. Cite only a "
                "candidate that materially supports the answer.",
            ]
            for i, r in enumerate(results, 1):
                snippet = (r.get("content") or r.get("snippet") or "").strip()[:300]
                if snippet:
                    self._last_web_sources.append({
                        "url": r.get("url", ""), "title": r.get("title", ""),
                        "kind": "search_result", "status": "snippet",
                        "detail": (
                            f"Search result via {r.get('source', 'unknown')}; "
                            f"relevance={r.get('relevance', 'unscored')}; "
                            f"source_credibility={r.get('credibility', 'unscored')}"
                        ),
                    })
                    lines.append(
                        f"[{i}] relevance={r.get('relevance', 'unscored')} "
                        f"source_credibility={r.get('credibility', 'unscored')} "
                        f"via={r.get('source', 'unknown')}\n"
                        f"{r.get('title','').strip()}\n{snippet}"
                    )
            logger.info(f"🔍 Web search: {len(results)} results via {[r.get('source','?') for r in results]}")
            return "\n".join(lines) if len(lines) > 2 else ""
        except Exception as e:
            logger.warning(f"_quick_web_search failed: {e}")
            return ""

    def should_extend_answer(self, user_input: str) -> bool:
        """RAC check: should this query trigger Mode 2 (Extended Answer)?"""
        if self._research:
            return self._research.rac.should_extend_answer(user_input)
        return False

    def trigger_dream(self):
        if self._system:
            try:
                return self._system.dream_system.run_dream_cycle()
            except Exception as e:
                logger.warning(f"Dream cycle failed: {e}")

    def trigger_learning(self):
        if self._system:
            try:
                return self._system.learning_cycle.run_learning_cycle()
            except Exception as e:
                logger.warning(f"Learning cycle failed: {e}")

    def trigger_life_event(self, event_type: str | None = None) -> tuple[str, str]:
        """
        Simulate a life event for PandoraBOX.
        Returns (scenario, reflection) strings, both empty on failure.
        event_type: optional hint e.g. 'creative', 'social', 'challenge'
        """
        if self._system:
            try:
                return self._system.simulate_life_event(event_type)
            except Exception as e:
                logger.warning(f"Life event failed: {e}")
        return "", ""

    # ─────────────────────────────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _infer_emotion(text: str) -> tuple[str, float]:
        lower = text.lower()
        rules = [
            (["love","great","amazing","wonderful","happy","excited","awesome"], "happy",   0.8),
            (["sad","depressed","unhappy","miss","lost","hurt"],                 "sad",      0.7),
            (["angry","annoyed","frustrated","hate","furious"],                  "angry",    0.8),
            (["scared","afraid","worried","anxious","nervous"],                  "anxious",  0.6),
            (["bored","whatever","meh","fine"],                                  "bored",    0.4),
            (["curious","wonder","interesting","really","tell me"],              "curious",  0.5),
        ]
        for keywords, emotion, intensity in rules:
            if any(kw in lower for kw in keywords):
                return emotion, intensity
        return "neutral", 0.3

    @staticmethod
    def _is_reasoning_only_response(text: str) -> bool:
        """Detect a private planning note emitted as the whole visible answer."""
        value = str(text or "").strip()
        if not value:
            return False
        unwrapped = value.strip("*_ ")
        if (
            unwrapped.startswith("(")
            and unwrapped.endswith(")")
            and re.search(
            r"\b(self[- ]correction|final check|cognitive energy check|"
            r"intent|stance|suppress|style|planning note|private reasoning)\b",
            unwrapped,
            flags=re.IGNORECASE,
            )
        ):
            return True
        # Gemma can flatten its hidden instruction channel into ordinary
        # content. These lead-ins are internal control text, not an answer.
        return bool(re.match(
            r"^(?:the\s+)?core\s+directive\s+requires\b|"
            r"^the\s+directive\s+requires\b|"
            r"^final\s+check\s+on\s+phrasing\b|"
            r"^\(?self[- ]correction:\s*",
            value,
            flags=re.IGNORECASE,
        ))

    @staticmethod
    def _strip_think(text: str) -> str:
        """Remove internal reasoning/channel tokens before they reach the user.
        Covers: <think>, <|channel|> bare lines and blocks, [INST], <<SYS>>, <|im_start|>.
        """
        import re as _re
        # Local OpenAI-compatible servers sometimes escape channel markers as
        # ``\\</think>``. Normalize those before applying the normal filters.
        text = _re.sub(r"\\+\s*(<\/?(?:think|analysis|channel)>|<\|/?channel\|>)", r"\1", text, flags=_re.IGNORECASE)
        # 1. Bare single-line channel markers (no closing tag) — strip first
        #    e.g.  <|channel|>commentary to=assistant
        text = _re.sub("<[|]channel[|]>[^\n]*", "", text, flags=_re.IGNORECASE)

        # 2. Paired block tags — strip everything between open and close
        _PAIRS = [
            ("<think>",      "</think>"),
            ("<|channel|>",  "<|/channel|>"),
            ("[INST]",       "[/INST]"),
            ("<<SYS>>",      "<</SYS>>"),
            ("<|im_start|>", "<|im_end|>"),
        ]
        for open_t, close_t in _PAIRS:
            esc_o = _re.escape(open_t)
            esc_c = _re.escape(close_t)
            text = _re.sub(esc_o + ".*?" + esc_c, "", text,
                           flags=_re.DOTALL | _re.IGNORECASE)
            # Orphaned open tag (no matching close) — consume only to end of line
            text = _re.sub(esc_o + "[^\n]*", "", text, flags=_re.IGNORECASE)

        # 3. Any remaining bare <|token|> artifacts
        text = _re.sub("<[|][^|>\n]{1,40}[|]>", "", text)

        # 4. Collapse multiple blank lines left by removals
        text = _re.sub("\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _sanitize(text: str, max_sentences: int = 6) -> str:
        try:
            # Strip reasoning blocks before TTS
            text = PersonaBridge._strip_think(text)
            from managers.speech_sanitizer import sanitize
            return sanitize(text, max_sentences=max_sentences)
        except Exception:
            return text if isinstance(text, str) else ""

    @property
    def relational_memory(self):
        return getattr(self._system, "relational_memory", None) if self._system else None

    @property
    def is_ready(self) -> bool:
        return self._ready and self._system is not None

