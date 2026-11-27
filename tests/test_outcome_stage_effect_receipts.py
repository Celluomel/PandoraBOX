"""Effect receipts must distinguish real updates from no-op outcome hooks."""
from pathlib import Path
from types import SimpleNamespace
import ast
import threading

from cognition.abstract_reasoning_engine import AbstractReasoningEngine, ReasoningResult
from cognition.empathy_engine import (
    AffectRead,
    EmpathyEngine,
    SIGNAL_EXPLORING,
    UserAffectModel,
)
from cognition.turn_context_evidence import (
    audit_safe_turn_summary,
    verify_history_exchange_append,
)
from core.state import _persona_relational_memory


ROOT = Path(__file__).resolve().parents[1]


class _Attractors:
    def __init__(self):
        self.values = {"curiosity": 0.5, "analytical_depth": 0.5}

    def get(self, trait):
        return self.values[trait]

    def nudge(self, trait, delta):
        self.values[trait] += delta


class _RelationalMemory:
    def __init__(self):
        self.relationship = SimpleNamespace(interaction_count=4)

    def get_or_create(self, _user_id):
        return self.relationship

    def record_exchange(self, **_kwargs):
        self.relationship.interaction_count += 1
        return self.relationship


def _empathy(*, has_read=True):
    engine = object.__new__(EmpathyEngine)
    engine._lock = threading.RLock()
    engine._last_reads = {}
    engine._models = {}
    engine._org = SimpleNamespace(attractor_system=_Attractors())
    engine._rm = _RelationalMemory()
    if has_read:
        engine._last_reads["u"] = AffectRead(
            user_id="u", signals=[SIGNAL_EXPLORING], valence="neutral", arousal="medium"
        )
        engine._models["u"] = UserAffectModel(user_id="u")
    return engine


def test_empathy_receipt_confirms_counter_and_trait_changes_without_claiming_durability():
    receipt = _empathy().record_outcome("u", "question", "answer")
    assert receipt == {
        "status": "updated",
        "relational_interaction_increment": 1,
        "attractor_traits_changed": 2,
        "persistence": "attempted_unverified",
    }


def test_empathy_without_prior_read_is_an_explicit_skip():
    receipt = _empathy(has_read=False).record_outcome("u", "question", "answer")
    assert receipt["status"] == "skipped_no_prior_affect_read"
    assert receipt["relational_interaction_increment"] == 0


def _are(result, beliefs=None):
    engine = object.__new__(AbstractReasoningEngine)
    engine._lock = threading.Lock()
    engine._cache = {"u": result} if result else {}
    engine._org = SimpleNamespace(
        world_model=SimpleNamespace(causal_beliefs=beliefs or [])
    )
    return engine


def test_abstract_reasoning_does_not_validate_its_own_insight_by_repetition():
    belief = SimpleNamespace(antecedent="a", consequent="b", confidence=0.4)
    engine = _are(ReasoningResult(user_id="u", causal_pair=("a", "b")), [belief])
    receipt = engine.record_outcome("u", "response repeats the insight")
    assert receipt == {
        "status": "skipped_no_independent_outcome_evidence",
        "beliefs_updated": 0,
        "causal_pair_available": True,
    }
    assert belief.confidence == 0.4


def test_abstract_reasoning_without_a_current_result_is_an_explicit_skip():
    engine = _are(ReasoningResult(user_id="u", causal_pair=("a", "b")))
    engine._cache.clear()
    receipt = engine.record_outcome("u", "response")
    assert receipt == {"status": "skipped_no_current_result", "beliefs_updated": 0}


def test_post_turn_reducer_handles_effect_receipts_before_generic_completed_branch():
    source = ROOT / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    method = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_stream_with_full_lifecycle"
    )
    body = ast.get_source_segment(source.read_text(encoding="utf-8"), method)
    assert body is not None
    assert '"skipped_no_prior_affect_read"' in body
    assert '"skipped_no_independent_outcome_evidence"' in body
    assert "invalid or unreported effect receipt" in body
    effect_branch = body.index("elif stage_name in {\"empathy_outcome\", \"abstract_reasoning_outcome\"}")
    post_turn_branch = body.index("elif stage_name == \"cognitive_post_turn\" and result is False")
    assert effect_branch < post_turn_branch


def test_abstract_reasoning_is_run_before_prompt_build_and_peer_scoped_out():
    source = ROOT / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge")
    method = next(
        node for node in bridge.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_stream_with_full_lifecycle"
    )
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)]
    are_call = next(
        node for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "to_thread"
        and any(isinstance(arg, ast.Attribute) and arg.attr == "reason" for arg in node.args)
    )
    prompt_call = next(
        node for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "to_thread"
        and any(isinstance(arg, ast.Attribute) and arg.attr == "_build_prompt_and_cache" for arg in node.args)
    )
    assert are_call.lineno < prompt_call.lineno
    method_source = ast.get_source_segment(source.read_text(encoding="utf-8"), method)
    assert "if peer_name" in method_source
    assert "_are_turn_status == \"completed\"" in method_source
    assert 'else "deferred" if _are_method == "deferred"' in method_source
    assert 'else "failed" if _are_method == "failed"' in method_source
    assert "allow_interactive_turn=True" in method_source
    assert '"llm_call_count"' in method_source
    assert '"reason_code"' in method_source
    builder = next(
        node for node in bridge.body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_prompt_and_cache"
    )
    builder_source = ast.get_source_segment(source.read_text(encoding="utf-8"), builder)
    assert "include_are_context" in builder_source
    append_context = next(
        node for node in bridge.body
        if isinstance(node, ast.FunctionDef) and node.name == "_append_cognitive_prompt_context"
    )
    append_source = ast.get_source_segment(source.read_text(encoding="utf-8"), append_context)
    assert '"skipped_not_applicable"' in append_source
    assert '"skipped_by_scope"' in append_source


def test_effect_receipt_summary_preserves_only_bounded_non_text_evidence():
    summary = audit_safe_turn_summary({
        "type": "cognitive_effect_receipt",
        "status": "updated",
        "relational_interaction_increment": 1,
        "attractor_traits_changed": 2,
        "persistence": "attempted_unverified",
        "private_text": "must not appear",
    })
    assert summary == {
        "type": "cognitive_effect_receipt",
        "quality": "present",
        "status": "updated",
        "relational_interaction_increment": 1,
        "attractor_traits_changed": 2,
        "persistence": "attempted_unverified",
    }


def test_route_and_history_receipts_keep_only_bounded_provenance():
    route = audit_safe_turn_summary({
        "type": "api_route_answer_receipt",
        "status": "matched_live_route_followup",
        "source": "brain.api.routes",
        "route_count": 21,
        "selected_route": {"method": "POST", "path": "/chat", "handler": "chat"},
        "resolution_source": "prior_assistant_route_verified_against_live_registry",
        "prior_route_context": "matched_current_route",
        "routes_sha256": "a" * 64,
        "answer": "private answer text is not copied",
    })
    assert route["status"] == "matched_live_route_followup"
    assert route["selected_route"] == {"method": "POST", "path": "/chat", "handler": "chat"}
    assert "answer" not in route

    history = audit_safe_turn_summary({
        "type": "conversation_history_write_receipt",
        "status": "recorded_in_memory",
        "record_history_enabled": True,
        "manager_available": True,
        "before_message_count": 2,
        "after_message_count": 4,
        "appended_message_count": 2,
        "in_memory_tail_matches": True,
        "durable_persistence": "unverified",
        "private_text": "must not appear",
    })
    assert history["appended_message_count"] == 2
    assert history["in_memory_tail_matches"] is True
    assert history["durable_persistence"] == "unverified"
    assert "private_text" not in history


def test_history_append_verification_survives_bounded_history_eviction():
    before = [
        {"role": "user", "content": f"old user {index}"}
        if index % 2 == 0 else {"role": "assistant", "content": f"old reply {index}"}
        for index in range(20)
    ]
    user_entry = {"role": "user", "content": "route follow-up"}
    assistant_entry = {"role": "assistant", "content": "POST"}
    after = [*before[2:], user_entry, assistant_entry]

    assert len(after) == len(before)
    assert verify_history_exchange_append(before, after, "route follow-up", "POST")
    assert not verify_history_exchange_append(before, before, "route follow-up", "POST")


def test_semantic_extraction_summary_exposes_persistence_without_concept_text():
    summary = audit_safe_turn_summary({
        "type": "semantic_extraction_receipt",
        "turn_kind": "topic",
        "goal_signal": "continuing_commitment",
        "goal_signal_evidence_valid": True,
        "learning_status": "accepted_topic_turn",
        "status": "completed",
        "persistence_status": "confirmed",
        "cag_status": "completed",
        "workspace_status": "completed",
        "concepts_parsed": 2,
        "concept_upsert_calls_returned": 2,
        "concepts_persisted": 2,
        "observation_calls_returned": 2,
        "observations_persisted": 2,
        "relation_upsert_calls_returned": 0,
        "relations_persisted": 0,
        "dominant_topic_selected": True,
        "curiosity_status": "stimulated",
        "curiosity_topic_selected": True,
        "curiosity_level_after": 0.60,
        "duration_ms": 12.5,
        "uncertainty_candidate": True,
        "uncertainty_source_receipt": {
            "status": "recorded", "recorded": True,
            "uncertainty_id": "uncertainty-123", "evidence": "private user evidence",
        },
        "concepts": ["private concept text"],
        "curiosity_topic": "private topic text",
    })
    assert summary["type"] == "semantic_extraction_receipt"
    assert summary["turn_kind"] == "topic"
    assert summary["goal_signal"] == "continuing_commitment"
    assert summary["goal_signal_evidence_valid"] is True
    assert summary["learning_status"] == "accepted_topic_turn"
    assert summary["persistence_status"] == "confirmed"
    assert summary["concepts_persisted"] == 2
    assert summary["dominant_topic_selected"] is True
    assert summary["curiosity_status"] == "stimulated"
    assert summary["curiosity_topic_selected"] is True
    assert summary["curiosity_level_after"] == 0.60
    assert summary["uncertainty_candidate"] is True
    assert summary["uncertainty_source_receipt"] == {
        "status": "recorded", "recorded": True,
        "uncertainty_id": "uncertainty-123",
    }
    assert "concepts" not in summary
    assert "curiosity_topic" not in summary
    assert "private topic text" not in str(summary)
    assert "private user evidence" not in str(summary)


def test_global_workspace_prompt_receipt_proves_all_open_uncertainty_refs_included():
    summary = audit_safe_turn_summary({
        "type": "global_workspace_prompt_receipt",
        "context_included": True,
        "open_uncertainty_source_count": 5,
        "uncertainty_synthesis_included": True,
        "uncertainty_source_refs": [
            "uncertainty:user-1", "uncertainty:prediction-2",
            "uncertainty:belief-3", "uncertainty:intention-4",
            "uncertainty:user-5",
        ],
        "uncertainty_source_turn_ids": ["turn-1", "turn-5"],
        "uncertainty_source_types": [
            "user_exchange:doubt", "prediction_error", "belief_conflict",
            "decision_reasoning_limit",
        ],
        "evidence": "private user quote must not enter audit summary",
    })

    assert summary["open_uncertainty_source_count"] == 5
    assert summary["uncertainty_synthesis_included"] is True
    assert len(summary["uncertainty_source_refs"]) == 5
    assert summary["uncertainty_source_turn_ids"] == ["turn-1", "turn-5"]
    assert "decision_reasoning_limit" in summary["uncertainty_source_types"]
    assert "private user quote" not in repr(summary)


def test_semantic_extraction_summary_preserves_non_topic_skip_reason():
    summary = audit_safe_turn_summary({
        "type": "semantic_extraction_receipt",
        "turn_kind": "retrieval",
        "learning_status": "skipped_non_topic_turn",
        "status": "completed",
        "persistence_status": "not_needed",
        "cag_status": "skipped_non_topic_turn",
        "workspace_status": "not_requested",
        "curiosity_status": "skipped_non_topic_turn",
        "curiosity_topic_selected": False,
        "concept_upsert_calls_returned": 0,
        "observations_persisted": 0,
    })
    assert summary["turn_kind"] == "retrieval"
    assert summary["learning_status"] == "skipped_non_topic_turn"
    assert summary["curiosity_status"] == "skipped_non_topic_turn"
    assert summary["concept_upsert_calls_returned"] == 0
    assert summary["observations_persisted"] == 0


def test_semantic_extraction_summary_proves_decision_learning_without_text():
    summary = audit_safe_turn_summary({
        "type": "semantic_extraction_receipt",
        "turn_kind": "decision",
        "learning_status": "accepted_decision_turn",
        "status": "completed",
        "persistence_status": "confirmed",
        "cag_status": "completed",
        "workspace_status": "not_requested",
        "concepts_parsed": 3,
        "concepts_persisted": 3,
        "curiosity_status": "no_grounded_dominant_topic",
        "curiosity_topic_selected": False,
        "concepts": ["private action details"],
    })
    assert summary["turn_kind"] == "decision"
    assert summary["learning_status"] == "accepted_decision_turn"
    assert summary["persistence_status"] == "confirmed"
    assert summary["concepts_persisted"] == 3
    assert summary["curiosity_topic_selected"] is False
    assert "private action details" not in repr(summary)


def test_semantic_extraction_summary_exposes_bounded_retry_exhaustion():
    summary = audit_safe_turn_summary({
        "type": "semantic_extraction_receipt",
        "status": "failed",
        "learning_status": "deferred_retry_exhausted",
        "retry_exhausted": True,
        "error_type": "_SemanticLearningDeferred",
        "concepts": ["private user concept"],
    })
    assert summary["status"] == "failed"
    assert summary["learning_status"] == "deferred_retry_exhausted"
    assert summary["retry_exhausted"] is True
    assert "private user concept" not in repr(summary)


def test_app_state_resolves_relational_memory_from_its_actual_owner():
    relationship_store = object()
    persona = SimpleNamespace(relational_memory=relationship_store)
    organism = SimpleNamespace()
    assert _persona_relational_memory(persona, organism) is relationship_store


def test_organism_relational_memory_takes_precedence_when_present():
    organism_store = object()
    persona = SimpleNamespace(relational_memory=object())
    organism = SimpleNamespace(relational_memory=organism_store)
    assert _persona_relational_memory(persona, organism) is organism_store
