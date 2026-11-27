from types import SimpleNamespace

from cognition.self_model_influence import SelfModelInfluence


class _Receiver:
    def __init__(self):
        self.received = []

    def receive_self_influence(self, value):
        self.received.append(dict(value))


def test_attention_influence_uses_numeric_measurements():
    attention = _Receiver()
    organism = SimpleNamespace(attention=attention)

    nudges = SelfModelInfluence()._apply_attention(
        organism,
        phi=0.3,
        relational_stability=0.8,
        surprise_index=0.5,
        novelty_pressure=0.12,
        strength=0.5,
    )

    expected = {
        "identity": 0.012,
        "user": 0.024,
        "memory": 0.02,
        "curiosity": 0.05,
    }
    assert set(nudges) == set(expected)
    assert all(abs(nudges[key] - value) < 1e-9 for key, value in expected.items())
    assert attention.received == [nudges]


def test_goal_and_emotion_influence_use_structured_state_not_descriptions():
    ecology = _Receiver()
    affect = _Receiver()
    organism = SimpleNamespace(goal_ecology=ecology, emotional_state=affect)
    influence = SelfModelInfluence()

    goal_biases = influence._apply_goal_biases(
        organism,
        trend="stable",
        relational_stability=0.8,
        value_consistency=0.7,
        strength=0.5,
        novelty_active=False,
    )
    affect_nudges = influence._apply_emotion_nudges(
        organism, trend="integrating", strength=0.5,
    )

    assert set(goal_biases) == {"help_user", "connect", "maintain_coherence"}
    assert abs(goal_biases["help_user"] - 0.0385) < 1e-9
    assert abs(goal_biases["connect"] - 0.038) < 1e-9
    assert abs(goal_biases["maintain_coherence"] - 0.01) < 1e-9
    assert ecology.received == [goal_biases]
    assert affect_nudges == {"satisfaction": 0.0075, "anxiety": -0.005}
    assert affect.received == [affect_nudges]


def test_memory_bias_passes_full_state_as_semantic_context_without_word_selection():
    context = (
        "channels: curiosity -0.20, warmth +0.18, anxiety +0.07; mixed affect"
    )

    query = SelfModelInfluence()._compute_memory_bias(
        context,
        trend="dispersing",
        values="care, fairness",
        narrative_thread="Learning to keep multiple sources in view.",
    )

    assert context in query
    assert "coherence trend: dispersing" in query
    assert "care, fairness" in query
    assert "Learning to keep multiple sources in view." in query
