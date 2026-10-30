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
            "observed_at": 1791069000.0,
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
            "observed_at": 1791069000.0,
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


if __name__ == "__main__":
    unittest.main()
