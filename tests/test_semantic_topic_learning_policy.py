from types import SimpleNamespace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from cognition.cognitive_organism import CognitiveOrganism
from cognition.persona_bridge import (
    _resolve_semantic_extractor_llm_fn,
    _semantic_turn_kind_for_route,
)
from cognition.semantic_extractor import SemanticExtractor
from cognition.persona_bridge import PersonaBridge
from managers.user_manager import UserManager


def _organism_stub():
    organism = Mock()
    organism._loop = SimpleNamespace(
        _world_self_dynamics=None,
        _resource_economy=None,
        _consequence_model=None,
        _auto_experiment=None,
    )
    organism.energy.mode.return_value = "normal"
    organism.energy.level.return_value = 0.7
    organism.ai_system.emotional_state.overall_arousal = 0.3
    organism.meta_cognition.post_response_eval.return_value = None
    organism.homeostasis.last_report.return_value = None
    organism.workspace = object()
    organism._semantic_extractor = Mock()
    return organism


def test_semantic_extractor_prefers_external_history_free_llm():
    configured = lambda prompt: f"configured:{prompt}"
    fallback = lambda prompt: f"fallback:{prompt}"

    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(_simple_llm_fn=configured), fallback,
    ) is fallback
    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(), fallback,
    ) is fallback
    assert _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(_simple_llm_fn=configured), None,
    ) is configured
    assert _resolve_semantic_extractor_llm_fn(SimpleNamespace(), None) is None


def test_semantic_learning_prompt_contains_user_input_but_not_assistant_response():
    prompts = []
    extractor = SemanticExtractor(
        semantic_memory=Mock(),
        llm_fn=lambda prompt: prompts.append(prompt) or '{"turn_kind":"topic"}',
    )

    extractor._parse(
        "Explain the cognitive memory architecture.",
        "ASSISTANT_ONLY_SECRET: Lumina claims Fred prefers topic X.",
    )

    assert len(prompts) == 1
    assert "Explain the cognitive memory architecture." in prompts[0]
    assert "ASSISTANT_ONLY_SECRET" not in prompts[0]
    assert "Lumina claims Fred prefers topic X" not in prompts[0]


def test_profile_claim_extraction_is_multilingual_and_requires_verbatim_evidence():
    message = "Ich bevorzuge kurze Antworten."
    payload = {
        "turn_kind": "topic",
        "goal_signal": "none",
        "concepts": [{"name": "kurze Antworten", "evidence": "kurze Antworten"}],
        "relations": [],
        "profile_claims": [
            {
                "category": "preference",
                "value": "kurze Antworten",
                "evidence": message,
                "assertion": "explicit_first_person",
                "durability": "durable",
            },
            {
                "category": "interest",
                "value": "Quantenphysik",
                "evidence": "Ich interessiere mich für Quantenphysik.",
                "assertion": "explicit_first_person",
                "durability": "durable",
            },
            {
                "category": "characteristic",
                "value": "müde",
                "evidence": "Ich bin müde.",
                "assertion": "explicit_first_person",
                "durability": "durable",
            },
        ],
        "dominant_topic": "kurze Antworten",
        "cognitive_load": 0.1,
    }
    extractor = SemanticExtractor(
        semantic_memory=Mock(), llm_fn=lambda _prompt: json.dumps(payload),
    )

    parsed = extractor._parse_with_profile(message, "assistant response is excluded")

    assert parsed[7] == [{
        "category": "preference",
        "value": "kurze Antworten",
        "evidence": message,
        "assertion": "explicit_first_person",
        "durability": "durable",
    }]


def test_semantic_profile_callback_persists_only_grounded_claim_with_turn_provenance():
    message = "Je préfère des réponses concises."
    claim = {
        "category": "preference",
        "value": "des réponses concises",
        "evidence": message,
        "assertion": "explicit_first_person",
        "durability": "durable",
    }
    payload = {
        "turn_kind": "topic",
        "goal_signal": "none",
        "concepts": [{"name": "réponses concises", "evidence": "réponses concises"}],
        "relations": [],
        "profile_claims": [claim],
        "dominant_topic": "réponses concises",
        "cognitive_load": 0.1,
    }
    with TemporaryDirectory() as directory:
        manager = UserManager(Path(directory) / "users.json")
        profile = manager.create("Fred")
        extractor = SemanticExtractor(
            semantic_memory=Mock(), llm_fn=lambda _prompt: json.dumps(payload),
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._record_turn_stage = Mock()
        extraction_receipts = []

        def persist_profile_claim(receipt):
            extraction_receipts.append(receipt)
            return bridge._record_semantic_topic_extraction(
                receipt,
                "turn-profile-1",
                user_id=profile.id,
                source_message=message,
                learn_profile=True,
            )

        with patch("managers.user_manager.user_manager", manager):
            profile_future = extractor.extract_async(
                message, "The assistant text is not profile evidence.",
                observation_role="user_topic",
                turn_id="turn-profile-1",
                completion_callback=persist_profile_claim,
                turn_kind_hint="topic",
            )
            profile_receipt = profile_future.result(timeout=3)
        reloaded = UserManager(Path(directory) / "users.json")

    persisted = reloaded.get(profile.id)
    extraction_receipt = extraction_receipts[0]
    assert extraction_receipt["profile_claims_status"] == "grounded_candidates"
    assert profile_receipt["status"] == "updated"
    assert profile_receipt["persisted"] is True
    assert persisted.preferences == ["des réponses concises"]
    fact_key = next(iter(persisted.profile_fact_provenance["preference"]))
    assert persisted.profile_fact_provenance["preference"][fact_key][0]["turn_id"] == "turn-profile-1"
    assert bridge._record_turn_stage.call_args_list[0].args[:2] == (
        "semantic_topic_extraction", "completed",
    )
    assert bridge._record_turn_stage.call_args_list[1].args[:2] == (
        "human_profile_learning", "updated",
    )
    assert bridge._record_turn_stage.call_args_list[1].kwargs["consumes"] == (
        "turn_input", "semantic_topic_extraction",
    )


def test_semantic_profile_learning_skips_guest_missing_turn_and_opt_out():
    claim = {
        "category": "interest", "value": "la botanique",
        "evidence": "Je m'intéresse à la botanique.",
        "assertion": "explicit_first_person", "durability": "durable",
    }
    with TemporaryDirectory() as directory:
        manager = UserManager(Path(directory) / "users.json")
        profile = manager.create("Fred")
        missing_turn = manager.learn_from_evidence_claims(
            profile.id, [claim], source_message=claim["evidence"], return_receipt=True,
        )
        invalid = manager.learn_from_evidence_claims(
            profile.id, [claim], source_message="Maybe Fred likes botany.",
            source_turn_id="turn-invalid", return_receipt=True,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._record_turn_stage = Mock()
        with patch("managers.user_manager.user_manager", manager):
            bridge._record_semantic_topic_extraction(
                {
                    "status": "completed", "turn_id": "turn-other",
                    "source_message_sha256": "not-the-message",
                    "profile_claims_status": "grounded_candidates",
                    "profile_claims": [claim],
                },
                "turn-opt-out", user_id=profile.id,
                source_message=claim["evidence"], learn_profile=False,
            )
            bridge._record_semantic_topic_extraction(
                {
                    "status": "completed", "turn_id": "turn-other",
                    "source_message_sha256": "not-the-message",
                    "profile_claims_status": "grounded_candidates",
                    "profile_claims": [claim],
                },
                "turn-opt-out", user_id=profile.id,
                source_message=claim["evidence"], learn_profile=True,
            )

    assert missing_turn["status"] == "skipped_missing_source_provenance"
    assert invalid["status"] == "no_grounded_profile_claim"
    assert profile.interests == []
    assert bridge._record_turn_stage.call_args_list[-1].args[:2] == (
        "human_profile_learning", "source_provenance_mismatch",
    )


def test_semantic_extractor_future_resolves_to_profile_callback_receipt():
    payload = {
        "turn_kind": "topic",
        "goal_signal": "none",
        "concepts": [],
        "relations": [],
        "profile_claims": [],
        "dominant_topic": "",
        "cognitive_load": 0.1,
    }
    extractor = SemanticExtractor(
        semantic_memory=Mock(), llm_fn=lambda _prompt: json.dumps(payload),
    )
    future = extractor.extract_async(
        "A substantive question about memory.", "Answer.",
        turn_id="turn-profile-future",
        turn_kind_hint="topic",
        completion_callback=lambda _receipt: {
            "status": "no_grounded_profile_claim",
            "persisted": False,
        },
    )

    result = future.result(timeout=3)

    assert result["status"] == "no_grounded_profile_claim"
    assert result["persisted"] is False


def test_semantic_worker_resolves_unexpected_failure_and_processes_next_turn():
    extractor = SemanticExtractor(semantic_memory=Mock())
    calls = 0

    def fail_once_then_succeed(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("unexpected parser boundary failure")
        return {
            "type": "semantic_extraction_receipt",
            "status": "completed",
            "turn_id": str(args[5]),
            "source_message_sha256": "ok",
            "profile_claims": [],
            "profile_claims_status": "no_grounded_claim",
        }

    extractor._extract = fail_once_then_succeed
    failed = extractor.extract_async(
        "first turn", "answer", turn_id="turn-worker-failure",
    )
    failure_receipt = failed.result(timeout=3)

    recovered = extractor.extract_async(
        "second turn", "answer", turn_id="turn-worker-recovery",
    )
    recovered_receipt = recovered.result(timeout=3)

    assert failure_receipt["status"] == "failed"
    assert failure_receipt["learning_status"] == "worker_exception"
    assert failure_receipt["turn_id"] == "turn-worker-failure"
    assert failure_receipt["profile_claims_status"] == "unavailable"
    assert recovered_receipt["status"] == "completed"
    assert recovered_receipt["turn_id"] == "turn-worker-recovery"


def test_semantic_learning_marks_provider_contention_for_queue_retry():
    class Manager:
        def __init__(self):
            self.calls = 0

        def generate_bare(self, prompt):
            return "legacy path must not run"

        def generate_bare_result(self, prompt, **kwargs):
            self.calls += 1
            assert kwargs["_audit_origin"] == "cognition.semantic_extractor._parse"
            if self.calls == 1:
                return {
                    "status": "deferred",
                    "reason": "interactive turn active",
                    "provider_call_count": 0,
                }
            return {"status": "ok", "text": '{"turn_kind":"topic"}'}

    manager = Manager()
    learning_fn = _resolve_semantic_extractor_llm_fn(
        SimpleNamespace(), manager.generate_bare,
    )

    try:
        learning_fn("extract from completed exchange")
    except RuntimeError as exc:
        assert getattr(exc, "semantic_learning_deferred", False) is True
    else:
        raise AssertionError("provider contention was not returned to the semantic queue")
    assert manager.calls == 1
    manager.calls = 0
    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=learning_fn)
    try:
        extractor._parse("A durable concept from this message", "answer")
    except RuntimeError as exc:
        assert getattr(exc, "semantic_learning_deferred", False) is True
    else:
        raise AssertionError("provider deferral incorrectly fell back to lexical extraction")
    manager.calls = 0
    receipt = extractor._extract(
        "A durable concept from this message", "answer", None, None,
        "user_topic", "turn-deferred", None, "topic",
    )
    assert receipt["status"] == "deferred"
    assert receipt["learning_status"] == "deferred_provider_busy"


def test_deferred_semantic_turn_yields_worker_to_next_queued_turn():
    class ImmediateTimer:
        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False

        def start(self):
            self.callback()

    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=None)
    finished = []

    def callback_for(turn):
        return lambda receipt: finished.append((turn, receipt["status"]))

    extractor._extract = Mock(side_effect=[
        {"status": "deferred", "learning_status": "deferred_provider_busy"},
        {"status": "completed", "learning_status": "accepted_topic_turn"},
        {"status": "completed", "learning_status": "accepted_decision_turn"},
    ])
    extractor._queue.put(("first", "answer", None, None, "user_topic", "turn-1", callback_for("turn-1"), "topic", 0))
    extractor._queue.put(("second", "answer", None, None, "user_topic", "turn-2", callback_for("turn-2"), "decision", 0))
    extractor._worker_running = True

    with patch("cognition.semantic_extractor.threading.Timer", ImmediateTimer):
        extractor._drain_queue()

    assert extractor._extract.call_args_list[1].args[0] == "second"
    assert extractor._extract.call_args_list[2].args[0] == "first"
    assert finished == [("turn-2", "completed"), ("turn-1", "completed")]
    assert extractor._queue.unfinished_tasks == 0


def test_deferred_semantic_turn_exhaustion_is_reported_and_worker_continues():
    class ImmediateTimer:
        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False

        def start(self):
            self.callback()

    extractor = SemanticExtractor(semantic_memory=Mock(), llm_fn=None)
    finished = []
    extractor._extract = Mock(return_value={
        "status": "deferred", "learning_status": "deferred_provider_busy",
    })
    item = ("user", "answer", None, None, "user_topic", "turn-1", finished.append, "topic", 0)
    extractor._queue.put(item)
    extractor._worker_running = True

    with patch("cognition.semantic_extractor._MAX_DEFERRED_RETRIES", 1), \
         patch("cognition.semantic_extractor.threading.Timer", ImmediateTimer):
        extractor._drain_queue()

    assert extractor._extract.call_count == 2
    assert finished == [{
        "status": "failed",
        "learning_status": "deferred_retry_exhausted",
        "retry_exhausted": True,
    }]
    assert extractor._queue.unfinished_tasks == 0


def test_source_recall_is_classified_by_semantic_extractor_not_a_lexical_gate():
    organism = _organism_stub()

    receipt = CognitiveOrganism._post_interaction(
        organism,
        user_input=(
            "Rappelle uniquement la consigne que je t’ai donnée : "
            "poursuivre l’audit sans redémarrer Lumina après chaque correctif."
        ),
        response="Je ne trouve pas de source suffisamment précise.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="recall-control-turn",
    )

    organism._semantic_extractor.extract_async.assert_called_once()
    assert receipt["semantic_topic_learning"] == {
        "status": "queued",
        "turn_id": "recall-control-turn",
        "reason": "semantic_intent_classification",
    }


def test_ordinary_topic_turn_still_queues_semantic_learning():
    organism = _organism_stub()

    receipt = CognitiveOrganism._post_interaction(
        organism,
        user_input="Explain how memory retrieval supports the cognitive audit.",
        response="Retrieval supplies prior episodes for the current turn.",
        cycle_data={"emo_values": {}},
        decision=None,
        turn_id="ordinary-topic-turn",
    )

    organism._semantic_extractor.extract_async.assert_called_once_with(
        user_input="Explain how memory retrieval supports the cognitive audit.",
        response="Retrieval supplies prior episodes for the current turn.",
        workspace=organism.workspace,
        observation_role="user_topic",
        turn_id="ordinary-topic-turn",
        completion_callback=None,
        turn_kind_hint="",
        goal_commitment_candidate=False,
    )
    assert receipt["semantic_topic_learning"]["status"] == "queued"
    assert receipt["semantic_topic_learning"]["reason"] == "semantic_intent_classification"


def test_upstream_turn_kind_is_forwarded_without_disabling_topic_learning():
    organism = _organism_stub()

    with patch(
        "cognition.profile_flow.update_behavioral_user_profile",
        return_value={"status": "updated", "changed": True, "persisted": True},
    ) as update_profile:
        receipt = CognitiveOrganism._post_interaction(
            organism,
            user_input="How are you?",
            response="I am doing well.",
            cycle_data={"emo_values": {}},
            decision=None,
            turn_id="deterministic-social-turn",
            semantic_turn_kind_hint="social",
        )

    organism._semantic_extractor.extract_async.assert_called_once_with(
        user_input="How are you?",
        response="I am doing well.",
        workspace=organism.workspace,
        observation_role="user_topic",
        turn_id="deterministic-social-turn",
        completion_callback=None,
        turn_kind_hint="social",
        goal_commitment_candidate=False,
    )
    assert receipt["semantic_topic_learning"]["status"] == "queued"
    update_profile.assert_called_once()
    assert update_profile.call_args.kwargs["learn_semantic_profile"] is False


def test_closed_world_report_route_is_forwarded_as_non_topic_learning_act():
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=True,
    ) == "other"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=True,
        deterministic_affect_report=False,
        closed_world_report=True,
    ) == "retrieval"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=True,
        closed_world_report=True,
    ) == "social"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        goal_means_decision=True,
    ) == "decision"
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
    ) == ""
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        explicit_profile_learning_opt_out=True,
    ) == "instruction"


def test_response_revision_route_skips_reclassifying_an_instruction_as_a_topic():
    assert _semantic_turn_kind_for_route(
        explicit_memory_recall=False,
        deterministic_affect_report=False,
        closed_world_report=False,
        response_format_revision=True,
    ) == "instruction"
