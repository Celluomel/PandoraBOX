"""Optional ROS 2 observation bridge for the independent Body runtime."""

from __future__ import annotations

import json
import os
import threading
import time
from importlib.metadata import PackageNotFoundError, version


class Ros2ObservationBridge:
    def __init__(self, on_observation, *, publish_topic="/body/observations", input_topic="/body/observations_in"):
        self.on_observation = on_observation
        self.publish_topic = publish_topic
        self.input_topic = input_topic
        self._lock = threading.RLock()
        self._node = None
        self._publisher = None
        self._executor = None
        self._thread = None
        self._rclpy = None
        self._context = None
        self._status = {"state": "stopped", "available": False, "last_error": ""}

    def status(self):
        with self._lock:
            result = dict(self._status)
        result.update({
            "ros_distro": os.environ.get("ROS_DISTRO", ""),
            "domain_id": os.environ.get("ROS_DOMAIN_ID", "0"),
            "publish_topic": self.publish_topic,
            "input_topic": self.input_topic,
            "physical_actuation": "not exposed by this bridge",
        })
        try:
            result["rclpy_version"] = version("rclpy")
        except PackageNotFoundError:
            result["rclpy_version"] = "system package not discoverable"
        return result

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self.status()
            try:
                import rclpy
                from rclpy.context import Context
                from rclpy.executors import SingleThreadedExecutor
                from std_msgs.msg import String
            except Exception as exc:
                self._status = {"state": "unavailable", "available": False, "last_error": str(exc)}
                return self.status()
            self._rclpy = rclpy
            try:
                context = Context()
                rclpy.init(args=None, context=context)
                node = rclpy.create_node("pandorabox_body_bridge", context=context)
                self._publisher = node.create_publisher(String, self.publish_topic, 10)
                node.create_subscription(String, self.input_topic, self._receive, 10)
                executor = SingleThreadedExecutor(context=context)
                executor.add_node(node)
                self._node, self._executor, self._context = node, executor, context
                self._status = {"state": "connected", "available": True, "last_error": "", "started_at": time.time()}
                self._thread = threading.Thread(target=self._spin, args=(executor,), name="body-ros2", daemon=True)
                self._thread.start()
            except Exception as exc:
                self._status = {"state": "error", "available": False, "last_error": str(exc)}
            return self.status()

    def _spin(self, executor):
        try:
            executor.spin()
        except Exception as exc:
            with self._lock:
                self._status.update(state="error", last_error=str(exc))
        finally:
            with self._lock:
                if self._status.get("state") == "connected":
                    self._status["state"] = "stopped"

    def _receive(self, message):
        try:
            payload = json.loads(message.data)
            if not isinstance(payload, dict):
                raise ValueError("expected a JSON object")
            observation = payload.get("observation", payload)
            if not isinstance(observation, dict) or not observation.get("subject"):
                raise ValueError("observation must contain a subject")
            self.on_observation(observation)
            with self._lock:
                self._status["last_input_at"] = time.time()
                self._status["input_count"] = int(self._status.get("input_count", 0)) + 1
        except Exception as exc:
            with self._lock:
                self._status["last_error"] = f"Rejected ROS observation: {exc}"

    def publish(self, observation):
        with self._lock:
            publisher, node = self._publisher, self._node
        if publisher is None or node is None:
            return False
        try:
            from std_msgs.msg import String
            message = String()
            message.data = json.dumps({"schema": "pandorabox.body_observation.v1", "observation": observation}, ensure_ascii=False, default=str)
            publisher.publish(message)
            with self._lock:
                self._status["last_output_at"] = time.time()
                self._status["output_count"] = int(self._status.get("output_count", 0)) + 1
            return True
        except Exception as exc:
            with self._lock:
                self._status["last_error"] = str(exc)
            return False

    def stop(self):
        with self._lock:
            executor, node, context, rclpy = self._executor, self._node, self._context, self._rclpy
            self._executor = self._node = self._publisher = self._context = None
            self._thread = None
            self._status.update(state="stopped", available=rclpy is not None)
        if executor is not None:
            executor.shutdown(timeout_sec=1.0)
        if node is not None:
            node.destroy_node()
        if context is not None and context.ok():
            context.shutdown()
