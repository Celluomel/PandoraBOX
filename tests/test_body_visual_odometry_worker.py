import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from body_runtime_host.runtime import BodyHost


class _StopAfterOneWait:
    def __init__(self):
        self.waited = []
        self.stopped = False

    def is_set(self):
        return self.stopped

    def wait(self, interval):
        self.waited.append(interval)
        self.stopped = True
        return True


class BodyVisualOdometryWorkerTests(unittest.TestCase):
    def test_refresh_cadence_tracks_power_mode(self):
        self.assertEqual(BodyHost.visual_odometry_refresh_interval("DEV"), 0.5)
        self.assertEqual(BodyHost.visual_odometry_refresh_interval("ATTENTIVE"), 0.75)
        self.assertEqual(BodyHost.visual_odometry_refresh_interval("IDLE"), 1.0)

    def test_worker_advances_odometry_without_an_http_request(self):
        host = object.__new__(BodyHost)
        host.stop_event = _StopAfterOneWait()
        host._power_mode = SimpleNamespace(status=lambda: {"mode": "DEV"})
        host._visual_odometry_status_lock = threading.Lock()
        host._visual_odometry_cached_status = {"state": "waiting", "available": False}
        host._visual_odometry_status_updated_at = time.monotonic()
        host._update_visual_odometry_status = Mock(return_value={
            "state": "tracking", "available": True, "captured_at": time.time(),
        })

        host.visual_odometry_loop()

        host._update_visual_odometry_status.assert_called_once_with()
        self.assertEqual(host._visual_odometry_cached_status["state"], "tracking")
        self.assertEqual(host.stop_event.waited, [0.5])

    def test_http_status_reads_cache_and_marks_old_frame_stale(self):
        host = object.__new__(BodyHost)
        host._visual_odometry_status_lock = threading.Lock()
        host._visual_odometry_cached_status = {
            "state": "tracking", "available": True,
            "captured_at": time.time() - 10.0,
        }
        host._visual_odometry_status_updated_at = time.monotonic()
        host._power_mode = SimpleNamespace(status=lambda: {"mode": "DEV"})

        result = host.visual_odometry_status()

        self.assertEqual(result["state"], "stale")
        self.assertFalse(result["available"])
        self.assertEqual(result["last_state"], "tracking")
        self.assertGreaterEqual(result["frame_age_s"], 10.0)


if __name__ == "__main__":
    unittest.main()
