import base64
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

_MODULE_PATH = Path(__file__).resolve().parents[1] / "cognition" / "body_runtime" / "remote.py"
_SPEC = importlib.util.spec_from_file_location("body_remote_test_target", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
RemoteWorldModel = _MODULE.RemoteWorldModel


class RemoteWorldModelAuthTests(unittest.TestCase):
    def test_basic_auth_header_is_sent_to_secure_body(self):
        client = RemoteWorldModel("https://body.example", auth_username="body", auth_password="secret")
        with patch.object(_MODULE.urllib.request, "urlopen") as open_url:
            open_url.return_value.__enter__.return_value.read.return_value = b"{}"
            client.ping()
        request = open_url.call_args.args[0]
        expected = "Basic " + base64.b64encode(b"body:secret").decode("ascii")
        self.assertEqual(request.get_header("Authorization"), expected)
        self.assertEqual(request.full_url, "https://body.example/health")

    def test_requests_without_credentials_remain_compatible(self):
        client = RemoteWorldModel("http://127.0.0.1:8766")
        with patch.object(_MODULE.urllib.request, "urlopen") as open_url:
            open_url.return_value.__enter__.return_value.read.return_value = b"{}"
            self.assertTrue(client.ping())
        self.assertIsNone(open_url.call_args.args[0].get_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
