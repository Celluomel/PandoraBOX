from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.cognitive_organism import CognitiveOrganism
from cognition.persona_bridge import (
    _resolve_semantic_extractor_llm_fn,
    _semantic_turn_kind_for_route,
)


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
    ) == ""
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        explicit_profile_learning_opt_out=True,
    ) == "instruction"
