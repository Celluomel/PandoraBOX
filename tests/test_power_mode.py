import unittest
import time
import threading

from body_runtime_host.power_mode import PowerModeManager
from body_runtime_host.runtime import BodyHost


class PowerModeManagerTests(unittest.TestCase):
    def test_mode_change_applies_policy_and_returns_status(self):
        calls = []
        manager = PowerModeManager(lambda old, new: calls.append((old, new)) or {"ok": True})
        status = manager.set_mode("ATTENTIVE")
        self.assertEqual(calls, [("DEV", "ATTENTIVE")])
        self.assertEqual(status["mode"], "ATTENTIVE")

    def test_auto_raise_only_moves_idle_to_attentive(self):
        calls = []
        manager = PowerModeManager(lambda old, new: calls.append((old, new)) or {"ok": True})
        manager.set_mode("IDLE")
        raised = manager.auto_raise("IMU motion")
        self.assertEqual(raised["mode"], "ATTENTIVE")
        self.assertIn("IMU motion", raised["reason"])
        self.assertIsNone(manager.auto_raise("another event"))
        self.assertEqual(calls, [("DEV", "IDLE"), ("IDLE", "ATTENTIVE")])

    def test_rolling_power_mean_is_grouped_by_mode_and_expires(self):
        manager = PowerModeManager(lambda old, new: {"ok": True})
        now = time.time()
        manager.record_watts(18.0, now=now)
        manager.set_mode("IDLE")
        manager.record_watts(10.0, now=now + 1.0)
        status = manager.status()
        self.assertEqual(status["rolling_60s_mean_w_by_mode"]["DEV"]["mean_w"], 18.0)
        self.assertEqual(status["rolling_60s_mean_w_by_mode"]["IDLE"]["mean_w"], 10.0)
        status = manager.status()
        self.assertEqual(status["rolling_60s_mean_w_by_mode"]["DEV"]["window_s"], 60)

    def test_runtime_overrides_restore_original_values_without_mutating_saved_config(self):
        class FakeService:
            def start(self):
                pass

            def stop(self):
                pass

        host = object.__new__(BodyHost)
        host.config = {
            "BODY_YOLO_ENABLED": True,
            "BODY_MIDAS_ENABLED": True,
            "BODY_SEGMENTATION_ENABLED": False,
            "BODY_YOLO_INTERVAL_S": 0.25,
            "BODY_MIDAS_INTERVAL_S": 0.4,
            "BODY_SEGMENTATION_INTERVAL_S": 1.0,
        }
        host._power_mode_overrides = {}
        host._power_mode_base = None
        host._power_motion_since = None
        host._local_camera_lock = threading.RLock()
        host._local_camera = None
        host._yolox_service = FakeService()
        host._midas_service = FakeService()
        host._segmentation_service = FakeService()
        host._configure_local_camera = lambda start=None: {"status": "stopped"}
        host._append_power_mode_trace = lambda old, new: None
        saved_config = dict(host.config)

        host._apply_power_mode("DEV", "ATTENTIVE")
        self.assertEqual(host.value("BODY_YOLO_INTERVAL_S"), 1.0)
        self.assertEqual(host.config, saved_config)
        host._apply_power_mode("ATTENTIVE", "DEV")
        self.assertEqual(host.value("BODY_YOLO_INTERVAL_S"), 0.25)
        self.assertEqual(host.config, saved_config)


if __name__ == "__main__":
    unittest.main()
