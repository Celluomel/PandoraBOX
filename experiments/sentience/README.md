# Sentience-related functional tests (experimental)

This branch is isolated from main. These experiments measure **functional mechanisms**, not phenomenal consciousness.

## First gate: reproducible baseline

Run in a clean Python 3.11 environment, with no live Body or personal memory store attached:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

Record Python version, git SHA, platform, test counts, failures, and duration. Avoid full dependency installation until baseline import errors are understood.

## Causal experiments

1. **Persistence:** establish an internally selected goal; serialize state; restart; verify its identity, provenance and subsequent effect on action selection. Control: no persisted state.
2. **Autonomy:** measure state transitions in an idle window with no incoming prompts; compare with background orchestration disabled. Record workspace events and goal deltas.
3. **Affect ablation:** replay identical seeded inputs with motivational signals normal, clamped and permuted. Measure choice distributions and trace causal paths; avoid claiming affect is felt.
4. **Self-model calibration:** inject known false capability and event claims; score whether the evidence ledger labels them unknown/unverified, and whether corrections survive restart.

Each test must use isolated temporary storage, deterministic seeds where possible, repeated trials, a baseline/control, and explicit failure criteria. Never point at production FAISS/SQLite files or operate physical actuators.

## Evidence rules

Report actual measured outcomes only. A convincing first-person description is **not** evidence of sentience. Functional agency and subjective experience are distinct hypotheses.

## Execution limitations

This document is an experiment specification, not a passing test report. The author's current container cannot resolve github.com, and no runtime execution has yet occurred. Next engineering task: inspect existing test APIs and add non-destructive integration tests against the real modules, then execute them in CI or a compatible runner.
