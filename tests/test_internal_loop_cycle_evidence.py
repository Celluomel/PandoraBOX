from collections import deque
import threading
from types import SimpleNamespace

from core.module_tick_log import ModuleTickLog
from core.internal_loop import InternalThoughtLoop, _executive_arbitration_skip_reason
from cognition.global_workspace import GlobalWorkspace
from cognition.thought_thread_engine import ThoughtThreadStatus


def make_loop():
    loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
    loop._cycle_evidence_lock = threading.RLock()
    loop._cycle_evidence = deque(maxlen=40)
    loop._active_cycle_evidence = None
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


def test_module_probe_records_hashed_inputs_and_marks_side_effect_only_output():
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
    assert stage["output_summary"] == {"kind": "none", "quality": "side_effect_only"}
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
    loop._governor = SimpleNamespace(may_run=lambda _name: False)
    loop._begin_cycle_evidence(20)

    assert not loop._periodic_module_due(
        "_goal_quality_filter", "goal_quality_filter", 20, "GQF",
    )

    stage = loop.cycle_evidence_snapshot()["cycles"][0]["stages"][0]
    assert stage["status"] == "skipped_governor"
    assert stage["metrics"] == {"cycle": 20, "interval_cycles": 20}
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

    metrics = loop._phase2_governor_skip_metrics("Phase2Narrative")

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

    assert loop._phase2_governor_skip_metrics("Phase2ThreadIdentity") == {
        "governor_subsystem": "Phase2ThreadIdentity",
    }


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
