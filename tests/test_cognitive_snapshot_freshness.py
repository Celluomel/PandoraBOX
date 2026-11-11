import threading
import time
import unittest

from cognition.cognitive_audit_engine import AuditState, CognitiveAuditEngine
from cognition.cognitive_immune_system import CognitiveImmuneSystem, ImmuneState


class CognitiveSnapshotFreshnessTests(unittest.TestCase):
    def _engine_with_snapshot(self, engine_type, state, timestamp):
        engine = engine_type.__new__(engine_type)
        engine._state = state
        engine._lock = threading.Lock()
        engine._process_started_at = time.time() - 5
        state.snapshot_log.append({"timestamp": timestamp})
        return engine

    def test_persisted_snapshots_are_not_mislabeled_as_current_process_data(self):
        old_timestamp = time.time() - 60
        cases = (
            (CognitiveAuditEngine, AuditState(), "last_snapshot_process_scope"),
            (CognitiveImmuneSystem, ImmuneState(), "last_snapshot_process_scope"),
        )

        for engine_type, state, scope_key in cases:
            with self.subTest(engine=engine_type.__name__):
                engine = self._engine_with_snapshot(engine_type, state, old_timestamp)
                status = engine.status_summary()

                self.assertEqual(status[scope_key], "persisted_or_unknown")
                self.assertGreaterEqual(status["last_snapshot_age_seconds"], 59)

    def test_snapshot_created_after_process_start_is_marked_current(self):
        timestamp = time.time()
        cases = (
            (CognitiveAuditEngine, AuditState()),
            (CognitiveImmuneSystem, ImmuneState()),
        )

        for engine_type, state in cases:
            with self.subTest(engine=engine_type.__name__):
                engine = self._engine_with_snapshot(engine_type, state, timestamp)
                status = engine.status_summary()

                self.assertEqual(status["last_snapshot_process_scope"], "current_process")
                self.assertLess(status["last_snapshot_age_seconds"], 2)


if __name__ == "__main__":
    unittest.main()
