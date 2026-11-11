from pathlib import Path
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
    )

    reloaded = UserManager(path=users_path)
    next_turn_id = reloaded.resolve_interaction_user_id("default")
    next_prompt_context = reloaded.prompt_context_for(next_turn_id)

    assert receipt["status"] == "updated"
    assert receipt["changed"] is True
    assert first_turn_id == next_turn_id == profile.id
    assert "Preferences: concise technical answers." in next_prompt_context


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
