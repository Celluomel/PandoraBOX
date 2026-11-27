import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from cognition.global_workspace import GlobalWorkspace
from cognition.semantic_extractor import SemanticExtractor
from cognition.intention_reasoner import IntentionReasoner
from cognition.cognitive_organism import (
    _global_workspace_uncertainty_fragment,
    _global_workspace_prompt_fragment,
    _workspace_state_for_prompt,
    _compress_workspace_source_refs,
    _common_workspace_text_prefix,
)
from cognition.persona_bridge import _workspace_prompt_uncertainty_receipt
from cognition.prompt_context_budget import PromptContextBudget
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


def test_uncertainty_sources_survive_restart_and_resolution_is_source_scoped(tmp_path):
    ledger_path = tmp_path / "workspace-uncertainties.json"
    first = GlobalWorkspace(uncertainty_path=ledger_path)
    user = first.record_uncertainty(
        source_type="user_exchange:open_question", source_module="semantic_extractor",
        source_ref="turn-user-1", turn_id="turn-user-1",
        question="Which of these sources is correct?", evidence="Two sources remain possible.",
        salience=0.7,
    )
    prediction = first.record_uncertainty(
        source_type="prediction_error", source_module="predictive_mind",
        source_ref="cycle-18", turn_id="turn-prediction-1", cycle_id=18,
        question="Why did the predicted result differ?", evidence="Observed result differed.",
        salience=0.8,
    )

    assert user["persistence_status"] == "persisted"
    assert prediction["persistence_status"] == "persisted"
    restarted = GlobalWorkspace(uncertainty_path=ledger_path)
    restored = restarted.get_state().uncertainty_sources
    assert {item["uncertainty_id"] for item in restored} == {
        user["uncertainty_id"], prediction["uncertainty_id"],
    }
    assert all(item["status"] == "open" for item in restored)
    assert {item["source_module"] for item in restored} == {
        "semantic_extractor", "predictive_mind",
    }

    resolution = restarted.resolve_uncertainty(
        user["uncertainty_id"], "resolution:turn-review",
    )
    assert resolution["resolved"] is True
    assert resolution["persistence_status"] == "persisted"
    after_restart = GlobalWorkspace(uncertainty_path=ledger_path).get_state()
    status_by_id = {item["uncertainty_id"]: item["status"] for item in after_restart.uncertainty_sources}
    assert status_by_id == {
        user["uncertainty_id"]: "resolved",
        prediction["uncertainty_id"]: "open",
    }


def test_workspace_does_not_resolve_source_when_ledger_write_fails():
    workspace = GlobalWorkspace()
    source = workspace.record_uncertainty(
        source_type="user_exchange:open_question", source_module="semantic_extractor",
        source_ref="turn-user-2", turn_id="turn-user-2",
        question="Which source remains open?", salience=0.6,
    )
    workspace._uncertainty_path = Path("unused-ledger.json")
    workspace._persist_uncertainty_sources_locked = lambda: "persistence_failed"

    resolution = workspace.resolve_uncertainty(source["uncertainty_id"], "resolution-attempt")

    assert resolution["status"] == "persistence_failed"
    assert resolution["resolved"] is False
    assert workspace.get_state().uncertainty_sources[0]["status"] == "open"


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
    assert receipt["workspace_status"] == "uncertainty_recorded"
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
    assert "5 records, 5 questions, 5 origins" in fragment
    assert "user_exchange:open_question/semantic_extractor" in fragment
    assert "preserve refs and keep all sources open" in fragment


def test_workspace_prompt_explicitly_reports_zero_open_uncertainty_sources():
    workspace = GlobalWorkspace()
    state = workspace.get_state()
    fragment = _global_workspace_uncertainty_fragment(state)
    full_prompt = _global_workspace_prompt_fragment(state)
    organism = SimpleNamespace(workspace=workspace)
    receipt = _workspace_prompt_uncertainty_receipt(organism, full_prompt)

    assert "0 independent uncertainty source records" in fragment
    assert "do not invent an internal source" in fragment
    assert "do not invent an internal source" in fragment
    assert "state that no open source is registered" in fragment
    assert "[Open uncertainty synthesis]" in full_prompt
    assert receipt["open_uncertainty_source_count"] == 0
    assert receipt["uncertainty_synthesis_included"] is True
    assert receipt["uncertainty_source_refs"] == []


def test_prompt_uses_current_workspace_sources_not_stale_slow_cycle_snapshot():
    workspace = GlobalWorkspace()
    record = workspace.record_uncertainty(
        source_type="user_exchange:open_question",
        source_module="semantic_extractor",
        source_ref="turn-current",
        turn_id="turn-current",
        question="Which source remains unresolved?",
        evidence="Several possible sources remain open.",
        salience=0.7,
    )
    stale_snapshot = GlobalWorkspace().get_state()
    organism = SimpleNamespace(workspace=workspace, _v32_workspace_state=stale_snapshot)

    selected = _workspace_state_for_prompt(organism)
    fragment = _global_workspace_prompt_fragment(selected)

    assert selected.uncertainty_sources[0]["uncertainty_id"] == record["uncertainty_id"]
    assert "Which source remains unresolved?" in fragment
    assert "refs=turn-current" in fragment
    assert "Several possible sources remain open." not in fragment


def test_prompt_receipt_attributes_all_open_origins_from_canonical_workspace():
    workspace = GlobalWorkspace()
    user = workspace.record_uncertainty(
        source_type="user_exchange:competing_explanations",
        source_module="semantic_extractor", source_ref="turn-user", turn_id="turn-user",
        question="Which explanation accounts for the mismatch?",
        evidence="private user quote", salience=0.7,
    )
    prediction = workspace.record_uncertainty(
        source_type="prediction_error", source_module="predictive_mind",
        source_ref="cycle-12", turn_id="turn-trigger", cycle_id=12,
        question="Why did the predicted outcome differ?",
        evidence="private prediction evidence", salience=0.8,
    )
    organism = SimpleNamespace(
        workspace=workspace,
        _v32_workspace_state=GlobalWorkspace().get_state(),
    )
    state = _workspace_state_for_prompt(organism)
    prompt = _global_workspace_prompt_fragment(state)

    receipt = _workspace_prompt_uncertainty_receipt(organism, prompt)
    assert receipt["open_uncertainty_source_count"] == 2
    assert receipt["uncertainty_synthesis_included"] is True
    assert set(receipt["uncertainty_source_refs"]) == {
        user["uncertainty_id"], prediction["uncertainty_id"],
    }
    assert receipt["uncertainty_source_turn_ids"] == ["turn-trigger", "turn-user"]
    assert receipt["uncertainty_source_types"] == [
        "prediction_error", "user_exchange:competing_explanations",
    ]
    assert "private user quote" not in prompt
    assert "private prediction evidence" not in prompt

    workspace.resolve_uncertainty(user["uncertainty_id"], "resolution:turn-review")
    remaining = _workspace_prompt_uncertainty_receipt(
        organism, _global_workspace_prompt_fragment(_workspace_state_for_prompt(organism)),
    )
    assert remaining["open_uncertainty_source_count"] == 1
    assert remaining["uncertainty_source_refs"] == [prediction["uncertainty_id"]]


def test_uncertainty_synthesis_has_reserved_prompt_budget_ahead_of_pressure_blocks():
    workspace = GlobalWorkspace()
    workspace.record_uncertainty(
        source_type="user_exchange:competing_explanations",
        source_module="semantic_extractor", source_ref="turn-user", turn_id="turn-user",
        question="Which explanation accounts for the mismatch?",
        evidence="private evidence", salience=0.7,
    )
    state = workspace.get_state()
    uncertainty = _global_workspace_uncertainty_fragment(state)
    budget = PromptContextBudget(path="unused-test-budget.json")
    budget.add("cognitive_pressure", "energy", "e" * 84)  # 21 estimated tokens
    budget.add("cognitive_pressure", "arbitration", "a" * 204)  # 51 tokens
    budget.add("cognitive_pressure", "global_workspace", "w" * 820)  # 205 tokens
    budget.add("epistemic_context", "global_workspace_uncertainty", uncertainty)

    assembled = budget.assemble()
    uncertainty_selection = budget.selection_receipt(
        "epistemic_context", "global_workspace_uncertainty",
    )
    legacy_workspace_selection = budget.selection_receipt(
        "cognitive_pressure", "global_workspace",
    )

    assert uncertainty_selection["selected"] is True
    assert uncertainty in assembled
    assert legacy_workspace_selection["selected"] is False
    assert legacy_workspace_selection["reason"] == "category_full"


def test_workspace_synthesis_groups_repeated_questions_without_dropping_source_refs():
    workspace = GlobalWorkspace()
    for episode in ("episode-a", "episode-b", "episode-c"):
        for index, limitation in enumerate(("measurement missing", "priors unvalidated", "score uncalibrated")):
            workspace.record_uncertainty(
                source_type="decision_reasoning_limit",
                source_module="intention_reasoner",
                source_ref=f"{episode}:uncertainty:{index}",
                question=f"Which sequence advances {episode}?",
                evidence=limitation,
                salience=0.65,
            )
    workspace.record_uncertainty(
        source_type="user_exchange:open_question",
        source_module="semantic_extractor", source_ref="turn-user",
        turn_id="turn-user", question="What remains unresolved?", salience=0.9,
    )
    fragment = _global_workspace_uncertainty_fragment(workspace.get_state())
    budget = PromptContextBudget(path="unused-test-grouped-budget.json")
    budget.add("epistemic_context", "global_workspace_uncertainty", fragment)
    budget.assemble()
    selection = budget.selection_receipt("epistemic_context", "global_workspace_uncertainty")

    assert "10 records, 4 questions, 2 origins" in fragment
    assert "decision_reasoning_limit/intention_reasoner×9" in fragment
    assert 'shared question prefix="Which sequence advances episode-"' in fragment
    assert "a? [refs=episode-a:uncertainty:{0,1,2}]" in fragment
    assert "b? [refs=episode-b:uncertainty:{0,1,2}]" in fragment
    assert "c? [refs=episode-c:uncertainty:{0,1,2}]" in fragment
    assert "turn-user" in fragment
    assert selection["selected"] is True


def test_large_workspace_uncertainty_compacts_without_resolving_or_hiding_origins():
    workspace = GlobalWorkspace()
    topics = (
        "relational understanding", "cognitive architecture", "reasoning coherence",
        "knowledge integration", "capability development", "memory continuity",
        "semantic grounding",
    )
    for episode, topic in enumerate(topics):
        for index in range(3):
            workspace.record_uncertainty(
                source_type="decision_reasoning_limit",
                source_module="intention_reasoner",
                source_ref=f"reason-{hashlib.sha256(f'{episode}/{index}'.encode()).hexdigest()[:24]}",
                question=f"Which sequence is most likely to make grounded progress on: {topic}?",
                evidence=f"open limitation {index}",
                salience=0.65,
            )
    workspace.record_uncertainty(
        source_type="user_exchange:query_about_ongoing_state",
        source_module="semantic_extractor",
        source_ref="turn-user-source",
        turn_id="turn-user-source",
        question="What uncertainties are being tracked?",
        salience=0.9,
    )

    state = workspace.get_state()
    fragment = _global_workspace_uncertainty_fragment(state)
    budget = PromptContextBudget(path="unused-test-large-uncertainty.json")
    budget.add("self_evidence", "grounded_identity", "i" * (76 * 4))
    budget.add("epistemic_context", "global_workspace_uncertainty", fragment)
    # Mirror the live turn's current selection pressure. Lower-priority
    # context may yield, but both the focus and the source synthesis must fit.
    budget.add("self_state", "self_model", "s" * (169 * 4))
    budget.add("self_correction", "self_correction", "c" * (77 * 4))
    budget.add("identity", "identity", "n" * (181 * 4))
    budget.add("cognitive_pressure", "energy_and_arbitration", "p" * (72 * 4))
    budget.add("cognitive_pressure", "global_workspace", "w" * (46 * 4))
    budget.add("attention", "attention", "a" * (77 * 4))
    budget.add("memory_active", "inner_monologue", "m" * (87 * 4))
    budget.add("skills", "skill_registry", "k" * (52 * 4))
    budget.assemble()

    uncertainty_receipt = budget.selection_receipt(
        "epistemic_context", "global_workspace_uncertainty",
    )
    focus_receipt = budget.selection_receipt("cognitive_pressure", "global_workspace")
    all_refs = {item["source_ref"] for item in state.uncertainty_sources if item["status"] == "open"}

    assert len(state.uncertainty_sources) == 22
    assert "22 independent records, 8 questions, 2 origins" in fragment
    assert "decision_reasoning_limit/intention_reasoner×21" in fragment
    assert "user_exchange:query_about_ongoing_state/semantic_extractor×1" in fragment
    assert "cognitive architecture" in fragment
    assert "all remain open" in fragment
    assert "Exact refs remain in the canonical ledger and turn receipt" in fragment
    assert all(
        item["source_ref"] not in fragment
        for item in state.uncertainty_sources
        if item["source_type"] == "decision_reasoning_limit"
    )
    assert "turn-user-source" in all_refs
    assert uncertainty_receipt["selected"] is True
    assert uncertainty_receipt["reason"] == "budget_ok"
    assert focus_receipt["selected"] is True
    assert budget._total_used <= 900


def test_workspace_uncertainty_synthesis_survives_full_prompt_budget_pressure():
    workspace = GlobalWorkspace()
    for episode in ("episode-a", "episode-b", "episode-c"):
        for index, limitation in enumerate(("measurement missing", "priors unvalidated", "score uncalibrated")):
            workspace.record_uncertainty(
                source_type="decision_reasoning_limit",
                source_module="intention_reasoner",
                source_ref=f"{episode}:uncertainty:{index}",
                question=f"Which sequence is most likely to make grounded progress on: {episode}?",
                evidence=limitation,
                salience=0.65,
            )
    workspace.record_uncertainty(
        source_type="user_exchange:open_question",
        source_module="semantic_extractor", source_ref="turn-user",
        turn_id="turn-user", question="What remains unresolved?", salience=0.9,
    )
    fragment = _global_workspace_uncertainty_fragment(workspace.get_state())
    budget = PromptContextBudget(path="unused-test-full-budget.json")
    # Mirror the real assembly priorities: higher-priority factual context,
    # the reserved uncertainty slot, then other cognitive context competing
    # for the hard total cap.
    budget.add("factual_telemetry", "factual_context", "x" * (480 * 4))
    budget.add("epistemic_context", "global_workspace_uncertainty", fragment)
    budget.add("self_evidence", "grounded_identity", "x" * (120 * 4))
    budget.add("self_correction", "self_correction", "x" * (120 * 4))
    budget.add("self_state", "self_model", "x" * (180 * 4))
    budget.assemble()

    receipt = budget.selection_receipt("epistemic_context", "global_workspace_uncertainty")
    assert receipt["selected"] is True
    assert receipt["reason"] == "budget_ok"
    assert "10 records, 4 questions, 2 origins" in fragment


def test_workspace_reference_prefix_compression_is_lossless():
    refs = [f"reason-abc123:uncertainty:{i}" for i in range(3)]
    compact = _compress_workspace_source_refs(refs)
    assert compact == "refs=reason-abc123:uncertainty:{0,1,2}"
    prefix, suffixes = compact.removeprefix("refs=").split("{", 1)
    expanded = [prefix + suffix for suffix in suffixes.rstrip("}").split(",")]
    assert expanded == refs


def test_workspace_question_prefix_compression_is_exact_and_language_agnostic():
    questions = [
        "Welche Quelle ist fuer den Plan: Erinnerung?",
        "Welche Quelle ist fuer den Plan: Absicht?",
    ]
    prefix = _common_workspace_text_prefix(questions)
    assert prefix == "Welche Quelle ist fuer den Plan: "
    assert [prefix + value[len(prefix):] for value in questions] == questions


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
