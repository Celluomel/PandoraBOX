from pathlib import Path

from cognition.cognitive_restructuring_engine import CognitiveRestructuringEngine
from cognition.cognitive_validator import CognitiveArchitectureMonitor, CognitiveValidator
from cognition.self_correction_engine import SelfCorrectionEngine


class _Energy:
    def level(self):
        return 0.7

    def mode(self):
        return "normal"


class _GoalEcology:
    class _Drive:
        name = "curiosity"

    def dominant_drive(self, _energy):
        return self._Drive()


class _Organism:
    energy = _Energy()
    goal_ecology = _GoalEcology()
    workspace = None
    _loop = None

    def _read_emotion_state(self):
        return "curious"


def test_lexical_validator_is_labeled_as_nonsemantic_and_has_no_workspace_effect():
    organism = _Organism()
    validator = CognitiveValidator(organism)

    result = validator.validate("A plain factual answer.")

    assert result.measurement_scope == "lexical_surface_proxy_not_semantic_quality"
    assert validator.summary()["measurement_scope"] == result.measurement_scope
    assert organism.workspace is None
    assert organism._loop is None


def test_surface_heuristic_does_not_change_architecture_health_score():
    class _Validator:
        def summary(self):
            return {"misalignment_rate": 1.0}

    monitor = CognitiveArchitectureMonitor(_Organism(), _Validator())
    monitor._check_thought_stream = lambda: 0.8
    monitor._check_workspace = lambda: 0.8
    monitor._o.predictive_mind = type("_PM", (), {
        "summary": staticmethod(lambda: {"total_predictions": 0, "accuracy": 1.0})
    })()
    monitor._check_event_bus = lambda: 0.8
    monitor._check_inner_monologue = lambda: 0.8

    report = monitor._build_report()

    assert report.component_scores["surface_alignment_heuristic"] == 0.0
    assert report.component_scores["intent_classification_proxy"] == 0.0
    assert report.overall_health == 0.8
    assert report.measurement_scope == "activity_and_availability_proxies_not_output_quality"
    assert any("not a semantic-quality measurement" in warning for warning in report.warnings)


def test_predictive_mind_empty_history_is_not_reported_as_perfect_accuracy():
    organism = _Organism()
    organism.predictive_mind = type("_PM", (), {
        "summary": staticmethod(lambda: {"total_predictions": 0, "accuracy": 1.0}),
    })()
    monitor = CognitiveArchitectureMonitor(organism, CognitiveValidator(organism))

    assert monitor._check_predictive_mind() == 0.0


def test_low_activity_monitor_result_does_not_broadcast_cognitive_claim():
    class _Workspace:
        def __init__(self):
            self.broadcasts = []

        def broadcast(self, **kwargs):
            self.broadcasts.append(kwargs)

    organism = _Organism()
    organism.workspace = _Workspace()
    monitor = CognitiveArchitectureMonitor(organism, CognitiveValidator(organism))
    monitor._check_thought_stream = lambda: 0.0
    monitor._check_workspace = lambda: 0.0
    monitor._check_predictive_mind = lambda: 0.0
    monitor._check_event_bus = lambda: 0.0
    monitor._check_inner_monologue = lambda: 0.0

    report = monitor.check(force=True)

    assert report.critical is True
    assert organism.workspace.broadcasts == []


def test_historical_event_bus_volume_does_not_count_as_current_activity():
    class _EventBus:
        def recent(self, _limit):
            return []

        def summary(self):
            return {"total_emitted": 10_000}

    organism = _Organism()
    organism.event_bus = _EventBus()
    monitor = CognitiveArchitectureMonitor(organism, CognitiveValidator(organism))

    assert monitor._check_event_bus() == 0.0


def test_restructuring_does_not_count_silence_as_success_or_failure(tmp_path):
    engine = CognitiveRestructuringEngine(None, str(Path(tmp_path) / "restructure.json"))
    engine._state["active_plan"] = {
        "trial": {"samples": 0, "successes": 0},
    }

    engine.observe_turn(correction=None, score=None)

    assert engine._state["active_plan"]["trial"] == {"samples": 0, "successes": 0}


def test_self_correction_needs_explicit_positive_feedback_to_confirm_pending_rule(tmp_path):
    engine = SelfCorrectionEngine(str(Path(tmp_path) / "rules.json"))
    learned = engine.observe("That was wrong; you missed the constraint.", "Response")
    assert learned["feedback_kind"] == "correction"

    engine.observe("What is the weather today?", "It is sunny.")
    stored = engine._rules[0]
    assert stored["successful_turns"] == 0
    assert stored["pending"] is True

    engine.observe("That is correct.", "Thanks.")
    assert stored["successful_turns"] == 1
    assert stored["pending"] is False


def test_word_substring_does_not_count_as_feedback(tmp_path):
    engine = SelfCorrectionEngine(str(Path(tmp_path) / "rules.json"))
    assert engine.observe("Yesterday was sunny.", "No issue.") is None
    assert engine.status()["rules"] == 0
