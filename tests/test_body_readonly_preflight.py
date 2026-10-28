"""Offline tests for read-only sensor preflight; never opens a socket."""
import unittest
from unittest.mock import patch
from io import BytesIO
import time

from tools.body_readonly_preflight import run, validate_frame


def frame(**overrides):
    data = {"timestamp": time.time(), "position": [0, 0, 0],
            "orientation": 0.0, "objects": []}
    data.update(overrides)
    return data


class FakeResponse:
    def __init__(self, payload):
        import json
        self.content = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n=-1):
        return self.content[:n]


class PreflightTests(unittest.TestCase):
    def test_fresh_frame(self):
        self.assertTrue(validate_frame(frame(), time.time())["valid"])

    def test_stale_future_missing_and_nonfinite_timestamp(self):
        for stamp in (0, time.time() + 20, None, float("nan"), float("inf")):
            with self.subTest(stamp=stamp):
                self.assertFalse(validate_frame(frame(timestamp=stamp), time.time())["valid"])

    def test_bad_geometry(self):
        for data in (frame(position=[0, 1]), frame(position=[0, float("nan"), 0]),
                     frame(orientation=float("inf")), frame(objects={})):
            self.assertFalse(validate_frame(data, time.time())["valid"])

    def test_only_get_is_used(self):
        requests = []
        def fake_open(request, timeout):
            requests.append(request)
            return FakeResponse(frame())
        with patch("tools.body_readonly_preflight.urlopen", side_effect=fake_open):
            result = run("http://127.0.0.1:1234", samples=3, timeout=1)
        self.assertTrue(result["passed"])
        self.assertEqual(len(requests), 3)
        self.assertTrue(all(request.get_method() == "GET" for request in requests))
        self.assertTrue(all(request.full_url.endswith("/sensors") for request in requests))
        self.assertFalse(result["actuation_attempted"])

    def test_network_failure_fails_closed(self):
        with patch("tools.body_readonly_preflight.urlopen", side_effect=OSError("offline")):
            result = run("http://127.0.0.1:1234", samples=1, timeout=1)
        self.assertFalse(result["passed"])
        self.assertFalse(result["actuation_attempted"])


if __name__ == "__main__":
    unittest.main()
