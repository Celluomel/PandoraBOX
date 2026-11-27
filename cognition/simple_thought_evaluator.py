"""
Quick Win #4: Thought Evaluator
Transforms thoughts from word-focused logs into concept-focused decision inputs.
This is the BRIDGE between thinking and acting.
"""
import json
import math
from pathlib import Path
from datetime import datetime
import hashlib
from typing import List, Dict, Any


# These are producer-owned ThoughtStream schema IDs, not words searched in
# thought text. Free prose must never decide whether the internal loop admits
# a goal proposal. Unknown/legacy IDs remain non-actionable until a producer
# supplies a typed signal.
_THOUGHT_TYPES_BY_SIGNAL = {
    "uncertainty": frozenset({"curiosity", "open_question", "uncertainty"}),
    "tension": frozenset({
        "tension_awareness", "associative_tension",
        "associative_contradiction", "contradiction",
    }),
    "opportunity": frozenset({
        "goal_evaluation", "associative_goal", "opportunity",
        "action_affordance",
    }),
}
_NON_REEVALUATABLE_SOURCE_IDS = frozenset({
    "goal_action.self_question", "goal_action.memory_recall",
    "goal_action.web_search", "insight", "reflection",
    "thought_evaluator.followup", "thought_evaluator.stagnation_guard",
})

class SimpleThoughtEvaluator:
    
    def __init__(self, persona_dir, thought_stream=None):
        self.persona_dir = Path(persona_dir)
        self.thought_stream = thought_stream
        
    @staticmethod
    def _timestamp_seconds(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError, OverflowError):
            try:
                return datetime.fromisoformat(
                    str(value).replace('Z', '+00:00')
                ).timestamp()
            except Exception:
                return 0.0
    
    def evaluate_recent_thoughts(self) -> List[Dict]:
        try:
            from core.data.access import DataAccess
            _dal = DataAccess(str(self.persona_dir))
            thoughts = _dal.get_thoughts(skip_expired=True)
            stream_recent = getattr(self.thought_stream, "recent_dicts", None)
            if callable(stream_recent):
                merged_by_id = {
                    str(item.get("id") or ""): item
                    for item in thoughts if isinstance(item, dict) and item.get("id")
                }
                for item in stream_recent(50):
                    if isinstance(item, dict) and item.get("id"):
                        merged_by_id[str(item["id"])] = item

                thoughts = sorted(
                    merged_by_id.values(),
                    key=lambda item: self._timestamp_seconds(item.get("timestamp")),
                    reverse=True,
                )[:50]
            goals_list = _dal.get_goals()
            goals_data = {'goals': {g['id']: g for g in goals_list}}
            _use_dal = True
        except Exception:
            thoughts_file = self.persona_dir / 'thought_stream.json'
            goals_file = self.persona_dir / 'goals.json'
            if not thoughts_file.exists():
                print("⚠️  thought_stream.json not found")
                return []
            with open(thoughts_file, 'r', encoding='utf-8') as f:
                thoughts_data = json.load(f)
            goals_data = {}
            if goals_file.exists():
                with open(goals_file, 'r', encoding='utf-8') as f:
                    goals_data = json.load(f)
            thoughts = thoughts_data.get('thoughts', [])
            _use_dal = False

        suggestions_by_concept = {}
        evaluated_count = 0
        evaluated_thoughts = []
        
        print(f"\n🧠 Evaluating {len(thoughts)} thoughts...")
        
        import time as _time
        _now = _time.time()
        REEVAL_INTERVAL = 1800

        for thought in thoughts:
            if thought.get('evaluated', False):
                stored_evaluation = thought.get("evaluation", {})
                stored_proposal = (
                    stored_evaluation.get("goal_proposal")
                    if isinstance(stored_evaluation, dict) else None
                )
                # Evaluation and arbitration are separate lifecycle stages. A
                # proposal that lost workspace competition remains durable and
                # is re-emitted without re-running the evaluator/LLM.
                if (
                    isinstance(stored_proposal, dict)
                    and stored_proposal.get("status", "pending") == "pending"
                ):
                    self._merge_proposal(suggestions_by_concept, stored_proposal)
                    continue
                evaluated_at = thought.get('evaluated_at', '')
                try:
                    from datetime import timezone
                    ev_ts = datetime.fromisoformat(
                        evaluated_at.replace('Z', '+00:00')
                    ).timestamp() if evaluated_at else 0
                    age = _now - ev_ts
                    if age < REEVAL_INTERVAL:
                        continue
                    thought['evaluated'] = False
                except Exception:
                    continue
            
            try:
                evaluation = self._evaluate_thought(thought)
            except Exception as _eval_err:
                import logging as _lg
                _lg.getLogger(__name__).warning(
                    f"[ThoughtEvaluator] _evaluate_thought error: {_eval_err}"
                )
                continue
            
            if evaluation:
                stored_proposal = None
                if (
                    evaluation.get("should_create_goal")
                    and evaluation.get("concept_source") != "structured_topic"
                ):
                    # Re-check at the proposal writer, not only in the
                    # evaluator. Stored/legacy evaluation payloads can predate
                    # the structured-topic contract.
                    evaluation["should_create_goal"] = False
                    evaluation["goal_proposal_deferred_reason"] = (
                        "missing_structured_topic"
                    )
                if evaluation['should_create_goal']:
                    if not self._has_existing_goal(goals_data, evaluation['concept']):
                        _concept_key = " ".join(
                            str(evaluation['concept']).replace("_", " ").casefold().split()
                        )
                        suggestion = {
                            'type': evaluation['goal_type'],
                            'concept': evaluation['concept'],
                            'priority': evaluation['priority'],
                            'origin_thought': thought.get('id', self._generate_id(thought)),
                            'origin_thought_source': str(thought.get('source') or '')[:100],
                            'origin_thought_type': str(thought.get('thought_type') or thought.get('type') or '')[:80],
                            'origin_thought_timestamp': str(thought.get('timestamp') or '')[:80],
                            'concept_source': evaluation.get('concept_source', 'missing_structured_topic'),
                            'origin_content': str(thought.get('content') or thought.get('text') or "")[:1200],
                            'created_at': datetime.now().isoformat(),
                            'conceptual_friction': evaluation.get('friction', ''),
                            'actionability': evaluation.get('actionability', 0.5),
                            'hypothesis': '',
                            'hypothesis_pending': bool(evaluation.get('hypothesis_pending')),
                            'supporting_thought_ids': [
                                str(thought.get('id') or self._generate_id(thought))
                            ],
                            'name': (
                                f"test_hypothesis_{evaluation['concept'][:30]}"
                                if evaluation.get('hypothesis_pending') else evaluation['concept']
                            ),
                        }
                        suggestion["proposal_id"] = self._proposal_id(
                            suggestion.get("origin_thought"), suggestion.get("concept")
                        )
                        suggestion["status"] = "pending"
                        stored_proposal = dict(suggestion)
                        self._merge_proposal(suggestions_by_concept, suggestion)
                
                thought['evaluated'] = True
                thought['evaluated_at'] = datetime.now().isoformat()
                thought['evaluation'] = {
                    'type': evaluation['type'],
                    'concept': evaluation['concept'],
                    'priority': evaluation['priority'],
                    'actionability': evaluation.get('actionability', 0.5),
                    'conceptual_friction': evaluation.get('friction', ''),
                    'goal_proposal_deferred_reason': evaluation.get(
                        'goal_proposal_deferred_reason', ''
                    ),
                    **({"goal_proposal": stored_proposal} if stored_proposal else {}),
                }
                evaluated_thoughts.append(thought)

                concept = evaluation['concept']
                if concept and concept != 'unknown' and _use_dal:
                    self._inject_followup_thoughts(_dal, concept, evaluation['type'])

                evaluated_count += 1
            else:
                # A negative classification is still a completed evaluation.
                # Leaving mundane or evaluator-generated thoughts pending made
                # every later pass reconsider the same input indefinitely.
                thought['evaluated'] = True
                thought['evaluated_at'] = datetime.now().isoformat()
                content = str(thought.get('content') or thought.get('text') or '').strip()
                thought['evaluation'] = {
                    'type': 'mundane',
                    'should_create_goal': False,
                    'reason_code': 'empty_content' if not content else 'no_goal_signal',
                }
                evaluated_thoughts.append(thought)
                evaluated_count += 1

        if _use_dal:
            updater = getattr(_dal, "update_thought", None)
            for thought in evaluated_thoughts:
                if self.thought_stream is not None:
                    mark_evaluated = getattr(self.thought_stream, "mark_evaluated", None)
                    if callable(mark_evaluated):
                        mark_evaluated(
                            str(thought.get("id") or ""),
                            thought.get("evaluation", {}),
                            str(thought.get("evaluated_at") or ""),
                        )
                if callable(updater):
                    updater(thought)
                else:
                    # Compatibility for older DataAccess adapters; the real
                    # DAL implements update_thought to avoid duplicate rows.
                    _dal.add_thought(thought)
            if self.thought_stream is not None:
                flush = getattr(self.thought_stream, "flush", None)
                if callable(flush):
                    flush()
        else:
            import os
            if isinstance(thoughts_data, dict):
                thoughts_data["thoughts"] = thoughts
            tmp = thoughts_file.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(thoughts_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, thoughts_file)
        
        has_recent_stagnation_seed = any(
            isinstance(thought, dict)
            and thought.get("source") == "thought_evaluator.stagnation_guard"
            and 0 <= _now - self._timestamp_seconds(thought.get("timestamp")) < 7200
            for thought in thoughts
        )
        if evaluated_count == 0 and _use_dal and not has_recent_stagnation_seed:
            import time as _t, random as _rand
            seeds = [
                "What is currently most important for me to understand?",
                "What recent interaction has stayed with me and why?",
                "What feels unresolved in my current state of mind?",
                "What assumption am I making that I should question?",
            ]
            try:
                _dal.add_thought({
                    'content': _rand.choice(seeds),
                    'source': 'thought_evaluator.stagnation_guard',
                    'priority': 0.50,
                    'thought_type': 'reflection',
                    'timestamp': _t.time(),
                    'evaluated': False,
                })
            except Exception:
                pass

        print(f"   ✅ Evaluated {evaluated_count} new thoughts")
        suggestions = sorted(
            suggestions_by_concept.values(),
            key=lambda item: (item['priority'], item['actionability']),
            reverse=True,
        )
        print(f"   🎯 Generated {len(suggestions)} distinct goal proposals")
        
        return suggestions

    @staticmethod
    def _proposal_id(origin_thought: Any, concept: Any) -> str:
        """Stable, content-minimal identifier for a source thought's proposal."""
        payload = f"{str(origin_thought or '')}\0{' '.join(str(concept or '').casefold().split())}"
        return "gpr_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]

    @staticmethod
    def _merge_proposal(suggestions_by_concept: Dict[str, Dict], proposal: Dict) -> None:
        concept = " ".join(
            str(proposal.get("concept") or "").replace("_", " ").casefold().split()
        )
        if not concept:
            return
        previous = suggestions_by_concept.get(concept)
        if previous is None:
            suggestions_by_concept[concept] = dict(proposal)
            return
        previous["priority"] = max(float(previous.get("priority", 0)), float(proposal.get("priority", 0)))
        previous["actionability"] = max(
            float(previous.get("actionability", 0)), float(proposal.get("actionability", 0))
        )
        previous["hypothesis_pending"] = bool(
            previous.get("hypothesis_pending") or proposal.get("hypothesis_pending")
        )
        ids = list(previous.get("supporting_thought_ids") or [])
        ids.extend(proposal.get("supporting_thought_ids") or [])
        previous["supporting_thought_ids"] = list(dict.fromkeys(str(item) for item in ids if item))

    def record_proposal_disposition(
        self, proposal: Dict, status: str, *, cycle: int | None = None, reason: str = "",
    ) -> int:
        """Persist a terminal disposition on each source thought that proposed it."""
        allowed = {"committed", "satisfied", "rejected"}
        if not isinstance(proposal, dict) or status not in allowed:
            return 0
        ids = proposal.get("supporting_thought_ids") or [proposal.get("origin_thought")]
        ids = {str(item) for item in ids if item}
        if not ids:
            return 0
        if self.thought_stream is not None:
            flush = getattr(self.thought_stream, "flush", None)
            if callable(flush):
                flush()
        try:
            from core.data.access import DataAccess
            dal = DataAccess(str(self.persona_dir))
            thoughts = dal.get_thoughts(skip_expired=False)
        except Exception:
            return 0
        now = datetime.now().isoformat()
        updated = 0
        for thought in thoughts:
            if not isinstance(thought, dict) or str(thought.get("id") or "") not in ids:
                continue
            evaluation = thought.get("evaluation")
            if not isinstance(evaluation, dict):
                evaluation = {}
            pending = evaluation.get("goal_proposal")
            if not isinstance(pending, dict) or pending.get("status", "pending") != "pending":
                continue
            pending = dict(pending)
            pending.update({
                "status": status,
                "resolved_at": now,
                "resolved_cycle": int(cycle) if cycle is not None else None,
                "reason_code": str(reason or status)[:80],
            })
            evaluation = dict(evaluation)
            evaluation["goal_proposal"] = pending
            thought["evaluation"] = evaluation
            if dal.update_thought(thought):
                updated += 1
            if self.thought_stream is not None:
                mark_evaluated = getattr(self.thought_stream, "mark_evaluated", None)
                if callable(mark_evaluated):
                    mark_evaluated(
                        str(thought.get("id") or ""), evaluation,
                        str(thought.get("evaluated_at") or now),
                    )
        if updated and self.thought_stream is not None:
            flush = getattr(self.thought_stream, "flush", None)
            if callable(flush):
                flush()
        # Return the number of source thoughts whose terminal state is
        # durable, not merely the number newly written in this attempt. This
        # makes a retry after a partial write idempotent: already committed
        # sources still count toward the complete receipt.
        try:
            persisted = dal.get_thoughts(skip_expired=False)
        except Exception:
            return 0
        durable_ids = {
            str(thought.get("id") or "")
            for thought in persisted
            if isinstance(thought, dict)
            and str(thought.get("id") or "") in ids
            and isinstance(thought.get("evaluation"), dict)
            and isinstance(thought["evaluation"].get("goal_proposal"), dict)
            and thought["evaluation"]["goal_proposal"].get("status") == status
        }
        return len(durable_ids)

    def record_proposal_rejection(self, origin_thought_id: str, reason: str) -> bool:
        """Close a proposal rejected by the pre-arbitration quality gate."""
        origin_thought_id = str(origin_thought_id or "")
        if not origin_thought_id:
            return False
        if self.thought_stream is not None:
            flush = getattr(self.thought_stream, "flush", None)
            if callable(flush):
                flush()
        try:
            from core.data.access import DataAccess
            dal = DataAccess(str(self.persona_dir))
            thoughts = dal.get_thoughts(skip_expired=False)
        except Exception:
            return False
        for thought in thoughts:
            if not isinstance(thought, dict) or str(thought.get("id") or "") != origin_thought_id:
                continue
            evaluation = thought.get("evaluation")
            if not isinstance(evaluation, dict):
                return False
            proposal = evaluation.get("goal_proposal")
            if not isinstance(proposal, dict) or proposal.get("status", "pending") != "pending":
                return False
            proposal = dict(proposal)
            proposal.update({
                "status": "rejected",
                "resolved_at": datetime.now().isoformat(),
                "reason_code": str(reason or "quality_gate_rejected")[:80],
            })
            evaluation = dict(evaluation)
            evaluation["goal_proposal"] = proposal
            thought["evaluation"] = evaluation
            persisted = bool(dal.update_thought(thought))
            if persisted and self.thought_stream is not None:
                mark = getattr(self.thought_stream, "mark_evaluated", None)
                if callable(mark):
                    mark(origin_thought_id, evaluation, str(thought.get("evaluated_at") or ""))
                flush = getattr(self.thought_stream, "flush", None)
                if callable(flush):
                    flush()
            return persisted
        return False
    
    def _evaluate_thought(self, thought: Dict) -> Dict[str, Any]:
        text = str(thought.get('content') or thought.get('text') or '')
        
        if not text:
            return None
        
        # ✅ FIX: pass thought here
        thought_type = self._classify_thought(text, thought)
        
        if thought_type == 'mundane':
            return None
        
        # ThoughtStream carries a clean structured topic when its producer
        # knows the subject. Free-text extraction is not a reliable substitute
        # for a structured concept and is language-biased.
        structured_topic = thought.get("topic") or thought.get("concept")
        concept = " ".join(str(structured_topic).replace("_", " ").split()) if structured_topic else ""
        concept_source = "structured_topic" if concept else "missing_structured_topic"
        priority = self._compute_priority(thought, thought_type)
        actionability = self._compute_actionability(text, thought_type)
        friction = self._identify_friction(text, thought_type)
        goal_type = self._determine_goal_type(thought_type)
        
        has_goal_signal = (
            thought_type in ['uncertainty', 'tension', 'opportunity'] and
            priority > 0.4 and
            actionability > 0.3
        )
        # A prose fragment is not a concept receipt. Do not manufacture a
        # durable goal by extracting a few words from free text: that could
        # turn an imperative such as "rappelle" into an objective. Short,
        # structured concepts remain eligible for semantic scoring.
        should_create_goal = has_goal_signal and concept_source == "structured_topic"
        goal_proposal_deferred_reason = (
            "missing_structured_topic"
            if has_goal_signal and concept_source != "structured_topic"
            else ""
        )

        # For high-priority tensions: generate a concrete hypothesis instead of
        # just labelling the tension. This shifts action from 'resolve_tension'
        # to 'test_hypothesis' — the key upgrade the analysis identified.
        hypothesis_pending = False
        if thought_type == 'tension' and priority >= 0.65:
            # Expensive LLM synthesis is deferred until workspace competition
            # selects this proposal. Evaluating every thought must stay a
            # cheap scoring pass, not 1 LLM call per candidate.
            hypothesis_pending = True

        return {
            'type': thought_type,
            'concept': concept,
            'priority': priority,
            'actionability': actionability,
            'friction': friction,
            'goal_type': 'test_hypothesis' if hypothesis_pending else goal_type,
            'hypothesis_pending': hypothesis_pending,
            'concept_source': concept_source,
            'should_create_goal': should_create_goal,
            'goal_proposal_deferred_reason': goal_proposal_deferred_reason,
        }
    
    # ✅ FIX: added thought parameter
    def _classify_thought(self, text: str, thought: Dict) -> str:
        """Classify only from producer-owned schema fields, never prose."""
        source = str(thought.get("source") or "").strip()
        if (
            source in _NON_REEVALUATABLE_SOURCE_IDS
            or source.startswith("goal_action.")
            or source.startswith("thought_evaluator.")
        ):
            return 'mundane'
        explicit_signal = str(thought.get("cognitive_signal") or "").strip().casefold()
        if explicit_signal in _THOUGHT_TYPES_BY_SIGNAL:
            return explicit_signal
        thought_type = str(thought.get("thought_type") or "").strip().casefold()
        for signal, schema_ids in _THOUGHT_TYPES_BY_SIGNAL.items():
            if thought_type in schema_ids:
                return signal
        return 'mundane'
    
    def _compute_priority(self, thought: Dict, _thought_type: str) -> float:
        """Use producer-measured priority; do not infer it from wording."""
        try:
            priority = float(thought.get("priority", 0.5))
        except (TypeError, ValueError, OverflowError):
            priority = 0.5
        if not math.isfinite(priority):
            priority = 0.5
        return max(0.0, min(1.0, priority))
    
    def _compute_actionability(self, text: str, thought_type: str) -> float:
        return {
            'uncertainty': 0.7,
            'tension': 0.6,
            'opportunity': 0.8,
            'mundane': 0.2
        }.get(thought_type, 0.3)
    
    def _identify_friction(self, text: str, thought_type: str) -> str:
        if thought_type == 'uncertainty':
            return 'Lexical uncertainty vs. Conceptual understanding'
        elif thought_type == 'tension':
            return 'Conflicting beliefs or values'
        elif thought_type == 'opportunity':
            return 'Current state vs. Potential state'
        return ''
    
    def _determine_goal_type(self, thought_type: str) -> str:
        return {
            'uncertainty': 'resolve_uncertainty',
            'tension': 'resolve_tension',
            'opportunity': 'explore_opportunity',
            'mundane': 'routine'
        }.get(thought_type, 'general')
    
    def _generate_hypothesis(self, text: str, concept: str) -> str:
        """
        For high-priority tensions: generate a concrete testable hypothesis
        using the LLM. This upgrades the action from 'resolve_tension' to
        'test_hypothesis' — active simulation rather than passive tension-holding.

        Returns text only when the provider confirms a complete response.
        """
        return str(self._generate_hypothesis_result(text, concept).get("hypothesis") or "")

    def _generate_hypothesis_result(self, text: str, concept: str) -> Dict[str, Any]:
        """Generate one hypothesis and retain completion evidence for the caller.

        An unverified or truncated fragment must not be promoted into a
        persistent ``test_hypothesis`` goal. In particular, do not discard the
        provider's completion status by calling the legacy string-only helper.
        """
        try:
            from core.state import state as _state
            llm = getattr(_state, 'llm', None)
            if not llm or not callable(getattr(llm, "generate_bare_result", None)):
                return {"status": "unavailable", "reason_code": "completion_evidence_unavailable", "hypothesis": ""}
            prompt = (
                f"A cognitive tension has been identified around: '{concept.replace('_', ' ')}'.\n"
                f"Context: {text[:200]}\n\n"
                f"Generate ONE concrete, testable hypothesis that could resolve this tension. "
                f"Format: 'If [action], then [expected outcome].' One sentence only."
            )
            completion = llm.generate_bare_result(
                prompt, max_tokens=128, temperature=0.35,
            )
            if not isinstance(completion, dict):
                return {"status": "unverified", "reason_code": "invalid_completion_receipt", "hypothesis": ""}
            completion_status = str(completion.get("status") or "unknown").strip().casefold()
            if completion_status != "ok":
                return {
                    "status": completion_status if completion_status in {"truncated", "deferred", "error", "empty"} else "unverified",
                    "reason_code": "provider_completion_not_usable",
                    "hypothesis": "",
                    "completion_reason": str(completion.get("reason") or completion.get("completion_reason") or "")[:80],
                }
            if completion.get("completion_verified") is not True:
                return {
                    "status": "unverified",
                    "reason_code": "provider_did_not_confirm_completion",
                    "hypothesis": "",
                    "completion_reason": str(completion.get("completion_reason") or "unknown")[:80],
                }
            hyp = str(completion.get("text") or "").strip()
            if len(hyp) <= 15:
                return {"status": "empty", "reason_code": "hypothesis_too_short", "hypothesis": ""}
            import logging as _lg
            _lg.getLogger(__name__).info(
                "[ThoughtEvaluator] 🔬 Verified hypothesis for '%s': %s",
                concept, hyp[:80],
            )
            # Record for emergence metrics only after completion is verified.
            try:
                from cognition.emergence_metrics import get_collector
                c = get_collector()
                if c:
                    c.record_hypothesis(hyp)
            except Exception:
                pass
            return {
                "status": "completed",
                "reason_code": "provider_completion_verified",
                "hypothesis": hyp,
                "completion_reason": str(completion.get("completion_reason") or "completed_response")[:80],
                "output_tokens": completion.get("output_tokens"),
                "max_output_tokens": completion.get("max_output_tokens"),
            }
        except Exception as exc:
            import logging as _lg
            _lg.getLogger(__name__).warning(
                "[ThoughtEvaluator] Hypothesis generation failed (%s)",
                type(exc).__name__,
            )
            return {"status": "error", "reason_code": "generation_exception", "hypothesis": ""}

    def _has_existing_goal(self, goals_data: Dict, concept: str) -> bool:
        """
        Check if a goal with this concept already exists.

        BUG FIX: when using DAL, goals_data['goals'] is a dict {id: goal_dict},
        not a list. Iterating a dict yields string keys, so isinstance(goal, dict)
        was always False → silently skipped every goal → always returned False
        → duplicate goals created every cycle.
        """
        raw = goals_data.get('goals', {})
        concept_lower = concept.lower()

        # Handle both dict {id: goal_dict} (DAL path) and list [goal_dict] (file path)
        if isinstance(raw, dict):
            goal_iter = raw.values()
        else:
            goal_iter = raw

        for goal in goal_iter:
            if not isinstance(goal, dict):
                continue
            name = (goal.get('name') or goal.get('topic') or '').lower()
            if concept_lower in name or name in concept_lower:
                return True

        return False

    def _inject_followup_thoughts(self, dal, concept: str, thought_type: str) -> None:
        """
        Inject a follow-up thought, with dedup to prevent spam.

        BUG FIX: previously fired 'What about X?' every 30 min for the same concept,
        flooding the thought stream with noise and triggering re-evaluation loops.
        Now tracks last injection per concept and skips if within 2 hours.
        Also skips GAE insight sources — those already generate their own follow-ups.
        """
        import time as _t

        # Skip for GAE insight sources — they self-generate follow-ups
        if thought_type == 'opportunity':
            return

        # Per-concept dedup: only inject once per 2 hours
        if not hasattr(self, '_last_injected'):
            self._last_injected = {}
        now = _t.time()
        last = self._last_injected.get(concept, 0)
        if now - last < 7200:
            return

        self._last_injected[concept] = now
        content = (
            f"I keep returning to the idea of {concept.replace('_', ' ')} — "
            f"what's the core tension there?"
            if thought_type == 'tension'
            else f"There's still something to understand about {concept.replace('_', ' ')}."
        )
        try:
            dal.add_thought({
                'content': content,
                'source': 'thought_evaluator.followup',
                'priority': 0.50,
                'thought_type': 'reflection',
                'timestamp': now,
                'evaluated': False,
            })
        except Exception:
            pass

    # ✅ FIX: use content instead of text
    def _generate_id(self, thought: Dict) -> str:
        content = thought.get('content', '') + str(datetime.now().timestamp())
        return hashlib.md5(content.encode()).hexdigest()[:12]


if __name__ == "__main__":
    evaluator = SimpleThoughtEvaluator('data/persona')
    evaluator.evaluate_recent_thoughts()
