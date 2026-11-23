from cognition.persona_bridge import PersonaBridge


def _bridge(classifier):
    bridge = object.__new__(PersonaBridge)
    bridge._external_llm_fn = classifier
    bridge._system = None
    return bridge


def test_short_status_update_is_decided_semantically_without_keyword_gate():
    calls = []
    bridge = _bridge(lambda *args, **kwargs: calls.append((args, kwargs)) or "NO")

    assert bridge._llm_should_search("restarted") is False
    assert len(calls) == 1
    assert "keyword lists" in calls[0][0][1]


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
    assert "live state" in system
    assert "keyword lists" in system
    assert kwargs["max_tokens"] >= 32
    assert kwargs["_allow_interactive_turn"] is True


def test_architecture_topic_can_still_request_new_external_papers():
    calls = []

    def classifier(prompt, system, **kwargs):
        calls.append((prompt, system, kwargs))
        return "YES"

    bridge = _bridge(classifier)
    query = (
        "Quels articles arXiv publiés cette semaine présentent une architecture "
        "de harnais cognitif synthétique ?"
    )
    receipts = [{
        "completed_at": "2026-11-22T19:00:00Z",
        "query": "Earlier unrelated search",
        "sources": [],
        "trace": {"providers_attempted": ["rss"], "feeds_attempted": []},
    }]

    assert bridge._llm_should_search(query, activity_receipts=receipts) is True
    assert len(calls) == 1
    assert "For requests for recent subject-matter facts or new papers, reply YES." in calls[0][1]


def test_always_mode_semantically_excludes_greetings_but_searches_eligible_topics():
    calls = []

    def classifier(prompt, system, **kwargs):
        calls.append((prompt, system, kwargs))
        return "NO" if "re bonjour" in prompt else "YES"

    bridge = _bridge(classifier)
    assert bridge._llm_should_search(
        "re bonjour Lumina", always_eligible_topics=True,
    ) is False
    assert bridge._llm_should_search(
        "Explain recent findings on Angelman syndrome", always_eligible_topics=True,
    ) is True
    assert len(calls) == 2
    assert all("meaning and context, not phrase matching" in call[1] for call in calls)
    assert all("greets" in call[1] for call in calls)
    assert all("re bonjour Lumina" in call[1] for call in calls)


def test_classifier_failure_does_not_treat_generic_body_question_as_web_search():
    def unavailable(*args, **kwargs):
        raise RuntimeError("classifier unavailable")

    bridge = _bridge(unavailable)

    assert bridge._llm_should_search("what is the body battery") is False


def test_invalid_classifier_output_fails_closed_without_a_second_llm_call():
    calls = []

    def invalid(*args, **kwargs):
        calls.append((args, kwargs))
        return ""

    bridge = _bridge(invalid)
    receipts = [{"query": "earlier search", "sources": [], "trace": {}}]

    assert bridge._llm_should_search(
        "What are the latest research results?", activity_receipts=receipts,
    ) is False
    assert len(calls) == 1
    assert calls[0][1]["max_tokens"] >= 32
    assert calls[0][1]["_allow_interactive_turn"] is True


def test_explicit_per_turn_search_opt_out_overrides_always_mode_instruction():
    opt_out = PersonaBridge._explicit_search_opt_out

    assert opt_out("Do not use web search for this answer.") is True
    assert opt_out("Don't search the web; answer from our conversation.") is True
    assert opt_out("Ne fais pas de recherche sur le web.") is True
    assert opt_out("Sans recherche en ligne, réponds avec les faits connus.") is True
    assert opt_out("Use web search to find current papers.") is False
    assert opt_out("What is the next unverified audit step?") is False
