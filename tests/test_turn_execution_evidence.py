import threading
import ast
import contextvars
import inspect
from pathlib import Path
from types import MethodType, SimpleNamespace

from cognition.ai_system import EnhancedAISystem
from cognition.ai_system import generate_semantic_hash
from cognition.persona_bridge import (
    PersonaBridge,
    _prior_assistant_evidence_detail,
    _prior_assistant_evidence_summary,
    _prior_assistant_trace_evidence,
    _runtime_execution_evidence_snapshot,
    _turn_output_evidence,
    _workspace_focus_state_provenance,
)
from core.module_tick_log import summarize_output
from cognition.turn_context_evidence import (
    deterministic_reasoning_dependencies,
    response_learning_evidence,
)
from core.turn_execution_context import current_turn_id


def _bridge():
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._turn_trace_lock = threading.RLock()
    bridge._last_turn_trace = {"turn_id": "turn-evidence-1", "stages": {}}
    bridge._turn_trace_history = []
    bridge._turn_stage_health = {}
    return bridge


def test_workspace_snapshot_fallback_reports_latest_focus_writer_without_claiming_cycle():
    provenance = _workspace_focus_state_provenance({
        "focus": "private focus text is not returned",
        "updated_by": [
            {"source": "workspace_competition", "fields": ["focus"], "timestamp": 95.0},
            {"source": "world_model", "fields": ["context"], "timestamp": 99.0},
        ],
    }, now=100.0)

    assert provenance == {
        "state_focus_source": "workspace_competition",
        "state_focus_updated_at": 95.0,
        "state_focus_age_seconds": 5.0,
    }
    assert "private focus text" not in repr(provenance)


def test_workspace_snapshot_without_focus_writer_stays_unattributed():
    assert _workspace_focus_state_provenance({
        "focus": "focus", "updated_by": [
            {"source": "world_model", "fields": ["context"], "timestamp": 99.0},
        ],
    }, now=100.0) == {}


def test_workspace_focus_provenance_survives_context_source_allowlist():
    bridge = _bridge()
    bridge._record_turn_context_source(
        "global_workspace_state", "injected_snapshot_attributed",
        turn_id="turn-evidence-1", state_focus_source="workspace_competition",
        state_focus_updated_at=95.0, state_focus_age_seconds=5.0,
        focus_text="private text must be dropped",
    )

    source = bridge._last_turn_trace["context_sources"]["global_workspace_state"]

    assert source["state_focus_source"] == "workspace_competition"
    assert source["state_focus_updated_at"] == 95.0
    assert source["state_focus_age_seconds"] == 5.0
    assert "focus_text" not in source


def test_prompt_context_timings_survive_redacted_turn_trace_allowlists():
    bridge = _bridge()
    bridge._record_turn_context_source(
        "prompt_context_timing", "measured", turn_id="turn-evidence-1",
        interval_ms=4700.0,
        operations_ms={
            "self_concept_inner_voice": 12.5,
            "memory_count_query": 4.0,
            "private_prompt_text": "must be dropped",
            "invalid_duration": float("nan"),
        },
        uninstrumented_ms=4683.5,
        private_payload="must be dropped",
    )

    trace = bridge.get_turn_trace("turn-evidence-1")
    source = trace["context_sources"]["prompt_context_timing"]

    assert source["interval_ms"] == 4700.0
    assert source["operations_ms"] == {
        "self_concept_inner_voice": 12.5,
        "memory_count_query": 4.0,
    }
    assert source["uninstrumented_ms"] == 4683.5
    assert "private_payload" not in repr(trace)
    assert "must be dropped" not in repr(trace)


def test_live_affect_channels_are_auditable_but_free_text_is_not_exposed():
    bridge = _bridge()
    bridge._record_turn_context_source(
        "affective_state", "injected", turn_id="turn-evidence-1",
        affect_source="EmotionalStateManager.affective_profile",
        affect_profile={"warmth": 0.82, "satisfaction": 0.61, "secret": 0.99},
        affect_event_type="drive_satisfied", affect_event_source="goal_engine",
        affect_event_age_seconds=4.2,
        affect_event_context={"drive": "expression", "private_text": "drop me"},
        affect_description="free-form affect text must not be exposed",
    )

    trace = bridge.get_turn_trace("turn-evidence-1")
    source = trace["context_sources"]["affective_state"]

    assert source["affect_source"] == "EmotionalStateManager.affective_profile"
    assert source["affect_profile"] == {"warmth": 0.82, "satisfaction": 0.61}
    assert source["affect_event_type"] == "drive_satisfied"
    assert source["affect_event_source"] == "goal_engine"
    assert source["affect_event_age_seconds"] == 4.2
    assert source["affect_event_context"] == {"drive": "expression"}
    assert "free-form affect text" not in repr(trace)
    assert "drop me" not in repr(trace)


def test_recursive_deliberation_turn_receipt_keeps_effect_metrics_and_drops_focus_text():
    bridge = _bridge()
    bridge._record_turn_stage(
        "recursive_deliberation", "completed", turn_id="turn-evidence-1",
        output={
            "type": "cognitive_deliberation_receipt", "status": "completed",
            "cycles_run": 2, "candidates_considered": 7, "final_utility": 0.63,
            "selected_candidate_type": "goal", "internal_pressure": 0.4,
            "internal_pressure_delta": -0.1, "internal_meta_error": 0.2,
            "efficacy_candidate_present": True, "efficacy_applied_to_focus": True,
            "efficacy_multiplier": 1.2, "efficacy_score_delta": 0.03,
            "efficacy_prediction_recorded": False,
            "final_focus": "private goal text must not appear",
        },
    )

    stage = bridge.get_turn_trace("turn-evidence-1")["stages"]["recursive_deliberation"]
    summary = stage["output_summary"]
    assert summary["type"] == "cognitive_deliberation_receipt"
    assert summary["cycles_run"] == 2
    assert summary["efficacy_applied_to_focus"] is True
    assert summary["efficacy_score_delta"] == 0.03
    assert "final_focus" not in summary
    assert "private goal text" not in repr(stage)


def test_affect_receipt_consumed_by_same_turn_trace_matches_rendered_evidence():
    from cognition.self_description import (
        affect_self_report_context,
        render_affect_change_analysis,
        sanitize_affect_event_receipts,
    )

    raw_receipt = {
        "timestamp": 1_800_000_000.0,
        "event_type": "interaction_appraisal",
        "source": "update_from_interaction",
        "turn_id": "turn-evidence-1",
        "changes": {"warmth": 0.04},
    }
    safe_receipts = sanitize_affect_event_receipts([raw_receipt])
    bridge = _bridge()
    bridge._record_turn_context_source(
        "affective_state", "injected", turn_id="turn-evidence-1",
        affect_profile={"warmth": 0.82}, affect_recent_events=safe_receipts,
    )
    bridge._record_turn_stage(
        "affective_state", "captured", turn_id="turn-evidence-1",
        output={"recent_event_count": len(safe_receipts)}, consumes=("turn_input",),
    )

    trace = bridge.get_turn_trace("turn-evidence-1")
    source_events = trace["context_sources"]["affective_state"]["affect_recent_events"]
    stage = trace["stages"]["affective_state"]
    prompt_evidence = affect_self_report_context(
        {"warmth": 0.82}, recent_events=source_events,
    )
    answer = render_affect_change_analysis(prompt_evidence, language="en")

    assert source_events == safe_receipts
    assert stage["status"] == "captured"
    assert stage["consumes"][0]["stage"] == "turn_input"
    assert source_events[0]["turn_id"] == "turn-evidence-1"
    assert "warmth=+0.040" in answer
    assert "turn ID(s) turn-evidence-1" in answer


def test_recent_turn_history_preserves_redacted_pipeline_and_answer_validation():
    bridge = _bridge()
    bridge._turn_trace_history = [{
        "turn_id": "turn-history-1", "scope": "human", "status": "completed",
        "started_at": 1.0, "completed_at": 2.0, "user_id": "private-user",
        "stages": {}, "context_sources": {}, "stage_events": [],
        "pipeline_integrity": {
            "status": "incomplete_evidence",
            "scope": "execution_order_and_data_flow_only",
            "semantic_correctness": "not_assessed",
            "missing_core_stages": ["response_validation"],
            "private_detail": "must not escape",
        },
        "semantic_answer_validation": {
            "status": "not_performed", "scope": "none",
            "stage_status": "unavailable", "reason": "must not escape",
            "reviewer_status": "invalid_review_output",
            "reviewer_reason": "reviewer_did_not_return_schema_valid_json",
        },
    }]

    history = bridge.get_last_turn_trace()["recent_turns"][0]

    assert history["pipeline_integrity"]["semantic_correctness"] == "not_assessed"
    assert history["pipeline_integrity"]["missing_core_stages"] == ["response_validation"]
    assert history["semantic_answer_validation"] == {
        "status": "not_performed", "scope": "none", "stage_status": "unavailable",
        "reviewer_status": "invalid_review_output",
        "reviewer_reason": "reviewer_did_not_return_schema_valid_json",
    }
    assert "must not escape" not in repr(history)


def test_semantic_validation_receipt_keeps_dimensions_without_answer_text():
    bridge = _bridge()
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "passed", {
            "relevant": True,
            "claim_basis": "factual",
            "evidence_support": "partially_supported",
            "contract_compliant": True,
            "material_issues": [],
            "repair": "private repair text",
        },
    )

    receipt = bridge._last_turn_trace["semantic_answer_validation"]
    assert receipt["status"] == "probabilistic_review_passed"
    assert receipt["relevant"] is True
    assert receipt["claim_basis"] == "factual"
    assert receipt["evidence_support"] == "partially_supported"
    assert receipt["contract_compliant"] is True
    assert receipt["material_issue_count"] == 0
    assert "private repair text" not in repr(receipt)


def test_source_grounded_answer_receipt_is_not_mislabeled_as_llm_review():
    bridge = _bridge()
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "passed_source_grounded", {
            "relevant": True,
            "claim_basis": "factual",
            "evidence_support": "supported",
            "contract_compliant": True,
            "reason": "exact source text match",
        },
    )

    receipt = bridge._last_turn_trace["semantic_answer_validation"]
    assert receipt["status"] == "source_grounded_exact_match"
    assert receipt["scope"] == "deterministic_response_equals_retrieved_user_source"
    assert receipt["stage_status"] == "passed_source_grounded"
    assert receipt["evidence_support"] == "supported"
    assert "probabilistic" not in receipt["status"]


def test_finished_turn_preserves_source_grounded_validation_scope():
    bridge = _bridge()
    bridge._record_turn_stage(
        "semantic_answer_validation", "passed_source_grounded",
        output={
            "validation_method": "exact_source_text_match",
            "source_ref": "source-123",
            "source_status": "supported_verbatim_source",
            "exact_source_match": True,
        },
        consumes=("memory_recall_answer", "deterministic_reasoning"),
    )
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "passed_source_grounded", {
            "relevant": True,
            "claim_basis": "factual",
            "evidence_support": "supported",
            "contract_compliant": True,
            "source_ref": "source-123",
            "source_status": "supported_verbatim_source",
        },
    )

    bridge._finish_turn_trace("completed")
    receipt = bridge._last_turn_trace["semantic_answer_validation"]

    assert receipt["status"] == "source_grounded_exact_match"
    assert receipt["scope"] == "deterministic_response_equals_retrieved_user_source"
    assert receipt["stage_status"] == "passed_source_grounded"
    assert receipt["validation_method"] == "exact_source_text_match"
    assert receipt["exact_source_match"] is True
    assert receipt["source_ref"] == "source-123"
    assert receipt["source_status"] == "supported_verbatim_source"
    safe_trace = bridge.get_turn_trace("turn-evidence-1")
    assert safe_trace["semantic_answer_validation"]["validation_method"] == (
        "exact_source_text_match"
    )
    assert safe_trace["semantic_answer_validation"]["exact_source_match"] is True


def test_finished_turn_preserves_deterministic_source_abstention_receipt():
    bridge = _bridge()
    bridge._record_turn_stage(
        "semantic_answer_validation", "passed_source_abstention",
        output={
            "scope": "deterministic_recall_gate_abstained",
            "validation_method": "deterministic_abstention_result_match",
            "source_status": "abstained_insufficient_source_match",
            "exact_result_match": True,
        },
        consumes=("memory_recall_answer", "deterministic_reasoning", "turn_input"),
    )
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "passed_source_abstention", {
            "relevant": True,
            "claim_basis": "factual",
            "evidence_support": "insufficient_evidence",
            "contract_compliant": True,
            "source_status": "abstained_insufficient_source_match",
            "validation_method": "deterministic_abstention_result_match",
            "exact_result_match": True,
        },
    )

    bridge._finish_turn_trace("completed")
    receipt = bridge._last_turn_trace["semantic_answer_validation"]

    assert receipt["status"] == "source_gate_abstention"
    assert receipt["scope"] == "deterministic_recall_gate_abstained"
    assert receipt["stage_status"] == "passed_source_abstention"
    assert receipt["validation_method"] == "deterministic_abstention_result_match"
    assert receipt["source_status"] == "abstained_insufficient_source_match"
    assert receipt["exact_result_match"] is True
    assert receipt["abstention_matches_gate"] is True

    safe_trace = bridge.get_turn_trace("turn-evidence-1")
    assert safe_trace["semantic_answer_validation"]["validation_method"] == (
        "deterministic_abstention_result_match"
    )
    assert safe_trace["semantic_answer_validation"]["abstention_matches_gate"] is True


def test_deterministic_affect_report_has_source_link_and_correct_validation_summary():
    bridge = _bridge()
    bridge._record_turn_stage("turn_input", "received", output="how are you doing")
    bridge._record_turn_stage(
        "affective_state", "captured",
        output={"source": "affective_profile", "affect_profile": {"warmth": 0.91}},
        consumes=("turn_input",),
    )
    bridge._record_turn_stage(
        "affect_status_report", "completed",
        output={"source": "affective_state", "response": "computed state"},
        consumes=("affective_state", "turn_input"),
    )
    bridge._record_turn_stage(
        "semantic_answer_validation", "passed_deterministic_source_projection",
        output={
            "validation_method": "deterministic_template_from_structured_channels",
            "no_subjective_sensation_claim": True,
        },
        consumes=("affect_status_report", "turn_input"),
    )
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "passed_deterministic_source_projection", {
            "relevant": True,
            "claim_basis": "factual",
            "evidence_support": "supported",
            "contract_compliant": True,
            "validation_method": "deterministic_template_from_structured_channels",
        },
    )

    bridge._finish_turn_trace("completed")
    trace = bridge.get_turn_trace("turn-evidence-1")

    assert trace["pipeline_integrity"]["data_flow_issues"] == []
    receipt = trace["semantic_answer_validation"]
    assert receipt["status"] == "deterministic_affect_source_projection"
    assert receipt["stage_status"] == "passed_deterministic_source_projection"
    assert receipt["validation_method"] == "deterministic_template_from_structured_channels"


def test_repaired_answer_receipt_proves_second_review_without_repair_text():
    bridge = _bridge()
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "repaired_and_passed",
        {"status": "needs_revision", "material_issues": ["initial mismatch"]},
        {"status": "passed", "material_issues": [], "repair": "private corrected answer"},
    )

    receipt = bridge._last_turn_trace["semantic_answer_validation"]
    assert receipt["repair_rechecked"] is True
    assert receipt["reviewer_status"] == "needs_revision"
    assert receipt["repair_reviewer_status"] == "passed"
    assert receipt["repair_reviewer_issue_count"] == 0
    assert "private corrected answer" not in repr(receipt)


def test_invalid_reviewer_output_is_distinguished_from_reviewer_outage():
    bridge = _bridge()
    bridge._record_semantic_validation_summary(
        "turn-evidence-1", "abstained_invalid_review_output", {
            "status": "invalid_review_output",
            "reason": "reviewer_did_not_return_schema_valid_json",
        },
    )

    receipt = bridge._last_turn_trace["semantic_answer_validation"]
    assert receipt["status"] == "response_replaced_after_review"
    assert receipt["stage_status"] == "abstained_invalid_review_output"
    assert receipt["reviewer_status"] == "invalid_review_output"
    assert receipt["reviewer_reason"] == "reviewer_did_not_return_schema_valid_json"


def test_turn_stage_records_redacted_output_and_actual_consumption_link():
    bridge = _bridge()
    private_prompt = "private prompt should never appear in the audit trace"
    bridge._record_turn_stage("prompt", "completed", output=private_prompt)
    bridge._record_turn_stage(
        "generation", "completed", output="visible answer",
        consumes=("prompt",),
    )
    bridge._last_turn_trace["stages"]["readiness"] = {"status": "passed"}
    bridge._last_turn_trace["stages"]["input_safety"] = {"status": "passed"}
    bridge._last_turn_trace["stages"]["prompt_assembly"] = {
        **bridge._last_turn_trace["stages"]["prompt"], "status": "completed"
    }
    bridge._last_turn_trace["stages"]["primary_generation"] = {
        **bridge._last_turn_trace["stages"]["generation"], "status": "completed"
    }
    bridge._last_turn_trace["stages"]["output_safety"] = {"status": "passed"}
    bridge._last_turn_trace["stages"]["response_finalization"] = {"status": "completed"}
    bridge._last_turn_trace["stages"]["response"] = {"status": "completed"}

    bridge._finish_turn_trace("completed")
    trace = bridge.get_last_turn_trace()

    assert trace["stages"]["prompt"]["output_summary"]["quality"] == "present_redacted"
    assert trace["stages"]["prompt"]["output_fingerprint"]
    assert private_prompt not in repr(trace)
    assert trace["pipeline_integrity"]["data_flow_issues"] == []
    assert trace["pipeline_integrity"]["scope"] == "execution_order_and_data_flow_only"
    assert trace["pipeline_integrity"]["semantic_correctness"] == "not_assessed"
    assert trace["semantic_answer_validation"]["status"] == "not_performed"


def test_contradiction_review_records_redacted_inputs_result_and_event_effect():
    bridge = _bridge()
    event = SimpleNamespace(payload={
        "affect_outcome": {"status": "applied"},
        "contradiction_reaction": {
            "tension_status": "returned",
            "curiosity_status": "returned",
            "workspace_status": "returned",
        },
    })
    bridge._organism = SimpleNamespace(
        observatory=None,
        event_bus=SimpleNamespace(
            emit=lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("legacy emit should not be used when a receipt API exists")
            ),
            emit_with_receipt=lambda *args, **kwargs: (event, 2),
        ),
    )
    bridge._record_turn_stage("turn_input", "received", output="private user prompt")
    bridge._record_turn_stage("response_finalization", "completed", output="private final answer")
    contradiction_text = "private belief statement must never enter trace"
    system = SimpleNamespace(
        liberty_contradiction=SimpleNamespace(
            detect_contradiction=lambda **kwargs: SimpleNamespace(
                claimed_belief=contradiction_text,
            ),
        ),
        self_concept=SimpleNamespace(
            _beliefs={"belief-1": SimpleNamespace(statement=contradiction_text)},
        ),
        _interaction_count=7,
        world_model=None,
    )

    bridge._review_liberty_contradiction(system, "private final answer", "turn-evidence-1")
    trace = bridge.get_turn_trace("turn-evidence-1")
    input_stage = trace["stages"]["contradiction_review_input"]
    review_stage = trace["stages"]["contradiction_review"]

    assert input_stage["status"] == "prepared"
    assert input_stage["output_summary"]["receipt_fields"]["belief_count"] == 1
    assert input_stage["output_summary"]["receipt_fields"]["response_characters"] == len("private final answer")
    assert input_stage["output_fingerprint"]
    assert [item["stage"] for item in input_stage["consumes"]] == [
        "turn_input", "response_finalization",
    ]
    assert review_stage["status"] == "completed"
    assert review_stage["output_summary"]["receipt_fields"]["detected"] is True
    assert review_stage["output_summary"]["receipt_fields"]["event_emitted"] is True
    assert review_stage["output_summary"]["receipt_fields"]["event_handler_count"] == 2
    assert review_stage["output_summary"]["receipt_fields"]["event_status"] == "handlers_called"
    assert review_stage["output_summary"]["receipt_fields"]["affect_status"] == "applied"
    assert review_stage["output_summary"]["receipt_fields"]["tension_status"] == "returned"
    assert review_stage["output_summary"]["receipt_fields"]["curiosity_status"] == "returned"
    assert review_stage["output_summary"]["receipt_fields"]["workspace_status"] == "returned"
    assert review_stage["consumes"][0]["fingerprint"] == input_stage["output_fingerprint"]
    assert contradiction_text not in repr(trace)


def test_contradiction_review_records_no_finding_as_a_completed_negative_result():
    bridge = _bridge()
    bridge._organism = SimpleNamespace(event_bus=None, observatory=None)
    bridge._record_turn_stage("turn_input", "received", output="prompt")
    bridge._record_turn_stage("response_finalization", "completed", output="answer")
    system = SimpleNamespace(
        liberty_contradiction=SimpleNamespace(
            detect_contradiction=lambda **kwargs: None,
        ),
        self_concept=SimpleNamespace(_beliefs={}),
        _interaction_count=1,
        world_model=None,
    )

    bridge._review_liberty_contradiction(system, "answer", "turn-evidence-1")
    review_stage = bridge.get_turn_trace("turn-evidence-1")["stages"]["contradiction_review"]

    assert review_stage["status"] == "completed"
    assert review_stage["output_summary"]["receipt_fields"]["detected"] is False
    assert review_stage["output_summary"]["receipt_fields"]["event_emitted"] is False
    assert review_stage["output_summary"]["receipt_fields"]["event_status"] == "not_emitted"


def test_deterministic_reasoning_receipt_links_memory_and_planner_inputs():
    assert deterministic_reasoning_dependencies(
        selected=True, memory_recall=True,
    ) == ("turn_input", "memory_recall_answer")
    assert deterministic_reasoning_dependencies(
        selected=True, planner_snapshot=True,
    ) == ("turn_input", "planner_factual_answer")
    assert deterministic_reasoning_dependencies(
        selected=True, cognitive_audit_report=True,
    ) == ("turn_input", "cognitive_audit_status_report")
    assert deterministic_reasoning_dependencies(selected=False, memory_recall=True) == ()


def test_runtime_execution_evidence_snapshot_binds_exact_turn_and_manifest_counts():
    snapshot = _runtime_execution_evidence_snapshot({
        "turn_id": "audit-turn-7",
        "stages": {
            "turn_input": {"status": "received", "output_fingerprint": "input-fp"},
            "primary_generation": {"status": "skipped_deterministic"},
            "private_stage": {"status": "completed", "detail": "private prompt"},
        },
        "context_sources": {
            "module_tick_manifest": {
                "status": "injected", "module_count": 43,
                "observed_count": 32, "tick_count": 244, "error_count": 0,
                "initialized_unobserved_count": 10, "unavailable_count": 1,
                "private_payload": "must not be copied",
            },
        },
    })

    assert snapshot["trace_available"] is True
    assert snapshot["turn_id"] == "audit-turn-7"
    assert snapshot["stage_statuses"] == {
        "turn_input": "received",
        "primary_generation": "skipped_deterministic",
    }
    assert snapshot["module_tick_manifest"] == {
        "status": "injected", "module_count": 43, "observed_count": 32,
        "tick_count": 244, "error_count": 0,
        "initialized_unobserved_count": 10, "unavailable_count": 1,
    }
    assert "must not be copied" not in repr(snapshot)
    summary = summarize_output(snapshot)
    assert summary["receipt_fields"]["module_count"] == 43
    assert summary["receipt_fields"]["observed_count"] == 32
    assert summary["receipt_fields"]["tick_count"] == 244


def test_runtime_execution_route_uses_originating_turn_trace_snapshot():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    exact_trace_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_turn_trace"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "_audit_turn_id"
    ]
    assert exact_trace_calls
    route_names = [
        node.args[0].value for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
        and node.args and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ]
    assert "runtime_execution_evidence_snapshot" in route_names


def test_turn_trace_exposes_safe_stream_failure_type_but_redacts_exception_text():
    bridge = _bridge()
    secret_detail = "provider failed while handling private prompt content"
    bridge._record_turn_stage(
        "streaming_lifecycle", "failed", secret_detail,
        error_type="ProviderStreamError",
    )

    trace = bridge.get_last_turn_trace()

    stage = trace["stages"]["streaming_lifecycle"]
    assert stage["status"] == "failed"
    assert stage["error_type"] == "ProviderStreamError"
    assert "detail" not in stage
    assert secret_detail not in repr(trace)


def test_exact_turn_trace_is_retrievable_without_prompt_or_user_content():
    bridge = _bridge()
    bridge._last_turn_trace = {
        "turn_id": "turn-current",
        "scope": "human",
        "status": "completed",
        "started_at": 1.0,
        "completed_at": 2.0,
        "user_id": "private-user-id",
        "stages": {
            "memory_retrieval": {
                "status": "completed",
                "detail": "private recalled memory text",
                "output_fingerprint": "sha256:receipt",
                "output_summary": {"candidate_count": 2, "quality": "present_redacted"},
            },
        },
        "stage_events": [{
            "stage": "memory_retrieval", "status": "completed", "at": 1.5,
            "detail": "private recalled memory text",
            "output_fingerprint": "sha256:receipt", "consumes": [],
        }],
        "context_sources": {},
        "pipeline_integrity": {"status": "consistent"},
        "semantic_answer_validation": {"status": "not_performed", "scope": "none", "reason": "private"},
    }

    trace = bridge.get_turn_trace("turn-current")

    assert trace["turn_id"] == "turn-current"
    assert trace["stages"]["memory_retrieval"]["output_fingerprint"] == "sha256:receipt"
    assert "detail" not in trace["stages"]["memory_retrieval"]
    assert "private-user-id" not in repr(trace)
    assert "private recalled memory text" not in repr(trace)
    assert "reason" not in trace["semantic_answer_validation"]
    assert bridge.get_turn_trace("unknown-turn") is None


def test_stream_lifecycle_receives_originating_audit_turn_id():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    methods = {
        node.name: node for node in bridge_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    lifecycle = methods["_stream_with_full_lifecycle"]
    assert "audit_turn_id" in {arg.arg for arg in lifecycle.args.kwonlyargs}

    calls = [
        node for node in ast.walk(methods["_get_response_stream_impl"])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_stream_with_full_lifecycle"
    ]
    assert len(calls) == 1
    audit_turn_id = next(
        (keyword.value for keyword in calls[0].keywords if keyword.arg == "audit_turn_id"),
        None,
    )
    assert isinstance(audit_turn_id, ast.Name)
    assert audit_turn_id.id == "audit_turn_id"


def test_every_stream_pipeline_stage_is_bound_to_originating_turn():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    stream = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    stage_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
    ]
    assert len(stage_calls) >= 70
    audit_id_assignments = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_audit_turn_id"
            for target in node.targets
        )
    ]
    assert len(audit_id_assignments) == 1
    assert audit_id_assignments[0].lineno < min(call.lineno for call in stage_calls)
    for call in stage_calls:
        turn_id = next(
            (keyword.value for keyword in call.keywords if keyword.arg == "turn_id"),
            None,
        )
        assert isinstance(turn_id, ast.Name) and turn_id.id == "_audit_turn_id"


def test_world_model_profile_failure_is_attributed_to_turn_and_fails_stage():
    bridge = _bridge()
    bridge._record_turn_stage("turn_input", "completed", output="human turn")

    profile_failed = bridge._record_world_model_profile_update({
        "status": "persistence_failed",
        "changed": True,
        "persisted": False,
        "interaction_count": 12,
    }, "turn-evidence-1")

    assert profile_failed is True
    profile_stage = bridge._last_turn_trace["stages"]["world_model_profile_update"]
    assert profile_stage["status"] == "failed"
    assert profile_stage["detail"] == "persistence_failed"
    assert profile_stage["output_summary"]["status"] == "persistence_failed"
    assert profile_stage["output_summary"]["persisted"] is False
    assert profile_stage["output_summary"]["quality"] == "failed"


def test_async_peer_post_turn_stage_does_not_attach_to_newer_turn():
    bridge = _bridge()
    originating = {"turn_id": "turn-peer-origin", "stages": {}}
    newer = {"turn_id": "turn-peer-newer", "stages": {}}
    bridge._turn_trace_history.append(originating)
    bridge._last_turn_trace = newer
    bridge._system = SimpleNamespace()

    result = bridge._run_full_post_turn_lifecycle(
        "peer message", "flux", "peer response", {}, {},
        organism=None, human_interaction=False,
        audit_turn_id="turn-peer-origin",
    )

    assert result is True
    assert originating["stages"]["peer_cognitive_evaluation"]["status"] == "skipped_unavailable"
    assert newer["stages"] == {}


def test_every_async_post_turn_stage_is_bound_to_its_originating_turn():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    lifecycle = next(
        node for node in bridge_class.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_run_full_post_turn_lifecycle"
    )
    calls = [
        node for node in ast.walk(lifecycle)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
    ]
    assert calls
    for call in calls:
        turn_id = next(
            (keyword.value for keyword in call.keywords if keyword.arg == "turn_id"),
            None,
        )
        assert isinstance(turn_id, ast.Name) and turn_id.id == "audit_turn_id"


def test_failed_post_response_memory_write_fails_turn_stage_with_redacted_receipt():
    bridge = _bridge()
    bridge._record_turn_stage("turn_input", "received", output="private user text")
    bridge._record_turn_stage("response_finalization", "completed", output="private answer")
    system = SimpleNamespace(
        _last_responses=[],
        _check_if_stuck=lambda: None,
        _post_response_processing=lambda *_args: {
            "status": "failed",
            "memory_write_count": 2,
            "memory_write_kinds": ["episodic_exchange", "user_authored_message"],
            "memory_persisted_count": 1,
            "failed_operations": ["user_authored_message"],
        },
        _queue_background_tasks=lambda: None,
        liberty_contradiction=None,
        liberty_goals=None,
        _interaction_count=0,
        liberty_reflection=None,
        _apply_pending_liberty_modifications=lambda: None,
    )
    bridge._system = system
    bridge._organism = None

    result = bridge._run_full_post_turn_lifecycle(
        "private user text", "user-a", "private answer",
        {"valence": "Neutral"}, {}, organism=None,
        audit_turn_id="turn-evidence-1",
    )

    assert result is True
    stage = bridge._last_turn_trace["stages"]["response_learning_and_memory"]
    assert stage["status"] == "failed"
    assert stage["output_summary"]["failed_operations"] == ["user_authored_message"]
    assert stage["consumes"] == [
        {"stage": "turn_input", "fingerprint": bridge._last_turn_trace["stages"]["turn_input"]["output_fingerprint"]},
        {"stage": "response_finalization", "fingerprint": bridge._last_turn_trace["stages"]["response_finalization"]["output_fingerprint"]},
    ]
    assert "private user text" not in repr(stage)
    assert "private answer" not in repr(stage)


def test_post_response_processing_reports_actual_memory_write_results():
    writes = []

    class Memory:
        def analyze_emotional_context(self, _text):
            return {"valence": "Neutral", "arousal": "Low"}

        def add_memory(self, text, _impact, memory_type, *_args, **_kwargs):
            writes.append(memory_type)
            return memory_type != "user_message"

    instance = SimpleNamespace(
        self_concept=SimpleNamespace(update_from_response=lambda *_args: None),
        memory_system=Memory(),
        relational_memory=SimpleNamespace(record_exchange=lambda *_args, **_kwargs: None),
        _quick_topic=lambda _text: "topic",
        _extract_and_store_personal_facts=lambda _text: {
            "attempted_count": 0, "persisted_count": 0, "failed_count": 0,
        },
        relational_graph=SimpleNamespace(extract_and_store=lambda _text: []),
        conditioning=SimpleNamespace(record_outcome=lambda *_args, **_kwargs: None),
        evolution_engine=SimpleNamespace(
            queue_experience=lambda *_args, **_kwargs: None,
            evolve=lambda *_args, **_kwargs: None,
        ),
        personality=object(),
        _decision_policy=None,
        _last_responses=[],
        _last_user_input="",
    )

    receipt = EnhancedAISystem._post_response_processing(
        instance, "user-a", "ordinary user message", "ordinary reply",
        {"valence": "Neutral", "arousal": "Low"}, {},
    )

    assert writes == ["episodic", "user_message"]
    assert receipt["status"] == "failed"
    assert receipt["memory_write_count"] == 2
    assert receipt["memory_persisted_count"] == 1
    assert receipt["failed_operations"] == ["user_authored_message"]
    assert "ordinary user message" not in repr(receipt)
    assert "ordinary reply" not in repr(receipt)


def test_post_response_processing_treats_existing_identical_user_memory_as_deduplicated():
    duplicate_hash = generate_semantic_hash(
        "User message: ordinary user message", "user-a",
    )

    class Persistence:
        def has_memory_hash(self, semantic_hash):
            return semantic_hash == duplicate_hash

    class Memory:
        persistence = Persistence()

        def analyze_emotional_context(self, _text):
            return {"valence": "Neutral", "arousal": "Low"}

        def add_memory(self, text, _impact, memory_type, *_args, **_kwargs):
            return memory_type != "user_message"

    instance = SimpleNamespace(
        self_concept=SimpleNamespace(update_from_response=lambda *_args: None),
        memory_system=Memory(),
        relational_memory=SimpleNamespace(record_exchange=lambda *_args, **_kwargs: None),
        _quick_topic=lambda _text: "topic",
        _extract_and_store_personal_facts=lambda _text: {
            "attempted_count": 0, "persisted_count": 0, "failed_count": 0,
        },
        relational_graph=SimpleNamespace(extract_and_store=lambda _text: []),
        conditioning=SimpleNamespace(record_outcome=lambda *_args, **_kwargs: None),
        evolution_engine=SimpleNamespace(
            queue_experience=lambda *_args, **_kwargs: None,
            evolve=lambda *_args, **_kwargs: None,
        ),
        personality=object(),
        _decision_policy=None,
        _last_responses=[],
        _last_user_input="",
    )

    receipt = EnhancedAISystem._post_response_processing(
        instance, "user-a", "ordinary user message", "ordinary reply",
        {"valence": "Neutral", "arousal": "Low"}, {},
    )

    assert receipt["status"] == "completed"
    assert receipt["memory_persisted_count"] == 2
    assert receipt["memory_deduplicated_count"] == 1
    assert receipt["failed_operations"] == []
    evidence = response_learning_evidence(receipt)
    assert evidence["memory_deduplicated_count"] == 1
    assert evidence["quality"] == "present"


def test_cognitive_context_is_linked_to_prompt_assembly_on_its_own_turn():
    bridge = _bridge()
    previous = {"turn_id": "turn-cognitive-context", "stages": {}}
    bridge._turn_trace_history.append(previous)
    bridge._last_turn_trace = {"turn_id": "turn-next", "stages": {}}

    bridge._record_turn_stage(
        "cognitive_prompt_context", "completed",
        output="[Global workspace] focus: testable audit objective",
        turn_id="turn-cognitive-context",
    )
    bridge._record_turn_stage(
        "prompt_assembly", "completed", output="full assembled prompt",
        consumes=("cognitive_prompt_context",),
        turn_id="turn-cognitive-context",
    )

    stages = previous["stages"]
    assert stages["cognitive_prompt_context"]["output_fingerprint"]
    assert stages["prompt_assembly"]["consumes"] == [{
        "stage": "cognitive_prompt_context",
        "fingerprint": stages["cognitive_prompt_context"]["output_fingerprint"],
    }]
    assert bridge._last_turn_trace["stages"] == {}


def test_empty_continuity_context_is_auditable_as_an_absence_receipt():
    bridge = _bridge()
    bridge._record_turn_stage(
        "conversation_continuity_context", "empty",
        "No preceding human-chat exchange was available to anchor.",
        output={
            "injected": False,
            "reason_code": "no_preceding_exchange",
            "message_count": 0,
            "source": "conversation_history",
        },
        consumes=("conversation_history",),
        turn_id="turn-evidence-1",
    )
    bridge._record_turn_stage(
        "prompt_assembly", "completed", output="assembled prompt",
        consumes=("conversation_continuity_context",),
        turn_id="turn-evidence-1",
    )

    stages = bridge._last_turn_trace["stages"]
    absence = stages["conversation_continuity_context"]
    edge = stages["prompt_assembly"]["consumes"][0]
    assert absence["status"] == "empty"
    assert absence["output_summary"]["quality"] == "present"
    assert edge == {
        "stage": "conversation_continuity_context",
        "fingerprint": absence["output_fingerprint"],
    }


def test_memory_and_profile_receipts_can_be_attached_to_their_originating_turn():
    bridge = _bridge()
    previous = {"turn_id": "turn-memory-profile", "stages": {}}
    bridge._turn_trace_history.append(previous)
    bridge._last_turn_trace = {"turn_id": "turn-newer", "stages": {}}

    for stage_name in ("user_profile_context", "memory_retrieval", "memory_prompt_context"):
        bridge._record_turn_stage(
            stage_name, "completed", output={"source": stage_name},
            turn_id="turn-memory-profile",
        )

    assert set(previous["stages"]) == {
        "user_profile_context", "memory_retrieval", "memory_prompt_context",
    }
    assert bridge._last_turn_trace["stages"] == {}
    assert all(
        stage["output_fingerprint"] for stage in previous["stages"].values()
    )


def test_prompt_assembly_declares_cognitive_context_as_an_input():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    stream = next(
        node for node in bridge_class.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    prompt_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "prompt_assembly"
    ]
    assert len(prompt_calls) == 1
    consumes = next(
        keyword.value for keyword in prompt_calls[0].keywords
        if keyword.arg == "consumes"
    )
    assert "cognitive_prompt_context" in {
        element.value for element in consumes.elts
        if isinstance(element, ast.Constant)
    }
    system_prompt_mutations = [
        node.lineno for node in ast.walk(stream)
        if isinstance(node, (ast.Assign, ast.AugAssign))
        and (
            any(isinstance(target, ast.Name) and target.id == "system_prompt"
                for target in node.targets)
            if isinstance(node, ast.Assign)
            else isinstance(node.target, ast.Name) and node.target.id == "system_prompt"
        )
    ]
    assert system_prompt_mutations
    assert prompt_calls[0].lineno > max(system_prompt_mutations)
    for stage_name in ("generation_request", "primary_generation_input"):
        stage_call = next(
            node for node in ast.walk(stream)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_record_turn_stage"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == stage_name
        )
        turn_id = next(
            keyword.value for keyword in stage_call.keywords
            if keyword.arg == "turn_id"
        )
        assert isinstance(turn_id, ast.Name) and turn_id.id == "_audit_turn_id"


def test_memory_and_profile_context_stages_are_bound_to_prompt_turn():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    build_prompt = next(
        node for node in bridge_class.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_build_prompt_and_cache"
    )
    expected = {"user_profile_context", "memory_retrieval", "memory_prompt_context"}
    observed = set()
    for node in ast.walk(build_prompt):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_record_turn_stage"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in expected
        ):
            continue
        observed.add(node.args[0].value)
        turn_id = next(
            keyword.value for keyword in node.keywords if keyword.arg == "turn_id"
        )
        assert isinstance(turn_id, ast.Name) and turn_id.id == "audit_turn_id"
        if node.args[0].value == "user_profile_context":
            consumes = next(
                keyword.value for keyword in node.keywords
                if keyword.arg == "consumes"
            )
            assert "turn_input" in {
                item.value for item in consumes.elts
                if isinstance(item, ast.Constant)
            }
    assert observed == expected


def test_exact_filename_recall_result_crosses_prompt_worker_boundary():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    stream = next(
        node for node in bridge_class.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    build_prompt = next(
        node for node in bridge_class.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_build_prompt_and_cache"
    )
    retrieval_calls = [
        node for node in ast.walk(build_prompt)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exact_filename_recall_result"
    ]
    assert len(retrieval_calls) == 1
    assert [argument.id for argument in retrieval_calls[0].args[:2]] == [
        "user_input", "memories",
    ]
    returned = [
        node for node in ast.walk(build_prompt)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Tuple)
        and any(
            isinstance(item, ast.Name) and item.id == "_memory_recall_result"
            for item in node.value.elts
        )
    ]
    assert returned
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exact_filename_recall_result"
        for node in ast.walk(stream)
    )
    worker_assignments = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Await)
        and isinstance(node.value.value, ast.Call)
        and isinstance(node.value.value.func, ast.Attribute)
        and node.value.value.func.attr == "to_thread"
        and any(
            isinstance(argument, ast.Attribute)
            and argument.attr == "_build_prompt_and_cache"
            for argument in node.value.value.args
        )
    ]
    assert len(worker_assignments) == 1
    target = worker_assignments[0].targets[0]
    assert isinstance(target, ast.Tuple)
    target_names = [item.id for item in target.elts if isinstance(item, ast.Name)]
    assert "_memory_recall_result" in target_names
    assert target_names[-1] == "_research_receipt"


def test_deferred_profile_and_post_turn_stages_keep_originating_turn_id():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    stream = next(
        node for node in bridge_class.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    profile_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "human_profile_learning"
    ]
    assert profile_calls
    for call in profile_calls:
        turn_id = next(
            keyword.value for keyword in call.keywords if keyword.arg == "turn_id"
        )
        assert isinstance(turn_id, ast.Name) and turn_id.id == "_audit_turn_id"

    lifecycle_submissions = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run_in_executor"
        and any(
            isinstance(argument, ast.Attribute)
            and argument.attr == "_run_full_post_turn_lifecycle"
            for argument in node.args
        )
    ]
    assert len(lifecycle_submissions) == 1
    lifecycle_index = next(
        index for index, argument in enumerate(lifecycle_submissions[0].args)
        if isinstance(argument, ast.Attribute)
        and argument.attr == "_run_full_post_turn_lifecycle"
    )
    lifecycle_arguments = lifecycle_submissions[0].args[lifecycle_index + 1:]
    assert isinstance(lifecycle_arguments[-1], ast.Name)
    assert lifecycle_arguments[-1].id == "_audit_turn_id"


def test_architecture_claim_check_is_reported_as_scoped_not_general_validation():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "completed"},
        "architecture_claim_validation": {"status": "passed"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    trace = bridge.get_last_turn_trace()

    assert trace["semantic_answer_validation"] == {
        "status": "scoped_check_performed",
        "scope": "architecture_claims_against_current_trace_only",
        "stage_status": "passed",
    }
    assert trace["pipeline_integrity"]["semantic_correctness"] == "not_assessed"


def test_provider_token_limit_marks_output_and_turn_trace_incomplete():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "completed"},
        "provider_completion": {"status": "truncated_by_token_limit"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    trace = bridge.get_last_turn_trace()

    assert trace["pipeline_integrity"]["status"] == "incomplete_evidence"
    assert trace["pipeline_integrity"]["incomplete_outputs"] == ["provider_completion"]


def test_missing_provider_completion_metadata_is_incomplete_evidence():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "completed"},
        "provider_completion": {"status": "completion_metadata_missing"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    trace = bridge.get_last_turn_trace()

    assert trace["pipeline_integrity"]["status"] == "incomplete_evidence"
    assert trace["pipeline_integrity"]["incomplete_outputs"] == ["provider_completion"]


def test_turn_integrity_detects_stale_upstream_output_fingerprint():
    bridge = _bridge()
    bridge._record_turn_stage("prompt", "completed", output="first prompt")
    bridge._record_turn_stage(
        "generation", "completed", output="answer", consumes=("prompt",)
    )
    bridge._record_turn_stage("prompt", "completed", output="different prompt")
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "completed"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")

    assert bridge._last_turn_trace["pipeline_integrity"]["status"] == "incomplete_evidence"
    assert bridge._last_turn_trace["pipeline_integrity"]["data_flow_issues"] == [
        "source_output_mismatch:prompt->generation"
    ]


def test_post_turn_stage_cannot_erase_data_flow_integrity_failure():
    bridge = _bridge()
    bridge._record_turn_stage("prompt", "completed", output="first prompt")
    bridge._record_turn_stage(
        "generation", "completed", output="answer", consumes=("prompt",)
    )
    bridge._record_turn_stage("prompt", "completed", output="different prompt")
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {
            **bridge._last_turn_trace["stages"]["prompt"], "status": "completed"
        },
        "primary_generation": {
            **bridge._last_turn_trace["stages"]["generation"], "status": "completed"
        },
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    assert bridge._last_turn_trace["pipeline_integrity"]["status"] == "incomplete_evidence"
    bridge._record_turn_stage("post_turn_effect", "completed", turn_id="turn-evidence-1")

    assert bridge._last_turn_trace["pipeline_integrity"]["status"] == "incomplete_evidence"


def test_response_finalization_receipt_precedes_post_response_workers():
    source = Path(__file__).resolve().parents[1] / "cognition" / "persona_bridge.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    stream = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    finalization_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_record_turn_stage"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "response_finalization"
    ]
    worker_calls = [
        node for node in ast.walk(stream)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run_in_executor"
        and any(
            isinstance(argument, ast.Attribute)
            and argument.attr == "_run_full_post_turn_lifecycle"
            for argument in node.args
        )
    ]
    assert len(finalization_calls) == 1
    assert len(worker_calls) == 1
    assert finalization_calls[0].lineno < worker_calls[0].lineno


def test_turn_integrity_labels_deterministic_self_report_path():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "turn_input": {"status": "received"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "deterministic_reasoning": {"status": "selected_direct"},
        "primary_generation": {"status": "skipped_deterministic"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    integrity = bridge._last_turn_trace["pipeline_integrity"]

    assert integrity["status"] == "consistent"
    assert integrity["execution_path"] == "deterministic_reasoning"
    assert integrity["required_core_stages"] == 7
    assert integrity["missing_core_stages"] == []


def test_delegated_fast_route_does_not_count_as_primary_generation():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "fast_first_pass": {"status": "delegated"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    integrity = bridge._last_turn_trace["pipeline_integrity"]

    assert integrity["status"] == "incomplete_evidence"
    assert "generation" in integrity["missing_core_stages"]


def test_completed_final_answer_recovery_counts_as_generation_evidence():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "empty"},
        "final_answer_recovery": {"status": "completed"},
        "output_safety": {"status": "passed"},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")
    integrity = bridge._last_turn_trace["pipeline_integrity"]

    assert integrity["status"] == "consistent"
    assert integrity["execution_path"] == "recovered_generation"
    assert integrity["missing_core_stages"] == []


def test_recovery_generation_must_precede_output_safety():
    bridge = _bridge()
    bridge._last_turn_trace["stages"].update({
        "readiness": {"status": "passed"},
        "input_safety": {"status": "passed"},
        "prompt_assembly": {"status": "completed"},
        "primary_generation": {"status": "empty"},
        "final_answer_recovery": {"status": "completed", "at": 20},
        "output_safety": {"status": "passed", "at": 10},
        "response_finalization": {"status": "completed"},
        "response": {"status": "completed"},
    })

    bridge._finish_turn_trace("completed")

    assert "output_safety_before_final_answer_recovery" in bridge._last_turn_trace[
        "pipeline_integrity"
    ]["stage_order_violations"]


def test_progressive_sentence_stream_keeps_prefix_and_final_safety_gates():
    tree = ast.parse(Path(inspect.getfile(PersonaBridge)).read_text(encoding="utf-8"))
    bridge_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PersonaBridge"
    )
    method = next(
        node for node in bridge_class.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_stream_with_full_lifecycle"
    )
    yields = [node for node in ast.walk(method) if isinstance(node, ast.Yield)]
    safety_calls = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "check_output"
    ]
    answer_yields = [
        node for node in yields
        if isinstance(node.value, ast.Name) and node.value.id == "_remaining_response"
    ]
    progressive_yields = [
        node for node in yields
        if isinstance(node.value, ast.Name) and node.value.id == "_progressive_chunk"
    ]
    history_writes = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(part, ast.Constant) and part.value == "content"
            for target in node.targets for part in ast.walk(target)
        )
    ]

    assert len(safety_calls) == 1
    assert len(answer_yields) == 1
    assert len(progressive_yields) == 1
    assert len(history_writes) == 1
    assert history_writes[0].lineno > safety_calls[0].lineno
    assert answer_yields[0].lineno > safety_calls[0].lineno
    progressive_gate_call = next(
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_take_progressive_chunk"
    )
    assert progressive_yields[0].lineno > progressive_gate_call.lineno
    assert not any(
        isinstance(node.value, ast.Name)
        and node.value.id in {"token", "after", "before", "_before_close", "_after_close"}
        for node in yields
    )


def test_prior_answer_trace_link_ignores_enriched_current_prompt():
    previous_answer = "Live test result: 4 active goals."
    prior_fingerprint, _ = _turn_output_evidence(previous_answer)
    manager = SimpleNamespace(history=[
        {"role": "user", "content": "Previous test question"},
        {"role": "assistant", "content": previous_answer},
        {"role": "user", "content": "Current user text plus generated prompt contract"},
        {"role": "assistant", "content": "Current generated candidate"},
    ])
    trace = {"recent_turns": [{
        "turn_id": "prior-turn",
        "scope": "human",
        "status": "completed",
        "stages": {
            "response_finalization": {"output_fingerprint": prior_fingerprint},
        },
    }]}

    evidence = _prior_assistant_trace_evidence(
        manager,
        trace,
        record_history=True,
        conversation_history=None,
        current_exchange_recorded=True,
    )

    assert evidence["text"] == previous_answer
    assert evidence["trace_linked"] is True
    assert evidence["turn_id"] == "prior-turn"


def test_prior_assistant_evidence_summary_keeps_text_out_of_trace_metadata():
    answer = "Sensitive previous assistant response"
    fingerprint, _ = _turn_output_evidence(answer)
    summary = _prior_assistant_evidence_summary({
        "text": answer,
        "fingerprint": fingerprint,
        "trace_linked": True,
        "turn_id": "prior-turn-42",
        "turn_status": "completed",
    })

    assert summary == {
        "available": True,
        "trace_linked": True,
        "turn_id": "prior-turn-42",
        "fingerprint": fingerprint,
    }
    assert answer not in repr(summary)
    detail = _prior_assistant_evidence_detail(summary)
    assert "trace_linked=True" in detail
    assert "turn_id=prior-turn-42" in detail
    assert f"answer_fingerprint={fingerprint}" in detail
    assert answer not in detail


def test_architecture_validation_can_link_candidate_prior_evidence_and_final_output():
    bridge = _bridge()
    bridge._record_turn_stage("turn_input", "received", output="follow-up")
    bridge._record_turn_stage("primary_generation_input", "delivered", output={"prompt": "bounded"})
    bridge._record_turn_stage("generation_candidate", "completed", output="candidate", consumes=("primary_generation_input",))
    bridge._record_turn_stage(
        "prior_assistant_evidence", "linked",
        output={"available": True, "trace_linked": True, "turn_id": "prior-turn", "fingerprint": "abc123"},
    )
    bridge._record_turn_stage(
        "architecture_claim_validation", "replaced_unverified_claims",
        output="grounded final", consumes=("generation_candidate", "prior_assistant_evidence", "turn_input"),
    )

    stages = bridge._last_turn_trace["stages"]
    validation = stages["architecture_claim_validation"]
    assert validation["output_fingerprint"] == _turn_output_evidence("grounded final")[0]
    assert [item["stage"] for item in validation["consumes"]] == [
        "generation_candidate", "prior_assistant_evidence", "turn_input",
    ]
    assert validation["consumes"][0]["fingerprint"] == stages["generation_candidate"]["output_fingerprint"]


def test_chat_turn_context_matches_trace_id_and_resets_after_completion():
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._response_turn_lock = _ImmediateAsyncLock()
    bridge._turn_sequence = 0
    bridge._last_turn_trace = {"turn_id": "", "cognitive_scope_id": "default"}
    observed = []

    async def fake_impl(self, _user_text, **kwargs):
        observed.append((current_turn_id.get(), kwargs["turn_id"]))
        self._turn_sequence += 1
        self._last_turn_trace = {
            "turn_id": kwargs["turn_id"],
            "cognitive_scope_id": "default",
        }
        yield "answer"
        yield {"__meta__": True}

    bridge._get_response_stream_impl = MethodType(fake_impl, bridge)

    result = _drain_immediate_async_generator(bridge.get_response_stream("test prompt"))
    generated_id = result[-1]["turn_id"]
    assert generated_id.startswith("lumina-")
    assert observed == [(generated_id, generated_id)]
    assert current_turn_id.get() == ""


def test_explicit_turn_id_is_used_for_context_correlation():
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._response_turn_lock = _ImmediateAsyncLock()
    bridge._turn_sequence = 0
    bridge._last_turn_trace = {"turn_id": "", "cognitive_scope_id": "default"}
    seen = []

    async def fake_impl(self, _user_text, **kwargs):
        seen.append(current_turn_id.get())
        self._turn_sequence += 1
        self._last_turn_trace = {
            "turn_id": kwargs["turn_id"],
            "cognitive_scope_id": "default",
        }
        yield {"__meta__": True}

    bridge._get_response_stream_impl = MethodType(fake_impl, bridge)

    result = _drain_immediate_async_generator(
        bridge.get_response_stream("test", turn_id="caller-turn-7"),
        fresh_context_per_next=True,
    )
    assert result[-1]["turn_id"] == "caller-turn-7"
    assert seen == ["caller-turn-7"]


class _ImmediateAsyncLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


def _drain_immediate_async_generator(generator, *, fresh_context_per_next=False):
    """Run the no-I/O fake async generator without Windows socketpair setup."""
    result = []
    while True:
        operation = generator.__anext__()
        try:
            context = contextvars.Context() if fresh_context_per_next else None
            value = (
                context.run(operation.send, None)
                if context is not None else operation.send(None)
            )
        except StopIteration as completed:
            result.append(completed.value)
        except StopAsyncIteration:
            return result

