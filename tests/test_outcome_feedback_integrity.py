import ast
from pathlib import Path
from types import SimpleNamespace

from cognition.pressure_system import PressureSystem


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
