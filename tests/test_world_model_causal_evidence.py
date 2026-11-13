import json
from pathlib import Path

from cognition.abstract_reasoning_engine import AbstractReasoningEngine, ReasoningResult
from cognition.cognitive_dissonance_engine import CDEContext, CognitiveDissonanceEngine
from cognition.tension_topics import generate_uncertainty_topic
from cognition.world_model import causal_belief_has_intervention_evidence
from cognition.world_model import WorldModel


def _world_model(path):
    return WorldModel(None, path=str(path))


def test_repeated_adjacent_topics_remain_associations_not_causal_beliefs(tmp_path):
    model = _world_model(tmp_path / "world.json")

    for _ in range(5):
        model.update_from_interaction(
            user_id="u",
            user_text="camera calibration",
            response="radar distance",
        )

    assert model.causal_beliefs == []
    assert model.related_topics("camera")


def test_causal_claim_requires_controlled_intervention_evidence(tmp_path):
    model = _world_model(tmp_path / "world.json")

    rejected = model.learn_causal("short answers", "engagement rises", confidence=0.9)

    assert rejected == {
        "status": "rejected_missing_intervention_evidence",
        "persisted": False,
    }
    assert model.causal_beliefs == []

    evidence = {
        "method": "controlled_intervention",
        "source": "conversation_experiment",
        "evidence_ref": "exp-42",
        "intervention": "short answers",
        "comparison": "usual answer length",
        "outcome": "follow-up rate 0.8",
        "comparison_outcome": "follow-up rate 0.4",
    }
    stored = model.learn_causal(
        "short answers", "engagement rises", confidence=0.9, evidence=evidence
    )

    assert stored["status"] == "stored_with_intervention_evidence"
    assert model.causal_beliefs[0].evidence_status == "intervention_reported"
    assert model.causal_beliefs[0].confidence == 0.9
    assert _world_model(tmp_path / "world.json").causal_beliefs[0].evidence_ref == "exp-42"


def test_abstract_analogy_does_not_write_causal_belief(tmp_path):
    model = _world_model(tmp_path / "world.json")
    engine = object.__new__(AbstractReasoningEngine)
    engine._org = type("Org", (), {
        "world_model": model,
        "curiosity_engine": None,
        "semantic_memory": None,
    })()
    engine._mem = None
    result = ReasoningResult(
        user_id="u",
        core_concept="identity",
        best_analogy="selection over time",
        analogy_domain="evolution",
        causal_pair=("identity", "structural pattern like evolution"),
    )

    engine._apply_side_effects(result)

    assert model.causal_beliefs == []


def test_legacy_causal_records_are_retained_but_excluded_from_reasoning(tmp_path):
    path = tmp_path / "world.json"
    path.write_text(json.dumps({
        "causal_beliefs": [{
            "antecedent": "not locomotion",
            "consequent": "unsafe movement",
            "confidence": 0.9,
            "auto_learned": True,
        }]
    }), encoding="utf-8")

    model = _world_model(path)

    assert len(model.causal_beliefs) == 1
    assert model.causal_beliefs[0].evidence_status == "legacy_unverified"
    assert model.predict_from_context("locomotion") == []
    assert not model.has_contradiction("locomotion")
    assert model.summary()["causal_beliefs"] == 0
    assert model.summary()["causal_records_total"] == 1
    assert model.summary()["causal_unverified"] == 1


def test_dissonance_engine_ignores_unverified_legacy_causal_records():
    engine = CognitiveDissonanceEngine()
    context = CDEContext(world_model={"causal_beliefs": [{
        "antecedent": "legacy belief",
        "consequent": "contradicting outcome",
        "confidence": 0.1,
        "evidence_status": "legacy_unverified",
    }]})

    assert engine._detect_belief_vs_evidence(context) == []


def test_dissonance_engine_uses_intervention_supported_records():
    engine = CognitiveDissonanceEngine()
    context = CDEContext(world_model={"causal_beliefs": [{
        "antecedent": "supported belief",
        "consequent": "observed outcome",
        "confidence": 0.1,
        "evidence_status": "intervention_reported",
        "evidence_method": "controlled_intervention",
        "evidence_source": "test",
        "evidence_ref": "test-1",
        "evidence_intervention": "condition A",
        "evidence_comparison": "condition B",
        "evidence_outcome": "outcome A",
        "evidence_comparison_outcome": "outcome B",
    }]})

    events = engine._detect_belief_vs_evidence(context)

    assert len(events) == 1
    assert events[0].belief_ref == "supported belief"


def test_status_alone_does_not_make_a_causal_record_usable():
    assert not causal_belief_has_intervention_evidence({
        "evidence_status": "intervention_reported",
        "antecedent": "x",
        "consequent": "y",
    })


def test_proactive_uncertainty_topic_ignores_unverified_legacy_causes(tmp_path):
    (tmp_path / "world_model.json").write_text(json.dumps({
        "causal_beliefs": [{
            "antecedent": "legacy topic",
            "consequent": "legacy outcome",
            "confidence": 0.1,
        }]
    }), encoding="utf-8")

    topic = generate_uncertainty_topic(tmp_path)

    assert "legacy topic" not in topic
    assert "legacy outcome" not in topic
