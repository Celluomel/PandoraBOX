import unittest
from types import SimpleNamespace

from core.module_tick_log import ModuleTickLog, summarize_output
from core.internal_loop import InternalThoughtLoop


class ModuleTickLogTests(unittest.TestCase):
    def test_output_summary_redacts_text_and_checks_numeric_fields(self):
        summary = summarize_output({
            "answer": "private generated text",
            "distance_m": 1.25,
            "bad": float("nan"),
        })

        self.assertEqual(summary["quality"], "invalid_numeric")
        self.assertEqual(summary["numeric_fields"]["distance_m"], {"finite": True})
        self.assertEqual(summary["non_finite_fields"], ["bad"])
        self.assertNotIn("private generated text", repr(summary))

    def test_output_summary_retains_only_allowlisted_tick_receipt_facts(self):
        summary = summarize_output({
            "outcome_status": "completed",
            "reason_code": "cadence_deferred",
            "cycle": 23,
            "goal_plans_pending": 2,
            "aspiration_plan_exists": False,
            "query": "private user text",
            "custom_status": "arbitrary",
        })

        self.assertEqual(summary["receipt_fields"], {
            "outcome_status": "completed",
            "reason_code": "cadence_deferred",
            "cycle": 23,
            "goal_plans_pending": 2,
            "aspiration_plan_exists": False,
        })
        self.assertNotIn("private user text", repr(summary))
        self.assertNotIn("custom_status", summary["receipt_fields"])

    def test_output_summary_exposes_safe_goal_quality_aggregate_counts(self):
        summary = summarize_output({
            "scored": [{"id": "private-goal-1", "name": "private goal"}],
            "completion_write_failed": ["private-goal-2"],
            "summary": {
                "noise_marked": 2,
                "boosted": 1,
                "settled": 0,
                "completion_write_failed": 1,
                "goal_write_failed": 2,
                "goal_writes_succeeded": 7,
                "generated": 3,
                "high_quality": 4,
                "private_detail": "do not expose",
            },
        })

        self.assertEqual(summary["summary_counts"], {
            "noise_marked": 2,
            "boosted": 1,
            "settled": 0,
            "completion_write_failed": 1,
            "goal_write_failed": 2,
            "goal_writes_succeeded": 7,
            "generated": 3,
            "high_quality": 4,
        })
        self.assertNotIn("private-goal-1", repr(summary))
        self.assertNotIn("private-goal-2", repr(summary))
        self.assertNotIn("do not expose", repr(summary))

    def test_output_summary_retains_contradiction_effect_statuses_only(self):
        summary = summarize_output({
            "event_status": "handlers_called",
            "event_handler_count": 2,
            "affect_status": "applied",
            "tension_status": "returned",
            "curiosity_status": "failed_RuntimeError",
            "workspace_status": "returned",
            "private_topic": "do not retain",
        })

        self.assertEqual(summary["receipt_fields"], {
            "event_status": "handlers_called",
            "event_handler_count": 2,
            "affect_status": "applied",
            "tension_status": "returned",
            "curiosity_status": "failed_RuntimeError",
            "workspace_status": "returned",
        })
        self.assertNotIn("do not retain", repr(summary))

    def test_semantic_extraction_receipt_exposes_counts_without_prose(self):
        summary = summarize_output({
            "status": "completed",
            "turn_id": "semantic-turn-17",
            "concepts_parsed": 3,
            "concept_upsert_calls_returned": 3,
            "observation_calls_returned": 2,
            "relation_upsert_calls_returned": 1,
            "cag_status": "completed",
            "workspace_status": "not_requested",
            "user_input": "private user text",
        })

        self.assertEqual(summary["receipt_fields"]["status"], "completed")
        self.assertEqual(summary["receipt_fields"]["concepts_parsed"], 3)
        self.assertEqual(summary["receipt_fields"]["observation_calls_returned"], 2)
        self.assertEqual(summary["receipt_fields"]["cag_status"], "completed")
        self.assertNotIn("private user text", repr(summary))
        self.assertNotIn("turn_id", summary["receipt_fields"])

    def test_none_output_is_unverified_not_a_claimed_side_effect(self):
        ticks = ModuleTickLog()
        ticks.register("side_effect", initialized=True)
        ticks.record("side_effect", "tick", started_at=1.0, duration_ms=1.0, output=None)

        state = ticks.snapshot()["side_effect"]
        self.assertEqual(state["last_output"]["quality"], "no_return_unverified")
        self.assertEqual(state["state"], "output_unverified")
        self.assertEqual(ticks.analysis()["last_output_qualities"], {"no_return_unverified": 1})

    def test_module_keeps_per_method_outputs_when_auxiliary_method_returns_none(self):
        ticks = ModuleTickLog()
        ticks.register("cognitive_governor", initialized=True)
        ticks.record(
            "cognitive_governor", "begin_cycle", started_at=1.0,
            duration_ms=1.0, output={"mode": "structured", "budget_total": 4},
        )
        ticks.record(
            "cognitive_governor", "summary_log", started_at=2.0,
            duration_ms=1.0, output=None,
        )

        module = ticks.snapshot()["cognitive_governor"]
        self.assertEqual(module["last_output"]["quality"], "no_return_unverified")
        self.assertEqual(
            module["method_results"]["begin_cycle"]["last_output"]["quality"],
            "present",
        )
        self.assertEqual(
            module["method_results"]["begin_cycle"]["last_output"]["keys"],
            ["budget_total", "mode"],
        )
        self.assertEqual(
            module["method_results"]["summary_log"]["last_output"]["quality"],
            "no_return_unverified",
        )

    def test_per_method_failure_does_not_overwrite_other_method_receipt(self):
        ticks = ModuleTickLog()
        ticks.register("attention", initialized=True)
        ticks.record(
            "attention", "compute_and_write", started_at=1.0,
            duration_ms=1.0, output={"primary_focus": "memory"},
        )
        try:
            raise ValueError("private detail")
        except ValueError as exc:
            ticks.record(
                "attention", "decay_context", started_at=2.0,
                duration_ms=1.0, error=exc,
            )

        methods = ticks.snapshot()["attention"]["method_results"]
        self.assertEqual(methods["compute_and_write"]["last_status"], "completed")
        self.assertEqual(methods["compute_and_write"]["last_output"]["quality"], "present")
        self.assertEqual(methods["decay_context"]["last_status"], "failed")
        self.assertEqual(methods["decay_context"]["last_error_type"], "ValueError")
        self.assertNotIn("private detail", repr(methods))

    def test_attention_decay_effect_receipt_is_auditable_without_raw_state(self):
        ticks = ModuleTickLog()
        ticks.register("cognitive_attention_engine", initialized=True)
        ticks.record(
            "cognitive_attention_engine", "decay_context",
            started_at=1.0, duration_ms=1.0,
            output={
                "effect_status": "context_bias_decayed",
                "outcome_status": "completed",
                "contexts_before": 3,
                "contexts_after": 3,
                "signals_before": 5,
                "signals_after": 5,
                "signals_pruned": 0,
                "contexts_pruned": 0,
                "persisted": True,
            },
        )

        module = ticks.snapshot()["cognitive_attention_engine"]
        self.assertEqual(module["state"], "output_present_unvalidated")
        self.assertEqual(
            module["last_output"]["receipt_fields"],
            {
                "effect_status": "context_bias_decayed",
                "outcome_status": "completed",
                "contexts_before": 3,
                "contexts_after": 3,
                "signals_before": 5,
                "signals_after": 5,
                "signals_pruned": 0,
                "contexts_pruned": 0,
                "persisted": True,
            },
        )

    def test_empty_and_uninspectable_outputs_are_not_marked_healthy(self):
        ticks = ModuleTickLog()
        ticks.register("empty", initialized=True)
        ticks.record("empty", "run", started_at=1.0, duration_ms=1.0, output=None)
        self.assertEqual(ticks.snapshot()["empty"]["state"], "output_unverified")

        class OpaqueResult:
            pass

        ticks.register("opaque", initialized=True)
        ticks.record("opaque", "run", started_at=1.0, duration_ms=1.0,
                     output=OpaqueResult())
        self.assertEqual(ticks.snapshot()["opaque"]["state"], "output_unverified")

    def test_tick_log_tracks_execution_and_error_without_retaining_exception_text(self):
        ticks = ModuleTickLog()
        ticks.register("sample", initialized=True)
        ticks.record("sample", "run", started_at=1.0, duration_ms=2.5,
                     output={"items": [1, 2]})
        ticks.record("sample", "run", started_at=2.0, duration_ms=3.0,
                     error=RuntimeError("sensitive prompt fragment"))
        state = ticks.snapshot()["sample"]

        self.assertEqual(state["tick_count"], 2)
        self.assertEqual(state["error_count"], 1)
        self.assertEqual(state["state"], "error")
        self.assertEqual(state["last_error_type"], "RuntimeError")
        self.assertNotIn("sensitive prompt fragment", repr(state))

    def test_tick_log_retains_safe_failure_provenance_after_later_success(self):
        ticks = ModuleTickLog()
        ticks.register("sample", initialized=True)
        try:
            raise UnboundLocalError("private local value")
        except UnboundLocalError as exc:
            ticks.record("sample", "run", started_at=1.0, duration_ms=1.0, error=exc)
        ticks.record("sample", "run", started_at=2.0, duration_ms=1.0, output={"ok": True})

        state = ticks.snapshot()["sample"]
        self.assertEqual(state["last_status"], "completed")
        self.assertEqual(state["last_error_type"], "UnboundLocalError")
        self.assertEqual(state["last_error"]["method"], "run")
        self.assertEqual(state["last_error"]["location"]["function"],
                         "test_tick_log_retains_safe_failure_provenance_after_later_success")
        self.assertNotIn("private local value", repr(state))
        self.assertEqual(ticks.analysis()["modules_with_errors"], 1)

    def test_registration_distinguishes_unavailable_from_unobserved(self):
        ticks = ModuleTickLog()
        ticks.register("initialized", initialized=True)
        ticks.register("missing", initialized=False)
        state = ticks.snapshot()
        self.assertEqual(state["initialized"]["state"], "initialized_unobserved")
        self.assertEqual(state["missing"]["state"], "unavailable")
        analysis = ticks.analysis()
        self.assertEqual(analysis["module_count"], 2)
        self.assertEqual(analysis["executed_module_count"], 0)
        self.assertEqual(analysis["states"]["unavailable"], 1)

    def test_policy_skip_is_visible_but_never_counted_as_execution(self):
        ticks = ModuleTickLog()
        ticks.register("periodic", initialized=True, cadence="every 20 cycles")
        ticks.record_skip("periodic", "skipped_cadence", metrics={"cycle": 7})

        state = ticks.snapshot()["periodic"]
        analysis = ticks.analysis()
        self.assertEqual(state["state"], "skipped_by_policy")
        self.assertEqual(state["tick_count"], 0)
        self.assertEqual(state["skip_count"], 1)
        self.assertEqual(state["last_skip_status"], "skipped_cadence")
        self.assertEqual(state["last_skip_metrics"], {"cycle": 7})
        self.assertEqual(analysis["executed_module_count"], 0)
        self.assertEqual(analysis["total_ticks"], 0)
        self.assertEqual(analysis["total_skips"], 1)
        self.assertEqual(analysis["modules_with_skips"], 1)

    def test_execution_state_survives_a_later_policy_skip(self):
        ticks = ModuleTickLog()
        ticks.register("periodic", initialized=True)
        ticks.record("periodic", "run", started_at=1.0, duration_ms=1.0,
                     output={"ok": True})
        ticks.record_skip("periodic", "skipped_governor")

        state = ticks.snapshot()["periodic"]
        self.assertEqual(state["tick_count"], 1)
        self.assertEqual(state["skip_count"], 1)
        self.assertEqual(state["state"], "output_present_unvalidated")

    def test_internal_loop_probe_records_real_call_and_output_quality(self):
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._tte = SimpleNamespace(step=lambda: {"score": float("inf")})

        loop._refresh_module_tick_probes()
        output = loop._tte.step()
        tick = loop.module_tick_snapshot()["thought_thread_engine"]

        self.assertEqual(output["score"], float("inf"))
        self.assertEqual(tick["tick_count"], 1)
        self.assertEqual(tick["state"], "degraded")
        self.assertEqual(tick["last_output"]["quality"], "invalid_numeric")
        self.assertFalse(tick["last_output"]["numeric_fields"]["score"]["finite"])
        self.assertEqual(loop.module_tick_analysis()["executed_module_count"], 1)

    def test_internal_loop_probe_does_not_infer_side_effect_from_none_annotation(self):
        class SideEffectModule:
            def tick(self) -> None:
                self.did_run = True

        module = SideEffectModule()
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._resource_economy = module

        loop._refresh_module_tick_probes()
        module.tick()

        output = loop.module_tick_snapshot()["cognitive_resource_economy"]["last_output"]
        self.assertTrue(module.did_run)
        self.assertEqual(output["quality"], "no_return_unverified")
        self.assertEqual(loop.module_tick_snapshot()["cognitive_resource_economy"]["state"],
                         "output_unverified")

    def test_internal_loop_probe_uses_structured_no_action_receipt(self):
        class GoalActionModule:
            _last_tick_outcome = None

            def run_tick(self):
                self._last_tick_outcome = {
                    "outcome_status": "skipped",
                    "reason_code": "no_eligible_goals",
                }
                return None

        module = GoalActionModule()
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._goal_action_executor = module

        loop._refresh_module_tick_probes()
        result = module.run_tick()

        tick = loop.module_tick_snapshot()["goal_action_executor"]
        self.assertIsNone(result)
        self.assertEqual(tick["tick_count"], 1)
        self.assertEqual(tick["last_status"], "completed")
        self.assertEqual(tick["state"], "output_present_unvalidated")
        self.assertEqual(tick["last_output"]["quality"], "present")
        self.assertEqual(
            tick["last_output"]["receipt_fields"]["reason_code"],
            "no_eligible_goals",
        )

    def test_probe_targets_match_live_internal_loop_entrypoints(self):
        calls = []
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._goal_action_executor = SimpleNamespace(
            run_tick=lambda: calls.append("goal_action") or {"success": False},
        )
        loop._persistent_exec_loop = SimpleNamespace(
            review=lambda organism: calls.append("persistent_review") or {},
        )
        loop._arbitration_learning = SimpleNamespace(
            review=lambda goals, cycle: calls.append("arbitration_review") or {},
        )
        loop._governor = SimpleNamespace(
            begin_cycle=lambda **kwargs: calls.append("governor_cycle"),
        )

        loop._refresh_module_tick_probes()
        loop._goal_action_executor.run_tick()
        loop._persistent_exec_loop.review(None)
        loop._arbitration_learning.review(None, 1)
        loop._governor.begin_cycle()

        snapshot = loop.module_tick_snapshot()
        for module_name in (
            "goal_action_executor", "persistent_executive_loop",
            "arbitration_learning", "cognitive_governor",
        ):
            self.assertEqual(snapshot[module_name]["tick_count"], 1)
        self.assertEqual(len(calls), 4)

    def test_analysis_uses_live_initialization_after_lazy_creation(self):
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._tte = SimpleNamespace(step=lambda: [])
        loop._module_tick_log.register("thought_thread_engine", initialized=False)

        analysis = loop.module_tick_analysis()

        self.assertEqual(analysis["module_count"], 43)
        self.assertEqual(analysis["states"]["initialized_unobserved"], 1)
        self.assertEqual(analysis["states"]["not_initialized_conditional"], 42)

    def test_lazy_module_before_its_cadence_is_not_reported_unavailable(self):
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._goal_action_executor = None
        loop._refresh_module_tick_probes()

        snapshot = loop.module_tick_snapshot()
        analysis = loop.module_tick_analysis()

        self.assertFalse(snapshot["goal_action_executor"]["initialized"])
        self.assertEqual(snapshot["goal_action_executor"]["state"], "not_initialized_conditional")
        self.assertEqual(analysis["states"].get("unavailable", 0), 0)

    def test_probe_attaches_before_first_call_of_lazily_assigned_module(self):
        loop = InternalThoughtLoop.__new__(InternalThoughtLoop)
        loop._module_tick_log = ModuleTickLog()
        loop._module_tick_wrapped = set()
        loop._long_horizon_planner = None
        loop._refresh_module_tick_probes()

        calls = []
        loop._long_horizon_planner = SimpleNamespace(
            tick=lambda cycle: calls.append(cycle) or {"cycle": cycle},
        )
        result = loop._long_horizon_planner.tick(21)

        observed = loop.module_tick_snapshot()["long_horizon_planner"]
        self.assertEqual(result, {"cycle": 21})
        self.assertEqual(calls, [21])
        self.assertEqual(observed["tick_count"], 1)
        self.assertEqual(observed["last_output"]["quality"], "present")


if __name__ == "__main__":
    unittest.main()
