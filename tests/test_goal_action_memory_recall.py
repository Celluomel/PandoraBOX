from types import SimpleNamespace

from cognition.goal_action_executor import GoalActionExecutor


class _MemoryBackend:
    def get_context(self, query, top_k=3):
        return "A sufficiently long retrieved memory relevant to the goal."


def _executor_with_publication(publication):
    executor = GoalActionExecutor.__new__(GoalActionExecutor)
    executor._o = SimpleNamespace(
        semantic_memory=None,
        ai_system=SimpleNamespace(memory_system=_MemoryBackend()),
    )
    executor._add_thought = lambda *args, **kwargs: publication
    return executor


def test_memory_recall_is_not_success_when_no_consumer_admits_thought():
    executor = _executor_with_publication({
        "thought_stream_recorded": False,
        "workspace_broadcast": False,
    })

    result = executor._try_memory_recall(SimpleNamespace(
        topic="audit cognitive memory retrieval"
    ))

    assert result["memory_retrieved"] is True
    assert result["thought_published"] is False
    assert result["success"] is False
    assert result["reason_code"] == "memory_result_not_admitted"
    assert "not admitted" in result["result"]


def test_memory_recall_success_requires_a_confirmed_consumer_admission():
    executor = _executor_with_publication({
        "thought_stream_recorded": True,
        "workspace_broadcast": False,
    })

    result = executor._try_memory_recall(SimpleNamespace(
        topic="audit cognitive memory retrieval"
    ))

    assert result["memory_retrieved"] is True
    assert result["thought_published"] is True
    assert result["success"] is True
    assert result["outcome_status"] == "succeeded"


def test_empty_memory_recall_has_machine_readable_failure_reason():
    executor = GoalActionExecutor.__new__(GoalActionExecutor)
    executor._o = SimpleNamespace(semantic_memory=None, ai_system=None)
    executor._add_thought = lambda *args, **kwargs: {}

    result = executor._try_memory_recall(SimpleNamespace(
        topic="audit cognitive memory retrieval"
    ))

    assert result["success"] is False
    assert result["outcome_status"] == "failed"
    assert result["reason_code"] == "no_relevant_memories"


def test_memory_recall_reports_provider_and_publication_phases_without_content():
    class _SemanticMemory:
        def get_related(self, concept, limit=5):
            return [SimpleNamespace(source=concept, target="grounded concept")]

    executor = _executor_with_publication({
        "thought_stream_recorded": True,
        "workspace_broadcast": False,
    })
    executor._o.semantic_memory = _SemanticMemory()
    phases = []

    result = executor._try_memory_recall(
        SimpleNamespace(topic="audit cognitive memory retrieval"),
        progress_callback=lambda phase, status, **metrics: phases.append(
            (phase, status, metrics)
        ),
    )

    assert result["success"] is True
    assert [(phase, status) for phase, status, _ in phases] == [
        ("sqlite_lookup", "started"),
        ("sqlite_lookup", "completed"),
        ("faiss_lookup", "started"),
        ("faiss_lookup", "completed"),
        ("publication", "started"),
        ("publication", "completed"),
    ]
    assert phases[1][2]["relations"] == 1
    assert phases[3][2]["result_present"] is True
    assert phases[5][2]["thought_stream_recorded"] is True
    assert all("content" not in metrics and "query" not in metrics for _, _, metrics in phases)
