from pathlib import Path
from types import SimpleNamespace

from core.phase1_integration import Phase1Orchestrator
from cognition.thought_stream import ThoughtStream


def test_phase1_competition_reads_new_in_memory_thought_before_disk_flush(tmp_path):
    stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    assert stream.add(
        "Memory about cognitive audit: concept links found",
        source="goal_action.memory_recall",
        priority=0.45,
        thought_type="goal_action",
    )
    assert stream._persist_dirty is True

    phase1 = Phase1Orchestrator.__new__(Phase1Orchestrator)
    phase1.persona_dir = Path(tmp_path)
    phase1._thought_stream = stream

    first = phase1._load_recent_thoughts()
    second = phase1._load_recent_thoughts()

    assert len(first) == 1
    assert first[0]["source"] == "goal_action.memory_recall"
    assert first[0]["thought_type"] == "goal_action"
    assert first[0]["id"].startswith("tht_")
    assert first[0]["id"] == second[0]["id"]

    # After persistence, the same in-memory and disk item must still be one
    # candidate with the same stable identity.
    stream._save_persisted()
    merged = phase1._load_recent_thoughts()
    assert len(merged) == 1
    assert merged[0]["id"] == first[0]["id"]


def test_thought_ids_survive_thought_stream_restart(tmp_path):
    first_stream = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    assert first_stream.add("A durable thought", source="audit", priority=0.5)
    thought_id = first_stream.recent_dicts(1)[0]["id"]
    first_stream.flush()

    reloaded = ThoughtStream(SimpleNamespace(_data_dir=tmp_path))
    assert reloaded.recent_dicts(1)[0]["id"] == thought_id
