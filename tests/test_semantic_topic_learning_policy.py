from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.cognitive_organism import CognitiveOrganism
from cognition.persona_bridge import (
    _resolve_semantic_extractor_llm_fn,
    _semantic_turn_kind_for_route,
)
from cognition.semantic_extractor import SemanticExtractor


def _organism_stub():
    organism = Mock()
    organism._loop = SimpleNamespace(
        _world_self_dynamics=None,
        _resource_economy=None,
        _consequence_model=None,
        _auto_experiment=None,
    )
    organism.energy.mode.return_value = "normal"
    organism.energy.level.return_value = 0.7
    organism.ai_system.emotional_state.overall_arousal = 0.3
    organism.meta_cognition.post_response_eval.return_value = None
    organism.homeostasis.last_report.return_value = None
    organism.workspace = object()
    organism._semantic_extractor = Mock()
    return organism


def test_semantic_extractor_prefers_external_history_free_llm():
    configured = lambda prompt: f"configured:{prompt}"
    fallback = lambda prompt: f"fallback:{prompt}"

    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(_simple_llm_fn=configured), fallback,
    ) is fallback
    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(), fallback,
    ) is fallback
    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(_simple_llm_fn=configured), None,
    ) is configured
    assert _resolve_semantic_extractor_llm_fn(SimpleNamespace(), None) is None


def test_semantic_learning_marks_provider_contention_for_queue_retry():
    class Manager:
        def __init__(self):
            self.calls = 0

        def generate_bare(self, prompt):
            return "legacy path must not run"

        def generate_bare_result(self, prompt, **kwargs):
            self.calls += 1
            assert kwargs["_audit_origin"] == "cognition.semantic_extractor._parse"
            if self.calls == 1:
                return {
                    "status": "deferred",
                    "reason": "interactive turn active",
                    "provider_call_count": 0,
                }
            return {"status": "ok", "text": '{"turn_kind":"topic"}'}

    manager = Manager()
    learning_fn = _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(), manager.generate_bare,
    )

    try:
        learning_fn("extract from completed exchange")
    except RuntimeError as exc:
        assert getattr(exc, "semantic_learning_deferred", False) is True
    else:
        raise AssertionError("provider contention was not returned to the semantic queue")
    assert manager.calls == 1
    manager.calls = 0
    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=learning_fn)
    try:
        extractor._parse("A durable concept from this message", "answer")
    except RuntimeError as exc:
        assert getattr(exc, "semantic_learning_deferred", False) is True
    else:
        raise AssertionError("provider deferral incorrectly fell back to lexical extraction")
    manager.calls = 0
    receipt = extractor._extract(
        "A durable concept from this message", "answer", None, None,
        "user_topic", "turn-deferred", None, "topic",
    )
    assert receipt["status"] == "deferred"
    assert receipt["learning_status"] == "deferred_provider_busy"


def test_deferred_semantic_turn_yields_worker_to_next_queued_turn():
    class ImmediateTimer:
        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False

        def start(self):
            self.callback()

    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=None)
    finished = []

    def callback_for(turn):
        return lambda receipt: finished.append((turn, receipt["status"]))

    extractor._extract = Mock(side_effect=[
        {"status": "deferred", "learning_status": "deferred_provider_busy"},
        {"status": "completed", "learning_status": "accepted_topic_turn"},
        {"status": "completed", "learning_status": "accepted_decision_turn"},
    ])
    extractor._queue.put(("first", "answer", None, None, "user_topic", "turn-1", callback_for("turn-1"), "topic", 0))
    extractor._queue.put(("second", "answer", None, None, "user_topic", "turn-2", callback_for("turn-2"), "decision", 0))
    extractor._worker_running = True

    with patch("cognition.semantic_extractor.threading.Timer", ImmediateTimer):
        extractor._drain_queue()

    assert extractor._extract.call_args_list[1].args[0] == "second"
    assert extractor._extract.call_args_list[2].args[0] == "first"
    assert finished == [("turn-2", "completed"), ("turn-1", "completed")]
    assert extractor._queue.unfinished_tasks == 0


def test_deferred_semantic_turn_exhaustion_is_reported_and_worker_continues():
    class ImmediateTimer:
        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False

        def start(self):
            self.callback()

    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=None)
    finished = []
    extractor._extract = Mock(return_value={
        "status": "deferred", "learning_status": "deferred_provider_busy",
    })
    item = ("user", "answer", None, None, "user_topic", "turn-1", finished.append, "topic", 0)
    extractor._queue.put(item)
    extractor._worker_running = True

    with patch("cognition.semantic_extractor._MAX_DEFERRED_RETRIES", 1), \
         patch("cognition.semantic_extractor.threading.Timer", ImmediateTimer):
        extractor._drain_queue()

    assert extractor._extract.call_count == 2
    assert finished == [{
        "status": "failed",
        "learning_status": "deferred_retry_exhausted",
        "retry_exhausted": True,
    }]
    assert extractor._queue.unfinished_tasks == 0


def test_source_recall_is_classified_by_semantic_extractor_not_a_lexical_gate():
    organism = _organism_stub()

    receipt = CognitiveOrganism._post_interaction(
        organism,
        user_input=(
            "Rappelle uniquement la consigne que je t’ai donnée : "
            "poursuivre l’audit sans redémarrer Lumina après chaque correctif."
        ),
        response="Je ne trouve pas de source suffisamment précise.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="recall-control-turn",
    )

    organism._semantic_extractor.extract_async.assert_called_once()
    assert receipt["semantic_topic_learning"] == {
        "status": "queued",
        "turn_id": "recall-control-turn",
        "reason": "semantic_intent_classification",
    }


def test_ordinary_topic_turn_still_queues_semantic_learning():
    organism = _organism_stub()

    receipt = CognitiveOrganism._post_interaction(
        organism,
        user_input="Explain how memory retrieval supports the cognitive audit.",
        response="Retrieval supplies prior episodes for the current turn.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="ordinary-topic-turn",
    )

    organism._semantic_extractor.extract_async.assert_called_once_with(
        user_input="Explain how memory retrieval supports the cognitive audit.",
        response="Retrieval supplies prior episodes for the current turn.",
        workspace=organism.workspace,
        observation_role="user_topic",
        turn_id="ordinary-topic-turn",
        completion_callback=None,
        turn_kind_hint="",
    )
    assert receipt["semantic_topic_learning"]["status"] == "queued"
    assert receipt["semantic_topic_learning"]["reason"] == "semantic_intent_classification"


def test_upstream_turn_kind_is_forwarded_without_disabling_topic_learning():
    organism = _organism_stub()

    with patch(
        "cognition.profile_flow.update_behavioral_user_profile",
        return_value={"status": "updated", "changed": True, "persisted": True},
    ) as update_profile:
        receipt = CognitiveOrganism._post_interaction(
            organism,
            user_input="How are you?",
            response="I am doing well.",
            cycle_data={"emo_values": {}},
            decision=None,
            turn_id="deterministic-social-turn",
            semantic_turn_kind_hint="social",
        )

    organism._semantic_extractor.extract_async.assert_called_once_with(
        user_input="How are you?",
        response="I am doing well.",
        workspace=organism.workspace,
        observation_role="user_topic",
        turn_id="deterministic-social-turn",
        completion_callback=None,
        turn_kind_hint="social",
    )
    assert receipt["semantic_topic_learning"]["status"] == "queued"
    update_profile.assert_called_once()
    assert update_profile.call_args.kwargs["learn_semantic_profile"] is False


def test_closed_world_report_route_is_forwarded_as_non_topic_learning_act():
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=True,
    ) == "other"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=True,
        deterministic_affect_report=False,
        closed_world_report=True,
    ) == "retrieval"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=True,
        closed_world_report=True,
    ) == "social"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        goal_means_decision=True,
    ) == "decision"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
    ) == ""
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        explicit_profile_learning_opt_out=True,
    ) == "instruction"
