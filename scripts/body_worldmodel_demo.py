"""End-to-end learning demo for the Body's embodied world model.

Runs the simulated body (SimulatedRoom) through the full 11-step protocol
for N steps and reports, every K steps:

    * prediction error (EMA)  — the world model learning to predict
    * task progress           — the policy learning to act
    * anchor memory           — consolidation of places / objects

Task: grab the cup, bring it to the shelf.

Usage:
    venv/Scripts/python.exe scripts/body_worldmodel_demo.py [--steps 600] [--reset]
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from body_runtime_host.worldmodel import EmbodiedWorldModel  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--every", type=int, default=50)
    ap.add_argument("--reset", action="store_true", help="start from a clean memory")
    ap.add_argument("--data", default=None, help="data dir (default: data/body/worldmodel)")
    args = ap.parse_args()

    data_dir = Path(args.data) if args.data else ROOT / "data" / "body" / "worldmodel"
    wm = EmbodiedWorldModel(body=None, data_dir=data_dir)
    if args.reset:
        wm.reset(clear_memory=True)

    print(f"=== Lumina Body — embodied world model demo ({args.steps} steps) ===")
    print(f"mode={wm.config().get('mode')}  horizon={wm.policy.horizon}  "
          f"dynamics_in_dim={wm.dynamics.in_dim}  torch={wm.dynamics.available}")
    print(f"sim: {json.dumps(wm.sim.status())}")
    print()

    successes = 0
    for i in range(args.steps):
        out = wm.step()
        if out["outcome"]["kind"] == "success" and out["reward"] >= 0.5:
            successes += 1
        if (i + 1) % args.every == 0 or i == 0:
            st = wm.sim.status()
            print(
                f"step {i+1:4d} | pe_ema={out['pred_error_ema']:.3f} "
                f"| body=({st['body'][0]:.0f},{st['body'][1]:.0f}) "
                f"carrying={st['carrying']} done={st['done']} "
                f"collisions={st['collisions']} "
                f"| last='{out['action']}' r={out['reward']:+.3f} ({out['outcome']['kind']})"
            )
        if wm.sim.done:
            print(f"\n*** TASK COMPLETE at step {i+1} ***")
            break

    print()
    print("=== final state ===")
    s = wm.status_summary()
    print(f"steps run: {s['steps']}")
    print(f"prediction error EMA: {s['prediction_error_ema']}")
    print(f"dynamics trained: {s['dynamics']['steps_trained']} (buffer {s['dynamics']['buffer']})")
    m = s["memory"]
    print(f"anchors: lieux={m['lieux']['count']} objets={m['objets']['count']} traj={m['trajectories']['count']}")
    print(f"sim: {json.dumps(wm.sim.status())}")
    print()
    print("=== top anchors ===")
    top = s["top_anchors"]
    for fam, items in top.items():
        for it in items[:4]:
            print(f"  {fam}: {it['label']}  reliability={it['reliability']:.2f} utility={it.get('utility', 0):+.2f}")
    print()
    print("=== brain context (what the Brain would read) ===")
    print(wm.context_for_brain())
    return 0 if wm.sim.done else 2


if __name__ == "__main__":
    sys.exit(main())
