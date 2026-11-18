import json

from cognition.narrative_identity import NarrativeIdentity


def test_record_chapter_rolls_back_when_persistence_fails(tmp_path, monkeypatch):
    identity = NarrativeIdentity(None, path=str(tmp_path / "identity.json"))
    monkeypatch.setattr(identity, "_save", lambda: False)

    assert identity.record_chapter("Resolved a question", "Evidence was compared") is False
    assert identity.life_story == []
    assert identity._last_chapter == 0.0
    assert identity._narrative_stale is True


def test_record_chapter_atomically_persists_and_can_be_reloaded(tmp_path):
    path = tmp_path / "identity.json"
    identity = NarrativeIdentity(None, path=str(path))

    assert identity.record_chapter("Resolved a question", "Evidence was compared") is True
    assert path.exists()
    assert not path.with_suffix(path.suffix + ".tmp").exists()

    restored = NarrativeIdentity(None, path=str(path))
    assert len(restored.life_story) == 1
    assert restored.life_story[0].title == "Resolved a question"


def test_load_removes_legacy_user_chat_from_global_identity_and_arc(tmp_path):
    path = tmp_path / "identity.json"
    path.write_text(json.dumps({
        "life_story": [
            {
                "timestamp": 1.0,
                "title": "Reflective exchange",
                "description": "User: private-profile-only phrase",
                "emotion": "curious",
                "significance": 0.7,
            },
            {
                "timestamp": 2.0,
                "title": "Internal reflection",
                "description": "A global self-observation.",
                "emotion": "curious",
                "significance": 0.6,
            },
        ],
        "current_arc": "Shared themes include private-profile-only phrase.",
        "last_arc_topic": "private-profile-only phrase",
        "milestones": [
            {"name": "world_model_250_topics", "description": "profile data", "timestamp": 3.0},
            {"name": "deep_relationship", "description": "profile data", "timestamp": 4.0},
            {"name": "interaction_10", "description": "global count", "timestamp": 5.0},
        ],
    }), encoding="utf-8")

    identity = NarrativeIdentity(None, path=str(path))

    assert [chapter.title for chapter in identity.life_story] == ["Internal reflection"]
    assert identity._current_arc == ""
    assert identity._last_arc_topic == ""
    assert [m["name"] for m in identity.milestones] == ["interaction_10"]
    persisted = path.read_text(encoding="utf-8")
    assert "private-profile-only phrase" not in persisted
    assert "deep_relationship" not in persisted

