"""Tests for affect being caused by cognitive appraisals and reaching thought output."""
import tempfile
import unittest
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS

# Avoid importing cognition/__init__.py and its optional runtime stack.
ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)
core_package = ModuleType("core")
core_package.__path__ = [str(ROOT / "core")]
sys.modules.setdefault("core", core_package)

from cognition.emotional_state import EmotionalStateManager
from cognition.thought_stream import ThoughtStream
from core.cognitive_event_bus import (
    CognitiveEventBus,
    CONTRADICTION_DETECTED,
    DRIVE_SATISFIED,
    TENSION_RELEASED,
    wire_cognitive_bus,
)


class EmotionalAffectEventTests(unittest.TestCase):
    def make_state(self, folder):
        return EmotionalStateManager(str(Path(folder) / "emotion.json"))

    def test_cognitive_event_changes_blended_emotions_and_records_cause(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            before = state.get_current_values()
            receipt = state.update_from_cognitive_event(
                CONTRADICTION_DETECTED, intensity=0.8, source="audit_test"
            )
            after = state.get_current_values()

            self.assertEqual(receipt["status"], "applied")
            self.assertGreater(after["anxiety"], before["anxiety"])
            self.assertGreater(after["frustration"], before["frustration"])
            self.assertGreater(after["curiosity"], before["curiosity"])
            self.assertIn("contradiction detected", state.get_state_description())
            self.assertEqual(state.get_recent_affect_events(1)[0]["source"], "audit_test")

    def test_unknown_event_does_not_mutate_affect(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            before = state.get_current_values()
            receipt = state.update_from_cognitive_event("unmapped", intensity=1.0)
            self.assertEqual(receipt["status"], "unmapped_event")
            self.assertEqual(state.get_current_values(), before)
            self.assertEqual(state.get_recent_affect_events(), [])

    def test_affect_event_survives_reload_and_snapshot_exposes_new_channels(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.update_from_cognitive_event("surprise_detected", intensity=1.0)
            restored = self.make_state(folder)
            self.assertEqual(
                restored.get_recent_affect_events(1)[0]["event_type"],
                "surprise_detected",
            )
            snapshot = restored.get_snapshot()
            self.assertGreater(snapshot.surprise, 0.05)

    def test_response_context_exposes_live_profile_and_appraisal_cause(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.update_from_cognitive_event(
                "identity_threatened", intensity=0.7, source="self_model"
            )
            modifiers = state.get_response_modifiers()
            self.assertEqual(len(modifiers["affective_profile"]), 11)
            self.assertEqual(
                modifiers["latest_affect_event"]["event_type"], "identity_threatened"
            )
            self.assertEqual(modifiers["latest_affect_event"]["source"], "self_model")

    def test_event_bus_routes_appraisal_and_deduplicates_satiation_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            organism = NS(ai_system=NS(emotional_state=state))
            bus = CognitiveEventBus()
            wire_cognitive_bus(organism, bus)

            bus.emit(CONTRADICTION_DETECTED, {"pressure": 0.8}, source="test")
            self.assertEqual(
                bus.recent(1)[0].payload["affect_outcome"]["status"], "applied"
            )
            payload = {"drive": "social", "amount": 0.1}
            bus.emit(DRIVE_SATISFIED, payload, source="pressure_system")
            bus.emit(TENSION_RELEASED, payload, source="pressure_system")

            events = state.get_recent_affect_events(20)
            self.assertEqual(sum(e["event_type"] == "drive_satisfied" for e in events), 1)
            self.assertEqual(sum(e["event_type"] == "tension_released" for e in events), 0)
            self.assertEqual(
                bus.recent(1)[0].payload["affect_outcome"]["status"], "already_counted"
            )

    def test_thought_stream_uses_live_emotional_description(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.update_from_cognitive_event("surprise_detected", intensity=1.0)
            stream = ThoughtStream.__new__(ThoughtStream)
            stream._o = NS(ai_system=NS(emotional_state=state))

            thought = stream._emotional_thought()
            self.assertIsNotNone(thought)
            self.assertEqual(thought.source, "emotion")
            self.assertIn("surprised", thought.content)


if __name__ == "__main__":
    unittest.main()
