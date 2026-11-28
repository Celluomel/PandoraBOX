from types import SimpleNamespace

from cognition.ai_system import EnhancedAISystem


class _Goals:
    def __init__(self):
        self.goals = {
            "connection": SimpleNamespace(satisfaction=0.23),
            "understanding": SimpleNamespace(satisfaction=0.41),
        }
        self.writes = []

    def discover_goals_from_behavior(self):
        return []

    def detect_goal_conflicts(self):
        return []

    def update_goal_satisfaction(self, goal_name, satisfaction):
        self.writes.append((goal_name, satisfaction))
        self.goals[goal_name].satisfaction = satisfaction


def test_liberty_reflection_does_not_convert_affect_channels_into_goal_progress():
    goals = _Goals()
    system = SimpleNamespace(
        liberty_goals=goals,
        liberty_reflection=None,
        personality=SimpleNamespace(to_dict=lambda: {}),
        emotional_state=SimpleNamespace(emotions={
            "warmth": SimpleNamespace(value=0.99),
            "curiosity": SimpleNamespace(value=0.97),
        }),
    )

    EnhancedAISystem._do_liberty_reflection(system)

    assert goals.writes == []
    assert goals.goals["connection"].satisfaction == 0.23
    assert goals.goals["understanding"].satisfaction == 0.41
