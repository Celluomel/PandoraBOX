import time

from types import SimpleNamespace

from cognition.goal_engine import Goal, GoalEngine, Motivation


def _engine(tmp_path):
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    engine._is_external_task_topic = lambda _topic: False
    return engine


def test_terminal_goal_does_not_permanently_block_topic_after_cooldown(tmp_path):
    engine = _engine(tmp_path)
    topic = "understand grounded memory retrieval"
    old_goal = Goal(
        id="old-goal", topic=topic, origin="explore", priority=0.7,
        energy=0.2, created_cycle=1, last_active=20, status="completed",
    )
    engine._goals[old_goal.id] = old_goal
    engine._recently_abandoned[topic.casefold()] = (
        time.time() - engine.TOPIC_COOLDOWN_SECS - 1
    )
    assert engine._save_goals()

    reloaded = _engine(tmp_path)
    candidates = reloaded.generate_candidates(
        [Motivation(name="explore", strength=0.7, origin="test")],
        [topic],
        limit=1,
    )

    assert len(candidates) == 1
    assert candidates[0].topic == topic
    assert reloaded.add_goal(candidates[0]) is True


def test_legacy_terminal_record_without_cooldown_can_reenter(tmp_path):
    engine = _engine(tmp_path)
    topic = "understand grounded memory retrieval"
    engine._goals["legacy-goal"] = Goal(
        id="legacy-goal", topic=topic, origin="explore", priority=0.7,
        energy=0.2, created_cycle=1, last_active=20, status="completed",
    )

    candidates = engine.generate_candidates(
        [Motivation(name="explore", strength=0.7, origin="test")],
        [topic],
        limit=1,
    )

    assert len(candidates) == 1
    assert engine.add_goal(candidates[0]) is True


def test_live_goal_and_unexpired_cooldown_still_suppress_reentry(tmp_path):
    engine = _engine(tmp_path)
    topic = "understand grounded memory retrieval"
    active = Goal(
        id="active-goal", topic=topic, origin="explore", priority=0.7,
        energy=0.7, created_cycle=1, last_active=1,
    )
    engine._goals[active.id] = active
    assert engine.generate_candidates(
        [Motivation(name="explore", strength=0.7, origin="test")],
        [topic],
        limit=1,
    ) == []

    active.status = "abandoned"
    engine._recently_abandoned[topic.casefold()] = time.time()
    assert engine.generate_candidates(
        [Motivation(name="explore", strength=0.7, origin="test")],
        [topic],
        limit=1,
    ) == []


def test_generated_goal_source_provenance_survives_persistence_reload(tmp_path):
    engine = _engine(tmp_path)
    topic = "cognitive architecture"
    engine._topic_quality_cache[topic] = True
    candidate = engine.generate_candidates(
        [Motivation(name="develop_capabilities", strength=0.7, origin="trait:curiosity")],
        [topic],
        limit=1,
        topic_source_turns={topic: ["turn-21", "turn-22"]},
        topic_source_provenance={topic: {
            "kind": "user_semantic_commitment",
            "method": "semantic_memory.recent_user_topic_evidence",
            "ref": "concept:17",
        }},
    )[0]

    assert candidate.source_turn_id == "turn-22"
    assert candidate.source_evidence_turn_ids == ["turn-21", "turn-22"]
    assert candidate.source_concept_kind == "user_semantic_commitment"
    assert candidate.source_concept_method == "semantic_memory.recent_user_topic_evidence"
    assert candidate.source_concept_ref == "concept:17"
    assert engine.add_goal(candidate)

    reloaded = _engine(tmp_path)
    restored = reloaded.get_goal_by_id(candidate.id)
    assert restored is not None
    assert restored.source_evidence_turn_ids == ["turn-21", "turn-22"]
    assert restored.source_concept_kind == "user_semantic_commitment"
    assert restored.source_concept_ref == "concept:17"
    assert restored.source_provenance_records[0]["source_turn_ids"] == [
        "turn-21", "turn-22",
    ]
