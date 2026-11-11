from __future__ import annotations

import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cognition.autonomous_reflection import (
    AutonomousReflectionEngine,
    ReflectionRecord,
    ReflectionState,
)


class _Validator:
    def epistemic_context(self):
        return ""

    def validate_reflection(self, **_kwargs):
        return SimpleNamespace(grounded=False, reason="insufficient state overlap")


class _SideEffect:
    def __init__(self):
        self.calls = []

    def add_tension(self, value):
        self.calls.append(("tension", value))

    def broadcast(self, **kwargs):
        self.calls.append(("broadcast", kwargs))


class AutonomousReflectionGroundingTests(unittest.TestCase):
    def _engine(self):
        engine = object.__new__(AutonomousReflectionEngine)
        engine._o = SimpleNamespace()
        engine._ai = SimpleNamespace()
        engine._epistemic = _Validator()
        engine._lock = threading.RLock()
        engine._state = ReflectionState()
        engine._build_state_snapshot = lambda: {
            "beliefs": "stable processing preference",
            "active_threads": "",
            "goal_urgencies": "curiosity=0.2",
            "phi": 0.4,
            "known_tensions": "none",
        }
        engine._llm_call = lambda *_args: "There is a tension about a completely unrelated topic."
        engine._save = lambda: None
        engine.records = []
        engine._store_record = engine.records.append
        return engine

    def test_inconsistent_reflection_is_audited_but_not_written_as_tension_or_workspace(self):
        effects = _SideEffect()
        engine = self._engine()
        engine._o.ai_system = SimpleNamespace(self_concept=effects)
        engine._o.workspace = effects

        engine._run_contradiction_surfacing(12)

        self.assertEqual(len(engine.records), 1)
        self.assertEqual(engine.records[0].grounding_status, "inconsistent")
        self.assertEqual(engine.records[0].grounding_reason, "insufficient state overlap")
        self.assertEqual(effects.calls, [])

    def test_unvalidated_reflection_record_does_not_absorb_symbols_or_propose_changes(self):
        engine = self._engine()
        engine._store_record = AutonomousReflectionEngine._store_record.__get__(
            engine, AutonomousReflectionEngine
        )
        record = ReflectionRecord(
            mode="wonder", output="I notice that I consistently seek novelty.",
            grounding_status="question_only",
        )

        with patch("cognition.symbol_system.get_symbol_system") as get_symbols, \
             patch("cognition.reflection_absorber.absorb_reflection") as absorb, \
             patch("cognition.reflection_proposal_bridge.maybe_propose_from_reflection") as propose:
            engine._store_record(record)

        self.assertEqual(engine._state.total_reflections, 1)
        get_symbols.assert_not_called()
        absorb.assert_not_called()
        propose.assert_not_called()


if __name__ == "__main__":
    unittest.main()
