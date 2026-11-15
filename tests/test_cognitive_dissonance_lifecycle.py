from types import SimpleNamespace

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
