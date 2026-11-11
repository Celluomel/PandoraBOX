from types import SimpleNamespace

from cognition.global_workspace import GlobalWorkspace
from cognition.workspace_state_sync import sync_workspace_state


def test_workspace_sync_preserves_context_from_independent_modules():
    workspace = GlobalWorkspace()
    organism = SimpleNamespace(
        world_model=SimpleNamespace(
            summary=lambda: {"source": "real_sensor", "objects": ["chair"]}
        ),
        narrative_identity=None,
        ai_system=SimpleNamespace(goal_engine=None),
        skill_registry=None,
    )
    internal_loop = SimpleNamespace(
        _counterfactual_sim=None,
        _consequence_model=None,
        _introspective_observer=SimpleNamespace(
            status=lambda: {"state": "reflecting"}
        ),
    )

    sync_workspace_state(workspace, organism=organism, internal_loop=internal_loop)

    state = workspace.get_state()
    assert state.context["world_model"] == {
        "source": "real_sensor",
        "objects": ["chair"],
    }
    assert state.context["introspection"] == {"state": "reflecting"}
    assert [entry["source"] for entry in state.updated_by] == [
        "world_model",
        "introspective_observer",
    ]
