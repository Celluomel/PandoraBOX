from scripts.watch_cognitive_harness_audit import (
    compact_snapshot, compare_snapshots, select_new_cycles,
)


def _payload(cycle, module_ticks, method_ticks, errors=0):
    return {
        "available": True,
        "loop_running": True,
        "slow_cycle_count": cycle,
        "module_tick_analysis": {
            "module_count": 1, "executed_module_count": 1,
            "total_ticks": module_ticks, "total_errors": errors,
        },
        "modules": {
            "cognitive_governor": {
                "tick_count": module_ticks, "skip_count": 2,
                "error_count": errors, "state": "output_unverified",
                "last_output": {"quality": "no_return_unverified"},
                "observed_methods": ["begin_cycle", "summary_log"],
                "method_results": {
                    "begin_cycle": {
                        "tick_count": method_ticks, "error_count": 0,
                        "last_status": "completed", "last_output": {
                            "quality": "present", "keys": ["mode", "budget_total"],
                        },
                    },
                    "summary_log": {
                        "tick_count": module_ticks - method_ticks,
                        "error_count": errors, "last_status": "completed",
                        "last_output": {"quality": "no_return_unverified"},
                    },
                },
            },
        },
        "recent_cycle_evidence": {"retained": 1, "cycles": [{
            "cycle_id": cycle, "status": "completed", "stages": [{
                "stage": "module_tick:cognitive_governor.begin_cycle",
                "status": "completed", "output_ref": "abc",
                "output_summary": {"kind": "mapping", "field_count": 2},
            }],
        }]},
        "interpretation_limit": "shape checks only",
    }


def test_compact_snapshot_keeps_per_method_and_cycle_receipts():
    snapshot = compact_snapshot(_payload(12, 8, 4), "http://localhost/audit")
    module = snapshot["modules"]["cognitive_governor"]
    assert module["method_results"]["begin_cycle"]["last_output"]["quality"] == "present"
    assert module["last_output"]["quality"] == "no_return_unverified"
    assert snapshot["recent_cycle_evidence"]["cycles"][0]["cycle_id"] == 12
    assert snapshot["recent_cycle_evidence"]["cycles"][0]["stages"][0]["output_ref"] == "abc"


def test_compare_snapshots_reports_only_observed_counter_deltas():
    before = compact_snapshot(_payload(12, 8, 4), "http://localhost/audit")
    after = compact_snapshot(_payload(13, 11, 6, errors=1), "http://localhost/audit")
    delta = compare_snapshots(before, after)
    assert delta["cycle_delta"] == 1
    assert delta["new_errors"] == 1
    module = delta["module_deltas"]["cognitive_governor"]
    assert module["tick_count"] == 3
    assert module["methods"]["begin_cycle"]["tick_delta"] == 2
    assert module["methods"]["summary_log"]["error_delta"] == 1
    assert "semantic correctness" in delta["interpretation"]


def test_select_new_cycles_deduplicates_and_handles_lumina_restart():
    cycles = [{"cycle_id": 21}, {"cycle_id": 22}, {"cycle_id": 23}]
    fresh, newest = select_new_cycles(cycles, 22)
    assert [item["cycle_id"] for item in fresh] == [23]
    assert newest == 23

    restarted, reset_id = select_new_cycles([{"cycle_id": 2}, {"cycle_id": 3}], 23)
    assert [item["cycle_id"] for item in restarted] == [2, 3]
    assert reset_id == 3
