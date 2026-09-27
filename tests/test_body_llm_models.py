import unittest
from unittest.mock import patch


class BodyLlmModelsTest(unittest.TestCase):
    def test_lmstudio_native_vlm_metadata_is_exposed(self):
        from body_runtime_host.runtime import BodyHost

        host = object.__new__(BodyHost)
        host.config = {"BODY_LLM_BASE_URL": "http://127.0.0.1:1234/v1"}
        native = {
            "data": [
                {"id": "qwen2.5-vl-3b-instruct", "type": "vlm", "arch": "qwen2vl"},
                {"id": "qwen2.5-3b-instruct", "type": "llm", "arch": "qwen2"},
            ]
        }

        def fake_get(url, **_):
            self.assertTrue(url.endswith("/api/v0/models"))
            return native

        with patch("body_runtime_host.runtime._http_get", side_effect=fake_get):
            models = host.body_llm_models()["models"]

        self.assertEqual([item["vision_capable"] for item in models], [True, False])
        self.assertEqual(models[0]["type"], "vlm")


if __name__ == "__main__":
    unittest.main()
