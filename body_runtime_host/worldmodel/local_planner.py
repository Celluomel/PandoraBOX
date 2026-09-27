"""Deterministic local routing over a Body snapshot.

This is intentionally independent of an LLM and of the learned policy.  It
turns a current scene into a short, explainable route and can be re-run on any
new observation when dynamic geometry changes.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .contracts import BodySnapshot
from .types import BodyState

Cell = Tuple[int, int]


@dataclass
class Route:
    target: str
    cells: List[Cell] = field(default_factory=list)
    reason: str = ""
    blocked: bool = False
    replanned: bool = False

    @property
    def next_cell(self) -> Optional[Cell]:
        return self.cells[1] if len(self.cells) > 1 else None

    def as_dict(self) -> Dict[str, Any]:
        return {"target": self.target, "cells": [list(cell) for cell in self.cells], "reason": self.reason, "blocked": self.blocked, "replanned": self.replanned}


class LocalRoutePlanner:
    """A* routing with obstacle inflation and reachable destination cells."""

    _BLOCKING_KINDS = {"obstacle", "chair", "table", "surface", "wall", "mobile_obstacle"}

    def __init__(self, geometry_mode: str = "continuous") -> None:
        # ``legacy_grid`` is retained only for paired benchmark comparisons.
        # Runtime planning defaults to the same metric envelope as the simulator.
        self.geometry_mode = "legacy_grid" if geometry_mode == "legacy_grid" else "continuous"
        self._scene_signatures: Dict[str, tuple] = {}
        self._next_segments: Dict[str, tuple[tuple[float, float], Cell, Cell]] = {}

    def route(self, target_id: str, snapshot: BodySnapshot, body: BodyState, reach: Optional[float] = None) -> Route:
        target = next((item for item in snapshot.objects if str(item.get("id")) == target_id), None)
        if target is None:
            return Route(target_id, reason="unknown_target", blocked=True)
        width = max(2, int(round(float(body.capabilities.get("world_width", 12)))))
        height = max(2, int(round(float(body.capabilities.get("world_height", 12)))))
        start = self._cell(body.position, width, height)
        blocked = self._blocked_cells(snapshot, target_id, width, height, body=body)
        mobile = next(
            (item for item in snapshot.objects if str(item.get("kind")) == "mobile_obstacle"),
            None,
        )
        predicted_mobile = body.capabilities.get("mobile_obstacle_predicted_position")
        if mobile is not None and str(mobile.get("id")) != target_id and predicted_mobile:
            predicted_cell = self._cell(predicted_mobile, width, height)
            if predicted_cell != start:
                blocked.add(predicted_cell)
        signature = tuple(sorted((str(item.get("id")), tuple(round(float(v), 1) for v in (item.get("position") or [])[:2])) for item in snapshot.objects))
        scene_changed = target_id in self._scene_signatures and self._scene_signatures[target_id] != signature
        replanned = scene_changed
        self._scene_signatures[target_id] = signature
        target_position = tuple(float(value) for value in (target.get("position") or [0.0, 0.0])[:2])
        cached = self._next_segments.get(target_id)
        if cached is not None:
            cached_target, cached_start, cached_next = cached
            if (
                not replanned
                and cached_target == target_position
                and cached_start == start
                and cached_next not in blocked
                and self._segment_clear(snapshot, body, cached_start, cached_next, target_id)
            ):
                return Route(target_id, [start, cached_next], "cached_safe_segment", replanned=False)
        goals = self._goal_cells(target, body, width, height, blocked, reach=reach)
        if start in goals:
            return Route(target_id, [start], "already_near_target", replanned=replanned)
        path = self._astar(start, goals, blocked, width, height)
        route_reason = ""
        if not path:
            # A mobile obstacle is a time-varying hazard, not permanent
            # architecture. If its current cell seals the snapshot route,
            # compute a provisional route through that cell and let the next
            # Body observation/collision check decide whether to wait or
            # replan. This prevents manipulation plans from dead-locking on
            # a transient obstacle that has an escape trajectory.
            dynamic_blocked = self._blocked_cells(snapshot, target_id, width, height, ignored_kinds={"mobile_obstacle"}, body=body)
            if dynamic_blocked != blocked:
                path = self._astar(start, goals, dynamic_blocked, width, height)
                if path:
                    blocked = dynamic_blocked
                    route_reason = "replan_around_dynamic_obstacle"
        if path and self.geometry_mode == "continuous":
            # A grid path can still cut through an inflated corner. Validate
            # every edge in metric space and fail closed if the projection is
            # not physically clear; the next observation can then replan.
            if not all(
                self._segment_clear(snapshot, body, left, right, target_id)
                for left, right in zip(path, path[1:])
            ):
                return Route(target_id, reason="metric_clearance_blocked", blocked=True, replanned=replanned)
        if not path:
            return Route(target_id, reason="recover_from_blockage", blocked=True, replanned=replanned)
        direct = abs(start[0] - path[-1][0]) + abs(start[1] - path[-1][1])
        reason = route_reason or ("replan_after_scene_change" if replanned else "avoid_obstacle" if len(path) - 1 > direct else "toward_target")
        if len(path) > 1:
            self._next_segments[target_id] = (target_position, start, path[1])
        return Route(target_id, path, reason, replanned=replanned)

    @staticmethod
    def _cell(position: List[float], width: int, height: int) -> Cell:
        return (max(0, min(width - 1, int(round(float(position[0]))))), max(0, min(height - 1, int(round(float(position[1]))))))

    def _blocked_cells(
        self, snapshot: BodySnapshot, target_id: str, width: int, height: int,
        ignored_kinds: Optional[set[str]] = None, body: Optional[BodyState] = None,
    ) -> set[Cell]:
        blocked: set[Cell] = set()
        ignored_kinds = ignored_kinds or set()
        for item in snapshot.objects:
            kind = str(item.get("kind"))
            if str(item.get("id")) == target_id or kind not in self._BLOCKING_KINDS or kind in ignored_kinds:
                continue
            pos = item.get("position") or [0.0, 0.0]
            if self.geometry_mode == "continuous":
                body_radius = max(0.01, float((body.capabilities if body else {}).get("body_radius_m", 0.3)))
                object_radius = max(0.05, float(item.get("size", 0.5)) * 0.3)
                radius = body_radius + object_radius + 0.05
            else:
                radius = max(0.7, float(item.get("size", 0.5)) * 0.5 + 0.35)
            for x in range(width):
                for y in range(height):
                    if math.hypot(x - float(pos[0]), y - float(pos[1])) <= radius:
                        blocked.add((x, y))
        return blocked

    def _segment_clear(
        self,
        snapshot: BodySnapshot,
        body: BodyState,
        start: Cell,
        end: Cell,
        target_id: str,
    ) -> bool:
        """Validate a planner edge using continuous circle geometry."""
        if self.geometry_mode == "legacy_grid":
            return True
        sx, sy = float(start[0]), float(start[1])
        ex, ey = float(end[0]), float(end[1])
        length = math.hypot(ex - sx, ey - sy)
        samples = max(1, int(math.ceil(length / 0.1)))
        width = float(body.capabilities.get("world_width", 12.0))
        height = float(body.capabilities.get("world_height", 12.0))
        body_radius = max(0.01, float(body.capabilities.get("body_radius_m", 0.3)))
        margin = max(0.0, float(body.capabilities.get("contact_margin_m", 0.05)))
        for index in range(samples + 1):
            ratio = index / samples
            x, y = sx + (ex - sx) * ratio, sy + (ey - sy) * ratio
            if x < body_radius or y < body_radius or x > width - body_radius or y > height - body_radius:
                return False
            for item in snapshot.objects:
                kind = str(item.get("kind"))
                if str(item.get("id")) == target_id or kind not in self._BLOCKING_KINDS:
                    continue
                position = item.get("position") or [0.0, 0.0]
                object_radius = max(0.05, float(item.get("size", 0.5)) * 0.3)
                clearance = body_radius + object_radius + margin
                if math.hypot(float(position[0]) - x, float(position[1]) - y) < clearance:
                    return False
        return True

    @staticmethod
    def _goal_cells(
        target: Dict[str, Any], body: BodyState, width: int, height: int,
        blocked: set[Cell], reach: Optional[float] = None,
    ) -> set[Cell]:
        pos = target.get("position") or [0.0, 0.0]
        reach = max(0.75, float(body.capabilities.get("reach", 1.0) if reach is None else reach))
        goals = {
            (x, y) for x in range(width) for y in range(height)
            if (x, y) not in blocked and math.hypot(x - float(pos[0]), y - float(pos[1])) <= reach
        }
        return goals or {(int(round(float(pos[0]))), int(round(float(pos[1]))))}

    @staticmethod
    def _astar(start: Cell, goals: set[Cell], blocked: set[Cell], width: int, height: int) -> List[Cell]:
        frontier: list[tuple[float, int, Cell]] = [(0.0, 0, start)]
        parents: Dict[Cell, Optional[Cell]] = {start: None}
        cost: Dict[Cell, int] = {start: 0}
        sequence = 0
        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current in goals:
                path: List[Cell] = []
                while current is not None:
                    path.append(current)
                    current = parents[current]
                return list(reversed(path))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                candidate = (current[0] + dx, current[1] + dy)
                if not (0 <= candidate[0] < width and 0 <= candidate[1] < height) or candidate in blocked:
                    continue
                new_cost = cost[current] + 1
                if new_cost >= cost.get(candidate, 1 << 30):
                    continue
                cost[candidate] = new_cost
                parents[candidate] = current
                sequence += 1
                heuristic = min(abs(candidate[0] - goal[0]) + abs(candidate[1] - goal[1]) for goal in goals)
                heapq.heappush(frontier, (new_cost + heuristic, sequence, candidate))
        return []
