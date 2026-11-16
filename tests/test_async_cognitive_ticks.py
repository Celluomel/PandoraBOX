"""Evidence and single-flight behavior for asynchronous cognitive ticks."""
import threading
import unittest
from unittest.mock import patch

from cognition.introspective_observer import IntrospectiveObserver
from cognition.counterfactual_simulator import CounterfactualSimulator


class _DeferredThread:
    workers = []

    def __init__(self, target, args=(), **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.workers.append(self)

    def start(self):
        return None


class AsyncCognitiveTickTests(unittest.TestCase):
    def setUp(self):
        _DeferredThread.workers = []

    @staticmethod
    def _observer():
        observer = IntrospectiveObserver.__new__(IntrospectiveObserver)
        observer._schedule_lock = threading.Lock()
        observer._run_pending = False
        observer._last_run_cycle = -10
        observer._run = lambda cycle: None
        return observer

    @staticmethod
    def _counterfactual():
        simulator = CounterfactualSimulator.__new__(CounterfactualSimulator)
        simulator._schedule_lock = threading.Lock()
        simulator._run_pending = False
        simulator._last_run_cycle = -5
        simulator._run = lambda cycle: None
        return simulator

    def test_observer_tick_reports_cadence_and_prevents_duplicate_workers(self):
        observer = self._observer()
        with patch("cognition.introspective_observer.threading.Thread", _DeferredThread):
            off_cycle = observer.tick(21)
            first = observer.tick(20)
            second = observer.tick(25)

        self.assertEqual(off_cycle["reason_code"], "not_consolidation_cycle")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "analysis_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        worker = _DeferredThread.workers[0]
        worker.target(*worker.args)
        self.assertFalse(observer._run_pending)

    def test_counterfactual_tick_reports_interval_and_prevents_duplicate_workers(self):
        simulator = self._counterfactual()
        with patch("cognition.counterfactual_simulator.threading.Thread", _DeferredThread):
            off_cycle = simulator.tick(6)
            first = simulator.tick(5)
            second = simulator.tick(10)

        self.assertEqual(off_cycle["reason_code"], "not_consolidation_cycle")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "analysis_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        worker = _DeferredThread.workers[0]
        worker.target(*worker.args)
        self.assertFalse(simulator._run_pending)


if __name__ == "__main__":
    unittest.main()
