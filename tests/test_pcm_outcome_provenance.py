import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from cognition.cognitive_organism import CognitiveOrganism
from cognition.predictive_consequence_model import PredictiveConsequenceModel
from cognition.cognitive_attention_engine import CognitiveAttentionEngine


class PCMOutcomeProvenanceTests(unittest.TestCase):
    def _model(self):
        model = PredictiveConsequenceModel.__new__(PredictiveConsequenceModel)
        model._records_lock = threading.RLock()
        model._records = []
        model._pending = None
        model._save = Mock()
        model._calibration_engine = None
        return model

    def test_unattributed_positive_label_is_stored_as_unrated(self):
        model = self._model()

        model.record_observed_transition(
            "social", [0.5] * 5, [0.4, 0.5, 0.5, 0.5, 0.5],
            outcome="positive",
            turn_id="turn-a",
        )

        record = model._records[0]
        self.assertEqual(record.outcome, "unrated")
        self.assertEqual(record.outcome_source, "unattributed")
        self.assertEqual(record.turn_id, "turn-a")

    def test_validated_action_probe_keeps_its_observed_outcome(self):
        model = self._model()

        model.record_observed_transition(
            "memory_recall", [0.5] * 5, [0.5, 0.8, 0.6, 0.5, 0.5],
            outcome="positive", outcome_source="validated_action_probe",
        )

        record = model._records[0]
        self.assertEqual(record.outcome, "positive")
        self.assertEqual(record.outcome_source, "validated_action_probe")

    def test_record_outcome_persists_turn_correlation_and_reports_save(self):
        model = self._model()
        model._pending = ("technical", [0.8] * 5, 3)

        persisted = model.record_outcome(
            [0.7, 0.75, 0.8, 0.8, 0.7],
            response_text="turn-correlated response",
            turn_id="turn-pcm-42",
        )

        self.assertTrue(persisted)
        self.assertEqual(model._records[0].turn_id, "turn-pcm-42")
        self.assertEqual(
            model._records[0].response_hash,
            model._response_hash("turn-correlated response"),
        )

    def test_failed_persistence_rolls_back_transition_and_reports_failure(self):
        model = self._model()
        model._save.return_value = False
        model._calibration_engine = Mock()

        persisted = model.record_observed_transition(
            "memory_recall", [0.5] * 3, [0.5, 0.6, 0.7],
            outcome="positive", outcome_source="validated_action_probe",
            resolve_calibration=True,
        )

        self.assertFalse(persisted)
        self.assertEqual(model._records, [])
        model._calibration_engine.resolve_prediction.assert_not_called()

    def test_organism_captures_pcm_after_turn_costs_are_applied(self):
        events = []

        class PCM:
            _pending = ("technical", [0.8] * 5, 2)
            _response_hash = staticmethod(PredictiveConsequenceModel._response_hash)

            def read_state(self):
                events.append("read_after")
                return [0.7, 0.75, 0.7, 0.6, 0.4]

            def record_outcome(self, state_after, **kwargs):
                events.append("record_outcome")
                self.state_after = list(state_after)
                self.kwargs = kwargs
                self._pending = None
                return True

        pcm = PCM()
        economy = Mock()
        economy.cognitive_energy = 0.7
        economy.social_energy = 0.75
        economy.record_interaction.side_effect = lambda **_: events.append("economy_interaction")
        economy.record_llm_call.side_effect = lambda **_: events.append("economy_llm")

        class Stub:
            def __getattr__(self, name):
                value = Mock()
                setattr(self, name, value)
                return value

        organism = Stub()
        organism._loop = SimpleNamespace(
            _consequence_model=pcm,
            _resource_economy=economy,
            _auto_experiment=None,
        )
        organism.energy.mode.return_value = "normal"
        organism.energy.drain.side_effect = lambda *_: events.append("energy_drain")
        organism.energy.level.return_value = 0.7
        organism.ai_system = SimpleNamespace(
            emotional_state=SimpleNamespace(overall_arousal=0.4),
            _interaction_count=2,
        )
        organism.meta_cognition.post_response_eval.return_value = SimpleNamespace(
            suggested_improvement="",
        )
        organism.homeostasis.last_report.return_value = None
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        organism._data_dir = temp_dir.name

        receipt = CognitiveOrganism._post_interaction(
            organism,
            user_input="Explain a technical audit result.",
            response="A concise explanation.",
            cycle_data={"emo_values": {}},
            decision=None,
            turn_id="turn-pcm-test",
        )

        self.assertLess(events.index("energy_drain"), events.index("read_after"))
        self.assertLess(events.index("economy_interaction"), events.index("read_after"))
        self.assertLess(events.index("economy_llm"), events.index("read_after"))
        self.assertEqual(pcm.state_after, [0.7, 0.75, 0.7, 0.6, 0.4])
        self.assertEqual(pcm.kwargs["outcome"], "unrated")
        self.assertEqual(pcm.kwargs["turn_id"], "turn-pcm-test")
        self.assertEqual(receipt["pcm_outcome"]["status"], "persisted")
        self.assertEqual(receipt["pcm_outcome"]["turn_id"], "turn-pcm-test")

    def test_explicit_rating_attaches_to_exact_response_and_attention_snapshot_once(self):
        model = self._model()
        model.record_observed_transition(
            "analytical", [0.5] * 5, [0.4, 0.5, 0.5, 0.5, 0.5],
            response_text="Answer for turn A",
            attention_weights_at_turn={"semantic_memory": 0.7, "self_model": 0.3},
            attention_context_key_at_turn="technical|high-trust",
        )

        receipt = model.record_explicit_feedback("Answer for turn A", True)
        duplicate = model.record_explicit_feedback("Answer for turn A", False)

        self.assertTrue(receipt["matched"])
        self.assertEqual(receipt["attention_weights_at_turn"]["semantic_memory"], 0.7)
        self.assertEqual(receipt["attention_context_key_at_turn"], "technical|high-trust")
        self.assertIsNone(duplicate)
        self.assertEqual(model._records[0].outcome, "positive")
        claims = model.claim_attention_feedback_batch([receipt["response_hash"]])
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["attention_context_key_at_turn"], "technical|high-trust")
        self.assertEqual(model.claim_attention_feedback(receipt["response_hash"]), None)
        self.assertTrue(model.mark_attention_feedback_applied(receipt["response_hash"]))
        self.assertTrue(model._records[0].attention_feedback_applied)

    def test_competing_consumers_can_claim_a_rating_only_once(self):
        model = self._model()
        model.record_observed_transition(
            "analytical", [0.5] * 5, [0.5] * 5,
            response_text="A unique reply",
            attention_weights_at_turn={"memory": 1.0},
        )
        receipt = model.record_explicit_feedback("A unique reply", True)
        claims = []
        barrier = threading.Barrier(3)

        def claim():
            barrier.wait()
            claims.append(model.claim_attention_feedback(receipt["response_hash"]))

        workers = [threading.Thread(target=claim) for _ in range(2)]
        for worker in workers:
            worker.start()
        barrier.wait()
        for worker in workers:
            worker.join()

        self.assertEqual(sum(item is not None for item in claims), 1)

    def test_legacy_outcome_labels_are_migrated_as_unattributed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pcm.json"
            path.write_text(json.dumps({"records": [{
                "action_type": "social",
                "state_before": [0.5] * 5,
                "state_after": [0.5] * 5,
                "delta": [0.0] * 5,
                "outcome": "negative",
            }]}), encoding="utf-8")
            model = PredictiveConsequenceModel.__new__(PredictiveConsequenceModel)
            model._path = path
            model._records_lock = threading.RLock()
            model._records = []

            model._load()

        self.assertEqual(model._records[0].outcome, "unrated")
        self.assertEqual(model._records[0].outcome_source, "legacy_unattributed")

    def test_context_attention_feedback_uses_response_context_not_live_context(self):
        engine = CognitiveAttentionEngine.__new__(CognitiveAttentionEngine)
        engine._context_memory = Mock()
        engine._last_context_key = "later-turn-context"

        engine.update_from_context_feedback(
            1.0,
            weights_at_feedback={"semantic_memory": 0.8},
            context_key="rated-response-context",
        )

        engine._context_memory.update.assert_called_once_with(
            "rated-response-context", 1.0, {"semantic_memory": 0.8}
        )


if __name__ == "__main__":
    unittest.main()
