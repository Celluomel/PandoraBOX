import unittest
from unittest.mock import patch

from cognition.body_runtime.runtime import BodyRuntime


class BodyRuntimeUrlConfigTests(unittest.TestCase):
    def _runtime(self, body_url, body_port):
        runtime = BodyRuntime.__new__(BodyRuntime)
        config = {"BODY_URL": body_url, "BODY_PORT": body_port}
        runtime.config_value = lambda key, fallback=None: config.get(key, fallback)
        return runtime

    def test_host_only_body_url_uses_configured_body_port(self):
        runtime = self._runtime("https://127.0.0.1", 8766)
        with patch("cognition.body_runtime.remote.RemoteWorldModel") as remote:
            remote.return_value.ping.return_value = True
            runtime._build_worldmodel()
        remote.assert_called_once()
        self.assertEqual(remote.call_args.args[0], "https://127.0.0.1:8766")

    def test_explicit_body_url_port_is_preserved(self):
        runtime = self._runtime("https://127.0.0.1:9443", 8766)
        with patch("cognition.body_runtime.remote.RemoteWorldModel") as remote:
            remote.return_value.ping.return_value = True
            runtime._build_worldmodel()
        self.assertEqual(remote.call_args.args[0], "https://127.0.0.1:9443")


if __name__ == "__main__":
    unittest.main()
