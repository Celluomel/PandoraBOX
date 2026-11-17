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
