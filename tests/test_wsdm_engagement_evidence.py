import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cognition.counterfactual_simulator import CounterfactualSimulator
from cognition.intention_reasoner import IntentionReasoner
from cognition.prospective_deliberation import _score_candidate
from cognition.world_self_dynamics_model import DynamicsRecord, WorldSelfDynamicsModel


class WSDMEngagementEvidenceTests(unittest.TestCase):
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

    def test_intention_gain_does_not_include_unmeasured_engagement(self):
        model = SimpleNamespace(predict_from_context=Mock(return_value=SimpleNamespace(
            self_deltas={"cognitive_energy": 0.1},
            world_deltas={
                "user_trust": 0.1,
                "engagement_signal": 0.9,
                "skill_depth_gain": 0.05,
            },
            confidence=0.8,
        )))
        organism = SimpleNamespace(_loop=SimpleNamespace(_world_self_dynamics=model))
        reasoner = IntentionReasoner.__new__(IntentionReasoner)
        reasoner._organism = organism

        hypothesis = reasoner._evaluate("memory_recall", [0.5] * 8)

        self.assertAlmostEqual(hypothesis.expected_gain, 0.15)
        self.assertEqual(hypothesis.evidence_source, "world_self_dynamics")


if __name__ == "__main__":
    unittest.main()
