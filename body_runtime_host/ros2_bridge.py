"""Optional ROS 2 observation bridge for the independent Body runtime."""

from __future__ import annotations

import json
import math
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
        self._nav2_client = None
        self._nav2_lock = threading.Lock()
        self._mock_nav2_client = None
        self._mock_nav2_server = None
        self._mock_nav2_action = "/pandorabox/mock_navigate_to_pose"
        self._status = {"state": "stopped", "available": False, "last_error": ""}

    def status(self):
        with self._lock:
            result = dict(self._status)
            node = self._node
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
        nav2_packages_available = False
        try:
            from action_msgs.msg import GoalStatus as _GoalStatus  # noqa: F401
            from nav2_msgs.action import NavigateToPose as _NavigateToPose  # noqa: F401
            from geometry_msgs.msg import PoseStamped as _PoseStamped  # noqa: F401
            nav2_packages_available = True
        except Exception:
            pass
        action_server_available = False
        mock_action_server_available = False
        if nav2_packages_available and node is not None:
            try:
                actions = node.get_action_names_and_types()
                action_server_available = any(name.rstrip("/") == "/navigate_to_pose" and "nav2_msgs/action/NavigateToPose" in types for name, types in actions)
                mock_action_server_available = any(name.rstrip("/") == self._mock_nav2_action and "nav2_msgs/action/NavigateToPose" in types for name, types in actions)
            except Exception:
                action_server_available = False
                mock_action_server_available = False
        result["nav2_packages_available"] = nav2_packages_available
        # Keep the old field as a compatibility alias for package availability.
        result["nav2_action_available"] = nav2_packages_available
        result["nav2_server_available"] = action_server_available
        result["nav2_mock_server_available"] = mock_action_server_available
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
                try:
                    from nav2_msgs.action import NavigateToPose
                    from rclpy.action import ActionServer, CancelResponse, GoalResponse

                    self._mock_nav2_server = ActionServer(
                        node, NavigateToPose, self._mock_nav2_action,
                        execute_callback=self._execute_mock_nav2_goal,
                        goal_callback=lambda _request: GoalResponse.ACCEPT,
                        cancel_callback=lambda _goal: CancelResponse.ACCEPT,
                    )
                except Exception:
                    self._mock_nav2_server = None
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

    def navigate_to_pose(self, *, x: float, y: float, yaw: float, frame_id: str = "map", timeout: float = 120.0):
        """Send one explicitly requested Nav2 NavigateToPose action and await its result."""
        from action_msgs.msg import GoalStatus
        from geometry_msgs.msg import PoseStamped
        from nav2_msgs.action import NavigateToPose
        from rclpy.action import ActionClient

        with self._nav2_lock:
            with self._lock:
                node, executor = self._node, self._executor
            if node is None or executor is None or not self.status().get("available"):
                raise RuntimeError("ROS 2 bridge is not running")
            if self._nav2_client is None:
                self._nav2_client = ActionClient(node, NavigateToPose, "navigate_to_pose")
            client = self._nav2_client
            if not client.wait_for_server(timeout_sec=min(5.0, max(0.1, timeout))):
                raise RuntimeError("Nav2 NavigateToPose action server is unavailable")

            goal = NavigateToPose.Goal()
            goal.pose = PoseStamped()
            goal.pose.header.frame_id = frame_id
            goal.pose.header.stamp = node.get_clock().now().to_msg()
            goal.pose.pose.position.x = x
            goal.pose.pose.position.y = y
            goal.pose.pose.position.z = 0.0
            goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
            goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

            def await_future(future, wait_seconds, label):
                done = threading.Event()
                box = {}
                future.add_done_callback(lambda completed: (box.setdefault("value", completed), done.set()))
                if not done.wait(wait_seconds):
                    raise TimeoutError(f"timed out waiting for Nav2 {label}")
                return box["value"].result()

            goal_handle = await_future(client.send_goal_async(goal), min(10.0, timeout), "goal acceptance")
            if not goal_handle.accepted:
                raise RuntimeError("Nav2 rejected the navigation goal")
            try:
                result = await_future(goal_handle.get_result_async(), timeout, "result")
            except TimeoutError:
                goal_handle.cancel_goal_async()
                raise
            status = int(getattr(result, "status", -1))
            if status != GoalStatus.STATUS_SUCCEEDED:
                raise RuntimeError(f"Nav2 navigation ended with action status {status}")
            with self._lock:
                self._status["last_nav2_goal_at"] = time.time()
                self._status["nav2_goal_count"] = int(self._status.get("nav2_goal_count", 0)) + 1
            return {"status": "succeeded", "frame_id": frame_id, "x": x, "y": y, "yaw": yaw, "action_status": status}

    def _execute_mock_nav2_goal(self, goal_handle):
        from nav2_msgs.action import NavigateToPose

        result = NavigateToPose.Result()
        result.error_code = NavigateToPose.Result.NONE
        result.error_msg = "Simulation only: goal acknowledged; no robot motion"
        goal_handle.succeed()
        with self._lock:
            self._status["mock_nav2_goal_count"] = int(self._status.get("mock_nav2_goal_count", 0)) + 1
            self._status["last_mock_nav2_goal_at"] = time.time()
        return result

    def navigate_to_pose_mock(self, *, x: float, y: float, yaw: float, frame_id: str = "map", timeout: float = 10.0):
        """Exercise the ROS 2 NavigateToPose action protocol on a non-hardware mock endpoint."""
        from action_msgs.msg import GoalStatus
        from geometry_msgs.msg import PoseStamped
        from nav2_msgs.action import NavigateToPose
        from rclpy.action import ActionClient

        with self._nav2_lock:
            node, executor = self._node, self._executor
            if node is None or executor is None or not self.status().get("available"):
                raise RuntimeError("ROS 2 bridge is not running")
            if self._mock_nav2_client is None:
                self._mock_nav2_client = ActionClient(node, NavigateToPose, self._mock_nav2_action)
            client = self._mock_nav2_client
            if not client.wait_for_server(timeout_sec=min(3.0, max(0.1, timeout))):
                raise RuntimeError("PandoraBOX mock Nav2 action server is unavailable")
            goal = NavigateToPose.Goal()
            goal.pose = PoseStamped()
            goal.pose.header.frame_id = frame_id
            goal.pose.header.stamp = node.get_clock().now().to_msg()
            goal.pose.pose.position.x = x
            goal.pose.pose.position.y = y
            goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
            goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
            event = threading.Event()
            box = {}
            future = client.send_goal_async(goal)
            future.add_done_callback(lambda done: (box.setdefault("goal", done.result()), event.set()))
            if not event.wait(min(5.0, timeout)):
                raise TimeoutError("timed out waiting for mock Nav2 goal acceptance")
            handle = box["goal"]
            if not handle.accepted:
                raise RuntimeError("mock Nav2 action rejected goal")
            event.clear()
            future = handle.get_result_async()
            future.add_done_callback(lambda done: (box.setdefault("result", done.result()), event.set()))
            if not event.wait(timeout):
                handle.cancel_goal_async()
                raise TimeoutError("timed out waiting for mock Nav2 result")
            response = box["result"]
            if int(getattr(response, "status", -1)) != GoalStatus.STATUS_SUCCEEDED:
                raise RuntimeError(f"mock Nav2 action ended with status {response.status}")
            return {"status": "succeeded", "frame_id": frame_id, "x": x, "y": y,
                    "yaw": yaw, "action_status": int(response.status), "simulation_only": True}
    def stop(self):
        with self._lock:
            executor, node, context, rclpy = self._executor, self._node, self._context, self._rclpy
            self._executor = self._node = self._publisher = self._context = None
            self._thread = None
            self._nav2_client = None
            self._mock_nav2_client = None
            self._mock_nav2_server = None
            self._status.update(state="stopped", available=rclpy is not None)
        if executor is not None:
            executor.shutdown(timeout_sec=1.0)
        if node is not None:
            node.destroy_node()
        if context is not None and context.ok():
            context.shutdown()
