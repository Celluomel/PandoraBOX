from cognition.persona_bridge import PersonaBridge


def _bridge(classifier):
    bridge = object.__new__(PersonaBridge)
    bridge._external_llm_fn = classifier
    bridge._system = None
    return bridge


def test_short_status_update_does_not_call_search_classifier():
    calls = []
    bridge = _bridge(lambda *args, **kwargs: calls.append((args, kwargs)) or "YES")

    assert bridge._llm_should_search("restarted") is False
    assert calls == []


def test_explicit_short_research_request_reaches_classifier():
    calls = []
    bridge = _bridge(lambda *args, **kwargs: calls.append((args, kwargs)) or "YES")

    assert bridge._llm_should_search("Find papers") is True
    assert len(calls) == 1


def test_question_fragment_reaches_classifier():
    calls = []
    bridge = _bridge(lambda *args, **kwargs: calls.append((args, kwargs)) or "NO")

    assert bridge._llm_should_search("News?") is False
    assert len(calls) == 1


def test_classifier_failure_does_not_treat_generic_body_question_as_web_search():
    def unavailable(*args, **kwargs):
        raise RuntimeError("classifier unavailable")

    bridge = _bridge(unavailable)

    assert bridge._llm_should_search("what is the body battery") is False
