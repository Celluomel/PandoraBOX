import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

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
        )

        record = model._records[0]
        self.assertEqual(record.outcome, "unrated")
        self.assertEqual(record.outcome_source, "unattributed")

    def test_validated_action_probe_keeps_its_observed_outcome(self):
        model = self._model()

        model.record_observed_transition(
            "memory_recall", [0.5] * 5, [0.5, 0.8, 0.6, 0.5, 0.5],
            outcome="positive", outcome_source="validated_action_probe",
        )

        record = model._records[0]
        self.assertEqual(record.outcome, "positive")
        self.assertEqual(record.outcome_source, "validated_action_probe")

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
