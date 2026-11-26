import hashlib

from pathlib import Path
from unittest.mock import patch
import ast

from managers.user_manager import UserManager


def test_generic_brain_api_user_id_resolves_to_persisted_active_profile(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    manager.set_active(profile.id)

    assert manager.resolve_interaction_user_id("default") == profile.id
    assert manager.resolve_interaction_user_id(None) == profile.id
    assert manager.resolve_interaction_user_id(profile.id) == profile.id


def test_explicit_user_identity_is_never_replaced_by_active_profile(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    active = manager.create("Fred")
    manager.set_active(active.id)
    other = manager.create("Other")

    assert manager.resolve_interaction_user_id(other.id) == other.id


def test_default_user_resolves_to_guest_when_no_named_profile_is_active(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")

    assert manager.resolve_interaction_user_id("default") == manager.GUEST_ID


def test_profile_learning_is_persisted_and_available_to_the_next_prompt(tmp_path):
    users_path = Path(tmp_path) / "users.json"
    manager = UserManager(path=users_path)
    profile = manager.create("Fred")
    manager.set_active(profile.id)

    first_turn_id = manager.resolve_interaction_user_id("default")
    receipt = manager.learn_from_message(
        first_turn_id,
        "I prefer concise technical answers.",
        return_receipt=True,
        source_turn_id="profile-turn-1",
    )

    reloaded = UserManager(path=users_path)
    next_turn_id = reloaded.resolve_interaction_user_id("default")
    next_prompt_context = reloaded.prompt_context_for(next_turn_id)

    assert receipt["status"] == "updated"
    assert receipt["changed"] is True
    assert first_turn_id == next_turn_id == profile.id
    assert "User-stated preferences: concise technical answers" in next_prompt_context
    assert "turn profile-turn-1" in next_prompt_context


def test_profile_fact_provenance_is_persisted_and_rendered_as_source_link(tmp_path):
    users_path = Path(tmp_path) / "users.json"
    manager = UserManager(path=users_path)
    profile = manager.create("Fred")

    receipt = manager.learn_from_message(
        profile.id,
        "I prefer concise technical answers.",
        return_receipt=True,
        source_turn_id="turn-123",
    )
    prompt_context = manager.prompt_context_for(profile.id)
    reloaded = UserManager(path=users_path)
    persisted_profile = reloaded.get(profile.id)

    assert receipt["status"] == "updated"
    assert receipt["provenance_records"] == 1
    assert "explicit user statement: turn turn-123" in prompt_context
    assert "explicit_user_stated_entries=1" in prompt_context
    assert persisted_profile.profile_fact_provenance["preference"]


def test_provenanced_profile_fact_reader_excludes_legacy_values(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    profile.preferences.append("legacy unverified preference")
    manager._save()
    manager.learn_from_message(
        profile.id,
        "I prefer concise technical answers.",
        return_receipt=True,
        source_turn_id="profile-source-1",
    )

    facts = manager.provenanced_profile_facts_for(profile.id)

    assert len(facts) == 1
    assert facts[0]["category"] == "preference"
    assert facts[0]["value"] == "concise technical answers"
    assert facts[0]["source_turn_id"] == "profile-source-1"
    assert all("legacy" not in item["value"] for item in facts)


def test_profile_fact_source_digest_references_the_user_message_not_the_value(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    source_message = "I prefer concise technical answers."
    source_turn_id = "source-digest-turn"

    receipt = manager.learn_from_message(
        profile.id,
        source_message,
        return_receipt=True,
        source_turn_id=source_turn_id,
    )
    fact = manager.provenanced_profile_facts_for(profile.id)[0]

    assert receipt["status"] == "updated"
    assert fact["source_turn_id"] == source_turn_id
    assert fact["source_sha256"] == hashlib.sha256(source_message.encode("utf-8")).hexdigest()
    assert fact["source_sha256"] != hashlib.sha256(fact["value"].encode("utf-8")).hexdigest()


def test_legacy_profile_facts_are_excluded_until_reasserted(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    manager.set_active(profile.id)
    profile.preferences.append("concise technical answers")
    manager._save()

    prompt_context = manager.prompt_context_for(profile.id)
    assert "explicit_user_stated_entries=0" in prompt_context
    assert "legacy_unverified_entries=1" in prompt_context
    assert "legacy entries without a user source receipt are excluded" in prompt_context
    assert "concise technical answers" not in prompt_context
    assert "concise technical answers" not in manager.active_context_for_prompt()


def test_profile_provenance_requires_a_user_source_receipt(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    profile.preferences.append("concise answers")
    key = hashlib.sha256(b"concise answers").hexdigest()
    profile.profile_fact_provenance = {"preference": {key: [{"recorded_at": "today"}]}}

    summary = manager.profile_provenance_summary_for(profile.id)
    prompt_context = manager.prompt_context_for(profile.id)

    assert summary["explicit_user_stated_entries"] == 0
    assert summary["legacy_unverified_entries"] == 1
    assert "legacy_unverified_entries=1" in prompt_context
    assert "concise answers" not in prompt_context


def test_profile_display_name_is_not_claimed_as_an_explicit_user_fact(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")

    summary = manager.profile_provenance_summary_for(profile.id)
    prompt_context = manager.prompt_context_for(profile.id)

    assert summary["display_name_source"] == "source_not_recorded"
    assert "Profile display label" in prompt_context
    assert "source receipt not recorded" in prompt_context
    assert "not an explicit user-stated fact" in prompt_context


def test_legacy_profile_notes_are_not_injected_into_chat_prompt(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    profile.notes = "Unverified old note with private preference detail."
    manager._save()

    prompt_context = manager.prompt_context_for(profile.id)

    assert "Legacy profile notes exist" in prompt_context
    assert "Unverified old note with private preference detail" not in prompt_context


def test_profile_learning_does_not_claim_update_when_persistence_fails(tmp_path):
    manager = UserManager(path=Path(tmp_path) / "users.json")
    profile = manager.create("Fred")
    before_last_seen = profile.last_seen
    manager._save = lambda: None

    receipt = manager.learn_from_message(
        profile.id,
        "I prefer concise technical answers.",
        return_receipt=True,
    )

    assert receipt["status"] == "persistence_failed"
    assert receipt["changed"] is False
    assert profile.preferences == []
    assert profile.last_seen == before_last_seen


def test_profile_atomic_replace_failure_preserves_previous_file_and_cleans_temp(tmp_path):
    users_path = Path(tmp_path) / "users.json"
    manager = UserManager(path=users_path)
    profile = manager.create("Fred")
    before = users_path.read_bytes()

    with patch("managers.user_manager.os.replace", side_effect=OSError("simulated replace failure")):
        receipt = manager.learn_from_message(
            profile.id,
            "I prefer concise technical answers.",
            return_receipt=True,
            source_turn_id="atomic-write-test",
        )

    assert receipt["status"] == "persistence_failed"
    assert receipt["persisted"] is False
    assert users_path.read_bytes() == before
    assert list(tmp_path.glob("users.json.*.tmp")) == []


def test_brain_chat_route_uses_the_resolved_identity_for_both_stream_modes():
    source = Path(__file__).parents[1] / "brain.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "chat"
    )
    calls = [
        node for node in ast.walk(route)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_response_stream"
    ]

    assert len(calls) == 2
    assert all(
        any(isinstance(arg, ast.Name) and arg.id == "resolved_user_id" for arg in call.args)
        or any(
            keyword.arg == "user_id"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "resolved_user_id"
            for keyword in call.keywords
        )
        for call in calls
    )


def test_state_reports_prompt_budget_admission_without_claiming_model_attention():
    source = Path(__file__).parents[1] / "brain.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "organism_state"
    )
    assignment = next(
        node for node in ast.walk(route)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Subscript)
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "prompt_context_admission"
            for target in node.targets
        )
    )
    payload = assignment.value
    assert isinstance(payload, ast.Dict)
    fields = {
        key.value: value.value
        for key, value in zip(payload.keys, payload.values)
        if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)
    }
    assert fields["metric_scope"] == "prompt_budget_admission"
    assert fields["model_attention_measured"] is False
    assert fields["response_effect_measured"] is False
