from types import SimpleNamespace

from cognition.cognitive_dissonance_engine import (
    CDEContext,
    CognitiveDissonanceEngine,
    DissonanceEvent,
    DissonanceEventType,
)
from cognition.narrative_arc_writer import NarrativeArcWriter
from cognition.narrative_identity import NarrativeIdentity
from cognition.thought_thread_engine import TTEContext, ThoughtThreadEngine, ThoughtThreadStatus
from cognition.thread_lifecycle_manager import ThreadLifecycleManager
from core.data.access import DataAccess
from core.data.schemas import normalize_thread


def test_tte_reads_admitted_active_goals_and_creates_one_provenance_linked_thread(tmp_path):
    goal = SimpleNamespace(
        id="goal-17",
        topic="cognitive execution evidence",
        desired_effect="Establish the evidence chain",
        priority=0.82,
        intent_kind="learn",
        success_criteria="A trace links the decision to the outcome",
        source_turn_id="turn-41",
        source_thought_id="thought-9",
    )

    class GoalEngine:
        calls = 0

        def get_active_goals(self):
            self.calls += 1
            return [goal]

    goal_engine = GoalEngine()
    organism = SimpleNamespace(ai_system=SimpleNamespace(goal_engine=goal_engine))
    context = ThoughtThreadEngine.collect_context(organism)
    assert context.world_state["goal_threads"] == [{
        "source_ref": "goal-17",
        "topic": "cognitive execution evidence",
        "goal": "Establish the evidence chain",
        "priority": 0.82,
        "intent_kind": "learn",
        "success_criteria": "A trace links the decision to the outcome",
        "source_turn_id": "turn-41",
        "source_thought_id": "thought-9",
    }]

    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    first = engine.step(context)
    second = engine.step(context)

    assert len(first) == 1
    assert len(second) == 1
    thread = second[0]
    assert thread.source == "goal_engine"
    assert thread.source_ref == "goal-17"
    assert thread.topic == "cognitive execution evidence"
    assert thread.goal == "Establish the evidence chain"
    assert thread.current_state["success_criteria"] == "A trace links the decision to the outcome"
    assert thread.current_state["source_turn_id"] == "turn-41"
    assert goal_engine.calls == 1


def test_goal_seed_upgrades_matching_unlinked_thread_without_confidence_inflation(tmp_path):
    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    context = TTEContext()
    existing = engine.spawn_thread(context, {
        "topic": "shared topic",
        "source": "curiosity",
        "current_state": {"existing": True},
    })
    confidence_before = existing.confidence

    reused = engine.spawn_thread(context, {
        "topic": "shared topic",
        "goal": "Persistent goal",
        "source": "goal_engine",
        "source_ref": "goal-88",
        "current_state": {"source_turn_id": "turn-8"},
    })

    assert reused.id == existing.id
    assert reused.source_ref == "goal-88"
    assert reused.source == "goal_engine"
    assert reused.current_state["source_turn_id"] == "turn-8"
    assert reused.confidence == confidence_before


def test_active_goal_reactivates_its_deferred_thread_and_preserves_receipts(tmp_path):
    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    context = TTEContext(energy=80.0)
    thread = engine.spawn_thread(context, {
        "topic": "knowledge integration",
        "goal": "Integrate evidence",
        "source": "goal_engine",
        "source_ref": "goal-active-1",
        "current_state": {"success_criteria": "A grounded synthesis is recorded"},
    })
    initial_confidence = thread.confidence
    engine.record_action_receipt(
        "goal-active-1", action="memory_recall", success=True,
        execution_id="execution-17", cycle_id=100,
        result="recalled one source",
    )
    thread.status = type(thread.status).DEFERRED
    context.world_state["goal_threads"] = [{
        "source_ref": "goal-active-1",
        "topic": "knowledge integration",
        "goal": "Integrate current evidence into a coherent account",
        "priority": 0.87,
        "intent_kind": "learn",
        "success_criteria": "A verified synthesis is recorded",
        "source_turn_id": "turn-22",
    }]

    active = engine.step(context)

    assert len(active) == 1
    assert active[0].id == thread.id
    assert active[0].status.value == "active"
    assert active[0].goal == "Integrate current evidence into a coherent account"
    assert active[0].current_state["success_criteria"] == "A verified synthesis is recorded"
    assert active[0].current_state["source_turn_id"] == "turn-22"
    assert active[0].current_state["action_receipt_count"] == 1
    assert active[0].current_state["last_action_receipt"]["execution_id"] == "execution-17"
    assert active[0].current_state["active_goal_reassertion"]["previous_thread_status"] == "deferred"
    assert active[0].confidence == initial_confidence


def test_cde_passes_new_meta_threads_to_dts_in_same_cycle(tmp_path):
    tte = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    tte_context = TTEContext(energy=80.0)
    event = DissonanceEvent(
        id="event-1",
        type=DissonanceEventType.PREDICTION_VS_REALITY,
        intensity=0.9,
    )
    engine = CognitiveDissonanceEngine()
    engine.detect = lambda _context: [event]

    selected_input = [SimpleNamespace(id="existing-thread")]
    output = engine.step(
        threads=selected_input,
        tte=tte,
        ctx=CDEContext(threads=selected_input),
        tte_ctx=tte_context,
    )

    assert len(output) == 2
    meta_thread = next(thread for thread in output if thread.id != "existing-thread")
    assert meta_thread.source == "dissonance"
    assert meta_thread.topic.startswith("dissonance:")
    assert engine.last_step_report["detected_event_count"] == 1
    assert engine.last_step_report["meta_threads_spawned"] == 1
    assert engine.last_step_report["event_refs"][0]["id"] == "event-1"


def test_tte_ticks_do_not_execute_actions_raise_confidence_or_complete_goal(tmp_path):
    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    context = TTEContext(energy=100.0)
    thread = engine.spawn_thread(context, {
        "topic": "verified outcome",
        "goal": "Check an outcome",
        "planned_actions": ["inspect evidence", "record result"],
    })
    initial_confidence = thread.confidence
    assert initial_confidence == 0.5  # energy is not epistemic evidence

    engine.advance_thread(thread, context)

    assert thread.confidence == initial_confidence
    assert thread.planned_actions == ["inspect evidence", "record result"]
    assert thread.status.value == "active"
    assert thread.history[-1]["planned_action"] == "inspect evidence"
    assert thread.history[-1]["action_status"] == "planned_not_executed"


def test_tte_step_batches_thread_mutations_into_one_atomic_persistence(tmp_path):
    store = tmp_path / "threads.json"
    engine = ThoughtThreadEngine(str(store))
    context = TTEContext(energy=100.0)
    threads = [
        engine.spawn_thread(context, {
            "topic": f"audit topic {index}",
            "goal": "record one scheduled tick",
            "source_ref": f"goal-{index}",
        })
        for index in range(3)
    ]

    writes = 0
    original_write = engine._write_snapshot_locked

    def count_write():
        nonlocal writes
        writes += 1
        original_write()

    engine._write_snapshot_locked = count_write
    result = engine.step(context)

    assert writes == 1
    assert {thread.id for thread in result} == {thread.id for thread in threads}
    assert all(thread.history[-1]["action_status"] == "planned_not_executed" for thread in result)
    assert not store.with_name(f"{store.name}.tmp").exists()

    restored = ThoughtThreadEngine(str(store))
    assert {thread.id for thread in restored.active_threads()} == {thread.id for thread in threads}
    assert all(thread.iteration_count == 1 for thread in restored.active_threads())


def test_thread_resolution_requires_explicit_evidence_receipt(tmp_path):
    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    context = TTEContext()
    thread = engine.spawn_thread(context, {"topic": "evidence", "goal": "verify"})

    engine.resolve_thread(thread, context)
    assert thread.status.value == "deferred"
    assert thread.current_state["resolution"] == "unverified_no_outcome_receipt"

    engine.resolve_thread(thread, context, success=True, evidence_ref="turn-8:receipt-2")
    assert thread.status.value == "completed"
    assert thread.current_state["resolution"] == "verified_success"
    assert thread.current_state["resolution_evidence_ref"] == "turn-8:receipt-2"
    assert "verified_outcome" not in thread.current_state

    engine.resolve_thread(
        thread, context, success=True, evidence_ref="turn-8:receipt-3",
        outcome_statement="The observed result met the recorded success criterion.",
        outcome_confidence=0.85,
    )
    assert thread.current_state["verified_outcome"]["evidence_ref"] == "turn-8:receipt-3"
    assert thread.current_state["verified_outcome"]["confidence"] == 0.85


def test_goal_action_receipt_updates_linked_thread_without_resolving_or_inflating_confidence(tmp_path):
    engine = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    context = TTEContext()
    thread = engine.spawn_thread(context, {
        "topic": "knowledge integration",
        "goal": "Integrate relevant evidence",
        "source": "goal_engine",
        "source_ref": "goal-22",
    })
    initial_confidence = thread.confidence

    assert engine.record_action_receipt(
        "goal-22",
        action="memory_recall",
        success=True,
        execution_id="execution-1",
        cycle_id=82,
        result="recalled one relevant source",
    ) == 1
    # Replaying the same terminal receipt is idempotent.
    assert engine.record_action_receipt(
        "goal-22",
        action="memory_recall",
        success=True,
        execution_id="execution-1",
        cycle_id=82,
        result="recalled one relevant source",
    ) == 1

    assert thread.status.value == "active"
    assert thread.confidence == initial_confidence
    assert thread.current_state["action_receipt_count"] == 1
    assert thread.current_state["last_action_receipt"]["cycle_id"] == 82
    assert thread.current_state["last_action_receipt"]["success"] is True

    restored = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    restored_thread = restored.get_thread(thread.id)
    assert restored_thread.current_state["action_receipt_count"] == 1


def test_lifecycle_manager_does_not_mint_belief_from_iteration_count_alone():
    manager = ThreadLifecycleManager.__new__(ThreadLifecycleManager)
    thread = {
        "id": "thread-44",
        "topic": "cognitive audit",
        "goal": "understand the audit",
        "iteration_count": 100,
        "history": [{"planned_action": "gather evidence"}],
        "current_state": {"resolution": "unverified_no_outcome_receipt"},
    }

    assert manager._extract_belief(thread) is None


def test_lifecycle_manager_preserves_over_budget_thread_while_goal_is_active():
    thread = {
        "id": "thread-active-goal",
        "topic": "knowledge integration",
        "goal": "Integrate current evidence",
        "source_ref": "goal-active-1",
        "status": "active",
        "iteration_count": 100,
        "history": [],
        "current_state": {"action_receipt_count": 1},
    }
    saved = []
    manager = ThreadLifecycleManager.__new__(ThreadLifecycleManager)
    manager.dal = SimpleNamespace(
        get_threads=lambda: [thread],
        save_thread=lambda value: saved.append(value.copy()) or True,
    )
    manager._repair_thought_goal_links = lambda: 0

    active_report = manager.run(active_goal_ids={"goal-active-1"})

    assert thread["status"] == "active"
    assert active_report["active_goal_threads_preserved"] == ["thread-a"]
    assert active_report["threads_retired"] == []
    assert saved == []

    closed_report = manager.run(active_goal_ids=set())
    assert thread["status"] == "retired"
    assert closed_report["unverified_threads_retired"] == ["thread-a"]


def test_lifecycle_manager_batches_thread_retirement_and_reports_persistence():
    thread = {
        "id": "thread-batch-1",
        "topic": "cognitive audit",
        "status": "active",
        "iteration_count": 100,
        "history": [],
        "current_state": {},
    }
    writes = []
    manager = ThreadLifecycleManager.__new__(ThreadLifecycleManager)
    manager.dal = SimpleNamespace(
        get_threads=lambda: [thread],
        save_threads=lambda values: writes.append([v.copy() for v in values]) or True,
    )
    manager._repair_thought_goal_links = lambda: 0

    report = manager.run(active_goal_ids=set())

    assert len(writes) == 1
    assert len(writes[0]) == 1
    assert writes[0][0]["status"] == "retired"
    assert report["threads_retired"] == ["thread-b"]
    assert report["threads_processed"] == 1
    assert report["unverified_threads_retired"] == ["thread-b"]
    assert report["thread_persistence_failed"] == []


def test_lifecycle_manager_does_not_claim_retirement_when_batch_save_fails():
    thread = {
        "id": "thread-save-fail",
        "topic": "cognitive audit",
        "status": "active",
        "iteration_count": 100,
        "history": [],
        "current_state": {},
    }
    manager = ThreadLifecycleManager.__new__(ThreadLifecycleManager)
    manager.dal = SimpleNamespace(
        get_threads=lambda: [thread],
        save_threads=lambda _values: False,
    )
    manager._repair_thought_goal_links = lambda: 0

    report = manager.run(active_goal_ids=set())

    assert report["threads_retired"] == []
    assert report["threads_processed"] == 0
    assert report["thread_persistence_failed"] == ["thread-s"]


def test_data_access_saves_multiple_beliefs_with_one_identity_write(tmp_path, monkeypatch):
    manager = DataAccess(str(tmp_path))
    snapshots = []
    monkeypatch.setattr(manager, "_load", lambda _name, default=None: {"beliefs": {}})
    monkeypatch.setattr(
        manager,
        "_save",
        lambda filename, payload: snapshots.append((filename, payload.copy())) or True,
    )

    assert manager.save_beliefs([
        {"name": "thread_learning_a", "value": 1.0, "confidence": 0.8},
        {"name": "thread_learning_b", "value": 0.0, "confidence": 0.7},
    ]) is True

    assert len(snapshots) == 1
    assert snapshots[0][0] == "identity.json"
    assert set(snapshots[0][1]["beliefs"]) == {
        "thread_learning_a", "thread_learning_b",
    }


def test_thread_schema_keeps_goal_link_and_tte_lifecycle_fields():
    raw = {
        "id": "thread-schema",
        "topic": "knowledge integration",
        "status": "active",
        "source": "goal_engine",
        "source_ref": "goal-schema-1",
        "last_advanced": 1234.5,
        "current_state": {"success_criteria": "verified synthesis"},
        "iteration_count": 27,
        "custom_future_field": {"preserve": True},
    }

    normalized = normalize_thread(raw)

    assert normalized["source_ref"] == "goal-schema-1"
    assert normalized["source"] == "goal_engine"
    assert normalized["last_advanced"] == 1234.5
    assert normalized["current_state"] == raw["current_state"]
    assert normalized["iteration_count"] == 27
    assert normalized["custom_future_field"] == {"preserve": True}


def test_lifecycle_manager_requires_verified_outcome_statement_and_reference():
    manager = ThreadLifecycleManager.__new__(ThreadLifecycleManager)
    thread = {
        "id": "thread-45",
        "topic": "cognitive audit",
        "iteration_count": 2,
        "current_state": {
            "verified_outcome": {
                "status": "success",
                "belief_statement": "The receipt links the selected goal to its observed result.",
                "evidence_ref": "cycle-45:stage-7",
                "confidence": 0.8,
            },
        },
    }

    belief = manager._extract_belief(thread)
    assert belief["statement"] == "The receipt links the selected goal to its observed result."
    assert belief["evidence_ref"] == "cycle-45:stage-7"
    assert belief["confidence"] == 0.8
    assert belief["value"] == 1.0


def test_goal_action_receipt_arriving_before_thread_seed_is_persisted_and_relinked(tmp_path):
    store = tmp_path / "thought_threads.json"
    engine = ThoughtThreadEngine(str(store))

    assert engine.record_action_receipt(
        "goal-before-seed",
        action="memory_recall",
        success=True,
        execution_id="exec-before-seed",
        cycle_id=41,
        result="recalled one source",
        evidence_ref="execution:exec-before-seed",
    ) == 0
    assert (tmp_path / "thought_threads_action_receipts.json").exists()

    restored = ThoughtThreadEngine(str(store))
    thread = restored.spawn_thread(TTEContext(), {
        "topic": "knowledge integration",
        "goal": "integrate evidence",
        "source": "goal_engine",
        "source_ref": "goal-before-seed",
    })

    receipts = thread.current_state["action_receipts"]
    assert len(receipts) == 1
    assert receipts[0]["execution_id"] == "exec-before-seed"
    assert receipts[0]["cycle_id"] == 41
    assert thread.current_state["last_action_receipt"] == receipts[0]


def test_narrative_writer_only_receives_unseen_terminal_threads():
    writer = NarrativeArcWriter()
    active = SimpleNamespace(id="active", status=ThoughtThreadStatus.ACTIVE)
    completed = SimpleNamespace(id="done", status=ThoughtThreadStatus.COMPLETED)
    failed = SimpleNamespace(id="failed", status=ThoughtThreadStatus.FAILED)
    deferred = SimpleNamespace(id="deferred", status=ThoughtThreadStatus.DEFERRED)
    writer._seen_thread_ids.add("failed")

    assert writer.pending_thread_resolutions([active, completed, failed, deferred]) == [completed]


def test_narrative_writer_retries_terminal_thread_after_persistence_failure():
    writer = NarrativeArcWriter()
    thread = SimpleNamespace(
        id="retryable", status=ThoughtThreadStatus.COMPLETED,
        topic="causal reasoning", goal="link evidence to outcome",
        confidence=0.8, history=[{}], source="test", age_hours=lambda: 1.0,
    )
    attempts = []

    def record_chapter(**chapter):
        attempts.append(chapter)
        return len(attempts) > 1

    narrative = SimpleNamespace(record_chapter=record_chapter)
    assert writer.watch_thread_resolution(thread, narrative) is False
    assert "retryable" not in writer._seen_thread_ids
    assert writer.pending_thread_resolutions([thread]) == [thread]
    assert writer.watch_thread_resolution(thread, narrative) is True
    assert "retryable" in writer._seen_thread_ids
    assert len(attempts) == 2
    assert all(item["scope"] == "global_internal" for item in attempts)


def test_narrative_arc_uses_internal_chapters_written_by_its_own_events(tmp_path):
    identity = NarrativeIdentity(SimpleNamespace(), path=str(tmp_path / "identity.json"))
    writer = NarrativeArcWriter()

    for index, topic in enumerate((
        "cognitive memory reasoning",
        "cognitive identity reasoning",
        "cognitive planning reasoning",
    )):
        thread = SimpleNamespace(
            id=f"internal-{index}", status=ThoughtThreadStatus.COMPLETED,
            topic=topic, goal=f"understand {topic}", confidence=0.8,
            history=[{}, {}], source="internal", age_hours=lambda: 0.1,
        )
        assert writer.watch_thread_resolution(thread, identity) is True

    assert len(identity.global_chapters()) == 3
    arc = writer.synthesise_arc(identity)
    assert arc
    assert "cognitive" in arc
    assert identity._current_arc == arc


def test_narrative_writer_retries_cde_chapter_after_persistence_failure():
    writer = NarrativeArcWriter()
    event = SimpleNamespace(
        id="cde-retry", resolved=True, intensity=0.8,
        type=DissonanceEventType.BELIEF_VS_EVIDENCE,
        belief_ref="belief", evidence_ref="observed evidence",
        action_ref="prior action", self_question="what changed?", hypotheses=[],
    )
    attempts = []

    def record_chapter(**chapter):
        attempts.append(chapter)
        return len(attempts) > 1

    identity = SimpleNamespace(record_chapter=record_chapter)
    assert writer.watch_cde_resolution(event, identity) is False
    assert event.id not in writer._seen_cde_ids
    assert writer.watch_cde_resolution(event, identity) is True
    assert event.id in writer._seen_cde_ids
    assert all(item["scope"] == "global_internal" for item in attempts)
