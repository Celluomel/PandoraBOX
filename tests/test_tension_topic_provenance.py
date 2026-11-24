import json
from pathlib import Path

from cognition.tension_topics import generate_topic_with_provenance


def test_curiosity_topic_receipt_names_and_fingerprints_the_source_record(tmp_path: Path):
    node = {
        "curiosity": 0.91,
        "questions": ["How does memory consolidation work?"],
        "times_encountered": 3,
        "times_researched": 0,
    }
    (tmp_path / "curiosity.json").write_text(json.dumps({
        "topics": {"memory consolidation": node},
    }), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"] == node["questions"][-1]
    assert receipt["generator"] == "cognition.tension_topics.generate_curiosity_topic"
    assert receipt["source_kind"] == "state_record"
    assert receipt["source_ref"] == "curiosity.json#/topics/memory consolidation"
    assert len(receipt["source_sha256"]) == 64
    assert "curiosity" not in receipt


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


def test_topic_without_a_matching_state_record_is_not_called_evidence(tmp_path: Path):
    (tmp_path / "curiosity.json").write_text(json.dumps({"topics": {}}), encoding="utf-8")

    receipt = generate_topic_with_provenance("curiosity_drive", tmp_path)

    assert receipt["topic"]
    assert receipt["source_kind"] == "unresolved"
    assert receipt["source_ref"] == ""
    assert receipt["source_sha256"] == ""
