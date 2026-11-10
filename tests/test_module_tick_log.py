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

    def test_declared_side_effect_only_none_is_not_reported_as_empty_output(self):
        ticks = ModuleTickLog()
        ticks.register("side_effect", initialized=True)
        ticks.record("side_effect", "tick", started_at=1.0, duration_ms=1.0,
                     output=None, side_effect_only=True)

        state = ticks.snapshot()["side_effect"]
        self.assertEqual(state["last_output"]["quality"], "side_effect_only")
        self.assertEqual(ticks.analysis()["last_output_qualities"], {"side_effect_only": 1})

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

    def test_internal_loop_probe_uses_declared_none_return_contract(self):
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
        self.assertEqual(output["quality"], "side_effect_only")

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
        self.assertEqual(analysis["states"]["unavailable"], 42)


if __name__ == "__main__":
    unittest.main()
