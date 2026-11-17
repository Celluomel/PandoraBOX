"""
cognition/autonomous_curiosity_resolver.py  (Patch 05)

Converts high-priority curiosity topics into GoalEngine goals so
GoalActionExecutor can pursue them via self_question actions.
"""
from __future__ import annotations
import logging, threading, time
from typing import Any, List, Optional, Set

logger = logging.getLogger(__name__)

RESOLVE_CHECK_EVERY_N   = 10
CURIOSITY_THRESHOLD     = 0.55
MAX_GOALS_FROM_CURIOSITY = 2
GOAL_PRIORITY_BASE      = 0.60

# Used only by the offline duplicate-overlap fallback. This is deliberately
# separate from goal admission: it must never decide whether a topic is a
# coherent or durable goal.
_RESOLVER_STOP = {
    "and", "the", "for", "with", "that", "this", "from", "into", "through",
    "about", "have", "more", "will", "been", "your", "our", "their", "its",
    "are", "was", "were", "has", "had", "not", "but", "can", "may", "how",
    "all", "any", "each", "both", "such", "than", "then", "when", "what",
    "something", "anything", "nothing", "true", "know", "think", "believe",
    "assume", "assuming", "belief", "beliefs", "curiosity", "question",
    "questions", "answer", "answers", "thinking", "thoughts",
    "avec", "dans", "pour", "sans", "sur", "sous", "entre", "depuis",
    "cela", "ceci", "cette", "comme", "mais", "donc", "alors", "quand",
    "quoi", "quel", "quelle", "quels", "quelles", "comment", "pourquoi",
    "être", "avoir", "faire", "dire", "voir", "savoir", "penser", "croire",
}


class AutonomousCuriosityResolver:
    def __init__(self, organism: Any) -> None:
        self._organism = organism
        self._lock     = threading.Lock()
        self._worker_lock = threading.Lock()
        self._worker_pending = False
        self._promoted: Set[str] = set()
        self._last_result: dict[str, Any] = {
            "status": "not_run", "cycle": 0,
        }
        logger.info("[CuriosityResolver] Initialised")

    def tick(self, slow_cycle: int) -> dict[str, Any]:
        if slow_cycle % RESOLVE_CHECK_EVERY_N != 0 or slow_cycle == 0:
            return self._tick_receipt(slow_cycle, "skipped", "curiosity_cadence_not_due")
        with self._worker_lock:
            if self._worker_pending:
                return self._tick_receipt(slow_cycle, "skipped", "promotion_already_running")
            self._worker_pending = True
        try:
            threading.Thread(
                target=self._check_and_promote_scheduled, args=(slow_cycle,),
                daemon=True, name="acr-promote",
            ).start()
        except Exception:
            with self._worker_lock:
                self._worker_pending = False
            return self._tick_receipt(slow_cycle, "failed", "worker_start_failed")
        return self._tick_receipt(slow_cycle, "scheduled", "promotion_worker_started")

    @staticmethod
    def _tick_receipt(cycle: int, status: str, reason: str) -> dict[str, Any]:
        return {
            "cycle": int(cycle), "outcome_status": status,
            "reason_code": reason, "worker_scheduled": status == "scheduled",
        }

    def _check_and_promote_scheduled(self, slow_cycle: int) -> None:
        started = time.perf_counter()
        try:
            result = self._check_and_promote(slow_cycle)
            if not isinstance(result, dict):
                result = {"status": "failed", "reason_code": "invalid_worker_result"}
        except Exception as error:
            logger.exception("[CuriosityResolver] promotion worker failed")
            result = {
                "status": "failed",
                "reason_code": "promotion_worker_exception",
                "error_type": type(error).__name__,
            }
        finally:
            with self._worker_lock:
                self._last_result = dict(result)
                self._last_result["cycle"] = int(slow_cycle)
                self._last_result["duration_ms"] = round(
                    (time.perf_counter() - started) * 1000, 2
                )
                self._worker_pending = False
            self._record_async_result(slow_cycle, self._last_result)

    def get_last_result(self) -> dict[str, Any]:
        """Return the content-free result of the most recent promotion scan."""
        lock = getattr(self, "_worker_lock", None)
        if lock is None:
            return dict(getattr(self, "_last_result", {"status": "not_run"}))
        with lock:
            return dict(getattr(self, "_last_result", {"status": "not_run"}))

    def _record_async_result(self, slow_cycle: int, result: dict[str, Any]) -> None:
        organism = getattr(self, "_organism", None)
        loop = getattr(organism, "_loop", None)
        recorder = getattr(loop, "record_async_cycle_stage", None)
        if not callable(recorder):
            return
        metrics = {
            key: result[key]
            for key in (
                "candidate_count", "duplicate_count", "admission_rejected_count",
                "promoted_count", "duration_ms",
            )
            if isinstance(result.get(key), (int, float))
        }
        try:
            recorder(
                slow_cycle,
                "autonomous_curiosity_resolver.promotion",
                str(result.get("status", "failed")),
                output={
                    key: result[key]
                    for key in ("status", "reason_code", "cycle", "candidate_count",
                                "duplicate_count", "admission_rejected_count", "promoted_count")
                    if key in result
                },
                metrics=metrics,
                error_type=result.get("error_type"),
            )
        except Exception as error:
            logger.debug("[CuriosityResolver] async receipt failed: %s", type(error).__name__)

    def _check_and_promote(self, slow_cycle: int) -> dict[str, Any]:
        o = self._organism
        gate = getattr(o, "behavior_gate", None)
        if gate and not gate.may_run_resolution():
            return {"status": "skipped", "reason_code": "behavior_gate_blocked"}
        ce = getattr(o, "curiosity", None)
        if not ce:
            return {"status": "skipped", "reason_code": "curiosity_unavailable"}

        topics: List[tuple] = []
        try:
            with ce._lock:
                for topic, node in ce._topics.items():
                    if node.curiosity >= CURIOSITY_THRESHOLD:
                        topics.append((topic, node.curiosity))
            topics.sort(key=lambda item: -item[1])
            topics = topics[:MAX_GOALS_FROM_CURIOSITY * 2]
        except Exception as error:
            logger.warning("[CuriosityResolver] topic read failed: %s", type(error).__name__)
            return {"status": "failed", "reason_code": "curiosity_read_failed",
                    "error_type": type(error).__name__}

        if not topics:
            return {"status": "completed", "reason_code": "no_candidates",
                    "candidate_count": 0, "duplicate_count": 0,
                    "admission_rejected_count": 0, "promoted_count": 0}

        ai = getattr(o, "ai_system", None)
        ge = getattr(ai, "goal_engine", None) if ai else None
        if not ge:
            return {"status": "skipped", "reason_code": "goal_engine_unavailable",
                    "candidate_count": len(topics)}

        existing: Set[str] = set()
        try:
            for goal in ge._goals.values():
                existing.add(goal.topic.lower().strip())
        except Exception:
            pass

        promoted = 0
        duplicate_count = 0
        admission_rejected_count = 0
        for topic, curiosity_val in topics:
            if promoted >= MAX_GOALS_FROM_CURIOSITY:
                break
            if topic in getattr(self, "_promoted", set()):
                continue
            # GoalEngine.add_goal is the single durable-goal admission contract:
            # it applies the semantic quality gate and all persistence checks.
            # A second English word-count/stopword gate here was rejecting valid
            # concise and French subjects before that shared decision.
            if self._is_duplicate(topic, existing):
                duplicate_count += 1
                continue
            if not self._create_goal(ge, topic, curiosity_val, slow_cycle):
                admission_rejected_count += 1
                continue
            with self._lock:
                if not hasattr(self, "_promoted"):
                    self._promoted = set()
                self._promoted.add(topic)
            existing.add(topic.lower().strip())
            promoted += 1

        if promoted:
            logger.info("[CuriosityResolver] Promoted %d topic(s) to goals (cycle=%d)",
                        promoted, slow_cycle)
        return {
            "status": "completed",
            "reason_code": "promotion_pass_complete",
            "candidate_count": len(topics),
            "duplicate_count": duplicate_count,
            "admission_rejected_count": admission_rejected_count,
            "promoted_count": promoted,
        }

    # Calibrated dedup threshold (QUALITY tier / nomic): near-duplicate goal
    # topics score >= 0.643, distinct topics <= 0.550 (measured gap ~0.09).
    # 0.60 sits comfortably inside that gap.
    DEDUP_COSINE_THRESHOLD = 0.60

    def _is_duplicate(self, candidate: str, existing_topics) -> bool:
        """True if candidate is a duplicate/near-duplicate of an existing goal.

        Primary signal: semantic similarity via the QUALITY-tier embedder
        (nomic-embed-text) - robust to rewording and truncation. If the
        embedder/API is unavailable, falls back to the legacy word-overlap
        heuristic so dedup still works offline.
        """
        cand = (candidate or "").lower().strip()
        topics = [str(t) for t in (existing_topics or []) if t and str(t).strip()]
        if not cand or not topics:
            return False
        # Fast exact-match
        if cand in {t.lower().strip() for t in topics}:
            return True
        # Semantic similarity (QUALITY tier, single batched call)
        try:
            import numpy as np
            from utils.shared_embedder import get_embedder
            emb = get_embedder(quality=True)
            vecs = np.asarray(
                emb.encode([candidate] + topics), dtype="float32")
            cand_vec = vecs[0]
            others = vecs[1:]
            cn = float(np.linalg.norm(cand_vec)) + 1e-9
            on = np.linalg.norm(others, axis=1) + 1e-9
            sims = (others @ cand_vec) / (on * cn)
            if len(sims) and float(np.max(sims)) >= self.DEDUP_COSINE_THRESHOLD:
                return True
            return False
        except Exception as e:
            logger.debug(
                "[CuriosityResolver] semantic dedup unavailable (%s); "
                "using word-overlap" % e)
            return self._is_duplicate_word_overlap(cand, topics)

    def _is_duplicate_word_overlap(self, cand: str, topics) -> bool:
        """Legacy word-overlap dedup (offline fallback)."""
        def content_words(s: str):
            return {w for w in s.split()
                    if len(w) > 3 and w.isalpha()
                    and w not in _RESOLVER_STOP}
        cw = content_words(cand)
        if not cw:
            return True  # no content words -> nothing specific -> skip
        for ex in topics:
            ew = content_words(ex)
            if (cand in ex or ex in cand) and min(len(cand), len(ex)) > 12:
                return True
            if len(cw & ew) >= 2:
                return True
            if len(cw) == 1 and next(iter(cw)) in ew:
                return True
        return False

    def _create_goal(self, goal_engine: Any, topic: str,
                     curiosity: float, slow_cycle: int) -> bool:
        try:
            from cognition.goal_engine import Goal
            import uuid
            priority = round(min(0.80, GOAL_PRIORITY_BASE + (curiosity - CURIOSITY_THRESHOLD) * 0.3), 3)
            goal = Goal(
                id            = f"curiosity_{uuid.uuid4().hex[:8]}",
                topic         = topic,
                priority      = priority,
                persistence   = 0,
                origin        = f"curiosity_autonomous_c{slow_cycle}",
                energy        = 0.8,
                created_cycle = slow_cycle,
                last_active   = slow_cycle,
            )
            if not goal_engine.add_goal(goal):
                return False
            logger.info("[CuriosityResolver] Goal committed: %r p=%.2f", topic, priority)
            return True
        except Exception as e:
            logger.debug(f"[CuriosityResolver] _create_goal error '{topic}': {e}")
            return False
