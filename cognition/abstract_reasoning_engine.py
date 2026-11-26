"""
cognition/abstract_reasoning_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abstract Reasoning Engine (ARE) — PandoraBOX's second priority skill.

Fills the gap between "reasoning about internal state" (existing) and
"reasoning with abstract concepts outward" (this module).

What it does per applicable conversation turn:
  One structured inference jointly decomposes the concept, maps an analogy,
  and synthesizes an insight from semantic memory + world model context.

Side effects:
  → open_question      planted as curiosity seed in CuriosityEngine
  → analogy chain      stored in SemanticMemory as new concept

Activation:
  ARE only fires when the topic is abstract / conceptual.
  Semantic embedding route shared with the goal-means intent pass.
  Skips when LLM scheduler is busy (returns cached result or None).

Prompt injection:
  get_reasoning_fragment(user_id) → string injected into system prompt
  Concise — 2-4 lines — not a full chain-of-thought dump.

Public API:
  are = AbstractReasoningEngine(organism, llm, memory)
  result = are.reason(user_id, user_text)    # call before response
  frag   = are.get_reasoning_fragment(user_id)
  are.record_outcome(user_id, ai_response)   # call after response

Design principles:
  • Does NOT replace the InnerMonologueEngine two-pass.
    ARE feeds INTO the system prompt; IME shapes the expression pass.
  • LLM calls are bare (no history pollution).
  • If the provider is busy, defer cleanly without inventing a substitute insight.
  • Uses at most one LLM call per reasoning result.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ARE_COOLDOWN_S             = 30  # min seconds between full LLM ARE runs per user


@dataclass
class ReasoningResult:
    """Output of one full ARE run."""
    user_id:        str
    timestamp:      float = field(default_factory=time.time)

    # Pass 1 — Decomposition
    components:     List[str] = field(default_factory=list)
    core_concept:   str       = ""

    # Pass 2 — Analogy mapping
    best_analogy:   str       = ""
    analogy_domain: str       = ""
    analogy_confidence: float = 0.0

    # Pass 3 — Synthesis
    derived_insight: str      = ""
    open_question:   str      = ""
    # Historical name retained for compatibility; these are analogy/source
    # strings, not a causal assertion. ARE never persists them as causality.
    causal_pair:     Tuple[str, str] = ("", "")

    # Meta
    method:         str       = "unavailable"
    abstract_score: float     = 0.0            # uncalibrated semantic cosine; not a probability
    prompt_fragment: str      = ""
    llm_call_count: int       = 0
    reason_code:    str       = ""
    completion_status: str    = "unverified"
    completion_verified: bool = False


class AbstractReasoningEngine:
    """
    Structured abstract reasoning: Decompose → Map → Synthesize.

    Feeds open questions into CuriosityEngine and analogies into SemanticMemory.
    Injects a concise reasoning fragment into the system prompt.
    """

    def __init__(
        self,
        organism:       Any,
        llm:            Any,
        memory:         Any = None,   # MemoryManager
    ):
        self._org    = organism
        self._llm    = llm
        self._mem    = memory
        self._lock   = threading.Lock()
        self._cache: Dict[str, ReasoningResult] = {}   # user_id → last result
        self._continuity_cache: Dict[str, ReasoningResult] = {}
        self._last_run: Dict[str, float] = {}           # user_id → timestamp
        self._last_input: Dict[str, str] = {}            # prevents cross-topic reuse

        # Domain analogy library — pairs (domain, structural pattern)
        # PandoraBOX draws from these when mapping abstract concepts
        self._analogy_seeds = [
            ("chess",          "strategic evaluation + lookahead under uncertainty"),
            ("evolution",      "selection pressure on variants over time"),
            ("thermodynamics", "energy gradient → flow → equilibrium"),
            ("ecology",        "niche competition + symbiosis + carrying capacity"),
            ("music",          "tension → resolution → motif development"),
            ("immune system",  "pattern recognition + tolerance + response amplification"),
            ("rivers",         "path of least resistance + erosion feedback"),
            ("language",       "combinatorial rules generating infinite expression"),
            ("markets",        "distributed signal aggregation + feedback loops"),
            ("crystallization","local order emerging from global chaos"),
        ]

        logger.info("🧠 AbstractReasoningEngine initialised")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Primary public API
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def reason(
        self, user_id: str, user_text: str, *, allow_interactive_turn: bool = False,
        semantic_gate: Optional[Dict[str, Any]] = None,
    ) -> Optional[ReasoningResult]:
        """
        Run abstract reasoning on user_text if the topic warrants it.
        Returns None if the text is not abstract enough to trigger ARE.
        Background calls defer during a live turn. An explicitly authorized
        foreground analysis uses the manager's bounded interactive path.
        """
        # ── Semantic abstractness check ─────────────────────────────────────
        # The normal chat path passes the semantic classification it already
        # computed for this turn, avoiding a second embedding request. Direct
        # callers use the same shared semantic router. No language-specific
        # keyword list or extra LLM classification call is involved.
        abstract_score = self._score_abstractness(user_text, semantic_gate=semantic_gate)
        if abstract_score < 0.3:
            # Preserve the prior insight for conversational continuity, but
            # remove it from the current-turn slot so it cannot masquerade as
            # analysis of this new practical or concrete message.
            with self._lock:
                previous = self._cache.pop(user_id, None)
                if previous is not None:
                    self._continuity_cache[user_id] = previous
            return None

        # ── Cooldown check ────────────────────────────────────────────────
        now = time.time()
        with self._lock:
            last = self._last_run.get(user_id, 0.0)
            last_input = self._last_input.get(user_id, "")
        if now - last < ARE_COOLDOWN_S:
            if " ".join(user_text.casefold().split()) == last_input:
                with self._lock:
                    result = self._cache.get(user_id) or self._continuity_cache.get(user_id)
                    if result is not None:
                        self._cache[user_id] = result
                    return result
            # Do not spend another LLM call or invent a keyword-selected
            # analogy during cooldown. Preserve the prior result as continuity.
            with self._lock:
                previous = self._cache.pop(user_id, None)
                if previous is not None:
                    self._continuity_cache[user_id] = previous
            return self._deferred_result(user_id, abstract_score, "per_user_cooldown")

        # ── Try LLM run ───────────────────────────────────────────────────
        result = None
        defer_reason = "provider_busy_or_unavailable"
        try:
            from core.llm_scheduler import llm_scheduler
            if llm_scheduler.is_busy() and not allow_interactive_turn:
                defer_reason = "llm_scheduler_busy"
            elif self._llm:
                result = self._llm_reason(
                    user_id, user_text, abstract_score,
                    allow_interactive_turn=allow_interactive_turn,
                )
                if result is None:
                    with self._lock:
                        previous = self._cache.pop(user_id, None)
                        if previous is not None:
                            self._continuity_cache[user_id] = previous
                    return self._deferred_result(user_id, abstract_score, "inference_unavailable")
                if result.method != "llm":
                    with self._lock:
                        previous = self._cache.pop(user_id, None)
                        if previous is not None:
                            self._continuity_cache[user_id] = previous
                        if result.method in {"failed", "unverified"}:
                            # Suppress repeated malformed/truncated calls during
                            # the normal per-user cooldown. Do not mark the new
                            # input as successfully analyzed.
                            self._last_run[user_id] = now
                            # The previous successful input may have been the
                            # same text. Clear its cache key so the exact-input
                            # cooldown path cannot resurrect that stale result
                            # as if it belonged to this failed analysis.
                            self._last_input.pop(user_id, None)
                    return result
            else:
                defer_reason = "llm_unavailable"
        except Exception:
            defer_reason = "reasoning_exception"

        if result is None:
            with self._lock:
                previous = self._cache.pop(user_id, None)
                if previous is not None:
                    self._continuity_cache[user_id] = previous
            return self._deferred_result(user_id, abstract_score, defer_reason)

        # ── Side effects ──────────────────────────────────────────────────
        self._apply_side_effects(result)

        # ── Cache ─────────────────────────────────────────────────────────
        with self._lock:
            previous = self._cache.get(user_id)
            if previous is not None:
                self._continuity_cache[user_id] = previous
            self._cache[user_id]    = result
            self._last_run[user_id] = now
            self._last_input[user_id] = " ".join(user_text.casefold().split())

        logger.debug(
            f"🧠 ARE [{result.method}] score={abstract_score:.2f} "
            f"concept={result.core_concept!r} "
            f"analogy={result.best_analogy[:40]!r}"
        )
        return result

    def get_reasoning_fragment(self, user_id: str) -> str:
        """
        Return current reasoning plus explicitly subordinate prior context.
        """
        with self._lock:
            result = self._cache.get(user_id)
            previous = self._continuity_cache.get(user_id)
        now = time.time()
        parts = []
        if result and result.prompt_fragment and now - result.timestamp <= 30:
            parts.append(result.prompt_fragment)
        if previous and previous is not result and now - previous.timestamp <= 120:
            parts.append(
                "[Previous-turn abstract context - continuity only]\n"
                f"{previous.prompt_fragment}\n"
                "Use this only where it remains directly relevant. It must not "
                "replace or override the current message's primary goal, facts, "
                "or material prerequisites."
            )
        return "\n".join(parts)

    def record_outcome(self, user_id: str, ai_response: str) -> Dict[str, Any]:
        """
        Post-turn feedback. Check if the response actually used the insight.
        Strengthens or weakens the causal belief accordingly.
        """
        with self._lock:
            result = self._cache.get(user_id)
        if not result:
            return {"status": "skipped_no_current_result", "beliefs_updated": 0}
        if not result.causal_pair or not result.causal_pair[0] or not result.causal_pair[1]:
            return {"status": "skipped_no_causal_pair", "beliefs_updated": 0}
        # Repetition in the generated answer is not independent evidence for
        # the causal claim. Do not reinforce a belief from the LLM echoing its
        # own insight; keep the causal record unchanged until an external or
        # otherwise independent outcome signal is available.
        return {
            "status": "skipped_no_independent_outcome_evidence",
            "beliefs_updated": 0,
            "causal_pair_available": True,
        }

    @staticmethod
    def _deferred_result(user_id: str, abstract_score: float, reason_code: str) -> ReasoningResult:
        """Represent a skipped inference without fabricating semantic content."""
        return ReasoningResult(
            user_id=user_id,
            method="deferred",
            abstract_score=abstract_score,
            prompt_fragment="",
            reason_code=reason_code[:64],
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Semantic abstractness routing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _score_abstractness(
        self, text: str, *, semantic_gate: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Return semantic-router cosine only for a selected abstract turn.

        This is an uncalibrated routing similarity, not a probability or a
        measure of reasoning quality. The router returns ``skip`` when its
        embedding evidence is uncertain or unavailable.
        """
        if semantic_gate is None:
            try:
                from cognition.goal_means_reasoning import classify_goal_means_intent
                semantic_gate = classify_goal_means_intent(text).get("abstract_reasoning")
            except Exception:
                semantic_gate = None
        if not isinstance(semantic_gate, dict) or semantic_gate.get("route") != "analyze":
            return 0.0
        try:
            return max(0.0, min(1.0, float(semantic_gate.get("positive_similarity", 0.0))))
        except (TypeError, ValueError):
            return 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Single-call structured reasoning
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _llm_reason(
        self, user_id: str, text: str, abstract_score: float, *,
        allow_interactive_turn: bool = False,
    ) -> Optional[ReasoningResult]:
        """
        Run one structured, history-free inference for all reasoning fields.
        Returns an explicit deferred/failed result when no usable inference
        can be attributed to this analysis attempt.
        """
        try:
            # ── Retrieve semantic memory context ─────────────────────────────
            mem_context = ""
            if self._mem and hasattr(self._mem, "get_context"):
                mem_context = self._mem.get_context(text, top_k=3)

            # ── World model causal context ────────────────────────────────────
            wm_context = ""
            try:
                wm = getattr(self._org, "world_model", None)
                if wm and hasattr(wm, "prompt_fragment"):
                    wm_context = wm.prompt_fragment()
            except Exception:
                pass

            seed_list = "\n".join(
                f"  {domain}: {pattern}"
                for domain, pattern in self._analogy_seeds
            )
            prompt = f"""Analyze this abstract/conceptual message in one pass. Keep every claim tied to the message and supplied context; an analogy is illustrative, not evidence of causality.

Message: "{text}"
Semantic memory context: {mem_context[:500] if mem_context else 'none'}
World model context: {wm_context[:300] if wm_context else 'none'}
Candidate analogy domains and patterns:
{seed_list}

Return only one JSON object with all of these fields:
{{
  "core_concept": "central idea in 1-5 words",
  "components": ["up to four structural components"],
  "best_analogy_domain": "best fitting listed or new domain",
  "structural_mapping": "brief analogy mapping, or empty if none fits",
  "confidence": 0.0,
  "derived_insight": "one grounded insight, or empty if none follows",
  "open_question": "one useful unresolved question, or empty",
  "causal_antecedent": "empty unless the message/context provides causal evidence",
  "causal_consequent": "empty unless the message/context provides causal evidence",
  "prompt_note": "one concise response consideration, or empty"
}}"""

            generate_result = getattr(self._llm, "generate_bare_result", None)
            if callable(generate_result):
                completion = generate_result(
                    prompt, max_tokens=420, temperature=0.35,
                    _allow_interactive_turn=allow_interactive_turn,
                )
                completion = completion if isinstance(completion, dict) else {}
                completion_status = str(completion.get("status") or "unverified").strip().casefold()
                completion_verified = completion.get("completion_verified") is True
                call_count = max(0, int(completion.get("provider_call_count", 1)))
                if completion_status == "deferred":
                    call_count = 0
                    return self._deferred_result(
                        user_id, abstract_score,
                        str(completion.get("reason") or "provider_deferred"),
                    )
                if completion_status != "ok" or not completion_verified:
                    result_method = (
                        "failed" if completion_status in {"error", "empty"}
                        else "unverified"
                    )
                    return ReasoningResult(
                        user_id=user_id, method=result_method, abstract_score=abstract_score,
                        reason_code=(
                            completion_status[:64] if completion_status != "ok"
                            else "provider_completion_unverified"
                        ),
                        llm_call_count=call_count,
                        completion_status=completion_status,
                        completion_verified=False,
                    )
                raw = str(completion.get("text") or "")
            else:
                # A legacy string-only provider cannot prove that its response
                # completed normally. Do not spend an inference call whose
                # result cannot be distinguished from a truncated response.
                return ReasoningResult(
                    user_id=user_id, method="unverified", abstract_score=abstract_score,
                    reason_code="completion_evidence_unavailable",
                    llm_call_count=0,
                    completion_status="unverified",
                    completion_verified=False,
                )
            if not raw.strip():
                return ReasoningResult(
                    user_id=user_id, method="failed", abstract_score=abstract_score,
                    reason_code="empty_provider_output", llm_call_count=call_count,
                )
            raw = re.sub(r"```json|```", "", raw).strip()
            result_data = json.loads(raw)

            core_concept = str(result_data.get("core_concept", "") or "")[:120]
            components = result_data.get("components", [])
            if not isinstance(components, list):
                components = []
            components = [str(item)[:120] for item in components[:4] if item]
            best_analogy = str(result_data.get("structural_mapping", "") or "")[:600]
            analogy_domain = str(result_data.get("best_analogy_domain", "") or "")[:120]
            try:
                analogy_confidence = max(0.0, min(1.0, float(result_data.get("confidence", 0.0))))
            except (TypeError, ValueError):
                analogy_confidence = 0.0
            derived_insight = str(result_data.get("derived_insight", "") or "")[:600]
            open_question = str(result_data.get("open_question", "") or "")[:400]
            causal_pair     = (
                str(result_data.get("causal_antecedent", "") or "")[:80],
                str(result_data.get("causal_consequent", "") or "")[:80],
            )
            prompt_note = str(result_data.get("prompt_note", "") or "")[:300]

            # ── Build prompt fragment ─────────────────────────────────────────
            fragment = self._build_fragment(
                core_concept, best_analogy, analogy_domain,
                derived_insight, open_question, prompt_note
            )

            return ReasoningResult(
                user_id            = user_id,
                components         = components,
                core_concept       = core_concept,
                best_analogy       = best_analogy,
                analogy_domain     = analogy_domain,
                analogy_confidence = analogy_confidence,
                derived_insight    = derived_insight,
                open_question      = open_question,
                causal_pair        = causal_pair,
                method             = "llm",
                abstract_score     = abstract_score,
                prompt_fragment    = fragment,
                llm_call_count     = call_count,
                completion_status  = completion_status,
                completion_verified=True,
            )

        except Exception as e:
            logger.debug(f"ARE LLM pass failed: {e}")
            return ReasoningResult(
                user_id=user_id, method="failed", abstract_score=abstract_score,
                reason_code=type(e).__name__[:64],
                llm_call_count=1 if "call_count" not in locals() else call_count,
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Side effects — WorldModel, CuriosityEngine, SemanticMemory
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _apply_side_effects(self, result: ReasoningResult) -> None:
        """
        Feed reasoning results back into the cognitive architecture.
        All calls are best-effort — never raise.
        """
        if result.method != "llm":
            return

        # An analogy pair is a conceptual link, not evidence that one item
        # causes the other. The analogy is persisted below in SemanticMemory;
        # do not promote it into the WorldModel's causal store.

        # ── CuriosityEngine: plant open question as curiosity seed ─────────
        try:
            if result.open_question:
                ce = getattr(self._org, "curiosity_engine", None)
                if ce and hasattr(ce, "plant_question"):
                    ce.plant_question(result.open_question, priority=0.6)
                elif ce and hasattr(ce, "add_question"):
                    ce.add_question(result.open_question)
                logger.debug(f"🧠 ARE → Curiosity: {result.open_question!r}")
        except Exception:
            pass

        # ── SemanticMemory: store analogy as new concept link ─────────────
        try:
            if result.best_analogy and result.core_concept:
                sm = getattr(self._org, "semantic_memory", None)
                if sm and hasattr(sm, "add_concept"):
                    sm.add_concept(
                        name        = result.core_concept,
                        description = result.best_analogy,
                        source      = f"analogy:{result.analogy_domain}",
                    )
                logger.debug(
                    f"🧠 ARE → SemanticMemory: {result.core_concept!r} "
                    f"via {result.analogy_domain}"
                )
        except Exception:
            pass

        # ── Memory: add derived insight as episodic trace ─────────────────
        try:
            if result.derived_insight and self._mem and hasattr(self._mem, "add_memory"):
                self._mem.add_memory(
                    f"[ARE insight] {result.derived_insight}",
                    metadata={"role": "sys", "source": "abstract_reasoning"},
                )
        except Exception:
            pass

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Prompt fragment builder
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _build_fragment(
        core_concept:    str,
        analogy:         str,
        analogy_domain:  str,
        derived_insight: str,
        open_question:   str,
        prompt_note:     str,
    ) -> str:
        """
        Build a concise prompt fragment — 3-4 lines max.
        Not a chain-of-thought dump. Informs without overwhelming.
        """
        lines = [f"[Abstract reasoning: concept='{core_concept}'"]

        if analogy_domain and analogy:
            short_analogy = analogy[:80] + ("…" if len(analogy) > 80 else "")
            lines.append(f" Analogy→{analogy_domain}: {short_analogy}")

        if derived_insight:
            short_insight = derived_insight[:100] + ("…" if len(derived_insight) > 100 else "")
            lines.append(f" Derived: {short_insight}")

        if open_question:
            lines.append(f" Open: {open_question[:80]}")

        if prompt_note:
            lines.append(f" Note: {prompt_note[:80]}")

        lines.append("]")
        return "\n".join(lines)
