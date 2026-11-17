"""
ThoughtThreadEngine (TTE)
=========================
Converts PandoraBOX's isolated word-chains into persistent, stateful thought
processes — threads that evolve over multiple cycles, accumulate context,
pursue goals, and resolve into memory and identity updates.

The core insight from the diagnosis:
    PandoraBOX produces:  word → likely next word → likely next word
    It should produce: goal → explore → discover → update → resolve

Each ThoughtThread is a cognitive unit that:
  - persists across interaction cycles
  - accumulates evidence and context
  - drives planning and action
  - resolves into memory + identity changes

The TTE step() method is called each slow cycle from InternalThoughtLoop.
The DominantThoughtSelector then picks the highest-priority thread to drive
the next LLM output via CognitivePreProcessor.

Thread lifecycle:
  spawn → advance → [branch] → resolve → archive → [reactivate]

Thread sources:
  - admitted active GoalEngine goals (including user/pressure-derived goals)
  - curiosity signal (passive curiosity → active inquiry)
  - salient vision surprise
  - dissonance detection (CDE injects meta-threads)
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict, fields
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_ACTIVE_THREADS  = 12   # cap to avoid cognitive overload
MAX_HISTORY_ENTRIES = 20   # per thread
THREAD_IDLE_HOURS   = 2.0  # defer threads inactive for this long
MIN_CONFIDENCE      = 0.05 # below this → thread is failed/archived
ACTION_RECEIPT_TTL_SECONDS = 24 * 60 * 60
MAX_PENDING_ACTION_RECEIPTS = 500
PERSISTENCE_PATH    = "data/persona/thought_threads.json"


# ── Enums ─────────────────────────────────────────────────────────────────────

class ThoughtThreadStatus(str, Enum):
    ACTIVE    = "active"
    ENGAGED   = "engaged"    # dominant — being acted upon right now
    DEFERRED  = "deferred"   # paused, may reactivate
    COMPLETED = "completed"
    FAILED    = "failed"
    RETIRED   = "retired"    # gracefully retired after max iterations (Phase 3)


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ThoughtThread:
    id:              str
    topic:           str
    goal:            str
    current_state:   Dict[str, Any]        = field(default_factory=dict)
    history:         List[Dict[str, Any]]  = field(default_factory=list)
    planned_actions: List[str]             = field(default_factory=list)
    memory_refs:     List[str]             = field(default_factory=list)
    confidence:      float                 = 0.50  # neutral prior until outcome evidence arrives
    uncertainty:     float                 = 0.50
    pressure:        Dict[str, float]      = field(default_factory=dict)
    curiosity:       float                 = 0.30
    dissonance:      float                 = 0.0
    energy_cost:     float                 = 10.0
    safety_risk:     float                 = 0.0
    parent_id:       Optional[str]         = None
    children_ids:    List[str]             = field(default_factory=list)
    status:          ThoughtThreadStatus   = ThoughtThreadStatus.ACTIVE
    created_at:      float                 = field(default_factory=time.time)
    last_advanced:   float                 = field(default_factory=time.time)
    source:          str                   = "internal"  # goal_engine / curiosity / vision / dissonance
    # Retained for compatibility with persisted TTE and lifecycle helpers.
    iteration_count: int                   = 0
    source_ref:      str                   = ""          # originating persistent goal, when present

    def age_hours(self) -> float:
        return (time.time() - self.created_at) / 3600.0

    def idle_hours(self) -> float:
        return (time.time() - self.last_advanced) / 3600.0

    def to_prompt_line(self) -> str:
        """Compact representation for injection into system prompt."""
        action = self.planned_actions[0] if self.planned_actions else "none"
        return (
            f"[THREAD:{self.topic}] goal={self.goal!r} "
            f"confidence={self.confidence:.0%} next_action={action!r}"
        )


@dataclass
class TTEContext:
    """Snapshot of global state consumed by the TTE each cycle."""
    metrics:        Dict[str, float]  = field(default_factory=dict)
    identity_state: Dict[str, Any]    = field(default_factory=dict)
    world_state:    Dict[str, Any]    = field(default_factory=dict)
    pressures:      Dict[str, float]  = field(default_factory=dict)
    curiosity_level: float            = 0.30
    energy:         float             = 80.0


# ── Engine ────────────────────────────────────────────────────────────────────

class ThoughtThreadEngine:
    """
    Manages the lifecycle of PandoraBOX's thought threads.

    Wire-up (in InternalThoughtLoop._slow_cycle):
        tte_ctx = ThoughtThreadEngine.collect_context(organism)
        tte.step(tte_ctx)
        dominant = dts.select(threads=tte.active_threads(), ctx=...)
    """

    def __init__(self, persistence_path: str = PERSISTENCE_PATH) -> None:
        self._path     = Path(persistence_path)
        self._receipt_path = self._path.with_name(
            f"{self._path.stem}_action_receipts.json"
        )
        self._threads: Dict[str, ThoughtThread] = {}
        self._pending_action_receipts: Dict[str, List[Dict[str, Any]]] = {}
        self._lock     = threading.RLock()
        self._persistence_batch_depth = 0
        self._persistence_dirty = False
        self._load_pending_action_receipts()
        self._load()
        logger.info(f"[TTE] Initialised — {len(self._threads)} threads loaded")

    # ── Public API ────────────────────────────────────────────────────────────

    def spawn_thread(self, ctx: TTEContext, seed: Dict[str, Any]) -> ThoughtThread:
        """
        Create a new thread from a trigger.
        seed keys: topic, goal, source, curiosity, pressure, planned_actions
        """
        with self._lock:
            # Deduplicate: don't spawn if same topic is already ACTIVE/ENGAGED
            topic = seed.get("topic", "unknown").lower()[:80]
            source_ref = str(seed.get("source_ref") or "")
            for t in self._threads.values():
                if source_ref and t.source_ref == source_ref:
                    if t.status not in (
                        ThoughtThreadStatus.ACTIVE,
                        ThoughtThreadStatus.ENGAGED,
                    ):
                        previous_status = t.status.value
                        t.status = ThoughtThreadStatus.ACTIVE
                        t.current_state["active_goal_reassertion"] = {
                            "reason": "goal_engine_still_active",
                            "previous_thread_status": previous_status,
                            "reactivated_at": time.time(),
                        }
                    # The active GoalEngine record is the authoritative
                    # snapshot for this goal. Refresh its descriptive fields
                    # without discarding accumulated history or action receipts.
                    t.topic = topic
                    t.goal = seed.get("goal", t.goal)
                    t.source = seed.get("source", t.source)
                    t.current_state.update(seed.get("current_state", {}))
                    t.last_advanced = time.time()
                    self._save()
                    return t
                if t.topic.lower() == topic and t.status in (
                    ThoughtThreadStatus.ACTIVE, ThoughtThreadStatus.ENGAGED
                ):
                    if source_ref and not t.source_ref:
                        # Upgrade an existing same-topic thread with the
                        # admitted goal's stable provenance instead of
                        # silently returning an unlinked curiosity thread.
                        t.source_ref = source_ref
                        t.source = seed.get("source", t.source)
                        t.goal = seed.get("goal", t.goal)
                        t.current_state.update(seed.get("current_state", {}))
                        t.last_advanced = time.time()
                        self._save()
                        return t
                    if source_ref and t.source_ref != source_ref:
                        # Two persistent goals may share a topic; their IDs
                        # remain distinct thread sources.
                        continue
                    logger.debug(f"[TTE] Reused existing thread without changing evidence state: {topic!r}")
                    return t

            thread = ThoughtThread(
                id              = uuid.uuid4().hex[:12],
                topic           = topic,
                goal            = seed.get("goal", f"explore {topic}"),
                current_state   = seed.get("current_state", {}),
                curiosity       = seed.get("curiosity", ctx.curiosity_level),
                pressure        = seed.get("pressure", {}),
                energy_cost     = seed.get("energy_cost", 10.0),
                planned_actions = seed.get("planned_actions", ["gather information"]),
                source          = seed.get("source", "internal"),
                source_ref      = source_ref,
            )
            # GoalActionExecutor runs before TTE seeds goal threads in the
            # internal cycle. Fast async actions can therefore finish first.
            # Reattach durable receipts by stable source_ref when the thread
            # appears instead of silently losing their causal evidence.
            pending = self._pending_action_receipts.pop(source_ref, []) if source_ref else []
            if pending:
                thread.current_state["action_receipts"] = pending[-20:]
                thread.current_state["last_action_receipt"] = pending[-1]
                thread.current_state["action_receipt_count"] = len(pending[-20:])
            try:
                thread.confidence = max(0.0, min(1.0, float(seed.get("confidence", 0.5))))
            except (TypeError, ValueError):
                thread.confidence = 0.5
            thread.uncertainty = 1.0 - thread.confidence

            self._threads[thread.id] = thread
            if pending:
                self._save_pending_action_receipts()
            self._save()
            logger.debug(f"[TTE] Spawned thread {thread.id[:8]}: {topic!r} from {thread.source}")
            return thread

    def advance_thread(self, thread: ThoughtThread, ctx: TTEContext) -> ThoughtThread:
        """
        Evolve a thread one step: update state, confidence, history.
        Called by step() for each active thread.
        """
        with self._lock:
            if thread.status not in (ThoughtThreadStatus.ACTIVE, ThoughtThreadStatus.ENGAGED):
                return thread

            # Record history entry
            snapshot = {
                "ts":           time.time(),
                "current_state": dict(thread.current_state),
                "confidence":   thread.confidence,
                "planned_action": thread.planned_actions[0] if thread.planned_actions else None,
                "action_status": "planned_not_executed",
            }
            thread.history.append(snapshot)
            thread.iteration_count = max(thread.iteration_count + 1, len(thread.history))
            if len(thread.history) > MAX_HISTORY_ENTRIES:
                thread.history = thread.history[-MAX_HISTORY_ENTRIES:]

            # A scheduler tick is not evidence that a planned action ran or
            # that the goal advanced. Keep both the plan and confidence
            # unchanged until a caller records an evidenced outcome.
            thread.uncertainty = max(0.0, min(1.0, 1.0 - thread.confidence))
            thread.last_advanced = time.time()

            self._save()
            return thread

    def branch_thread(
        self, thread: ThoughtThread, ctx: TTEContext, sub_goal: str
    ) -> ThoughtThread:
        """Create a child thread for a sub-goal discovered during exploration."""
        child = self.spawn_thread(ctx, {
            "topic":           f"{thread.topic}:{sub_goal[:40]}",
            "goal":            sub_goal,
            "source":          "branch",
            "curiosity":       thread.curiosity * 0.8,
            "pressure":        dict(thread.pressure),
            "energy_cost":     thread.energy_cost * 0.7,
            "planned_actions": ["investigate sub-goal"],
        })
        with self._lock:
            child.parent_id = thread.id
            thread.children_ids.append(child.id)
            self._save()
        logger.debug(f"[TTE] Branched {thread.id[:8]} → child {child.id[:8]}: {sub_goal!r}")
        return child

    def resolve_thread(self, thread: ThoughtThread, ctx: TTEContext, *,
                       success: Optional[bool] = None,
                       evidence_ref: Optional[str] = None,
                       outcome_statement: Optional[str] = None,
                       outcome_confidence: Optional[float] = None) -> ThoughtThread:
        """Resolve only from an explicit outcome receipt; otherwise defer unverified."""
        with self._lock:
            if success is None or not str(evidence_ref or "").strip():
                thread.status = ThoughtThreadStatus.DEFERRED
                thread.current_state["resolution"] = "unverified_no_outcome_receipt"
            elif success:
                thread.status = ThoughtThreadStatus.COMPLETED
                thread.current_state["resolution"] = "verified_success"
            else:
                thread.status = ThoughtThreadStatus.FAILED
                thread.current_state["resolution"] = "verified_failure"
            if evidence_ref:
                thread.current_state["resolution_evidence_ref"] = str(evidence_ref)[:200]
            if (success is not None and evidence_ref and outcome_statement
                    and isinstance(outcome_confidence, (int, float))
                    and not isinstance(outcome_confidence, bool)
                    and 0.0 <= float(outcome_confidence) <= 1.0):
                thread.current_state["verified_outcome"] = {
                    "status": "success" if success else "failure",
                    "belief_statement": str(outcome_statement)[:500],
                    "evidence_ref": str(evidence_ref)[:200],
                    "confidence": float(outcome_confidence),
                }
            thread.current_state["resolved_at"] = time.time()
            self._save()
        logger.debug(f"[TTE] Resolved {thread.id[:8]}: {thread.status.value}")
        return thread

    def record_action_receipt(
        self, goal_id: str, *, action: str, success: bool,
        execution_id: str = "", cycle_id: Optional[int] = None,
        result: str = "", evidence_ref: str = "",
    ) -> int:
        """Attach a completed goal action to its thread without resolving it.

        An action receipt proves that an operation returned a terminal result;
        it does not prove that the thread's broader success criterion was met.
        Keep that distinction explicit and leave confidence/status untouched.
        Returns the number of matched threads (normally zero or one).
        """
        source_ref = str(goal_id or "").strip()[:80]
        action_name = str(action or "").strip()[:48]
        execution_ref = str(execution_id or "").strip()[:100]
        if not source_ref or not action_name or not execution_ref:
            return 0
        receipt = {
            "execution_id": execution_ref,
            "cycle_id": cycle_id if isinstance(cycle_id, int) else None,
            "action": action_name,
            "success": bool(success),
            "result": str(result or "").strip()[:200],
            "evidence_ref": str(evidence_ref or "").strip()[:160],
            "recorded_at": time.time(),
        }
        matched = 0
        with self._lock:
            self._prune_pending_action_receipts_locked()
            for thread in self._threads.values():
                if thread.source_ref != source_ref:
                    continue
                receipts = thread.current_state.get("action_receipts")
                if not isinstance(receipts, list):
                    receipts = []
                if any(
                    isinstance(item, dict)
                    and item.get("execution_id") == execution_ref
                    for item in receipts
                ):
                    matched += 1
                    continue
                receipts.append(receipt)
                thread.current_state["action_receipts"] = receipts[-20:]
                thread.current_state["last_action_receipt"] = receipt
                thread.current_state["action_receipt_count"] = len(receipts[-20:])
                self._save()
                matched += 1
            if not matched:
                pending = self._pending_action_receipts.setdefault(source_ref, [])
                if not any(item.get("execution_id") == execution_ref for item in pending):
                    pending.append(receipt)
                    self._pending_action_receipts[source_ref] = pending[-20:]
                    # Keep the global cache bounded; recently updated source
                    # refs are retained first.
                    while len(self._pending_action_receipts) > MAX_PENDING_ACTION_RECEIPTS:
                        self._pending_action_receipts.pop(next(iter(self._pending_action_receipts)))
                    self._save_pending_action_receipts()
        return matched

    def _prune_pending_action_receipts_locked(self) -> None:
        cutoff = time.time() - ACTION_RECEIPT_TTL_SECONDS
        stale_sources = []
        for source_ref, receipts in self._pending_action_receipts.items():
            fresh = [
                item for item in receipts
                if isinstance(item, dict)
                and float(item.get("recorded_at", 0.0) or 0.0) >= cutoff
            ]
            if fresh:
                self._pending_action_receipts[source_ref] = fresh[-20:]
            else:
                stale_sources.append(source_ref)
        for source_ref in stale_sources:
            self._pending_action_receipts.pop(source_ref, None)

    def _save_pending_action_receipts(self) -> None:
        try:
            self._receipt_path.parent.mkdir(parents=True, exist_ok=True)
            self._receipt_path.write_text(
                json.dumps(self._pending_action_receipts, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("[TTE] Pending action receipt save failed: %s", type(exc).__name__)

    def _load_pending_action_receipts(self) -> None:
        if not self._receipt_path.exists():
            return
        try:
            raw = json.loads(self._receipt_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return
            cutoff = time.time() - ACTION_RECEIPT_TTL_SECONDS
            for source_ref, receipts in raw.items():
                if not isinstance(source_ref, str) or not isinstance(receipts, list):
                    continue
                fresh = [
                    item for item in receipts
                    if isinstance(item, dict)
                    and float(item.get("recorded_at", 0.0) or 0.0) >= cutoff
                ][-20:]
                if fresh:
                    self._pending_action_receipts[source_ref[:80]] = fresh
            self._prune_pending_action_receipts_locked()
        except Exception as exc:
            logger.warning("[TTE] Pending action receipt load failed: %s", type(exc).__name__)

    def step(self, ctx: TTEContext) -> List[ThoughtThread]:
        """
        Main tick — called each slow cycle.
        Returns list of currently active threads after update.
        """
        with self._batched_persistence():
            return self._run_step(ctx)

    def _run_step(self, ctx: TTEContext) -> List[ThoughtThread]:
        """Apply one slow-cycle update; persistence is committed by ``step``."""
        with self._lock:
            threads = list(self._threads.values())

        # ── Auto-correction based on metrics ──────────────────────────────────
        ccs     = ctx.metrics.get("CCS", 0.5)
        energy  = ctx.energy

        for thread in threads:
            if thread.status not in (ThoughtThreadStatus.ACTIVE, ThoughtThreadStatus.ENGAGED):
                continue

            # Defer idle threads
            if thread.idle_hours() > THREAD_IDLE_HOURS:
                with self._lock:
                    thread.status = ThoughtThreadStatus.DEFERRED
                continue

            # Low CCS: don't advance fragile threads — favour focused ones
            if ccs < 0.15 and thread.confidence < 0.4:
                continue

            # Low energy: reduce cost, still advance (reduce intensity, not stop)
            cost_mod = max(0.3, energy / 100.0)
            thread.energy_cost = thread.energy_cost * cost_mod

            self.advance_thread(thread, ctx)

        # ── Seed threads from admitted persistent goals ────────────────────
        # Persistent GoalEngine goals are already admitted, typed, and
        # provenance-bearing cognitive commitments. Feed their active
        # state into the thread/DTS path instead of requiring a separate
        # high-curiosity topic threshold before the executive pipeline can
        # represent any current goal.
        for goal_seed in ctx.world_state.get("goal_threads", []):
            if not isinstance(goal_seed, dict):
                continue
            topic = str(goal_seed.get("topic") or "").strip()
            source_ref = str(goal_seed.get("source_ref") or "").strip()
            if not topic or not source_ref:
                continue
            self.spawn_thread(ctx, {
                "topic": topic,
                "goal": str(goal_seed.get("goal") or topic),
                "source": "goal_engine",
                "source_ref": source_ref,
                "curiosity": float(goal_seed.get("priority", 0.5) or 0.0),
                "pressure": dict(ctx.pressures),
                "energy_cost": 8.0,
                "planned_actions": [
                    "gather evidence relevant to the goal",
                    "evaluate its stated success criteria",
                    "update goal progress from observed results",
                ],
                "current_state": {
                    "goal_priority": float(goal_seed.get("priority", 0.5) or 0.0),
                    "goal_intent_kind": str(goal_seed.get("intent_kind") or "learn"),
                    "success_criteria": str(goal_seed.get("success_criteria") or ""),
                    "source_turn_id": str(goal_seed.get("source_turn_id") or ""),
                    "source_thought_id": str(goal_seed.get("source_thought_id") or ""),
                },
            })

        # ── Spawn from curiosity with Goal Fitness scoring ─────────────────
        # Gemini insight: goal spawning should be weighted by drive alignment
        # AND tension relief, not just curiosity level. High-pressure topics
        # score higher and take priority.
        if energy > 20.0 and ctx.curiosity_level > 0.3:
            curiosity_topic = ctx.world_state.get("top_curiosity_topic")
            if curiosity_topic:
                # Goal Fitness = drive_alignment * 0.5 + tension_relief * 0.5
                # drive_alignment: curiosity level (how much organism wants this)
                # tension_relief: how much spawning this thread reduces dominant pressure
                dominant_pressure = max(ctx.pressures.values()) if ctx.pressures else 0.3
                tension_relief    = min(1.0, dominant_pressure * 1.5)
                goal_fitness      = (ctx.curiosity_level * 0.5) + (tension_relief * 0.5)

                # Only spawn if fitness clears threshold — prevents low-value spam
                if goal_fitness > 0.35:
                    # Guard: reject noise topics before spawning a thread.
                    # Topics like "statement", "question", "verbe" survive
                    # curiosity_engine's IDF filter (low df in small corpora)
                    # but produce deferred threads that never resolve.
                    _topic_ok = True
                    if len(curiosity_topic) < 4:
                        _topic_ok = False  # too short to be meaningful
                    elif curiosity_topic in {
                        "statement", "question", "answer", "exploration",
                        "uncertainty", "verbe", "verb", "noun", "word",
                        "thing", "something", "nothing", "feeling",
                        "emotion", "thought", "response", "sentence",
                        "continue", "continue...", "conversation",
                    }:
                        _topic_ok = False  # grammatical noise
                    elif len([t for t in self._threads.values()
                              if t.topic == curiosity_topic
                              and t.status.value == "deferred"]) >= 3:
                        _topic_ok = False  # deferred 3+ times — give up
                    if _topic_ok:
                        self.spawn_thread(ctx, {
                            "topic":           curiosity_topic,
                            "goal":            f"explore and understand: {curiosity_topic}",
                            "source":          "curiosity",
                            "curiosity":       ctx.curiosity_level,
                            "energy_cost":     max(5.0, 15.0 * (1.0 - goal_fitness)),
                            "planned_actions": ["research topic", "synthesize findings",
                                               "update world model", "resolve tension"],
                            "current_state":   {"goal_priority": goal_fitness},
                        })

        # ── Spawn from vision surprise if available ────────────────────────
        # Gemini insight: sensory surprise should spawn a thought thread,
        # not just broadcast to GW. Vision events that are novel/salient
        # become "Perceptual Threads" with their own goal and history.
        vision_surprise = ctx.world_state.get("vision_surprise")
        if vision_surprise and energy > 25.0:
            salience = vision_surprise.get("salience", 0.0)
            if salience > 0.6:
                self.spawn_thread(ctx, {
                    "topic":           f"visual_observation:{vision_surprise.get('summary','unknown')[:40]}",
                    "goal":            f"understand what was observed: {vision_surprise.get('summary','unknown')[:60]}",
                    "source":          "sensory_bridge",
                    "curiosity":       salience,
                    "energy_cost":     8.0,
                    "planned_actions": ["analyze observation", "link to known context", "update world model"],
                })
                ctx.world_state.pop("vision_surprise", None)  # consume event

        # ── Prune: cap at MAX_ACTIVE_THREADS ──────────────────────────────────
        with self._lock:
            active = [t for t in self._threads.values()
                      if t.status in (ThoughtThreadStatus.ACTIVE, ThoughtThreadStatus.ENGAGED)]
            if len(active) > MAX_ACTIVE_THREADS:
                # Archive lowest-confidence surplus
                active.sort(key=lambda t: t.confidence)
                for t in active[: len(active) - MAX_ACTIVE_THREADS]:
                    t.status = ThoughtThreadStatus.DEFERRED
            self._save()

        return self.active_threads()

    def active_threads(self) -> List[ThoughtThread]:
        with self._lock:
            return [
                t for t in self._threads.values()
                if t.status in (ThoughtThreadStatus.ACTIVE, ThoughtThreadStatus.ENGAGED)
            ]

    def all_threads(self) -> List[ThoughtThread]:
        with self._lock:
            return list(self._threads.values())

    def get_thread(self, thread_id: str) -> Optional[ThoughtThread]:
        with self._lock:
            return self._threads.get(thread_id)

    @staticmethod
    def collect_context(organism: Any) -> TTEContext:
        """
        Collect a TTEContext from the live organism object.
        Safe: any missing attribute returns a sensible default.
        """
        ctx = TTEContext()
        try:
            obs = getattr(organism, "observatory", None)
            if obs:
                snap = obs.snapshot()
                ctx.metrics = {
                    "CCS": snap.get("CCS", snap.get("cognitive_coherence", 0.5)),
                    "GEI": snap.get("GEI", snap.get("goal_engagement", 0.3)),
                    "IDX": snap.get("IDX", snap.get("identity_index", 0.5)),
                    "STR": snap.get("STR", snap.get("strangeness", 0.4)),
                }
        except Exception:
            pass
        try:
            ctx.energy = organism.energy.level() if hasattr(organism, "energy") else 80.0
        except Exception:
            pass
        try:
            pressure_sys = getattr(organism, "pressure", None)
            if pressure_sys:
                ctx.pressures = {
                    k: getattr(r, "level", 0.0)
                    for k, r in getattr(pressure_sys, "reservoirs", {}).items()
                }
        except Exception:
            pass
        try:
            curiosity = getattr(organism, "curiosity", None)
            if curiosity:
                ctx.curiosity_level = getattr(curiosity, "_global", 0.3)
                top = curiosity.top_topic()
                if top:
                    ctx.world_state["top_curiosity_topic"] = top
        except Exception:
            pass

        # GoalEngine is the canonical source of persistent active goals.
        # Keep the bridge read-only and carry existing IDs/provenance; the
        # TTE consumes only goals that have already passed GoalEngine's own
        # admission and activation rules.
        try:
            ai_system = getattr(organism, "ai_system", None)
            goal_engine = getattr(ai_system, "goal_engine", None)
            if goal_engine and hasattr(goal_engine, "get_active_goals"):
                active_goals = goal_engine.get_active_goals() or []
                ctx.world_state["goal_threads"] = [
                    {
                        "source_ref": str(getattr(goal, "id", "") or ""),
                        "topic": str(getattr(goal, "topic", "") or ""),
                        "goal": str(getattr(goal, "desired_effect", "") or getattr(goal, "topic", "") or ""),
                        "priority": float(getattr(goal, "priority", 0.5) or 0.0),
                        "intent_kind": str(getattr(goal, "intent_kind", "learn") or "learn"),
                        "success_criteria": str(getattr(goal, "success_criteria", "") or ""),
                        "source_turn_id": str(getattr(goal, "source_turn_id", "") or ""),
                        "source_thought_id": str(getattr(goal, "source_thought_id", "") or ""),
                    }
                    for goal in active_goals
                    if getattr(goal, "id", None) and getattr(goal, "topic", None)
                ]
        except Exception as e:
            logger.debug("[TTE] Active GoalEngine context unavailable: %s", e)

        # ── Vision surprise → sensory bridge signal ──────────────────────────
        # If the GW has a recent high-priority ambient_vision item that is novel,
        # package it as a vision_surprise for TTE to spawn a perceptual thread.
        try:
            ws = getattr(organism, "workspace", None)
            if ws:
                recent_gw = ws.recent(8)
                for item in reversed(recent_gw):
                    src = getattr(item, "source", "")
                    pri = getattr(item, "priority", 0.0)
                    if src == "ambient_vision" and pri >= 0.50:
                        content = str(getattr(item, "content", ""))
                        # Salience from priority (ambient vision is capped at 0.28 normally,
                        # so anything >= 0.50 is a genuine surprise from the event bus)
                        ctx.world_state["vision_surprise"] = {
                            "salience": min(1.0, pri * 1.5),
                            "summary":  content[:80],
                        }
                        break
        except Exception:
            pass

        return ctx

    # ── Persistence ───────────────────────────────────────────────────────────

    @contextmanager
    def _batched_persistence(self):
        """Persist the complete step once, after its in-memory updates finish."""
        with self._lock:
            self._persistence_batch_depth += 1
        try:
            yield
        finally:
            with self._lock:
                self._persistence_batch_depth = max(0, self._persistence_batch_depth - 1)
                if self._persistence_batch_depth == 0 and self._persistence_dirty:
                    self._persistence_dirty = False
                    try:
                        self._write_snapshot_locked()
                    except Exception as exc:
                        self._persistence_dirty = True
                        logger.debug("[TTE] Batched save error: %s", exc)

    def _save(self) -> None:
        try:
            with self._lock:
                if self._persistence_batch_depth:
                    self._persistence_dirty = True
                    return
                self._write_snapshot_locked()
                self._persistence_dirty = False
        except Exception as e:
            logger.debug(f"[TTE] Save error: {e}")

    def _write_snapshot_locked(self) -> None:
        """Atomically write a consistent snapshot while the thread lock is held."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            tid: {**asdict(t), "status": t.status.value}
            for tid, t in self._threads.items()
        }
        temporary_path = self._path.with_name(f"{self._path.name}.tmp")
        temporary_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(temporary_path, self._path)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("thought-thread store must be an object")
            known_fields = {item.name for item in fields(ThoughtThread)}
            loaded = 0
            rejected = 0
            for tid, raw_thread in data.items():
                if not isinstance(raw_thread, dict):
                    rejected += 1
                    continue
                try:
                    thread_data = {key: value for key, value in raw_thread.items()
                                   if key in known_fields}
                    thread_data.setdefault("id", tid)
                    thread_data["status"] = ThoughtThreadStatus(
                        thread_data.get("status", "active")
                    )
                    self._threads[tid] = ThoughtThread(**thread_data)
                    loaded += 1
                except Exception as item_error:
                    rejected += 1
                    logger.warning("[TTE] Skipping invalid thread %s: %s", tid, item_error)
            # Only keep non-completed threads
            self._threads = {
                tid: t for tid, t in self._threads.items()
                if t.status not in (ThoughtThreadStatus.COMPLETED, ThoughtThreadStatus.FAILED)
            }
            if rejected:
                logger.warning(
                    "[TTE] Loaded %d valid thread(s); skipped %d invalid record(s)",
                    loaded, rejected,
                )
        except Exception as e:
            logger.warning(f"[TTE] Load error (starting fresh): {e}")
