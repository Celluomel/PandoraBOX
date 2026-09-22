"""Simulated physical world — the Body's test environment.

A small grid room with a body (position, heading, reach, strength, gripper),
    a few physical objects with mass, one *target* (the cup), one intermediate
    surface (the table), one *drop zone* (the shelf) and one *obstacle*. The
    body's task is sequential: **grab → table → grab → shelf**.

This is the executable "body" used to demonstrate and test the embodied
world model end-to-end.  In a real deployment the Body's sensors and
actuators come from Home Assistant / the body bridge; this module is the
sandbox in which the same principles (affordances, latent dynamics,
imagination, consolidation) are learned and verified.

Physics implemented:
    * reach gating   — can only grab/push objects within reach
    * strength gate  — can only push objects lighter than its strength
    * collision      — moving into an obstacle is "danger" and blocks
    * carrying       — a grabbed object follows the body until released
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from .types import Action, BodyState, Observation, Outcome, SceneObject

GRID = 12          # room is GRID x GRID units
REACH = 1.8        # base reach (metres)
STRENGTH = 30.0    # max pushable mass


class SimulatedRoom:
    def __init__(self, seed_target: bool = True):
        self.width = GRID
        self.height = GRID
        # body
        self.px = 1.0
        self.py = 1.0
        self.heading = 0.0
        self.carrying: Optional[str] = None
        # objects: id -> dict
        self.objects: Dict[str, Dict[str, Any]] = {}
        self._reset_objects()
        # goal
        self.shelf = (1.0, 9.0)  # drop zone centre
        self.task_stage = "to_target"
        self.done = False
        self.steps = 0
        self.collision_count = 0
        self.near_miss_count = 0
        self._mobile_was_near = False
        self.success_count = 0

    # ── setup ───────────────────────────────────────────────────────────────

    def _reset_objects(self) -> None:
        self.objects = {
            "table": {
                "id": "table", "label": "table", "kind": "table",
                "x": 4.0, "y": 4.0, "mass": 25.0, "size": 1.0,
            },
            "chair": {
                "id": "chair", "label": "chair", "kind": "chair",
                "x": 8.0, "y": 3.0, "mass": 6.0, "size": 0.8,
            },
            "obstacle": {
                "id": "obstacle", "label": "pillar", "kind": "obstacle",
                "x": 6.0, "y": 6.0, "mass": 999.0, "size": 1.0,
            },
            "mobile_obstacle": {
                "id": "mobile_obstacle", "label": "moving obstacle", "kind": "mobile_obstacle",
                "x": 7.0, "y": 8.0, "mass": 999.0, "size": 0.8,
            },
            "cup": {
                "id": "cup", "label": "cup", "kind": "target",
                "x": 10.0, "y": 9.0, "mass": 0.4, "size": 0.4,
            },
        }

    def reset(self) -> None:
        self.px, self.py, self.heading = 1.0, 1.0, 0.0
        self.carrying = None
        self._reset_objects()
        self.shelf = (1.0, 9.0)
        self.task_stage = "to_target"
        self.done = False
        self.steps = 0
        self.collision_count = 0
        self.near_miss_count = 0
        self._mobile_was_near = False
        self.success_count = 0

    def shuffle_objects(self) -> None:
        """Place the scene objects in a fresh, collision-free arrangement."""
        cells = [
            (float(x), float(y))
            for x in range(1, self.width - 1)
            for y in range(1, self.height - 1)
        ]
        random.SystemRandom().shuffle(cells)
        self.shelf = next(
            cell for cell in cells
            if math.hypot(cell[0] - 1.0, cell[1] - 1.0) >= 2.0
        )
        reserved = [(1.0, 1.0), self.shelf]
        cells = [
            (float(x), float(y))
            for x in range(1, self.width - 1)
            for y in range(1, self.height - 1)
            if all(math.hypot(x - rx, y - ry) >= 1.5 for rx, ry in reserved)
        ]
        random.SystemRandom().shuffle(cells)
        placed: list[tuple[float, float]] = []
        for object_id in ("table", "chair", "obstacle", "mobile_obstacle", "cup"):
            candidates = [
                cell for cell in cells
                if all(math.hypot(cell[0] - px, cell[1] - py) >= 1.5 for px, py in placed)
                and (object_id != "cup" or math.hypot(cell[0] - self.shelf[0], cell[1] - self.shelf[1]) >= 3.0)
            ]
            if not candidates:
                break
            position = candidates[0]
            placed.append(position)
            self.objects[object_id]["x"], self.objects[object_id]["y"] = position

    def reset_episode(self, shuffle: bool = False) -> None:
        self.reset()
        if shuffle:
            self.shuffle_objects()

    # ── perception ──────────────────────────────────────────────────────────

    def body_state(self) -> BodyState:
        return BodyState(
            position=[self.px, self.py, 0.0],
            orientation=self.heading,
            capabilities={
                "reach": REACH, "speed": 1.0,
                "strength": STRENGTH, "gripper": 1.0,
                "world_width": float(self.width), "world_height": float(self.height),
                "task_stage": self.task_stage,
                "goal": list(self.shelf),
            },
        )

    def _scene(self) -> List[SceneObject]:
        out = []
        for o in self.objects.values():
            out.append(SceneObject(
                id=o["id"], label=o["label"], kind=o["kind"],
                position=[o["x"], o["y"], 0.0], size=o["size"], mass=o["mass"],
            ))
        return out

    def observe(self) -> Observation:
        body = self.body_state()
        scene = self._scene()
        text = self._describe()
        return Observation(
            subject="scene", value=None, source="simulated_room",
            kind="scene", confidence=1.0, scene=scene, text=text,
        )

    def _describe(self) -> str:
        parts = [f"Body at ({self.px:.1f},{self.py:.1f}) heading {math.degrees(self.heading):.0f}deg. Task stage: {self.task_stage}."]
        if self.carrying:
            parts.append(f"Carrying {self.carrying}.")
        objs = []
        for o in self.objects.values():
            d = math.hypot(o["x"] - self.px, o["y"] - self.py)
            rel = "within reach" if d <= REACH * (1.0 + 0.25 * o["size"]) else f"{d:.1f} away"
            objs.append(f"{o['label']} ({o['kind']}, {rel})")
        parts.append("Scene: " + "; ".join(objs) + f". Shelf at ({self.shelf[0]},{self.shelf[1]}).")
        return " ".join(parts)

    # ── action execution (the "physics") ────────────────────────────────────

    def _free_cell(self, x: float, y: float, ignore_id: str | None = None) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        if math.hypot(x - self.px, y - self.py) < 0.6:
            return False
        for o in self.objects.values():
            if o["id"] in {self.carrying, ignore_id}:
                continue
            if math.hypot(o["x"] - x, o["y"] - y) < 0.6:
                return False
        return True

    def _move_mobile_obstacle(self) -> bool:
        """Move the dynamic obstacle toward the Body, stopping before overlap.

        The Body is deliberately an attractor: this creates observable dynamic
        collision risk for the navigation policy instead of teaching the
        obstacle to keep away. Static geometry and the Body still block overlap.
        """
        mobile = self.objects.get("mobile_obstacle")
        if mobile is None or self.done:
            return False
        current_distance = math.hypot(mobile["x"] - self.px, mobile["y"] - self.py)
        candidates: list[tuple[float, float, float]] = []
        for dx, dy in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)):
            nx, ny = mobile["x"] + dx, mobile["y"] + dy
            if self._free_cell(nx, ny, ignore_id="mobile_obstacle"):
                distance = math.hypot(nx - self.px, ny - self.py)
                if distance < current_distance:
                    candidates.append((distance, nx, ny))
        if candidates:
            _, mobile["x"], mobile["y"] = min(candidates)
        near = math.hypot(mobile["x"] - self.px, mobile["y"] - self.py) <= 1.25
        entered_near_zone = near and not self._mobile_was_near
        self._mobile_was_near = near
        return entered_near_zone

    def step(self, action: Action) -> Tuple[Observation, Outcome]:
        """Execute one action; return (next_observation, outcome)."""
        self.steps += 1
        a = action.type
        reward = 0.0
        kind = "neutral"
        desc = ""

        if a == "forward":
            nx = self.px + math.cos(self.heading)
            ny = self.py + math.sin(self.heading)
            if self._free_cell(nx, ny):
                self.px, self.py = nx, ny
                desc = "moved forward"
            else:
                self.collision_count += 1
                reward -= 0.2
                kind = "danger"
                desc = "blocked (collision)"
        elif a == "backward":
            nx = self.px - math.cos(self.heading)
            ny = self.py - math.sin(self.heading)
            if self._free_cell(nx, ny):
                self.px, self.py = nx, ny
                desc = "moved backward"
            else:
                self.collision_count += 1
                reward -= 0.2
                kind = "danger"
                desc = "blocked (collision)"
        elif a == "turn_left":
            self.heading = (self.heading + math.radians(90) + math.pi) % (2 * math.pi) - math.pi
            desc = "turned left"
        elif a == "turn_right":
            self.heading = (self.heading - math.radians(90) + math.pi) % (2 * math.pi) - math.pi
            desc = "turned right"
        elif a == "grab":
            if self.carrying is not None:
                # single-slot gripper: you cannot grab while already carrying
                kind = "failure"
                reward -= 0.05
                desc = f"already carrying {self.carrying}"
            else:
                target = self._nearest_graspable()
                if target is None:
                    kind = "failure"
                    reward -= 0.05
                    desc = "nothing within reach to grab"
                else:
                    self.carrying = target["id"]
                    if target["id"] == "cup":
                        self.task_stage = "to_table" if self.task_stage == "to_target" else "to_shelf"
                    kind = "success"
                    # The environment knows its own goal: grabbing the *target*
                    # object (the cup) is strongly rewarded, grabbing anything
                    # else is only mildly useful.  This is the task signal the
                    # policy must learn to seek out.
                    reward += 0.3 if target["kind"] == "target" else 0.05
                    desc = f"grabbed {target['label']}"
        elif a == "release":
            if self.carrying is None:
                kind = "failure"
                desc = "not carrying anything"
            else:
                oid = self.carrying
                on_shelf = math.hypot(
                    self.objects[oid]["x"] - self.shelf[0],
                    self.objects[oid]["y"] - self.shelf[1],
                ) < 1.2
                table = self.objects["table"]
                on_table = math.hypot(self.px - table["x"], self.py - table["y"]) < 1.2
                if on_table and oid == "cup" and self.task_stage == "to_table":
                    self.objects[oid]["x"] = table["x"]
                    self.objects[oid]["y"] = table["y"]
                    self.carrying = None
                    self.task_stage = "to_target_from_table"
                    kind = "success"
                    reward += 0.4
                    self.success_count += 1
                    desc = f"placed {oid} on the table — intermediate objective complete"
                elif on_shelf and oid == "cup" and self.task_stage == "to_shelf":
                    self.objects[oid]["x"] = self.shelf[0]
                    self.objects[oid]["y"] = self.shelf[1]
                    self.carrying = None
                    kind = "success"
                    reward += 1.0
                    self.success_count += 1
                    self.done = True
                    desc = f"placed {oid} on the shelf — TASK COMPLETE"
                else:
                    self.objects[oid]["x"] = self.px
                    self.objects[oid]["y"] = self.py
                    self.carrying = None
                    kind = "failure"
                    reward -= 0.3
                    desc = f"dropped {oid} (not on a valid objective surface)"
        elif a == "push":
            target = self._nearest_pushable()
            if target is None:
                kind = "failure"
                reward -= 0.05
                desc = "nothing within reach to push"
            else:
                dx = self.px - target["x"]
                dy = self.py - target["y"]
                d = max(1e-6, math.hypot(dx, dy))
                ux, uy = dx / d, dy / d
                nx = target["x"] + ux
                ny = target["y"] + uy
                if self._free_cell(nx, ny):
                    target["x"], target["y"] = nx, ny
                    # push is a *neutral* interaction: it costs nothing but is
                    # not a task success either (no positive reward, so the
                    # policy cannot learn a spurious "pushing is good" optimum).
                    kind = "neutral"
                    desc = f"pushed {target['label']}"
                else:
                    kind = "failure"
                    desc = f"couldn't push {target['label']} (blocked)"
        else:  # wait
            desc = "waited"

        # The environment changes after the action, so the next decision must
        # use the resulting observation rather than a frozen obstacle map.
        near_miss = self._move_mobile_obstacle()

        # carried object follows the body (it is held, not left behind)
        if self.carrying is not None:
            self.objects[self.carrying]["x"] = self.px
            self.objects[self.carrying]["y"] = self.py

        # shaping reward: distance to goal (cup if not carried, shelf if carried)
        if not self.done:
            if self.carrying is None:
                cup = self.objects["cup"]
                goal = (cup["x"], cup["y"])
            else:
                goal = self.shelf
            dist = math.hypot(self.px - goal[0], self.py - goal[1])
            reward -= 0.02 * dist
            reward += 0.0  # (small positive shaping handled by value head)
        mobile = self.objects.get("mobile_obstacle")
        mobile_distance = math.hypot(mobile["x"] - self.px, mobile["y"] - self.py) if mobile else math.inf
        if mobile_distance <= 1.25:
            reward -= 0.12
            if kind == "neutral":
                kind = "danger"
            if near_miss:
                self.near_miss_count += 1
                desc = f"{desc}; moving obstacle entered the collision zone".strip("; ")

        outcome = Outcome(kind=kind, reward=round(float(reward), 4), description=desc)
        return self.observe(), outcome

    # ── affordance helpers (reach / strength gated) ─────────────────────────

    def _nearest_graspable(self) -> Optional[Dict[str, Any]]:
        best, best_d = None, None
        for o in self.objects.values():
            # Furniture and environmental structures are not gripper targets.
            # Without this guard the exploratory policy could grab the chair,
            # after which the normal carried-object rule made it follow the
            # Body and look like a second moving agent.
            if o["kind"] in {"obstacle", "mobile_obstacle", "table", "chair"} or o["mass"] > max(5.0, STRENGTH * 0.5):
                continue
            d = math.hypot(o["x"] - self.px, o["y"] - self.py)
            if d <= REACH * (1.0 + 0.25 * o["size"]):
                if best_d is None or d < best_d:
                    best, best_d = o, d
        return best

    def _nearest_pushable(self) -> Optional[Dict[str, Any]]:
        best, best_d = None, None
        for o in self.objects.values():
            if o["kind"] == "obstacle" or o["mass"] > STRENGTH:
                continue
            d = math.hypot(o["x"] - self.px, o["y"] - self.py)
            if d <= REACH * (1.0 + 0.25 * o["size"]):
                if best_d is None or d < best_d:
                    best, best_d = o, d
        return best

    # ── introspection ───────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "width": self.width, "height": self.height,
            "body": [round(self.px, 2), round(self.py, 2)],
            "heading_deg": round(math.degrees(self.heading), 1),
            "carrying": self.carrying,
            "task_stage": self.task_stage,
            "goal_sequence": ["to_target", "to_table", "to_target_from_table", "to_shelf"],
            "objects": {
                k: {"x": round(v["x"], 2), "y": round(v["y"], 2), "kind": v["kind"]}
                for k, v in self.objects.items()
            },
            "shelf": list(self.shelf),
            "done": self.done,
            "steps": self.steps,
            "collisions": self.collision_count,
            "near_misses": self.near_miss_count,
            "successes": self.success_count,
        }
