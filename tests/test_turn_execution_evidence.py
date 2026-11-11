import threading
import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

from cognition.persona_bridge import (
    PersonaBridge,
    _prior_assistant_evidence_detail,
    _prior_assistant_evidence_summary,
    _prior_assistant_trace_evidence,
    _turn_output_evidence,
)


def _bridge():
    bridge = PersonaBridge.__new__(PersonaBridge)
    bridge._turn_trace_lock = threading.RLock()
    bridge._last_turn_trace = {"turn_id": "turn-evidence-1", "stages": {}}
    bridge._turn_trace_history = []
    bridge._turn_stage_health = {}
    return bridge


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


def test_streamed_answer_is_not_released_before_output_safety_gate():
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
        if isinstance(node.value, ast.Name) and node.value.id == "raw_response"
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
    assert len(history_writes) == 1
    assert history_writes[0].lineno > safety_calls[0].lineno
    assert answer_yields[0].lineno > safety_calls[0].lineno
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
