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


def test_internal_state_classifier_is_directed_to_use_runtime_evidence():
    calls = []

    def classifier(prompt, system, **kwargs):
        calls.append((prompt, system, kwargs))
        return "NO"

    bridge = _bridge(classifier)
    query = (
        "Quelles émotions fonctionnelles sont actives en toi maintenant? "
        "Décris-les selon les signaux internes disponibles."
    )

    assert bridge._llm_should_search(query) is False
    assert len(calls) == 1
    _, system, kwargs = calls[0]
    assert "current internal state" in system
    assert "supplied internal context" in system
    assert "explicit request for external research" in system
    assert kwargs["max_tokens"] == 5


def test_classifier_failure_does_not_treat_generic_body_question_as_web_search():
    def unavailable(*args, **kwargs):
        raise RuntimeError("classifier unavailable")

    bridge = _bridge(unavailable)

    assert bridge._llm_should_search("what is the body battery") is False


def test_explicit_per_turn_search_opt_out_overrides_always_mode_instruction():
    opt_out = PersonaBridge._explicit_search_opt_out

    assert opt_out("Do not use web search for this answer.") is True
    assert opt_out("Don't search the web; answer from our conversation.") is True
    assert opt_out("Ne fais pas de recherche sur le web.") is True
    assert opt_out("Sans recherche en ligne, réponds avec les faits connus.") is True
    assert opt_out("Use web search to find current papers.") is False
    assert opt_out("What is the next unverified audit step?") is False
