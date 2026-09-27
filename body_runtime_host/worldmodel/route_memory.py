"""Persistent metric/topological route memory owned by the Body."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional


class RouteMemory:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                value.setdefault("version", 1)
                value.setdefault("routes", [])
                value.setdefault("flags", {})
                return value
        except Exception:
            pass
        return {"version": 1, "routes": [], "flags": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    @staticmethod
    def _distance(a: List[float], b: List[float]) -> float:
        return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))

    def record(self, body: Dict[str, Any], objects: List[Dict[str, Any]], *, frame_id: str = "") -> None:
        """Record a waypoint only after meaningful movement or rotation."""
        position = list(body.get("position") or [0.0, 0.0, 0.0])[:3]
        while len(position) < 3:
            position.append(0.0)
        pose = {
            "position": position,
            "yaw": float(body.get("orientation", 0.0) or 0.0),
            "coordinate_frame": str(body.get("coordinate_frame") or "local_map"),
            "position_source": str(body.get("position_source") or "odometry"),
            "position_accuracy_m": body.get("position_accuracy_m"),
            "geo": dict(body.get("geo") or {}),
        }
        now = time.time()
        with self._lock:
            routes = self._data.setdefault("routes", [])
            route = routes[-1] if routes else None
            if route is None or route.get("closed"):
                route = {"route_id": f"route-{int(now * 1000)}", "started_at": now, "closed": False,
                         "start": pose, "origin": dict(pose), "distance": 0.0, "waypoints": []}
                routes.append(route)
            waypoints = route.setdefault("waypoints", [])
            previous = waypoints[-1] if waypoints else None
            moved = self._distance(previous["position"], position) if previous else 999.0
            yaw_delta = abs(((pose["yaw"] - float(previous.get("yaw", 0.0)) + math.pi) % (2 * math.pi)) - math.pi) if previous else 999.0
            if previous and moved < 0.25 and yaw_delta < math.radians(15):
                return
            cumulative = float(route.get("distance", 0.0)) + (moved if previous else 0.0)
            waypoint = {**pose, "index": len(waypoints), "distance": round(cumulative, 3),
                        "timestamp": now, "frame_id": frame_id}
            waypoints.append(waypoint)
            route["distance"] = round(cumulative, 3)
            route["updated_at"] = now
            for item in objects[:32]:
                object_id = str(item.get("id") or "")
                if not object_id or not item.get("position"):
                    continue
                self._data.setdefault("flags", {})[object_id] = {
                    "id": object_id, "label": item.get("label") or object_id,
                    "kind": item.get("kind") or "object", "position": list(item["position"]),
                    "last_seen": now, "frame_id": frame_id,
                    "coordinate_frame": item.get("coordinate_frame") or pose["coordinate_frame"],
                    "position_source": item.get("position_source") or "perception",
                    "position_accuracy_m": item.get("position_accuracy_m"),
                    "geo": dict(item.get("geo") or {}),
                }
            self._data["routes"] = routes[-32:]
            self._save()

    def close_current(self) -> None:
        with self._lock:
            if self._data.get("routes"):
                self._data["routes"][-1]["closed"] = True
                self._data["routes"][-1]["closed_at"] = time.time()
                self._save()

    def route_to(self, target: str) -> Dict[str, Any]:
        with self._lock:
            flags = self._data.get("flags", {})
            target_flag = flags.get(str(target))
            routes = self._data.get("routes", [])
            if not target_flag or not routes:
                return {"available": False, "target": target, "reason": "target flag or route unavailable"}
            route = routes[-1]
            waypoints = route.get("waypoints", [])
            if not waypoints:
                return {"available": False, "target": target, "reason": "route has no waypoints"}
            end = min(waypoints, key=lambda item: self._distance(item["position"], target_flag["position"]))
            return {"available": True, "target": target, "flag": target_flag,
                    "route_id": route.get("route_id"), "waypoints": waypoints[:int(end["index"]) + 1],
                    "distance": end.get("distance", 0.0), "mode": "replayable_metric_route"}

    def route_to_start(self) -> Dict[str, Any]:
        with self._lock:
            routes = self._data.get("routes", [])
            if not routes or not routes[-1].get("waypoints"):
                return {"available": False, "reason": "no recorded route"}
            route = routes[-1]
            return {"available": True, "route_id": route.get("route_id"),
                    "waypoints": list(reversed(route.get("waypoints", []))),
                    "distance": route.get("distance", 0.0), "mode": "return_to_start"}

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            routes = self._data.get("routes", [])
            current = routes[-1] if routes else None
            return {"version": 1, "current": current, "routes": len(routes),
                    "flags": list(self._data.get("flags", {}).values()),
                    "waypoints": len((current or {}).get("waypoints", [])),
                    "distance": float((current or {}).get("distance", 0.0) or 0.0),
                    "coordinate_frame": ((current or {}).get("start") or {}).get("coordinate_frame", "local_map"),
                    "position_source": ((current or {}).get("start") or {}).get("position_source", "odometry"),
                    "position_accuracy_m": ((current or {}).get("start") or {}).get("position_accuracy_m"),
                    "origin": (current or {}).get("origin") or (current or {}).get("start") or {},
                    "coordinate_contract": "body_spatial_fix.v1"}
