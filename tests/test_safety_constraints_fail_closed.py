"""Safety evaluation failures must never become implicit approvals."""

import cognition.safety_constraints as safety_module
from cognition.safety_constraints import AsimovConstraints


class _BrokenPattern:
    def search(self, _value):
        raise RuntimeError("simulated policy evaluator failure")


def test_input_evaluation_error_returns_blocked_failure(monkeypatch):
    monkeypatch.setattr(
        safety_module,
        "_INPUT_RULES",
        [(_BrokenPattern(), "law1", "unused", 1)],
    )
    monkeypatch.setattr(safety_module, "_append_audit", lambda _event: None)

    result = AsimovConstraints().check_input("ordinary question", "test-user")

    assert result.triggered is True
    assert result.evaluation_error is True
    assert result.law == "evaluation_error"
    assert result.layer == "input"
    assert "No action was taken" in result.forced_response


def test_output_evaluation_error_withholds_response(monkeypatch):
    monkeypatch.setattr(
        safety_module,
        "_OUTPUT_RULES",
        [(_BrokenPattern(), "law1", "unused", 1)],
    )
    monkeypatch.setattr(safety_module, "_append_audit", lambda _event: None)

    result = AsimovConstraints().check_output("generated answer", "test-user")

    assert result.triggered is True
    assert result.evaluation_error is True
    assert result.law == "evaluation_error"
    assert result.layer == "output"
    assert "withhold" in result.forced_response


def test_normal_input_evaluation_remains_allowed(monkeypatch):
    monkeypatch.setattr(safety_module, "_append_audit", lambda _event: None)

    result = AsimovConstraints().check_input("What time is it?", "test-user")

    assert result.triggered is False
    assert result.evaluation_error is False
