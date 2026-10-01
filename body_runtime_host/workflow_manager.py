"""Persistent, manually-triggered Body workflows with an explicit node allowlist."""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class WorkflowError(ValueError):
    pass


class WorkflowManager:
    STARTER_WORKFLOW = {
        "name": "Body sensorimotor pipeline",
        "nodes": [
            {"id": "camera", "type": "camera", "x": 28, "y": 76},
            {"id": "lidar", "type": "lidar", "x": 28, "y": 238},
            {"id": "imu", "type": "imu", "x": 28, "y": 400},
            {"id": "perception", "type": "perception", "x": 258, "y": 238},
            {"id": "fusion", "type": "fusion", "x": 488, "y": 238},
            {"id": "world", "type": "world", "x": 718, "y": 238},
            {"id": "safety", "type": "safety", "x": 948, "y": 238},
            {"id": "brain", "type": "brain", "x": 1178, "y": 238},
        ],
        "edges": [
            ["camera", "perception"], ["lidar", "perception"], ["imu", "perception"],
            ["perception", "fusion"], ["fusion", "world"], ["world", "safety"],
            ["safety", "brain"],
        ],
    }

    NODE_TYPES = {
        "camera", "lidar", "imu", "ros2_in", "perception", "fusion",
        "world", "safety", "brain", "ros2_out", "fnk",
        "sim_base_navigate", "frame_guard", "sim_arm_action",
    }
    NODE_CONTRACTS = {
        "camera": {"group": "Input", "output": "camera_frame"},
        "lidar": {"group": "Input", "output": "observation"},
        "imu": {"group": "Input", "output": "observation"},
        "ros2_in": {"group": "Input", "output": "observation"},
        "perception": {"group": "Process", "input": "any", "output": "perception_frame"},
        "fusion": {"group": "Process", "input": "any", "output": "fused_scene"},
        "world": {"group": "Process", "input": "any", "output": "world_state"},
        "safety": {"group": "Process", "input": "any", "output": "safety_decision"},
        "brain": {"group": "Output", "input": "any", "output": "ack"},
        "ros2_out": {"group": "Output", "input": "any", "output": "ack"},
        "fnk": {"group": "Output", "input": "any", "output": "ack"},
        "sim_base_navigate": {"group": "Robot · simulation", "input": "any", "output": "pose"},
        "frame_guard": {"group": "Robot · simulation", "input": "pose", "output": "safe_pose"},
        "sim_arm_action": {"group": "Robot · simulation", "input": "safe_pose", "output": "task_result"},
    }

    MOBILE_MANIPULATION_DEMO = {
        "name": "Coordinated base + arm (simulation)",
        "nodes": [
            {"id": "approach", "type": "sim_base_navigate", "label": "Base · approach object", "x": 90, "y": 160,
             "config": {"device_id": "sim_mobile_base", "frame_id": "map", "x": 2.0, "y": 2.0, "heading_deg": 0}},
            {"id": "shared_frame", "type": "frame_guard", "label": "Check shared frame & reach", "x": 410, "y": 160,
             "config": {"frame_id": "map", "object_id": "demo_object", "x": 2.45, "y": 2.1, "z": 0.4, "max_reach_m": 0.75}},
            {"id": "manipulate", "type": "sim_arm_action", "label": "Arm · grasp target", "x": 730, "y": 160,
             "config": {"device_id": "sim_manipulator", "action": "grasp", "object_id": "demo_object", "frame_id": "map"}},
        ],
        "edges": [["approach", "shared_frame"], ["shared_frame", "manipulate"]],
    }

    def __init__(self, host, path: Path):
        self.host = host
        self.path = path
        self._lock = threading.RLock()
        self._workflows: dict[str, dict[str, Any]] = {}
        self._load()

    def catalog(self) -> dict[str, Any]:
        """Describe executable node contracts and distinguish real from simulated devices."""
        try:
            robot = self.host.robot_status()
            settings = self.host.fnk0031_settings()
        except Exception:
            robot, settings = {}, {}
        return {
            "schema": "pandorabox.workflow_catalog.v1",
            "nodes": [
                {"type": node_type, **contract}
                for node_type, contract in self.NODE_CONTRACTS.items()
            ],
            "devices": [
                {
                    "id": "fnk0031",
                    "label": "FNK0031 hexapod",
                    "kind": "mobile_base",
                    "mode": "hardware",
                    "state": "connected" if robot.get("last_ok") else "configured" if settings.get("url") else "not_configured",
                    "actuation": "confirmation_gated" if settings.get("actuation_enabled") else "disabled",
                    "capabilities": ["locomotion", "body_pose", "camera_input"],
                    "transport": "FNK0031 gateway",
                },
                {
                    "id": "sim_mobile_base",
                    "label": "Virtual mobile base",
                    "kind": "mobile_base",
                    "mode": "simulation",
                    "state": "available",
                    "frame_id": "map",
                    "capabilities": ["navigate_to_pose"],
                },
                {
                    "id": "sim_manipulator",
                    "label": "Virtual manipulator",
                    "kind": "manipulator",
                    "mode": "simulation",
                    "state": "available",
                    "frame_id": "map",
                    "capabilities": ["reach", "grasp", "release"],
                },
            ],
            "physical_actuation_enabled": False,
        }

    @classmethod
    def mobile_manipulation_demo(cls) -> dict[str, Any]:
        return json.loads(json.dumps(cls.MOBILE_MANIPULATION_DEMO))

    def _load(self) -> None:
        if not self.path.exists():
            self._workflows = {}
            self.save(self.STARTER_WORKFLOW)
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            rows = payload.get("workflows", []) if isinstance(payload, dict) else []
            self._workflows = {str(row["id"]): row for row in rows if isinstance(row, dict) and row.get("id")}
        except (OSError, ValueError, TypeError):
            self._workflows = {}

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"schema": "pandorabox.body_workflows.v1", "workflows": list(self._workflows.values())}, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)

    @classmethod
    def validate(cls, nodes: Any, edges: Any) -> dict[str, Any]:
        if not isinstance(nodes, list) or not 1 <= len(nodes) <= 40:
            raise WorkflowError("workflow must contain between 1 and 40 nodes")
        if not isinstance(edges, list) or len(edges) > 100:
            raise WorkflowError("workflow must contain at most 100 connections")
        ids: list[str] = []
        for node in nodes:
            if not isinstance(node, dict):
                raise WorkflowError("each node must be an object")
            node_id, node_type = str(node.get("id") or ""), str(node.get("type") or "")
            if not node_id or len(node_id) > 100 or node_id in ids:
                raise WorkflowError("node ids must be unique, non-empty strings")
            if node_type not in cls.NODE_TYPES:
                raise WorkflowError(f"unsupported workflow node type: {node_type}")
            if not isinstance(node.get("config", {}), dict):
                raise WorkflowError(f"node {node_id} config must be an object")
            ids.append(node_id)
        indegree = dict.fromkeys(ids, 0)
        adjacency = {node_id: [] for node_id in ids}
        normalized_edges = []
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 2:
                raise WorkflowError("connections must be [source_id, target_id] pairs")
            source, target = map(str, edge)
            if source not in indegree or target not in indegree or source == target:
                raise WorkflowError("connection references an unknown node or a self-loop")
            if [source, target] not in normalized_edges:
                source_type = next(node["type"] for node in nodes if node["id"] == source)
                target_type = next(node["type"] for node in nodes if node["id"] == target)
                expected = cls.NODE_CONTRACTS[target_type].get("input", "any")
                produced = cls.NODE_CONTRACTS[source_type].get("output", "any")
                if expected != "any" and produced != expected:
                    raise WorkflowError(
                        f"incompatible connection {source} ({produced}) -> {target} (expects {expected})"
                    )
                normalized_edges.append([source, target])
                adjacency[source].append(target)
                indegree[target] += 1
        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        order = []
        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            for target in adjacency[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if len(order) != len(ids):
            raise WorkflowError("workflow connections must be acyclic")
        return {"order": order, "edges": normalized_edges}

    def list(self) -> dict[str, Any]:
        with self._lock:
            rows = sorted(self._workflows.values(), key=lambda row: row.get("updated_at", 0), reverse=True)
            return {"workflows": [self._summary(row) for row in rows]}

    @staticmethod
    def _summary(row: dict) -> dict:
        return {key: row.get(key) for key in ("id", "name", "updated_at", "created_at", "revision", "active", "nodes", "edges", "last_execution")}

    def get(self, workflow_id: str) -> dict[str, Any]:
        with self._lock:
            row = self._workflows.get(workflow_id)
            if row is None:
                raise KeyError(workflow_id)
            return dict(row)

    def save(self, payload: dict) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise WorkflowError("workflow payload must be an object")
        workflow = payload.get("workflow", payload)
        if not isinstance(workflow, dict):
            raise WorkflowError("workflow payload must contain a workflow object")
        graph = self.validate(workflow.get("nodes"), workflow.get("edges"))
        now = time.time()
        workflow_id = str(workflow.get("id") or uuid.uuid4().hex)
        if len(workflow_id) > 100:
            raise WorkflowError("workflow id is too long")
        name = str(workflow.get("name") or "Untitled workflow").strip()[:120] or "Untitled workflow"
        with self._lock:
            previous = self._workflows.get(workflow_id, {})
            row = {
                "schema": "pandorabox.body_workflow.v1", "id": workflow_id,
                "name": name, "nodes": workflow["nodes"], "edges": graph["edges"],
                "created_at": previous.get("created_at", now), "updated_at": now,
                "revision": int(previous.get("revision", 0)) + 1,
                "active": bool(previous.get("active", False)),
                "executions": previous.get("executions", [])[-50:],
                "last_execution": previous.get("last_execution"),
            }
            self._workflows[workflow_id] = row
            self._persist()
            return dict(row)

    def delete(self, workflow_id: str) -> bool:
        with self._lock:
            if workflow_id not in self._workflows:
                return False
            del self._workflows[workflow_id]
            self._persist()
            return True

    def executions(self, workflow_id: str) -> dict[str, Any]:
        row = self.get(workflow_id)
        return {"workflow_id": workflow_id, "executions": list(row.get("executions", []))}

    def execute(self, workflow_id: str) -> dict[str, Any]:
        with self._lock:
            row = self._workflows.get(workflow_id)
            if row is None:
                raise KeyError(workflow_id)
            row = dict(row)
        graph = self.validate(row["nodes"], row["edges"])
        node_by_id = {node["id"]: node for node in row["nodes"]}
        if any(node["type"] == "fnk" for node in row["nodes"]):
            raise WorkflowError("workflow contains FNK physical actuation, which is not available in this executor; no nodes were run")
        if any(node["type"] == "ros2_out" for node in row["nodes"]):
            bridge = self.host._ros2_bridge
            if bridge is None or not bridge.status().get("available"):
                raise WorkflowError("workflow requires an available ROS 2 bridge; no nodes were run")
        incoming: dict[str, list[str]] = {node_id: [] for node_id in node_by_id}
        for source, target in graph["edges"]:
            incoming[target].append(source)
        simulated = any(node["type"].startswith("sim_") or node["type"] == "frame_guard" for node in row["nodes"])
        run = {"id": uuid.uuid4().hex, "workflow_id": workflow_id, "started_at": time.time(), "status": "running", "execution_mode": "simulation" if simulated else "body_dataflow", "nodes": [], "error": ""}
        values: dict[str, Any] = {}
        try:
            for node_id in graph["order"]:
                node = node_by_id[node_id]
                node_type = node["type"]
                inputs = [values[parent] for parent in incoming[node_id] if parent in values]
                result = self._execute_node(node_type, inputs, node.get("config") or {})
                values[node_id] = result
                run["nodes"].append({"id": node_id, "type": node_type, "label": node.get("label") or node_type, "status": "success", "output": self._compact(result)})
            run["status"] = "completed"
        except Exception as exc:
            run["status"] = "failed"
            run["error"] = str(exc)[:400]
            failed_id = node_id if "node_id" in locals() else ""
            run["nodes"].append({"id": failed_id, "type": node_by_id.get(failed_id, {}).get("type", ""), "status": "failed", "error": run["error"]})
        run["finished_at"] = time.time()
        run["duration_ms"] = round((run["finished_at"] - run["started_at"]) * 1000, 1)
        with self._lock:
            saved = self._workflows.get(workflow_id)
            if saved is not None:
                saved["last_execution"] = run
                saved.setdefault("executions", []).append(run)
                saved["executions"] = saved["executions"][-50:]
                self._persist()
        return run

    def _execute_node(self, node_type: str, inputs: list[Any], config: dict[str, Any] | None = None) -> Any:
        config = config or {}
        if node_type == "sim_base_navigate":
            target = self._pose_from_config(config)
            return {
                "kind": "pose", "device_id": "sim_mobile_base", "frame_id": target["frame_id"],
                "position": target["position"], "heading_deg": target["heading_deg"],
                "mode": "simulation", "actuation": False,
                "reason": "Virtual navigation result; no Body map or hardware was moved.",
            }
        if node_type == "frame_guard":
            base = next((item for item in reversed(inputs) if isinstance(item, dict) and item.get("kind") == "pose"), None)
            if base is None:
                raise WorkflowError("frame guard requires a mobile-base pose input")
            target = self._pose_from_config(config)
            if base.get("frame_id") != target["frame_id"]:
                raise WorkflowError(f"coordinate frame mismatch: base={base.get('frame_id')} target={target['frame_id']}")
            base_position, target_position = base["position"], target["position"]
            distance = sum((base_position[index] - target_position[index]) ** 2 for index in range(3)) ** 0.5
            limit = self._bounded_number(config.get("max_reach_m", 0.75), "max_reach_m", 0.05, 5.0)
            if distance > limit:
                raise WorkflowError(f"arm target is out of reach ({distance:.3f} m > {limit:.3f} m)")
            return {
                "kind": "safe_pose", "frame_id": target["frame_id"], "base_pose": base_position,
                "target_pose": target_position, "distance_m": round(distance, 4),
                "reach_limit_m": limit, "safe": True, "mode": "simulation",
            }
        if node_type == "sim_arm_action":
            checked = next((item for item in reversed(inputs) if isinstance(item, dict) and item.get("kind") == "safe_pose"), None)
            if checked is None or not checked.get("safe"):
                raise WorkflowError("simulated arm requires a passing frame/reach guard")
            if config.get("frame_id", checked.get("frame_id")) != checked.get("frame_id"):
                raise WorkflowError("arm and shared target coordinate frames do not match")
            action = str(config.get("action", "grasp")).strip().lower()
            if action not in {"reach", "grasp", "release"}:
                raise WorkflowError("simulated arm action must be reach, grasp or release")
            return {
                "kind": "task_result", "device_id": "sim_manipulator", "action": action,
                "object_id": str(config.get("object_id") or "target"), "status": "simulated_success",
                "frame_id": checked["frame_id"], "target_pose": checked["target_pose"],
                "mode": "simulation", "actuation": False,
            }
        if node_type == "camera":
            frame = self.host.camera_frame()
            camera = frame.get("camera") or {}
            return {"available": bool(frame.get("available")), "source": camera.get("source"), "timestamp": camera.get("timestamp"), "width": camera.get("width"), "height": camera.get("height"), "status": frame.get("status")}
        if node_type in {"lidar", "imu", "ros2_in"}:
            kinds = {"lidar": {"lidar", "range", "point_cloud"}, "imu": {"imu", "odometry", "localization"}, "ros2_in": set()}[node_type]
            rows = [entry for entry in self.host.latest.values() if (str(entry.get("source", "")).startswith("ros2") if node_type == "ros2_in" else str(entry.get("kind", "")).lower() in kinds)]
            rows.sort(key=lambda entry: float(entry.get("observed_at") or 0), reverse=True)
            return {"available": bool(rows), "count": len(rows), "observations": rows[:20]}
        if node_type == "perception":
            wm = self.host.worldmodel
            if wm is None:
                raise WorkflowError("world model is unavailable")
            return wm.status_summary().get("perception") or {"available": False}
        if node_type == "fusion":
            wm = self.host.worldmodel
            if wm is None:
                raise WorkflowError("world model is unavailable")
            perception = wm.status_summary().get("perception") or {}
            return {"contract": perception.get("contract"), "objects": perception.get("objects", []), "associations": perception.get("associations", []), "sensor_projections": perception.get("sensor_projections", {}), "quality": perception.get("quality", {})}
        if node_type == "world":
            wm = self.host.worldmodel
            if wm is None:
                raise WorkflowError("world model is unavailable")
            return wm.context_for_brain()
        if node_type == "safety":
            wm = self.host.worldmodel
            status = wm.status_summary() if wm is not None else {}
            alert = status.get("navigation_alert")
            return {"state": "blocked" if alert else "clear", "navigation_alert": alert, "note": "Reports Body navigation safety state; this node does not authorize physical actuation."}
        upstream = inputs[-1] if inputs else {}
        if node_type == "brain":
            observation = {"entity_id": f"body.workflow.{int(time.time() * 1000)}", "source": "body_workflow", "kind": "workflow_result", "subject": "workflow observation", "value": upstream, "unit": "", "confidence": 1.0, "observed_at": time.time(), "provenance": {"transport": "body_bridge"}}
            self.host._bridge_put(observation)
            return {"accepted": True, "destination": "Brain observation bridge"}
        if node_type == "ros2_out":
            bridge = self.host._ros2_bridge
            if bridge is None or not bridge.status().get("available"):
                raise WorkflowError("ROS 2 observation bridge is not available")
            observation = {"entity_id": f"body.workflow.{int(time.time() * 1000)}", "source": "body_workflow", "kind": "workflow_result", "subject": "workflow observation", "value": upstream, "unit": "", "confidence": 1.0, "observed_at": time.time(), "provenance": {"transport": "ros2"}}
            if not bridge.publish(observation):
                raise WorkflowError("ROS 2 observation publish failed")
            return {"accepted": True, "destination": "ROS 2 observation topic"}
        if node_type == "fnk":
            raise WorkflowError("FNK physical actuation is not an executable workflow node; use the confirmation-gated Body command path")
        raise WorkflowError(f"node type has no execution handler: {node_type}")

    @staticmethod
    def _bounded_number(value: Any, field: str, minimum: float, maximum: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise WorkflowError(f"{field} must be a number") from None
        if not minimum <= number <= maximum:
            raise WorkflowError(f"{field} must be between {minimum} and {maximum}")
        return number

    @classmethod
    def _pose_from_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        frame_id = str(config.get("frame_id") or "map").strip()
        if not frame_id or len(frame_id) > 100:
            raise WorkflowError("frame_id must be a non-empty string")
        position = [
            cls._bounded_number(config.get("x", 0), "x", -100.0, 100.0),
            cls._bounded_number(config.get("y", 0), "y", -100.0, 100.0),
            cls._bounded_number(config.get("z", 0), "z", -10.0, 10.0),
        ]
        heading = cls._bounded_number(config.get("heading_deg", 0), "heading_deg", -3600.0, 3600.0)
        return {"frame_id": frame_id, "position": position, "heading_deg": heading}

    @classmethod
    def _compact(cls, value: Any, depth: int = 0) -> Any:
        if depth > 5:
            return "…"
        if isinstance(value, dict):
            return {str(key): cls._compact(item, depth + 1) for key, item in list(value.items())[:80] if "base64" not in str(key).lower() and "jpeg" not in str(key).lower()}
        if isinstance(value, (list, tuple)):
            return [cls._compact(item, depth + 1) for item in value[:30]]
        if isinstance(value, str) and len(value) > 1000:
            return value[:1000] + "…"
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)[:1000]
