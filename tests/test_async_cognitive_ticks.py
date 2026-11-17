"""Evidence and single-flight behavior for asynchronous cognitive ticks."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from cognition.introspective_observer import IntrospectiveObserver
from cognition.counterfactual_simulator import CounterfactualSimulator
from cognition.cognitive_audit_engine import AuditState, CognitiveAuditEngine, DevelopmentProposal
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
from cognition.meta_learning_audit import META_EVERY_N, MetaLearningAudit
from cognition.narrative_compression import COMPRESS_EVERY_N, NarrativeCompression
from cognition.cognitive_immune_system import IMMUNE_EVERY_N, CognitiveImmuneSystem
from cognition.flux_mind_model import UPDATE_EVERY_N, FluxMindModel
from cognition.contradiction_belief_reviser import REVISION_EVERY_N, ContradictionBeliefReviser
from cognition.autonomous_reflection import EVOLUTION_EVERY_N, AutonomousReflectionEngine
from cognition.autonomous_experimentation import EVALUATE_EVERY_N, AutonomousExperimentationEngine
from cognition.proactive_outreach import ProactiveOutreachEngine


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

    def test_cognitive_audit_worker_records_origin_cycle_and_effect_deltas(self):
        engine = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        engine._lock = threading.Lock()
        engine._state = AuditState()
        engine._state.proposal_attempt_total = 2
        engine._audit_in_progress = True
        receipts = []
        engine._organism = SimpleNamespace(
            _loop=SimpleNamespace(
                record_async_cycle_stage=lambda *args, **kwargs: receipts.append((args, kwargs))
            )
        )

        def run_audit(cycle):
            engine._state.snapshot_log.append({"slow_cycle": cycle})
            engine._state.last_audit_cycle = cycle
            engine._state.proposal_attempt_total += 1
            engine._state.last_proposal_attempt = {"status": "no_causally_mapped_parameter"}

        engine._run_audit = run_audit
        engine._run_audit_scheduled(42)

        self.assertFalse(engine._audit_in_progress)
        self.assertEqual(len(receipts), 1)
        args, kwargs = receipts[0]
        self.assertEqual(args, (42, "cognitive_audit_worker", "completed"))
        self.assertEqual(kwargs["metrics"]["snapshot_delta"], 1)
        self.assertEqual(kwargs["metrics"]["proposal_attempt_delta"], 1)
        self.assertEqual(kwargs["metrics"]["proposal_status"], "no_causally_mapped_parameter")

    def test_cognitive_audit_trial_worker_records_outcome_and_commit_effect(self):
        engine = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        engine._lock = threading.Lock()
        engine._state = AuditState()
        engine._state.committed_params = {}
        engine._trial_evaluation_in_progress = True
        receipts = []
        engine._organism = SimpleNamespace(
            _loop=SimpleNamespace(
                record_async_cycle_stage=lambda *args, **kwargs: receipts.append((args, kwargs))
            )
        )
        trial = DevelopmentProposal(
            dimension="epistemic_grounding_rate",
            signal_at_proposal=0.4,
            signal_target=0.7,
            parameter="probe",
            prior_value=1,
            proposed_value=2,
            rationale="test",
            proposed_at_cycle=20,
        )

        def evaluate(current_trial, cycle):
            current_trial.outcome = "confirmed"
            current_trial.committed = True
            engine._state.trial_log.append({
                "outcome": current_trial.outcome,
                "committed": current_trial.committed,
                "signal_sample_count_at_eval": 2,
            })
            engine._state.committed_params["probe"] = 2
            return True

        engine._evaluate_trial = evaluate
        engine._evaluate_trial_once(trial, 42)

        self.assertFalse(engine._trial_evaluation_in_progress)
        args, kwargs = receipts[0]
        self.assertEqual(args, (42, "cognitive_audit_worker", "completed"))
        self.assertEqual(kwargs["metrics"]["outcome"], "confirmed")
        self.assertTrue(kwargs["metrics"]["committed_parameter_changed"])

    def test_proactive_outreach_runs_single_flight_and_reports_pending_delivery(self):
        engine = ProactiveOutreachEngine.__new__(ProactiveOutreachEngine)
        engine._tick_lock = threading.Lock()
        engine._tick_pending = False
        engine._lock = threading.RLock()
        engine._state = SimpleNamespace(
            outreach_log=[], total_sent=0, last_outreach_by_user={}
        )
        receipts = []
        engine._o = SimpleNamespace(
            _loop=SimpleNamespace(
                record_async_cycle_stage=lambda *args, **kwargs: receipts.append((args, kwargs))
            )
        )
        engine._evaluate = lambda cycle: engine._state.outreach_log.append({
            "event_id": "event-1", "source_slow_cycle": cycle,
            "user_id": "fred", "delivery_status": "pending", "message_text": "private"
        })
        engine._save = lambda: None

        with patch("cognition.proactive_outreach.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(19)
            scheduled = engine.tick(20)
            duplicate = engine.tick(40)

        self.assertEqual(off_cycle["reason_code"], "outreach_cadence_not_due")
        self.assertEqual(scheduled["outcome_status"], "scheduled")
        self.assertEqual(duplicate["reason_code"], "outreach_evaluation_running")
        worker = _DeferredThread.workers[-1]
        worker.target(*worker.args)
        self.assertFalse(engine._tick_pending)
        args, kwargs = receipts[0]
        self.assertEqual(args, (20, "proactive_outreach_evaluation", "outreach_pending"))
        self.assertEqual(kwargs["metrics"]["new_event_count"], 1)
        self.assertEqual(kwargs["metrics"]["delivery_statuses"], ["pending"])
        self.assertNotIn("private", str(kwargs))

        engine._complete_delivery("event-1", True)
        delivery_args, delivery_kwargs = receipts[1]
        self.assertEqual(delivery_args, (20, "proactive_outreach_evaluation", "delivery_accepted"))
        self.assertTrue(delivery_kwargs["metrics"]["provider_accepted"])

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
        async_receipts = []
        resolver._organism = SimpleNamespace(
            _loop=SimpleNamespace(
                record_async_cycle_stage=lambda *args, **kwargs: async_receipts.append((args, kwargs))
            )
        )
        resolver._check_and_promote = lambda cycle: {
            "status": "completed", "reason_code": "no_candidates",
            "candidate_count": 0, "promoted_count": 0,
        }
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
        self.assertEqual(resolver.get_last_result()["cycle"], due)
        self.assertEqual(resolver.get_last_result()["status"], "completed")
        self.assertEqual(async_receipts[0][0], (
            due, "autonomous_curiosity_resolver.promotion", "completed",
        ))
        self.assertEqual(async_receipts[0][1]["metrics"]["candidate_count"], 0)

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

    def test_meta_learning_audit_tick_is_single_flight_and_receipted(self):
        engine = MetaLearningAudit.__new__(MetaLearningAudit)
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._records = []
        engine._pending = []
        engine._run = lambda cycle: True
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))

        with patch("cognition.meta_learning_audit.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(META_EVERY_N)
            second = engine.tick(META_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "meta_audit_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "meta_audit_already_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)
        self.assertEqual(completions[0][0][:3], (META_EVERY_N, "meta_learning_audit.worker", "completed"))

    def test_narrative_compression_tick_is_single_flight_and_receipted(self):
        engine = NarrativeCompression.__new__(NarrativeCompression)
        engine._lock = threading.Lock()
        engine._worker_pending = False
        engine._themes = []
        engine._last_attempt_cycle = None
        engine._last_error = ""
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))

        with patch("cognition.narrative_compression.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(COMPRESS_EVERY_N)
            second = engine.tick(COMPRESS_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "compression_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "compression_already_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)
        self.assertEqual(completions[0][0][:3], (COMPRESS_EVERY_N, "narrative_compression.worker", "skipped"))

    def test_narrative_compression_never_prunes_when_arc_persistence_fails(self):
        engine = NarrativeCompression.__new__(NarrativeCompression)
        engine._lock = threading.Lock()
        engine._themes = []
        engine._last_attempt_cycle = None
        engine._last_error = ""
        chapters = [SimpleNamespace(significance=0.2, title=f"chapter {i}", description="identity") for i in range(10)]
        identity = SimpleNamespace(life_story=chapters, _current_arc="")
        identity._save = lambda: False
        engine._organism = SimpleNamespace(narrative_identity=identity)
        engine._cluster = lambda _: [[0, 1]]
        engine._synthesise_theme = lambda _: "A coherent identity theme."
        engine._save = lambda: True

        outcome = engine._run(COMPRESS_EVERY_N)

        self.assertEqual(outcome["reason_code"], "identity_arc_persistence_failed")
        self.assertEqual(outcome["outcome_status"], "failed")
        self.assertEqual(len(identity.life_story), len(chapters))
        self.assertEqual(identity._current_arc, "")

    def test_cognitive_immune_check_tick_is_single_flight_and_receipted(self):
        immune = CognitiveImmuneSystem.__new__(CognitiveImmuneSystem)
        immune._lock = threading.Lock()
        immune._check_pending = False
        immune._transition_pending = False
        immune._state = SimpleNamespace(counterfactual_active=False, active_event=None)
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        immune._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        immune._run_check = lambda cycle: {
            "outcome_status": "completed", "reason_code": "immune_snapshot_recorded", "cycle": cycle,
        }

        with patch("cognition.cognitive_immune_system.threading.Thread", _DeferredThread):
            off_cycle = immune.tick(1)
            first = immune.tick(IMMUNE_EVERY_N)
            second = immune.tick(IMMUNE_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "immune_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "immune_check_already_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(immune._check_pending)
        self.assertEqual(completions[0][0][:3], (IMMUNE_EVERY_N, "cognitive_immune.check", "completed"))

    def test_cognitive_immune_counterfactual_transition_is_single_flight(self):
        immune = CognitiveImmuneSystem.__new__(CognitiveImmuneSystem)
        immune._lock = threading.Lock()
        immune._transition_pending = False
        immune._state = SimpleNamespace(counterfactual_active=False)
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        immune._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))

        def enter():
            immune._state.counterfactual_active = True
            return {"outcome_status": "completed", "reason_code": "counterfactual_mode_activated", "topic_count": 2}

        with patch("cognition.cognitive_immune_system.threading.Thread", _DeferredThread):
            first = immune._schedule_transition("enter", enter, (), 50)
            second = immune._schedule_transition("enter", enter, (), 60)

        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "counterfactual_transition_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(immune._transition_pending)
        self.assertEqual(completions[0][0][:3], (50, "cognitive_immune.counterfactual_enter", "completed"))
        self.assertEqual(completions[0][1]["output"]["topic_count"], 2)

    def test_flux_mind_model_tick_is_single_flight_and_receipted(self):
        model = FluxMindModel.__new__(FluxMindModel)
        model._lock = threading.Lock()
        model._worker_pending = False
        model._last_update_cycle = None
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        model._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        model._update = lambda: {
            "outcome_status": "completed", "reason_code": "profile_updated", "exchange_count": 3,
        }

        with patch("cognition.flux_mind_model.threading.Thread", _DeferredThread):
            off_cycle = model.tick(1)
            first = model.tick(UPDATE_EVERY_N)
            second = model.tick(UPDATE_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "flux_model_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "flux_model_update_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(model._worker_pending)
        self.assertEqual(completions[0][0][:3], (UPDATE_EVERY_N, "flux_mind_model.worker", "completed"))

    def test_contradiction_reviser_tick_is_single_flight_and_receipted(self):
        reviser = ContradictionBeliefReviser.__new__(ContradictionBeliefReviser)
        reviser._lock = threading.Lock()
        reviser._worker_pending = False
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        reviser._organism = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        reviser._run_revision = lambda cycle: {
            "outcome_status": "completed", "reason_code": "confrontations_revised", "confronted_count": 1,
        }

        with patch("cognition.contradiction_belief_reviser.threading.Thread", _DeferredThread):
            off_cycle = reviser.tick(1)
            first = reviser.tick(REVISION_EVERY_N)
            second = reviser.tick(REVISION_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "revision_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "revision_already_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(reviser._worker_pending)
        self.assertEqual(completions[0][0][:3], (REVISION_EVERY_N, "contradiction_belief_reviser.worker", "completed"))

    def test_autonomous_reflection_dispatch_is_single_flight_and_nonblocking(self):
        engine = AutonomousReflectionEngine.__new__(AutonomousReflectionEngine)
        engine._lock = threading.RLock()
        engine._worker_pending = False
        engine._last_worker_cycle = None
        engine._force_evolution_synthesis = False
        engine._state = SimpleNamespace(total_reflections=0, reflection_log=[])
        engine._o = SimpleNamespace()
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._o._loop = SimpleNamespace(record_async_cycle_stage=recorder)
        engine._run_evolution_synthesis = lambda cycle: None

        with patch("cognition.autonomous_reflection.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(EVOLUTION_EVERY_N)
            second = engine.tick(EVOLUTION_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "reflection_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "reflection_already_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._worker_pending)
        self.assertEqual(completions[0][0][:3], (EVOLUTION_EVERY_N, "autonomous_reflection.worker", "skipped"))

    def test_autonomous_experimentation_dispatch_is_single_flight_and_nonblocking(self):
        engine = AutonomousExperimentationEngine.__new__(AutonomousExperimentationEngine)
        engine._lock = threading.RLock()
        engine._tick_worker_pending = False
        engine._state = SimpleNamespace(total_experiments=0, experiment_log=[], active_experiment=None)
        completions = []
        recorder = lambda *args, **kwargs: completions.append((args, kwargs))
        engine._o = SimpleNamespace(_loop=SimpleNamespace(record_async_cycle_stage=recorder))
        engine._run_tick_work = lambda cycle: {
            "outcome_status": "skipped", "reason_code": "no_experiment_effect",
            "evaluation_recorded": False, "experiment_created": False,
        }

        with patch("cognition.autonomous_experimentation.threading.Thread", _DeferredThread):
            off_cycle = engine.tick(1)
            first = engine.tick(EVALUATE_EVERY_N)
            second = engine.tick(EVALUATE_EVERY_N * 2)

        self.assertEqual(off_cycle["reason_code"], "experiment_cadence_not_due")
        self.assertEqual(first["outcome_status"], "scheduled")
        self.assertEqual(second["reason_code"], "experiment_worker_running")
        _DeferredThread.workers[0].target(*_DeferredThread.workers[0].args)
        self.assertFalse(engine._tick_worker_pending)
        self.assertEqual(completions[0][0][:3], (EVALUATE_EVERY_N, "autonomous_experimentation.worker", "skipped"))


if __name__ == "__main__":
    unittest.main()
