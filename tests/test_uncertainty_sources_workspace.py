import json
from types import SimpleNamespace

from cognition.global_workspace import GlobalWorkspace
from cognition.semantic_extractor import SemanticExtractor
from cognition.intention_reasoner import IntentionReasoner
from cognition.cognitive_organism import _global_workspace_prompt_fragment
from core.cognitive_event_bus import (
    CognitiveEventBus,
    CONTRADICTION_DETECTED,
    SURPRISE_DETECTED,
    wire_cognitive_bus,
)


class _Memory:
    def upsert_concept(self, *_args, **_kwargs):
        return 1

    def record_observation(self, *_args, **_kwargs):
        return True

    def upsert_relation(self, *_args, **_kwargs):
        return True


def test_global_workspace_keeps_independent_uncertainty_sources_and_resolves_one():
    workspace = GlobalWorkspace()
    user = workspace.record_uncertainty(
        source_type="user_exchange:competing_explanations",
        source_module="semantic_extractor",
        source_ref="turn-1",
        turn_id="turn-1",
        question="Which explanation accounts for the mismatch?",
        evidence="I am unsure which explanation is right.",
        salience=0.7,
    )
    prediction = workspace.record_uncertainty(
        source_type="prediction_error",
        source_module="predictive_mind",
        source_ref="event-1",
        question="Why did the prediction differ?",
        evidence="observed outcome differed",
        salience=0.8,
    )

    assert user["recorded"] and prediction["recorded"]
    assert workspace.get_state().uncertainty == 0.8
    assert workspace.resolve_uncertainty(user["uncertainty_id"], "evidence-1")["resolved"]
    state = workspace.get_state()
    assert len(state.uncertainty_sources) == 2
    statuses = {item["source_type"]: item["status"] for item in state.uncertainty_sources}
    assert statuses == {
        "user_exchange:competing_explanations": "resolved",
        "prediction_error": "open",
    }
    assert state.uncertainty == 0.8


def test_semantic_extractor_records_user_uncertainty_only_with_verbatim_evidence():
    user_text = "Je ne suis pas certain que l'index mémoire restitue la bonne source."
    parsed = {
        "turn_kind": "topic",
        "goal_signal": "none",
        "goal_signal_evidence": "",
        "uncertainty_signal": {
            "present": True,
            "issue": "Whether memory retrieval returned the correct source",
            "evidence": "Je ne suis pas certain que l'index mémoire restitue la bonne source.",
            "kind": "user_stated_doubt",
            "salience": 0.76,
        },
        "concepts": [{"name": "index mémoire", "evidence": "index mémoire"}],
        "relations": [],
        "profile_claims": [],
        "dominant_topic": "index mémoire",
        "cognitive_load": 0.2,
    }
    workspace = GlobalWorkspace()
    extractor = SemanticExtractor(_Memory(), llm_fn=lambda _prompt: json.dumps(parsed))

    receipt = extractor._extract(
        user_text, "", None, workspace,
        observation_role="user_topic", turn_id="turn-user-uncertainty",
    )

    assert receipt["uncertainty_source_receipt"]["recorded"] is True
    record = workspace.get_state().uncertainty_sources[0]
    assert record["turn_id"] == "turn-user-uncertainty"
    assert record["source_type"] == "user_exchange:user_stated_doubt"
    assert record["evidence"] in user_text

    parsed["uncertainty_signal"]["evidence"] = "assistant invented evidence"
    ungrounded = SemanticExtractor._ground_uncertainty_signal(
        parsed["uncertainty_signal"], user_text,
    )
    assert ungrounded == {}


def test_retrieval_hint_does_not_suppress_semantically_routed_user_uncertainty():
    user_text = "Je ne sais pas quelle source est correcte; plusieurs restent possibles."
    parsed = {
        "turn_kind": "topic",
        "goal_signal": "none",
        "goal_signal_evidence": "",
        "uncertainty_signal": {
            "present": True,
            "issue": "Which of the possible sources is correct",
            "evidence": user_text,
            "kind": "user_stated_doubt",
            "salience": 0.72,
        },
        "concepts": [],
        "relations": [],
        "profile_claims": [],
        "dominant_topic": "",
        "cognitive_load": 0.2,
    }
    workspace = GlobalWorkspace()
    extractor = SemanticExtractor(_Memory(), llm_fn=lambda _prompt: json.dumps(parsed))

    receipt = extractor._extract(
        user_text, "", None, workspace, observation_role="user_topic",
        turn_id="turn-retrieval-uncertainty", turn_kind_hint="retrieval",
        uncertainty_candidate=True,
    )

    assert receipt["turn_kind"] == "retrieval"
    assert receipt["classification_source"] == (
        "upstream_turn_contract_plus_uncertainty_extraction"
    )
    assert receipt["learning_status"] == "skipped_non_topic_turn"
    assert receipt["uncertainty_source_receipt"]["recorded"] is True
    assert workspace.get_state().uncertainty_sources[0]["turn_id"] == (
        "turn-retrieval-uncertainty"
    )


def test_peer_turn_never_becomes_user_uncertainty_source():
    workspace = GlobalWorkspace()
    extractor = SemanticExtractor(
        _Memory(), llm_fn=lambda _prompt: (_ for _ in ()).throw(
            AssertionError("peer turn should not trigger user uncertainty extraction")
        ),
    )

    receipt = extractor._extract(
        "uncertainty-like peer input", "", None, workspace,
        observation_role="peer_topic", turn_id="peer-turn",
        turn_kind_hint="retrieval", uncertainty_candidate=True,
    )

    assert receipt["classification_source"] == "upstream_turn_contract"
    assert receipt["uncertainty_source_receipt"]["status"] == "not_candidate"
    assert workspace.get_state().uncertainty_sources == []


def test_event_bus_routes_conflict_and_prediction_error_as_distinct_sources():
    workspace = GlobalWorkspace()
    bus = CognitiveEventBus()
    wire_cognitive_bus(SimpleNamespace(workspace=workspace), bus)
    conflict, _ = bus.emit_with_receipt(
        CONTRADICTION_DETECTED,
        {"topic": "belief", "claimed_belief": "claim A", "actual_behavior": "evidence B",
         "contradiction_id": "contradiction-1", "turn_id": "turn-2", "pressure": 0.6},
        source="belief_reviser",
    )
    surprise, _ = bus.emit_with_receipt(
        SURPRISE_DETECTED,
        {"domain": "retrieval", "error_level": 0.4, "turn_id": "turn-3", "cycle_id": 12,
         "evidence": "expected X, observed Y"},
        source="predictive_mind",
    )

    assert conflict.payload["uncertainty_workspace_receipt"]["recorded"] is True
    assert surprise.payload["uncertainty_workspace_receipt"]["recorded"] is True
    records = workspace.get_state().uncertainty_sources
    assert {item["source_type"] for item in records} == {
        "belief_conflict", "prediction_error",
    }
    assert {item["source_module"] for item in records} == {
        "belief_reviser", "predictive_mind",
    }
    assert {item["turn_id"] for item in records if item["turn_id"]} == {"turn-2", "turn-3"}
    assert [item["cycle_id"] for item in records if item["cycle_id"]] == [12]


def test_workspace_prompt_surfaces_open_uncertainty_without_flattening_source():
    state = GlobalWorkspace().get_state()
    state.uncertainty_sources = [
        {"status": "open", "source_type": "user_exchange:open_question",
         "source_module": "semantic_extractor", "source_ref": "turn-3",
         "question": "Which source supports this claim?", "salience": 0.7},
        {"status": "open", "source_type": "belief_conflict",
         "source_module": "belief_reviser", "source_ref": "contradiction-4",
         "question": "Do these beliefs conflict?", "salience": 0.8},
        {"status": "open", "source_type": "prediction_error",
         "source_module": "predictive_mind", "source_ref": "event-5",
         "question": "Why did the observed outcome differ?", "salience": 0.6},
        {"status": "open", "source_type": "decision_reasoning_limit",
         "source_module": "intention_reasoner", "source_ref": "episode-6",
         "question": "Which action is feasible?", "salience": 0.5},
        {"status": "open", "source_type": "user_exchange:clarification",
         "source_module": "semantic_extractor", "source_ref": "turn-7",
         "question": "Which of the cited origins is still unverified?", "salience": 0.9},
    ]

    fragment = _global_workspace_prompt_fragment(state)

    assert "user_exchange:open_question" in fragment
    assert "belief_conflict" in fragment
    assert "prediction_error" in fragment and "decision_reasoning_limit" in fragment
    assert "user_exchange:clarification" in fragment
    assert all(ref in fragment for ref in (
        "turn-3", "contradiction-4", "event-5", "episode-6", "turn-7",
    ))
    assert "5 independent open source record(s)" in fragment
    assert "peak salience=0.90" in fragment
    assert "contributing modules" in fragment


def test_intention_reasoning_limits_enter_workspace_as_separate_evidence(tmp_path):
    workspace = GlobalWorkspace()
    organism = SimpleNamespace(workspace=workspace, _loop=None)
    reasoner = IntentionReasoner(organism, path=str(tmp_path / "episodes.json"))
    goal = SimpleNamespace(
        id="goal-a", topic="memory grounding", origin="user_semantic_commitment",
        priority=0.8, source_turn_id="turn-goal", source_cycle_id=17,
    )

    episode = reasoner.deliberate(goal, ["memory_recall", "self_question"])

    records = workspace.get_state().uncertainty_sources
    assert len(records) == len(episode.uncertainties)
    assert all(item["source_type"] == "decision_reasoning_limit" for item in records)
    assert all(item["turn_id"] == "turn-goal" and item["cycle_id"] == 17 for item in records)
    assert len({item["source_ref"] for item in records}) == len(records)
