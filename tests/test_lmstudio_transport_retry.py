from unittest.mock import Mock, patch

import requests

from managers.llm_manager import LLMManager, LMStudioProvider


def test_native_connect_timeout_does_not_retry_same_unreachable_host():
    provider = LMStudioProvider(model="gemma")
    provider.generate_background_result = Mock(
        side_effect=requests.exceptions.ConnectTimeout("local listener unavailable")
    )
    provider._generate_messages = Mock(return_value="should not be called")
    provider._generate_messages_stream = Mock(return_value=iter(["should not be called"]))

    result = LLMManager(provider).generate_bare_result("background task")

    assert result["status"] == "error"
    assert result["reason"] == "ConnectTimeout"
    assert result["provider_call_count"] == 1
    provider._generate_messages.assert_not_called()
    provider._generate_messages_stream.assert_not_called()


def test_native_endpoint_compatibility_error_still_uses_openai_fallback():
    provider = LMStudioProvider(model="gemma")
    provider.generate_background_result = Mock(
        side_effect=RuntimeError("native endpoint returned unsupported status 404")
    )
    provider._generate_messages = Mock(return_value="fallback answer")

    result = LLMManager(provider).generate_bare_result("background task")

    assert result["status"] == "ok"
    assert result["text"] == "fallback answer"
    assert result["provider_call_count"] == 2
    provider._generate_messages.assert_called_once()


def test_lmstudio_timeout_uses_short_connect_and_separate_generation_deadline():
    provider = LMStudioProvider(model="gemma")
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

    with patch("managers.llm_manager.requests.post", return_value=response) as post:
        assert provider._generate_messages(
            [{"role": "user", "content": "test"}], timeout=60
        ) == "ok"

    assert post.call_args.kwargs["timeout"] == (3.0, 60.0)
