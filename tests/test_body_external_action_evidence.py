"""Offline world-model external execution integration tests.

Build a minimal world-model object without starting threads or hardware.
Tests the real execute_external boundary and evidence serialization.
"""
import threading
import time
import unittest
from unittest.mock import Mock

from body_runtime_host.worldmodel.core import EmbodiedWorldModel
from body_runtime_host.worldmodel.types import Action, Observation, Outcome, BodyState


class ExternalActionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.model = EmbodiedWorldModel.__new__(EmbodiedWorldModel)
        self.model._lock = threading.RLock()
        self.model._steps = 0
        self.model._episodes = []
        self.model._last_success_step = -1
        self.model._log_episode = Mock()
        self.model._action_label = lambda action: action.type
        self.model.source = Mock()
        self.model.source.simulated = False
        self.model.source.observe.return_value = Observation(timestamp=time.time())
        self.model.source.body_state.return_value = BodyState(timestamp=time.time())

    def test_controller_ack_is_unverified(self):
        self.model.source.execute_authorized.return_value = (
            Observation(timestamp=time.time()),
            Outcome(kind="success", reward=1, description="controller ACK"),
        )
        result = self.model.execute_external(Action(type="forward"))
        self.assertEqual(result["outcome"]["kind"], "success")
        self.assertEqual(result["evidence"]["state"], "acknowledged_unverified")
        self.assertFalse(result["evidence"]["physical_effect_verified"])
        self.assertEqual(self.model._last_success_step, -1)
        self.assertEqual(len(self.model._episodes), 1)

    def test_stale_pre_action_pose_refuses_adapter(self):
        self.model.source.body_state.return_value = BodyState(timestamp=time.time() - 30)
        result = self.model.execute_external(Action(type="forward"))
        self.assertEqual(result["outcome"]["kind"], "failure")
        self.model.source.execute_authorized.assert_not_called()

    def test_missing_actuator_source_fails_closed(self):
        self.model.source = None
        self.model._bridge_observation = Mock(return_value=Observation(timestamp=time.time()))
        result = self.model.execute_external(Action(type="forward"))
        self.assertEqual(result["outcome"]["kind"], "failure")
        self.assertEqual(result["evidence"]["state"], "failed")


if __name__ == "__main__":
    unittest.main()
