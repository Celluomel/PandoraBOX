from types import SimpleNamespace
from unittest.mock import Mock

from cognition.cognitive_organism import CognitiveOrganism


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
    )
    assert receipt["semantic_topic_learning"]["status"] == "queued"
    assert receipt["semantic_topic_learning"]["reason"] == "semantic_intent_classification"
