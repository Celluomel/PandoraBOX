from types import SimpleNamespace
from unittest.mock import Mock

from cognition.cognitive_organism import CognitiveOrganism
from cognition.narrative_identity import NarrativeIdentity
from cognition.predictive_mind import PredictiveMind


def test_global_predictive_metrics_ignore_user_profile_order_and_values():
    profiles_a = {
        "alice": SimpleNamespace(
            interaction_count=20, _recent_new_topics=20, _topic_quality=0.1
        ),
        "bob": SimpleNamespace(
            interaction_count=20, _recent_new_topics=0, _topic_quality=0.95
        ),
    }
    profiles_b = dict(reversed(list(profiles_a.items())))

    first = PredictiveMind(SimpleNamespace(world_model=SimpleNamespace(user_profiles=profiles_a)))
    second = PredictiveMind(SimpleNamespace(world_model=SimpleNamespace(user_profiles=profiles_b)))
    first._total_predictions = second._total_predictions = 10

    metrics_a = first.stability_metrics()
    metrics_b = second.stability_metrics()

    assert metrics_a == metrics_b
    assert metrics_a["novelty_rate"] == 0.15
    assert metrics_a["topic_quality"] is None
    assert metrics_a["topic_quality_status"] == "unavailable_global_metric_not_defined"


def test_narrative_identity_does_not_turn_user_profile_stats_into_global_milestones(tmp_path):
    profiles = {
        "first": SimpleNamespace(
            topic_entries={str(i): object() for i in range(300)},
            relational=SimpleNamespace(bond_strength=0.99),
        ),
        "second": SimpleNamespace(
            topic_entries={}, relational=SimpleNamespace(bond_strength=0.0)
        ),
    }
    organism = SimpleNamespace(world_model=SimpleNamespace(user_profiles=profiles))
    identity = NarrativeIdentity(organism, path=str(tmp_path / "identity.json"))

    identity.check_auto_milestones(interaction_count=0)

    names = {milestone["name"] for milestone in identity.milestones}
    assert not any(name.startswith("world_model_") for name in names)
    assert "deep_relationship" not in names


def test_narrative_identity_keeps_global_interaction_milestones(tmp_path):
    identity = NarrativeIdentity(SimpleNamespace(), path=str(tmp_path / "identity.json"))

    identity.check_auto_milestones(interaction_count=10)

    names = {milestone["name"] for milestone in identity.milestones}
    assert {"interaction_1", "interaction_10"} <= names


def test_post_interaction_does_not_store_user_text_in_global_narrative():
    organism = Mock()
    organism.ai_system._interaction_count = 4
    organism.narrative_identity = Mock()
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

    CognitiveOrganism._post_interaction(
        organism,
        user_input="Our private topic should stay in its profile and never become Lumina's global identity.",
        response="A response long enough to resemble a significant exchange and test the global narrative write path.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="profile-isolation-turn",
    )

    organism.narrative_identity.record_chapter.assert_not_called()
    organism.narrative_identity.check_auto_milestones.assert_called_once_with(4)


def test_contextual_chapters_do_not_enter_global_identity_or_arc(tmp_path):
    identity = NarrativeIdentity(SimpleNamespace(), path=str(tmp_path / "identity.json"))
    identity.record_chapter(
        "User topic", "private-profile phrase that must not enter the global prompt"
    )
    identity._current_arc = "The private-profile phrase is the current global arc."

    assert identity.global_chapters() == []
    assert "private-profile" not in identity.prompt_fragment()
    assert "private-profile" not in identity.self_description()

    from cognition.narrative_arc_writer import NarrativeArcWriter

    assert NarrativeArcWriter().synthesise_arc(identity) == ""


def test_explicit_global_chapter_is_available_for_identity_context(tmp_path):
    identity = NarrativeIdentity(SimpleNamespace(), path=str(tmp_path / "identity.json"))
    identity.record_chapter(
        "Internal milestone", "A verified internal transition.",
        significance=0.9, scope="global_internal",
    )

    assert [chapter.title for chapter in identity.global_chapters()] == ["Internal milestone"]
    assert "Internal milestone" in identity.self_description()


def test_post_interaction_does_not_store_user_text_in_global_narrative():
    organism = Mock()
    organism.ai_system._interaction_count = 4
    organism.narrative_identity = Mock()
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

    CognitiveOrganism._post_interaction(
        organism,
        user_input="Our private topic should stay in its profile and never become Lumina's global identity.",
        response="A response long enough to resemble a significant exchange and test the global narrative write path.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="profile-isolation-turn",
    )

    organism.narrative_identity.record_chapter.assert_not_called()
    organism.narrative_identity.check_auto_milestones.assert_called_once_with(4)

