from collections import deque
import hashlib
import json
import threading
from types import SimpleNamespace

from core.module_tick_log import ModuleTickLog, summarize_output
from core.cognitive_governor import CognitiveGovernor
from core.internal_loop import InternalThoughtLoop, _executive_arbitration_skip_reason
from cognition.global_workspace import GlobalWorkspace
from cognition.dominant_thought_selector import SelectionResult
from cognition.thought_thread_engine import ThoughtThread, ThoughtThreadStatus
from cognition.cognitive_dissonance_engine import DissonanceEvent, DissonanceEventType


def make_loop():
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._process_instance_id = "test-process-instance"
    loop._cycle_evidence_lock = threading.RLock()
    loop._cycle_evidence = deque(maxlen=40)
    loop._active_cycle_evidence = None
    loop._cycle_evidence_audit_path = None
    loop._cycle_evidence_persistence_status = "disabled"
    loop._cycle_evidence_load_failed = False
    loop._module_tick_wrapped = set()
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


def test_failure_cycle_receipt_keeps_bounded_redacted_diagnostic():
    loop = make_loop()
    loop._begin_cycle_evidence(13)
    error = RuntimeError(
        "provider failed password=hunter2 api_key=sk-test Bearer abc123"
    )

    loop._finish_cycle_evidence(
        "failed", type(error).__name__, loop._exception_summary(error),
    )
    receipt = loop.cycle_evidence_snapshot()["cycles"][0]

    assert receipt["error_type"] == "RuntimeError"
    assert "provider failed" in receipt["error_summary"]
    assert "hunter2" not in repr(receipt)
    assert "sk-test" not in repr(receipt)
    assert "abc123" not in repr(receipt)
    assert len(receipt["error_summary"]) <= 240


def test_audit_mode_cycle_receipts_persist_and_restore_across_restart(tmp_path):
    path = tmp_path / "cycle-evidence.json"
    loop = make_loop()
    loop._cycle_evidence_audit_path = path
    loop._cycle_evidence_persistence_status = "new_store"
    loop._begin_cycle_evidence(41)
    output_ref = loop._record_cycle_stage(
        "cognitive_dissonance_engine", "completed",
        output={"event_store_status": "persisted", "event_count": 4},
        metrics={"prediction_detector_status": "unavailable_no_outcome_results"},
    )
    loop._finish_cycle_evidence("completed")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "lumina_cognitive_cycle_evidence.v1"
    assert payload["cycles"][0]["process_id"] > 0
    assert payload["cycles"][0]["process_instance_id"] == loop._process_instance_id
    assert payload["cycles"][0]["stages"][0]["output_ref"] == output_ref
    assert loop.cycle_evidence_snapshot()["persistence_status"] == "persisted"

    restored = make_loop()
    restored._process_instance_id = "restored-process-instance"
    restored._cycle_evidence_audit_path = path
    restored._load_cycle_evidence_audit()
    snapshot = restored.cycle_evidence_snapshot()
    assert snapshot["persistence_status"] == "loaded"
    assert snapshot["cycles"] == []
    assert snapshot["historical_cycles"][0]["cycle_id"] == 41
    assert snapshot["historical_cycles"][0]["stages"][0]["metrics"]["prediction_detector_status"] == "unavailable_no_outcome_results"


def test_cycle_snapshot_never_labels_previous_process_receipts_as_live():
    loop = make_loop()
    loop._process_instance_id = "current-process-instance"
    loop._cycle_evidence.append({
        "cycle_id": 99,
        "process_id": 101,
        "process_instance_id": "previous-process-instance",
        "stages": [],
    })

    snapshot = loop.cycle_evidence_snapshot()

    assert snapshot["current_process_instance_id"] == "current-process-instance"
    assert snapshot["cycles"] == []
    assert snapshot["historical_cycles"][0]["cycle_id"] == 99


def test_audit_cycle_receipt_does_not_overwrite_corrupt_journal(tmp_path):
    path = tmp_path / "cycle-evidence.json"
    original = b"not-json"
    path.write_bytes(original)
    loop = make_loop()
    loop._cycle_evidence_audit_path = path
    loop._load_cycle_evidence_audit()
    loop._begin_cycle_evidence(42)
    loop._record_cycle_stage("test_stage", "completed", output={"ok": True})
    loop._finish_cycle_evidence("completed")

    assert loop.cycle_evidence_snapshot()["persistence_status"] == "load_failed_preserved"
    assert path.read_bytes() == original


def test_cycle_receipt_keeps_boolean_action_effect_evidence_without_user_text():
    summary = InternalThoughtLoop._evidence_summary({
        "action": "memory_recall",
        "goal_state_persisted": True,
        "memory_retrieved": True,
        "thought_published": False,
        "thought_stream_recorded": False,
        "workspace_broadcast": False,
        "result": "private recalled text",
    })

    assert summary["goal_state_persisted"] is True
    assert summary["memory_retrieved"] is True
    assert summary["thought_published"] is False
    assert summary["thought_stream_recorded"] is False
    assert summary["workspace_broadcast"] is False
    assert summary["action"] == "memory_recall"
    assert "private recalled text" not in repr(summary)


def test_selection_result_receipt_keeps_choice_metrics_without_topic_or_rationale_text():
    dominant = SimpleNamespace(
        id="thread-private-id", topic="private audit topic", confidence=0.7,
        uncertainty=0.2, dissonance=0.1, safety_risk=0.0, curiosity=0.4,
    )
    result = SelectionResult(
        dominant=dominant,
        secondary=[SimpleNamespace(id="secondary")],
        scores={"thread-private-id": 0.63, "other-private-id": 0.31},
        rationale="Selected private audit topic for current pressure",
    )

    summary = InternalThoughtLoop._evidence_summary(result)

    assert summary["selection_outcome"] == "selected"
    assert summary["has_dominant"] is True
    assert summary["secondary_count"] == 1
    assert summary["scored_candidate_count"] == 2
    assert summary["selected_score"] == 0.63
    assert summary["score_distribution"] == {
        "count": 2, "min": 0.31, "mean": 0.47, "max": 0.63,
    }
    assert "private audit topic" not in repr(summary)
    assert "Selected private audit topic" not in repr(summary)


def test_selection_result_receipt_distinguishes_no_eligible_threads_from_threshold_rejection():
    no_candidates = InternalThoughtLoop._evidence_summary(
        SelectionResult(dominant=None, scores={}, rationale="No eligible threads")
    )
    below_threshold = InternalThoughtLoop._evidence_summary(
        SelectionResult(dominant=None, scores={"thread-id": 0.12}, rationale="Below threshold")
    )

    assert no_candidates["selection_outcome"] == "no_eligible_threads"
    assert below_threshold["selection_outcome"] == "below_threshold"
    assert below_threshold["scored_candidate_count"] == 1


def test_module_tick_selection_result_keeps_choice_metrics_without_private_text():
    result = SelectionResult(
        dominant=SimpleNamespace(
            id="private-id", topic="private topic", confidence=0.7,
            uncertainty=0.2, dissonance=0.1, safety_risk=0.0, curiosity=0.4,
        ),
        secondary=[],
        scores={"private-id": 0.63},
        rationale="Private rationale text",
    )

    summary = summarize_output(result)

    assert summary["type"] == "SelectionResult"
    assert summary["selection_outcome"] == "selected"
    assert summary["scored_candidate_count"] == 1
    assert summary["selected_score"] == 0.63
    assert summary["dominant_metrics"]["confidence"] == 0.7
    assert "private topic" not in repr(summary)
    assert "Private rationale text" not in repr(summary)


def test_goal_admission_receipt_preserves_rejection_counts_and_safe_reason_codes():
    summary = InternalThoughtLoop._evidence_summary({
        "accepted_count": 2,
        "rejected_count": 3,
        "rejection_reason_counts": {
            "low_quality_topic": 2,
            "quality_unavailable": 1,
            "private free-form explanation": 99,
        },
        "rejections": [{"topic": "private topic text"}],
    })

    assert summary["numeric_metrics"] == {"accepted_count": 2, "rejected_count": 3}
    assert summary["rejection_reason_counts"] == {
        "low_quality_topic": 2,
        "quality_unavailable": 1,
    }
    assert "private topic text" not in repr(summary)
    assert "private free-form explanation" not in repr(summary)


def test_goal_quality_filter_performance_metrics_are_kept_in_cycle_receipt():
    summary = InternalThoughtLoop._evidence_summary({
        "semantic_scoring_ms": 12.5,
        "goal_scoring_ms": 0.8,
        "goal_persistence_ms": 3.1,
        "semantic_scoring_batch_count": 1,
        "provider_prompt": "must not be copied into evidence",
    })

    assert summary["numeric_metrics"] == {
        "semantic_scoring_ms": 12.5,
        "goal_scoring_ms": 0.8,
        "goal_persistence_ms": 3.1,
        "semantic_scoring_batch_count": 1,
    }
    assert "provider_prompt" not in summary


def test_cycle_receipt_distinguishes_in_memory_commit_from_persistence_checkpoint():
    summary = InternalThoughtLoop._evidence_summary({
        "outcome_status": "committed",
        "reason_code": "commitment_added",
        "cycle": 13906,
        "history_count": 51,
        "persistence_status": "deferred_by_checkpoint",
        "topic": "private cognitive topic",
    })

    assert summary["outcome_status"] == "committed"
    assert summary["persistence_status"] == "deferred_by_checkpoint"
    assert summary["numeric_metrics"]["history_count"] == 51
    assert "private cognitive topic" not in repr(summary)


def test_phase2_narrative_delivery_receipt_links_synthesis_to_workspace_admission():
    loop = make_loop()
    loop._begin_cycle_evidence(24)
    narrative_ref = loop._record_cycle_stage(
        "phase2_narrative_synthesis", "completed",
        output={"narrative_present": True},
    )

    class _Workspace:
        def broadcast(self, **_kwargs):
            return True

    loop._publish_phase2_narrative(
        "private narrative text", _Workspace(), narrative_ref,
    )
    loop._finish_cycle_evidence("completed")

    receipt = loop.cycle_evidence_snapshot()["cycles"][0]
    delivery = next(
        stage for stage in receipt["stages"]
        if stage["stage"] == "phase2_narrative_workspace_broadcast"
    )
    assert delivery["status"] == "admitted"
    assert delivery["inputs"]["narrative_output_ref"] == narrative_ref
    assert delivery["output_summary"]["workspace_broadcast"] is True
    assert "private narrative text" not in repr(receipt)


def test_phase2_narrative_delivery_receipt_reports_workspace_rejection():
    loop = make_loop()
    loop._begin_cycle_evidence(25)

    class _Workspace:
        def broadcast(self, **_kwargs):
            return False

    loop._publish_phase2_narrative("narrative", _Workspace(), "narrative-ref")

    receipt = loop.cycle_evidence_snapshot()["cycles"][0]
    delivery = receipt["stages"][0]
    assert delivery["stage"] == "phase2_narrative_workspace_broadcast"
    assert delivery["status"] == "rejected"
    assert delivery["output_summary"]["workspace_broadcast"] is False


def test_phase2_narrative_delivery_receipt_distinguishes_missing_workspace():
    loop = make_loop()
    loop._begin_cycle_evidence(26)

    loop._publish_phase2_narrative("narrative", None, "narrative-ref")

    receipt = loop.cycle_evidence_snapshot()["cycles"][0]
    delivery = receipt["stages"][0]
    assert delivery["status"] == "unavailable"
    assert delivery["output_summary"]["delivery_status"] == "workspace_unavailable"


def test_workspace_decision_age_does_not_encode_missing_winner_as_giant_stale_age():
    assert InternalThoughtLoop._workspace_decision_age_cycles(11085, None, None) is None
    assert InternalThoughtLoop._workspace_decision_age_cycles(
        11085, {"type": "thought"}, -10**9,
    ) is None
    assert InternalThoughtLoop._workspace_decision_age_cycles(
        11085, {"type": "goal"}, 11080,
    ) == 5


def test_executive_arbitration_skip_reason_distinguishes_non_goal_winner():
    result = {
        "winner": {"type": "thought", "name": "internal reflection"},
        "competition": {"all_candidates": [
            {"type": "thought", "score": 0.8},
            {"type": "thought", "score": 0.7},
        ]},
    }

    assert _executive_arbitration_skip_reason(result, object()) == "no_goal_candidates"


def test_executive_arbitration_skip_reason_identifies_missing_predictor():
    result = {
        "winner": {"type": "goal", "name": "audit memory recall"},
        "competition": {"all_candidates": [{"type": "goal", "score": 0.8}]},
    }

    assert _executive_arbitration_skip_reason(result, None) == "prediction_model_unavailable"


def test_executive_arbitration_skip_reason_does_not_claim_a_result_when_prediction_is_empty():
    result = {
        "winner": {"type": "goal", "name": "audit memory recall"},
        "competition": {"all_candidates": [{"type": "goal", "score": 0.8}]},
    }
    predictor = SimpleNamespace(read_state=lambda: None)

    assert _executive_arbitration_skip_reason(result, predictor) == "no_predictable_candidate"


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


def test_cycle_list_summary_exposes_tte_lifecycle_without_private_thread_text():
    active = ThoughtThread(
        id="thread-private-1", topic="private topic one", goal="private goal one",
        status=ThoughtThreadStatus.ACTIVE, confidence=0.7, uncertainty=0.2,
    )
    completed = ThoughtThread(
        id="thread-private-2", topic="private topic two", goal="private goal two",
        status=ThoughtThreadStatus.COMPLETED, confidence=0.9, uncertainty=0.1,
    )

    summary = InternalThoughtLoop._evidence_summary([active, completed])

    assert summary["item_count"] == 2
    assert summary["item_type_counts"] == {"ThoughtThread": 2}
    assert summary["status_counts"] == {"active": 1, "completed": 1}
    assert summary["numeric_metrics"]["confidence"] == {
        "count": 2, "min": 0.7, "mean": 0.8, "max": 0.9,
    }
    assert len(summary["item_id_refs"]) == 2
    assert "private topic" not in str(summary)
    assert "private goal" not in str(summary)


def test_cycle_list_summary_exposes_cde_resolution_and_event_distributions():
    unresolved = DissonanceEvent(
        id="event-private-1", type=DissonanceEventType.BELIEF_VS_EVIDENCE,
        intensity=0.4, resolved=False, resolution_status="deferred_low_intensity",
        self_question="private question",
    )
    resolved = DissonanceEvent(
        id="event-private-2", type=DissonanceEventType.PREDICTION_VS_REALITY,
        intensity=0.8, resolved=True, resolution_status="verified_resolved",
        self_question="another private question",
    )

    summary = InternalThoughtLoop._evidence_summary([unresolved, resolved])

    assert summary["event_type_counts"] == {
        "belief_vs_evidence": 1, "prediction_vs_reality": 1,
    }
    assert summary["resolution_status_counts"] == {
        "deferred_low_intensity": 1, "verified_resolved": 1,
    }
    assert summary["resolved_count"] == 1
    assert summary["numeric_metrics"]["intensity"]["mean"] == 0.6
    assert "private question" not in str(summary)


def test_cycle_list_summary_keeps_unrecognized_payloads_count_only():
    values = [
        "private free text",
        {"status": "completed", "id": "untrusted prose id"},
    ]

    summary = InternalThoughtLoop._evidence_summary(values)

    assert summary["item_count"] == 2
    assert summary["item_type_counts"] == {"str": 1, "mapping": 1}
    assert "status_counts" not in summary
    assert "item_id_refs" not in summary
    assert "private free text" not in str(summary)
    assert "untrusted prose id" not in str(summary)


def test_cycle_list_summary_bounds_typed_record_inspection():
    values = [
        ThoughtThread(
            id=f"thread-{index}", topic="private", goal="private",
            status=ThoughtThreadStatus.ACTIVE,
        )
        for index in range(205)
    ]

    summary = InternalThoughtLoop._evidence_summary(values)

    assert summary["item_count"] == 205
    assert summary["inspected_count"] == 200
    assert summary["truncated"] is True
    assert summary["status_counts"] == {"active": 200}


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


def test_module_probe_records_hashed_inputs_without_claiming_unobserved_effects():
    loop = make_loop()
    loop._module_tick_log = ModuleTickLog()

    class SideEffectModule:
        def tick(self, context) -> None:
            self.last_context = context

    loop._side_effect_module = SideEffectModule()
    loop._begin_cycle_evidence(5)
    loop._refresh_module_tick_probes(only_attr="_side_effect_module")
    # Add this one-off probe entry without changing the production registry.
    from core.internal_loop import _TICK_PROBES
    _TICK_PROBES["_side_effect_module"] = ("test_side_effect_module", ("tick",))
    try:
        loop._refresh_module_tick_probes(only_attr="_side_effect_module")
        loop._side_effect_module.tick({"private": "do not retain"})
    finally:
        _TICK_PROBES.pop("_side_effect_module", None)

    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert stage["inputs"]["args"][0]["ref"]
    assert stage["inputs"]["args"][0]["summary"]["field_count"] == 1
    assert stage["output_summary"] == {"kind": "none", "quality": "no_return_unverified"}
    assert "do not retain" not in repr(stage)


def test_periodic_module_not_due_is_explicit_without_counting_a_fake_tick():
    loop = make_loop()
    loop._slow_cycle_count = 7
    loop._goal_quality_filter = object()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_log.register("goal_quality_filter", initialized=True)
    loop._begin_cycle_evidence(7)

    assert not loop._periodic_module_due(
        "_goal_quality_filter", "goal_quality_filter", 20, "GQF",
    )

    snapshot = loop.module_tick_snapshot()
    assert snapshot["goal_quality_filter"]["tick_count"] == 0
    assert snapshot["goal_quality_filter"]["skip_count"] == 1
    assert snapshot["goal_quality_filter"]["state"] == "skipped_by_policy"
    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert stage["stage"] == "goal_quality_filter"
    assert stage["status"] == "skipped_cadence"
    assert stage["metrics"] == {"cycle": 7, "interval_cycles": 20}


def test_periodic_module_governor_skip_is_distinct_from_cadence_skip():
    loop = make_loop()
    loop._slow_cycle_count = 20
    loop._goal_quality_filter = object()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_log.register("goal_quality_filter", initialized=True)
    loop._governor = SimpleNamespace(
        may_run=lambda _name: False,
        status=lambda: SimpleNamespace(
            mode="structured",
            total_pressure=0.31,
            budget_remaining=0,
            blocked_systems=["GQF(budget_exhausted)"],
        ),
    )
    loop._begin_cycle_evidence(20)

    assert not loop._periodic_module_due(
        "_goal_quality_filter", "goal_quality_filter", 20, "GQF",
    )

    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert stage["status"] == "skipped_governor"
    assert stage["metrics"] == {
        "cycle": 20,
        "interval_cycles": 20,
        "governor_subsystem": "GQF",
        "governor_mode": "structured",
        "governor_pressure": 0.31,
        "governor_budget_remaining": 0,
        "governor_block_reason": "budget_exhausted",
    }
    module = loop.module_tick_snapshot()["goal_quality_filter"]
    assert module["tick_count"] == 0
    assert module["skip_count"] == 1
    assert module["last_skip_status"] == "skipped_governor"


def test_phase2_cadence_receipt_maps_to_orchestrator_without_fake_tick():
    loop = make_loop()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_log.register("phase2_orchestrator", initialized=True)
    loop._phase2 = object()
    loop._begin_cycle_evidence(9)

    loop._record_cycle_stage("phase2_narrative_synthesis", "skipped_cadence",
                             metrics={"cycle": 9})

    module = loop.module_tick_snapshot()["phase2_orchestrator"]
    assert module["tick_count"] == 0
    assert module["skip_count"] == 1
    assert module["last_skip_status"] == "skipped_cadence"
    assert module["state"] == "skipped_by_policy"


def test_arbitration_learning_maintenance_skip_is_recorded_without_fake_tick():
    loop = make_loop()
    loop._arbitration_learning = object()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_log.register("arbitration_learning", initialized=True)
    loop._slow_cycle_count = 10919
    loop._begin_cycle_evidence(10919)

    assert not loop._periodic_module_due(
        "_arbitration_learning", "arbitration_learning", 8, "ARB_LEARN",
    )
    module = loop.module_tick_snapshot()["arbitration_learning"]
    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert module["tick_count"] == 0
    assert module["skip_count"] == 1
    assert module["state"] == "skipped_by_policy"
    assert stage["stage"] == "arbitration_learning"
    assert stage["status"] == "skipped_cadence"
    assert stage["metrics"] == {"cycle": 10919, "interval_cycles": 8}


def test_consolidation_and_self_concept_skips_are_attributed_without_fake_ticks():
    loop = make_loop()
    loop._module_tick_log = ModuleTickLog()
    loop._module_tick_log.register("cognitive_flux_engine", initialized=True)
    loop._module_tick_log.register("cognitive_attention_engine", initialized=True)
    loop._module_tick_log.register("self_concept_synchronizer", initialized=True)
    loop._flux_engine = object()
    loop._attention_engine = object()
    loop._self_concept_sync = object()
    loop._begin_cycle_evidence(10902)

    for name in (
        "cognitive_flux_engine",
        "cognitive_attention_engine",
        "self_concept_synchronizer",
    ):
        loop._record_cycle_stage(name, "skipped_cadence",
                                 metrics={"cycle": 10902, "interval_cycles": 5})

    snapshot = loop.module_tick_snapshot()
    for name in (
        "cognitive_flux_engine",
        "cognitive_attention_engine",
        "self_concept_synchronizer",
    ):
        assert snapshot[name]["tick_count"] == 0
        assert snapshot[name]["skip_count"] == 1
        assert snapshot[name]["state"] == "skipped_by_policy"


def test_thread_lifecycle_and_persistent_executive_record_cadence_skips():
    loop = make_loop()
    loop._slow_cycle_count = 10144
    loop._thread_lifecycle_mgr = object()
    loop._persistent_exec_loop = object()
    loop._governor = SimpleNamespace(may_run=lambda _name: True)
    loop._begin_cycle_evidence(10144)

    assert not loop._periodic_module_due(
        "_thread_lifecycle_mgr", "thread_lifecycle_manager", 15, "ThreadLifecycle"
    )
    assert not loop._periodic_module_due(
        "_persistent_exec_loop", "persistent_executive_loop", 10, "PEL"
    )

    stages = loop.cycle_evidence_snapshot()["cycles"][0]["stages"]
    assert [(item["stage"], item["status"]) for item in stages] == [
        ("thread_lifecycle_manager", "skipped_cadence"),
        ("persistent_executive_loop", "skipped_cadence"),
    ]


def test_periodic_module_runs_only_when_due_and_governor_allows():
    loop = make_loop()
    loop._slow_cycle_count = 20
    loop._goal_quality_filter = object()
    loop._governor = SimpleNamespace(may_run=lambda _name: True)
    loop._begin_cycle_evidence(20)

    assert loop._periodic_module_due(
        "_goal_quality_filter", "goal_quality_filter", 20, "GQF",
    )
    assert loop.cycle_evidence_snapshot()["cycles"][0]["stages"] == []


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


def test_async_action_receipt_exposes_effect_flags_without_result_text():
    loop = make_loop()
    loop._begin_cycle_evidence(41)
    loop._finish_cycle_evidence("completed")

    assert loop.record_async_cycle_stage(
        41,
        "goal_action_executor.web_search",
        "succeeded",
        output={
            "action": "web_search",
            "success": True,
            "goal_state_persisted": True,
            "thought_stream_recorded": True,
            "workspace_broadcast": True,
            "research_item_queued": True,
            "result": "private research summary",
        },
    )
    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]

    assert stage["output_ref"]
    assert stage["output_summary"]["success"] is True
    assert stage["output_summary"]["goal_state_persisted"] is True
    assert stage["output_summary"]["thought_stream_recorded"] is True
    assert stage["output_summary"]["workspace_broadcast"] is True
    assert stage["output_summary"]["research_item_queued"] is True
    assert "private research summary" not in repr(stage)


def test_cycle_summary_exposes_only_allowlisted_cognitive_outcome_counts():
    loop = make_loop()
    loop._begin_cycle_evidence(6)
    loop._record_cycle_stage(
        "goal_engine_tick", "completed",
        output={
            "status": "completed",
            "active_goal_count": 3,
            "accepted_candidate_count": 1,
            "created_count": 2,
            "updated_count": 1,
            "merged_count": 0,
            "pre_goal_records_seen": 23,
            "post_goal_records_seen": 18,
            "pre_dormant_goal_count": 5,
            "post_dormant_goal_count": 0,
            "private_topic": "do not expose this",
        },
    )

    summary = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]["output_summary"]
    assert summary["numeric_metrics"] == {
        "active_goal_count": 3,
        "accepted_candidate_count": 1,
        "created_count": 2,
        "updated_count": 1,
        "merged_count": 0,
        "pre_goal_records_seen": 23,
        "post_goal_records_seen": 18,
        "pre_dormant_goal_count": 5,
        "post_dormant_goal_count": 0,
    }
    assert "private_topic" not in repr(summary)
    assert "do not expose this" not in repr(summary)


def test_cycle_summary_exposes_safe_executor_outcome_and_hashed_execution_ref():
    loop = make_loop()
    loop._begin_cycle_evidence(17)
    loop._record_cycle_stage(
        "goal_action_executor", "failed",
        output={
            "action": "memory_recall",
            "outcome_status": "failed",
            "reason_code": "no_relevant_memories",
            "success": False,
            "execution_id": "act_private_identifier",
            "goal_topic": "private topic must remain hidden",
            "result": "private retrieved text must remain hidden",
        },
    )

    summary = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]["output_summary"]
    assert summary["action"] == "memory_recall"
    assert summary["outcome_status"] == "failed"
    assert summary["reason_code"] == "no_relevant_memories"
    assert summary["success"] is False
    assert summary["execution_ref"]
    assert "goal_topic" not in repr(summary)
    assert "private retrieved text" not in repr(summary)


def test_async_goal_action_outcome_is_attached_to_its_origin_cycle():
    from cognition.goal_action_executor import GoalActionExecutor

    loop = make_loop()
    loop._begin_cycle_evidence(23)
    loop._record_cycle_stage(
        "goal_action_executor", "dispatched",
        output={
            "action": "web_search", "outcome_status": "dispatched",
            "success": False, "execution_id": "act_async_23",
        },
    )
    loop._finish_cycle_evidence("completed")

    executor = GoalActionExecutor.__new__(GoalActionExecutor)
    executor._o = SimpleNamespace(_loop=loop)
    executor._pending_predictions = {}
    executor._get_goal_engine = lambda: None
    executor._persist_goal_action_receipt = lambda *args: False
    executor._broadcast = lambda *args: None
    executor._record_plan_outcome = lambda *args, **kwargs: None
    goal = SimpleNamespace(id="goal-23", topic="private goal topic")
    receipt = executor._finalize_async_action(
        goal, "web_search", False, "private search result text",
        execution_id="act_async_23", cycle_id=23,
    )

    assert receipt["success"] is False
    cycles = loop.cycle_evidence_snapshot(limit=10)["cycles"]
    origin = next(cycle for cycle in cycles if cycle["cycle_id"] == 23)
    async_stage = origin["stages"][-1]
    assert async_stage["stage"] == "goal_action_executor.web_search"
    assert async_stage["status"] == "failed"
    assert async_stage["async_completion"] is True
    assert async_stage["metrics"]["success"] is False
    assert async_stage["metrics"]["execution_ref"]
    assert "private search result text" not in repr(origin)
    assert "private goal topic" not in repr(origin)


def test_goal_broadcast_receipt_counts_only_admissions_and_reports_failures():
    class _Workspace:
        def broadcast(self, source, content, priority):
            if content == "raise":
                raise RuntimeError("listener failed")
            return content == "admitted"

    status, counts = InternalThoughtLoop._broadcast_goal_thoughts(
        _Workspace(),
        [
            {"content": "admitted", "priority": 0.7},
            {"content": "blocked", "priority": 0.6},
            {"content": "raise", "priority": 0.5},
        ],
    )

    assert status == "partial"
    assert counts == {
        "broadcast_count": 1,
        "requested_count": 3,
        "rejected_count": 1,
        "error_count": 1,
    }


def test_goal_broadcast_reports_all_rejected_without_claiming_success():
    status, counts = InternalThoughtLoop._broadcast_goal_thoughts(
        SimpleNamespace(broadcast=lambda **_kwargs: False),
        [{"content": "blocked", "priority": 0.7}],
    )

    assert status == "rejected"
    assert counts["broadcast_count"] == 0
    assert counts["rejected_count"] == 1


def test_rejected_thought_proposal_cannot_become_durable_workspace_focus():
    winner = {"type": "thought", "source_data": {"_goal_proposal": {"concept": "noise"}}}

    assert not InternalThoughtLoop._selected_proposal_commit_admitted(
        winner,
        {"created": False, "verified": False, "reason": "goal_engine_rejected"},
    )
    assert InternalThoughtLoop._selected_proposal_commit_admitted(
        winner,
        {"created": True, "verified": True},
    )
    assert InternalThoughtLoop._selected_proposal_commit_admitted(
        winner,
        {"created": False, "verified": True, "reason": "existing_goal"},
    )
    assert InternalThoughtLoop._selected_proposal_commit_admitted(
        {"type": "thought", "source_data": {}}, None,
    )


def test_proposal_admission_receipt_is_not_applicable_for_ordinary_winner():
    status, output = InternalThoughtLoop._proposal_focus_admission_evidence(
        {"type": "goal", "id": "existing-goal", "source_data": {}}, True,
    )

    assert status == "not_applicable"
    assert output == {"applicable": False}


def test_proposal_admission_receipt_reports_actual_proposal_result():
    winner = {"type": "thought", "source_data": {"_goal_proposal": {"concept": "x"}}}

    assert InternalThoughtLoop._proposal_focus_admission_evidence(winner, True) == (
        "admitted", {"applicable": True, "admitted": True},
    )
    assert InternalThoughtLoop._proposal_focus_admission_evidence(winner, False) == (
        "rejected", {"applicable": True, "admitted": False},
    )


def test_proposal_disposition_receipt_requires_every_source_thought_to_persist():
    proposal = {"origin_thought": "thought-1", "supporting_thought_ids": ["thought-1", "thought-2"]}

    result = InternalThoughtLoop._persist_proposal_disposition(
        proposal, "committed", lambda *_args, **_kwargs: 1,
        cycle=7, reason="goal_readback_verified",
    )

    assert result == {
        "status": "partial", "updated_sources": 1, "expected_sources": 2,
        "reason_code": "source_disposition_not_durable",
    }


def test_proposal_disposition_receipt_records_missing_recorder_as_failure():
    result = InternalThoughtLoop._persist_proposal_disposition(
        {"origin_thought": "thought-1"}, "satisfied", None,
        cycle=7, reason="existing_goal_verified",
    )

    assert result["status"] == "failed"
    assert result["reason_code"] == "disposition_recorder_unavailable"


def test_post_arbitration_focus_and_existing_plan_reach_shared_workspace_state():
    organism = SimpleNamespace(workspace=GlobalWorkspace())
    planner = SimpleNamespace(status=lambda: {"plans": [{
        "domain": "goal:goal-7", "status": "active",
        "objective": "Resolve the evidence gap", "next": "memory_recall",
    }]})

    state = InternalThoughtLoop._publish_global_workspace_focus(
        organism,
        {"type": "goal", "id": "goal-7", "topic": "evidence gap"},
        planner,
    )

    assert state["focus"] == "evidence gap"
    assert state["intention"] == "Resolve the evidence gap — next: memory_recall"
    assert state["updated_by"][-1]["source"] == "workspace_competition"


def test_rejected_proposal_clears_shared_workspace_focus_and_intention():
    organism = SimpleNamespace(workspace=GlobalWorkspace())
    organism.workspace.update_state("previous", focus="old focus", intention="old plan")

    state = InternalThoughtLoop._publish_global_workspace_focus(
        organism,
        {"type": "rejected_proposal", "name": "", "topic": ""},
    )

    assert state["focus"] is None
    assert state["intention"] is None


def test_phase2_recognizes_completed_tte_threads_and_retries_failed_link():
    loop = make_loop()
    calls = []
    saved = []
    thread = SimpleNamespace(
        id="thread-1",
        topic="resolved hypothesis",
        type="reflection",
        conclusion="evidence reviewed",
        status=ThoughtThreadStatus.COMPLETED,
        current_state={},
    )

    class Phase2:
        result = []

        def link_resolved_threads(self, payloads):
            calls.append(payloads)
            return self.result

    class Threads:
        def _save(self):
            saved.append(True)

    loop._phase2 = Phase2()
    loop._tte = Threads()

    assert loop._phase2_thread_is_resolved(thread)
    assert loop._link_phase2_thread(thread) is None
    assert not thread.current_state.get("identity_linked")
    assert saved == []

    loop._phase2.result = [{
        "beliefs_changed": [],
        "traits_changed": [],
        "confidence_updates": [],
        "narrative_updates": [],
    }]
    class FailingThreads:
        def _save(self):
            raise RuntimeError("persistence unavailable")

    loop._tte = FailingThreads()
    try:
        loop._link_phase2_thread(thread)
        raise AssertionError("persistence failure should propagate")
    except RuntimeError as error:
        assert str(error) == "persistence unavailable"
    assert not thread.current_state.get("identity_linked")
    assert not getattr(thread, "_identity_linked", False)

    loop._tte = Threads()
    result = loop._link_phase2_thread(thread)

    assert result is loop._phase2.result[0]
    assert thread.current_state["identity_linked"] is True
    assert loop._phase2_thread_identity_linked(thread)
    assert len(calls) == 3
    assert saved == [True]
    assert loop._link_phase2_thread(thread) is None


def test_phase2_governor_denial_receipt_explains_structured_mode_and_budget():
    loop = make_loop()
    loop._governor = SimpleNamespace(status=lambda: SimpleNamespace(
        mode="structured",
        total_pressure=0.68,
        budget_remaining=2,
        blocked_systems=["Phase2Narrative(structured_mode)"],
    ))

    metrics = loop._governor_skip_metrics("Phase2Narrative")

    assert metrics == {
        "governor_subsystem": "Phase2Narrative",
        "governor_mode": "structured",
        "governor_pressure": 0.68,
        "governor_budget_remaining": 2,
        "governor_block_reason": "structured_mode",
    }


def test_phase2_governor_skip_receipt_remains_safe_without_status_api():
    loop = make_loop()
    loop._governor = SimpleNamespace(may_run=lambda _name: False)

    assert loop._governor_skip_metrics("Phase2ThreadIdentity") == {
        "governor_subsystem": "Phase2ThreadIdentity",
    }


def test_resolved_thread_identity_linking_remains_eligible_in_structured_mode():
    governor = CognitiveGovernor()
    governor.begin_cycle(total_pressure=0.2453, goal_count=15, cycle_number=11184)

    assert governor.mode == CognitiveGovernor.MODE_STRUCTURED
    assert governor.may_run("Phase2ThreadIdentity") is True
    # Operations that can generate goals or unconstrained narrative remain gated.
    assert governor.may_run("Phase2ThoughtEval") is False
    assert governor.may_run("Phase2Narrative") is False


def test_governor_goal_count_excludes_retained_terminal_goal_records():
    goals = {
        "active": SimpleNamespace(status="active"),
        "dormant": SimpleNamespace(status="dormant"),
        "completed": SimpleNamespace(status="completed"),
        "archived": SimpleNamespace(status="archived"),
        "low_quality": SimpleNamespace(status="low_quality"),
        "abandoned": SimpleNamespace(status="abandoned"),
    }
    goal_engine = SimpleNamespace(_goals=goals)

    assert InternalThoughtLoop._governor_goal_count(goal_engine) == 2
    assert InternalThoughtLoop._governor_goal_status_counts(goal_engine) == {
        "active": 1,
        "dormant": 1,
        "completed": 1,
        "archived": 1,
        "abandoned": 1,
        "low_quality": 1,
        "other": 0,
        "total": 6,
    }
    assert InternalThoughtLoop._governor_goal_count(None) == 0


def test_low_pressure_and_four_live_goals_allow_governor_to_leave_structured_mode():
    governor = CognitiveGovernor()
    live_goal_count = InternalThoughtLoop._governor_goal_count(SimpleNamespace(
        _goals={
            "active_1": SimpleNamespace(status="active"),
            "active_2": SimpleNamespace(status="active"),
            "dormant_1": SimpleNamespace(status="dormant"),
            "dormant_2": SimpleNamespace(status="dormant"),
            "archived": SimpleNamespace(status="archived"),
            "completed": SimpleNamespace(status="completed"),
        }
    ))

    snapshot = governor.begin_cycle(
        total_pressure=0.2453,
        goal_count=live_goal_count,
        cycle_number=1,
    )
    assert governor.mode == CognitiveGovernor.MODE_EXPLORATORY
    assert governor.may_run("GoalEngine") is True
    for cycle in range(2, 4):
        snapshot = governor.begin_cycle(
            total_pressure=0.2453,
            goal_count=live_goal_count,
            cycle_number=cycle,
        )

    assert live_goal_count == 4
    assert governor.mode == CognitiveGovernor.MODE_EXPLORATORY
    assert snapshot["mode"] == CognitiveGovernor.MODE_EXPLORATORY
    assert snapshot["goal_count"] == 4
    assert snapshot["total_pressure"] == 0.2453
    assert snapshot["cycle"] == 3
    assert governor.may_run("Phase2Narrative") is True


def test_governor_initializes_exploratory_mode_immediately_when_goal_pool_is_empty():
    governor = CognitiveGovernor()

    snapshot = governor.begin_cycle(
        total_pressure=0.21596,
        goal_count=0,
        cycle_number=13426,
    )

    assert snapshot["mode"] == CognitiveGovernor.MODE_EXPLORATORY
    assert governor.may_run("GoalEngine") is True


def test_structured_hysteresis_does_not_starve_goal_engine_below_safety_ceilings():
    governor = CognitiveGovernor()

    for cycle in range(1, 41):
        governor.begin_cycle(total_pressure=0.4323, goal_count=6, cycle_number=cycle)
        assert governor.mode == CognitiveGovernor.MODE_STRUCTURED
        assert governor.block_goal_generation() is False
        assert governor.may_run("GoalEngine") is True


def test_goal_generation_has_explicit_pressure_and_goal_pool_guards():
    governor = CognitiveGovernor()
    governor.begin_cycle(total_pressure=0.60, goal_count=4, cycle_number=1)

    assert governor.block_goal_generation() is True
    assert governor.may_run("GoalEngine") is False
    assert governor.status().blocked_systems == ["GoalEngine(pressure_ceiling)"]

    governor.begin_cycle(total_pressure=0.40, goal_count=15, cycle_number=2)

    assert governor.block_goal_generation() is True
    assert governor.may_run("GoalEngine") is False
    assert governor.status().blocked_systems == ["GoalEngine(goal_pool_ceiling)"]


def test_governor_cycle_snapshot_is_auditable_without_prose_or_private_state():
    governor = CognitiveGovernor()
    snapshot = governor.begin_cycle(
        total_pressure=0.42,
        goal_count=4,
        cycle_number=12,
    )

    assert snapshot == {
        "mode": "structured",
        "total_pressure": 0.42,
        "goal_count": 4,
        "budget_total": governor.BUDGET_MED_PRESSURE,
        "budget_remaining": governor.BUDGET_MED_PRESSURE,
        "cycle": 12,
        "pressure_source": "provided",
    }
    summary = InternalThoughtLoop._evidence_summary(snapshot)
    assert summary["mode"] == "structured"
    assert summary["numeric_metrics"] == {
        "total_pressure": 0.42,
        "goal_count": 4,
        "budget_total": governor.BUDGET_MED_PRESSURE,
        "budget_remaining": governor.BUDGET_MED_PRESSURE,
        "cycle": 12,
    }


def test_governor_snapshot_includes_the_goal_state_counts_it_saw():
    governor = CognitiveGovernor()
    snapshot = governor.begin_cycle(
        total_pressure=0.2,
        goal_count=4,
        cycle_number=13,
        goal_status_counts={
            "active": 0, "dormant": 4, "completed": 2, "archived": 5,
            "abandoned": 3, "low_quality": 2, "other": 0, "total": 16,
        },
    )

    assert snapshot["goal_count"] == 4
    assert snapshot["active_goal_count"] == 0
    assert snapshot["dormant_goal_count"] == 4
    assert snapshot["completed_goal_count"] == 2
    assert snapshot["archived_goal_count"] == 5
    assert snapshot["abandoned_goal_count"] == 3
    assert snapshot["low_quality_goal_count"] == 2
    assert snapshot["other_goal_count"] == 0
    assert snapshot["goal_records_seen"] == 16
    summary = InternalThoughtLoop._evidence_summary(snapshot)
    assert summary["numeric_metrics"]["dormant_goal_count"] == 4
    assert summary["numeric_metrics"]["goal_records_seen"] == 16


def test_governor_summary_returns_policy_outcome_for_tick_audit():
    governor = CognitiveGovernor()
    governor.begin_cycle(total_pressure=0.42, goal_count=3, cycle_number=117)
    assert governor.may_run("Phase1Threads") is True
    assert governor.may_run("Phase2Narrative") is False

    summary = governor.summary_log()

    assert summary["cycle"] == 117
    assert summary["mode"] == governor.MODE_STRUCTURED
    assert summary["goal_count"] == 3
    assert summary["run_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["run_systems"] == ["Phase1Threads"]
    assert summary["blocked_systems"] == ["Phase2Narrative(structured_mode)"]


def test_governor_summary_receipt_is_visible_to_module_tick_probe():
    loop = make_loop()
    loop._module_tick_log = ModuleTickLog()
    loop._governor = CognitiveGovernor()
    loop._governor.begin_cycle(0.42, 3, 118)
    loop._refresh_module_tick_probes(only_attr="_governor")

    loop._governor.summary_log()

    module = loop.module_tick_snapshot()["cognitive_governor"]
    assert module["state"] == "output_present_unvalidated"
    assert module["method_results"]["summary_log"]["last_output"]["quality"] == "present"


def test_cycle_receipt_uses_explicit_no_action_reason_when_executor_returns_none():
    executor = SimpleNamespace(_last_tick_outcome={
        "outcome_status": "skipped",
        "reason_code": "no_eligible_goals",
    })

    assert InternalThoughtLoop._goal_action_receipt(None, executor) == {
        "outcome_status": "skipped",
        "reason_code": "no_eligible_goals",
    }
    completed = {"outcome_status": "dispatched", "execution_id": "act_ref"}
    assert InternalThoughtLoop._goal_action_receipt(completed, executor) is completed


def test_goal_action_receipt_identifies_fallback_selection_without_goal_text():
    loop = object.__new__(InternalThoughtLoop)

    evidence = loop._goal_action_selection_evidence(
        {"goal_id": "private-goal-id", "goal_topic": "private goal text"},
        decision_is_fresh=False,
    )

    assert evidence["selection_source"] == "active_goal_fallback"
    assert evidence["selected_goal_id_ref"] == loop._evidence_fingerprint("private-goal-id")
    assert "private-goal-id" not in str(evidence)
    assert "private goal text" not in str(evidence)


def test_memory_recall_candidate_reference_matches_stable_thought_id():
    thought_id = "tht_audit_memory_123"
    expected = hashlib.sha256(thought_id.encode()).hexdigest()[:20]
    competition = {
        "competition": {
            "all_candidates": [
                {
                    "type": "thought",
                    "source_data": {
                        "id": thought_id,
                        "source": "goal_action.memory_recall",
                        "content": "private retrieved text must not enter the receipt",
                    },
                },
                {
                    "type": "thought",
                    "source_data": {"id": "other", "source": "curiosity"},
                },
            ],
        },
    }

    refs = InternalThoughtLoop._memory_recall_candidate_refs(competition)
    assert refs == [expected]

    summary = InternalThoughtLoop._evidence_summary({
        "memory_recall_candidate_refs": refs + ["private topic", "f" * 21],
    })
    assert summary["memory_recall_candidate_refs"] == [expected]
    assert summary["memory_recall_candidate_count"] == 1
    assert "private retrieved text" not in str(summary)


def test_goal_proposal_receipt_preserves_hashed_source_and_candidate_lineage():
    thought_id = "tht_recalled_fact_42"
    expected = hashlib.sha256(thought_id.encode()).hexdigest()[:20]

    refs = InternalThoughtLoop._goal_proposal_origin_refs([
        {"origin_thought": thought_id, "concept": "memory integration"},
        {"origin_thought": thought_id, "concept": "duplicate source"},
        {"origin_thought": "", "concept": "unlinked"},
    ])
    assert refs == [expected]

    summary = InternalThoughtLoop._evidence_summary({
        "goal_proposal_origin_refs": refs,
        "proposal_source_thought_ref": expected,
        "persisted_source_thought_ref": expected,
        "selected_candidate_ref": "b" * 20,
        "private_topic": "never enter the receipt",
    })
    assert summary["goal_proposal_origin_refs"] == [expected]
    assert summary["goal_proposal_origin_count"] == 1
    assert summary["proposal_source_thought_ref"] == expected
    assert summary["persisted_source_thought_ref"] == expected
    assert summary["selected_candidate_ref"] == "b" * 20
    assert "private_topic" not in summary
    assert "never enter the receipt" not in str(summary)


def test_goal_tick_receipt_exposes_safe_semantic_and_candidate_counters_only():
    summary = InternalThoughtLoop._evidence_summary({
        "status": "completed",
        "topic_quality": {
            "semantic_memory": {
                "candidate_count": 4, "accepted_count": 2,
                "rejected_count": 1, "unscored_count": 1,
                "private_topics": ["do not serialize"],
            },
            "autonomous": {"candidate_count": 5, "accepted_count": 5},
            "embedding_status": "available",
            "private_topic": "do not serialize",
        },
        "candidate_generation": {
            "considered_count": 10,
            "cooldown_suppressed_count": 2,
            "live_duplicate_suppressed_count": 3,
            "user_task_suppressed_count": 1,
            "semantic_rejected_count": 2,
            "semantic_unavailable_count": 0,
            "candidate_count": 2,
            "capacity_blocked": False,
            "candidate_text": "do not serialize",
        },
    })

    assert summary["topic_quality"]["semantic_memory"] == {
        "candidate_count": 4, "accepted_count": 2,
        "rejected_count": 1, "unscored_count": 1,
    }
    assert summary["topic_quality"]["embedding_status"] == "available"
    assert summary["candidate_generation"]["live_duplicate_suppressed_count"] == 3
    assert "private_topic" not in str(summary)
    assert "candidate_text" not in str(summary)
    assert "do not serialize" not in str(summary)
