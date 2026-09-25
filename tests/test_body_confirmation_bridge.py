import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cognition.persona_bridge import PersonaBridge


class BodyConfirmationBridgeTests(unittest.TestCase):
    def test_status_ambiguity_is_rechecked_as_confirmation(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {
            "default": {
                "plan": {"objective": "move parcel", "steps": [{"verb": "navigate", "target": "goal"}]},
                "replace_plan_id": "",
            }
        }
        body = SimpleNamespace(
            submit_worldmodel_plan=Mock(return_value={
                "accepted": True,
                "plan": {"steps": [{"verb": "navigate", "target": "goal"}]},
            }),
            run_worldmodel=Mock(return_value={"running": True}),
        )
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = Mock(side_effect=["body_status", "confirm"])

        result = bridge.handle_body_chat_turn("execute the plan")

        self.assertEqual(result["status"], "submitted")
        body.submit_worldmodel_plan.assert_called_once()
        body.run_worldmodel.assert_called_once_with(True, False)


if __name__ == "__main__":
    unittest.main()
