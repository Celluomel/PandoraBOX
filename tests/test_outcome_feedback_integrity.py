import ast
from pathlib import Path
from types import SimpleNamespace

from cognition.pressure_system import PressureSystem
from cognition.self_model import SelfModel


ROOT = Path(__file__).resolve().parents[1]


def _method_calls(path: str, method_name: str, owner: str, function_name: str) -> list[ast.Call]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == owner)
    method = next(
        node for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    )
    return [
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == method_name
    ]


def test_generated_response_style_does_not_score_drives_or_emotions():
    assert not _method_calls(
        "cognition/cognitive_organism.py", "record_satisfaction", "CognitiveOrganism",
        "_post_interaction",
    )
    assert not _method_calls(
        "cognition/persona_bridge.py", "record_satisfaction", "PersonaBridge",
        "_run_full_post_turn_lifecycle",
    )
    bridge = ast.parse((ROOT / "cognition/persona_bridge.py").read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.FunctionDef) and node.name == "_infer_emotion_from_response"
        for node in ast.walk(bridge)
    )


def test_interaction_contact_does_not_satiate_epistemic_uncertainty(tmp_path):
    pressure = PressureSystem(SimpleNamespace(), path=str(tmp_path / "pressure.json"))
    uncertainty_before = pressure.pressure("uncertainty")
    social_before = pressure.pressure("social")
    expression_before = pressure.pressure("expression")

    pressure.record_interaction()

    assert pressure.pressure("uncertainty") == uncertainty_before
    assert pressure.pressure("social") < social_before
    assert pressure.pressure("expression") < expression_before


def test_unrated_interaction_records_load_without_claiming_success(tmp_path):
    model = SelfModel(str(tmp_path / "self_model.json"))
    before_confidence = model.confidence
    before_capability = model.capabilities["conversation"]
    before_score = before_capability.score

    model.record_interaction(success=None, domain="conversation", load_delta=0.1)

    assert model.total_interactions == 1
    assert model.session_interactions == 1
    assert model.cognitive_load > 0.2
    assert model.confidence == before_confidence
    assert before_capability.score == before_score
    assert (before_capability.success, before_capability.failure) == (0, 0)


def test_only_explicit_outcome_changes_self_model_capability(tmp_path):
    model = SelfModel(str(tmp_path / "self_model.json"))
    before = model.capabilities["conversation"].score

    model.record_outcome(success=False, domain="conversation")

    assert model.capabilities["conversation"].failure == 1
    assert model.capabilities["conversation"].score < before
    assert model.total_interactions == 0


def test_response_processing_does_not_infer_outcome_from_affect_or_response_style():
    tree = ast.parse((ROOT / "cognition/ai_system.py").read_text(encoding="utf-8"))
    ai_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "EnhancedAISystem")
    post = next(node for node in ai_class.body if isinstance(node, ast.FunctionDef) and node.name == "_post_response_processing")
    feedback = next(node for node in ai_class.body if isinstance(node, ast.FunctionDef) and node.name == "receive_feedback")
    post_calls = [node for node in ast.walk(post) if isinstance(node, ast.Call)]
    feedback_calls = [node for node in ast.walk(feedback) if isinstance(node, ast.Call)]

    assert not any(
        isinstance(node.func, ast.Attribute) and node.func.attr in {"update_from_interaction", "update_from_feedback"}
        for node in post_calls
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "queue_experience"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value in {"creative_success", "positive_interaction", "negative_interaction"}
        for node in post_calls
    )
    assert any(
        isinstance(node.func, ast.Attribute) and node.func.attr == "record_outcome"
        for node in feedback_calls
    )
    policy_aliases = {
        target.id
        for node in ast.walk(feedback)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "getattr"
        and len(node.value.args) >= 2
        and isinstance(node.value.args[1], ast.Constant)
        and node.value.args[1].value == "update_from_interaction"
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert any(
        isinstance(node.func, ast.Name) and node.func.id in policy_aliases
        for node in feedback_calls
    )

    page = (ROOT / "pages/main_page.py").read_text(encoding="utf-8")
    assert "len(accumulated_text) > 10" not in page
    assert "_feedback_response" in page
    bubble_start = page.index("def _bubble(")
    bubble_end = page.index("# ── Network bubble", bubble_start)
    bubble_source = page[bubble_start:bubble_end]
    assert "_last_responses" not in bubble_source
    assert "response=text" in bubble_source
