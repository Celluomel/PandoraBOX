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

    _BLOCKING_KINDS = {"obstacle", "chair", "table", "wall", "mobile_obstacle"}

    def __init__(self) -> None:
        self._scene_signatures: Dict[str, tuple] = {}

    def route(self, target_id: str, snapshot: BodySnapshot, body: BodyState, reach: Optional[float] = None) -> Route:
        target = next((item for item in snapshot.objects if str(item.get("id")) == target_id), None)
        if target is None:
            return Route(target_id, reason="unknown_target", blocked=True)
        width = max(2, int(round(float(body.capabilities.get("world_width", 12)))))
        height = max(2, int(round(float(body.capabilities.get("world_height", 12)))))
        start = self._cell(body.position, width, height)
        blocked = self._blocked_cells(snapshot, target_id, width, height)
        signature = tuple(sorted((str(item.get("id")), tuple(round(float(v), 1) for v in (item.get("position") or [])[:2])) for item in snapshot.objects))
        replanned = target_id in self._scene_signatures and self._scene_signatures[target_id] != signature
        self._scene_signatures[target_id] = signature
        goals = self._goal_cells(target, body, width, height, blocked, reach=reach)
        if start in goals:
            return Route(target_id, [start], "already_near_target", replanned=replanned)
        path = self._astar(start, goals, blocked, width, height)
        if not path:
            return Route(target_id, reason="recover_from_blockage", blocked=True, replanned=replanned)
        direct = abs(start[0] - path[-1][0]) + abs(start[1] - path[-1][1])
        reason = "replan_after_scene_change" if replanned else "avoid_obstacle" if len(path) - 1 > direct else "toward_target"
        return Route(target_id, path, reason, replanned=replanned)

    @staticmethod
    def _cell(position: List[float], width: int, height: int) -> Cell:
        return (max(0, min(width - 1, int(round(float(position[0]))))), max(0, min(height - 1, int(round(float(position[1]))))))

    def _blocked_cells(self, snapshot: BodySnapshot, target_id: str, width: int, height: int) -> set[Cell]:
        blocked: set[Cell] = set()
        for item in snapshot.objects:
            if str(item.get("id")) == target_id or str(item.get("kind")) not in self._BLOCKING_KINDS:
                continue
            pos = item.get("position") or [0.0, 0.0]
            radius = max(0.7, float(item.get("size", 0.5)) * 0.5 + 0.35)
            for x in range(width):
                for y in range(height):
                    if math.hypot(x - float(pos[0]), y - float(pos[1])) <= radius:
                        blocked.add((x, y))
        return blocked

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
