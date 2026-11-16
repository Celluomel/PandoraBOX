import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cognition.counterfactual_simulator import CounterfactualQuery, CounterfactualSimulator
from cognition.intention_reasoner import IntentionReasoner
from cognition.prospective_deliberation import _score_candidate
from cognition.world_self_dynamics_model import DynamicsRecord, WorldSelfDynamicsModel


class WSDMEngagementEvidenceTests(unittest.TestCase):
    def test_concurrent_turn_outcomes_use_their_own_before_state(self):
        model = WorldSelfDynamicsModel.__new__(WorldSelfDynamicsModel)
        model._lock = threading.Lock()
        model._pending = None
        model._pending_by_turn = {}
        model.capture_context = Mock(side_effect=[
            [1.0] * 8, [2.0] * 8, [20.0] * 8, [10.0] * 8,
        ])
        model.record_observed_transition = Mock()

        model.record_context("analytical", "fred", 1, turn_id="turn-a")
        model.record_context("social", "peer", 2, turn_id="turn-b")
        model.record_outcome(user_id="peer", user_input="b", turn_id="turn-b")
        model.record_outcome(user_id="fred", user_input="a", turn_id="turn-a")

        calls = model.record_observed_transition.call_args_list
        self.assertEqual(calls[0].args[:3], ("social", "peer", [2.0] * 8))
        self.assertEqual(calls[0].args[3], [20.0] * 8)
        self.assertEqual(calls[1].args[:3], ("analytical", "fred", [1.0] * 8))
        self.assertEqual(calls[1].args[3], [10.0] * 8)
        self.assertEqual(model._pending_by_turn, {})

    def _historical_model(self):
        model = WorldSelfDynamicsModel.__new__(WorldSelfDynamicsModel)
        model._records = [
            DynamicsRecord(
                action_type="analytical",
                context_before=[0.4, 0.5, 0.6, 0.7, 0.2, 0.5, 0.1, 0.2],
                self_delta=[0.01, 0.0, 0.0, 0.0],
                # Legacy persisted values are response-style proxies, not
                # measurements. The predictor must never learn from them.
                world_delta=[0.02, 0.9, 0.03],
                outcome="positive",
                recorded_at=float(index + 1),
            )
            for index in range(8)
        ]
        return model

    def test_prediction_ignores_legacy_response_style_engagement(self):
        model = self._historical_model()

        prediction = model._predict("analytical", [0.4, 0.5, 0.6, 0.7, 0.2, 0.5, 0.1, 0.2])

        self.assertIsNotNone(prediction)
        self.assertIsNone(prediction.world_deltas["engagement_signal"])
        self.assertAlmostEqual(prediction.world_deltas["user_trust"], 0.02, places=3)
        self.assertAlmostEqual(prediction.world_deltas["skill_depth_gain"], 0.03, places=3)
        self.assertNotIn("engagement", prediction.narrative)

    def test_new_transition_stores_engagement_as_unavailable_and_unrated(self):
        model = WorldSelfDynamicsModel.__new__(WorldSelfDynamicsModel)
        model._records = []
        model._lock = threading.Lock()
        model._measure_skill_gain = Mock(return_value=0.04)
        model._save = Mock()
        model._calibration_engine = None

        model.record_observed_transition(
            "analytical", "fred",
            [0.4, 0.5, 0.6, 0.7, 0.2, 0.5, 0.1, 0.2],
            [0.3, 0.5, 0.6, 0.7, 0.2, 0.55, 0.1, 0.2],
            response_text="A very long answer with several questions? Why?",
            user_input="ok",
        )

        record = model._records[0]
        self.assertEqual(record.world_delta, [0.05, None, 0.04])
        self.assertEqual(record.outcome, "unrated")

    def test_counterfactual_does_not_turn_missing_engagement_into_score(self):
        simulator = CounterfactualSimulator.__new__(CounterfactualSimulator)
        simulator._calibration_engine = None
        pcm = SimpleNamespace(_predict=Mock(return_value=None))
        wsdm = SimpleNamespace(
            _records=[object()] * 6,
            _predict=Mock(return_value=SimpleNamespace(
                world_deltas={"engagement_signal": None}, confidence=0.9
            )),
        )

        branch = simulator._predict_branch(pcm, wsdm, "analytical", [0.0] * 5, [0.0] * 8, False)

        self.assertIsNone(branch.wsdm_engagement)
        self.assertEqual(branch.joint_score, 0.0)

    def test_counterfactual_analysis_is_idempotent_for_same_pcm_window(self):
        simulator = CounterfactualSimulator.__new__(CounterfactualSimulator)
        pcm_record = SimpleNamespace(
            interaction_n=7, recorded_at=123.5, response_hash="abc",
            action_type="social", state_before=[0.0] * 5,
            outcome="unrated",
        )
        simulator._organism = SimpleNamespace(_loop=SimpleNamespace(
            _consequence_model=SimpleNamespace(_records=[pcm_record] * 15),
            _world_self_dynamics=None,
        ))
        simulator._lock = threading.Lock()
        simulator._run_guard = threading.Lock()
        simulator._log = []
        simulator._last_run_cycle = 0
        simulator._save = Mock()
        calls = []

        def analyse(_pcm, _wsdm, _record, _wsdm_by_n):
            calls.append(1)
            return CounterfactualQuery(
                interaction_n=7, actual_action="social", actual_outcome="unrated",
                branches={}, best_alternative="creative", actual_rank=2,
                worst_actual=False,
            )

        simulator._analyse_interaction = analyse
        simulator._run(10)
        simulator._run(15)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(simulator._log), 1)
        self.assertTrue(simulator._log[0]["source_ref"])
        simulator._save.assert_called_once()

    def test_counterfactual_runs_do_not_overlap(self):
        simulator = CounterfactualSimulator.__new__(CounterfactualSimulator)
        pcm_record = SimpleNamespace(
            interaction_n=8, recorded_at=124.5, response_hash="def",
            action_type="technical", state_before=[0.0] * 5,
            outcome="unrated",
        )
        simulator._organism = SimpleNamespace(_loop=SimpleNamespace(
            _consequence_model=SimpleNamespace(_records=[pcm_record] * 15),
            _world_self_dynamics=None,
        ))
        simulator._lock = threading.Lock()
        simulator._run_guard = threading.Lock()
        simulator._log = []
        simulator._last_run_cycle = 0
        simulator._save = Mock()
        calls = []
        started = threading.Event()
        release_analysis = threading.Event()

        def analyse(_pcm, _wsdm, _record, _wsdm_by_n):
            calls.append(1)
            started.set()
            release_analysis.wait(timeout=1.0)
            return CounterfactualQuery(
                interaction_n=8, actual_action="technical", actual_outcome="unrated",
                branches={}, best_alternative="creative", actual_rank=2,
                worst_actual=False,
            )

        simulator._analyse_interaction = analyse
        first = threading.Thread(target=simulator._run, args=(10,))
        first.start()
        self.assertTrue(started.wait(timeout=1.0))
        simulator._run(15)
        release_analysis.set()
        first.join(timeout=1.0)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(simulator._log), 1)

    def test_prospective_score_keeps_missing_engagement_unavailable(self):
        pcm = SimpleNamespace(_predict=Mock(return_value=None))
        wsdm = SimpleNamespace(
            _records=[object()] * 6,
            _predict=Mock(return_value=SimpleNamespace(
                world_deltas={"engagement_signal": None}, confidence=0.9
            )),
        )

        candidate = _score_candidate(pcm, wsdm, None, "analytical", [0.0] * 5, [0.0] * 8, False)

        self.assertIsNone(candidate.wsdm_engagement)
        self.assertEqual(candidate.joint_score, 0.0)

    def test_intention_reasoner_does_not_transfer_chat_class_outcomes_to_plan_steps(self):
        model = SimpleNamespace(predict_from_context=Mock())
        organism = SimpleNamespace(_loop=SimpleNamespace(_world_self_dynamics=model))
        reasoner = IntentionReasoner.__new__(IntentionReasoner)
        reasoner._organism = organism

        hypothesis = reasoner._evaluate("memory_recall", [0.5] * 8)

        model.predict_from_context.assert_not_called()
        self.assertEqual(hypothesis.evidence_source, "unvalidated_operation_prior")
        self.assertIn("effect on the intention has not been measured", hypothesis.statement)


if __name__ == "__main__":
    unittest.main()
