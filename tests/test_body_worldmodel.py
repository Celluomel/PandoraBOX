"""Tests for the Body's embodied world model (body_runtime_host.worldmodel).

Run:  venv/Scripts/python.exe -m pytest tests/test_body_worldmodel.py -v
"""
import math
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class WorldModelTypesTest(unittest.TestCase):
    def test_north_up_heading_transform_matches_world_cardinals(self):
        from body_runtime_host.coordinate_frames import (
            compass_heading_degrees,
            north_up_svg_rotation_degrees,
        )

        for heading, compass, svg_rotation in (
            (0.0, 90.0, 90.0),
            (math.pi / 2, 0.0, 0.0),
            (math.pi, 270.0, -90.0),
            (-math.pi / 2, 180.0, 180.0),
        ):
            with self.subTest(heading=heading):
                self.assertAlmostEqual(compass_heading_degrees(heading), compass)
                self.assertAlmostEqual(north_up_svg_rotation_degrees(heading), svg_rotation)
                radians = math.radians(svg_rotation)
                rendered_front = (math.sin(radians), -math.cos(radians))
                expected_front = (math.cos(heading), -math.sin(heading))
                self.assertAlmostEqual(rendered_front[0], expected_front[0], places=7)
                self.assertAlmostEqual(rendered_front[1], expected_front[1], places=7)

    def test_anchor_serialization_roundtrip(self):
        from body_runtime_host.worldmodel import AnchorLieu, AnchorObjet, Action

        lieu = AnchorLieu(label="kitchen", position=[1.0, 2.0, 0.0], affordances={"forward": 0.8})
        d = lieu.as_dict()
        lieu2 = AnchorLieu.from_dict(d)
        self.assertEqual(lieu2.label, "kitchen")
        self.assertEqual(lieu2.position, [1.0, 2.0, 0.0])
        self.assertAlmostEqual(lieu2.affordances["forward"], 0.8)

        obj = AnchorObjet(id="cup", label="cup", kind="target")
        self.assertEqual(AnchorObjet.from_dict(obj.as_dict()).id, "cup")

        act = Action(type="grab", target="cup", params={"dx": 0.5})
        act2 = Action.from_dict(act.as_dict())
        self.assertEqual(act2.type, "grab")
        self.assertEqual(act2.target, "cup")

    def test_body_state_defaults(self):
        from body_runtime_host.worldmodel import BodyState

        b = BodyState()
        self.assertEqual(b.position, [0.0, 0.0, 0.0])
        self.assertEqual(b.capabilities.get("reach", 0), 1.8)


class CortexTest(unittest.TestCase):
    def test_affordances_respect_reach(self):
        from body_runtime_host.worldmodel import (
            ArtificialCortex, BodyState, Observation, SceneObject,
        )

        cortex = ArtificialCortex()
        body = BodyState(position=[0.0, 0.0, 0.0], capabilities={"reach": 1.5})
        obs = Observation(
            scene=[
                SceneObject(id="near", label="near", kind="chair", position=[1.0, 0.0, 0.0], mass=5.0, size=0.8),
                SceneObject(id="far", label="far", kind="table", position=[9.0, 0.0, 0.0], mass=25.0, size=1.0),
            ]
        )
        aff = cortex.affordances(obs, body)
        by_id = {w["id"]: w for w in aff["which2act"]}
        # near is within reach -> actionable (grab/push); far is only approachable
        self.assertIn("near", by_id)
        self.assertIn("far", by_id)
        self.assertTrue(by_id["near"]["in_reach"])
        self.assertFalse(by_id["far"]["in_reach"])
        self.assertIn("grab", by_id["near"]["actions"])
        self.assertNotIn("grab", by_id["far"]["actions"])
        self.assertIn("approach", by_id["far"]["actions"])
        # how2act only contains actions the body is actually able to do
        for h in aff["how2act"]:
            self.assertGreaterEqual(h["score"], 0.0)
            self.assertLessEqual(h["score"], 1.0)

    def test_encode_is_deterministic_and_body_conditioned(self):
        from body_runtime_host.worldmodel import (
            ArtificialCortex, BodyState, Observation,
        )

        cortex = ArtificialCortex()
        obs = Observation(text="a chair and a table are visible")
        b1 = BodyState(position=[0.0, 0.0, 0.0], capabilities={"reach": 1.0})
        b2 = BodyState(position=[5.0, 5.0, 0.0], capabilities={"reach": 3.0})
        v1 = cortex.encode(obs, b1)
        v1b = cortex.encode(obs, b1)
        v2 = cortex.encode(obs, b2)
        self.assertEqual(v1.shape, v2.shape)
        self.assertTrue(all(a == b for a, b in zip(v1, v1b)))
        self.assertTrue(any(a != b for a, b in zip(v1, v2)))

    def test_action_space_gated_by_body(self):
        from body_runtime_host.worldmodel import BodyState, action_space_for_body

        weak = BodyState(capabilities={"gripper": 0.0, "strength": 0.5})
        types = {a.type for a in action_space_for_body(weak)}
        self.assertNotIn("grab", types)
        self.assertNotIn("push", types)

        strong = BodyState(capabilities={"gripper": 1.0, "strength": 40.0})
        types = {a.type for a in action_space_for_body(strong)}
        self.assertIn("grab", types)
        self.assertIn("push", types)


class DynamicsTest(unittest.TestCase):
    def test_dynamics_learns_a_linear_world(self):
        import numpy as np
        from body_runtime_host.worldmodel import LatentWorldDynamics, encode_action

        torch_ok = LatentWorldDynamics(4).available
        if not torch_ok:
            self.skipTest("torch unavailable")
        wm = LatentWorldDynamics(in_dim=8, latent_dim=16, hidden_dim=32, lr=1e-2)
        rng = np.random.default_rng(0)
        # World: x_next = 0.9*x + 0.5*action_effect (per-dim)
        errors = []
        for step in range(400):
            x = rng.normal(size=8).astype("float32") * 0.5
            a = encode_action({"type": "forward", "params": {"dx": 0.5}})
            x_next = (0.9 * x + 0.5 * np.abs(a)[:8]).astype("float32")
            wm.remember(x, a, x_next, reward=0.1, success=True)
            loss = wm.train_step(batch=32, epochs=1)
            if loss is not None and step % 20 == 19:
                # measure one-step prediction error
                s = wm.encode(x)
                s_pred = wm.step(s, a)
                s_true = wm.encode(x_next)
                errors.append(float(np.sqrt(np.mean((np.asarray(s_pred) - np.asarray(s_true)) ** 2))))
        self.assertLess(errors[-1], errors[0], f"error should decrease: {errors}")

    def test_counterfactual_is_action_conditioned(self):
        import numpy as np
        from body_runtime_host.worldmodel import LatentWorldDynamics

        wm = LatentWorldDynamics(in_dim=8)
        if not wm.available:
            self.skipTest("torch unavailable")
        # counterfactual operates on a *latent state* (output of encode)
        s = wm.encode(np.zeros(8, dtype="float32"))
        cf_a = wm.counterfactual(s, "forward", horizon=4)
        cf_b = wm.counterfactual(s, "wait", horizon=4)
        self.assertEqual(cf_a["horizon"], 4)
        self.assertIn("terminal_value", cf_a)
        # Different actions must (almost surely) produce different imagined futures
        self.assertNotEqual(cf_a["terminal_state_norm"], cf_b["terminal_state_norm"])


class AnchorsTest(unittest.TestCase):
    def test_anchor_merge_and_reinforce_stability(self):
        from body_runtime_host.worldmodel import PhysicalMemory, AnchorLieu

        with tempfile.TemporaryDirectory() as tmp:
            mem = PhysicalMemory(Path(tmp) / "anchors.json")
            a1 = mem.upsert_lieu(label="spot", position=[1.0, 1.0, 0.0])
            a2 = mem.upsert_lieu(label="spot2", position=[1.5, 1.2, 0.0])
            self.assertEqual(a1.id, a2.id, "nearby places must merge into one anchor")
            self.assertGreaterEqual(mem.lieux[a1.id].visits, 2)

            # A reliable anchor must adapt SLOWLY (stability/plasticity)
            reliable = mem.lieux[a1.id]
            reliable.reliability = 0.95
            from body_runtime_host.worldmodel import ConsolidationEngine
            eng = ConsolidationEngine(mem)
            alpha_fast = eng._effective_alpha(0.1)
            alpha_slow = eng._effective_alpha(0.95)
            self.assertGreater(alpha_fast, alpha_slow)

            # persistence round-trip
            mem.save()
            mem2 = PhysicalMemory(Path(tmp) / "anchors.json")
            self.assertEqual(len(mem2.lieux), 1)
            self.assertEqual(mem2.lieux[a1.id].visits, reliable.visits)

    def test_reset_is_explicit(self):
        from body_runtime_host.worldmodel import PhysicalMemory

        with tempfile.TemporaryDirectory() as tmp:
            mem = PhysicalMemory(Path(tmp) / "anchors.json")
            mem.upsert_objet("x", "x", "object", [0.0, 0.0, 0.0])
            mem.reset()
            self.assertEqual(mem.stats()["objets"]["count"], 0)


class SimWorldTest(unittest.TestCase):
    def test_grab_requires_reach(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        # cup is at (10,9), body at (1,1): far away
        obs, outcome = room.step(Action(type="grab"))
        self.assertEqual(outcome.kind, "failure")
        self.assertIsNone(room.carrying)

    def test_collision_is_danger(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        # pillar at (6,6); face it and walk in
        room.px, room.py, room.heading = 5.0, 6.0, 0.0
        _, outcome = room.step(Action(type="forward"))
        self.assertEqual(outcome.kind, "danger")
        self.assertEqual(room.px, 5.0, "body must not pass through the obstacle")

    def test_mobile_obstacle_approaches_body_and_records_near_miss(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        room.px, room.py = 5.0, 5.0
        room.objects["mobile_obstacle"]["x"] = 8.0
        room.objects["mobile_obstacle"]["y"] = 5.0

        room.step(Action(type="wait"))
        self.assertEqual(room.objects["mobile_obstacle"]["x"], 7.0)
        room.step(Action(type="wait"))
        self.assertEqual(room.objects["mobile_obstacle"]["x"], 7.0, "pursuer moves at half the Body's decision rate")
        _, outcome = room.step(Action(type="wait"))

        mobile = room.objects["mobile_obstacle"]
        self.assertEqual((mobile["x"], mobile["y"]), (6.0, 5.0))
        self.assertEqual(room.near_miss_count, 1)
        self.assertEqual(outcome.kind, "danger")
        self.assertLess(outcome.reward, -0.12)

        _, collision = room.step(Action(type="forward"))
        self.assertEqual(collision.kind, "danger")
        self.assertEqual(room.collision_count, 1)
        self.assertEqual((room.px, room.py), (5.0, 5.0))

    def test_sprint_uses_speed_advantage_without_tunneling(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        room.px, room.py, room.heading = 2.0, 5.0, 0.0
        room.objects["mobile_obstacle"]["x"] = 8.0
        room.objects["mobile_obstacle"]["y"] = 5.0
        _, outcome = room.step(Action(type="sprint", params={"speed": 2.0}))
        self.assertEqual((room.px, room.py), (4.0, 5.0))
        self.assertIn("sprinted 2 cells", outcome.description)
        self.assertGreaterEqual(room.status()["mobile_obstacle_speed_cells_per_action"], 0.2)
        self.assertLessEqual(room.status()["mobile_obstacle_speed_cells_per_action"], 0.9)
        self.assertEqual(room.objects["mobile_obstacle"]["x"], 7.0, "pursuer reacts to the pre-sprint Body position")

        room.objects["obstacle"]["x"] = 5.0
        room.objects["obstacle"]["y"] = 5.0
        _, blocked = room.step(Action(type="sprint", params={"speed": 2.0}))
        self.assertEqual((room.px, room.py), (4.0, 5.0), "sprint must stop before fixed geometry")
        self.assertEqual(blocked.kind, "danger")

    def test_fixed_object_can_block_pursuing_obstacle(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        room.px, room.py = 5.0, 5.0
        room.objects["obstacle"]["x"] = 7.0
        room.objects["obstacle"]["y"] = 5.0
        room.objects["mobile_obstacle"]["x"] = 8.0
        room.objects["mobile_obstacle"]["y"] = 5.0
        room.step(Action(type="wait"))
        status = room.status()
        self.assertEqual(status["objects"]["mobile_obstacle"]["x"], 8.0)
        self.assertTrue(status["mobile_obstacle_blocked_by_static_object"])

    def test_mobile_obstacle_escapes_when_close_pursuit_cell_is_unavailable(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        room.px, room.py = 5.0, 5.0
        room.objects["mobile_obstacle"]["x"] = 6.0
        room.objects["mobile_obstacle"]["y"] = 5.0

        room.step(Action(type="wait"))
        status = room.status()
        self.assertNotEqual(
            (status["objects"]["mobile_obstacle"]["x"], status["objects"]["mobile_obstacle"]["y"]),
            (6.0, 5.0),
            "a close mobile obstacle must choose a safe escape cell instead of freezing",
        )
        self.assertNotEqual(status["mobile_obstacle_velocity"], [0.0, 0.0])
        self.assertTrue(status["mobile_obstacle_blocked_by_static_object"])

    def test_navigation_detours_and_keeps_advancing_near_mobile_obstacle(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom
        from body_runtime_host.worldmodel.navigation import navigation_guidance

        room = SimulatedRoom()
        room.px, room.py, room.heading = 5.0, 5.0, 0.0
        room.objects["mobile_obstacle"]["x"] = 6.0
        room.objects["mobile_obstacle"]["y"] = 5.0

        guidance = navigation_guidance(room.observe(), room.body_state())
        self.assertIn("forward", guidance["forbidden"])
        self.assertEqual(guidance["recommended"], "retreat")

        room.step(Action(type=guidance["recommended"]))
        self.assertEqual(room.px, 3.0)
        self.assertEqual(room.status()["mobile_obstacle_distance"], 2.0)

    def test_navigation_reverses_instead_of_spinning_when_pursuer_blocks_front(self):
        from body_runtime_host.worldmodel import SimulatedRoom
        from body_runtime_host.worldmodel.navigation import navigation_guidance

        room = SimulatedRoom()
        room.px, room.py, room.heading = 5.0, 5.0, 0.0
        room.objects["mobile_obstacle"]["x"] = 6.0
        room.objects["mobile_obstacle"]["y"] = 5.0
        guidance = navigation_guidance(room.observe(), room.body_state())
        self.assertEqual(guidance["recommended"], "retreat")

    def test_navigation_holds_when_pursuer_closes_both_directions(self):
        from body_runtime_host.worldmodel import SimulatedRoom
        from body_runtime_host.worldmodel.navigation import navigation_guidance

        room = SimulatedRoom()
        room.px, room.py, room.heading = 5.0, 5.0, 0.0
        room.objects["mobile_obstacle"]["x"] = 6.0
        room.objects["mobile_obstacle"]["y"] = 5.0
        room.objects["obstacle"]["x"] = 4.0
        room.objects["obstacle"]["y"] = 5.0
        guidance = navigation_guidance(room.observe(), room.body_state())
        self.assertEqual(guidance["recommended"], "wait")

    def test_predictive_route_breaks_chase_loop_and_reaches_goal(self):
        from body_runtime_host.worldmodel import Action, SimulatedRoom
        from body_runtime_host.worldmodel.navigation import navigation_guidance

        room = SimulatedRoom()
        room.px, room.py, room.heading = 10.0, 6.0, -math.pi / 2
        room.carrying = "cup"
        room.task_stage = "to_shelf"
        room.shelf = (5.0, 5.0)
        room.objects["table"].update(x=8.0, y=9.0)
        room.objects["chair"].update(x=9.0, y=3.0)
        room.objects["obstacle"].update(x=1.0, y=4.0)
        room.objects["mobile_obstacle"].update(x=9.0, y=6.0)
        room.objects["cup"].update(x=10.0, y=6.0)

        for _ in range(10):
            guidance = navigation_guidance(room.observe(), room.body_state(), carrying=True)
            room.step(Action(type=guidance["recommended"] or "wait", params={"speed": 2.0}))
            if room.done:
                break
        self.assertTrue(room.done, "time-aware routing should avoid chasing the moving obstacle in a loop")
        self.assertEqual(room.carrying, None)

    def test_full_task_is_solvable(self):
        """A scripted (non-learned) policy must be able to solve the task —
        proving the environment itself is solvable (separates environment
        correctness from learning)."""
        import math
        from body_runtime_host.worldmodel import Action, SimulatedRoom

        room = SimulatedRoom()
        # This fixture checks the static manipulation route; dynamic obstacle
        # interaction has its own attraction/avoidance test above.
        room.objects.pop("mobile_obstacle")

        def walk_to(x: float, y: float) -> None:
            """Axis-aligned walk to (x, y) — the grid is unit-stepped."""
            guard = 0
            while (room.px, room.py) != (x, y) and guard < 200:
                if room.px < x:
                    room.heading = 0.0
                elif room.px > x:
                    room.heading = math.pi
                elif room.py < y:
                    room.heading = math.pi / 2
                else:
                    room.heading = -math.pi / 2
                room.step(Action(type="forward"))
                guard += 1

        # (1,1) -> (1,9): approach the cup's row
        walk_to(1.0, 9.0)
        # -> (9,9): next to the cup (its own cell is occupied)
        walk_to(9.0, 9.0)
        obs, out = room.step(Action(type="grab"))
        self.assertEqual(out.kind, "success", f"expected to grab cup, got {out.description}")
        self.assertEqual(room.carrying, "cup")
        # carried object must follow the body
        self.assertAlmostEqual(room.objects["cup"]["x"], room.px)
        # Place it on the intermediate table, then retrieve it.
        walk_to(3.0, 4.0)
        _, out = room.step(Action(type="release"))
        self.assertEqual(out.kind, "success", f"expected table placement, got {out.description}")
        walk_to(3.0, 4.0)
        _, out = room.step(Action(type="grab"))
        self.assertEqual(out.kind, "success", f"expected to retrieve cup, got {out.description}")
        # Carry it to the shelf (1,9).
        walk_to(1.0, 9.0)
        obs, out = room.step(Action(type="release"))
        self.assertTrue(room.done, f"task should complete: {out.description}")
        self.assertGreaterEqual(out.reward, 1.0)


class CoreLoopTest(unittest.TestCase):
    def test_step_protocol_runs_and_learns(self):
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            out = None
            for _ in range(30):
                out = wm.step()
            self.assertIsNotNone(out)
            self.assertIn(out["outcome"]["kind"], {"success", "failure", "danger", "neutral"})
            self.assertGreaterEqual(wm._steps, 30)
            # memory must have been activated
            self.assertGreaterEqual(wm.memory.stats()["objets"]["count"], 4)
            self.assertGreaterEqual(wm.memory.stats()["lieux"]["count"], 1)
            # prediction error must be finite
            self.assertTrue(math.isfinite(wm._pred_error_ema))
            # brain context must be non-empty and grounded
            ctx = wm.context_for_brain()
            self.assertIn("CURRENT EMBODIED STATE", ctx)
            self.assertIn("places", ctx)

    def test_status_summary_serializable(self):
        import json
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            wm.step()
            payload = json.dumps(wm.status_summary(), default=str)
            self.assertIn("prediction_error_ema", payload)

    def test_stalled_objective_alert_is_exposed_to_brain(self):
        from unittest.mock import patch
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            wm._navigation_stagnation = 7
            wm._navigation_objective_key = ("to_target", (10.0, 9.0))
            stalled = {
                "target": [10.0, 9.0], "phase": "to_target", "distance_to_target": 12.0,
                "recommended": "turn_left", "forbidden": [], "prior": {},
            }
            with patch("body_runtime_host.worldmodel.core.navigation_guidance", return_value=stalled):
                wm.step()
            status = wm.status_summary()
            self.assertEqual(status["goal_status"]["state"], "blocked")
            self.assertEqual(status["navigation_alert"]["type"], "goal_progress_stalled")
            self.assertIn("BODY ALERT", wm.context_for_brain())

    def test_completed_body_is_reported_as_terminal_not_current_motion(self):
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            wm.sim.done = True
            wm.sim.steps = 17
            context = wm.context_for_brain()
            self.assertIn("TERMINAL BODY STATE", context)
            self.assertIn("stopped", context)
            self.assertIn("Final Body pose from the live simulator", context)
            self.assertNotIn("Active Body plan:", context)

    def test_new_plan_reopens_terminal_simulation_without_teleporting_body(self):
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            wm.sim.done = True
            wm.sim.steps = 24
            wm.sim.px, wm.sim.py = 5.0, 6.0
            result = wm.submit_plan({
                "objective": "inspect the cup",
                "required_capabilities": ["navigate"],
                "expires_at": time.time() + 60,
                "steps": [{"step_id": "inspect", "verb": "inspect", "target": "cup"}],
            })
            self.assertTrue(result["accepted"])
            self.assertFalse(wm.sim.done)
            self.assertEqual(wm.sim.steps, 24)
            self.assertEqual(wm.sim.body_state().position[:2], [5.0, 6.0])

    def test_reset_clears_state(self):
        from body_runtime_host.worldmodel import EmbodiedWorldModel

        with tempfile.TemporaryDirectory() as tmp:
            wm = EmbodiedWorldModel(body=None, data_dir=tmp)
            for _ in range(5):
                wm.step()
            wm.reset(clear_memory=True)
            self.assertEqual(wm._steps, 0)
            self.assertEqual(wm.memory.stats()["lieux"]["count"], 0)


import math  # noqa: E402  (used in CoreLoopTest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
