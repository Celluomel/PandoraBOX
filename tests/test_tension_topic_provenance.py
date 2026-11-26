import json
from pathlib import Path

from cognition.tension_topics import generate_topic_with_provenance


def test_curiosity_topic_receipt_names_and_fingerprints_the_source_record(tmp_path: Path):
    node = {
        "curiosity": 0.91,
        "source_turn_ids": ["turn-user-topic-42"],
        "questions": ["How does memory consolidation work?"],
        "times_encountered": 3,
        "times_researched": 0,
    }
    (tmp_path / "curiosity.json").write_text(json.dumps({
        "topics": {"memory consolidation": node},
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"] == "memory consolidation"
    assert receipt["generator"] == "cognition.tension_topics.generate_curiosity_topic"
    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "curiosity.json#/topics/memory consolidation"
    assert len(receipt["source_sha256"]) == 64
    assert "curiosity" not in receipt


def test_generated_curiosity_questions_and_unlinked_topics_do_not_ground_goals(
    tmp_path: Path,
):
    (tmp_path / "curiosity.json").write_text(json.dumps({
        "topics": {
            "rappelle": {
                "curiosity": 0.99,
                "source": "goal_exploration",
                "times_encountered": 276,
                "times_researched": 1,
                "questions": ["What can I learn about rappelle?"],
            },
            "cognitive architecture": {
                "curiosity": 0.62,
                "source": "goal_exploration",
                "source_turn_ids": ["turn-topic-17"],
                "times_encountered": 4,
                "times_researched": 0,
                "questions": ["What can I learn about cognitive architecture?"],
            },
        },
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"] == "cognitive architecture"
    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "curiosity.json#/topics/cognitive architecture"


def test_curiosity_source_turn_ids_must_be_structured_and_nonempty(tmp_path: Path):
    (tmp_path / "curiosity.json").write_text(json.dumps({
        "topics": {
            "stale question": {
                "curiosity": 0.99,
                "source_turn_ids": "legacy-string-is-not-a-turn-list",
                "questions": ["What can I learn about stale question?"],
            },
        },
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"] == ""
    assert receipt["source_kind"] == "unresolved"
    assert receipt["source_ref"] == ""


def test_identity_topic_receipt_points_to_the_selected_belief(tmp_path: Path):
    belief = {
        "statement": "I value careful evidence",
        "violations": 4,
        "affirmations": 1,
        "confidence": 0.7,
    }
    (tmp_path / "self_concept.json").write_text(json.dumps({
        "beliefs": {"careful_evidence": belief},
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("identity_stress", tmp_path)

    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "self_concept.json#/beliefs/careful_evidence"
    assert "I value careful evidence" in receipt["topic"]


def test_contradiction_topic_receipt_points_to_unconfronted_record(tmp_path: Path):
    contradiction = {
        "claimed_belief": "I check evidence",
        "actual_behavior": "I accepted an unsupported claim",
        "confronted": False,
        "discrepancy_score": 0.8,
    }
    (tmp_path / "contradictions.json").write_text(json.dumps({
        "contradictions": [contradiction],
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("contradiction_pressure", tmp_path)

    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "contradictions.json#/contradictions/0"
    assert "I accepted an unsupported claim" in receipt["topic"]


def test_uncertainty_topic_receipt_requires_and_points_to_intervention_evidence(tmp_path: Path):
    belief = {
        "antecedent": "a longer prompt",
        "consequent": "better recall",
        "confidence": 0.2,
        "evidence_status": "intervention_reported",
        "evidence_method": "controlled_intervention",
        "evidence_source": "test run",
        "evidence_ref": "run-17",
        "evidence_intervention": "prompt changed",
        "evidence_comparison": "before versus after",
        "evidence_outcome": "recall improved",
        "evidence_comparison_outcome": "lower recall before",
    }
    (tmp_path / "world_model.json").write_text(json.dumps({
        "causal_beliefs": [belief],
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("knowledge_uncertainty", tmp_path)

    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "world_model.json#/causal_beliefs/0"
    assert "a longer prompt" in receipt["topic"]


def test_social_topic_receipt_points_to_high_activation_open_question(tmp_path: Path):
    question = {"text": "What did the last test actually establish?", "activation": 0.9}
    (tmp_path / "thought_stream.json").write_text(json.dumps({
        "open_questions": [question],
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("social_drive", tmp_path)

    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "thought_stream.json#/open_questions/0"
    assert question["text"] in receipt["topic"]


def test_topic_without_a_matching_state_record_is_not_called_evidence(tmp_path: Path):
    (tmp_path / "curiosity.json").write_text(json.dumps({"topics": {}}), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"] == ""
    assert receipt["source_kind"] == "unresolved"
    assert receipt["source_ref"] == ""
    assert receipt["source_sha256"] == ""
