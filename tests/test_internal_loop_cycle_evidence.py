from collections import deque
import threading
from types import SimpleNamespace

from core.module_tick_log import ModuleTickLog
from core.internal_loop import InternalThoughtLoop


def make_loop():
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._cycle_evidence_lock = threading.RLock()
    loop._cycle_evidence = deque(maxlen=40)
    loop._active_cycle_evidence = None
    return loop


def test_cycle_receipt_links_outputs_to_actual_consumer_inputs_without_text():
    loop = make_loop()
    loop._begin_cycle_evidence(12)
    winner_ref = loop._record_cycle_stage(
        "workspace_competition", "completed",
        output={"winner": {"topic": "private user topic", "score": 0.81}},
    )
    loop._record_cycle_stage(
        "executive_arbitration", "completed",
        inputs={"competition_output_ref": winner_ref},
        output={"winner_type": "goal", "score": 0.83},
        metrics={"override": True},
    )
    loop._finish_cycle_evidence("completed")

    receipt = loop.cycle_evidence_snapshot()["cycles"][0]
    assert receipt["cycle_id"] == 12
    assert receipt["status"] == "completed"
    assert receipt["stages"][1]["inputs"]["competition_output_ref"] == winner_ref
    assert "private user topic" not in repr(receipt)
    assert receipt["stages"][0]["output_summary"] == {"kind": "mapping", "field_count": 1}


def test_cycle_receipts_are_bounded_and_failed_cycles_are_retained():
    loop = make_loop()
    for cycle_id in range(1, 44):
        loop._begin_cycle_evidence(cycle_id)
        loop._record_cycle_stage("core", "failed" if cycle_id == 43 else "completed")
        loop._finish_cycle_evidence("failed" if cycle_id == 43 else "completed",
                                    "RuntimeError" if cycle_id == 43 else None)

    snapshot = loop.cycle_evidence_snapshot(limit=10)
    assert snapshot["retained"] == 40
    assert len(snapshot["cycles"]) == 10
    assert snapshot["cycles"][-1]["cycle_id"] == 43
    assert snapshot["cycles"][-1]["error_type"] == "RuntimeError"
    assert "semantic_quality_not_assessed" in snapshot["evidence_scope"]


def test_in_progress_cycle_is_visible_without_being_marked_completed():
    loop = make_loop()
    loop._begin_cycle_evidence(7)
    loop._record_cycle_stage("thought_thread_engine", "completed", output=[{"id": 1}])

    snapshot = loop.cycle_evidence_snapshot()
    assert snapshot["retained"] == 0
    assert snapshot["cycles"][0]["status"] == "running"
    assert snapshot["cycles"][0]["stages"][0]["output_summary"]["item_count"] == 1


def test_module_probe_emits_per_cycle_execution_receipt():
    loop = make_loop()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_wrapped = set()
    loop._resource_economy = SimpleNamespace(tick=lambda: {"recovered": 0.2})
    loop._begin_cycle_evidence(4)

    loop._refresh_module_tick_probes(only_attr="_resource_economy")
    loop._resource_economy.tick()

    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert stage["stage"] == "module_tick:cognitive_resource_economy.tick"
    assert stage["status"] == "completed"
    assert stage["output_ref"]
    assert "recovered" not in stage["output_summary"]
    assert stage["output_summary"]["field_count"] == 1


def test_activity_from_another_thread_is_not_attributed_to_active_cycle():
    loop = make_loop()
    loop._begin_cycle_evidence(5)
    other_thread_result = []

    thread = threading.Thread(
        target=lambda: other_thread_result.append(
            loop._record_cycle_stage("concurrent_chat_call", "completed", output={"ok": True})
        )
    )
    thread.start()
    thread.join()

    assert other_thread_result == [None]
    assert loop.cycle_evidence_snapshot()["cycles"][0]["stages"] == []


def test_async_worker_result_is_attached_to_its_origin_cycle_not_current_cycle():
    loop = make_loop()
    loop._begin_cycle_evidence(10)
    loop._record_cycle_stage("motivational_field_tick", "completed",
                             output={"need_scan": "scheduled", "cycle": 10})
    loop._finish_cycle_evidence("completed")
    loop._begin_cycle_evidence(11)

    worker_result = []
    thread = threading.Thread(target=lambda: worker_result.append(
        loop.record_async_cycle_stage(
            10, "motivational_field.need_scan", "completed",
            metrics={"need_count": 2, "acted_count": 1},
        )
    ))
    thread.start()
    thread.join()

    cycles = loop.cycle_evidence_snapshot(limit=10)["cycles"]
    origin = next(cycle for cycle in cycles if cycle["cycle_id"] == 10)
    current = next(cycle for cycle in cycles if cycle["cycle_id"] == 11)
    assert worker_result == [True]
    assert origin["stages"][-1]["async_completion"] is True
    assert origin["stages"][-1]["metrics"] == {"need_count": 2, "acted_count": 1}
    assert current["stages"] == []


def test_cycle_summary_exposes_only_allowlisted_cognitive_outcome_counts():
    loop = make_loop()
    loop._begin_cycle_evidence(6)
    loop._record_cycle_stage(
        "goal_engine_tick", "completed",
        output={
            "status": "completed",
            "active_goal_count": 3,
            "accepted_candidate_count": 1,
            "private_topic": "do not expose this",
        },
    )

    summary = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]["output_summary"]
    assert summary["numeric_metrics"] == {
        "active_goal_count": 3,
        "accepted_candidate_count": 1,
    }
    assert "private_topic" not in repr(summary)
    assert "do not expose this" not in repr(summary)
