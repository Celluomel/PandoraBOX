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

    def test_read_only_camera_question_stays_in_conversation_without_motor_plan(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        body = SimpleNamespace(interpret_camera=Mock(return_value={
            "ok": True,
            "model": "body-vlm",
            "interpretation": "Une tasse est visible devant le robot.",
        }))
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = Mock(return_value="normal")
        bridge.assess_body_action_request = Mock(side_effect=AssertionError("must not plan movement"))

        result = bridge.handle_body_chat_turn("Décris la caméra du robot")

        self.assertIsNone(result)
        body.interpret_camera.assert_not_called()
        bridge.assess_body_action_request.assert_not_called()

    def test_read_only_camera_question_does_not_claim_unavailable_body_vlm(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(
            interpret_camera=Mock(return_value={"ok": False, "error": "401 Unauthorized"}),
        ))
        bridge._classify_body_chat_turn = Mock(return_value="normal")

        result = bridge.handle_body_chat_turn("What is on the robot camera?")

        self.assertIsNone(result)

    def test_read_only_perception_question_stays_in_conversation(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(
            body_snapshot=Mock(return_value={"available": False, "error": "Body host unreachable"}),
        ))
        bridge._classify_body_chat_turn = Mock(return_value="normal")

        result = bridge.handle_body_chat_turn("Que détectent les capteurs du robot ?")

        self.assertIsNone(result)

    def test_read_only_body_diagnostic_does_not_compile_or_send_motion(self):
        now = __import__("time").time()
        observations = [{
            "subject": "sensor.ultrasonic",
            "source": "remote:body:hc_sr04_ventuno_bridge",
            "observed_at": now,
            "value": {"available": False, "simulated": False, "sensors": [
                {"id": "front_left", "available": False, "distance_m": None, "error": "echo_timeout"},
            ]},
        }, {
            "subject": "fnk0031.usb_status",
            "source": "remote:body:fnk0031_usb",
            "observed_at": now,
            "value": {"connected": True, "actuation_enabled": True,
                      "estimated_leg_state": {"source": "fnhr_internal_command_estimate"},
                      "estimated_state_is_measured": False},
        }]
        body = SimpleNamespace(
            snapshot=Mock(return_value=observations),
            metric_yolo_status=Mock(return_value={
                "state": "ready", "frame_id": "frame-1", "captured_at": now,
                "detections": [{"label": "tv", "confidence": 0.82}],
            }),
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {}
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge._classify_body_chat_turn = Mock(return_value="body_diagnostic")
        bridge.assess_body_action_request = Mock(side_effect=AssertionError("diagnostics must not create a motor plan"))

        result = bridge.handle_body_chat_turn("Procède aux tests des capteurs et du mouvement")

        self.assertEqual(result["status"], "diagnostic")
        self.assertIn("tv", result["response"])
        self.assertIn("no echo/data", result["response"])
        self.assertIn("estimée depuis les commandes FNHR", result["response"])
        self.assertFalse(result["diagnostic"]["actions_sent"])
        bridge.assess_body_action_request.assert_not_called()

    def test_semantic_classifier_has_a_read_only_diagnostic_route(self):
        class Manager:
            history = [
                {"role": "user", "content": "Je veux vérifier les capacités sensorielles et motrices du Body."},
                {"role": "assistant", "content": "Je peux vérifier les flux réels et signaler ce qui exige une action physique."},
            ]

            def generate_interactive_analysis(self, prompt, system, **kwargs):
                self.system = system
                self.prompt = prompt
                return "BODY_DIAGNOSTIC"

            def stream(self, *args, **kwargs):
                return iter(())

        manager = Manager()
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._llm_stream_fn = manager.stream

        with patch("managers.settings_manager.config", SimpleNamespace(FAST_ROUND_ENABLED=False)):
            route = bridge._classify_body_chat_turn(
                "Procède aux tests des capteurs et du mouvement"
            )

        self.assertEqual(route, "body_diagnostic")
        self.assertIn("checklist or request to test a capability remains BODY_DIAGNOSTIC", manager.system)
        self.assertIn("vérifier les capacités sensorielles", manager.prompt)

    def test_status_ambiguity_is_rechecked_as_confirmation(self):
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._pending_body_plans = {
            "default": {
                "plan": {"objective": "move parcel", "steps": [{"verb": "navigate", "target": "goal"}]},
                "replace_plan_id": "",
            }
        }
        body = SimpleNamespace(
            snapshot=Mock(return_value=[]),
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
