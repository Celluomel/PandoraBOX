import json
import threading
from unittest.mock import patch

from managers.llm_manager import LLMManager, LMStudioProvider, _structured_response_format


SCHEMA = {
    "name": "sample_review",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
        "additionalProperties": False,
    },
}


def test_explicit_schema_maps_to_openai_compatible_json_schema():
    assert _structured_response_format({"json_schema": SCHEMA}) == {
        "type": "json_schema",
        "json_schema": SCHEMA,
    }


def test_legacy_json_mode_maps_to_permissive_schema_not_json_object():
    result = _structured_response_format({"json_mode": True})
    assert result["type"] == "json_schema"
    assert result["json_schema"]["strict"] is False
    assert result["json_schema"]["schema"] == {"type": "object"}


def test_lmstudio_nonstream_request_transmits_response_schema():
    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": '{"ok":true}'}}]}

    provider = LMStudioProvider(model="test", base_url="http://localhost:1234/v1")
    with patch("managers.llm_manager.requests.post", return_value=Response()) as post:
        result = provider._generate_messages(
            [{"role": "user", "content": "Review"}], json_schema=SCHEMA,
        )

    assert json.loads(result) == {"ok": True}
    payload = post.call_args.kwargs["json"]
    assert payload["response_format"] == {
        "type": "json_schema",
        "json_schema": SCHEMA,
    }


def test_lmstudio_stream_request_transmits_response_schema():
    chunk_sizes = []

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def iter_lines(self, chunk_size=512):
            chunk_sizes.append(chunk_size)
            yield b'data: {"choices":[{"delta":{"content":"first"}}]}'
            yield b'data: {"choices":[{"delta":{"content":" token"}}]}'
            yield b'data: [DONE]'

    provider = LMStudioProvider(model="test", base_url="http://localhost:1234/v1")
    with patch("managers.llm_manager.requests.post", return_value=Response()) as post:
        result = list(provider._generate_messages_stream(
            [{"role": "user", "content": "Review"}], json_schema=SCHEMA,
        ))

    assert result == ["first", " token"]
    assert chunk_sizes == [1]
    payload = post.call_args.kwargs["json"]
    assert payload["response_format"] == {
        "type": "json_schema",
        "json_schema": SCHEMA,
    }


def test_structured_background_request_bypasses_native_endpoint():
    class Provider:
        model = "test"
        native_called = False

        def generate_background_result(self, *_args, **_kwargs):
            self.native_called = True
            raise AssertionError("native endpoint cannot carry response_format")

        def _generate_messages(self, _messages, **kwargs):
            assert kwargs["json_schema"] == SCHEMA
            return '{"ok":true}'

    provider = Provider()
    manager = LLMManager.__new__(LLMManager)
    manager.provider = provider
    manager.text_model = "test"
    manager._provider_lock = threading.Lock()
    manager._chat_active = threading.Event()

    result = manager.generate_bare_result("review", json_schema=SCHEMA)

    assert result["status"] == "ok"
    assert result["text"] == '{"ok":true}'
    assert provider.native_called is False
