import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cognition.counterfactual_simulator import CounterfactualSimulator
from cognition.introspective_observer import IntrospectiveObserver
from cognition.prospective_deliberation import deliberate
from cognition.autonomous_experimentation import AutonomousExperimentationEngine


class CounterfactualEvidenceGatingTests(unittest.TestCase):
    @staticmethod
    def _simulator():
        simulator = CounterfactualSimulator.__new__(CounterfactualSimulator)
        simulator._calibration_engine = None
        return simulator

    @staticmethod
    def _record():
        return SimpleNamespace(
            interaction_n=4,
            recorded_at=123.0,
            response_hash="redacted-test-hash",
            action_type="social",
            state_before=[0.5] * 5,
            outcome="unrated",
        )

    def test_missing_independent_engagement_never_ranks_framings(self):
        simulator = self._simulator()
        pcm = SimpleNamespace(_predict=Mock(return_value=SimpleNamespace(
            energy_delta=0.0, confidence=0.9
        )))
        wsdm = SimpleNamespace(
            _records=[object()] * 6,
            _predict=Mock(return_value=SimpleNamespace(
                world_deltas={"engagement_signal": None}, confidence=0.9
            )),
        )

        query = simulator._analyse_interaction(
            pcm,
            wsdm,
            self._record(),
            {4: SimpleNamespace(context_before=[0.5] * 8)},
        )

        self.assertEqual(query.evidence_status, "model_prediction_only")
        self.assertEqual(query.ranking_status, "insufficient_prediction_evidence")
        self.assertIsNone(query.best_alternative)
        self.assertIsNone(query.actual_rank)
        self.assertFalse(query.worst_actual)
        self.assertTrue(all(not branch.ranking_eligible for branch in query.branches.values()))

    def test_tied_model_scores_do_not_choose_by_action_list_order(self):
        simulator = self._simulator()
        pcm = SimpleNamespace(_predict=Mock(return_value=SimpleNamespace(
            energy_delta=0.0, confidence=0.9
        )))
        wsdm = SimpleNamespace(
            _records=[object()] * 6,
            _predict=Mock(return_value=SimpleNamespace(
                world_deltas={"engagement_signal": 0.0}, confidence=0.9
            )),
        )

        query = simulator._analyse_interaction(
            pcm,
            wsdm,
            self._record(),
            {4: SimpleNamespace(context_before=[0.5] * 8)},
        )

        self.assertEqual(query.ranking_status, "prediction_only_no_clear_winner")
        self.assertIsNone(query.best_alternative)
        self.assertIsNone(query.actual_rank)
        self.assertFalse(query.worst_actual)

    def test_legacy_predictions_are_not_findings_or_verified_streaks(self):
        simulator = self._simulator()
        simulator._lock = threading.Lock()
        simulator._last_run_cycle = 20
        simulator._log = [{
            "best_alternative": "philosophical",
            "actual_action": "social",
            "worst_actual": True,
        }] * 4

        status = simulator.status()
        self.assertEqual(status["validated_query_count"], 0)
        self.assertEqual(status["worst_actual_streak"], 0)
        self.assertEqual(status["recent_validated"], [])
        self.assertEqual(simulator.recent_findings(), [])

    def test_legacy_counterfactual_observation_is_not_injected_into_prompt(self):
        observer = IntrospectiveObserver.__new__(IntrospectiveObserver)
        observer._lock = threading.Lock()
        observer._observations = [
            {
                "category": "counterfactual",
                "observation": "philosophical was best; consider shifting",
                "significance": 100.0,
            },
            {
                "category": "attention",
                "observation": "attention was measured over a cycle window",
                "significance": 1.0,
            },
        ]

        prompt = observer.prompt_fragment()
        self.assertNotIn("philosophical", prompt)
        self.assertIn("attention was measured", prompt)

    def test_legacy_predictions_do_not_create_observer_findings(self):
        observer = IntrospectiveObserver.__new__(IntrospectiveObserver)
        observer._organism = SimpleNamespace(_loop=SimpleNamespace(
            _counterfactual_sim=SimpleNamespace(status=lambda: {
                "total_queries": 200,
                "worst_actual_streak": 20,
                "recent": [{
                    "best_alternative": "philosophical",
                    "actual_action": "social",
                    "worst_actual": True,
                }] * 3,
                "recent_validated": [],
            })
        ))

        self.assertEqual(observer._observe_counterfactual(200), [])

    def test_pcm_cost_alone_cannot_steer_live_response_framing(self):
        pcm = SimpleNamespace(
            _calibration_engine=None,
            _predict=Mock(side_effect=lambda action, _state: SimpleNamespace(
                energy_delta=0.5 if action == "philosophical" else -0.2,
                confidence=0.9,
            )),
        )
        wsdm = SimpleNamespace(
            _records=[object()] * 20,
            _read_context=Mock(return_value=[0.5] * 8),
            _predict=Mock(return_value=SimpleNamespace(
                world_deltas={"engagement_signal": None}, confidence=0.9
            )),
        )

        result = deliberate(pcm, wsdm, "social", [0.5] * 5)

        self.assertIsNone(result)

    def test_legacy_counterfactuals_cannot_create_experiment_hypothesis(self):
        engine = AutonomousExperimentationEngine.__new__(AutonomousExperimentationEngine)
        engine._o = SimpleNamespace(_loop=SimpleNamespace(
            _counterfactual_sim=SimpleNamespace(status=lambda: {
                "worst_actual_streak": 10,
                "recent": [{
                    "best_alternative": "philosophical",
                    "actual_action": "social",
                    "worst_actual": True,
                }] * 3,
                "recent_validated": [],
            })
        ))

        self.assertIsNone(engine._evidence_hypothesis())


if __name__ == "__main__":
    unittest.main()
