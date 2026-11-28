"""Shared, language-independent interpretation of producer-owned thought IDs.

Only typed metadata is considered. Content text is deliberately ignored, so
generated prose and language choice cannot manufacture a cognitive signal.
"""
from __future__ import annotations

from typing import Any, Mapping


_SIGNAL_TYPES = (
    ("uncertainty", frozenset({"curiosity", "open_question", "uncertainty"})),
    ("tension", frozenset({
        "tension_awareness", "associative_tension",
        "associative_contradiction", "contradiction",
    })),
    ("opportunity", frozenset({
        "goal_evaluation", "associative_goal", "opportunity",
        "action_affordance",
    })),
)


def signal_for_thought(thought: Mapping[str, Any] | None) -> str | None:
    """Return a validated producer signal, or ``None`` when none is present."""
    if not isinstance(thought, Mapping):
        return None
    source = str(thought.get("source") or "").strip().casefold()
    if source.startswith(("goal_action.", "thought_evaluator.")) or source in {
        "insight", "reflection",
    }:
        return None

    explicit = str(thought.get("cognitive_signal") or "").strip().casefold()
    if explicit in {name for name, _ in _SIGNAL_TYPES}:
        return explicit

    thought_type = str(thought.get("thought_type") or "").strip().casefold()
    for signal, schema_ids in _SIGNAL_TYPES:
        if thought_type in schema_ids:
            return signal
    return None
