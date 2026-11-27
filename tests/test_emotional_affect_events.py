"""Tests for affect being caused by cognitive appraisals and reaching thought output."""
import tempfile
import json
import unittest
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

# Load the focused modules by file path so this unit test does not replace the
# process-wide cognition/core packages and alter later integration-test imports.
ROOT = Path(__file__).resolve().parents[1]


def _load_focused_module(alias, relative_path):
    spec = importlib.util.spec_from_file_location(alias, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


_emotional_state_module = _load_focused_module(
    "_lumina_test_emotional_state", "cognition/emotional_state.py",
)
EmotionalStateManager = _emotional_state_module.EmotionalStateManager
affect_self_report_context = _load_focused_module(
    "_lumina_test_self_description", "cognition/self_description.py",
).affect_self_report_context
ThoughtStream = _load_focused_module(
    "_lumina_test_thought_stream", "cognition/thought_stream.py",
).ThoughtStream
_event_bus = _load_focused_module(
    "_lumina_test_cognitive_event_bus", "core/cognitive_event_bus.py",
)
CognitiveEventBus = _event_bus.CognitiveEventBus
CONTRADICTION_DETECTED = _event_bus.CONTRADICTION_DETECTED
DRIVE_SATISFIED = _event_bus.DRIVE_SATISFIED
TENSION_RELEASED = _event_bus.TENSION_RELEASED
wire_cognitive_bus = _event_bus.wire_cognitive_bus


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

    def test_personality_changes_neutral_baselines_without_pinning_them_high(self):
        personality = NS(to_dict=lambda: {
            "curiosity": 0.64, "creativity": 0.57, "confidence": 0.52,
            "empathy_emotional": 0.78, "empathy": 0.63, "pragmatism": 0.59,
        })
        with tempfile.TemporaryDirectory() as folder:
            state = EmotionalStateManager(str(Path(folder) / "emotion.json"), personality)
            self.assertGreater(state.emotions["curiosity"].baseline, 0.30)
            self.assertLess(state.emotions["curiosity"].baseline, 0.60)
            self.assertLess(state.emotions["warmth"].baseline, 0.60)
            self.assertLess(state.emotions["satisfaction"].baseline, 0.60)

    def test_legacy_high_baselines_migrate_while_preserving_affect_deviation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "emotion.json"
            now = 1_794_434_000.0
            path.write_text(json.dumps({
                "emotions": {
                    "curiosity": {"value": 0.99, "baseline": 0.85, "last_updated_ts": now},
                    "warmth": {"value": 0.98, "baseline": 0.85, "last_updated_ts": now},
                    "satisfaction": {"value": 0.95, "baseline": 0.85, "last_updated_ts": now},
                },
                "history": [], "recent_affect_events": [],
            }))
            state = EmotionalStateManager(str(path))
            self.assertAlmostEqual(state.emotions["curiosity"].baseline, 0.30)
            self.assertAlmostEqual(state.emotions["curiosity"].value, 0.44)
            migrated = json.loads(path.read_text())
            self.assertEqual(migrated["schema_version"], 2)
            self.assertAlmostEqual(migrated["emotions"]["curiosity"]["baseline"], 0.30)

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

    def test_non_cognitive_affect_mutations_record_source_and_channel_deltas(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.update_from_interaction("Positive", "High", intensity=0.8)
            interaction = state.get_recent_affect_events(1)[0]
            self.assertEqual(interaction["event_type"], "interaction_appraisal")
            self.assertEqual(interaction["source"], "update_from_interaction")
            self.assertEqual(interaction["cause_context"], {
                "valence": "positive", "arousal": "high",
            })
            self.assertTrue(interaction["changes"])

            state.update_from_feedback(False)
            feedback = state.get_recent_affect_events(1)[0]
            self.assertEqual(feedback["event_type"], "user_feedback")
            self.assertEqual(feedback["cause_context"], {"feedback": "negative"})
            self.assertTrue(feedback["changes"])

            state.update_from_time_gap(36.0)
            gap = state.get_recent_affect_events(1)[0]
            self.assertEqual(gap["event_type"], "conversation_gap")
            self.assertEqual(gap["cause_context"], {"gap_hours": "36.0"})
            self.assertTrue(gap["changes"])

            state.receive_self_influence({"warmth": 0.04}, source="threat_response")
            influence = state.get_recent_affect_events(1)[0]
            self.assertEqual(influence["event_type"], "self_influence")
            self.assertEqual(influence["source"], "threat_response")
            self.assertGreater(influence["changes"]["warmth"], 0)

    def test_affect_regulation_records_the_channels_it_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.emotions["warmth"].value = min(1.0, state.emotions["warmth"].baseline + 0.5)
            state.regulate()
            receipt = state.get_recent_affect_events(1)[0]
            self.assertEqual(receipt["event_type"], "affect_regulation")
            self.assertEqual(receipt["source"], "emotional_state_regulator")
            self.assertLess(receipt["changes"]["warmth"], 0)

    def test_personality_baseline_recalibration_has_a_separate_receipt(self):
        personality = NS(to_dict=lambda: {
            "curiosity": 0.95, "creativity": 0.90, "confidence": 0.80,
            "empathy_emotional": 0.85, "empathy": 0.80, "pragmatism": 0.20,
        })
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            before = state.emotions["curiosity"].baseline
            state.recalibrate_baselines(personality)
            receipt = state.get_recent_affect_events(1)[0]
            self.assertEqual(receipt["event_type"], "baseline_recalibration")
            self.assertEqual(receipt["changes"], {})
            self.assertNotEqual(receipt["baseline_changes"]["curiosity"], 0)
            self.assertNotEqual(state.emotions["curiosity"].baseline, before)

    def test_subthreshold_decay_accumulates_until_it_can_be_recorded(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            emotion = state.emotions["warmth"]
            emotion.value = min(1.0, emotion.baseline + 0.5)
            base_ts = 1_000_000.0
            emotion.last_updated_ts = base_ts
            original_value = emotion.value

            emotion.decay(base_ts + 0.1)
            self.assertEqual(emotion.value, original_value)
            self.assertEqual(emotion.last_updated_ts, base_ts)

            with patch.object(_emotional_state_module.time, "time", return_value=base_ts + 100.0):
                state.apply_time_decay()
            recent = state.get_recent_affect_events(1)
            self.assertTrue(recent)
            self.assertEqual(recent[0]["event_type"], "time_decay")
            self.assertNotEqual(emotion.value, original_value)

    def test_feedback_clipped_at_channel_limits_does_not_claim_an_affect_event(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            for name in ("satisfaction", "enthusiasm"):
                state.emotions[name].value = 1.0
            state.emotions["anxiety"].value = 0.0

            state.update_from_feedback(True)

            self.assertEqual(state.get_recent_affect_events(), [])

    def test_event_bus_routes_appraisal_and_deduplicates_satiation_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            organism = NS(ai_system=NS(emotional_state=state))
            bus = CognitiveEventBus()
            wire_cognitive_bus(organism, bus)

            bus.emit(
                CONTRADICTION_DETECTED,
                {"pressure": 0.8, "turn_id": "turn-affect-42"},
                source="test",
            )
            self.assertEqual(
                bus.recent(1)[0].payload["affect_outcome"]["status"], "applied"
            )
            self.assertEqual(
                state.get_recent_affect_events(1)[0]["turn_id"], "turn-affect-42"
            )
            payload = {"drive": "social", "amount": 0.1}
            bus.emit(DRIVE_SATISFIED, payload, source="pressure_system")
            bus.emit(TENSION_RELEASED, payload, source="pressure_system")

            events = state.get_recent_affect_events(20)
            self.assertEqual(sum(e["event_type"] == "drive_satisfied" for e in events), 1)
            self.assertEqual(sum(e["event_type"] == "tension_released" for e in events), 0)
            latest = state.get_response_modifiers()["latest_affect_event"]
            self.assertEqual(latest["cause_context"], {"drive": "social"})
            affect_context = affect_self_report_context(
                state.get_current_values(), state.get_state_description(), latest
            )
            self.assertIn("drive=social", affect_context)
            self.assertEqual(
                bus.recent(1)[0].payload["affect_outcome"]["status"], "already_counted"
            )

    def test_contradiction_receipt_reports_each_downstream_handler_return(self):
        tension_calls = []
        curiosity_calls = []
        workspace_calls = []
        organism = NS(
            ai_system=NS(emotional_state=NS(update_from_cognitive_event=lambda *a, **k: {
                "status": "applied",
            })),
            tension_engine=NS(add_contradiction_pressure=tension_calls.append),
            curiosity=NS(stimulate=lambda *a, **k: curiosity_calls.append((a, k))),
            workspace=NS(broadcast=lambda **kwargs: workspace_calls.append(kwargs)),
        )
        bus = CognitiveEventBus()
        wire_cognitive_bus(organism, bus)

        handled = bus.emit(
            CONTRADICTION_DETECTED,
            {"topic": "memory consistency", "pressure": 0.75},
            source="audit_test",
        )

        event = bus.recent_of_type(CONTRADICTION_DETECTED, 1)[0]
        reaction = event.payload["contradiction_reaction"]
        self.assertEqual(handled, 2)
        self.assertEqual(event.payload["affect_outcome"]["status"], "applied")
        self.assertEqual(reaction, {
            "tension_status": "returned",
            "curiosity_status": "returned",
            "workspace_status": "returned",
        })
        self.assertEqual(len(tension_calls), 1)
        self.assertEqual(len(curiosity_calls), 1)
        self.assertEqual(len(workspace_calls), 1)

        exact_event, exact_handled = bus.emit_with_receipt(
            CONTRADICTION_DETECTED,
            {"topic": "second event", "pressure": 0.4},
            source="audit_test",
        )
        self.assertIs(exact_event, bus.recent_of_type(CONTRADICTION_DETECTED, 1)[0])
        self.assertEqual(exact_handled, 2)
        self.assertEqual(
            exact_event.payload["contradiction_reaction"]["workspace_status"],
            "returned",
        )

    def test_contradiction_receipt_distinguishes_missing_and_failed_handlers(self):
        def fail(*_args, **_kwargs):
            raise RuntimeError("private details must not enter receipt")

        organism = NS(
            tension_engine=NS(add_contradiction_pressure=fail),
            curiosity=None,
            workspace=NS(broadcast=lambda **_kwargs: None),
        )
        bus = CognitiveEventBus()
        wire_cognitive_bus(organism, bus)
        bus.emit(CONTRADICTION_DETECTED, {"pressure": 0.5}, source="audit_test")

        reaction = bus.recent_of_type(CONTRADICTION_DETECTED, 1)[0].payload[
            "contradiction_reaction"
        ]
        self.assertEqual(reaction["tension_status"], "failed_RuntimeError")
        self.assertEqual(reaction["curiosity_status"], "unavailable")
        self.assertEqual(reaction["workspace_status"], "returned")
        self.assertNotIn("private details", repr(reaction))

    def test_affect_event_context_does_not_persist_free_text(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.make_state(folder)
            state.update_from_cognitive_event(
                "drive_satisfied", intensity=0.5, source="pressure_system",
                context={"drive": "social", "topic": "private free text"},
            )
            latest = state.get_recent_affect_events(1)[0]
            self.assertEqual(latest["cause_context"], {"drive": "social"})

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

