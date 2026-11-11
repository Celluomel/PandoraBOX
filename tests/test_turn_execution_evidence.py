import threading

from cognition.persona_bridge import PersonaBridge


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
