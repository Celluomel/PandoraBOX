import threading
import unittest
from unittest.mock import Mock

from cognition.predictive_consequence_model import PredictiveConsequenceModel
from cognition.world_self_dynamics_model import WorldSelfDynamicsModel


class PeerPredictiveOutcomeIsolationTests(unittest.TestCase):
    def test_pcm_peer_transition_does_not_consume_human_pending_prediction(self):
        model = PredictiveConsequenceModel.__new__(PredictiveConsequenceModel)
        model._records = []
        model._pending = ("human-action", [0.1, 0.2, 0.3, 0.4, 0.5], 7)
        model._save = Mock()
        model._calibration_engine = Mock()

        model.record_observed_transition(
            "peer-social",
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.3, 0.5, 0.4, 0.8],
            interaction_n=2,
            outcome="neutral",
        )

        self.assertEqual(model._pending, ("human-action", [0.1, 0.2, 0.3, 0.4, 0.5], 7))
        self.assertEqual(len(model._records), 1)
        self.assertEqual(model._records[0].action_type, "peer-social")
        self.assertEqual(model._records[0].delta, [0.1, 0.0, 0.1, -0.1, 0.2])
        model._calibration_engine.resolve_prediction.assert_not_called()

    def test_pcm_calibration_uses_measured_energy_delta_not_valence_label(self):
        model = PredictiveConsequenceModel.__new__(PredictiveConsequenceModel)
        model._records = []
        model._pending = None
        model._save = Mock()
        model._calibration_engine = Mock()

        model.record_observed_transition(
            "reasoning", [0.8, 0.5, 0.4, 0.6, 0.2],
            [0.6, 0.5, 0.4, 0.6, 0.2],
            outcome="positive", resolve_calibration=True,
        )

        model._calibration_engine.resolve_prediction.assert_called_once_with(
            module="pcm", key="reasoning", actual_direction="negative",
        )

    def test_wsdm_peer_transition_is_pair_scoped_and_keeps_pending_human_turn(self):
        model = WorldSelfDynamicsModel.__new__(WorldSelfDynamicsModel)
        model._records = []
        model._pending = ("human-action", "fred", [0.0] * 8, 9)
        model._lock = threading.Lock()
        model._measure_skill_gain = Mock(return_value=0.05)
        model._save = Mock()
        model._calibration_engine = Mock()

        before = [0.4, 0.5, 0.6, 0.7, 0.2, 0.5, 0.1, 0.2]
        after = [0.3, 0.6, 0.6, 0.7, 0.2, 0.55, 0.1, 0.2]
        model.record_observed_transition(
            "peer-social", "lumina_child_flux", before, after,
            interaction_n=3,
            outcome="neutral",
            response_text="A substantive peer answer?",
            user_input="A peer prompt",
        )

        self.assertEqual(model._pending, ("human-action", "fred", [0.0] * 8, 9))
        self.assertEqual(len(model._records), 1)
        self.assertEqual(model._records[0].user_id, "lumina_child_flux")
        self.assertEqual(model._records[0].self_delta, [-0.1, 0.1, 0.0, 0.0])
        model._calibration_engine.resolve_prediction.assert_not_called()

    def test_wsdm_calibration_uses_measured_energy_delta_not_valence_label(self):
        model = WorldSelfDynamicsModel.__new__(WorldSelfDynamicsModel)
        model._records = []
        model._pending = None
        model._lock = threading.Lock()
        model._measure_skill_gain = Mock(return_value=0.0)
        model._save = Mock()
        model._calibration_engine = Mock()

        before = [0.3, 0.5, 0.7, 0.8, 0.2, 0.5, 0.1, 0.2]
        after = [0.4, 0.5, 0.7, 0.8, 0.2, 0.5, 0.1, 0.2]
        model.record_observed_transition(
            "reasoning", "fred", before, after,
            outcome="negative", resolve_calibration=True,
        )

        model._calibration_engine.resolve_prediction.assert_called_once_with(
            module="wsdm", key="reasoning", actual_direction="positive",
        )


if __name__ == "__main__":
    unittest.main()
