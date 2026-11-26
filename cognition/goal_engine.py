"""
Goal Engine — Autonomous Goal Formation System
==============================================
Transforms Identity + Memory + Pressures into persistent internal goals.

This module addresses the fundamental gap: PandoraBOX has curiosity and identity,
but no goal persistence. The organism explores but doesn't pursue.

Architecture:
    Identity traits → Motivations → Goal candidates → Persistent goals

Key concepts:
    - Motivation: General drive (e.g., "explore", "understand_user")
    - Goal: Specific topic + priority + persistence (e.g., "understand quantum computing")
    - Persistence: Goals survive multiple cycles (not just one-shot impulses)

Integration with PandoraBOX:
    - Reads: Identity (traits, values), Pressures (epistemic, identity), Semantic Memory (topics)
    - Writes: Goals (persistent state), Observatory metrics (GEI)
    - Interacts: Global Workspace (injects goal-driven thoughts)

Goal lifecycle:
    1. derive_motivations() — Identity traits → Motivations
    2. generate_candidates() — Motivations × Topics → Goal candidates
    3. update_goals() — Energy decay, persistence tracking
    4. inject_to_workspace() — Active goals → Thoughts
    5. compute_gei() — Observable metric for autonomy

Persists to: data/persona/goals.json
"""

import json
import logging
import re
import time
import unicodedata
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Curiosity entries fed directly by conversation can guide retrieval and
# attention, but they are not independent evidence of a durable objective.
# These are structured source identifiers from CuriosityEngine call sites, not
# words matched against a user's language.
_USER_ORIGINATED_CURIOSITY_SOURCES = {
    "conversation", "user_input", "user_semantic", "user_signal",
}

# ── Phase 5.1 shared constants ──────────────────────────────────────────────
# Extracted from derive_motivations() so PersistentExecutiveLoop can check
# whether the reason a goal was created still holds, using the exact same
# thresholds that created it — not a second, drift-prone copy of the numbers.
PRESSURE_MOTIVATION_THRESHOLDS: Dict[str, float] = {
    "epistemic":  0.55,
    "uncertainty": 0.45,
    "coherence":  0.40,
    "identity":   0.50,
    "expression": 0.55,
    "aspirational": 0.35,  # resting 0.10 + 0.25, matching the other five's uniform offset
}
TRAIT_MOTIVATION_THRESHOLDS: Dict[str, float] = {
    "curiosity":      0.5,
    "empathy":        0.5,
    "growth_mindset": 0.6,
    "logic":          0.6,
}


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class Motivation:
    """General drive derived from identity/pressures."""
    name: str              # e.g., "explore", "resolve_uncertainty", "understand_user"
    strength: float        # 0.0-1.0
    origin: str            # e.g., "trait:curiosity", "pressure:epistemic"
    
    def __post_init__(self):
        self.strength = max(0.0, min(1.0, self.strength))


@dataclass
class Goal:
    """Specific persistent goal with topic and lifecycle tracking."""
    id: str                           # unique identifier
    topic: str                        # what the goal is about
    origin: str                       # motivation name that spawned it
    
    priority: float                   # importance (0.0-1.0)
    energy: float                     # current motivation level (0.0-1.0)
    
    created_cycle: int                # when it was born
    last_active: int                  # last cycle it influenced behavior
    
    persistence: int = 0              # cycles survived
    actions_taken: int = 0            # observable behaviors
    # Completion semantics (B+A): world-facing action gate + tension provenance
    non_introspective_actions: int = 0    # web_search / user_question actions taken
    tension_source: Optional[str] = None  # tension that spawned this goal (A gate)
    tension_level: float = 0.0            # tension level at creation (metadata)
    status: str = "active"            # active, dormant, completed, abandoned
    
    completion: float = 0.0           # progress toward goal (0.0-1.0)

    # Intent model: a goal is a desired state transition, not only a topic.
    # Defaults keep persisted goals from older versions loadable.
    intent_kind: str = "learn"       # execute, correct, project, learn, become, strengthen, interact
    temporal_scope: str = "ongoing"  # immediate, continuing, future, retrospective
    desired_effect: str = ""
    success_criteria: str = ""
    subject: str = ""
    # Link an explicitly user-requested goal to the exact chat turn that
    # caused the write. Topic-derived autonomous goals also retain the source
    # turns that independently established the topic.
    source_turn_id: str = ""
    source_evidence_turn_ids: List[str] = field(default_factory=list)
    # Autonomous thought-evaluator proposals retain their originating thought
    # across persistence so a committed goal can be traced to its evidence.
    source_thought_id: str = ""
    source_thought_source: str = ""
    source_thought_type: str = ""
    source_thought_timestamp: str = ""
    source_concept_method: str = ""
    source_concept_kind: str = ""
    source_concept_ref: str = ""
    source_concept_sha256: str = ""
    # Full causal source set. Singular source_concept_* fields remain as the
    # primary source for compatibility; consolidation can retain additional
    # origins here without flattening them into an ambiguous label.
    source_provenance_records: List[Dict[str, object]] = field(default_factory=list)
    # Admission status is explicit so an old, unprovenanced goal can be kept
    # for audit/history without remaining eligible for autonomous execution.
    source_provenance_status: str = "unverified"
    source_provenance_reason: str = ""
    # Last autonomous action receipt, persisted with the goal so its counters
    # can be audited against the causal ledger instead of inferred from totals.
    last_action_execution_id: str = ""
    last_action_cycle_id: Optional[int] = None
    last_action_source_turn_id: str = ""
    last_action_type: str = ""
    last_action_at: str = ""
    # User-requested development goals require explicit criterion evidence;
    # completing a search/action alone is not evidence that the goal was met.
    success_criteria_verified: bool = False
    success_criteria_evidence: str = ""
    success_criteria_verified_by: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        self.priority = max(0.0, min(1.0, self.priority))
        self.energy = max(0.0, min(1.0, self.energy))
        self.completion = max(0.0, min(1.0, self.completion))
        if not self.subject:
            self.subject = self.topic
        if not self.desired_effect:
            self.desired_effect = _goal_effect(self.intent_kind, self.topic)
        if not self.success_criteria:
            self.success_criteria = _goal_success(self.intent_kind, self.topic)


def _goal_intent(origin: str, topic: str) -> Tuple[str, str]:
    """Infer a coarse action intention from motivation and durable subject."""
    text = f"{origin} {topic}".casefold()
    if any(word in text for word in ("correct", "repair", "failure", "error", "contradiction")):
        return "correct", "retrospective"
    if any(word in text for word in ("project", "future", "aspiration", "plan", "horizon")):
        return "project", "future"
    if any(word in text for word in ("user", "relational", "social", "connect")):
        return "interact", "continuing"
    if any(word in text for word in ("identity", "become", "coherence")):
        return "become", "future"
    if any(word in text for word in ("memory", "consolidat", "reinforce", "strength")):
        return "strengthen", "continuing"
    if any(word in text for word in ("execute", "action", "do ")):
        return "execute", "immediate"
    return "learn", "continuing"


def _goal_effect(kind: str, topic: str) -> str:
    effects = {
        "execute": "produce an immediate observable result",
        "correct": "reduce the error and prevent its repetition",
        "project": "move from the present state toward a viable future state",
        "learn": "increase grounded understanding of the subject",
        "become": "develop a more stable and coherent capability or identity",
        "strengthen": "reinforce a capability through repeated evidence",
        "interact": "improve a meaningful exchange with the relevant person or system",
    }
    return f"{effects.get(kind, 'make measurable progress')} around {topic}"


def _goal_success(kind: str, topic: str) -> str:
    if kind == "execute":
        return "an observable result is produced"
    if kind == "correct":
        return "the correction is applied and a later check shows no recurrence"
    if kind == "project":
        return "a dated next step and its dependency are recorded"
    if kind == "interact":
        return "the exchange produces a relevant response or updated relational evidence"
    if kind == "strengthen":
        return "repeated evidence shows improved reliability"
    if kind == "become":
        return "the capability or identity trait gains stable supporting evidence"
    return f"a grounded insight about {topic} is recorded and verified"


# ── Goal Engine ────────────────────────────────────────────────────────────

class GoalEngine:
    """
    Generates and maintains persistent internal goals from identity and pressures.
    
    Core loop:
        1. derive_motivations(identity, pressures) → Motivations
        2. generate_candidates(motivations, topics) → New goals
        3. update_goals(cycle) → Energy decay, persistence tracking
        4. get_active_goals() → Goals that should influence behavior
    """
    
    # Thresholds
    # Keep this aligned with GoalActionExecutor's eligibility floor. A higher
    # engine-only threshold creates goals that exist on disk but can never
    # reach the planner or the autonomous action loop.
    ACTIVATION_THRESHOLD = 0.10     # priority × energy must exceed this to be active
    DORMANCY_ENERGY = 0.15          # goals below this energy go dormant
    ABANDONMENT_CYCLES = 8          # dormant for >8 cycles → abandoned (was 20: too slow)
    MAX_ACTIVE_GOALS = 8            # cap on concurrent active goals
    MAX_TOTAL_GOALS   = 20          # hard cap including dormant/completed
    MAX_STALE_CYCLES  = 15          # no action taken in N cycles → go dormant early
    TOPIC_COOLDOWN_SECS = 600       # seconds before an abandoned topic can respawn
    EXTERNAL_TASK_TTL_SECS = 21600  # user-owned practical goals stay quarantined for 6h
    
    # Energy decay
    ENERGY_DECAY_RATE = 0.93        # 7% loss/cycle — dormant in ~25 cycles (was 0.97: too slow)
    CURIOSITY_BOOST = 0.15          # energy boost when curiosity pressure high
    
    # Persistence thresholds for GEI calculation
    MIN_PERSISTENCE_FOR_GEI = 1     # goal must survive 1+ cycle to count (was 3 — too slow)
    
    def __init__(self, ai_system, persistence_file: Optional[str] = None):
        self.ai_system = ai_system
        # update_goals completes eligible goals through complete_goal, which
        # acquires this same lock on the same thread.
        self._lock = RLock()
        self._goals: Dict[str, Goal] = {}
        # Terminal history remains queryable for outcome review, but does not
        # consume the bounded pool used for live goal admission/execution.
        self._goal_history: Dict[str, Goal] = {}
        # Records managed by DataAccess (e.g. GQF low-quality/archive records)
        # can be intentionally absent from the live Goal object pool. Preserve
        # them on writes unless the engine explicitly recycles their IDs.
        self._deleted_goal_ids: set[str] = set()
        self._topic_quality_cache: Dict[str, bool] = {}
        self._cycle_counter: int = 0
        self._persistence_file = Path(persistence_file or "data/persona/goals.json")
        self._external_tasks_file = self._persistence_file.with_name(
            "external_goal_contexts.json"
        )
        self._external_tasks: List[Dict[str, object]] = []
        # topic → timestamp of abandonment (for TOPIC_COOLDOWN_SECS check)
        self._recently_abandoned: Dict[str, float] = {}
        self._tick_report_lock = RLock()
        self._last_tick_report: Dict[str, object] = {
            "status": "not_run",
            "tick_at": None,
        }
        
        # Load persisted goals
        self._load_goals()
        self._load_external_tasks()
        self._retire_interaction_echo_goals()
        self._retire_external_task_goals()
        self._retire_invalid_active_goals()
        self._defer_unverified_active_goals()
        
        logger.info(f"GoalEngine initialized with {len(self._goals)} persisted goals")

    @staticmethod
    def _ownership_terms(text: str) -> set[str]:
        """Extract stable content terms used only for goal-ownership matching."""
        normalized = unicodedata.normalize("NFKD", str(text or "").casefold())
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))
        return {
            token for token in re.findall(r"[a-z0-9]+", normalized)
            if len(token) >= 4
        }

    def _load_external_tasks(self) -> None:
        """Load unexpired user-owned task concepts from disk."""
        try:
            if self._external_tasks_file.exists():
                data = json.loads(self._external_tasks_file.read_text(encoding="utf-8"))
                now = time.time()
                self._external_tasks = [
                    item for item in data.get("contexts", [])
                    if float(item.get("expires_at", 0.0)) > now
                ]
        except Exception as exc:
            self._external_tasks = []
            logger.debug("Could not load external goal contexts: %s", exc)

    def _save_external_tasks(self) -> None:
        try:
            self._external_tasks_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {"contexts": self._external_tasks, "saved_at": datetime.now().isoformat()}
            tmp = self._external_tasks_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            import os
            os.replace(tmp, self._external_tasks_file)
        except Exception as exc:
            logger.warning("Could not save external goal contexts: %s", exc)

    def _is_external_task_topic(self, topic: str) -> bool:
        """Return True when a candidate belongs to a recent human task."""
        now = time.time()
        self._external_tasks = [
            item for item in self._external_tasks
            if float(item.get("expires_at", 0.0)) > now
        ]
        topic_terms = self._ownership_terms(topic)
        if not topic_terms:
            return False
        normalized_topic = " ".join(topic.casefold().split())
        return any(
            normalized_topic in {
                " ".join(str(value).casefold().split())
                for value in item.get("exact_topics", [])
            }
            or bool(topic_terms.intersection(set(item.get("terms", []))))
            for item in self._external_tasks
        )

    def _is_valid_goal_topic(self, topic: str) -> bool:
        """Strict, language-neutral gate for durable goals.

        Semantic quality is the decision. This deliberately avoids deciding
        that a token is a fragment because it appears in a language dictionary.
        If no embedder is reachable, an isolated token is not enough evidence
        for a durable goal; defer it until the semantic scorer is available.
        """
        normalized = " ".join(str(topic or "").casefold().split())
        if not normalized:
            return False
        with self._lock:
            cached = self._topic_quality_cache.get(normalized)
        if cached is not None:
            return cached
        try:
            from cognition import goal_semantics
            semantic_quality = goal_semantics.batch_topic_quality([normalized])
            if semantic_quality is not None:
                accepted = bool(semantic_quality[normalized][2])
                with self._lock:
                    self._topic_quality_cache[normalized] = accepted
                return accepted
        except Exception:
            pass
        # Unknown is not a negative verdict: callers must defer the candidate
        # and persisted goals must remain intact until embeddings are available.
        return False

    def thought_proposal_rejection_reason(self, topic: str) -> str | None:
        """Apply the durable-goal topic gates before a proposal enters competition.

        The commit path still repeats all admission checks. This early check
        keeps a proposal that cannot become a durable goal from winning the
        workspace and displacing an admissible candidate.
        """
        normalized = " ".join(str(topic or "").replace("_", " ").casefold().split())
        if not normalized:
            return "missing_topic"
        if self._is_external_task_topic(normalized):
            return "user_owned_task"
        if self._is_valid_goal_topic(normalized):
            return None
        with self._lock:
            semantic_verdict = self._topic_quality_cache.get(normalized)
        return "low_quality_topic" if semantic_verdict is False else "quality_unavailable"

    @staticmethod
    def _goal_provenance_records(goal: Goal) -> List[Dict[str, object]]:
        records = getattr(goal, "source_provenance_records", None)
        if isinstance(records, list) and records:
            return [record for record in records if isinstance(record, dict)]
        kind = str(getattr(goal, "source_concept_kind", "") or "").strip()
        if not kind:
            return []
        return [{
            "kind": kind,
            "method": str(getattr(goal, "source_concept_method", "") or "").strip(),
            "ref": str(getattr(goal, "source_concept_ref", "") or "").strip(),
            "sha256": str(getattr(goal, "source_concept_sha256", "") or "").strip(),
            "source_turn_ids": list(getattr(goal, "source_evidence_turn_ids", []) or []),
            "source_turn_id": str(getattr(goal, "source_turn_id", "") or "").strip(),
            "source_thought_id": str(getattr(goal, "source_thought_id", "") or "").strip(),
        }]

    @classmethod
    def goal_provenance_verdict(cls, goal: Goal) -> Tuple[bool, str]:
        """Validate the causal receipt required before a persistent goal can run.

        This checks typed source evidence, never topic wording, language, or
        token count. A short topic is valid when its source is valid.
        """
        records = cls._goal_provenance_records(goal)
        if not records:
            return False, "missing_source_receipt"
        for record in records:
            kind = str(record.get("kind", "") or "").strip()
            method = str(record.get("method", "") or "").strip()
            ref = str(record.get("ref", "") or "").strip()
            turns = record.get("source_turn_ids", [])
            turn_ids = {str(value).strip() for value in turns if str(value).strip()} \
                if isinstance(turns, (list, tuple, set)) else set()
            singular_turn = str(record.get("source_turn_id", "") or "").strip()
            if singular_turn:
                turn_ids.add(singular_turn)
            thought_id = str(record.get("source_thought_id", "") or "").strip()
            if kind == "user_semantic_commitment":
                if len(turn_ids) >= 2 and method == "semantic_memory.recent_user_topic_evidence" and ref.startswith("concept:"):
                    return True, "verified_user_commitment"
            elif kind == "user_explicit_goal":
                explicit_turn = singular_turn or (next(iter(turn_ids)) if len(turn_ids) == 1 else "")
                if explicit_turn and method == "GoalEngine.create_user_requested_goal" and ref == f"turn:{explicit_turn}":
                    return True, "verified_explicit_user_goal"
            elif kind == "selected_workspace_thought":
                if thought_id and method and ref == f"thought:{thought_id}":
                    return True, "verified_workspace_thought"
            elif kind == "autonomous_motivation":
                if method and ref:
                    return True, "verified_autonomous_motivation"
            elif kind == "internal_curiosity_state":
                # Curiosity is a signal for attention and exploration, not by
                # itself authority to create a persistent, executable goal.
                # A curiosity topic must first become a selected workspace
                # thought with an actual proposal (or receive user commitment
                # evidence); otherwise a fragment such as "rappelle" can be
                # inflated into a generic plan solely because it recurred.
                continue
            elif kind == "state_record":
                # Curiosity records can contain self-generated questions. They
                # are not durable goal authority without repeated user intent.
                if (getattr(goal, "tension_source", None) == "curiosity_drive"
                        and not any(
                            str(item.get("kind", "")) == "user_semantic_commitment"
                            and len({str(value).strip() for value in item.get("source_turn_ids", [])
                                     if str(value).strip()}) >= 2
                            for item in records
                        )):
                    continue
                digest = str(record.get("sha256", "") or "").strip()
                if method and ref and len(digest) == 64:
                    return True, "verified_state_record"
        return False, "source_receipt_incomplete_or_ineligible"

    def _defer_unverified_active_goals(self) -> int:
        """Quarantine legacy active goals whose source cannot authorize work."""
        deferred = 0
        for goal in self._goals.values():
            if goal.status != "active":
                continue
            verified, reason = self.goal_provenance_verdict(goal)
            if verified:
                goal.source_provenance_status = "verified"
                goal.source_provenance_reason = reason
                continue
            goal.status = "deferred"
            goal.source_provenance_status = "unverified"
            goal.source_provenance_reason = reason
            deferred += 1
        if deferred:
            self._save_goals()
            logger.warning(
                "Goal provenance migration deferred %d active goal(s) without executable source evidence",
                deferred,
            )
        return deferred

    def _retire_invalid_active_goals(self) -> int:
        """Migrate legacy goals that predate the strict topic-quality gate."""
        retired = 0
        now = time.time()
        for goal in self._goals.values():
            if goal.status != "active" or self._is_valid_goal_topic(goal.topic):
                continue
            normalized = " ".join(goal.topic.casefold().split())
            with self._lock:
                has_semantic_verdict = normalized in self._topic_quality_cache
            if not has_semantic_verdict:
                continue
            if goal.status == "active":
                goal.status = "abandoned"
                self._recently_abandoned[goal.topic.casefold()] = now
                retired += 1
        if retired:
            self._save_goals()
            logger.info("Goal quality migration retired %d persisted goal(s)", retired)
        return retired

    def _retire_interaction_echo_goals(self) -> int:
        """Retire legacy social goals copied from generic emotional traces.

        Older GoalQualityFilter versions promoted descriptions such as
        ``Still thinking about: [curiosity] during interaction: <user text>``
        into persistent social goals. Emotional residue remains valid memory,
        but a raw interaction was never an explicit durable objective.
        """
        legacy_topic = re.compile(
            r"^still thinking about:\s*\[[^\]]+\]\s*during interaction:",
            re.IGNORECASE,
        )
        retired = 0
        now = time.time()
        for goal in self._goals.values():
            if (goal.status != "active"
                    or goal.origin != "goal_quality_filter"
                    or goal.tension_source != "social_drive"
                    or not legacy_topic.match(goal.topic.strip())):
                continue
            goal.status = "abandoned"
            self._recently_abandoned[goal.topic.casefold()] = now
            retired += 1
        if retired:
            self._save_goals()
            logger.info(
                "Retired %d legacy social goal(s) copied from ordinary interactions",
                retired,
            )
        return retired

    def _retire_external_task_goals(self) -> int:
        """Apply persisted ownership boundaries whenever the engine starts."""
        retired = 0
        now = time.time()
        for goal in self._goals.values():
            if goal.status == "active" and self._is_external_task_topic(goal.topic):
                goal.status = "abandoned"
                self._recently_abandoned[goal.topic.casefold()] = now
                retired += 1
        if retired:
            self._save_goals()
            logger.info("Goal ownership correction retired %d persisted goal(s)", retired)
        return retired

    def register_external_task(
        self,
        user_text: str,
        primary_goal: str,
        options: Optional[List[str]] = None,
    ) -> int:
        """Quarantine a human-owned practical goal from autonomous goal formation."""
        terms = self._ownership_terms(primary_goal)
        for option in options or []:
            terms.update(self._ownership_terms(option))
        if not terms:
            terms = self._ownership_terms(user_text)
        if not terms:
            return 0

        now = time.time()
        entry = {
            "primary_goal": str(primary_goal or "")[:200],
            "terms": sorted(terms),
            "created_at": now,
            "expires_at": now + self.EXTERNAL_TASK_TTL_SECS,
        }
        with self._lock:
            self._external_tasks = [
                item for item in self._external_tasks
                if float(item.get("expires_at", 0.0)) > now
            ]
            self._external_tasks.append(entry)
            retired = self._retire_external_task_goals()
            self._save_external_tasks()
            self._save_goals()
        return retired

    # ── Resource economy bridge ────────────────────────────────────────────
    # v59: attention pool was fully decorative — CognitiveResourceEconomy
    # has record_goal_opened()/record_goal_closed() but nothing in the
    # codebase ever called them, so attention sat at 1.0 forever regardless
    # of how many goals were open. Wired through here since GoalEngine is
    # the single place goals are actually opened and closed.
    def _economy(self):
        try:
            org = getattr(self.ai_system, '_organism', None)
            loop = getattr(org, '_loop', None) if org else None
            return getattr(loop, '_resource_economy', None) if loop else None
        except Exception:
            return None

    
    # ── Persistence ────────────────────────────────────────────────────────
    
    def _load_goals(self):
        """Load goals from disk."""
        self._goal_history = getattr(self, "_goal_history", {})
        if not self._persistence_file.exists():
            return

        try:
            with open(self._persistence_file) as f:
                data = json.load(f)
                self._cycle_counter = data.get('cycle_counter', 0)
                cooldowns = data.get('topic_cooldowns', {})
                if isinstance(cooldowns, dict):
                    loaded_cooldowns: Dict[str, float] = {}
                    for topic, timestamp in cooldowns.items():
                        try:
                            if str(topic).strip():
                                loaded_cooldowns[str(topic).casefold()] = float(timestamp)
                        except (TypeError, ValueError):
                            continue
                    self._recently_abandoned = loaded_cooldowns
                goals_data = data.get('goals', {})

                # Defensive: goals_data may be a list if saved by an older schema version.
                # Normalise to dict keyed by goal id before iterating.
                if isinstance(goals_data, list):
                    goals_data = {
                        item.get('goal_id', str(i)): item
                        for i, item in enumerate(goals_data)
                        if isinstance(item, dict)
                    }

                for gid, gdata in goals_data.items():
                    try:
                        # Archived and merged records are durable history, not
                        # live GoalEngine work items.  Loading them into the
                        # bounded runtime pool lets old history exhaust
                        # MAX_TOTAL_GOALS and permanently reject new goals.
                        # _save_goals() preserves these records from the
                        # existing JSON payload, so excluding them here does
                        # not delete or rewrite their history.
                        persisted_status = str(gdata.get("status", "active")).casefold()
                        if persisted_status in {"archived", "merged"}:
                            history = {
                                key: value for key, value in gdata.items()
                                if key in Goal.__dataclass_fields__
                            }
                            history.setdefault("id", str(gid))
                            history.setdefault("topic", str(gdata.get("name", "")))
                            history.setdefault("origin", "persisted_history")
                            history.setdefault("priority", 0.0)
                            history.setdefault("energy", 0.0)
                            history.setdefault("created_cycle", self._cycle_counter)
                            history.setdefault("last_active", self._cycle_counter)
                            self._goal_history[gid] = Goal(**history)
                            continue
                        self._goals[gid] = Goal(**gdata)
                    except Exception as _ge:
                        # Schema bridge: DAL/GQF goals use "name" not "topic".
                        # They also use string timestamps for created_cycle/last_active.
                        # Translate to GoalEngine format instead of silently dropping.
                        try:
                            # Helper: safely convert last_active which may be an
                            # ISO timestamp string ("2026-04-07T...") or an int.
                            def _to_int_cycle(val, default):
                                try:
                                    return int(val)
                                except (TypeError, ValueError):
                                    return default  # ISO string or None

                            _bridged = {
                                "id":           gdata.get("id", gid),
                                "topic":        gdata.get("topic") or gdata.get("name", "unknown"),
                                "origin":       gdata.get("origin", "goal_quality_filter"),
                                "priority":     float(gdata.get("priority", 0.5)),
                                "energy":       float(gdata.get("energy", 0.5)),
                                "created_cycle": _to_int_cycle(
                                    gdata.get("created_cycle"), self._cycle_counter),
                                "last_active":   _to_int_cycle(
                                    gdata.get("last_active"), self._cycle_counter),
                                "persistence":   _to_int_cycle(
                                    gdata.get("persistence"), 0),
                                "actions_taken": _to_int_cycle(
                                    gdata.get("actions_taken"), 0),
                                    "non_introspective_actions": _to_int_cycle(
                                        gdata.get("non_introspective_actions"), 0),
                                    "tension_source": gdata.get("tension_source"),
                                    "tension_level": float(
                                        gdata.get("tension_level", 0.0) or 0.0),
                                "status":        gdata.get("status", "active"),
                                "completion":    float(gdata.get("completion", 0.0)),
                                "created_at":    str(gdata.get("created_at",
                                                     gdata.get("created_cycle", ""))),
                            }
                            # Only load runtime-relevant bridged goals. Terminal
                            # records remain in the persisted history and are
                            # intentionally excluded from the bounded live pool.
                            bridged_status = str(_bridged["status"]).casefold()
                            if bridged_status in {"archived", "merged"}:
                                self._goal_history[gid] = Goal(**_bridged)
                            elif bridged_status not in {
                                "completed", "abandoned", "low_quality", "archived", "merged",
                            }:
                                self._goals[gid] = Goal(**_bridged)
                                logger.debug(
                                    f"[GoalEngine] Bridged DAL goal {gid!r}: "
                                    f"topic={_bridged['topic']!r}"
                                )
                        except Exception as _be:
                            logger.debug(f"Skipping malformed goal {gid!r}: {_ge} | bridge: {_be}")

                logger.info(f"Loaded {len(self._goals)} goals from disk (cycle {self._cycle_counter})")
        except Exception as e:
            logger.error(f"Failed to load goals: {e}")

    def reload_from_disk(self) -> int:
        """Synchronize the live goal pool with writers using DataAccess.

        GoalQualityFilter and a few maintenance tools persist canonical goals
        independently of this long-lived engine instance. Without an explicit
        refresh, the file reports newly generated active goals while the
        executor and GEI continue reading the stale in-memory pool.
        """
        with self._lock:
            before = len(self._goals)
            self._goals.clear()
            self._goal_history.clear()
            self._load_goals()
            self._retire_interaction_echo_goals()
            self._retire_external_task_goals()
            self._retire_invalid_active_goals()
            after = len(self._goals)
            logger.info(
                "[GoalEngine] synchronized live pool from disk (%d → %d goals)",
                before, after,
            )
            return after
    
    def _save_goals(self) -> bool:
        """Atomically persist live goals without erasing DAL-owned metadata."""
        try:
            self._persistence_file.parent.mkdir(parents=True, exist_ok=True)
            existing_data = {}
            if self._persistence_file.exists():
                try:
                    existing_data = json.loads(
                        self._persistence_file.read_text(encoding="utf-8")
                    )
                except Exception:
                    existing_data = {}
            existing_goals = existing_data.get("goals", {})
            if isinstance(existing_goals, list):
                existing_goals = {
                    str(item.get("id") or item.get("goal_id") or index): item
                    for index, item in enumerate(existing_goals)
                    if isinstance(item, dict)
                }
            if not isinstance(existing_goals, dict):
                existing_goals = {}
            goals_payload = {
                str(goal_id): dict(record)
                for goal_id, record in existing_goals.items()
                if str(goal_id) not in self._deleted_goal_ids and isinstance(record, dict)
            }
            for goal_id, goal in self._goals.items():
                record = goals_payload.get(str(goal_id), {})
                # Dataclass fields are authoritative for live records; fields
                # owned by other subsystems (quality scores, repair history)
                # survive if GoalEngine does not model them.
                record.update(asdict(goal))
                goals_payload[str(goal_id)] = record
            data = {
                'cycle_counter': self._cycle_counter,
                'topic_cooldowns': self._recently_abandoned,
                'goals': goals_payload,
                'saved_at': datetime.now().isoformat()
            }
            # Atomic write (tmp → rename) prevents partial-write corruption
            import os
            tmp = self._persistence_file.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self._persistence_file)
            persisted = json.loads(self._persistence_file.read_text(encoding="utf-8"))
            persisted_goals = persisted.get("goals", {})
            if not isinstance(persisted_goals, dict) or not set(self._goals).issubset(persisted_goals):
                raise IOError("Goal persistence read-back did not contain the live registry")
            if self._deleted_goal_ids.intersection(persisted_goals):
                raise IOError("Goal persistence read-back retained explicitly recycled goals")
            self._deleted_goal_ids.clear()
            logger.debug(f"Saved {len(self._goals)} goals to disk")
            return True
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")
            return False
    
    # ── Motivation Derivation ──────────────────────────────────────────────
    
    def derive_motivations(
        self,
        identity,
        pressures: Optional[Dict[str, float]] = None
    ) -> List[Motivation]:
        """
        Transform identity traits and pressures into motivations.
        
        Args:
            identity: AIIdentity from identity_system
            pressures: Dict of pressure names → values (0.0-1.0)
        
        Returns:
            List of Motivation objects
        """
        motivations = []
        pressures = pressures or {}
        
        # 1. Trait-driven motivations
        for trait in identity.core_traits:
            # Curiosity → explore
            if trait.name == "curiosity" and trait.confidence > TRAIT_MOTIVATION_THRESHOLDS["curiosity"]:
                # Cap at 0.75 (was 0.9) — prevents curiosity goals from reaching
                # priority 0.95 and permanently outcompeting all other workspace
                # goals. The trait is real but should not dominate forever.
                motivations.append(Motivation(
                    name="explore",
                    strength=min(0.75, trait.confidence + 0.05),
                    origin=f"trait:{trait.name}"
                ))
            
            # Empathy → understand user
            if trait.name == "empathy" and trait.confidence > TRAIT_MOTIVATION_THRESHOLDS["empathy"]:
                motivations.append(Motivation(
                    name="understand_user",
                    strength=trait.confidence,
                    origin=f"trait:{trait.name}"
                ))
            
            # Growth mindset → improve capabilities
            if trait.name == "growth_mindset" and trait.confidence > TRAIT_MOTIVATION_THRESHOLDS["growth_mindset"]:
                motivations.append(Motivation(
                    name="improve_capabilities",
                    strength=trait.confidence,
                    origin=f"trait:{trait.name}"
                ))
            
            # Logic → analyze patterns
            if trait.name == "logic" and trait.confidence > TRAIT_MOTIVATION_THRESHOLDS["logic"]:
                motivations.append(Motivation(
                    name="analyze_patterns",
                    strength=trait.confidence,
                    origin=f"trait:{trait.name}"
                ))
        
        # 2. Pressure-driven motivations.
        # Thresholds calibrated to real resting levels (epistemic rests at 0.30,
        # identity at 0.25) — old thresholds of 0.4-0.5 were never reached in
        # normal operation, so no pressure ever produced a motivation.
        # Thresholds are set ABOVE resting levels so a motivation only fires
        # when there is genuine elevated pressure, not constantly.
        # Resting levels: epistemic≈0.30, uncertainty≈0.20, coherence≈0.15,
        # identity≈0.25, expression≈0.30. Old thresholds matched resting so
        # 4-5 motivations fired every single cycle → constant goal generation.
        epistemic = pressures.get("epistemic", 0.0)
        if epistemic > PRESSURE_MOTIVATION_THRESHOLDS["epistemic"]:   # well above resting (0.30) — genuinely elevated
            motivations.append(Motivation(
                name="resolve_uncertainty",
                strength=min(1.0, epistemic * 1.2),
                origin="pressure:epistemic"
            ))

        uncertainty = pressures.get("uncertainty", 0.0)
        if uncertainty > PRESSURE_MOTIVATION_THRESHOLDS["uncertainty"]:  # above resting (0.20)
            motivations.append(Motivation(
                name="resolve_uncertainty",
                strength=uncertainty,
                origin="pressure:uncertainty"
            ))

        coherence = pressures.get("coherence", 0.0)
        if coherence > PRESSURE_MOTIVATION_THRESHOLDS["coherence"]:   # well above resting (0.15)
            motivations.append(Motivation(
                name="resolve_contradictions",
                strength=coherence,
                origin="pressure:coherence"
            ))

        identity_pressure = pressures.get("identity", 0.0)
        if identity_pressure > PRESSURE_MOTIVATION_THRESHOLDS["identity"]:  # above resting (0.25)
            motivations.append(Motivation(
                name="affirm_identity",
                strength=identity_pressure,
                origin="pressure:identity"
            ))

        expression = pressures.get("expression", 0.0)
        if expression > PRESSURE_MOTIVATION_THRESHOLDS["expression"]:  # above resting (0.30)
            motivations.append(Motivation(
                name="express_and_communicate",
                strength=expression,
                origin="pressure:expression"
            ))

        # Bug fix: "aspirational" pressure (pressure_system.py's reservoir, fed
        # by AspirationalSelf.aspirational_pressure()) was computed and
        # correctly surfaced by get_current_pressures() but never read here —
        # the only place a pressure becomes a Motivation, and therefore a
        # Goal. Aspirations could accumulate indefinitely and never once
        # reach GoalEngine/deliberate()'s workspace competition. Mirrors the
        # five branches above exactly; threshold follows their established
        # resting+0.25 convention (0.10 + 0.25 = 0.35).
        aspirational = pressures.get("aspirational", 0.0)
        if aspirational > PRESSURE_MOTIVATION_THRESHOLDS["aspirational"]:  # above resting (0.10)
            motivations.append(Motivation(
                name="pursue_aspiration",
                strength=aspirational,
                origin="pressure:aspirational"
            ))

        # 3. Baseline motivation — always explore when topics exist.
        # Ensures goal formation can happen even when identity traits have
        # not yet accumulated enough evidence (< 3 memories per trait).
        # This is not artificial injection — it reflects the organism's
        # fundamental drive to engage with whatever it has been processing.
        if not motivations:
            motivations.append(Motivation(
                name="explore",
                strength=0.50,
                origin="baseline:always_curious"
            ))

        logger.debug(f"Derived {len(motivations)} motivations from identity + pressures")
        return motivations
    
    # ── Goal Generation ────────────────────────────────────────────────────
    
    def generate_candidates(
        self,
        motivations: List[Motivation],
        topics: List[str],
        limit: int = 5,
        topic_source_turns: Optional[Dict[str, List[str]]] = None,
        topic_source_provenance: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> List[Goal]:
        """
        Generate goal candidates by pairing motivations with topics.
        
        Args:
            motivations: List of Motivation objects
            topics: Recent topics from semantic memory
            limit: Max new goals to generate
        
        Returns:
            List of new Goal objects
        """
        candidates = []
        generation_report = {
            "considered_count": 0,
            "cooldown_suppressed_count": 0,
            "live_duplicate_suppressed_count": 0,
            "user_task_suppressed_count": 0,
            "semantic_rejected_count": 0,
            "semantic_unavailable_count": 0,
            "provenance_suppressed_count": 0,
            "candidate_count": 0,
            "capacity_blocked": False,
        }
        
        # Only generate if we have room
        active_count = len([g for g in self._goals.values() if g.status == "active"])
        if active_count >= self.MAX_ACTIVE_GOALS:
            generation_report["capacity_blocked"] = True
            self._last_candidate_generation_report = generation_report
            logger.debug(f"Max active goals reached ({active_count}), skipping generation")
            return []
        
        # Pair motivations with topics.
        # seen_topics tracks both existing goals AND candidates generated in
        # this batch — without this, the same topic can appear in multiple
        # candidates before any are added to self._goals.
        # Terminal history is not a permanent duplicate lock. Cooldowns govern
        # when a completed/abandoned topic may return; only live work and
        # dormant work should suppress a new candidate indefinitely.
        seen_topics = {
            g.topic.casefold() for g in self._goals.values()
            if g.status in {"active", "dormant"}
        }

        for motive in motivations:
            if len(candidates) >= limit:
                break

            for topic in topics[:5]:  # consider top 5 topics
                if len(candidates) >= limit:
                    break

                generation_report["considered_count"] += 1
                t_lower = topic.casefold().strip()
                if time.time() - self._recently_abandoned.get(t_lower, 0.0) < self.TOPIC_COOLDOWN_SECS:
                    generation_report["cooldown_suppressed_count"] += 1
                    continue
                if t_lower in seen_topics:  # dedup across batch AND existing goals
                    generation_report["live_duplicate_suppressed_count"] += 1
                    continue
                if self._is_external_task_topic(t_lower):
                    generation_report["user_task_suppressed_count"] += 1
                    logger.debug(
                        "GoalEngine: skipping user-owned task topic %r", topic
                    )
                    continue
                # Fail closed if semantic topic scoring is unavailable; the
                # conversation fragment must not become a durable goal.
                if not self._is_valid_goal_topic(t_lower):
                    with self._lock:
                        semantic_verdict = self._topic_quality_cache.get(t_lower)
                    if semantic_verdict is None:
                        generation_report["semantic_unavailable_count"] += 1
                    else:
                        generation_report["semantic_rejected_count"] += 1
                    continue

                intent_kind, temporal_scope = _goal_intent(motive.name, topic)
                provenance_key = " ".join(t_lower.split())
                provenance = (topic_source_provenance or {}).get(provenance_key, {})
                source_turn_ids = list((topic_source_turns or {}).get(topic, []))
                source_record = {
                    "kind": str(provenance.get("kind", "unverified"))[:80],
                    "method": str(provenance.get("method", ""))[:120],
                    "ref": str(provenance.get("ref", ""))[:240],
                    "sha256": str(provenance.get("sha256", ""))[:64],
                    "source_turn_ids": source_turn_ids[-20:],
                    "source_thought_id": str(provenance.get("source_thought_id", ""))[:120],
                }
                source_kind = source_record["kind"]
                if source_kind == "user_semantic_commitment" and len(set(source_turn_ids)) < 2:
                    generation_report["provenance_suppressed_count"] += 1
                    continue
                if source_kind not in {
                    "user_semantic_commitment", "user_explicit_goal",
                    "selected_workspace_thought", "autonomous_motivation",
                    "state_record",
                } or not source_record["method"] or not source_record["ref"]:
                    generation_report["provenance_suppressed_count"] += 1
                    continue
                goal = Goal(
                    id            = str(uuid.uuid4())[:8],
                    topic         = topic,
                    origin        = motive.name,
                    priority      = min(0.95, motive.strength * 1.1),  # tensions boost strength to 0.5-0.8
                    energy        = motive.strength,
                    created_cycle = self._cycle_counter,
                    last_active   = self._cycle_counter,
                    intent_kind   = intent_kind,
                    temporal_scope= temporal_scope,
                    source_turn_id=(
                        (topic_source_turns or {}).get(topic, [""])[-1]
                        if (topic_source_turns or {}).get(topic) else ""
                    ),
                    source_evidence_turn_ids=list(
                        (topic_source_turns or {}).get(topic, [])
                    ),
                    source_concept_kind=str(provenance.get("kind", "unverified"))[:80],
                    source_concept_method=str(
                        provenance.get("method", "goal_engine.generate_candidates")
                    )[:120],
                    source_concept_ref=str(
                        provenance.get("ref", f"topic:{t_lower}")
                    )[:240],
                    source_provenance_records=[source_record],
                )
                verified, reason = self.goal_provenance_verdict(goal)
                if not verified:
                    generation_report["provenance_suppressed_count"] += 1
                    continue
                goal.source_provenance_status = "verified"
                goal.source_provenance_reason = reason

                candidates.append(goal)
                generation_report["candidate_count"] += 1
                seen_topics.add(t_lower)  # mark so next motivation skips it
        self._last_candidate_generation_report = generation_report
        logger.info(f"Generated {len(candidates)} goal candidates")
        return candidates
    
    # ── Goal Update ────────────────────────────────────────────────────────
    
    def update_goals(self, pressures: Optional[Dict[str, float]] = None):
        """
        Update all goals: decay energy, track persistence, change status.
        
        Args:
            pressures: Current pressure values (optional curiosity boost)
        """
        with self._lock:
            self._cycle_counter += 1
            pressures = pressures or {}
            
            epistemic = pressures.get("epistemic", 0.0)
            curiosity_active = epistemic > 0.5
            
            for goal in list(self._goals.values()):
                if goal.status != "active":
                    # Track dormancy time
                    if goal.status == "dormant":
                        cycles_dormant = self._cycle_counter - goal.last_active
                        if cycles_dormant > self.ABANDONMENT_CYCLES:
                            goal.status = "abandoned"
                            logger.debug(f"Goal '{goal.topic}' abandoned after {cycles_dormant} dormant cycles")
                            try:
                                ec = self._economy()
                                if ec:
                                    ec.record_goal_closed()
                            except Exception:
                                pass
                    continue
                
                # Increment persistence
                goal.persistence += 1
                
                # Energy decay
                goal.energy *= self.ENERGY_DECAY_RATE

                # Curiosity boost for explore goals — but NOT when energy is
                # already low (goal approaching dormancy). Boosting a depleted
                # explore goal is what kept "Actively pursue curiosity-driven
                # exploration" cycling indefinitely at e=0.35 despite repeated
                # insight generation driving energy toward the dormancy floor.
                if (curiosity_active
                        and goal.origin == "explore"
                        and goal.energy > self.DORMANCY_ENERGY
                        and goal.actions_taken == 0):
                    # Phase 2.9 GAP 3: attention-weighted continuous boost.
                    # Replaces binary "curiosity_active → full CURIOSITY_BOOST"
                    # with scaling by curiosity_engine attention share.
                    # Uniform weight=0.10 → 1.0× (unchanged from Phase 2.8).
                    # High attention=0.20 → 2.0× (focus amplifies drive).
                    # Low attention=0.05 → 0.5× (defocus dampens it).
                    try:
                        import json as _j2
                        from pathlib import Path as _P2
                        _ap2 = _P2("data/persona/cognitive_attention.json")
                        _cw  = _j2.loads(_ap2.read_text()).get(
                            "attention_weights", {}
                        ).get("curiosity_engine", 0.10) if _ap2.exists() else 0.10
                    except Exception:
                        _cw = 0.10
                    _attn_scale = min(2.5, _cw / 0.10)
                    goal.energy = min(1.0, goal.energy + self.CURIOSITY_BOOST * _attn_scale)
                
                # Stale goal: active but no action taken for MAX_STALE_CYCLES
                if goal.actions_taken == 0 and goal.persistence > self.MAX_STALE_CYCLES:
                    goal.status = "dormant"
                    logger.debug(
                        f"Goal '{goal.topic}' forced dormant (stale: "
                        f"{goal.persistence} cycles, 0 actions)"
                    )
                    continue

                # Auto-complete: acted on meaningfully over time — but only if
                # the completion semantics (B+A) are satisfied: a world-facing
                # action was taken, and (if the goal is tension-derived) that
                # tension has since resolved. Otherwise leave it — it may become
                # eligible later (GQF settlement) or go dormant via energy decay.
                if goal.actions_taken >= 3 and goal.persistence >= 10:
                    from cognition.goal_completion import (
                        goal_completion_eligible,
                        load_current_tensions,
                        record_goal_completion,
                    )
                    eligible, reason = goal_completion_eligible(
                        goal, load_current_tensions()
                    )
                    if eligible:
                        org = (
                            getattr(self.ai_system, "_organism", None)
                            if self.ai_system else None
                        )
                        completion_written = record_goal_completion(
                            goal, goal_engine=self, organism=org,
                            reason=("long-lived: %d actions over %d cycles; %s"
                                    % (goal.actions_taken, goal.persistence, reason)),
                        )
                        if completion_written:
                            logger.info("Goal auto-completed: '%s' "
                                        "(%d actions, %d cycles)"
                                        % (goal.topic, goal.actions_taken,
                                           goal.persistence))
                            continue
                        logger.warning(
                            "Goal auto-completion was eligible but persistence failed: %s",
                            goal.id,
                        )
                    # B/A not yet satisfied — keep it active; the GQF settlement
                    # pass or future actions may close it properly.


                # Check for dormancy
                if goal.energy < self.DORMANCY_ENERGY:
                    goal.status = "dormant"
                    logger.debug(f"Goal '{goal.topic}' went dormant (energy={goal.energy:.2f})")
            
            # Record abandoned topic timestamps for cooldown, then prune
            _now = time.time()
            for g in self._goals.values():
                if g.status == "abandoned":
                    self._recently_abandoned[g.topic.casefold()] = _now
                # Fix: completed topics also enter cooldown (set once) so
                # generate_candidates can't immediately respawn them — without
                # this, high-priority goals complete then reappear within the
                # same session because only "abandoned" status was cooled down.
                elif g.status in ("completed", "archived"):
                    _existing = self._recently_abandoned.get(g.topic.casefold(), 0.0)
                    if _existing == 0.0:
                        self._recently_abandoned[g.topic.casefold()] = _now
            # Evict stale cooldown entries (older than 2× TOPIC_COOLDOWN_SECS)
            _stale_cutoff = _now - self.TOPIC_COOLDOWN_SECS * 2
            self._recently_abandoned = {
                t: ts for t, ts in self._recently_abandoned.items()
                if ts > _stale_cutoff
            }
            # Persist terminal status before removing abandoned goals from the
            # live pool. _save_goals preserves records owned by other writers;
            # pruning first would therefore leave their old persisted status
            # (usually dormant), and reload_from_disk could resurrect them.
            # Keep them in memory and retry on a later tick if the write fails.
            if self._save_goals():
                self._goals = {
                    gid: g for gid, g in self._goals.items()
                    if g.status != "abandoned"
                }
            elif any(g.status == "abandoned" for g in self._goals.values()):
                logger.warning(
                    "GoalEngine retained abandoned goals in the live pool "
                    "because persistence failed"
                )
            
            active = len([g for g in self._goals.values() if g.status == "active"])
            logger.debug(f"Goal update: {active} active, {len(self._goals)} total")
    
    def add_goal(self, goal: Goal) -> bool:
        """Add and persist a goal; return True only after the write is confirmed."""
        topic = goal.topic.strip().casefold()

        if self._is_external_task_topic(topic):
            logger.info("GoalEngine: rejected user-owned task topic %r", goal.topic)
            return False

        if not self._is_valid_goal_topic(topic):
            logger.info("GoalEngine: rejected low-quality topic %r", goal.topic)
            return False

        verified, provenance_reason = self.goal_provenance_verdict(goal)
        if not verified:
            goal.source_provenance_status = "unverified"
            goal.source_provenance_reason = provenance_reason
            logger.info(
                "GoalEngine: rejected goal without executable source evidence (%s)",
                provenance_reason,
            )
            return False
        goal.source_provenance_status = "verified"
        goal.source_provenance_reason = provenance_reason

        # Topic cooldown: don't re-create a recently abandoned topic
        _last_abandoned = self._recently_abandoned.get(topic, 0.0)
        if time.time() - _last_abandoned < self.TOPIC_COOLDOWN_SECS:
            logger.debug(
                f"GoalEngine: topic '{goal.topic}' in cooldown "
                f"({self.TOPIC_COOLDOWN_SECS}s), skipping"
            )
            return False

        with self._lock:
            # Also reject if we already have this topic (near-duplicate)
            existing_topics = {
                g.topic.casefold() for g in self._goals.values()
                if g.status in {"active", "dormant"}
            }
            if topic.casefold() in existing_topics:
                logger.debug(f"GoalEngine: duplicate topic '{goal.topic}'")
                return False

            # Recycle only after all rejection gates pass, so an invalid or
            # duplicate candidate cannot evict a dormant goal from the pool.
            victim = None
            if len(self._goals) >= self.MAX_TOTAL_GOALS:
                recyclable = [g for g in self._goals.values() if g.status in {
                    "dormant", "completed", "abandoned", "low_quality", "deferred",
                }]
                if recyclable:
                    victim = min(
                        recyclable,
                        key=lambda g: (getattr(g, "last_active", 0), getattr(g, "persistence", 0)),
                    )
                    self._goals.pop(victim.id, None)
                    self._deleted_goal_ids.add(victim.id)
                    logger.info(
                        "GoalEngine: recycled non-active goal '%s' to admit '%s'",
                        victim.topic, goal.topic,
                    )
                else:
                    logger.warning(
                        "GoalEngine: total goal cap (%d) reached; not adding '%s'",
                        self.MAX_TOTAL_GOALS, goal.topic,
                    )
                    return False

            self._goals[goal.id] = goal
            if not self._save_goals():
                self._goals.pop(goal.id, None)
                if victim is not None:
                    self._goals[victim.id] = victim
                    self._deleted_goal_ids.discard(victim.id)
                return False
            logger.info(f"Added goal: {goal.topic} (origin={goal.origin}, priority={goal.priority:.2f})")
            try:
                ec = self._economy()
                if ec:
                    ec.record_goal_opened()
            except Exception:
                pass
            return True

    def create_user_requested_goal(
        self,
        topic: str,
        success_criteria: str,
        source_turn_id: str,
    ) -> Dict[str, object]:
        """Persist an explicitly requested goal and verify its stored record.

        This is the side-effect boundary for chat-originated goal creation.
        A response may claim success only when both GoalEngine admission and
        a disk read-back confirm the exact goal and source turn.
        """
        clean_topic = " ".join(str(topic or "").split())[:240]
        clean_criteria = " ".join(str(success_criteria or "").split())[:500]
        turn_id = str(source_turn_id or "").strip()
        if not clean_topic or not clean_criteria or not turn_id:
            return {"created": False, "verified": False, "reason": "missing_topic_criteria_or_turn_id"}

        goal_id = f"Goal_{uuid.uuid4().hex[:8]}"
        goal = Goal(
            id=goal_id,
            topic=clean_topic,
            origin="user_requested_development",
            priority=0.75,
            energy=0.75,
            created_cycle=self._cycle_counter,
            last_active=self._cycle_counter,
            intent_kind="learn",
            temporal_scope="ongoing",
            desired_effect=f"Improve capability around {clean_topic}",
            success_criteria=clean_criteria,
            subject=clean_topic,
            source_turn_id=turn_id,
            source_concept_kind="user_explicit_goal",
            source_concept_method="GoalEngine.create_user_requested_goal",
            source_concept_ref=f"turn:{turn_id}"[:240],
            source_provenance_records=[{
                "kind": "user_explicit_goal",
                "method": "GoalEngine.create_user_requested_goal",
                "ref": f"turn:{turn_id}"[:240],
                "source_turn_ids": [turn_id],
                "source_turn_id": turn_id,
            }],
        )

        # Hold the re-entrant lock across admission and read-back so a
        # concurrent autonomous cycle cannot obscure which turn wrote it.
        with self._lock:
            before = dict(self._goals)
            if not self.add_goal(goal):
                self._goals.clear()
                self._goals.update(before)
                # If the atomic replace happened but its read-back check
                # failed, put the prior registry back on disk as well.
                self._save_goals()
                return {"created": False, "verified": False, "id": goal_id, "reason": "goal_engine_rejected_or_save_failed"}
            try:
                payload = json.loads(self._persistence_file.read_text(encoding="utf-8"))
                record = payload.get("goals", {}).get(goal_id)
                verified = bool(
                    isinstance(record, dict)
                    and record.get("topic") == clean_topic
                    and record.get("success_criteria") == clean_criteria
                    and record.get("source_turn_id") == turn_id
                )
            except Exception as exc:
                logger.warning("[GoalEngine] explicit goal read-back failed: %s", exc)
                verified = False

            if not verified:
                self._goals.clear()
                self._goals.update(before)
                self._save_goals()
                return {"created": False, "verified": False, "id": goal_id, "reason": "persistence_readback_failed"}

        return {
            "created": True,
            "verified": True,
            "id": goal_id,
            "topic": clean_topic,
            "success_criteria": clean_criteria,
            "source_turn_id": turn_id,
            "status": goal.status,
        }

    def commit_selected_thought_proposal(
        self, proposal: Dict[str, object], cycle: int
    ) -> Dict[str, object]:
        """Persist one workspace-selected proposal and verify its exact record.

        Evaluator output is a proposal, not a goal. This is the single
        transition boundary from arbitration to the persistent goal registry.
        Losing proposals never reach this method.
        """
        concept = " ".join(str(proposal.get("concept") or "").replace("_", " ").split())[:240]
        if not concept:
            return {"created": False, "verified": False, "reason": "missing_concept"}

        proposal_type = str(proposal.get("type") or "uncertainty")
        source_thought_id = str(proposal.get("origin_thought") or "").strip()
        hypothesis = " ".join(str(proposal.get("hypothesis") or "").split())[:500]
        goal_type = str(proposal.get("goal_type") or proposal_type)
        if goal_type == "test_hypothesis" and not hypothesis:
            return {
                "created": False,
                "verified": False,
                "topic": concept,
                "reason": "hypothesis_required",
            }
        origin = f"thought_evaluator:{goal_type}"
        if proposal_type == "tension" and hypothesis:
            origin = "thought_evaluator:test_hypothesis"

        goal_id = f"Goal_{uuid.uuid4().hex[:8]}"
        goal = Goal(
            id=goal_id,
            topic=concept,
            origin=origin,
            priority=float(proposal.get("priority", 0.5) or 0.5),
            energy=0.75,
            created_cycle=int(cycle),
            last_active=int(cycle),
            intent_kind="correct" if proposal_type == "tension" else "learn",
            temporal_scope="continuing",
            desired_effect=(hypothesis or f"Develop grounded understanding of {concept}"),
            success_criteria=(
                "A recorded observation supports or falsifies the hypothesis"
                if hypothesis else f"A grounded insight about {concept} is recorded and verified"
            ),
            subject=concept,
            source_thought_id=source_thought_id,
            source_thought_source=str(proposal.get("origin_thought_source") or "")[:100],
            source_thought_type=str(proposal.get("origin_thought_type") or "")[:80],
            source_thought_timestamp=str(proposal.get("origin_thought_timestamp") or "")[:80],
            source_concept_method=str(proposal.get("concept_source") or "legacy_text_extraction")[:80],
            source_concept_kind="selected_workspace_thought",
            source_concept_ref=f"thought:{source_thought_id}"[:240],
            source_provenance_records=[{
                "kind": "selected_workspace_thought",
                "method": str(proposal.get("concept_source") or "legacy_text_extraction")[:120],
                "ref": f"thought:{source_thought_id}"[:240],
                "source_thought_id": source_thought_id,
            }],
        )

        with self._lock:
            if not self.add_goal(goal):
                existing = self.get_goal_by_topic(concept)
                return {
                    "created": False,
                    "verified": bool(existing),
                    "id": existing.id if existing else goal_id,
                    "topic": concept,
                    "reason": "existing_goal" if existing else "goal_engine_rejected_or_save_failed",
                }
            try:
                payload = json.loads(self._persistence_file.read_text(encoding="utf-8"))
                record = payload.get("goals", {}).get(goal_id)
                verified = bool(
                    isinstance(record, dict)
                    and record.get("topic") == concept
                    and record.get("source_thought_id", "") == source_thought_id
                    and record.get("source_thought_source", "") == goal.source_thought_source
                    and record.get("source_thought_type", "") == goal.source_thought_type
                    and record.get("source_thought_timestamp", "") == goal.source_thought_timestamp
                    and record.get("desired_effect") == goal.desired_effect
                )
            except Exception as exc:
                logger.warning("[GoalEngine] thought-proposal read-back failed: %s", exc)
                verified = False
            if not verified:
                self._goals.pop(goal_id, None)
                self._save_goals()
                return {"created": False, "verified": False, "id": goal_id, "reason": "persistence_readback_failed"}

        logger.info(
            "[GoalEngine] committed selected thought proposal id=%s topic=%r source_thought=%s",
            goal_id, concept, source_thought_id or "unknown",
        )
        return {
            "created": True,
            "verified": True,
            "id": goal_id,
            "topic": concept,
            "source_thought_id": source_thought_id,
            "source_thought_source": goal.source_thought_source,
            "source_thought_type": goal.source_thought_type,
            "source_concept_method": goal.source_concept_method,
            "status": goal.status,
        }
    
    def mark_action(
        self,
        goal_id: str,
        action_type: Optional[str] = None,
        *,
        execution_id: str = "",
        cycle_id: Optional[int] = None,
    ) -> bool:
        """Mark that an action was taken for this goal.

        action_type: when a world-facing action (web_search / user_question)
        was taken, also increment non_introspective_actions — the B gate a
        goal must pass before it is allowed to complete.
        """
        from cognition.goal_completion import NON_INTROSPECTIVE_ACTIONS
        with self._lock:
            if goal_id in self._goals:
                g = self._goals[goal_id]
                previous = (
                    g.actions_taken,
                    g.non_introspective_actions,
                    g.last_active,
                    g.last_action_execution_id,
                    g.last_action_cycle_id,
                    g.last_action_source_turn_id,
                    g.last_action_type,
                    g.last_action_at,
                )
                g.actions_taken += 1
                if action_type in NON_INTROSPECTIVE_ACTIONS:
                    g.non_introspective_actions = (
                        getattr(g, "non_introspective_actions", 0) + 1
                    )
                g.last_active = self._cycle_counter
                g.last_action_execution_id = str(execution_id or "")
                g.last_action_cycle_id = cycle_id
                g.last_action_source_turn_id = str(g.source_turn_id or "")
                g.last_action_type = str(action_type or "")
                g.last_action_at = datetime.now().isoformat()
                if not self._save_goals():
                    (
                        g.actions_taken,
                        g.non_introspective_actions,
                        g.last_active,
                        g.last_action_execution_id,
                        g.last_action_cycle_id,
                        g.last_action_source_turn_id,
                        g.last_action_type,
                        g.last_action_at,
                    ) = previous
                    return False
                return True
        return False
    
    def complete_goal(self, goal_id: str, completion: float = 1.0) -> bool:
        """Complete a goal, refusing unverified explicit user criteria."""
        with self._lock:
            if goal_id in self._goals:
                goal = self._goals[goal_id]
                if (goal.origin == "user_requested_development"
                        and not self._has_verified_success_criteria(goal)):
                    logger.warning(
                        "Refusing completion of user goal %s: success criterion "
                        "has no verified evidence", goal_id
                    )
                    return False
                previous_status, previous_completion = goal.status, goal.completion
                goal.status = "completed"
                goal.completion = max(0.0, min(1.0, float(completion)))
                if not self._save_goals():
                    goal.status, goal.completion = previous_status, previous_completion
                    return False
                logger.info(f"Goal completed: {goal.topic}")
                try:
                    ec = self._economy()
                    if ec:
                        ec.record_goal_closed()
                except Exception:
                    pass
                return True
        return False

    @staticmethod
    def _has_verified_success_criteria(goal: Goal) -> bool:
        """Require criterion-specific evidence for explicit user goals."""
        return bool(
            str(getattr(goal, "success_criteria", "") or "").strip()
            and getattr(goal, "success_criteria_verified", False) is True
            and str(getattr(goal, "success_criteria_evidence", "") or "").strip()
            and str(getattr(goal, "success_criteria_verified_by", "") or "").strip()
        )

    def record_success_criteria_verification(
        self,
        goal_id: str,
        criteria: str,
        evidence: str,
        verified_by: str,
    ) -> bool:
        """Persist criterion-specific verification from a trusted audit step.

        This records evidence; it does not evaluate free-form criteria itself.
        Callers must supply the exact criterion and identify the verifying
        instrument/reviewer. Generic action results must never call this.
        """
        evidence = " ".join(str(evidence or "").split())[:2000]
        verified_by = " ".join(str(verified_by or "").split())[:120]
        with self._lock:
            goal = self._goals.get(str(goal_id))
            if (
                goal is None
                or goal.origin != "user_requested_development"
                or not str(criteria or "").strip()
                or str(criteria).strip() != str(goal.success_criteria or "").strip()
                or not evidence
                or not verified_by
            ):
                return False
            previous = (
                goal.success_criteria_verified,
                goal.success_criteria_evidence,
                goal.success_criteria_verified_by,
            )
            goal.success_criteria_verified = True
            goal.success_criteria_evidence = evidence
            goal.success_criteria_verified_by = verified_by
            if not self._save_goals():
                (
                    goal.success_criteria_verified,
                    goal.success_criteria_evidence,
                    goal.success_criteria_verified_by,
                ) = previous
                return False
            return True
    
    # ── Goal Query ─────────────────────────────────────────────────────────
    
    def dormant_goal(self, goal_id: str, reason: str = "") -> bool:
        """Move a goal to dormant WITHOUT marking it complete.

        Used when the introspection budget is exhausted (or the goal is
        stale) but the completion semantics (B+A) are not yet satisfied —
        i.e. the goal has not taken a world-facing action, or its
        spawning tension has not resolved. It stays eligible for proper
        completion later (via GQF settlement) instead of being falsely
        'completed'.
        """
        with self._lock:
            if goal_id in self._goals:
                self._goals[goal_id].status = "dormant"
                self._goals[goal_id].last_active = self._cycle_counter
                self._save_goals()
                logger.info(
                    "Goal dormant: '%s'%s" % (
                        self._goals[goal_id].topic,
                        (" (%s)" % reason) if reason else "",
                    )
                )
                return True
            return False


    def get_active_goals(self, min_activation: Optional[float] = None) -> List[Goal]:
        """
        Get currently active goals above activation threshold.
        
        Args:
            min_activation: Override default ACTIVATION_THRESHOLD
        
        Returns:
            List of active Goal objects sorted by priority × energy
        """
        threshold = min_activation or self.ACTIVATION_THRESHOLD
        
        active = []
        deferred = False
        for goal in self._goals.values():
            if goal.status != "active":
                continue
            verified, reason = self.goal_provenance_verdict(goal)
            if not verified:
                goal.status = "deferred"
                goal.source_provenance_status = "unverified"
                goal.source_provenance_reason = reason
                deferred = True
                logger.warning(
                    "GoalEngine: quarantined active goal %s before execution (%s)",
                    goal.id, reason,
                )
                continue
            goal.source_provenance_status = "verified"
            goal.source_provenance_reason = reason
            if (self._is_valid_goal_topic(goal.topic)
                    and (goal.priority * goal.energy) >= threshold):
                active.append(goal)
        if deferred:
            self._save_goals()
        
        # Sort by activation strength
        active.sort(key=lambda g: g.priority * g.energy, reverse=True)
        
        return active
    
    def get_goal_by_topic(self, topic: str) -> Optional[Goal]:
        """Find goal matching topic."""
        topic_lower = topic.casefold()
        for goal in self._goals.values():
            if goal.topic.casefold() == topic_lower:
                return goal
        return None

    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """
        Find goal by id, any status. Note: update_goals() prunes 'abandoned'
        goals out of self._goals entirely (but keeps 'completed' ones) — so
        a miss here for an id that was previously valid reliably means the
        goal was abandoned, not merely dormant or completed. Used by
        ArbitrationLearningTracker (Phase 5.4) to check the outcome of a
        past arbitration decision.
        """
        return self._goals.get(goal_id) or getattr(self, "_goal_history", {}).get(goal_id)

    # ── Observatory Metrics ────────────────────────────────────────────────
    
    def compute_gei(self) -> float:
        """
        Compute Goal Emergence Index for Observatory.

        GEI = fraction of active goals that have received at least one
        autonomous action (actions_taken > 0).

        The old count-based formula (len(goals)/TARGET_POOL) permanently
        returned a fixed ceiling once goal count exceeded 10 — providing
        no useful signal. This action-based formula measures genuine
        autonomous BEHAVIOR:

          GEI = goals_with_actions_taken / total_active

          0.00 = no autonomous behavior (GAE not working)
          0.30 = ~30% of goals acted on (healthy, rising)
          1.00 = every active goal acted on (ideal)

        GEI rises as GoalActionExecutor fires, resets when GoalConsolidator
        archives and recreates goals — creating a real activity signal.
        """
        try:
            active = [g for g in self._goals.values() if g.status == "active"]
            if not active:
                return 0.0
            acted = sum(1 for g in active if getattr(g, 'actions_taken', 0) > 0)
            result = round(acted / len(active), 3)
            logger.debug(
                f"[GoalEngine] compute_gei: {acted}/{len(active)} goals acted → {result}"
            )
            return result
        except Exception as e:
            logger.error(f"[GoalEngine] compute_gei failed: {e}", exc_info=True)
            return 0.0
    
    def get_metrics(self) -> Dict:
        """Get goal metrics for Observatory."""
        active = [g for g in self._goals.values() if g.status == "active"]
        dormant = [g for g in self._goals.values() if g.status == "dormant"]
        completed = [g for g in self._goals.values() if g.status == "completed"]
        
        avg_persistence = (
            sum(g.persistence for g in active) / len(active)
            if active else 0
        )
        
        total_actions = sum(g.actions_taken for g in self._goals.values())
        
        return {
            "total_goals": len(self._goals),
            "active": len(active),
            "dormant": len(dormant),
            "completed": len(completed),
            "avg_persistence": round(avg_persistence, 1),
            "total_actions": total_actions,
            "gei": round(self.compute_gei(), 3),
            "cycle": self._cycle_counter
        }
    
    # ── Integration with Workspace ─────────────────────────────────────────
    
    def get_goal_thoughts(self) -> List[Dict]:
        """
        Generate thought candidates for Global Workspace based on active goals.
        
        Returns:
            List of thought dicts ready for workspace injection
        """
        thoughts = []
        
        for goal in self.get_active_goals()[:3]:  # Top 3 active goals
            activation = goal.priority * goal.energy
            
            thoughts.append({
                "type": "goal",
                "topic": goal.topic,
                "origin": goal.origin,
                "priority": activation,
                "source": "goal_engine",
                "goal_id": goal.id,
                "intent_kind": getattr(goal, "intent_kind", "learn"),
                "desired_effect": getattr(goal, "desired_effect", ""),
                "persistence": goal.persistence,
                "content": f"pursue understanding of {goal.topic}"
            })
        
        return thoughts
    
    # ── Main Loop Hook ─────────────────────────────────────────────────────
    
    def save_goals(self) -> None:
        """Public wrapper — lets other modules (e.g. PersistentExecutiveLoop,
        Phase 5.1) persist after mutating a goal's fields directly, without
        reaching into the private _save_goals()."""
        with self._lock:
            self._save_goals()

    def get_current_pressures(self) -> Dict[str, float]:
        """
        Live pressure dict: PressureSystem reservoirs (organism.pressure)
        supplemented by tensions.json (higher-signal for identity/curiosity).
        Extracted from tick() so PersistentExecutiveLoop (Phase 5.1) can read
        the exact same live pressures tick() uses to derive motivations —
        the two must agree on "current pressure" or a goal could be reduced
        for a reason that wouldn't have stopped it from being created.
        """
        pressures: Dict[str, float] = {}
        try:
            org = getattr(self.ai_system, '_organism', None)
            if org:
                ps = getattr(org, 'pressure', None)
                if ps:
                    pressures = {
                        k: getattr(r, 'level', 0.0)
                        for k, r in getattr(ps, 'reservoirs', {}).items()
                    }
        except Exception:
            pass
        try:
            from core.data.access import DataAccess
            _tensions = DataAccess().get_tensions()
            _tension_map = {
                'curiosity_drive':       'epistemic',
                'identity_stress':       'identity',
                'social_drive':          'social',
                'knowledge_uncertainty': 'uncertainty',
                'goal_pressure':         'aspirational',
                'contradiction_pressure':'coherence',
            }
            for t_key, p_key in _tension_map.items():
                t_val = _tensions.get(t_key, 0.0)
                pressures[p_key] = max(pressures.get(p_key, 0.0), t_val)
        except Exception:
            pass
        return pressures

    def tick(self):
        """
        Main autonomous tick — called from internal_loop each slow cycle.

        Goals emerge from three real sources:
          1. Identity traits (curiosity, empathy, logic) → motivation types
          2. Pressure levels (epistemic, identity, expression) → urgency
          3. Semantic memory topics (what PandoraBOX has actually been thinking about)

        This is real goal emergence — not injection. Goals form because the
        organism has traits, is under pressure, and has been processing topics.
        """
        import time as _t
        _now = _t.time()
        _last = getattr(self, '_last_tick_time', 0.0)
        if _now - _last < 60.0:
            self._set_tick_report({
                "status": "skipped_cooldown",
                "tick_at": _now,
                "cooldown_remaining_seconds": round(max(0.0, 60.0 - (_now - _last)), 2),
            })
            logger.debug(f"[GoalEngine] tick skipped (cooldown: {_now-_last:.0f}s)")
            return
        self._last_tick_time = _now
        self._recently_abandoned = getattr(self, "_recently_abandoned", {})
        metrics = {}
        filtered_topics = []
        topic_source_turns = {}
        topic_source_provenance: Dict[str, Dict[str, str]] = {}
        motivations = []
        candidates = []
        accepted = 0
        _generation_blocked = False
        topic_quality_metrics = {
            "semantic_memory": {"candidate_count": 0, "accepted_count": 0,
                                "rejected_count": 0, "unscored_count": 0},
            "curiosity": {"candidate_count": 0, "accepted_count": 0,
                          "rejected_count": 0, "unscored_count": 0,
                          "user_origin_suppressed_count": 0,
                          "provenance_unverified_suppressed_count": 0},
            "autonomous": {"candidate_count": 0, "accepted_count": 0,
                           "rejected_count": 0, "unscored_count": 0},
            "embedding_status": "not_requested",
        }
        candidate_generation_metrics = {
            "considered_count": 0,
            "cooldown_suppressed_count": 0,
            "live_duplicate_suppressed_count": 0,
            "user_task_suppressed_count": 0,
            "semantic_rejected_count": 0,
            "semantic_unavailable_count": 0,
            "provenance_suppressed_count": 0,
            "candidate_count": 0,
            "capacity_blocked": False,
        }

        def _admit_semantic_topics(raw_topics, source_name, limit=8):
            unique_topics = list(dict.fromkeys(
                str(topic).strip() for topic in raw_topics if str(topic).strip()
            ))
            source_metrics = topic_quality_metrics[source_name]
            source_metrics["candidate_count"] = len(unique_topics)
            if not unique_topics:
                return []

            try:
                from cognition import goal_semantics as _gs
                scores = _gs.batch_topic_quality(unique_topics)
            except Exception as error:  # noqa: BLE001
                logger.debug("[GoalEngine] %s topic quality failed: %s", source_name, error)
                scores = None

            if scores is None:
                topic_quality_metrics["embedding_status"] = "deferred"
                source_metrics["unscored_count"] = len(unique_topics)
                logger.info(
                    "[GoalEngine] %s topic scoring deferred; no unscored topics promoted",
                    source_name,
                )
                return []

            topic_quality_metrics["embedding_status"] = "available"
            admitted = []
            for topic in unique_topics:
                verdict = scores.get(topic)
                if verdict is None:
                    source_metrics["unscored_count"] += 1
                    continue
                good_sim, noise_sim, is_quality = verdict
                normalized = " ".join(topic.casefold().split())
                with self._lock:
                    self._topic_quality_cache[normalized] = bool(is_quality)
                logger.debug(
                    "[GoalEngine] %s topic '%s' %s semantic (good=%.2f noise=%.2f)",
                    source_name, topic, "PASS" if is_quality else "reject",
                    good_sim, noise_sim,
                )
                if is_quality:
                    admitted.append(topic)
                else:
                    source_metrics["rejected_count"] += 1

            admitted = admitted[:limit]
            source_metrics["accepted_count"] = len(admitted)
            logger.info(
                "[GoalEngine] %d/%d %s topic(s) passed EMBEDDING quality gate",
                len(admitted), len(unique_topics), source_name,
            )
            return admitted

        try:
            # Clean legacy conversational fragments from the live pool as well
            # as at startup, so a long-running process can recover immediately.
            self._retire_invalid_active_goals()

            # ── 1. Get identity from identity_system ─────────────────────────
            identity = self.ai_system.identity_system.get_identity()

            # ── 2. Get pressures from organism + tensions.json ────────────────
            pressures = self.get_current_pressures()

            # ── 3. Derive motivations from identity + pressures ───────────────
            motivations = self.derive_motivations(identity, pressures)

            # ── 4. Get real topics from semantic memory (on organism) ──────────
            topics = []
            try:
                org = getattr(self.ai_system, '_organism', None)
                sem = getattr(org, 'semantic_memory', None) if org else None
                if sem:
                    # Query provenance, not the whole concept graph. Assistant
                    # confirmations must never become autonomous goals.
                    evidence_reader = getattr(sem, "recent_user_topic_evidence", None)
                    if callable(evidence_reader):
                        evidence = evidence_reader(
                            limit=15, min_strength=0.5, min_observations=2
                        )
                        raw_topics = [item.get("topic", "") for item in evidence]
                        topic_source_turns = {
                            str(item.get("topic", "")): list(item.get("turn_ids", []))
                            for item in evidence if item.get("topic")
                        }
                        topic_source_provenance.update({
                            " ".join(str(item.get("topic", "")).casefold().split()): {
                                "kind": "user_semantic_commitment",
                                "method": "semantic_memory.recent_user_topic_evidence",
                                "ref": f"concept:{item.get('concept_id', item.get('topic', ''))}",
                            }
                            for item in evidence if item.get("topic")
                        })
                    else:
                        raw_topics = sem.recent_user_topics(
                            limit=15, min_strength=0.5, min_observations=2
                        )
                        topic_source_provenance.update({
                            " ".join(str(topic).casefold().split()): {
                                "kind": "unverified_legacy_semantic_memory",
                                "method": "semantic_memory.recent_user_topics",
                                "ref": f"topic:{topic}",
                            }
                            for topic in raw_topics if topic
                        })
                    topics = _admit_semantic_topics(raw_topics, "semantic_memory")
            except Exception as e:
                logger.debug(f"[GoalEngine] semantic topics: {e}")

            # Curiosity is a fallback only for internally stimulated topics.
            # Conversation-originated topics can guide attention and recall,
            # but they need an explicit continuing-commitment observation in
            # SemanticMemory before becoming durable GoalEngine objectives.
            if not topics:
                try:
                    org = getattr(self.ai_system, '_organism', None)
                    cu  = getattr(org, 'curiosity', None) if org else None
                    if cu:
                        curiosity_topics = []
                        with cu._lock:
                            for node in cu._topics.values():
                                if node.curiosity < 0.45:
                                    continue
                                source_history = getattr(node, "source_history", None)
                                history_complete = bool(
                                    getattr(node, "source_history_complete", False)
                                )
                                sources = {
                                    str(value).strip().casefold()
                                    for value in source_history
                                    if str(value).strip()
                                } if isinstance(source_history, (list, tuple)) else set()
                                latest_source = str(
                                    getattr(node, "source", "") or ""
                                ).strip().casefold()
                                # `node.source` is the latest stimulus in older
                                # schemas, not reliable lineage. Do not promote
                                # a mixed or legacy topic into a durable goal.
                                if sources & _USER_ORIGINATED_CURIOSITY_SOURCES or (
                                    latest_source in _USER_ORIGINATED_CURIOSITY_SOURCES
                                ):
                                    topic_quality_metrics["curiosity"][
                                        "user_origin_suppressed_count"
                                    ] += 1
                                    continue
                                if not history_complete or not sources:
                                    topic_quality_metrics["curiosity"][
                                        "provenance_unverified_suppressed_count"
                                    ] += 1
                                    continue
                                curiosity_topics.append(node.topic)
                                topic_source_provenance[
                                    " ".join(str(node.topic).casefold().split())
                                ] = {
                                    "kind": "internal_curiosity_state",
                                    "method": "curiosity_engine.stimulate",
                                    "ref": "topic:" + str(node.topic) + ";sources:" + ",".join(sorted(sources)),
                                }
                        topics = _admit_semantic_topics(
                            curiosity_topics, "curiosity", limit=6
                        )
                except Exception:
                    pass

            # PandoraBOX must be able to form self-directed goals between human
            # turns. These are broad cognitive domains, not copies of user
            # tasks, and are only used when no durable topic was recovered.
            # Build fallback subjects from the organism's motivations. This
            # gives autonomous goals a developmental direction grounded in
            # identity rather than turning a greeting or a stray phrase into
            # an objective.
            autonomous_topics = []
            for motivation in motivations:
                name = str(getattr(motivation, "name", "")).lower()
                if name == "understand_user":
                    autonomous_topics.append("relational understanding")
                elif name in {"improve_capabilities", "develop_capabilities"}:
                    autonomous_topics.append("cognitive capability development")
                elif name in {"maintain_coherence", "resolve_uncertainty"}:
                    autonomous_topics.append("identity coherence")
                elif name == "pursue_aspiration":
                    autonomous_topics.append("meaningful aspiration development")
                else:
                    autonomous_topics.append("knowledge integration")
            autonomous_topics.extend([
                "cognitive architecture",
                "reasoning coherence",
                "memory consolidation",
            ])
            # Preserve order while avoiding duplicate autonomous goals.
            autonomous_topics = list(dict.fromkeys(autonomous_topics))
            for topic in autonomous_topics:
                matching_motivations = [
                    motivation for motivation in motivations
                    if (
                        (motivation.name == "understand_user" and topic == "relational understanding")
                        or (motivation.name in {"improve_capabilities", "develop_capabilities"}
                            and topic == "cognitive capability development")
                        or (motivation.name in {"maintain_coherence", "resolve_uncertainty"}
                            and topic == "identity coherence")
                        or (motivation.name == "pursue_aspiration"
                            and topic == "meaningful aspiration development")
                        or (motivation.name not in {
                            "understand_user", "improve_capabilities", "develop_capabilities",
                            "maintain_coherence", "resolve_uncertainty", "pursue_aspiration",
                        } and topic == "knowledge integration")
                    )
                ]
                topic_source_provenance.setdefault(
                    " ".join(topic.casefold().split()),
                    {
                        "kind": "autonomous_motivation",
                        "method": "goal_engine.derive_motivations",
                        "ref": "motivations:" + ",".join(
                            f"{getattr(item, 'name', 'unknown')}@{getattr(item, 'origin', 'unspecified')}"
                            for item in matching_motivations
                        ) if matching_motivations else "autonomous_domain:" + topic,
                    },
                )
            # Autonomous subjects use the same meaning-based admission as
            # conversational and curiosity topics. No token list or minimum
            # word-length rule may override the semantic decision.
            autonomous_topics = _admit_semantic_topics(
                autonomous_topics, "autonomous", limit=8
            )
            # User-grounded topics provide conversational relevance, but they
            # must never suppress self-directed development.  Both streams
            # are candidates; provenance only prevents assistant prose from
            # masquerading as a user topic.
            user_topics = list(dict.fromkeys(topics))
            topics = user_topics + [
                topic for topic in autonomous_topics if topic not in user_topics
            ]
            if not user_topics:
                logger.info(
                    "[GoalEngine] no conversational topic available; using "
                    "autonomous cognitive domains"
                )
            else:
                logger.debug(
                    "[GoalEngine] merged %d user topic(s) with %d autonomous topic(s)",
                    len(user_topics), len(autonomous_topics),
                )

            # Source-level semantic admission has already classified user,
            # curiosity, and autonomous topics. A second lexical pass used to
            # discard admitted topics by token identity and word length.
            filtered_topics = list(topics)

            # ── 6. Generate and add goal candidates ───────────────────────────
            # Governor safety gate: high pressure or a saturated live-goal
            # pool blocks generation. Scheduler mode alone is not a veto.
            # The governor is accessed through ai_system when available.
            _gov = None
            try:
                _il = getattr(self.ai_system, '_internal_loop', None)
                if _il is None:
                    # Try the organism path
                    _org = getattr(self.ai_system, '_organism', None)
                    _il  = getattr(_org, '_internal_loop', None)
                _gov = getattr(_il, '_governor', None)
            except Exception:
                pass

            _generation_blocked = _gov is not None and _gov.block_goal_generation()

            # Never bypass the quality gate with raw mined fragments. If the
            # conversation produced no durable subject, autonomous domains are
            # the only valid fallback.
            use_topics = filtered_topics if filtered_topics else autonomous_topics
            if motivations and use_topics and not _generation_blocked:
                if topic_source_turns:
                    candidates = self.generate_candidates(
                        motivations, use_topics, limit=3,
                        topic_source_turns=topic_source_turns,
                        topic_source_provenance=topic_source_provenance,
                    )
                else:
                    candidates = self.generate_candidates(
                        motivations, use_topics, limit=3,
                        topic_source_provenance=topic_source_provenance,
                    )
                candidate_generation_metrics.update(
                    getattr(self, "_last_candidate_generation_report", {})
                )
                accepted = 0
                for goal in candidates:
                    if self.add_goal(goal):
                        accepted += 1
                if candidates:
                    logger.debug(
                        f"[GoalEngine] spawned {accepted}/{len(candidates)} goals from "
                        f"{len(motivations)} motivations x {len(use_topics)} topics"
                    )
            elif _generation_blocked:
                logger.debug(
                    "[GoalEngine] goal generation blocked by governor safety ceiling "
                    f"(mode={getattr(_gov, 'mode', 'unknown')}, "
                    f"pressure={getattr(_gov, '_pressure', 0):.2f})"
                )

            # ── 6. Update existing goals (decay + persistence) ─────────────────
            self.update_goals(pressures)

            metrics = self.get_metrics()
            self._set_tick_report({
                "status": "completed",
                "tick_at": _now,
                "motivation_count": len(motivations),
                "user_topic_count": len(user_topics),
                "filtered_topic_count": len(filtered_topics),
                "topic_quality": topic_quality_metrics,
                "candidate_generation": candidate_generation_metrics,
                "candidate_count": len(candidates),
                "accepted_candidate_count": accepted,
                "generation_blocked": bool(_generation_blocked),
                "active_goal_count": int(metrics.get("active", 0)),
                "total_goal_count": int(metrics.get("total_goals", 0)),
            })
            logger.info(
                f"[GoalEngine] tick: {metrics['active']} active, "
                f"{metrics['total_goals']} total, GEI={metrics['gei']:.3f}"
            )

        except Exception as e:
            self._set_tick_report({
                "status": "failed",
                "tick_at": _now,
                "error_type": type(e).__name__,
                "motivation_count": len(motivations),
                "filtered_topic_count": len(filtered_topics),
                "topic_quality": topic_quality_metrics,
                "candidate_generation": candidate_generation_metrics,
                "candidate_count": len(candidates),
                "accepted_candidate_count": accepted,
            })
            logger.error(f"[GoalEngine] tick failed: {e}", exc_info=True)

    def _set_tick_report(self, report: Dict[str, object]) -> None:
        """Store a privacy-safe result for the most recent autonomous tick."""
        lock = getattr(self, "_tick_report_lock", None)
        if lock is None:
            self._tick_report_lock = RLock()
            lock = self._tick_report_lock
        with lock:
            self._last_tick_report = dict(report)

    def get_last_tick_report(self) -> Dict[str, object]:
        """Return the latest tick outcome without exposing topic or exception text."""
        lock = getattr(self, "_tick_report_lock", None)
        if lock is None:
            return dict(getattr(self, "_last_tick_report", {"status": "not_run"}))
        with lock:
            return dict(self._last_tick_report)
