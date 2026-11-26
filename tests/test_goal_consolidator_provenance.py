from cognition.goal_consolidator import GoalConsolidator


class _MemoryDal:
    def __init__(self):
        self.saved = []

    def save_goal(self, goal):
        self.saved.append(dict(goal))
        return True


def test_consolidation_unions_source_records_without_erasing_each_origin():
    consolidator = GoalConsolidator.__new__(GoalConsolidator)
    consolidator.dal = _MemoryDal()
    keeper = {
        "id": "g-user", "name": "cognitive architecture", "origin": "explore",
        "priority": 0.9, "quality_score": 0.9, "status": "active",
        "source_concept_kind": "user_semantic_commitment",
        "source_concept_method": "semantic_memory.recent_user_topic_evidence",
        "source_concept_ref": "concept:17",
        "source_turn_id": "turn-22",
        "source_evidence_turn_ids": ["turn-21", "turn-22"],
        "source_provenance_records": [{
            "kind": "user_semantic_commitment",
            "method": "semantic_memory.recent_user_topic_evidence",
            "ref": "concept:17",
            "source_turn_ids": ["turn-21", "turn-22"],
        }],
    }
    victim = {
        "id": "g-internal", "name": "understand cognitive architecture",
        "origin": "develop_capabilities", "priority": 0.4,
        "quality_score": 0.4, "status": "active",
        "source_concept_kind": "autonomous_motivation",
        "source_concept_method": "goal_engine.derive_motivations",
        "source_concept_ref": "motivation:develop_capabilities",
        "source_provenance_records": [{
            "kind": "autonomous_motivation",
            "method": "goal_engine.derive_motivations",
            "ref": "motivation:develop_capabilities",
            "source_turn_ids": [],
        }],
    }

    merged, archived = consolidator._merge_cluster([keeper, victim])

    assert merged is keeper
    assert len(archived) == 1
    assert merged["source_evidence_turn_ids"] == ["turn-21", "turn-22"]
    assert {item["kind"] for item in merged["source_provenance_records"]} == {
        "user_semantic_commitment", "autonomous_motivation",
    }
    assert archived[0]["source_provenance_records"] == victim["source_provenance_records"]
    assert consolidator.dal.saved[0]["source_provenance_records"] == merged[
        "source_provenance_records"
    ]


def test_consolidation_recovers_legacy_singular_provenance_fields():
    consolidator = GoalConsolidator.__new__(GoalConsolidator)
    consolidator.dal = _MemoryDal()
    keeper = {
        "id": "g1", "name": "cognitive architecture", "priority": 0.9,
        "quality_score": 0.9, "source_concept_kind": "user_semantic_commitment",
        "source_concept_ref": "concept:1", "source_turn_id": "turn-1",
    }
    victim = {
        "id": "g2", "name": "understand cognitive architecture", "priority": 0.3,
        "quality_score": 0.3, "source_concept_kind": "autonomous_motivation",
        "source_concept_ref": "motivation:learn",
    }

    merged, _ = consolidator._merge_cluster([keeper, victim])

    assert {item["source_concept_kind"] for item in merged["source_provenance_records"]} == {
        "user_semantic_commitment", "autonomous_motivation",
    }
