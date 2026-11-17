"""
PANDORABOX V32 — Phase 4.3 : Thread Lifecycle Manager
==================================================
Handles threads that have exceeded their iteration budget.
Instead of just marking them 'deferred', extracts the key learning
as a belief and properly retires the thread.

Also ensures bidirectional thought↔goal linking.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.data.access import DataAccess
from core.data.schemas import make_belief

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ThreadLifecycleManager:
    """
    Manages the full lifecycle of cognitive threads:
      - Detects threads stuck at max iterations
      - Extracts insight/belief from thread context
      - Links extracted belief to identity.json
      - Retires stuck threads gracefully
      - Repairs bidirectional thought↔goal links
    """

    MAX_ITER_THRESHOLD = 15    # threads at or above this are "stuck"

    def __init__(self, persona_dir: str = "data/persona"):
        self.persona_dir = Path(persona_dir)
        self.dal = DataAccess(str(persona_dir))

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, active_goal_ids: Optional[set[str]] = None) -> Dict[str, Any]:
        """Run lifecycle pass without retiring threads for goals still active.

        Iteration count alone is not completion evidence. A linked active goal
        remains eligible for TTE/DTS even after its thread crosses the legacy
        stuck-thread threshold; once the GoalEngine closes that goal, normal
        retirement policy applies again.
        """
        active_goal_ids = {
            str(goal_id).strip() for goal_id in (active_goal_ids or set())
            if str(goal_id).strip()
        }
        report = {
            'threads_processed': 0,
            'beliefs_extracted': [],
            'threads_retired':   [],
            'unverified_threads_retired': [],
            'active_goal_threads_preserved': [],
            'links_repaired':    0,
            'belief_persistence_failed': [],
            'thread_persistence_failed': [],
        }

        # 1. Handle stuck threads
        threads = self.dal.get_threads()
        retirement_candidates = []
        belief_candidates = []
        unverified_candidate_ids = set()
        for thread in threads:
            iters  = thread.get('iteration_count', 0)
            status = thread.get('status', 'active')

            source_ref = str(thread.get('source_ref') or '').strip()
            if source_ref and source_ref in active_goal_ids:
                report['active_goal_threads_preserved'].append(thread['id'][:8])
                continue

            if iters >= self.MAX_ITER_THRESHOLD and status not in ('resolved', 'retired'):
                belief = self._extract_belief(thread)
                if belief:
                    belief_candidates.append(belief)
                    thread['_lifecycle_belief_name'] = belief['name']
                    # Link thread to the belief
                    thread['identity_link']  = belief['name']
                    thread['learning_at']    = _now()
                else:
                    unverified_candidate_ids.add(thread['id'][:8])

                thread['status']      = 'retired'
                thread['retired_at']  = _now()
                thread['retire_reason'] = f"Exceeded {self.MAX_ITER_THRESHOLD} iterations"
                retirement_candidates.append(thread)

        # The old loop rewrote the full multi-megabyte thread JSON file once
        # per retired thread. Persist this maintenance batch once instead.
        beliefs_saved = True
        if belief_candidates:
            batch_saver = getattr(self.dal, 'save_beliefs', None)
            if callable(batch_saver):
                beliefs_saved = bool(batch_saver(belief_candidates))
            else:
                beliefs_saved = all(
                    self.dal.save_belief(belief) for belief in belief_candidates
                )
            if beliefs_saved:
                report['beliefs_extracted'] = [
                    belief['name'] for belief in belief_candidates
                ]
            else:
                failed_belief_names = {belief['name'] for belief in belief_candidates}
                report['belief_persistence_failed'] = sorted(failed_belief_names)

        if not beliefs_saved:
            retirement_candidates = [
                thread for thread in retirement_candidates
                if thread.get('_lifecycle_belief_name') not in failed_belief_names
            ]
        for thread in retirement_candidates:
            thread.pop('_lifecycle_belief_name', None)

        if retirement_candidates:
            batch_saver = getattr(self.dal, 'save_threads', None)
            if callable(batch_saver):
                threads_saved = bool(batch_saver(retirement_candidates))
            else:
                threads_saved = all(
                    self.dal.save_thread(thread) for thread in retirement_candidates
                )
            if threads_saved:
                report['threads_retired'] = [
                    thread['id'][:8] for thread in retirement_candidates
                ]
                report['threads_processed'] = len(retirement_candidates)
                report['unverified_threads_retired'] = [
                    thread['id'][:8] for thread in retirement_candidates
                    if thread['id'][:8] in unverified_candidate_ids
                ]
            else:
                report['thread_persistence_failed'] = [
                    thread['id'][:8] for thread in retirement_candidates
                ]

        # 2. Repair thought→goal links
        report['links_repaired'] = self._repair_thought_goal_links()

        return report

    # ── Belief extraction ─────────────────────────────────────────────────────

    def _extract_belief(self, thread: Dict) -> Optional[Dict]:
        """
        Persist only an explicit outcome statement with a verified
        evidence reference; age, iterations and the topic are not evidence.
        """
        topic   = thread.get('topic', '').strip()
        state = thread.get('current_state', {})
        tid     = thread.get('id', '')
        outcome = state.get('verified_outcome') if isinstance(state, dict) else None
        if not topic or not isinstance(outcome, dict):
            return None
        if outcome.get('status') not in {'success', 'failure'}:
            return None
        evidence_ref = str(outcome.get('evidence_ref') or '').strip()
        statement = str(outcome.get('belief_statement') or '').strip()
        confidence = outcome.get('confidence')
        if (not evidence_ref or not statement
                or not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not 0.0 <= float(confidence) <= 1.0):
            return None

        belief_name = f"thread_learning_{tid[:8]}"
        bel = make_belief(
            name=belief_name,
            value=1.0 if outcome['status'] == 'success' else 0.0,
            confidence=round(float(confidence), 3),
            source_thread=tid,
        )
        bel['category']      = 'thread_learning'
        bel['thread_id']     = tid
        bel['topic']         = topic
        bel['statement']     = statement
        bel['description']   = f"Verified {outcome['status']} outcome for thread on '{topic}'"
        bel['evidence_ref']  = evidence_ref[:200]
        bel['outcome_status'] = outcome['status']
        bel['iterations']    = int(thread.get('iteration_count', 0) or 0)

        return bel

    # ── Thought↔Goal link repair ──────────────────────────────────────────────

    def _repair_thought_goal_links(self) -> int:
        """
        For each goal that has origin_thoughts, ensure the corresponding
        thought has linked_goal set back.
        Returns number of links repaired.
        """
        goals   = self.dal.get_goals()
        thoughts = self.dal.get_thoughts(limit=200, skip_expired=False)
        thought_idx = {t.get('id'): t for t in thoughts if t.get('id')}

        repaired = 0
        for goal in goals:
            gid = goal.get('id')
            if not gid:
                continue
            for origin in goal.get('origin_thoughts', []):
                tid = origin if isinstance(origin, str) else origin.get('thought_id', '')
                if not tid:
                    continue
                thought = thought_idx.get(tid)
                if thought and not thought.get('linked_goal'):
                    thought['linked_goal'] = gid
                    self.dal.add_thought(thought)
                    repaired += 1

        return repaired


if __name__ == '__main__':
    mgr = ThreadLifecycleManager()
    report = mgr.run()
    print('\n=== THREAD LIFECYCLE REPORT ===')
    print(f"  Threads processed : {report['threads_processed']}")
    print(f"  Beliefs extracted : {report['beliefs_extracted']}")
    print(f"  Threads retired   : {report['threads_retired']}")
    print(f"  Links repaired    : {report['links_repaired']}")
