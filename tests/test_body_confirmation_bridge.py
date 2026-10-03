import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cognition.persona_bridge import PersonaBridge
from cognition.body_runtime.remote import RemoteWorldModel


class BodyConfirmationBridgeTests(unittest.TestCase):
    @patch("cognition.body_runtime.remote._request")
    def test_remote_body_camera_calls_body_owned_vlm_endpoint(self, request):
        request.return_value = {"ok": True, "interpretation": "scene"}
        remote = RemoteWorldModel("https://192.0.2.10", auth_username="body", auth_password="secret")

        result = remote.interpret_camera()

        self.assertTrue(result["ok"])
        args, kwargs = request.call_args
        self.assertEqual(args[:2], ("POST", "https://192.0.2.10/body/camera/test-vlm"))
        self.assertEqual(args[2], {})
        self.assertGreaterEqual(args[3], 90)
        self.assertIn("Authorization", args[4])

    def test_body_camera_request_uses_body_vlm_without_compiling_motor_plan(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        body = SimpleNamespace(interpret_camera=Mock(return_value={
            "ok": True,
            "model": "body-vlm",
            "interpretation": "Une tasse est visible devant le robot.",
        }))
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = Mock(return_value="body_camera")
        bridge.assess_body_action_request = Mock(side_effect=AssertionError("must not plan movement"))

        result = bridge.handle_body_chat_turn("Décris la caméra du robot")

        self.assertEqual(result["status"], "interpreted")
        self.assertIn("Une tasse", result["response"])
        body.interpret_camera.assert_called_once_with()
        bridge.assess_body_action_request.assert_not_called()

    def test_body_camera_unavailable_is_reported_without_claiming_connection(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(
            interpret_camera=Mock(return_value={"ok": False, "error": "401 Unauthorized"}),
        ))
        bridge._classify_body_chat_turn = Mock(return_value="body_camera")

        result = bridge.handle_body_chat_turn("What is on the robot camera?")

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("ne peux pas décrire", result["response"])

    def test_body_perception_unavailable_is_explicit(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(
            body_snapshot=Mock(return_value={"available": False, "error": "Body host unreachable"}),
        ))
        bridge._classify_body_chat_turn = Mock(return_value="body_perception")

        result = bridge.handle_body_chat_turn("Que détectent les capteurs du robot ?")

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("pas de perception actuelle", result["response"])

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
