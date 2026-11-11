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


def test_predictive_mind_does_not_compare_user_intent_with_response_register():
    from cognition.predictive_mind import PredictiveMind

    organism = _Organism()
    predictive = PredictiveMind(organism)
    prediction = predictive.predict({"user_text": "What is the battery level?"})
    predictive.store_response("The battery level is not available.")

    outcome = predictive.evaluate({"user_text": "What is the battery level?"})

    assert prediction.expected_intent == "question"
    assert outcome is None
    assert predictive.summary()["total_predictions"] == 1
    assert predictive.summary()["validated_predictions"] == 0
    assert predictive.stability_metrics()["validated_predictions"] == 0
    assert predictive.stability_metrics()["total_predictions"] == 1
    assert predictive.summary()["accuracy_status"] == "unmeasured_no_independent_outcome_labels"
    assert predictive.accuracy() == 0.5
    assert predictive.recent_error_level() is None
    assert len(predictive._surprise_window) == 0
    stability = predictive.stability_metrics()
    assert stability["health"] == "unmeasured"
    assert stability["surprise_index"] == 0.5
    assert stability["confirmation_bias"] == 0.5


def test_missing_prediction_outcome_does_not_trigger_self_revision_recovery():
    from types import SimpleNamespace
    from cognition.self_revision_engine import SelfRevisionEngine

    moment = SimpleNamespace(phi=0.60)
    organism = SimpleNamespace(self_moment=SimpleNamespace(current=moment))
    engine = SelfRevisionEngine()
    engine.state.recent_errors.extend([0.0, 0.0, 0.0])

    events = engine.revise(organism, None)

    assert events == []
    assert moment.phi == 0.60


def test_unmeasured_prediction_error_does_not_raise_observatory_strangeness():
    from types import SimpleNamespace
    from cognition.cognitive_observatory import CognitiveObservatory

    class _PredictiveMind:
        def stability_metrics(self):
            return {
                "measurement_status": "unmeasured_no_independent_outcome_labels",
                "surprise_index": 0.99,
                "novelty_rate": 0.0,
            }

    monitor = object.__new__(CognitiveObservatory)
    monitor._o = SimpleNamespace(predictive_mind=_PredictiveMind())
    notes = []

    score = monitor._compute_strangeness(0.0, 0.0, 0.0, 0.0, notes)

    assert score == 0.0
    assert notes == []


def test_memory_breadth_audit_excludes_legacy_unvalidated_samples(tmp_path):
    import json
    from cognition.memory_breadth_audit import MemoryBreadthAudit

    audit_path = tmp_path / "memory_breadth_audit.json"
    legacy = {
        "pending": [{"widened": True, "pre_error_level": 0.0, "turn_id": 1}],
        "widened_deltas": [0.0, 0.2],
        "baseline_deltas": [0.0],
    }
    audit_path.write_text(json.dumps(legacy), encoding="utf-8")
    audit = MemoryBreadthAudit(str(audit_path))

    class _UnmeasuredPredictor:
        def summary(self):
            return {"validated_predictions": 0, "accuracy_status": "unmeasured_no_independent_outcome_labels"}

        def recent_error_level(self):
            return 0.0

    result = audit.record_and_review(True, _UnmeasuredPredictor())
    summary = audit.summary()

    assert result["reviewed"] == 0
    assert result["status"] == "unmeasured"
    assert summary["measurement_status"] == "unmeasured_no_independent_outcome_labels"
    assert summary["widened_samples"] == 0
    assert summary["baseline_samples"] == 0
    assert summary["legacy_unvalidated_samples_excluded"] == {
        "pending": 1, "widened": 2, "baseline": 1
    }
    assert json.loads(audit_path.read_text(encoding="utf-8")) == legacy


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
