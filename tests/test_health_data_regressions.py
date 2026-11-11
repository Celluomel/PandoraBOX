"""Health data regressions, without starting PandoraBOX or calling an LLM."""
import ast
import json
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
package = ModuleType('cognition')
package.__path__ = [str(ROOT / 'cognition')]
with patch.dict(sys.modules, {'cognition': package}):
    from cognition.cognitive_audit_engine import (
        AuditState, CognitiveAuditEngine, SignalSnapshot,
    )
    from cognition.narrative_compression import NarrativeCompression
    from cognition.temporal_projection import TemporalProjection, PathProjection


class HealthDataTests(unittest.TestCase):
    def test_cognitive_audit_breaks_underperformance_streak_on_missing_signal(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState(consecutive_under={
            'mean_skill_depth': 8,
            'question_resolution_rate': 13,
            'experiment_confirmation_rate': 9,
        })
        audit._lock = __import__('threading').Lock()

        audit._update_consecutive_underperformance(SignalSnapshot(
            slow_cycle=200,
            timestamp=1000.0,
            mean_skill_depth=0.3,
            question_resolution_rate=None,
            experiment_confirmation_rate=None,
        ))

        self.assertEqual(audit._state.consecutive_under['mean_skill_depth'], 9)
        self.assertEqual(audit._state.consecutive_under['question_resolution_rate'], 0)
        self.assertEqual(audit._state.consecutive_under['experiment_confirmation_rate'], 0)

    def test_cognitive_audit_waits_briefly_for_llm_slot_and_exposes_skip_reason(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._ai = NS(llm=NS(get_response=Mock(return_value="")))
        scheduler = ModuleType('core.llm_scheduler')
        scheduler_instance = NS(sync_slot=Mock(return_value=nullcontext(False)))
        scheduler.llm_scheduler = scheduler_instance

        with patch.dict(sys.modules, {'core.llm_scheduler': scheduler}):
            self.assertIsNone(audit._llm_call('bounded proposal prompt'))

        scheduler_instance.sync_slot.assert_called_once_with(
            priority=3, skip_if_busy=True, caller='cognitive_audit', wait_seconds=5.0,
        )
        self.assertEqual(audit._proposal_attempt_status, 'llm_slot_busy')

        audit._ai = NS(llm=NS(
            get_response=Mock(side_effect=RuntimeError('provider failure'))
        ))
        scheduler_instance.sync_slot.return_value = nullcontext(True)
        with patch.dict(sys.modules, {'core.llm_scheduler': scheduler}):
            self.assertIsNone(audit._llm_call('bounded proposal prompt'))
        self.assertEqual(audit._proposal_attempt_status, 'llm_error')

    def test_cognitive_audit_uses_low_level_adapter_with_mapped_parameter(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState()
        audit._organism = NS(_loop=None)
        response = json.dumps({
            'parameter': 'grounding_boost',
            'proposed_value': 0.039,
            'rationale': 'A modest change affects belief confidence directly. '
                         'The trial will be evaluated against the same signal.',
        })
        adapter = NS(get_response=Mock(return_value=response))
        facade_call = Mock(
            side_effect=AssertionError('chat facade must not handle internal proposal')
        )
        audit._ai = NS(llm=adapter, get_response=facade_call)

        scheduler = ModuleType('core.llm_scheduler')
        scheduler.llm_scheduler = NS(sync_slot=Mock(return_value=nullcontext(True)))
        with patch.dict(sys.modules, {'core.llm_scheduler': scheduler}):
            proposal = audit._generate_proposal(
                'belief_confidence_mean', 0.3, 0.5, 120,
            )

        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.parameter, 'grounding_boost')
        self.assertEqual(proposal.prior_value, 0.03)
        self.assertEqual(proposal.proposed_value, 0.039)
        adapter.get_response.assert_called_once()
        call = adapter.get_response.call_args.kwargs
        self.assertEqual(call['max_tokens'], 200)
        self.assertEqual(call['temperature'], 0.50)
        self.assertEqual(call['messages'][0]['role'], 'user')
        self.assertIn(
            'belief_confidence_mean',
            call['messages'][0]['content'],
        )
        self.assertIn('grounding_boost', call['messages'][0]['content'])
        self.assertNotIn('generate_every_n', call['messages'][0]['content'])
        facade_call.assert_not_called()
        self.assertEqual(audit._proposal_attempt_status, 'proposal_created')

    def test_cognitive_audit_refuses_unmapped_signal_without_calling_llm(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        adapter = NS(get_response=Mock())
        audit._ai = NS(llm=adapter)

        proposal = audit._generate_proposal('mean_skill_depth', 0.3, 1.0, 160)

        self.assertIsNone(proposal)
        adapter.get_response.assert_not_called()
        self.assertEqual(
            audit._proposal_attempt_status, 'no_causally_mapped_parameter',
        )

    def test_cognitive_audit_rejects_llm_parameter_outside_signal_mapping(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState()
        audit._organism = NS(_loop=None)
        response = json.dumps({
            'parameter': 'generate_every_n',
            'proposed_value': 20,
            'rationale': 'This parameter changes experiment frequency.',
        })
        adapter = NS(get_response=Mock(return_value=response))
        audit._ai = NS(llm=adapter)
        scheduler = ModuleType('core.llm_scheduler')
        scheduler.llm_scheduler = NS(sync_slot=Mock(return_value=nullcontext(True)))

        with patch.dict(sys.modules, {'core.llm_scheduler': scheduler}):
            proposal = audit._generate_proposal(
                'belief_confidence_mean', 0.3, 0.5, 160,
            )

        self.assertIsNone(proposal)
        self.assertEqual(
            audit._proposal_attempt_status, 'parameter_signal_mismatch',
        )

    def test_cognitive_audit_does_not_tune_unmapped_worst_signal(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState()
        audit._lock = __import__('threading').Lock()
        audit._proposal_attempt_status = 'not_started'
        audit._proposal_attempt_detail = ''
        snapshot = SignalSnapshot(
            slow_cycle=200, timestamp=1000.0, mean_skill_depth=0.3,
            belief_confidence_mean=0.8, epistemic_grounding_rate=0.9,
        )
        audit._read_signals = lambda _cycle: snapshot
        with tempfile.TemporaryDirectory() as folder:
            audit._path = Path(folder) / 'cognitive_params.json'
            audit._run_audit(200)

        self.assertIsNone(audit._state.active_trial)
        self.assertEqual(audit._state.proposal_attempt_total, 1)
        self.assertEqual(
            audit._state.last_proposal_attempt['status'],
            'no_causally_mapped_parameter',
        )
        self.assertEqual(
            audit._state.last_proposal_attempt['dimension'], 'mean_skill_depth',
        )

    def test_cognitive_audit_counts_active_trial_and_rolls_back_legacy_mismatch(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState(active_trial={
            'dimension': 'mean_skill_depth', 'signal_at_proposal': 0.3,
            'signal_target': 1.0, 'parameter': 'grounding_boost',
            'prior_value': 0.03, 'proposed_value': 0.039,
            'rationale': 'legacy mismatched trial', 'proposed_at_cycle': 9640,
            'proposed_at_time': 1000.0, 'outcome': 'pending',
            'signal_at_eval': None, 'evaluated_at_cycle': 0,
            'committed': False,
        }, consecutive_under={'mean_skill_depth': 3})
        audit._lock = __import__('threading').Lock()
        self.assertEqual(audit.status_summary()['total_trials'], 1)
        with tempfile.TemporaryDirectory() as folder:
            audit._path = Path(folder) / 'cognitive_params.json'
            with patch.object(CognitiveAuditEngine, '_set_module_global') as set_global:
                audit._recover_incompatible_active_trial()

        set_global.assert_called_once_with('grounding_boost', 0.03)
        self.assertIsNone(audit._state.active_trial)
        self.assertEqual(
            audit._state.trial_log[-1]['outcome'], 'rejected_causal_mismatch',
        )
        self.assertEqual(audit._state.consecutive_under['mean_skill_depth'], 0)
        self.assertEqual(
            audit._state.last_proposal_attempt['status'],
            'trial_reverted_causal_mismatch',
        )

    def test_cognitive_audit_persists_proposal_attempt_separately_from_trial(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._state = AuditState()
        audit._lock = __import__('threading').Lock()
        with tempfile.TemporaryDirectory() as folder:
            audit._path = Path(folder) / 'cognitive_params.json'
            audit._record_proposal_attempt(
                120, 'mean_skill_depth', 'invalid_response', 'bad JSON',
            )
            persisted = json.loads(audit._path.read_text(encoding='utf-8'))

        self.assertEqual(audit.status_summary()['total_trials'], 0)
        self.assertEqual(audit.status_summary()['proposal_attempt_count'], 1)
        self.assertEqual(persisted['proposal_attempt_total'], 1)
        self.assertEqual(
            persisted['last_proposal_attempt']['status'], 'invalid_response',
        )
        self.assertEqual(persisted['trial_log'], [])

    def test_audit_reads_current_storage_contracts(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._organism = NS(skill_registry=NS(_state=NS(
            skills={'a': {'depth': 1}, 'b': {'depth': 3}})))
        audit._ai = NS(self_concept=NS(_beliefs={
            'a': NS(confidence=0.6), 'b': NS(confidence=0.8)}))
        snapshot = audit._read_signals(42)
        self.assertEqual(snapshot.mean_skill_depth, 2)
        self.assertAlmostEqual(snapshot.belief_confidence_mean, 0.7)

    def test_audit_marks_empty_denominators_unmeasured(self):
        audit = CognitiveAuditEngine.__new__(CognitiveAuditEngine)
        audit._organism = NS(
            _loop=NS(
                _autonomous_reflection=NS(
                    _epistemic=NS(_recent_grounding_rate=lambda: 0.8)),
                _auto_experiment=NS(_state=NS(
                    total_experiments=0, total_confirmed=0)),
                _resolution_engine=NS(_state=NS(
                    total_resolved=0, total_unresolvable=0)),
            ),
            skill_registry=NS(_state=NS(skills={})),
        )
        audit._ai = NS(self_concept=NS(_beliefs={}))
        snapshot = audit._read_signals(42)

        self.assertIsNone(snapshot.experiment_confirmation_rate)
        self.assertIsNone(snapshot.question_resolution_rate)
        self.assertIsNone(snapshot.mean_skill_depth)
        self.assertIsNone(snapshot.belief_confidence_mean)
        self.assertEqual(snapshot.deficit(), {
            'epistemic_grounding_rate': 0.8 - 0.6,
        })
        self.assertIsNone(snapshot.worst_signal())

    def test_projection_restores_nested_paths_and_skips_bad_entry(self):
        path = dict(archetype='intensive', cumulative_cost=0.2,
                    progress_rate=0.1, efficiency=0.5, crosses_critical=False,
                    min_energy_predicted=0.8, action_sequence=['technical'])
        result = dict(aspiration_domain='cognitive', aspiration_desc='test',
                      projected_at_cycle=10, timestamp=100, paths=[path],
                      preferred_path='intensive', preferred_action='technical',
                      rationale='test')
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'projections.json'
            file.write_text(json.dumps({'active': {'bad': {}, 'cognitive': result},
                                        'log': [result]}))
            engine = TemporalProjection(None, None, str(file))
            self.assertEqual(engine.status()['active_projections'], 1)
            self.assertEqual(len(engine._log), 1)
            self.assertIsInstance(engine._active['cognitive'].paths[0], PathProjection)

    def test_narrative_uses_low_level_llm_not_chat_pipeline(self):
        engine = NarrativeCompression.__new__(NarrativeCompression)
        engine._ai = NS(llm=NS(get_response=Mock(return_value='I learn.')),
                        get_response=Mock(side_effect=AssertionError('chat called')))
        scheduler = ModuleType('core.llm_scheduler')
        scheduler.llm_scheduler = NS(sync_slot=Mock(return_value=nullcontext(True)))
        with patch.dict(sys.modules, {'core.llm_scheduler': scheduler}):
            self.assertEqual(engine._synthesise_theme([NS(title='t', description='d')]),
                             'I learn.')
        engine._ai.llm.get_response.assert_called_once()
        engine._ai.get_response.assert_not_called()

    def test_streaming_deliberation_precedes_prompt_build(self):
        tree = ast.parse((ROOT / 'cognition/persona_bridge.py').read_text(encoding='utf-8'))
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == '_build_prompt_and_cache')
        calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
        deliberate = next(n for n in calls if isinstance(n.func, ast.Name)
                          and n.func.id == 'deliberate')
        build = next(n for n in calls if isinstance(n.func, ast.Attribute)
                     and n.func.attr == '_build_prompt_additions')
        self.assertLess(deliberate.lineno, build.lineno)

    def test_live_cognitive_telemetry_precedes_narrative_prompt_sections(self):
        source = (ROOT / 'cognition/persona_bridge.py').read_text(encoding='utf-8')
        prompt_start = source.index('system_prompt = f"""')
        prompt_end = source.index('"""', prompt_start + len('system_prompt = f"""'))
        prompt_template = source[prompt_start:prompt_end]

        self.assertLess(
            prompt_template.index('{_organism_prompt_section}'),
            prompt_template.index('━━ CURRENT FUNCTIONAL STATE ━━'),
        )
        self.assertNotIn('━━ COGNITIVE STATE ━━', source[prompt_end:])

    def test_self_report_can_initialise_planner_without_background_cycle(self):
        source = (ROOT / 'cognition/cognitive_organism.py').read_text(encoding='utf-8')
        self.assertIn('LongHorizonPlanner.is_self_report_query(user_input)', source)
        self.assertIn('loop._long_horizon_planner = lhp', source)
        self.assertIn('factual planning telemetry unavailable', source)

    def test_factual_self_report_contract_is_adjacent_to_generation(self):
        source = (ROOT / 'cognition/persona_bridge.py').read_text(encoding='utf-8')
        self.assertIn('FINAL FACTUAL SELF-REPORT CONTRACT', source)
        self.assertIn(
            'Do not claim that composing or explaining this answer starts or completes',
            source,
        )
        self.assertIn('_generation_input, system_prompt,', source)
        self.assertIn('arb_temperature = min(', source)


if __name__ == '__main__':
    unittest.main()
