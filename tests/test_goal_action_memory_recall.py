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
