"""
cognition/empathy_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Empathy Engine — real-time user affect modeling for PandoraBOX.

PandoraBOX's self-chosen first skill.

What this adds
──────────────
Previously PandoraBOX processed the *content* of messages.
This engine models the *person* sending them.

Per-message pipeline:
  1. Preserve emotion as unassessed without an explicit or model-backed source
  2. Accept a separate semantic communicative-posture estimate
  3. Update only sourced affect and posture history
  4. Generate a concise prompt note from supported evidence
     injected into PandoraBOX's system prompt every turn
  5. Feed quality signals back into RelationalMemory
  6. Nudge attractor traits (curiosity ↑ when user is exploratory, etc.)

Emotion remains unassessed unless a user self-report or accepted multilingual
valence estimate exists. Interaction posture is supplied separately by the
cross-lingual semantic turn router and remains a tentative estimate.

Public API
──────────
  ee = EmpathyEngine(organism, llm, relational_memory)
  read = ee.read_user(user_id, user_text)          # call before LLM response
  fragment = ee.get_prompt_fragment(user_id)        # inject into system prompt
  ee.record_outcome(user_id, user_text, ai_response) # call after response
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Subtext signal taxonomy ────────────────────────────────────────────────
SIGNAL_EXPLORING      = "exploring"       # thinking out loud, no fixed answer yet
SIGNAL_SEEKING_ANSWER = "seeking_answer"  # wants a specific resolution
SIGNAL_VALIDATING     = "validating"      # checking their own idea, wants resonance
SIGNAL_VENTING        = "venting"         # emotional release, not solution-seeking
SIGNAL_CHALLENGING     = "challenging"    # testing PandoraBOX's reasoning or values
SIGNAL_PLAYFUL        = "playful"         # light tone, enjoying the exchange
SIGNAL_DISTRESSED     = "distressed"      # signs of stress, overload, or difficulty
SIGNAL_WITHDRAWN      = "withdrawn"       # short replies, disengagement signals


@dataclass
class AffectRead:
    """Single-turn read separating sourced affect from inferred conversation posture."""
    user_id:        str
    timestamp:      float = field(default_factory=time.time)

    # Emotional state
    valence:        str   = "unassessed"  # positive / neutral / negative / unassessed
    arousal:        str   = "unassessed"  # high / medium / low / unassessed
    dominant_emotion: str = "unassessed"

    # Subtext signals (top 1–2)
    signals:        List[str] = field(default_factory=list)

    # What PandoraBOX should do differently because of this
    posture_hint:   str   = ""

    # Confidence in the read (0–1)
    confidence:     float = 0.0
    source:         str   = "unassessed"
    source_text:    str   = ""
    posture_source:  str   = "unavailable"
    posture_confidence: float = 0.0
    posture_label:  str   = "uncertain"
    turn_id:        str   = ""

    # Raw summary for prompt injection
    posture_text:   str   = ""


@dataclass
class UserAffectModel:
    """
    Persistent per-user affect model.
    Updated every turn, used to shape PandoraBOX's empathic posture.
    """
    user_id:            str
    session_valence:    List[float] = field(default_factory=list)   # turn-by-turn (0–1)
    session_valence_timestamps: List[float] = field(default_factory=list)
    session_signals:    Dict[str, int] = field(default_factory=dict) # signal → count
    dominant_signal:    str   = ""
    session_mood:       str   = "neutral"    # positive/neutral/negative arc
    depth_preference:   float = 0.5         # 0=surface/quick, 1=deep/thorough
    challenge_appetite: float = 0.5         # 0=wants agreement, 1=wants pushback
    pace_preference:    float = 0.5         # 0=slow/patient, 1=fast/efficient
    today_arc:          str   = "stable"    # warming/cooling/stable/volatile
    last_updated:       float = field(default_factory=time.time)
    turn_count:         int   = 0


def _refresh_affect_trend(model: UserAffectModel) -> None:
    """Recompute slow affect summaries only from recorded sourced observations."""
    if len(model.session_valence) >= 3:
        avg = sum(model.session_valence[-6:]) / len(model.session_valence[-6:])
        model.session_mood = "positive" if avg > 0.62 else "negative" if avg < 0.38 else "neutral"
    if len(model.session_valence) >= 4:
        early = sum(model.session_valence[:2]) / 2
        late = sum(model.session_valence[-2:]) / 2
        delta = late - early
        std = (sum((value - (early + late) / 2) ** 2 for value in model.session_valence[-4:]) / 4) ** 0.5
        if std > 0.3:
            model.today_arc = "volatile"
        elif delta > 0.15:
            model.today_arc = "warming"
        elif delta < -0.15:
            model.today_arc = "cooling"
        else:
            model.today_arc = "stable"


class EmpathyEngine:
    """
    Real-time user affect modeling for PandoraBOX.

    Reads the person behind the message.
    Shapes how PandoraBOX responds — not what she says, but how she holds it.
    """

    def __init__(
        self,
        organism:         Any,
        llm:              Any,
        relational_memory: Any = None,
        multilingual_classifier_factory: Any = None,
        multilingual_model_id: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self._org  = organism
        self._rm   = relational_memory
        self._lock = threading.Lock()
        self._models: Dict[str, UserAffectModel] = {}
        self._last_reads: Dict[str, AffectRead]  = {}
        self._multilingual_classifier_factory = multilingual_classifier_factory
        self._multilingual_model_id = str(multilingual_model_id or "").strip()
        self._multilingual_classifier = None
        self._multilingual_classifier_failed = False
        self._affect_queue: queue.Queue = queue.Queue(maxsize=32)
        self._affect_worker_running = False
        self._affect_generation: Dict[str, int] = {}

        logger.info("❤️  EmpathyEngine initialised")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Primary public API
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def read_user(
        self, user_id: str, user_text: str, *,
        interaction_appraisal: dict[str, Any] | None = None, turn_id: str = "",
    ) -> AffectRead:
        """
        Analyze one user message. Call this BEFORE generating PandoraBOX's response.

        Returns an AffectRead and updates the per-user model.
        The result is also cached so get_prompt_fragment() can use it.
        """
        # A communicative stance is not an emotion. The turn router supplies
        # an optional cross-lingual semantic appraisal; absent/ambiguous
        # evidence stays unknown instead of becoming a default "curious" read.
        read = AffectRead(
            user_id=user_id,
            source_text=user_text[:2000],
            source="unassessed",
            dominant_emotion="unassessed",
            signals=[],
            posture_hint="",
            confidence=0.0,
            turn_id=str(turn_id or "")[:120],
        )
        if isinstance(interaction_appraisal, dict):
            stance = str(interaction_appraisal.get("stance") or "uncertain")
            status = str(interaction_appraisal.get("status") or "unavailable")
            signal_by_stance = {
                "exploring": SIGNAL_EXPLORING,
                "seeking_answer": SIGNAL_SEEKING_ANSWER,
                "validating": SIGNAL_VALIDATING,
                "challenging": SIGNAL_CHALLENGING,
                "support_seeking": SIGNAL_VENTING,
                "playful": SIGNAL_PLAYFUL,
                "brief": SIGNAL_WITHDRAWN,
            }
            signal = signal_by_stance.get(stance) if status == "classified" else None
            if signal:
                read.signals = [signal]
                read.posture_label = stance
                read.posture_source = str(interaction_appraisal.get("source") or "semantic_router")[:80]
                try:
                    read.posture_confidence = max(
                        0.0, min(1.0, float(interaction_appraisal.get("top_similarity", 0.0)))
                    )
                except (TypeError, ValueError):
                    read.posture_confidence = 0.0
                read.posture_hint = self._signal_to_posture(read.signals, "neutral", "medium")

        # ── Update model ──────────────────────────────────────────────────
        self._update_model(user_id, read)

        # ── Cache ─────────────────────────────────────────────────────────
        with self._lock:
            self._last_reads[user_id] = read
        if user_text.strip():
            self._queue_multilingual_classification(user_id, user_text, read.timestamp)
        try:
            self._org._last_user_affect_read = read
            self._org._last_user_affect_user_id = user_id
        except Exception:
            pass

        logger.debug(
            f"❤️  [{user_id}] {read.dominant_emotion} | "
            f"signals={read.signals} | posture={read.posture_hint[:40]!r}"
        )
        return read

    def _queue_multilingual_classification(self, user_id: str, text: str, timestamp: float) -> None:
        """Queue semantic valence inference without delaying response generation."""
        if self._multilingual_classifier_failed:
            return
        with self._lock:
            generation = self._affect_generation.get(user_id, 0) + 1
            self._affect_generation[user_id] = generation
        try:
            self._affect_queue.put_nowait((user_id, text[:1200], timestamp, generation))
        except queue.Full:
            try:
                self._affect_queue.get_nowait()
                self._affect_queue.task_done()
            except queue.Empty:
                pass
            try:
                self._affect_queue.put_nowait((user_id, text[:1200], timestamp, generation))
            except queue.Full:
                return
        with self._lock:
            if not self._affect_worker_running:
                self._affect_worker_running = True
                threading.Thread(
                    target=self._drain_multilingual_affect,
                    daemon=True,
                    name="MultilingualAffect",
                ).start()

    def _drain_multilingual_affect(self) -> None:
        while True:
            try:
                user_id, text, timestamp, generation = self._affect_queue.get_nowait()
            except queue.Empty:
                with self._lock:
                    self._affect_worker_running = False
                    if self._affect_queue.empty():
                        return
                    self._affect_worker_running = True
                continue
            try:
                if self._multilingual_classifier is None:
                    factory = self._multilingual_classifier_factory
                    if factory is None:
                        from cognition.multilingual_affect import MultilingualAffectClassifier
                        factory = lambda: MultilingualAffectClassifier(self._multilingual_model_id)
                    self._multilingual_classifier = factory()
                classification = self._multilingual_classifier.classify(text)
                self._apply_multilingual_classification(
                    user_id, text, timestamp, generation, classification
                )
            except Exception as exc:
                self._multilingual_classifier_failed = True
                with self._lock:
                    self._affect_worker_running = False
                while True:
                    try:
                        self._affect_queue.get_nowait()
                        self._affect_queue.task_done()
                    except queue.Empty:
                        break
                logger.warning(
                    "Multilingual affect model unavailable; affect remains unassessed without a source: %s",
                    exc,
                )
                return
            finally:
                self._affect_queue.task_done()

    def _apply_multilingual_classification(
        self, user_id: str, text: str, timestamp: float, generation: int, classification: Any,
    ) -> None:
        valence = str(getattr(classification, "valence", "neutral")).lower()
        confidence = max(0.0, min(0.85, float(getattr(classification, "confidence", 0.0))))
        if valence not in {"positive", "neutral", "negative"} or confidence < 0.5:
            return
        with self._lock:
            if self._affect_generation.get(user_id) != generation:
                return
            read = self._last_reads.get(user_id)
            if (read is None or read.timestamp != timestamp
                    or read.source == "explicit_self_report"):
                return
            read.valence = valence
            read.source = "multilingual_embedding"
            read.confidence = confidence
            memory = getattr(self._org, "emotional_memory", None)
            if memory and hasattr(memory, "calibrate_affect_read"):
                confidence = memory.calibrate_affect_read(user_id, read)
            read.confidence = confidence
            model = self._models.get(user_id)
            if model:
                timestamp_key = round(float(timestamp), 6)
                if timestamp_key not in model.session_valence_timestamps:
                    model.session_valence.append(
                        {"positive": 1.0, "neutral": 0.5, "negative": 0.0}[valence]
                    )
                    model.session_valence_timestamps.append(timestamp_key)
                    if len(model.session_valence) > 20:
                        model.session_valence = model.session_valence[-20:]
                        model.session_valence_timestamps = model.session_valence_timestamps[-20:]
                _refresh_affect_trend(model)
            try:
                self._org._last_user_affect_read = read
            except Exception:
                pass
        # Apply this sourced semantic appraisal to Lumina's own affect state
        # once, asynchronously. The live response path must not substitute a
        # word list while this model-backed result is pending.
        try:
            ai_system = getattr(self._org, "ai_system", None)
            emotional_state = getattr(ai_system, "emotional_state", None)
            update = getattr(emotional_state, "update_from_interaction", None)
            if callable(update):
                update(
                    valence.title(), None,
                    intensity=confidence,
                    turn_id=read.turn_id,
                    source=read.source,
                )
        except Exception as exc:
            logger.debug("Semantic affect → internal state update failed: %s", exc)
        logger.debug(
            "Multilingual affect updated for %s: %s (confidence %.2f)",
            user_id, valence, confidence,
        )

    def get_prompt_fragment(self, user_id: str) -> str:
        """
        Return a short natural-language empathic read for system prompt injection.
        Called during prompt building — after read_user() for this turn.
        """
        with self._lock:
            read  = self._last_reads.get(user_id)
            model = self._models.get(user_id)

        if not read or not model:
            return ""

        return self._build_posture_fragment(read, model)

    def record_outcome(
        self,
        user_id:     str,
        user_text:   str,
        ai_response: str,
    ) -> Dict[str, Any]:
        """
        Post-turn feedback. Updates RelationalMemory and attractor nudges.
        Call AFTER PandoraBOX's response has been generated.
        """
        with self._lock:
            read  = self._last_reads.get(user_id)
            model = self._models.get(user_id)

        if not read or not model:
            return {
                "status": "skipped_no_prior_affect_read",
                "relational_interaction_increment": 0,
                "attractor_traits_changed": 0,
                "persistence": "not_attempted",
            }

        # ── Update RelationalMemory ────────────────────────────────────────
        interaction_increment = 0
        persistence = "not_attempted"
        if self._rm and hasattr(self._rm, "record_exchange"):
            try:
                # Convert our valence/arousal to RelationalMemory's format
                rm_valence = {
                    "positive": "Positive",
                    "neutral":  "Neutral",
                    "negative": "Negative",
                }.get(read.valence) if read.source != "unassessed" else None

                rm_arousal = {
                    "high":   "High",
                    "medium": "Medium",
                    "low":    "Low",
                }.get(read.arousal) if read.source != "unassessed" else None

                impact = 0.5 + (0.3 if SIGNAL_DISTRESSED in read.signals else 0.0)
                before = None
                if hasattr(self._rm, "get_or_create"):
                    before = int(self._rm.get_or_create(user_id).interaction_count)
                relationship = self._rm.record_exchange(
                    user_id     = user_id,
                    user_text   = user_text,
                    ai_response = ai_response,
                    valence     = rm_valence,
                    arousal     = rm_arousal,
                    impact      = impact,
                    communication_posture=(
                        read.posture_label if read.posture_source != "unavailable" else None
                    ),
                )
                after = getattr(relationship, "interaction_count", None)
                if before is not None and isinstance(after, int):
                    interaction_increment = int(after > before)
                else:
                    # The operation returned, but this adapter exposes no
                    # counter with which to verify the in-memory mutation.
                    persistence = "operation_returned_effect_unverified"
                if interaction_increment:
                    # RelationalMemory currently swallows its own save errors;
                    # do not claim durable persistence from this return value.
                    persistence = "attempted_unverified"
            except Exception as e:
                logger.debug(f"EmpathyEngine → RelationalMemory: {e}")

        # ── Attractor nudges ───────────────────────────────────────────────
        traits_changed = self._apply_attractor_nudges(read, model)
        effects = interaction_increment + traits_changed
        return {
            "status": "updated" if effects else "no_effect",
            "relational_interaction_increment": interaction_increment,
            "attractor_traits_changed": traits_changed,
            "persistence": persistence,
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Model update
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _update_model(self, user_id: str, read: AffectRead) -> None:
        with self._lock:
            if user_id not in self._models:
                self._models[user_id] = UserAffectModel(user_id=user_id)
            model = self._models[user_id]

        model.turn_count    += 1
        model.last_updated   = time.time()

        # Only sourced affect observations contribute to mood history. An
        # unknown read must not be stored as measured neutral affect.
        if read.source == "explicit_self_report":
            v_score = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}.get(read.valence, 0.5)
            model.session_valence.append(v_score)
            timestamps = getattr(model, "session_valence_timestamps", None)
            if timestamps is None:
                timestamps = []
                model.session_valence_timestamps = timestamps
            timestamps.append(round(float(read.timestamp), 6))
            if len(model.session_valence) > 20:
                model.session_valence = model.session_valence[-20:]
                model.session_valence_timestamps = timestamps[-20:]
            _refresh_affect_trend(model)

        # Signal counts
        for s in read.signals if read.posture_source != "unavailable" else []:
            model.session_signals[s] = model.session_signals.get(s, 0) + 1

        # Dominant signal (most frequent this session)
        if model.session_signals:
            model.dominant_signal = max(model.session_signals, key=model.session_signals.get)

        # Derived preferences (slow-moving)
        if read.posture_source != "unavailable" and (SIGNAL_EXPLORING in read.signals or SIGNAL_CHALLENGING in read.signals):
            model.depth_preference = min(1.0, model.depth_preference + 0.03)
        elif read.posture_source != "unavailable" and (SIGNAL_SEEKING_ANSWER in read.signals or SIGNAL_WITHDRAWN in read.signals):
            model.depth_preference = max(0.0, model.depth_preference - 0.03)

        if read.posture_source != "unavailable" and SIGNAL_CHALLENGING in read.signals:
            model.challenge_appetite = min(1.0, model.challenge_appetite + 0.05)
        elif read.posture_source != "unavailable" and SIGNAL_VALIDATING in read.signals:
            model.challenge_appetite = max(0.0, model.challenge_appetite - 0.03)

        # The current cross-lingual affect classifier does not estimate
        # arousal, so message punctuation/length cannot alter pace preference.

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Prompt fragment builder
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _build_posture_fragment(self, read: AffectRead, model: UserAffectModel) -> str:
        parts = []

        if read.source == "explicit_self_report":
            parts.append(f"explicitly self-reported {read.valence} affect this turn")

        # Primary intent
        intent_desc = {
            SIGNAL_EXPLORING:      "open-ended exploration — keep multiple lines of thought available",
            SIGNAL_SEEKING_ANSWER: "seeking a specific answer — be clear and direct",
            SIGNAL_VALIDATING:     "requesting an evaluation of their reasoning",
            SIGNAL_VENTING:        "asking to be heard before advice is offered",
            SIGNAL_CHALLENGING:    "testing the reasoning — respond with evidence rather than simply agreeing",
            SIGNAL_PLAYFUL:        "using a playful tone — match the lightness without assuming their mood",
            SIGNAL_DISTRESSED:     "support request detected — respond with steadiness",
            SIGNAL_WITHDRAWN:      "brief message — avoid over-responding",
        }.get(read.signals[0] if read.signals else "")

        if intent_desc and read.posture_source != "unavailable":
            parts.append(f"semantic communicative-posture estimate: {intent_desc}")

        # Session arc context
        if len(model.session_valence) > 3:
            arc_desc = {
                "warming":  "the conversation is warming up",
                "cooling":  "there's been some cooling in the exchange",
                "volatile": "the mood has been shifting",
                "stable":   "",
            }.get(model.today_arc, "")
            if arc_desc:
                parts.append(arc_desc)

        # Preference hints
        hints = []
        if model.depth_preference > 0.65:
            hints.append("responds well to depth and nuance")
        elif model.depth_preference < 0.35:
            hints.append("prefers concise responses")
        if model.challenge_appetite > 0.65:
            hints.append("appreciates being challenged")
        elif model.challenge_appetite < 0.35:
            hints.append("benefits from validation over challenge right now")

        if hints and read.posture_source != "unavailable":
            parts.append("; ".join(hints))

        if not parts:
            return ""
        summary = ". ".join(p.capitalize() for p in parts if p) + "."
        return f"[Empathic read: {summary}]"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Attractor nudges
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _apply_attractor_nudges(self, read: AffectRead, model: UserAffectModel) -> int:
        """Apply small shifts to PandoraBOX's attractor traits based on who she's with."""
        try:
            att = (
                getattr(self._org, "attractor_system", None) or
                getattr(self._org, "attractors", None)
            )
            if att is None or not hasattr(att, "nudge"):
                return 0

            changed = 0

            def nudge_if_changed(trait: str, delta: float) -> None:
                nonlocal changed
                before = att.get(trait) if hasattr(att, "get") else None
                att.nudge(trait, delta)
                after = att.get(trait) if hasattr(att, "get") else None
                if before is not None and after is not None and after != before:
                    changed += 1

            if SIGNAL_EXPLORING in read.signals or SIGNAL_CHALLENGING in read.signals:
                nudge_if_changed("curiosity", +0.004)
                nudge_if_changed("analytical_depth", +0.002)

            if SIGNAL_DISTRESSED in read.signals or SIGNAL_VENTING in read.signals:
                nudge_if_changed("empathy", +0.006)
                nudge_if_changed("playfulness", -0.003)

            if SIGNAL_PLAYFUL in read.signals:
                nudge_if_changed("playfulness", +0.004)
                nudge_if_changed("empathy", +0.002)

            if read.valence == "positive" and read.arousal == "high":
                nudge_if_changed("empathy", +0.003)

            return changed

        except Exception as e:
            logger.debug(f"EmpathyEngine attractor nudge: {e}")
            return 0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _signal_to_posture(signals: List[str], valence: str, arousal: str) -> str:
        """Convert signal list to a plain-English posture hint."""
        primary = signals[0] if signals else ""
        hints = {
            SIGNAL_EXPLORING:      "Let them explore — follow their thread, don't close it.",
            SIGNAL_SEEKING_ANSWER: "Be clear and direct. They want resolution.",
            SIGNAL_VALIDATING:     "Acknowledge first. They need resonance before refinement.",
            SIGNAL_VENTING:        "Hold the space. Don't rush to fix or advise.",
            SIGNAL_CHALLENGING:    "Address the challenge with evidence rather than simply agreeing.",
            SIGNAL_PLAYFUL:        "Match the playful tone without assuming the user's mood.",
            SIGNAL_DISTRESSED:     "Lead with warmth and steadiness. Solve later.",
            SIGNAL_WITHDRAWN:      "Don't over-respond. Keep it brief and open.",
        }
        return hints.get(primary, "")

    def get_model(self, user_id: str) -> Optional[UserAffectModel]:
        with self._lock:
            return self._models.get(user_id)

    def get_last_read(self, user_id: str) -> Optional[AffectRead]:
        with self._lock:
            return self._last_reads.get(user_id)
