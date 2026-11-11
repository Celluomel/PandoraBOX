from cognition.global_workspace import GlobalWorkspace


def test_capacity_rejection_returns_false_without_mutation_or_listener_call():
    workspace = GlobalWorkspace(max_items=2)
    admitted = []
    workspace.add_listener(admitted.append)

    assert workspace.broadcast("memory", "alpha evidence", 0.6) is True
    assert workspace.broadcast("attention", "beta focus", 0.5) is True
    before = [item.to_dict() for item in workspace.recent(10)]
    listener_count = len(admitted)

    accepted = workspace.broadcast("curiosity", "gamma exploration", 0.4)

    assert accepted is False
    assert [item.to_dict() for item in workspace.recent(10)] == before
    assert len(admitted) == listener_count
    assert workspace.summary()["total_items"] == 2


def test_capacity_eviction_uses_configured_capacity_and_only_evicts_lower_priority():
    workspace = GlobalWorkspace(max_items=2)
    workspace.broadcast("memory", "alpha evidence", 0.6)
    workspace.broadcast("attention", "beta focus", 0.5)

    assert workspace.broadcast("curiosity", "gamma exploration", 0.8) is True
    items = workspace.recent(10)

    assert len(items) == 2
    assert {item.source for item in items} == {"memory", "curiosity"}


def test_capacity_rejection_is_counted_as_blocked():
    workspace = GlobalWorkspace(max_items=1)
    workspace.broadcast("memory", "alpha evidence", 0.5)

    assert workspace.broadcast("curiosity", "gamma exploration", 0.5) is False
    assert workspace.summary()["blocked_total"] == 1


def test_workspace_state_reads_are_isolated_from_live_state():
    workspace = GlobalWorkspace()
    workspace.update_state(
        "test_writer",
        focus="grounded focus",
        context={"nested": {"value": 1}},
        goals=[{"name": "goal A"}],
    )
    workspace.set_hypotheses("test_writer", [{"label": "hypothesis A"}])

    snapshot = workspace.get_state()
    snapshot.focus = "untracked mutation"
    snapshot.context["nested"]["value"] = 99
    snapshot.goals[0]["name"] = "untracked goal mutation"
    snapshot.active_hypotheses[0]["label"] = "untracked hypothesis mutation"
    snapshot.updated_by.clear()

    live = workspace.get_state()
    assert live.focus == "grounded focus"
    assert live.context["nested"]["value"] == 1
    assert live.goals[0]["name"] == "goal A"
    assert live.active_hypotheses[0]["label"] == "hypothesis A"
    assert any(entry["source"] == "test_writer" for entry in live.updated_by)


def test_state_summary_nested_values_are_isolated():
    workspace = GlobalWorkspace()
    workspace.update_state("test_writer", context={"nested": {"value": 1}})

    summary = workspace.state_summary()
    summary["context"]["nested"]["value"] = 2
    summary["updated_by"].clear()

    live = workspace.get_state()
    assert live.context["nested"]["value"] == 1
    assert live.updated_by
