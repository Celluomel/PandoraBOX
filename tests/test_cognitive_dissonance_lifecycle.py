from types import SimpleNamespace
from datetime import datetime
import json
import time

from cognition.cognitive_dissonance_engine import (
    CDEContext,
    CognitiveDissonanceEngine,
    DissonanceEvent,
    DissonanceEventType,
)


def _event(*, intensity=0.5, event_id="event-a"):
    return DissonanceEvent(
        id=event_id,
        type=DissonanceEventType.IDENTITY_VS_ACTION,
        belief_ref="curious",
        action_ref="no exploration action taken",
        intensity=intensity,
    )


def test_low_intensity_event_is_deferred_not_resolved_or_learned():
    engine = CognitiveDissonanceEngine()
    event = _event(intensity=0.2)
    engine._detect_identity_vs_action = lambda _ctx: [event]
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []

    queued = []
    organism = SimpleNamespace(ai_system=SimpleNamespace(
        personality_evolution=SimpleNamespace(
            queue_experience=lambda *args, **kwargs: queued.append((args, kwargs))
        )
    ))
    tte = SimpleNamespace(spawn_thread=lambda _ctx, payload: SimpleNamespace(
        id="meta-1", topic=payload["topic"], source="dissonance"
    ))

    engine.step([SimpleNamespace(id="thread-1")], tte, CDEContext(), None, organism)

    assert event.resolved is False
    assert event.resolution_status == "deferred_low_intensity"
    assert queued == []
    assert engine.last_step_report["auto_resolved_event_count"] == 0
    assert engine.last_step_report["deferred_low_intensity_count"] == 1


def test_repeated_detection_reuses_pending_event_and_escalation_reactivates_it():
    engine = CognitiveDissonanceEngine()
    next_event = [_event(intensity=0.2, event_id="first")]

    def detect_identity(_ctx):
        return [next_event[0]]

    engine._detect_identity_vs_action = detect_identity
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []

    first = engine.detect(CDEContext())
    assert len(first) == 1
    first[0].resolution_status = "deferred_low_intensity"

    next_event[0] = _event(intensity=0.3, event_id="second")
    assert engine.detect(CDEContext()) == []
    assert first[0].observation_count == 2
    assert first[0].resolved is False

    next_event[0] = _event(intensity=0.8, event_id="third")
    reactivated = engine.detect(CDEContext())
    assert reactivated == [first[0]]
    assert first[0].observation_count == 3
    assert first[0].resolution_status == "pending"
    assert first[0].intensity == 0.8


def test_cde_event_id_and_resolution_state_survive_restart(tmp_path):
    store = tmp_path / "cde-events.json"
    engine = CognitiveDissonanceEngine(str(store))
    event = _event(intensity=0.8, event_id="stable-event-id")
    engine._events.append(event)
    engine._detect_identity_vs_action = lambda _ctx: []
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []
    thread = SimpleNamespace(source="dissonance", current_state={
        "cde_event_id": event.id,
        "verified_outcome": {
            "status": "success",
            "evidence_ref": "observation:later-action-7",
            "belief_statement": "A later matching action receipt counters the specific absence observation.",
            "confidence": 0.75,
        },
    })
    tte = SimpleNamespace(
        all_threads=lambda: [thread],
        resolve_thread=lambda _thread, _ctx, **kwargs: SimpleNamespace(
            status=SimpleNamespace(value="completed"), **kwargs,
        ),
        spawn_thread=lambda *_args: None,
    )

    engine.step([], tte, CDEContext(), SimpleNamespace())

    persisted = json.loads(store.read_text(encoding="utf-8"))
    assert persisted["schema"] == "lumina_cde_events.v1"
    assert persisted["events"][0]["id"] == event.id
    assert persisted["events"][0]["resolved"] is True
    assert engine.last_step_report["event_store_status"] == "persisted"
    assert engine.last_step_report["event_store_event_count"] == 1

    restored = CognitiveDissonanceEngine(str(store))
    restored_event = restored._events[0]
    assert restored_event.id == event.id
    assert restored_event.resolved is True
    assert restored_event.resolution_evidence_ref == "observation:later-action-7"


def test_cde_persistence_failure_is_reported_without_claiming_durability(tmp_path):
    blocked_path = tmp_path / "blocked.json"
    blocked_path.mkdir()
    engine = CognitiveDissonanceEngine(str(tmp_path / "working.json"))
    engine._path = blocked_path
    event = _event(event_id="not-durable")
    engine._events.append(event)
    engine._detect_identity_vs_action = lambda _ctx: []
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []
    engine.step([], SimpleNamespace(all_threads=lambda: []), CDEContext(), SimpleNamespace())

    assert engine.last_step_report["event_store_status"].startswith("persistence_failed:")
    assert event.resolved is False


def test_cde_retains_open_event_links_beyond_resolved_history_limit(tmp_path):
    store = tmp_path / "cde-events.json"
    engine = CognitiveDissonanceEngine(str(store))
    open_event = _event(event_id="open-event")
    open_event.created_at = 1.0
    engine._events.append(open_event)
    engine._events.extend(
        _event(event_id=f"resolved-{index}")
        for index in range(25)
    )
    for event in engine._events[1:]:
        event.resolved = True

    assert engine._save_events() is True

    restored = CognitiveDissonanceEngine(str(store))
    retained_ids = {event.id for event in restored._events}
    assert "open-event" in retained_ids
    assert "resolved-0" not in retained_ids
    assert len(retained_ids) == 21  # 1 pending + most recent 20 resolved


def test_detection_does_not_evict_unresolved_events_referenced_by_meta_threads():
    engine = CognitiveDissonanceEngine()
    referenced = _event(event_id="referenced-pending-event")
    engine._events.append(referenced)
    def create_new_events(_ctx):
        events = []
        for index in range(25):
            event = _event(event_id=f"new-{index}")
            event.belief_ref = f"belief-{index}"
            events.append(event)
        return events

    engine._detect_identity_vs_action = create_new_events
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []

    engine.detect(CDEContext())

    retained_ids = {event.id for event in engine._events}
    assert referenced.id in retained_ids
    assert len(retained_ids) == 26


def test_cde_does_not_overwrite_an_unreadable_existing_journal(tmp_path):
    store = tmp_path / "cde-events.json"
    original = b"{not valid json"
    store.write_bytes(original)
    engine = CognitiveDissonanceEngine(str(store))
    engine._events.append(_event(event_id="must-not-replace-corrupt-history"))
    engine._detect_identity_vs_action = lambda _ctx: []
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []

    engine.step([], SimpleNamespace(all_threads=lambda: []), CDEContext(), SimpleNamespace())

    assert engine.last_step_report["event_store_status"] == "load_failed_preserved"
    assert store.read_bytes() == original


def test_prediction_detector_does_not_treat_heuristic_confidence_as_realized_outcome():
    engine = CognitiveDissonanceEngine()
    result = SimpleNamespace(
        prediction=SimpleNamespace(expected_intent="factual", confidence=0.95),
        actual_intent="social",
        error_level=0.8,
    )
    ctx = CDEContext(predictive_mind=SimpleNamespace(_results=[result]))

    assert engine._detect_prediction_vs_reality(ctx) == []
    assert engine._prediction_detector_status == "unavailable_no_independent_same_domain_outcomes"


def test_prediction_detector_requires_and_preserves_independent_same_domain_evidence():
    engine = CognitiveDissonanceEngine()
    result = SimpleNamespace(
        prediction=SimpleNamespace(expected_intent="factual", confidence=0.95),
        actual_intent="social",
        error_level=0.8,
        evidence_status="independently_validated",
        evidence_ref="annotator:turn-51:label-2",
        outcome_scope="intent",
    )
    ctx = CDEContext(predictive_mind=SimpleNamespace(_results=[result]))

    events = engine._detect_prediction_vs_reality(ctx)

    assert len(events) == 1
    assert events[0].evidence_ref == "annotator:turn-51:label-2"
    assert events[0].predicted["intent"] == "factual"
    assert events[0].actual["intent"] == "social"
    assert engine._prediction_detector_status == "validated_same_domain_outcome_checked"


def test_resolution_requires_verified_outcome_receipt_before_personality_update():
    engine = CognitiveDissonanceEngine()
    event = _event(intensity=0.8)
    queued = []
    organism = SimpleNamespace(ai_system=SimpleNamespace(
        personality_evolution=SimpleNamespace(
            queue_experience=lambda *args, **kwargs: queued.append((args, kwargs))
        )
    ))

    engine.resolve([event], CDEContext(), organism)
    assert event.resolved is False
    assert event.resolution_status == "unverified_no_resolution_receipt"
    assert queued == []

    unlinked = SimpleNamespace(source="dissonance", current_state={
        "cde_event_id": "different-event",
        "verified_outcome": {
            "status": "success",
            "evidence_ref": "turn-12:outcome-3",
            "belief_statement": "The expected action was observed in the following turn.",
            "confidence": 0.9,
        },
    })
    engine.resolve([event], CDEContext(), organism, outcome_threads=[unlinked])
    assert event.resolved is False
    assert queued == []

    linked = SimpleNamespace(source="dissonance", current_state={
        "cde_event_id": event.id,
        "verified_outcome": {
            "status": "success",
            "evidence_ref": "turn-12:outcome-3",
            "belief_statement": "The expected action was observed in the following turn.",
            "confidence": 0.9,
        },
    })
    engine.resolve([event], CDEContext(), organism, outcome_threads=[linked])

    assert event.resolved is True
    assert event.resolution_status == "verified_resolved"
    assert event.resolution_evidence_ref == "turn-12:outcome-3"
    assert len(queued) == 2  # primary dissonance plus identity-specific update


def test_step_consumes_only_successful_tte_outcome_linked_to_event():
    engine = CognitiveDissonanceEngine()
    event = _event(intensity=0.8)
    engine._events.append(event)
    engine._detect_identity_vs_action = lambda _ctx: []
    engine._detect_goal_vs_outcome = lambda _ctx: []
    engine._detect_belief_vs_evidence = lambda _ctx: []
    engine._detect_prediction_vs_reality = lambda _ctx: []
    outcome_thread = SimpleNamespace(source="dissonance", current_state={
        "cde_event_id": event.id,
        "verified_outcome": {
            "status": "success",
            "evidence_ref": "cycle-9:outcome-2",
            "belief_statement": "The inquiry established the cause.",
            "confidence": 0.85,
        },
    })
    tte = SimpleNamespace(all_threads=lambda: [outcome_thread], spawn_thread=lambda *_: None)

    engine.step([], tte, CDEContext(), None)

    assert event.resolved is True
    assert event.resolution_status == "verified_resolved"
    assert event.resolution_evidence_ref == "cycle-9:outcome-2"


def test_verified_cde_outcome_also_completes_its_tte_inquiry_thread(tmp_path):
    from cognition.thought_thread_engine import (
        ThoughtThread,
        ThoughtThreadEngine,
        ThoughtThreadStatus,
        TTEContext,
    )

    event = _event(intensity=0.8)
    thread = ThoughtThread(
        id="inquiry-17",
        topic="dissonance inquiry",
        goal="investigate the recorded mismatch",
        source="dissonance",
        current_state={
            "cde_event_id": event.id,
            "verified_outcome": {
                "status": "success",
                "evidence_ref": "cycle-22:verified-outcome",
                "belief_statement": "The expected cause was checked against the recorded evidence.",
                "confidence": 0.88,
            },
        },
    )
    tte = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    tte._threads[thread.id] = thread
    engine = CognitiveDissonanceEngine()
    engine.resolve(
        [event], CDEContext(), outcome_threads=[thread],
        tte=tte, tte_ctx=TTEContext(),
    )

    assert event.resolved is True
    assert event.resolution_status == "verified_resolved"
    assert thread.status is ThoughtThreadStatus.COMPLETED
    assert thread.current_state["resolution_evidence_ref"] == "cycle-22:verified-outcome"
    assert thread.current_state["verified_outcome"]["confidence"] == 0.88


def test_identity_action_detector_consumes_typed_action_receipts():
    engine = CognitiveDissonanceEngine()
    context = CDEContext(
        beliefs=["I am curious", "I am expressive"],
        action_receipts=[
            {"action": "web_search", "success": True},
            {"action": "user_question", "success": True},
        ],
    )

    assert engine._detect_identity_vs_action(context) == []


def test_identity_action_detector_does_not_treat_failed_action_as_behavior():
    engine = CognitiveDissonanceEngine()
    context = CDEContext(
        beliefs=["I am curious"],
        action_receipts=[{"action": "web_search", "success": False}],
    )

    events = engine._detect_identity_vs_action(context)

    assert len(events) == 1
    assert events[0].action_ref == "no exploration action taken"


def test_identity_action_detector_does_not_count_internal_question_as_expression():
    engine = CognitiveDissonanceEngine()
    context = CDEContext(
        beliefs=["I am expressive"],
        action_receipts=[{"action": "self_question", "success": True}],
    )

    events = engine._detect_identity_vs_action(context)

    assert len(events) == 1
    assert events[0].action_ref == "no expression action taken"


def test_later_successful_exploration_receipt_closes_only_its_linked_incident(tmp_path):
    from cognition.thought_thread_engine import (
        ThoughtThread, ThoughtThreadEngine, ThoughtThreadStatus, TTEContext,
    )

    event = _event(intensity=0.8, event_id="event-curiosity")
    event.created_at = time.time() - 10
    thread = ThoughtThread(
        id="inquiry-curiosity", topic="dissonance:curiosity",
        goal="Check whether exploration resumed", source="dissonance",
        current_state={"cde_event_id": event.id},
    )
    tte = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    tte._threads[thread.id] = thread
    engine = CognitiveDissonanceEngine()
    engine._events.append(event)
    receipt = {
        "event_id": "ledger-outcome-42",
        "timestamp": datetime.fromtimestamp(event.created_at + 2).isoformat(),
        "action": "web_search",
        "success": True,
    }

    engine.step([], tte, CDEContext(action_receipts=[receipt]), TTEContext())

    assert event.resolved is True
    assert event.resolution_status == "verified_resolved"
    assert event.resolution_evidence_ref == "consequence:ledger-outcome-42"
    assert thread.status is ThoughtThreadStatus.COMPLETED
    outcome = thread.current_state["verified_outcome"]
    assert "does not establish a stable personality trait" in outcome["belief_statement"]
    assert engine.last_step_report["verified_action_counterevidence_count"] == 1


def test_tte_goal_action_receipt_reaches_cde_and_closes_later_matching_event(tmp_path):
    from cognition.thought_thread_engine import (
        ThoughtThread, ThoughtThreadEngine, ThoughtThreadStatus, TTEContext,
    )

    event = _event(intensity=0.8, event_id="event-goal-action")
    event.created_at = time.time() - 10
    thread = ThoughtThread(
        id="inquiry-goal-action", topic="dissonance:goal-action",
        goal="Check whether exploration resumed", source="dissonance",
        current_state={
            "cde_event_id": event.id,
            "action_receipts": [{
                "execution_id": "exec-goal-action-1",
                "cycle_id": 44,
                "action": "web_search",
                "success": True,
                "evidence_ref": "execution:exec-goal-action-1",
                "recorded_at": event.created_at + 2,
            }],
        },
    )
    tte = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    tte._threads[thread.id] = thread
    engine = CognitiveDissonanceEngine()
    engine._events.append(event)

    engine.step([], tte, CDEContext(), TTEContext())

    assert event.resolved is True
    assert event.resolution_status == "verified_resolved"
    assert event.resolution_evidence_ref == "goal_action:execution:exec-goal-action-1"
    assert thread.status is ThoughtThreadStatus.COMPLETED
    assert engine.last_step_report["goal_action_receipt_count"] == 1
    assert engine.last_step_report["verified_action_counterevidence_count"] == 1


def test_cde_step_report_separates_new_resolution_from_resolved_history():
    engine = CognitiveDissonanceEngine()
    historical = _event(intensity=0.8, event_id="historical-resolution")
    historical.resolved = True
    historical.resolution_status = "verified_resolved"
    historical.resolution_evidence_ref = "prior:verified-evidence"
    engine._events.append(historical)

    engine.step([], SimpleNamespace(all_threads=lambda: []), CDEContext(), None)

    assert engine.last_step_report["verified_resolved_event_count"] == 0
    assert engine.last_step_report["resolved_event_history_count"] == 1


def test_action_counterevidence_requires_later_success_and_matching_event_thread(tmp_path):
    from cognition.thought_thread_engine import (
        ThoughtThread, ThoughtThreadEngine, ThoughtThreadStatus, TTEContext,
    )

    event = _event(intensity=0.8, event_id="event-curiosity")
    event.created_at = time.time() - 10
    thread = ThoughtThread(
        id="inquiry-curiosity", topic="dissonance:curiosity",
        goal="Check whether exploration resumed", source="dissonance",
        current_state={"cde_event_id": "different-event"},
    )
    tte = ThoughtThreadEngine(str(tmp_path / "threads.json"))
    tte._threads[thread.id] = thread
    engine = CognitiveDissonanceEngine()
    engine._events.append(event)
    receipts = [
        {"event_id": "past", "timestamp": datetime.fromtimestamp(event.created_at - 2).isoformat(),
         "action": "web_search", "success": True},
        {"event_id": "failed", "timestamp": datetime.fromtimestamp(event.created_at + 2).isoformat(),
         "action": "web_search", "success": False},
    ]

    engine.step([], tte, CDEContext(action_receipts=receipts), TTEContext())

    assert event.resolved is False
    assert thread.status is not ThoughtThreadStatus.COMPLETED
    assert engine.last_step_report["verified_action_counterevidence_count"] == 0
