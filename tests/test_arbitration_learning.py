from types import SimpleNamespace

import cognition.arbitration_learning as learning


def test_reviewed_arbitration_outcome_changes_weights_read_by_live_arbitration(
    tmp_path, monkeypatch
):
    tracker = learning.ArbitrationLearningTracker(
        str(tmp_path / "arbitration_learning.json")
    )
    monkeypatch.setattr(learning, "_tracker", None)
    monkeypatch.setattr(learning, "ArbitrationLearningTracker", lambda: tracker)

    # InternalThoughtLoop and executive_arbitration must resolve the same
    # cached instance for review updates to affect decisions without a restart.
    assert learning.get_tracker() is tracker
    before = learning.get_learned_weights()
    from cognition.executive_arbitration import _get_base_weights

    assert _get_base_weights() == before

    goal = {"id": "goal-1", "type": "goal"}
    candidate = SimpleNamespace(candidate=goal, utility_terms={"predicted": 1.0})
    result = SimpleNamespace(arbitrated_winner=goal, candidates=[candidate])
    live_goal = SimpleNamespace(actions_taken=0, status="active")
    goal_engine = SimpleNamespace(get_goal_by_id=lambda goal_id: live_goal)

    tracker.record(result, cycle=10, goal_engine=goal_engine)
    live_goal.actions_taken = 1
    report = tracker.review(goal_engine, cycle=10 + learning.REVIEW_DELAY_CYCLES)

    after = learning.get_learned_weights()
    assert report["reviewed"] == 1
    assert report["good"] == 1
    assert tracker.learned_delta()["predicted"] > 0
    assert after["predicted"] > before["predicted"]
    assert _get_base_weights()["predicted"] == after["predicted"]
