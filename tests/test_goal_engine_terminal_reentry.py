import time

from types import SimpleNamespace

from cognition.goal_engine import Goal, GoalEngine, Motivation


def _engine(tmp_path):
    engine = GoalEngine(SimpleNamespace(), persistence_file=str(tmp_path / "goals.json"))
    engine._is_valid_goal_topic = lambda _topic: True
    engine._is_external_task_topic = lambda _topic: False
    return engine


def _autonomous_source(topic):
    return {topic: {
        "kind": "autonomous_motivation",
        "method": "goal_engine.derive_motivations",
        "ref": f"autonomous_domain:{topic}",
    }}


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
        topic_source_provenance=_autonomous_source(topic),
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
        topic_source_provenance=_autonomous_source(topic),
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
        topic_source_provenance=_autonomous_source(topic),
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


def test_weak_one_word_curiosity_record_is_not_executable_goal(tmp_path):
    engine = _engine(tmp_path)
    legacy = Goal(
        id="legacy-rappelle", topic="rappelle", origin="goal_quality_filter",
        priority=0.82, energy=0.82, created_cycle=1, last_active=1,
        tension_source="curiosity_drive", source_concept_kind="state_record",
        source_concept_method="cognition.tension_topics.generate_curiosity_topic",
        source_concept_ref="curiosity.json#/topics/rappelle",
        source_concept_sha256="a" * 64,
    )
    engine._goals[legacy.id] = legacy

    assert engine.get_active_goals() == []
    assert legacy.status == "deferred"
    assert legacy.source_provenance_status == "unverified"
    assert legacy.source_provenance_reason == "source_receipt_incomplete_or_ineligible"


def test_semantically_valid_one_word_topic_is_allowed_with_repeated_commitment(tmp_path):
    engine = _engine(tmp_path)
    topic = "photosynthesis"
    candidates = engine.generate_candidates(
        [Motivation(name="explore", strength=0.7, origin="test")],
        [topic], limit=1,
        topic_source_turns={topic: ["turn-a", "turn-b"]},
        topic_source_provenance={topic: {
            "kind": "user_semantic_commitment",
            "method": "semantic_memory.recent_user_topic_evidence",
            "ref": "concept:photosynthesis",
        }},
    )
    assert len(candidates) == 1
    assert candidates[0].topic == topic
    assert engine.add_goal(candidates[0])
