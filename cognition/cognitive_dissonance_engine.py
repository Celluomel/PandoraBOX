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
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from cognition.world_model import causal_belief_has_intervention_evidence

if TYPE_CHECKING:
    from cognition.thought_thread_engine import ThoughtThread, ThoughtThreadEngine, TTEContext

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
DISSONANCE_THRESHOLD = 0.35   # below this intensity → ignore
CONFIDENCE_PENALTY   = 0.12   # per dissonance event applied to thread
MAX_DISSONANCE_EVENTS = 20    # keep only most recent


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

    def __init__(self) -> None:
        self._events: List[DissonanceEvent] = []
        self.last_step_report: Dict[str, Any] = {
            "detected_event_count": 0,
            "meta_threads_spawned": 0,
            "auto_resolved_event_count": 0,
            "reobserved_event_count": 0,
            "deferred_low_intensity_count": 0,
            "verified_resolved_event_count": 0,
            "event_refs": [],
        }
        logger.info("[CDE] CognitiveDissonanceEngine initialised")

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

        if len(self._events) > MAX_DISSONANCE_EVENTS:
            self._events = self._events[-MAX_DISSONANCE_EVENTS:]

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
            "verified_resolved_event_count": sum(1 for event in report_events.values() if event.resolved),
            "event_refs": [
                {"id": str(event.id), "type": event.type.value,
                 "intensity": round(float(event.intensity), 3),
                 "resolved": bool(event.resolved),
                 "resolution_status": str(event.resolution_status),
                 "observation_count": int(event.observation_count),
                 "resolution_evidence_ref": str(event.resolution_evidence_ref or "")[:48]}
                for event in list(report_events.values())[-20:]
            ],
        }
        return result

    # ── Private detection helpers ─────────────────────────────────────────────

    def _detect_identity_vs_action(self, ctx: CDEContext) -> List[DissonanceEvent]:
        """Check if any belief in identity_state is contradicted by recent actions."""
        events = []
        beliefs = ctx.beliefs or ctx.identity_state.get("beliefs", [])
        recent = ctx.action_receipts or ctx.recent_actions

        def action_kind(item: Any) -> str:
            if isinstance(item, dict):
                return str(item.get("action") or item.get("action_type") or "").casefold()
            return str(item).casefold()

        def action_succeeded(item: Any) -> bool:
            # Typed execution receipts distinguish dispatched/failed actions
            # from completed behavior. Do not use an attempted operation as
            # evidence that an identity claim was enacted.
            return isinstance(item, dict) and item.get("success") is True

        exploration_actions = {
            "memory_recall", "web_search", "self_question",
            "bisociative_hypothesis", "explore", "research",
        }
        expression_actions = {"user_question", "express", "respond"}

        for belief in beliefs[:10]:
            bl = belief.lower()

            if "curious" in bl:
                # Curiosity claim: check if exploration actions happened
                explored = any(
                    action_succeeded(action)
                    and (
                        action_kind(action) in exploration_actions
                        or "explore" in action_kind(action)
                        or "research" in action_kind(action)
                    )
                    for action in recent[-5:]
                )
                if not explored and recent:
                    events.append(DissonanceEvent(
                        id          = uuid.uuid4().hex[:12],
                        type        = DissonanceEventType.IDENTITY_VS_ACTION,
                        belief_ref  = belief,
                        action_ref  = "no exploration action taken",
                        intensity   = 0.45,
                    ))

            elif "expressive" in bl or "expressive" in bl:
                communicated = any(
                    action_succeeded(action)
                    and (
                        action_kind(action) in expression_actions
                        or "express" in action_kind(action)
                        or "respond" in action_kind(action)
                    )
                    for action in recent[-5:]
                )
                if not communicated and recent:
                    events.append(DissonanceEvent(
                        id          = uuid.uuid4().hex[:12],
                        type        = DissonanceEventType.IDENTITY_VS_ACTION,
                        belief_ref  = belief,
                        action_ref  = "no expression action taken",
                        intensity   = 0.35,
                    ))

        return events

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
        Phase 5.3 — the event type that was missing: 'expected confidence
        0.82, actual 0.61'. Reads PredictiveMind's real _results history
        (Prediction.confidence vs PredictionResult.error_level) rather
        than inventing a new tracking mechanism.
        """
        events: List[DissonanceEvent] = []
        pm = getattr(ctx, "predictive_mind", None)
        results = list(getattr(pm, "_results", []))[-5:] if pm else []
        for r in results:
            pred_conf = getattr(getattr(r, "prediction", None), "confidence", None)
            err = getattr(r, "error_level", None)
            if pred_conf is None or err is None:
                continue
            realized = 1.0 - err   # actual outcome quality, in hindsight
            gap = pred_conf - realized
            if gap > 0.20:   # confidently expected better than what happened
                events.append(DissonanceEvent(
                    id        = uuid.uuid4().hex[:12],
                    type      = DissonanceEventType.PREDICTION_VS_REALITY,
                    predicted = {"confidence": round(pred_conf, 3)},
                    actual    = {"confidence": round(realized, 3)},
                    intensity = min(0.9, gap),
                ))
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
