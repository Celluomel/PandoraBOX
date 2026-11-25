"""
CognitiveDissonanceEngine (CDE)
================================
Detects conflicts between PandoraBOX's beliefs, identity, and actions, then
resolves them through identity mutation, belief revision, or meta-thread
creation.

Three detection modes:
  1. BELIEF_VS_EVIDENCE  — world model says X, recent action implies not-X
  2. IDENTITY_VS_ACTION  — self-model claims trait Y, behavior contradicts Y
  3. GOAL_VS_OUTCOME     — thread predicted result Z, actual result was not-Z

Effects when dissonance is detected:
  - Thread confidence decreases
  - Thread dissonance score rises
  - A meta-thread is spawned (e.g. "why did I act against my values?")
  - resolution triggers identity/belief mutation

Integration:
  - Called after TTE.step() in InternalThoughtLoop._slow_cycle()
  - Meta-threads are injected back into TTE
  - Resolved events trigger personality_evolution.queue_experience()
"""
from __future__ import annotations

import logging
import json
import math
import os
import time
import uuid
from datetime import datetime
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from cognition.world_model import causal_belief_has_intervention_evidence

if TYPE_CHECKING:
    from cognition.thought_thread_engine import ThoughtThread, ThoughtThreadEngine, TTEContext

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
DISSONANCE_THRESHOLD = 0.35   # below this intensity → ignore
CONFIDENCE_PENALTY   = 0.12   # per dissonance event applied to thread
MAX_DISSONANCE_EVENTS = 20    # keep only most recent
DEFAULT_PERSISTENCE_PATH = "data/persona/cognitive_dissonance_events.json"

_EXPLORATION_ACTIONS = {
    "memory_recall", "web_search", "self_question",
    "bisociative_hypothesis", "explore", "research",
}
_EXPRESSION_ACTIONS = {"user_question", "express", "respond"}


# ── Types ──────────────────────────────────────────────────────────────────────

class DissonanceEventType(str, Enum):
    BELIEF_VS_EVIDENCE     = "belief_vs_evidence"
    IDENTITY_VS_ACTION     = "identity_vs_action"
    GOAL_VS_OUTCOME        = "goal_vs_outcome"
    PREDICTION_VS_REALITY  = "prediction_vs_reality"   # Phase 5.3


@dataclass
class DissonanceEvent:
    id:           str
    type:         DissonanceEventType
    thread_id:    Optional[str]   = None
    belief_ref:   Optional[str]   = None
    evidence_ref: Optional[str]   = None
    identity_ref: Optional[str]   = None
    action_ref:   Optional[str]   = None
    predicted:    Optional[Dict]  = None
    actual:       Optional[Dict]  = None
    intensity:    float           = 0.5
    resolved:     bool            = False
    resolution_status: str        = "pending"
    resolution_evidence_ref: str  = ""
    observation_count: int         = 1
    last_observed_at: float        = field(default_factory=time.time)
    created_at:   float           = field(default_factory=time.time)
    # Phase 5.3 — Recursive Self-Inquiry: the mismatch, made examinable.
    # owner_statement binds the prediction to the persistent self ("I
    # expected...", not "confidence decreased") — the difference the
    # proposal called out between monitoring and genuine self-inquiry.
    owner_statement: Optional[str]        = None
    self_question:   Optional[str]        = None
    hypotheses:      List[str]            = field(default_factory=list)


@dataclass
class CDEContext:
    threads:        List[Any]       = field(default_factory=list)  # ThoughtThread list
    world_model:    Dict[str, Any]  = field(default_factory=dict)
    identity_state: Dict[str, Any]  = field(default_factory=dict)
    recent_actions: List[Dict]      = field(default_factory=list)
    action_receipts: List[Dict]     = field(default_factory=list)
    metrics:        Dict[str, float] = field(default_factory=dict)
    beliefs:        List[str]       = field(default_factory=list)
    predictive_mind: Any            = None   # Phase 5.3 — for PREDICTION_VS_REALITY


# ── Engine ────────────────────────────────────────────────────────────────────

class CognitiveDissonanceEngine:
    """
    Detects and resolves cognitive dissonances within the TTE/DTS pipeline.
    Instantiated once and owned by the InternalThoughtLoop.
    """

    def __init__(self, persistence_path: str | None = None) -> None:
        # Keep the engine deterministic in isolated/unit use. Production wires
        # an explicit persona data path from InternalThoughtLoop.
        self._path = Path(persistence_path) if persistence_path else None
        self._lock = threading.RLock()
        self._events: List[DissonanceEvent] = []
        self._last_persistence_status = "not_attempted"
        self._prediction_detector_status = "not_run"
        self._load_failed = False
        if self._path is None:
            self._last_persistence_status = "disabled_in_memory_only"
        else:
            self._load_events()
        self.last_step_report: Dict[str, Any] = {
            "detected_event_count": 0,
            "meta_threads_spawned": 0,
            "auto_resolved_event_count": 0,
            "reobserved_event_count": 0,
            "deferred_low_intensity_count": 0,
            "verified_resolved_event_count": 0,
            "verified_action_counterevidence_count": 0,
            "goal_action_receipt_count": 0,
            "resolved_event_history_count": 0,
            "event_refs": [],
            "event_store_status": self._last_persistence_status,
            "event_store_event_count": len(self._events),
            "prediction_detector_status": self._prediction_detector_status,
            "identity_action_detector_status": "not_run",
        }
        logger.info(
            "[CDE] CognitiveDissonanceEngine initialised — event_store=%s events=%d",
            self._last_persistence_status,
            len(self._events),
        )

    def _load_events(self) -> None:
        """Restore stable CDE event IDs so persisted TTE links remain resolvable."""
        if self._path is None:
            self._last_persistence_status = "disabled_in_memory_only"
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            rows = raw.get("events", []) if isinstance(raw, dict) else []
            if not isinstance(rows, list):
                raise ValueError("CDE event journal events must be a list")
            loaded = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    values = dict(row)
                    values["type"] = DissonanceEventType(values["type"])
                    event = DissonanceEvent(**values)
                except (KeyError, TypeError, ValueError):
                    continue
                if event.id:
                    loaded.append(event)
            self._events = self._retain_events(loaded)
            self._last_persistence_status = "loaded" if loaded else "loaded_empty"
        except FileNotFoundError:
            self._last_persistence_status = "new_store"
        except Exception as exc:
            self._load_failed = True
            self._last_persistence_status = f"load_failed:{type(exc).__name__}"
            logger.warning("[CDE] Event journal load failed: %s", type(exc).__name__)

    def _save_events(self) -> bool:
        """Atomically persist the bounded journal and verify the bytes round-trip."""
        if self._path is None:
            self._last_persistence_status = "disabled_in_memory_only"
            return False
        if self._load_failed:
            self._last_persistence_status = "load_failed_preserved"
            return False
        temporary_path = self._path.with_name(self._path.name + ".tmp")
        try:
            with self._lock:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                retained_events = self._retained_events_locked()
                payload = {
                    "schema": "lumina_cde_events.v1",
                    "events": [asdict(event) | {"type": event.type.value}
                               for event in retained_events],
                }
                serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
                temporary_path.write_text(serialized, encoding="utf-8")
                os.replace(temporary_path, self._path)
                saved = json.loads(self._path.read_text(encoding="utf-8"))
                if saved != json.loads(serialized):
                    raise OSError("CDE event journal read-back mismatch")
                self._events = retained_events
            self._last_persistence_status = "persisted"
            return True
        except Exception as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._last_persistence_status = f"persistence_failed:{type(exc).__name__}"
            logger.warning("[CDE] Event journal persistence failed: %s", type(exc).__name__)
            return False

    @staticmethod
    def _retain_events(events: List[DissonanceEvent]) -> List[DissonanceEvent]:
        """Keep every open event (TTE may reference it), plus recent resolved history."""
        unresolved = [event for event in events if not event.resolved]
        resolved = [event for event in events if event.resolved]
        retained_ids = {event.id for event in unresolved}
        retained_ids.update(event.id for event in resolved[-MAX_DISSONANCE_EVENTS:])
        return sorted(
            (event for event in events if event.id in retained_ids),
            key=lambda event: (event.created_at, event.id),
        )

    def _retained_events_locked(self) -> List[DissonanceEvent]:
        return self._retain_events(self._events)

    # ── Detection ─────────────────────────────────────────────────────────────

    def detect(self, ctx: CDEContext) -> List[DissonanceEvent]:
        """
        Scan for all three dissonance types. Returns new events only.
        """
        candidates: List[DissonanceEvent] = []

        # 1. IDENTITY_VS_ACTION: check each thread's actual behaviour
        candidates.extend(self._detect_identity_vs_action(ctx))

        # 2. GOAL_VS_OUTCOME: check thread predictions vs current_state outcomes
        candidates.extend(self._detect_goal_vs_outcome(ctx))

        # 3. BELIEF_VS_EVIDENCE: world model causal beliefs vs recent events
        candidates.extend(self._detect_belief_vs_evidence(ctx))

        # 4. PREDICTION_VS_REALITY (Phase 5.3): predicted vs actual confidence
        candidates.extend(self._detect_prediction_vs_reality(ctx))

        # Detectors are sampled repeatedly. Preserve an unresolved event's ID
        # across cycles so repeated observation is not mistaken for new
        # evidence, repeated confidence penalties, or repeated learning.
        def signature(event: DissonanceEvent) -> tuple:
            def stable(value: Any) -> str:
                if value is None:
                    return ""
                if isinstance(value, dict):
                    return repr(sorted((str(k), stable(v)) for k, v in value.items()))
                if isinstance(value, (list, tuple)):
                    return repr(tuple(stable(item) for item in value))
                return str(value).strip().casefold()

            return (
                event.type.value,
                stable(event.thread_id), stable(event.belief_ref),
                stable(event.evidence_ref), stable(event.action_ref),
                stable(event.predicted), stable(event.actual),
            )

        unresolved_by_signature = {
            signature(event): event for event in self._events if not event.resolved
        }
        new_events: List[DissonanceEvent] = []
        self._last_reobserved_count = 0
        for candidate in candidates:
            prior = unresolved_by_signature.get(signature(candidate))
            if prior is None:
                self._events.append(candidate)
                unresolved_by_signature[signature(candidate)] = candidate
                new_events.append(candidate)
                continue
            prior.observation_count += 1
            prior.last_observed_at = candidate.last_observed_at
            prior.intensity = max(prior.intensity, candidate.intensity)
            self._last_reobserved_count += 1
            if (
                prior.resolution_status == "deferred_low_intensity"
                and prior.intensity >= DISSONANCE_THRESHOLD + 0.1
            ):
                prior.resolution_status = "pending"
                new_events.append(prior)

        # The cap applies to resolved history only. Open events can be
        # referenced by durable TTE meta-threads, so truncating by list age
        # would orphan their event IDs before resolution.
        self._events = self._retain_events(self._events)

        if new_events:
            logger.debug(f"[CDE] Detected {len(new_events)} new dissonance event(s)")

        return new_events

    def apply_to_threads(
        self, events: List[DissonanceEvent], threads: List[Any]
    ) -> List[Any]:
        """
        Apply dissonance effects to affected threads:
        - reduce confidence
        - raise dissonance score
        - block resolution until addressed
        """
        if not events:
            return threads

        affected: Dict[str, DissonanceEvent] = {
            e.thread_id: e for e in events if e.thread_id
        }

        for thread in threads:
            if thread.id in affected:
                ev = affected[thread.id]
                thread.confidence  = max(0.05, thread.confidence  - CONFIDENCE_PENALTY * ev.intensity)
                thread.dissonance  = min(1.0,  thread.dissonance  + ev.intensity * 0.3)
                logger.debug(
                    f"[CDE] Thread {thread.id[:8]} penalised "
                    f"(conf={thread.confidence:.2f}, dissonance={thread.dissonance:.2f})"
                )

        return threads

    def spawn_meta_threads(
        self,
        events: List[DissonanceEvent],
        tte: Any,  # ThoughtThreadEngine
        ctx: Any,  # TTEContext
    ) -> List[Any]:
        """
        For high-intensity dissonances, create meta-threads of self-reflection.
        These are injected into the TTE so the executive loop can act on them.
        """
        meta_threads = []
        for ev in events:
            if ev.intensity < DISSONANCE_THRESHOLD + 0.15:
                continue  # minor dissonance — no meta-thread needed
            goal = (
                f"Reflect on dissonance: {ev.type.value}. "
                f"Belief={ev.belief_ref or 'unknown'}, Action={ev.action_ref or 'unknown'}."
            )
            if ev.self_question:
                goal += f" Inquiry: {ev.self_question}"
            if ev.hypotheses:
                goal += " Candidate explanations: " + " | ".join(ev.hypotheses[:3])
            mt = tte.spawn_thread(ctx, {
                "topic":           f"dissonance:{ev.id[:8]}",
                "goal":            goal,
                "source":          "dissonance",
                "curiosity":       0.1,
                "energy_cost":     8.0,
                "current_state":   {
                    "cde_event_id": ev.id,
                    "inquiry_question": ev.self_question or "",
                    "candidate_explanations": list(ev.hypotheses[:3]),
                },
                "planned_actions": [
                    "identify root cause",
                    "revise belief or behavior",
                    "update self-model",
                ],
            })
            meta_threads.append(mt)
            logger.debug(f"[CDE] Meta-thread spawned for event {ev.id[:8]}: {ev.type.value}")
        return meta_threads

    def resolve(
        self,
        events: List[DissonanceEvent],
        ctx: CDEContext,
        organism: Any = None,
        *,
        outcome_threads: List[Any] | None = None,
        tte: Any = None,
        tte_ctx: Any = None,
    ) -> None:
        """
        Close only events backed by a successful TTE inquiry thread carrying a
        structured verified outcome tied to that event's stable ID.

        A generated question, hypothesis, or elapsed cycle is not evidence that
        the underlying conflict was resolved and must not train personality.
        """
        receipts: Dict[str, Dict[str, Any]] = {}
        for thread in outcome_threads or []:
            state = getattr(thread, "current_state", None)
            outcome = state.get("verified_outcome") if isinstance(state, dict) else None
            event_id = str(state.get("cde_event_id") or "").strip() if isinstance(state, dict) else ""
            if (
                getattr(thread, "source", "") != "dissonance"
                or not event_id
                or not isinstance(outcome, dict)
                or outcome.get("status") != "success"
            ):
                continue
            evidence_ref = str(outcome.get("evidence_ref") or "").strip()
            resolution = str(outcome.get("belief_statement") or "").strip()
            confidence = outcome.get("confidence")
            if (
                evidence_ref and resolution
                and isinstance(confidence, (int, float))
                and not isinstance(confidence, bool)
                and 0.0 <= float(confidence) <= 1.0
            ):
                receipts[event_id] = {
                    "evidence_ref": evidence_ref,
                    "resolution": resolution,
                    "confidence": float(confidence),
                    "thread": thread,
                }
        for ev in events:
            if ev.resolved:
                continue

            receipt = receipts.get(ev.id)
            evidence_ref = str(receipt.get("evidence_ref") or "").strip() if receipt else ""
            outcome = str(receipt.get("resolution") or "").strip() if receipt else ""
            if not (evidence_ref and outcome):
                ev.resolution_status = "unverified_no_resolution_receipt"
                continue

            # Keep the TTE lifecycle and CDE event lifecycle in sync, but only
            # after the same event-linked verified outcome has passed the
            # receipt checks above. A generated question/hypothesis or a goal
            # action receipt alone never reaches this path.
            if tte is not None and tte_ctx is not None:
                thread = receipt.get("thread")
                try:
                    resolved_thread = tte.resolve_thread(
                        thread, tte_ctx, success=True,
                        evidence_ref=evidence_ref,
                        outcome_statement=outcome,
                        outcome_confidence=receipt.get("confidence"),
                    )
                    thread_status = getattr(resolved_thread, "status", None)
                    if getattr(thread_status, "value", thread_status) != "completed":
                        ev.resolution_status = "verified_thread_not_completed"
                        continue
                except Exception as exc:
                    ev.resolution_status = "verified_thread_sync_failed"
                    logger.warning(
                        "[CDE] Verified event %s could not close its TTE inquiry thread (%s)",
                        ev.id[:8], type(exc).__name__,
                    )
                    continue

            ev.resolved = True
            ev.resolution_status = "verified_resolved"
            ev.resolution_evidence_ref = evidence_ref

            # Trigger personality evolution — dissonance is a learning signal.
            # Keys must match exactly the entries in EXPERIENCE_PRESSURE dict.
            if organism is not None:
                try:
                    sys = getattr(organism, "ai_system", None) or getattr(organism, "_system", None)
                    if sys:
                        pe = getattr(sys, "personality_evolution", None)
                        if pe:
                            _type_key_map = {
                                "identity_vs_action": "resolved dissonance (identity_vs_action)",
                                "belief_vs_evidence": "resolved dissonance (belief_vs_evidence)",
                                "goal_vs_outcome":    "resolved dissonance (goal_vs_outcome)",
                            }
                            _exp_key = _type_key_map.get(ev.type.value, "contradiction_resolved")
                            pe.queue_experience(_exp_key, intensity=ev.intensity)
                            if ev.intensity > 0.6:
                                if ev.type.value == "identity_vs_action":
                                    pe.queue_experience("identity_dissonance_resolved", intensity=ev.intensity * 0.6)
                                elif ev.type.value == "belief_vs_evidence":
                                    pe.queue_experience("epistemic_dissonance_resolved", intensity=ev.intensity * 0.6)
                except Exception as e:
                    logger.debug(f"[CDE] Personality evolution update failed: {e}")

                # A belief/evidence pair that resolves dissonance is not an
                # intervention comparison and must not become a causal claim.

        logger.debug(f"[CDE] Verified resolutions: {sum(1 for e in events if e.resolved)}")
        # Persist both newly detected and resolved events. TTE stores the
        # event ID on its meta-thread; losing this journal on restart would
        # leave that durable thread detached from its source observation.
        self._save_events()

    def step(
        self,
        threads: List[Any],
        tte: Any,
        ctx: CDEContext,
        tte_ctx: Any,
        organism: Any = None,
    ) -> List[Any]:
        """
        Main tick — called after TTE.step() in the slow cycle.
        Returns the updated thread list.
        """
        previously_resolved_event_objects = {
            id(event) for event in self._events if event.resolved
        }
        events = self.detect(ctx)
        threads = self.apply_to_threads(events, threads)
        for event in events:
            if event.intensity < DISSONANCE_THRESHOLD + 0.15:
                continue
            self._generate_self_question(event)
            if organism is not None:
                self._generate_competing_hypotheses(event, organism)
        meta_threads = self.spawn_meta_threads(events, tte, tte_ctx)

        # Resolution is tied to a successful CDE inquiry thread, not a
        # generated hypothesis or an arbitrary caller-supplied dictionary.
        all_threads = []
        if tte is not None and hasattr(tte, "all_threads"):
            try:
                all_threads = list(tte.all_threads())
            except Exception as exc:
                logger.debug("[CDE] Could not read TTE outcome receipts: %s", exc)
        self._record_action_counterevidence(
            self._events, ctx, all_threads, tte, tte_ctx
        )
        self.resolve(
            self._events, ctx, organism, outcome_threads=all_threads,
            tte=tte, tte_ctx=tte_ctx,
        )
        report_events = {event.id: event for event in self._events}
        report_events.update({event.id: event for event in events})

        # Low-intensity events are deferred, not declared resolved. A future
        # stronger observation can reactivate the same event without creating
        # another penalty or treating scheduler time as evidence.
        deferred = [e for e in events if e.intensity < DISSONANCE_THRESHOLD + 0.1]
        for event in deferred:
            if not event.resolved:
                event.resolution_status = "deferred_low_intensity"

        # New meta-threads are already persisted by the TTE, but returning
        # only the input list delayed their first DTS selection until the
        # next slow cycle. Include them now so detection → reflection →
        # selection is one observable cycle.
        result = list(threads)
        known_ids = {getattr(thread, "id", None) for thread in result}
        result.extend(thread for thread in meta_threads
                      if getattr(thread, "id", None) not in known_ids)
        self.last_step_report = {
            "detected_event_count": len(events),
            "reobserved_event_count": int(getattr(self, "_last_reobserved_count", 0)),
            "meta_threads_spawned": len(meta_threads),
            "auto_resolved_event_count": 0,
            "deferred_low_intensity_count": len(deferred),
            # Distinguish outcomes observed in this tick from retained journal
            # history. Counting every previously-resolved event made a stale
            # success look like a fresh cognitive effect on every later cycle.
            "verified_resolved_event_count": sum(
                1 for event in self._events
                if event.resolved and id(event) not in previously_resolved_event_objects
            ),
            "resolved_event_history_count": sum(
                1 for event in self._events if event.resolved
            ),
            "verified_action_counterevidence_count": int(
                getattr(self, "_last_counterevidence_count", 0)
            ),
            "goal_action_receipt_count": int(
                getattr(self, "_last_goal_action_receipt_count", 0)
            ),
            "event_refs": [
                {"id": str(event.id), "type": event.type.value,
                 "intensity": round(float(event.intensity), 3),
                 "resolved": bool(event.resolved),
                 "resolution_status": str(event.resolution_status),
                 "observation_count": int(event.observation_count),
                 "resolution_evidence_ref": str(event.resolution_evidence_ref or "")[:48]}
                for event in list(report_events.values())[-20:]
            ],
            "event_store_status": self._last_persistence_status,
            "event_store_event_count": len(self._events),
            "prediction_detector_status": self._prediction_detector_status,
            "identity_action_detector_status": str(
                getattr(self, "_identity_action_detector_status", "unreported")
            ),
        }
        return result

    def _record_action_counterevidence(
        self,
        events: List[DissonanceEvent],
        ctx: CDEContext,
        threads: List[Any],
        tte: Any,
        tte_ctx: Any,
    ) -> int:
        """Record narrow, event-linked counterevidence from a later action receipt.

        This closes only identity/action events whose detector explicitly
        observed a missing recent action. It does not infer a stable trait or
        resolve belief/outcome events from unrelated action success.
        """
        self._last_counterevidence_count = 0
        self._last_goal_action_receipt_count = 0
        if tte is None or tte_ctx is None or not hasattr(tte, "resolve_thread"):
            return 0

        candidates = {
            "no exploration action taken": _EXPLORATION_ACTIONS,
            "no expression action taken": _EXPRESSION_ACTIONS,
        }
        action_fragments = {
            "no exploration action taken": ("explore", "research"),
            "no expression action taken": ("express", "respond"),
        }
        by_event = {}
        goal_action_receipts = []
        for thread in threads:
            state = getattr(thread, "current_state", None)
            stored_receipts = state.get("action_receipts", []) if isinstance(state, dict) else []
            if isinstance(stored_receipts, list):
                goal_action_receipts.extend(
                    receipt for receipt in stored_receipts
                    if isinstance(receipt, dict)
                )
            event_id = state.get("cde_event_id") if isinstance(state, dict) else None
            if (getattr(thread, "source", "") == "dissonance" and event_id
                    and event_id not in by_event):
                by_event[str(event_id)] = thread

        # GoalActionExecutor persists terminal receipts on TTE goal threads.
        # Keep that source separate from the ConsequenceTracker: these receipts
        # are used only to close a matching, later identity/action observation.
        self._last_goal_action_receipt_count = len(goal_action_receipts)
        seen_receipts = set()
        action_receipts = []
        for source, receipts in (
            ("consequence", ctx.action_receipts),
            ("goal_thread", goal_action_receipts),
        ):
            for receipt in receipts or []:
                if not isinstance(receipt, dict):
                    continue
                identity = str(
                    receipt.get("event_id") or receipt.get("evidence_ref")
                    or receipt.get("execution_id") or ""
                ).strip()
                key = (source, identity) if identity else (source, id(receipt))
                if key in seen_receipts:
                    continue
                seen_receipts.add(key)
                action_receipts.append((source, receipt))

        for event in events:
            if event.resolved or event.type != DissonanceEventType.IDENTITY_VS_ACTION:
                continue
            expected_actions = candidates.get(str(event.action_ref or "").strip().casefold())
            thread = by_event.get(str(event.id))
            if not expected_actions or thread is None:
                continue
            for source, receipt in action_receipts:
                if not isinstance(receipt, dict) or receipt.get("success") is not True:
                    continue
                action = str(receipt.get("action") or receipt.get("action_type") or "").casefold()
                if action not in expected_actions and not any(
                    part in action for part in action_fragments[str(event.action_ref).casefold()]
                ):
                    continue
                timestamp = receipt.get("timestamp") or receipt.get("recorded_at")
                try:
                    if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
                        observed_at = float(timestamp)
                    else:
                        observed_at = datetime.fromisoformat(
                            str(timestamp or "").strip().replace("Z", "+00:00")
                        ).timestamp()
                except (TypeError, ValueError, OverflowError, OSError):
                    continue
                # Require a later timestamp and an explicit receipt reference;
                # same-second ISO receipts remain ambiguous and are rejected.
                event_ref = str(
                    receipt.get("event_id") or receipt.get("evidence_ref")
                    or receipt.get("execution_id") or ""
                ).strip()
                if observed_at <= event.created_at or not event_ref:
                    continue

                evidence_ref = (
                    f"consequence:{event_ref}" if source == "consequence"
                    else f"goal_action:{event_ref}"
                )[:200]
                outcome = (
                    f"A successful {action} action receipt was recorded after this "
                    "specific recent-absence observation. It is counterevidence to "
                    "that observation only; it does not establish a stable personality trait."
                )
                try:
                    resolved = tte.resolve_thread(
                        thread, tte_ctx, success=True, evidence_ref=evidence_ref,
                        outcome_statement=outcome, outcome_confidence=0.75,
                    )
                except Exception as exc:
                    logger.warning(
                        "[CDE] Could not record event-linked action evidence for %s (%s)",
                        event.id[:8], type(exc).__name__,
                    )
                    break
                if getattr(getattr(resolved, "status", None), "value", None) == "completed":
                    self._last_counterevidence_count += 1
                break
        return self._last_counterevidence_count

    # ── Private detection helpers ─────────────────────────────────────────────

    def _detect_identity_vs_action(self, ctx: CDEContext) -> List[DissonanceEvent]:
        """Detect only explicit identity/behavior contradictions.

        Goal-action receipts are a sparse log of selected operations, not a
        complete observation window of behavior. In particular, a failed
        operation or the absence of a matching operation among the last five
        receipts cannot establish that a trait was contradicted. Successful
        receipts may still close an already-open, event-linked inquiry in
        ``_record_action_counterevidence``; that is separate from detecting a
        new contradiction.
        """
        beliefs = ctx.beliefs or ctx.identity_state.get("beliefs", [])
        recent = ctx.action_receipts or ctx.recent_actions
        tracks_behavioral_trait = any(
            isinstance(belief, str)
            and any(trait in belief.casefold() for trait in ("curious", "expressive"))
            for belief in beliefs[:10]
        )
        # No producer currently supplies a complete, independently observed
        # behavioral window with an explicit contradiction. Keep the gap
        # visible instead of manufacturing evidence from sparse action logs.
        self._identity_action_detector_status = (
            "insufficient_behavioral_observation" if tracks_behavioral_trait
            else "not_applicable"
        )
        if recent and tracks_behavioral_trait:
            logger.debug(
                "[CDE] Identity/action contradiction not evaluated: sparse action receipts "
                "do not establish behavioral absence"
            )
        return []

    def _detect_goal_vs_outcome(self, ctx: CDEContext) -> List[DissonanceEvent]:
        """Check if any thread's predicted outcome differs from current_state."""
        events = []
        for thread in ctx.threads:
            predicted = thread.current_state.get("predicted_outcome")
            actual    = thread.current_state.get("actual_outcome")
            if predicted and actual and predicted != actual:
                events.append(DissonanceEvent(
                    id          = uuid.uuid4().hex[:12],
                    type        = DissonanceEventType.GOAL_VS_OUTCOME,
                    thread_id   = thread.id,
                    predicted   = {"value": predicted},
                    actual      = {"value": actual},
                    intensity   = min(0.9, thread.dissonance + 0.3),
                ))
        return events

    def _detect_belief_vs_evidence(self, ctx: CDEContext) -> List[DissonanceEvent]:
        """Check if causal beliefs in the world model are contradicted by recent evidence."""
        events = []
        causal = ctx.world_model.get("causal_beliefs", [])
        recent = ctx.recent_actions

        for belief in causal[:15]:
            if not causal_belief_has_intervention_evidence(belief):
                continue
            if isinstance(belief, dict):
                ant = belief.get("antecedent", "")
                con = belief.get("consequent", "")
                conf = belief.get("confidence", 0.5)
            else:
                ant = getattr(belief, "antecedent", "")
                con = getattr(belief, "consequent", "")
                conf = getattr(belief, "confidence", 0.5)

            if not ant or not con:
                continue

            # Low confidence causal belief — flag for review
            if conf < 0.25:
                events.append(DissonanceEvent(
                    id           = uuid.uuid4().hex[:12],
                    type         = DissonanceEventType.BELIEF_VS_EVIDENCE,
                    belief_ref   = ant,
                    evidence_ref = con,
                    intensity    = max(0.1, 0.5 - conf),
                ))
                continue

            # Recent-evidence contradiction: the antecedent condition showed
            # up in recent activity but the belief's expected consequent
            # didn't follow — the belief predicts X→Y, X happened, Y didn't.
            recent_text = [str(a).lower() for a in recent[-8:]]
            ant_seen = any(str(ant).lower() in t for t in recent_text)
            con_seen = any(str(con).lower() in t for t in recent_text)
            if ant_seen and not con_seen and recent_text:
                events.append(DissonanceEvent(
                    id           = uuid.uuid4().hex[:12],
                    type         = DissonanceEventType.BELIEF_VS_EVIDENCE,
                    belief_ref   = ant,
                    evidence_ref = f"expected '{con}' after '{ant}' in recent activity, didn't observe it",
                    intensity    = max(0.1, min(0.6, 0.4 * conf)),
                ))
        return events[:5]  # cap to avoid event flood

    def _detect_prediction_vs_reality(self, ctx: "CDEContext") -> List[DissonanceEvent]:
        """
        Compare predicted and observed intent only when an independent,
        same-domain outcome receipt exists. Prediction confidence and error
        magnitude are different quantities and must never be compared as if
        one were the realized value of the other.
        """
        events: List[DissonanceEvent] = []
        pm = getattr(ctx, "predictive_mind", None)
        if pm is None:
            self._prediction_detector_status = "unavailable_no_predictive_mind"
            return events
        results = list(getattr(pm, "_results", []))[-5:]
        if not results:
            self._prediction_detector_status = "unavailable_no_outcome_results"
            return events
        rejected = 0
        for r in results:
            evidence_status = getattr(r, "evidence_status", "unvalidated")
            evidence_ref = str(getattr(r, "evidence_ref", "") or "").strip()
            outcome_scope = getattr(r, "outcome_scope", "")
            prediction = getattr(r, "prediction", None)
            predicted_intent = str(getattr(prediction, "expected_intent", "") or "").strip()
            actual_intent = str(getattr(r, "actual_intent", "") or "").strip()
            pred_conf = getattr(prediction, "confidence", None)
            error_level = getattr(r, "error_level", None)
            if (
                evidence_status != "independently_validated"
                or not evidence_ref
                or outcome_scope != "intent"
                or not predicted_intent
                or not actual_intent
                or not isinstance(pred_conf, (int, float))
                or not math.isfinite(float(pred_conf))
                or not 0.0 <= float(pred_conf) <= 1.0
                or not isinstance(error_level, (int, float))
                or not math.isfinite(float(error_level))
                or not 0.0 <= float(error_level) <= 1.0
            ):
                rejected += 1
                continue
            if predicted_intent.casefold() != actual_intent.casefold() and float(pred_conf) >= 0.6:
                events.append(DissonanceEvent(
                    id        = uuid.uuid4().hex[:12],
                    type      = DissonanceEventType.PREDICTION_VS_REALITY,
                    evidence_ref = evidence_ref,
                    predicted = {"intent": predicted_intent, "confidence": round(float(pred_conf), 3)},
                    actual    = {"intent": actual_intent, "error_level": round(float(error_level), 3)},
                    intensity = min(0.9, float(pred_conf) * max(float(error_level), 0.35)),
                ))
        self._prediction_detector_status = (
            "unavailable_no_independent_same_domain_outcomes"
            if rejected == len(results) and not events
            else "validated_same_domain_outcome_checked"
        )
        return events[:3]

    # ── Phase 5.3: self-question / ownership / competing hypotheses ────────

    def _generate_self_question(self, event: DissonanceEvent) -> None:
        """
        Binds the mismatch to the persistent self ('I expected...') rather
        than leaving it as an impersonal monitoring statement ('confidence
        decreased'). Tailored per event type, not a generic template.
        """
        t = event.type
        if t == DissonanceEventType.PREDICTION_VS_REALITY:
            pc = (event.predicted or {}).get("confidence")
            ac = (event.actual or {}).get("confidence")
            pc_text = f"{pc:.2f}" if isinstance(pc, (int, float)) else "unknown"
            ac_text = f"{ac:.2f}" if isinstance(ac, (int, float)) else "unknown"
            event.owner_statement = f"I expected to be confident here (~{pc_text}), but it didn't hold up (~{ac_text})."
            event.self_question = "Why did my confidence fall short here — what did I misjudge?"
        elif t == DissonanceEventType.BELIEF_VS_EVIDENCE:
            event.owner_statement = f"I believed '{event.belief_ref}', but recent evidence didn't back it up."
            event.self_question = f"Why do I still hold '{event.belief_ref}' when the evidence is thinning?"
        elif t == DissonanceEventType.IDENTITY_VS_ACTION:
            event.owner_statement = f"I think of myself as someone who '{event.belief_ref}', but I didn't act like it."
            event.self_question = f"Why did I act against '{event.belief_ref}' just now?"
        elif t == DissonanceEventType.GOAL_VS_OUTCOME:
            event.owner_statement = "I was pursuing this goal expecting a different result than what happened."
            event.self_question = "Why is this goal not producing what I expected — is the goal or my approach wrong?"

    def _generate_competing_hypotheses(self, event: DissonanceEvent, organism: Any) -> None:
        """
        Scoped, honest version of 'competing hypotheses': two candidates
        pulled from distinct real data sources rather than invented —
        (1) a causal-belief explanation from the world model, (2) a
        skill-rustiness explanation from the skill registry. Not creative
        hypothesis generation; a bounded, evidence-grounded starting set.
        """
        hyps = []
        topic = (event.belief_ref or "").strip()
        try:
            wm = getattr(organism, "world_model", None)
            if wm and topic and hasattr(wm, "causal_beliefs"):
                # causal_beliefs is a List[CausalBelief] with antecedent/consequent,
                # not a dict and not a `.cause` field — v87 had both wrong.
                for cb in list(getattr(wm, "causal_beliefs", []))[:20]:
                    if not causal_belief_has_intervention_evidence(cb):
                        continue
                    antecedent = str(getattr(cb, "antecedent", ""))
                    if topic and topic.lower() in antecedent.lower():
                        hyps.append(f"Perhaps this connects to what I already believe about '{antecedent}' — that belief may itself be outdated.")
                        break
        except Exception:
            pass
        try:
            sr = getattr(organism, "skill_registry", None)
            if sr and topic:
                relevant = sr.relevant_skills(topic, n=1) if hasattr(sr, "relevant_skills") else []
                for sk in relevant:
                    if hasattr(sk, "is_rusty") and sk.is_rusty():
                        hyps.append(f"Perhaps my grasp of '{topic}' has gone rusty from disuse, not that my reasoning was wrong.")
        except Exception:
            pass
        if not hyps:
            hyps.append("Perhaps this was a one-off — worth watching before concluding anything changed.")
        event.hypotheses = hyps[:2]

    def pending_count(self) -> int:
        return sum(1 for e in self._events if not e.resolved)
