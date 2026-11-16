"""Evidence and single-flight behavior for asynchronous cognitive ticks."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cognition.introspective_observer import IntrospectiveObserver
from cognition.counterfactual_simulator import CounterfactualSimulator
from cognition.cognitive_audit_engine import AuditState, CognitiveAuditEngine
from cognition.causal_mechanism_model import CAUSAL_EVERY_N, CausalMechanismModel
from cognition.cross_layer_feedback import FEEDBACK_EVERY_N, CrossLayerFeedback
from cognition.autonomous_curiosity_resolver import (
    RESOLVE_CHECK_EVERY_N, AutonomousCuriosityResolver,
)
from cognition.generative_aspiration_engine import (
    GENERATIVE_EVERY_N, GenerativeAspirationEngine,
)
from cognition.aspirational_synthesis_engine import (
    SYNTHESIS_EVERY_N, AspirationalSynthesisEngine,
)
from cognition.temporal_projection import PROJECTION_EVERY_N, TemporalProjection
from cognition.temporal_self_projection import PROJECT_EVERY_N, TemporalSelfProjection
from cognition.structural_coupling import COUPLING_EVERY_N, StructuralCoupling


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

    def test_cognitive_audit_tick_reports_cadence_and_prevents_duplicate_workers(self):
        engine = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        engine._lock = threading.Lock()
        engine._state = AuditState()
        engine._trial_evaluation_in_progress = False
        engine._audit_in_progress = False
        engine._run_audit = lambda cycle: None

        with patch("cognition.cognitive_audit_engine.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(40)
            second = engine.tick(80)

        self.assertEqual(off_cycle["reason_code"], "audit_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "audit_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        worker = _DeferredThread.workers[0]
        worker.target(*worker.args)
        self.assertFalse(engine._audit_in_progress)

    def test_causal_mechanism_tick_is_single_flight_and_receipted(self):
        model = CausalMechanismModel.__new__(CausalMechanismModel)
        model._lock = threading.Lock()
        model._run_pending = False
        model._run = lambda: None
        due = CAUSAL_EVERY_N

        with patch("cognition.causal_mechanism_model.threading.Thread", _DeferredThread):
            off_cycle = model.tick(1)
            first = model.tick(due)
            second = model.tick(due * 2)

        self.assertEqual(off_cycle["reason_code"], "causal_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "analysis_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(model._run_pending)

    def test_cross_layer_feedback_tick_is_single_flight_and_receipted(self):
        feedback = CrossLayerFeedback.__new__(CrossLayerFeedback)
        feedback._lock = threading.Lock()
        feedback._run_pending = False
        feedback._run_all = lambda cycle: None
        due = FEEDBACK_EVERY_N

        with patch("cognition.cross_layer_feedback.threading.Thread", _DeferredThread):
            off_cycle = feedback.tick(1)
            first = feedback.tick(due)
            second = feedback.tick(due * 2)

        self.assertEqual(off_cycle["reason_code"], "feedback_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "feedback_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(feedback._run_pending)

    def test_curiosity_resolver_tick_is_single_flight_and_receipted(self):
        resolver = AutonomousCuriosityResolver.__new__(AutonomousCuriosityResolver)
        resolver._worker_lock = threading.Lock()
        resolver._worker_pending = False
        resolver._check_and_promote = lambda cycle: None
        due = RESOLVE_CHECK_EVERY_N

        with patch("cognition.autonomous_curiosity_resolver.threading.Thread", _DeferredThread):
            off_cycle = resolver.tick(1)
            first = resolver.tick(due)
            second = resolver.tick(due * 2)

        self.assertEqual(off_cycle["reason_code"], "curiosity_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "promotion_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(resolver._worker_pending)

    def test_generative_aspiration_tick_is_single_flight_and_receipted(self):
        engine = GenerativeAspirationEngine.__new__(GenerativeAspirationEngine)
        engine._organism = object()
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._run = lambda cycle: None
        due = GENERATIVE_EVERY_N

        with patch("cognition.generative_aspiration_engine.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(due)
            second = engine.tick(due * 2)

        self.assertEqual(off_cycle["reason_code"], "generation_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "generation_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)

    def test_aspirational_synthesis_tick_is_single_flight_and_receipted(self):
        engine = AspirationalSynthesisEngine.__new__(AspirationalSynthesisEngine)
        engine._organism = object()
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._run_synthesis = lambda cycle: None
        due = SYNTHESIS_EVERY_N

        with patch("cognition.aspirational_synthesis_engine.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(due)
            second = engine.tick(due * 2)

        self.assertEqual(off_cycle["reason_code"], "synthesis_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "synthesis_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)

    def test_temporal_projection_tick_is_single_flight_and_receipted(self):
        engine = TemporalProjection.__new__(TemporalProjection)
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._last_worker_cycle = None
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        engine._run_projections = lambda cycle: {
            "outcome_status": "completed", "reason_code": "projections_updated", "projection_count": 1,
        }

        with patch("cognition.temporal_projection.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(PROJECTION_EVERY_N)
            second = engine.tick(PROJECTION_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "projection_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "projection_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)
        self.assertEqual(completions[0][0][:3], (PROJECTION_EVERY_N, "temporal_projection.worker", "completed"))

    def test_temporal_self_projection_tick_is_single_flight_and_receipted(self):
        engine = TemporalSelfProjection.__new__(TemporalSelfProjection)
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._last_worker_cycle = None
        engine._record_snapshot = lambda cycle: None
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        engine._project = lambda cycle: {
            "outcome_status": "completed", "reason_code": "trajectory_updated", "dimension_count": 2,
        }

        with patch("cognition.temporal_self_projection.threading.Thread", _DeferredThread):
            first = engine.tick(PROJECT_EVERY_N)
            second = engine.tick(PROJECT_EVERY_N * 2)

        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "projection_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)
        self.assertEqual(completions[0][0][:3], (PROJECT_EVERY_N, "temporal_self_projection.worker", "completed"))

    def test_structural_coupling_tick_is_single_flight_and_receipted(self):
        coupling = StructuralCoupling.__new__(StructuralCoupling)
        coupling._lock = threading.Lock()
        coupling._worker_pending = False
        coupling._last_worker_cycle = None
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        coupling._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        coupling._push = lambda: {
            "outcome_status": "completed", "reason_code": "peer_updates_sent", "sent_count": 1,
        }

        with patch("cognition.structural_coupling.threading.Thread", _DeferredThread):
            off_cycle = coupling.tick(1)
            first = coupling.tick(COUPLING_EVERY_N)
            second = coupling.tick(COUPLING_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "coupling_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "coupling_already_running")
        self.assertEqual(len(_DeferredThread.workers), 1)
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(coupling._worker_pending)
        self.assertEqual(completions[0][0][:3], (COUPLING_EVERY_N, "structural_coupling.worker", "completed"))


if __name__ == "__main__":
    unittest.main()
