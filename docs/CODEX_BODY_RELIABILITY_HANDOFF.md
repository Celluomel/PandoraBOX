# PandoraBOX / Lumina — Codex handoff: Body reliability gate

**Status:** Engineering gate OPEN. This document is a handoff for resuming work on the Brain PC when the operator returns home. It is not a claim of passing CI or physical hardware validation.

**Repository:** `Celluomel/PandoraBOX` · branch `main`

## Immediate goal

Run and fix all four Body reliability suites in the **actual repository environment**, obtain a reproducible green GitHub Actions run, then proceed to simulated Brain-to-Body network integration. Do not require or enable physical VENTUNO actuation for these tests.

## Resume checklist (Codex)

1. Open a fresh checkout of `main` on the Brain PC; check `git status`, `git log -8 --oneline`, and `python --version`. Preserve local uncommitted work. Do not blindly reset or overwrite it.
2. Create/use a Python 3.11 virtual environment. Install the dependencies required by the repository, starting with `numpy>=1.24,<2` (the current CI minimum). Inspect project requirements and imports if further dependencies are needed.
3. Run **all four** suites from the repository root, capture stdout/stderr and exit codes. Do not mark a suite passing based on a successful import or a mocked assertion alone.
4. Diagnose failures against the real implementation; fix root causes without deleting tests or weakening safety assertions. Commit each coherent fix, add regression coverage, and rerun all four suites.
5. Confirm GitHub Actions `Body reliability regression` passes on the resulting commit. Save the workflow URL, run ID, SHA, test counts, and logs in the final report. The workflow uploads `body-reliability-logs` even when tests fail.
6. Only after the offline gate is green: build a **non-actuating** Brain-to-Body transport integration test (real local HTTP/socket transport if available, with a fake Body/robot adapter), covering authentication, approval provenance, expiry, duplicates, dropped acknowledgements, reconnects, stale telemetry, and fail-closed behavior.
7. Defer VENTUNO hardware tests until physically present. Keep physical actuation disabled by default; require an explicit operator-controlled test plan, e-stop verification, and a safe test area before moving hardware.

## Exact commands (run from repository root)

```bash
python -m pip install "numpy>=1.24,<2"
python -m unittest discover -s tests -p "test_body_reliability_v1.py" -v
python -m unittest discover -s tests -p "test_body_command_replay.py" -v
python -m unittest discover -s tests -p "test_body_http_fault_injection.py" -v
python -m unittest discover -s tests -p "test_body_command_delivery.py" -v
```

On Windows PowerShell, activate the project venv first and use the same `python -m unittest` commands. If tests fail to import, identify the missing package/module from the traceback and update the reproducible dependency declaration; do not install arbitrary packages without checking repository requirements.

GitHub Actions workflow: [Body reliability regression](https://github.com/Celluomel/PandoraBOX/actions/workflows/body-reliability.yml). Select **Run workflow** on `main` or inspect the latest push run.

## Suites and expected properties

| Suite | Scope | Essential safety invariant |
|---|---|---|
| `tests/test_body_reliability_v1.py` | Snapshot freshness, bounded recovery, persistence, paused-plan behavior | Stale geometry and exhausted recovery cannot authorize movement |
| `tests/test_body_command_replay.py` | Durable command ID reservations, expiry validation, corruption and disk failure | Restart, renewed expiry and malformed ledger cannot replay commands |
| `tests/test_body_http_fault_injection.py` | Mocked HTTP robot sensor faults | Outages, missing/zero/stale/future telemetry and disabled actuation never issue `POST /command` |
| `tests/test_body_command_delivery.py` | Minimal mocked `BodyHost` command gateway | Unapproved/expired/duplicate commands and failures cannot be reported as executed |

**Important:** The HTTP and command-delivery tests are isolated unit/fault-injection tests, **not** proof of full Brain-to-Body transport integration or real VENTUNO behavior.

## Recent development context

- `4d489f2`: offline HTTP sensor fault injection.
- `515ff9b`: CI includes HTTP fault tests.
- `5ed979a`: fresh pose check at final HTTP actuator boundary.
- `288a454`: physical actuation requires explicit robot-origin sensor timestamp.
- `92ff655`: missing-timestamp regression test.
- `2800fa2`: offline Brain-to-Body command-delivery tests.
- `ba5ca04`: CI includes delivery tests.
- `86f9be6`: preserve zero timestamp rather than replacing it with local time.
- `8fe5334`: zero-timestamp regression.
- `45658d3`: initialize post-action observation when no source is attached.
- `9467131`: publish CI logs as artifacts.

**Evidence:** The previous assistant reported 8/8 command-replay tests passing in an isolated reconstructed environment, but there is **no verified full-repository four-suite run** and no verified green CI baseline. Treat all four suites as unverified until executed on the checked-out repository.

## Audit items while resolving the gate

- Check the complete `RobotHttpSource.execute_authorized` flow and its timestamp/pose checks. Distinguish robot-origin timestamps from locally synthesized observation times; confirm behavior for malformed, nonfinite, stale, future and absent timestamps.
- Inspect `BodyHost.execute_command` for actual Brain-side command producer compatibility (`command_id`, `expires_at`, `status=approved`), authentic approval provenance and clear failure semantics. A string field saying `approved` is not itself authentication.
- Review `CommandReplayLedger` for multi-process concurrency and crash durability (atomic replace does not imply fsync), and malformed direct-call inputs. Maintain fail-closed behavior.
- Review `BodyPlanRuntime` recovery completion: a recovery action acknowledgment must not be confused with an observed postcondition; avoid both infinite recovery and permanent unnecessary pause.
- Inspect whether CI imports the full worldmodel package and needs additional dependencies. Record reproducible fixes.
- Do not conflate successful HTTP acknowledgment with verified physical movement.

## Definition of done for the current gate

- All four commands exit 0 from the real checkout, with captured logs and test counts.
- A green GitHub Actions run for the same commit is verified and linked.
- Any failures are repaired with regression tests, without bypassing safety checks.
- The handoff report states exactly what was tested and what remains untested.
- Physical actuation remains disabled; VENTUNO hardware validation is explicitly pending.

## Prompt to paste into Codex

> Continue the PandoraBOX / Lumina Body reliability engineering gate using `docs/CODEX_BODY_RELIABILITY_HANDOFF.md`. Work on the current `main` checkout without discarding local changes. Run all four offline suites in the actual repository, capture results, fix failures at their source, rerun all suites, and verify a green GitHub Actions run on the same commit. Then propose or implement non-actuating Brain-to-Body transport fault-injection tests. Preserve all existing features and fail-closed safety behavior. Do not enable physical VENTUNO actuation or claim hardware validation. Report commits, exact commands, pass/fail counts, CI URL, and remaining risks.
