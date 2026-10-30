import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BrainBodyStatusResponseTest(unittest.TestCase):
    def test_movement_status_prioritizes_ack_without_claiming_physical_motion(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        observations = [{
            "subject": "fnk0031.usb_status",
            "source": "remote:body:fnk0031_usb",
            "kind": "hardware_status",
            "observed_at": now,
            "value": {"connected": True, "estimated_leg_state": None,
                      "estimated_state_is_measured": False},
        }, {
            "subject": "robot.turn_left",
            "source": "remote:body_action",
            "kind": "actuation_feedback",
            "observed_at": now,
            "value": "acknowledged",
            "provenance": {"command_status": "acknowledged", "verification_status": "unknown"},
        }, {
            "subject": "sensor.odometry",
            "source": "remote:body:ros2_simulation",
            "kind": "sensor",
            "observed_at": now,
            "value": {"position_m": [2.0, 0.0, 0.0]},
        }]
        body = SimpleNamespace(snapshot=lambda max_age=None: observations)
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("what is the robot movement status")

        self.assertIn("contrôleur FNK0031 connecté", result["response"])
        self.assertIn("robot.turn_left: acknowledged", result["response"])
        self.assertIn("déplacement physique non vérifié", result["response"])
        self.assertIn("Aucune odométrie physique indépendante", result["response"])
        self.assertNotIn("2.0", result["response"])
        self.assertFalse(result["body_status"]["physical_odometry_confirmed"])

    def test_movement_status_reports_no_recent_command_and_disconnected_controller(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "fnk0031.usb_status",
            "source": "remote:body:fnk0031_usb",
            "kind": "hardware_status",
            "observed_at": __import__("time").time(),
            "value": {"connected": False},
        }])
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("status of robot movements")

        self.assertIn("contrôleur FNK0031 non connecté", result["response"])
        self.assertIn("aucun résultat récent de commande", result["response"])

    def test_no_plan_still_reports_bridged_runtime_observation(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.runtime",
            "source": "remote:body-ventuno:body_runtime",
            "observed_at": __import__("time").time(),
            "value": {
                "camera": {"status": "capturing", "available": True, "observed_fps": 15.0},
                "robot": {"enabled": False, "connected": False},
                "world_model": {"enabled": False, "running": False},
                "plugins": [],
            },
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}, "observation_count": 1},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        with patch("cognition.persona_bridge.time.time", return_value=1791069001.0):
            result = bridge._body_status_response()

        self.assertEqual(result["status"], "reported")
        self.assertIn("Aucun plan Body actif", result["response"])
        self.assertIn("camera", result["response"])
        self.assertIn("15", result["response"])
        self.assertIn("pont", result["response"].lower())

    def test_battery_question_returns_compact_estimate_instead_of_sensor_dump(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.runtime",
            "source": "remote:body-ventuno:body_runtime",
            "observed_at": __import__("time").time(),
            "value": {
                "power": {
                    "battery_estimate": {
                        "level_percent_est": 10.2,
                        "remaining_wh_est": 8.562,
                        "source": "continuous INA232 input-rail integration; estimate only",
                    }
                }
            },
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}, "observation_count": 1},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("quel le niveau de battery du body")

        self.assertIn("10.2%", result["response"])
        self.assertIn("8.56 Wh", result["response"])
        self.assertIn("pas une mesure directe", result["response"])
        self.assertNotIn("ranges_m", result["response"])

    def test_body_status_formats_live_sensor_channels_without_raw_json_dump(self):
        from cognition.persona_bridge import PersonaBridge

        observations = [{
            "subject": "sensor.ultrasonic",
            "source": "remote:body:hc_sr04_ventuno_bridge",
            "observed_at": __import__("time").time(),
            "value": {"available": True, "simulated": False, "sensors": [
                {"id": "front_left", "available": True, "distance_m": 0.73},
                {"id": "front_right", "available": False, "distance_m": None},
                {"id": "rear", "available": True, "distance_m": 1.2},
            ]},
        }, {
            "subject": "body.world_model",
            "source": "remote:body:world_model",
            "observed_at": __import__("time").time(),
            "value": {"simulated_only": True, "objects": [{"label": "table"}]},
        }]
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: observations,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("explain body feedback")

        self.assertIn("front_left 0.73m", result["response"])
        self.assertIn("front_right no echo/data", result["response"])
        self.assertIn("simulation-only", result["response"])
        self.assertNotIn('"distance_m"', result["response"])

    def test_body_status_excludes_ros2_simulation_sensors(self):
        from cognition.persona_bridge import PersonaBridge

        observations = [{
            "subject": "sensor.odometry",
            "source": "remote:body:ros2_simulation",
            "observed_at": __import__("time").time(),
            "value": {"position_m": [0.5, 0.0, 0.0]},
        }, {
            "subject": "sensor.gps",
            "source": "remote:body:ventuno_usart3_gps",
            "observed_at": __import__("time").time(),
            "value": {"available": True, "fix": True, "latitude": 48.86,
                      "longitude": 2.11, "satellites": 6},
        }]
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: observations,
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("explain body feedback")

        self.assertIn("gps live: fix 48.860000, 2.110000", result["response"])
        self.assertIn("Nav2 simulés", result["response"])
        self.assertNotIn("0.5", result["response"])
        self.assertNotIn("sensor.odometry [remote", result["response"])

    def test_body_status_shows_older_hardware_samples_as_stale_not_missing(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "sensor.gps",
            "source": "remote:body:ventuno_usart3_gps",
            "observed_at": __import__("time").time() - 24,
            "value": {"available": True, "fix": True, "latitude": 48.86,
                      "longitude": 2.11, "satellites": 6},
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("body status")

        self.assertIn("STALE sample (24s)", result["response"])
        self.assertIn("gps live: fix", result["response"])

    def test_body_status_never_expands_simulation_snapshot_without_flag(self):
        from cognition.persona_bridge import PersonaBridge

        observation = {
            "subject": "body.world_model",
            "source": "remote:body:world_model",
            "observed_at": __import__("time").time(),
            "value": {"source": "ros2_simulation", "objects": [{"label": "simulated chair"}]},
        }
        body = SimpleNamespace(
            worldmodel_plan=lambda: {"active_plan": None},
            worldmodel=None,
            status=lambda: {"brain_bridge": {"connected": True}},
            snapshot=lambda max_age=None: [observation],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_status_response("body status")

        self.assertIn("simulation-only scene", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_uses_real_sensor_telemetry_when_scene_is_simulated(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(
            snapshot=lambda max_age=None: [{
                "subject": "sensor.gps",
                "value": {"available": True, "fix": True, "latitude": 48.8625,
                          "longitude": 2.1187, "satellites": 7},
            }],
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"ground_truth_available": True, "objects": [{"label": "simulated chair"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation du robot réel", result["response"])
        self.assertIn("48.862500, 2.118700", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_still_reports_sensors_without_scene_snapshot(self):
        from cognition.persona_bridge import PersonaBridge

        body = SimpleNamespace(snapshot=lambda max_age=None: [{
            "subject": "sensor.tof",
            "value": {"available": True, "distance_m": 0.62, "simulated": False},
        }])
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)
        bridge.current_body_perception = lambda: {"available": False, "error": "stale world model"}

        result = bridge._body_perception_response()

        self.assertEqual(result["status"], "reported")
        self.assertIn("Capteurs réels", result["response"])
        self.assertIn("0.62m", result["response"])
        self.assertFalse(result["perception"]["scene_available"])

    def test_perception_response_rejects_simulation_source_without_flag(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(snapshot=lambda max_age=None: []))
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"source": "ros2_simulation", "objects": [{"label": "simulated chair"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_rejects_simulated_room_source(self):
        from cognition.persona_bridge import PersonaBridge

        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=SimpleNamespace(snapshot=lambda max_age=None: []))
        bridge.current_body_perception = lambda: {
            "available": True,
            "snapshot": {"source": "simulated_room", "objects": [{"label": "moving obstacle"}]},
        }

        result = bridge._body_perception_response()

        self.assertIn("simulation, pas une observation", result["response"])
        self.assertNotIn("moving obstacle", result["response"])

    def test_perception_response_prefers_fresh_live_yolox_over_simulated_map(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(
            camera_yolo_status=lambda: {
                "state": "ready", "frame_id": "camera-42", "captured_at": now,
                "detections": [
                    {"label": "person", "confidence": 0.7931},
                    {"label": "person", "confidence": 0.4156},
                ],
            },
            body_snapshot=lambda: {
                "source": "simulated_room", "objects": [{"label": "simulated chair"}],
            },
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_perception_response()

        self.assertIn("YOLOX", result["response"])
        self.assertIn("2 détection(s) 2D", result["response"])
        self.assertIn("person (79%)", result["response"])
        self.assertIn("simulateur", result["response"])
        self.assertNotIn("simulated chair", result["response"])

    def test_perception_response_reports_stale_yolox_as_stale_not_live(self):
        from cognition.persona_bridge import PersonaBridge

        now = __import__("time").time()
        body = SimpleNamespace(
            camera_yolo_status=lambda: {
                "state": "ready", "frame_id": "camera-old", "captured_at": now - 28,
                "detections": [{"label": "person", "confidence": 0.77}],
            },
            body_snapshot=lambda: {"source": "simulated_room", "objects": []},
        )
        bridge = PersonaBridge.__new__(PersonaBridge)
        bridge._organism = SimpleNamespace(_body_runtime=body)

        result = bridge._body_perception_response()

        self.assertIn("dernière analyse il y a 28s · STALE", result["response"])
        self.assertIn("person (77%)", result["response"])
        self.assertTrue(result["perception"]["camera"]["stale"])


if __name__ == "__main__":
    unittest.main()
