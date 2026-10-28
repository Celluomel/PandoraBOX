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

---

## Continued embodied development roadmap (after the immediate gate)

This is the **single canonical Codex handoff** for the current Body/Brain integration program. The earlier checklist is the first blocking milestone, not the whole project. Work sequentially unless a dependency or failing test requires a corrective detour. Every milestone must preserve existing behavior, remain local-first, and be independently reviewable and reversible. No milestone authorizes physical movement by itself.

### M0 — Reproducible offline reliability baseline (blocking)

**Work:** Complete the four-suite execution and CI verification described above. Resolve missing dependencies, mismatched mocks, failures and source defects. Add regression tests for each fix.

**Exit criteria:** All four suites pass in the real checkout and on the same SHA in GitHub Actions; exact test counts, commands, logs, and workflow URL recorded. **Stop** if this cannot be demonstrated; do not mark the gate complete based on code review alone.

### M1 — Brain-to-Body transport and command lifecycle (no actuation)

**Work:** Trace the actual command producer, serializer, transport, Body gateway, acknowledgements, and persisted replay ledger. Exercise real local transport against a fake Body adapter. Cover authorization provenance (not merely a string `status=approved`), expiry, clock skew, duplicate IDs, retries, network partitions, delayed/dropped acknowledgements, crash/restart and fail-closed behavior. Specify command states `proposed → approved → accepted/rejected → attempted → observed/failed/unknown`; never equate an HTTP 200 or an actuator ACK with observed physical success. Preserve backward compatibility deliberately and document any migration.

**Exit criteria:** Deterministic integration tests for happy path and each failure class; a failed or ambiguous delivery never results in an unguarded retry; no physical actuator adapter is called; documented protocol and transition table.

### M2 — Grounded perception and state validity

**Work:** Audit timestamps, coordinate frames, sensor origin, confidence, sensor/pose consistency and freshness from VENTUNO adapters through the world model. Explicitly distinguish unavailable, degraded, stale and valid data. Test out-of-order frames, impossible coordinates, NaN/Inf, missing fields, inconsistent units and sensor recovery. Keep safety guards at the final actuation boundary rather than relying only on planning-layer checks.

**Exit criteria:** Sensor contracts and replayable fixtures; freshness and provenance checks reject invalid data before any physical command; graceful degradation has documented permitted actions and test coverage.

### M3 — Closed-loop action verification and bounded recovery

**Work:** Define observable postconditions for movement/manipulation, separate command acceptance from execution and observed effect, and make plan transitions conditional on fresh post-action evidence. Audit `BodyPlanRuntime`, TaskGraph and `resume_after_recovery` for success, failure, pause, cancellation, expiry, restart and bounded retries. Verify no recovery action can silently bypass a paused plan or safety policy.

**Exit criteria:** Deterministic simulation tests demonstrate successful observed recovery, exhaustion to paused state, no infinite loops, and safe restart semantics; every transition is logged with the evidence that justified it.

### M4 — World-model learning and prediction benchmarks

**Work:** Establish reproducible simulation datasets and fixed-seed benchmarks for latent dynamics, short-horizon predictions, uncertainty calibration, affordance prediction, stability/plasticity and out-of-distribution behavior. Compare against simple nonlearning baselines. Check for data leakage and false improvements caused by simulator assumptions. Keep training separate from safety authorization.

**Exit criteria:** Versioned benchmark harness, baseline metrics and regression thresholds; learning improvements supported by held-out results, with failure cases recorded. No claim of physical generalization from simulation alone.

### M5 — Hierarchical planning and safe autonomy in simulation

**Work:** Integrate verified capabilities/skills with TaskGraph, world-model prediction, resource limits, operator constraints and navigation. Test interruptions, competing goals, stale plans, emergency-stop state, contradictory evidence and restart. Preserve the Body's authority to refuse Brain proposals. Avoid expanding action privileges as an incidental effect of improved planning.

**Exit criteria:** Repeatable scenarios show completion, refusal, cancellation, bounded recovery and auditability; no safety invariant regressions; measurable improvement over M4 baseline.

### M6 — VENTUNO hardware validation (operator-gated)

**Prerequisites:** M0–M3 verified; operator physically present; known firmware/adapter versions; e-stop and power isolation checked; constrained safe test space; explicit authorization for each test stage.

**Work:** Begin with read-only sensor/clock/frame validation, then stationary command-path dry runs, then individually authorized low-energy actions. Measure actual latency, stopping behavior, feedback consistency, drift and failure recovery. Disable actuation by default and stop on unexpected movement, stale telemetry or missing e-stop capability.

**Exit criteria:** Operator-signed hardware test report with measurements and failure notes. A passing offline CI run is **not** hardware certification.

### M7 — Iterative embodied capability expansion (only after hardware evidence)

**Work:** Improve perception, navigation, manipulation, learning and multimodal interaction in small, reversible increments. Each new physical capability needs a bounded operating envelope, simulator test, safety review, hardware-specific verification plan and explicit operator approval.

**Exit criteria:** Per-capability acceptance tests, versioned evidence and rollback procedure; do not describe the system as independently safe or generally autonomous based solely on limited trials.

## Codex operating rules and stop conditions

- **May proceed independently:** repository inspection, offline simulations, tests, docs, static audits, non-actuating adapters, minimal safety-preserving bug fixes, and CI diagnostics. Commit coherent, reviewed-in-context changes with regression coverage. Preserve local uncommitted work and existing features.
- **Must ask the operator first:** physical actuation or deployment to VENTUNO, disabling or weakening any safety interlock, changing authorization boundaries, destructive data migrations, force pushes, deleting user data, replacing models/configurations in a way that disrupts running systems, or major architectural rewrites.
- **Stop and report:** failing safety tests that cannot be resolved, unclear authorization semantics, non-reproducible results, missing hardware prerequisites, unverified CI, or a change that requires relaxing a safety invariant. Report blockers rather than inventing evidence.
- **Evidence ledger per milestone:** record commit SHA, exact commands, environment/dependencies, number of tests passing/failing/skipped, CI run URL and status, benchmark inputs/metrics where relevant, known limitations, and recommended next action. Keep simulated, mocked, integration and hardware evidence clearly separated.
- **Priority:** M0 first; then M1–M3 for trustworthy closed-loop behavior; M4–M5 for capability gains; M6 only with operator; M7 incrementally. Hardware absence is not a blocker to M0–M5.

## Updated Codex continuation instruction

> Read this entire file as the canonical PandoraBOX Body/Brain handoff. First close M0 with four-suite execution and a verified green CI run. Then advance through M1–M5 in dependency order, implementing and testing one bounded increment at a time while maintaining a milestone evidence ledger. You may autonomously perform non-actuating development, but you must stop and request explicit operator approval for hardware movement, safety-policy relaxation, destructive changes or deployment. Do not confuse mocked results, HTTP acknowledgements, simulator predictions or narrative claims with physical evidence. Preserve existing capabilities and report exact commits, tests, CI evidence, risks and next steps.


### Body recovery development update — 2026-10-28 (offline, hardware unavailable)

- `e1eb4dd`: In `EmbodiedWorldModel.step()`, a recovering plan now calls `resume_after_recovery` **only after** the original step postcondition is observed in a fresh post-action snapshot and pose; successful resume then permits `advance`. An actuator acknowledgement alone does not resume recovery. This fixes the prior control-flow dead end where `advance` rejected plans still in `recovery`.
- `962dec6`: Added plan-runtime tests for successful recovery → executing → completed and for refusal to resume an exhausted/paused plan.
- **Verification limitation:** these commits were checked into GitHub, but a passing four-suite CI run and hardware behavior are not verified. Do not mark M0 or M3 complete until real repository tests pass. In particular, add a world-model-level deterministic test proving that `step()` invokes the verified recovery path with fresh post-action evidence, and rejects stale/missing evidence.
- **Next recommended non-actuating work:** define explicit action-evidence lifecycle and verification states, ensure `execute_external` does not equate adapter acknowledgement with observed physical movement, and make learned-dynamics training distinguish verified versus uncertain transitions. Keep physical VENTUNO tests pending operator presence.


### Action evidence / learning gate update — 2026-10-28

**Implemented on `main` (source verified; execution/CI still unverified):**

- `1f74611`: `worldmodel/action_evidence.py` defines conservative `classify_action_evidence` states: `failed`, `not_executed`, `unknown`, `acknowledged_unverified`, `verified_simulation`, `verified_observation`. Verification requires a strictly newer fresh post-action timestamp and an explicit caller-provided observed postcondition; an actuator success response is never sufficient.
- `3345df8`: `EmbodiedWorldModel.execute_external` includes evidence in its response; without a task postcondition it reports an acknowledgement as unverified and does not update verified-success bookkeeping.
- `c205ede`: `BodyHost.execute_command` reports `acknowledged` rather than `executed` for a success outcome lacking verified evidence; also exposes `verification_status`. **Compatibility change:** audit every Brain/UI consumer of `command_result.status` and adapt to the new state before deployment.
- `308b51d`: command-delivery tests cover acknowledged versus explicitly verified execution.
- `7a88abf`, `f2f2b96`: deterministic evidence tests, including nonfinite, future, stale and reused frames.
- `008c8db`: the autonomous world-model step avoids feeding unverified physical transitions into learned dynamics; simulated transitions remain trainable. This does not yet provide a general-purpose verified physical training path.
- `63d316f`, `40aa587`: HTTP adapter reports an ambiguous/neutral outcome when a command ACK is followed by failed/stale post-action sensor polling; regression test verifies no false success.
- `33d518a`: CI includes the fifth evidence suite.
- `f88ecc3`, `cd7f186`: require strictly newer post-action sensor evidence for verification and plan completion.

**Updated offline test command:**

```bash
python -m unittest discover -s tests -p "test_body_action_evidence.py" -v
```

**Important unresolved tasks before declaring M1–M4 complete:**

1. Run **all five** suites from the actual checkout and obtain a green CI run for the same SHA. Fix any regressions from the status change.
2. Trace all Brain-side consumers of `executed` and `acknowledged`; document protocol compatibility and migration.
3. Add full `EmbodiedWorldModel.step()` integration tests for recovery, cached-frame refusal, and simulation learning; existing tests exercise mostly isolated components.
4. Build an explicit verified physical postcondition pipeline (motion/pose/target effect, confidence, source, timestamp, command correlation). Do not set `postcondition_observed=True` based only on controller acknowledgement or on elapsed time.
5. Add a genuine local transport integration test with a fake robot server; unit mocks are not network tests.
6. Benchmark learned dynamics on held-out simulated trajectories and compare with a nonlearning baseline.
7. Reserve hardware-specific latency, motor control, e-stop and calibration validation for when VENTUNO is available. Do not claim physical readiness from offline tests.

**Milestone status:** M0 remains OPEN pending real CI; M1–M4 are PARTIALLY IMPLEMENTED, not complete; M5+ not validated. The roadmap above remains the intended direction, not a record of completed milestones.
