import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class BrainBodyStatusResponseTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
