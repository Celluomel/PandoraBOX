"""Optional ROS 2 observation bridge for the independent Body runtime."""

from __future__ import annotations

import json
import math
import os
import threading
import time
from importlib.metadata import PackageNotFoundError, version

DEFAULT_SENSOR_TOPICS = {
    "imu": "/imu/data",
    "gps": "/gps/fix",
    "lidar": "/scan",
    "odometry": "/odom",
    "range": "/range/front",
}

BODY_SENSOR_PUBLISH_TOPICS = {
    "imu": "/body/sensors/imu",
    "gps": "/body/sensors/gps/fix",
    "tof": "/body/sensors/tof/front",
    "ultrasonic_front_left": "/body/sensors/ultrasonic/front_left",
    "ultrasonic_front_right": "/body/sensors/ultrasonic/front_right",
    "ultrasonic_rear": "/body/sensors/ultrasonic/rear",
    "mmwave_targets": "/body/sensors/mmwave/targets",
}


class Ros2ObservationBridge:
    def __init__(self, on_observation, *, publish_topic="/body/observations",
                 input_topic="/body/observations_in", nav2_simulation_enabled=False,
                 sensor_topics=None):
        self.on_observation = on_observation
        self.publish_topic = publish_topic
        self.input_topic = input_topic
        self.sensor_topics = {**DEFAULT_SENSOR_TOPICS, **(sensor_topics or {})}
        self._lock = threading.RLock()
        self._node = None
        self._publisher = None
        self._body_sensor_publishers = {}
        self._body_sensor_status = {}
        self._sensor_subscriptions = []
        self._sensor_status = {}
        self._executor = None
        self._thread = None
        self._rclpy = None
        self._context = None
        self._nav2_client = None
        self._nav2_lock = threading.Lock()
        self._mock_nav2_client = None
        self._mock_nav2_server = None
        self._mock_nav2_action = "/pandorabox/mock_navigate_to_pose"
        self._nav2_simulation_enabled = bool(nav2_simulation_enabled)
        self._nav2_simulation = None
        self._status = {"state": "stopped", "available": False, "last_error": ""}

    def status(self):
        with self._lock:
            result = dict(self._status)
            node = self._node
            sensor_status = {key: dict(value) for key, value in self._sensor_status.items()}
            body_sensor_status = {key: dict(value) for key, value in self._body_sensor_status.items()}
        result.update({
            "ros_distro": os.environ.get("ROS_DISTRO", ""),
            "domain_id": os.environ.get("ROS_DOMAIN_ID", "0"),
            "publish_topic": self.publish_topic,
            "input_topic": self.input_topic,
            "sensor_topics": dict(self.sensor_topics),
            "sensor_subscriptions": sensor_status,
            "physical_actuation": "not exposed by this bridge",
            "body_sensor_publish_topics": dict(BODY_SENSOR_PUBLISH_TOPICS),
            "body_sensor_publishers": body_sensor_status,
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
        graph = {"topics": {}, "services": []}
        if nav2_packages_available and node is not None:
            try:
                services = node.get_service_names_and_types()
                graph["services"] = [name for name, _types in services]
                expected_type = "nav2_msgs/action/NavigateToPose_SendGoal"
                action_server_available = any(
                    name.rstrip("/").endswith("/navigate_to_pose/_action/send_goal")
                    and expected_type in types
                    for name, types in services
                )
                mock_action_server_available = any(
                    name.rstrip("/") == f"{self._mock_nav2_action}/_action/send_goal"
                    and expected_type in types
                    for name, types in services
                )
            except Exception:
                action_server_available = False
                mock_action_server_available = False
        if node is not None:
            try:
                graph["topics"] = {
                    name: types for name, types in node.get_topic_names_and_types()
                }
            except Exception:
                graph["topics"] = {}
        simulation_status = self._nav2_simulation.status() if self._nav2_simulation else {
            "enabled": False, "simulation_only": True,
            "note": "Enable the Nav2 simulation in Body ROS 2 settings.",
        }
        simulation_status.update(self._cmd_vel_isolation(node))
        result["nav2_packages_available"] = nav2_packages_available
        # Keep the old field as a compatibility alias for package availability.
        result["nav2_action_available"] = nav2_packages_available
        result["nav2_server_available"] = action_server_available
        result["nav2_mock_server_available"] = mock_action_server_available
        result["nav2_preflight"] = self._nav2_preflight(
            nav2_packages_available, action_server_available, graph["topics"], graph["services"]
        )
        result["physical_nav2_preflight"] = self._physical_nav2_preflight(body_sensor_status)
        result["nav2_simulation"] = simulation_status
        return result

    @staticmethod
    def _physical_nav2_preflight(sensor_publishers=None):
        """Describe repository-level hardware blockers without implying ROS graph readiness is physical readiness."""
        sensor_publishers = sensor_publishers or {}
        blockers = [
            "Typed outputs follow the world-model sampling cadence (default 2 s), not a validated control-rate stream",
            "Available HC-SR04 and LD2450 coverage is not a 360-degree navigation costmap source",
            "Stock and opt-in custom FNHR profiles expose blocking gait actions, not continuous cmd_vel control",
            "FNK0031 stock firmware reports no planar pose or odometry",
            "No physical map/localization/robot-TF bringup is configured in this repository",
            "No physical-motion safety controller or independent emergency stop is integrated here",
        ]
        required_sensor_streams = ("imu", "ultrasonic_front_left", "ultrasonic_front_right", "ultrasonic_rear")
        sensor_streams = {}
        for key in required_sensor_streams:
            state = dict(sensor_publishers.get(key, {}))
            age = time.time() - float(state.get("last_published_at") or 0.0)
            state["fresh"] = bool(state.get("last_published_at") and age <= 3.0)
            sensor_streams[key] = state
            if not state["fresh"]:
                blockers.append(f"physical sensor stream has not published a fresh {key} sample")
        return {
            "ready": False,
            "simulation_only": True,
            "hardware_actuation_enabled": False,
            "robot_profile": "Freenove FNK0031 hexapod / Crawling Robot Controller V3.2",
            "sensor_platform": "Body and robot are one co-mounted physical platform; Body sensors are robot sensors",
            "blockers": blockers,
            "sensor_streams": sensor_streams,
            "required_before_physical_test": [
                "calibrated, timestamped planar odometry with a validated map->odom->base_link TF chain",
                "typed, timestamped physical obstacle data with verified frame IDs and sensor QoS",
                "a continuous velocity/gait adapter with watchdog, bounds, stop behavior, and measured feedback",
                "independent emergency stop and a bounded, low-speed test procedure",
            ],
        }

    def visualization(self):
        with self._lock:
            simulation = self._nav2_simulation
        if simulation is None:
            return {"available": False, "source": "none", "simulation_only": True,
                    "reason": "Synthetic Nav2 inputs are not running; no live ROS map is available."}
        return simulation.visualization()

    @staticmethod
    def _cmd_vel_isolation(node):
        """Fail closed if anything besides this synthetic base consumes /cmd_vel."""
        if node is None:
            return {"cmd_vel_hardware_isolated": False, "cmd_vel_subscribers": []}
        try:
            endpoints = node.get_subscriptions_info_by_topic("/cmd_vel")
            subscribers = [
                {
                    "node": str(getattr(endpoint, "node_name", "")),
                    "namespace": str(getattr(endpoint, "node_namespace", "")),
                    "type": str(getattr(endpoint, "topic_type", "")),
                }
                for endpoint in endpoints
            ]
            own_node = str(node.get_name())
            isolated = len(subscribers) == 1 and subscribers[0]["node"] == own_node
            return {
                "cmd_vel_hardware_isolated": isolated,
                "cmd_vel_subscribers": subscribers,
            }
        except Exception as exc:
            return {
                "cmd_vel_hardware_isolated": False,
                "cmd_vel_subscribers": [],
                "cmd_vel_isolation_error": str(exc)[:180],
            }

    @staticmethod
    def _nav2_preflight(packages_available, action_server_available, topics, services):
        """Report graph prerequisites without treating package presence as robot readiness."""
        requirements = {
            "/map": {"nav_msgs/msg/OccupancyGrid"},
            "/odom": {"nav_msgs/msg/Odometry"},
            "/tf": {"tf2_msgs/msg/TFMessage"},
            "/scan": {"sensor_msgs/msg/LaserScan", "sensor_msgs/msg/PointCloud2"},
            "/cmd_vel": {"geometry_msgs/msg/Twist", "geometry_msgs/msg/TwistStamped"},
        }
        present = {}
        for topic, accepted in requirements.items():
            types = set(topics.get(topic, []))
            present[topic] = bool(types & accepted)
        blockers = []
        if not packages_available:
            blockers.append("ROS 2 navigation message packages are unavailable")
        if not action_server_available:
            blockers.append("Nav2 NavigateToPose action server is not running")
        for topic in ("/map", "/odom", "/tf", "/scan", "/cmd_vel"):
            if not present[topic]:
                blockers.append(f"required ROS graph topic/type missing: {topic}")
        if action_server_available and not present["/cmd_vel"]:
            blockers.append("Nav2 controller output is not visible to a robot adapter")
        return {
            "ready": not blockers,
            "packages_available": bool(packages_available),
            "action_server_available": bool(action_server_available),
            "topics": present,
            "blockers": blockers,
            "scope": "ROS graph preflight only; does not certify frames, sensor freshness, calibration, or physical safety",
        }

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
                self._start_body_sensor_publishers(node)
                node.create_subscription(String, self.input_topic, self._receive, 10)
                self._start_sensor_subscriptions(node)
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
                if self._nav2_simulation_enabled:
                    self._start_nav2_simulation(node)
                executor = SingleThreadedExecutor(context=context)
                executor.add_node(node)
                self._node, self._executor, self._context = node, executor, context
                self._status = {"state": "connected", "available": True, "last_error": "", "started_at": time.time()}
                self._thread = threading.Thread(target=self._spin, args=(executor,), name="body-ros2", daemon=True)
                self._thread.start()
            except Exception as exc:
                self._status = {"state": "error", "available": False, "last_error": str(exc)}
            return self.status()

    def _start_body_sensor_publishers(self, node):
        """Create typed outputs for the physical samples already acquired by Body."""
        try:
            from sensor_msgs.msg import Imu, NavSatFix, PointCloud2, Range
            from rclpy.qos import qos_profile_sensor_data
        except Exception as exc:
            self._body_sensor_publishers = {}
            self._body_sensor_status = {key: {"state": "unavailable", "error": str(exc)[:180]}
                                        for key in BODY_SENSOR_PUBLISH_TOPICS}
            return
        message_types = {
            "imu": Imu, "gps": NavSatFix, "tof": Range,
            "ultrasonic_front_left": Range, "ultrasonic_front_right": Range,
            "ultrasonic_rear": Range, "mmwave_targets": PointCloud2,
        }
        publishers, statuses = {}, {}
        for key, topic in BODY_SENSOR_PUBLISH_TOPICS.items():
            try:
                publishers[key] = node.create_publisher(message_types[key], topic, qos_profile_sensor_data)
                statuses[key] = {"state": "ready", "topic": topic, "count": 0}
            except Exception as exc:
                statuses[key] = {"state": "error", "topic": topic, "error": str(exc)[:180]}
        self._body_sensor_publishers = publishers
        self._body_sensor_status = statuses

    @staticmethod
    def _set_ros_stamp(header, timestamp):
        from builtin_interfaces.msg import Time
        stamp = float(timestamp)
        seconds = math.floor(stamp)
        header.stamp = Time(sec=int(seconds), nanosec=int((stamp - seconds) * 1_000_000_000))

    @classmethod
    def _range_message(cls, sample, *, frame_id, ultrasonic):
        from sensor_msgs.msg import Range
        message = Range()
        message.header.frame_id = frame_id
        cls._set_ros_stamp(message.header, sample.get("timestamp") or time.time())
        message.radiation_type = Range.ULTRASOUND if ultrasonic else Range.INFRARED
        message.field_of_view = 0.0  # Sensor FOV is not calibrated/configured here.
        message.min_range = 0.02 if ultrasonic else float(sample.get("min_range_m", 0.04) or 0.04)
        message.max_range = 4.0 if ultrasonic else float(sample.get("max_range_m", 4.0) or 4.0)
        distance = sample.get("distance_m")
        message.range = float(distance) if sample.get("available") and distance is not None else math.inf
        return message

    def publish_body_sensor_observation(self, observation):
        """Publish typed messages without polling hardware or fabricating missing measurements."""
        with self._lock:
            publishers = dict(self._body_sensor_publishers)
            node = self._node
        if not publishers or node is None:
            return False
        modalities = observation.get("modalities", {}) if isinstance(observation, dict) else {}
        if not isinstance(modalities, dict):
            return False
        sent = []
        try:
            imu = modalities.get("imu") or {}
            if imu.get("simulated") is False and imu.get("available", True) and publishers.get("imu"):
                from sensor_msgs.msg import Imu
                message = Imu()
                message.header.frame_id = str(imu.get("frame") or "imu_sensor")
                self._set_ros_stamp(message.header, imu.get("timestamp") or time.time())
                attitude_valid = bool(imu.get("attitude_valid"))
                if attitude_valid:
                    roll, pitch, yaw = (math.radians(float(imu[k])) for k in
                                        ("roll_deg", "pitch_deg", "yaw_relative_deg"))
                    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
                    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
                    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
                    q = message.orientation
                    q.x, q.y = sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy
                    q.z, q.w = cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy
                    message.orientation_covariance = [0.1, 0, 0, 0, 0.1, 0, 0, 0, 0.5]
                else:
                    message.orientation_covariance[0] = -1.0
                gyro = imu.get("angular_velocity_dps") or [0, 0, 0]
                accel = imu.get("acceleration_g") or [0, 0, 0]
                message.angular_velocity.x, message.angular_velocity.y, message.angular_velocity.z = [math.radians(float(v)) for v in gyro]
                message.linear_acceleration.x, message.linear_acceleration.y, message.linear_acceleration.z = [float(v) * 9.80665 for v in accel]
                message.angular_velocity_covariance = [0.02, 0, 0, 0, 0.02, 0, 0, 0, 0.04]
                message.linear_acceleration_covariance = [0.1, 0, 0, 0, 0.1, 0, 0, 0, 0.1]
                publishers["imu"].publish(message)
                sent.append("imu")

            gps = modalities.get("gps") or {}
            if gps.get("simulated") is False and publishers.get("gps") and gps.get("latitude") is not None and gps.get("longitude") is not None:
                from sensor_msgs.msg import NavSatFix
                message = NavSatFix()
                message.header.frame_id = "gps"
                self._set_ros_stamp(message.header, gps.get("timestamp") or time.time())
                message.status.status = 0 if gps.get("fix") else -1
                message.status.service = 1
                message.latitude, message.longitude = float(gps["latitude"]), float(gps["longitude"])
                message.altitude = float(gps.get("altitude_m") or 0.0)
                message.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
                publishers["gps"].publish(message)
                sent.append("gps")

            tof = modalities.get("tof") or {}
            if tof.get("simulated") is False and publishers.get("tof") and tof.get("available") and tof.get("distance_m") is not None:
                publishers["tof"].publish(self._range_message(tof, frame_id=str(tof.get("frame") or "tof_front"), ultrasonic=False))
                sent.append("tof")

            ultrasonic = modalities.get("ultrasonic") or {}
            by_id = {str(item.get("id")): item for item in ultrasonic.get("sensors", []) if isinstance(item, dict)}
            for sensor_id, key, frame in (
                ("front_left", "ultrasonic_front_left", "hc_sr04_front_left"),
                ("front_right", "ultrasonic_front_right", "hc_sr04_front_right"),
                ("rear", "ultrasonic_rear", "hc_sr04_rear"),
            ):
                sample = by_id.get(sensor_id)
                if sample and ultrasonic.get("simulated") is False and publishers.get(key):
                    sample = {**sample, "timestamp": ultrasonic.get("timestamp")}
                    publishers[key].publish(self._range_message(sample, frame_id=frame, ultrasonic=True))
                    sent.append(key)

            radar = modalities.get("mmwave_radar") or {}
            if radar.get("simulated") is False and publishers.get("mmwave_targets") and radar.get("available", True):
                from sensor_msgs.msg import PointCloud2
                from sensor_msgs_py import point_cloud2
                points = []
                for target in radar.get("targets", []):
                    position = target.get("position_m") or []
                    if len(position) >= 3 and all(math.isfinite(float(v)) for v in position[:3]):
                        points.append(tuple(float(v) for v in position[:3]))
                stamp = float(radar.get("timestamp") or time.time())
                header = node.get_clock().now().to_msg()
                seconds, nanoseconds = int(stamp), int((stamp % 1) * 1_000_000_000)
                header.sec, header.nanosec = seconds, nanoseconds
                header.frame_id = str(radar.get("frame") or "ld2450")
                publishers["mmwave_targets"].publish(point_cloud2.create_cloud_xyz32(header, points))
                sent.append("mmwave_targets")
        except Exception as exc:
            with self._lock:
                self._status["body_sensor_publish_error"] = str(exc)[:200]
            return False
        with self._lock:
            for key in sent:
                status = self._body_sensor_status.get(key, {})
                status["count"] = int(status.get("count", 0)) + 1
                status["last_published_at"] = time.time()
                self._body_sensor_status[key] = status
            self._status["body_sensor_observation_count"] = int(self._status.get("body_sensor_observation_count", 0)) + 1
            self._status["body_sensor_last_published_at"] = time.time()
            self._status.pop("body_sensor_publish_error", None)
        return bool(sent)

    def _start_nav2_simulation(self, node=None):
        node = node or self._node
        if node is None:
            raise RuntimeError("ROS 2 bridge must be running before starting Nav2 simulation inputs")
        if self._nav2_simulation is None:
            from .nav2_simulation import Nav2Simulation
            self._nav2_simulation = Nav2Simulation(node)
        self._nav2_simulation_enabled = True
        return self._nav2_simulation.status()

    def set_nav2_simulation(self, enabled):
        enabled = bool(enabled)
        if enabled:
            if self._node is None:
                status = self.start()
                if not status.get("available"):
                    raise RuntimeError(status.get("last_error") or "ROS 2 is unavailable")
            return self._start_nav2_simulation()
        if self._nav2_simulation is not None:
            self._nav2_simulation.stop()
            self._nav2_simulation = None
        self._nav2_simulation_enabled = False
        return {"enabled": False, "simulation_only": True}

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

    def _start_sensor_subscriptions(self, node):
        try:
            from sensor_msgs.msg import Imu, LaserScan, NavSatFix, Range
            from nav_msgs.msg import Odometry
            message_types = {
                "imu": Imu,
                "gps": NavSatFix,
                "lidar": LaserScan,
                "odometry": Odometry,
                "range": Range,
            }
        except Exception as exc:
            self._sensor_status = {key: {"state": "unavailable", "error": str(exc)[:180]}
                                   for key in self.sensor_topics}
            return
        try:
            from rclpy.qos import qos_profile_sensor_data
        except Exception:
            # Keeps non-ROS unit tests usable; a sourced ROS runtime provides this profile.
            qos_profile_sensor_data = 10
        self._sensor_subscriptions = []
        self._sensor_status = {}
        for modality, message_type in message_types.items():
            topic = str(self.sensor_topics.get(modality, "") or "").strip()
            if not topic:
                self._sensor_status[modality] = {"state": "disabled", "topic": ""}
                continue
            try:
                subscription = node.create_subscription(
                    message_type, topic,
                    lambda message, key=modality, name=topic: self._receive_sensor_message(key, name, message),
                    qos_profile_sensor_data,
                )
                self._sensor_subscriptions.append(subscription)
                self._sensor_status[modality] = {"state": "listening", "topic": topic, "count": 0}
            except Exception as exc:
                self._sensor_status[modality] = {"state": "error", "topic": topic, "error": str(exc)[:180]}

    def _receive_sensor_message(self, modality, topic, message):
        try:
            observation = self.normalize_sensor_message(modality, message)
            observation["source"] = "ros2_sensor"
            observation["provenance"] = {
                "transport": "ros2",
                "topic": topic,
                "frame_id": str(getattr(getattr(message, "header", None), "frame_id", "") or ""),
                "source_stamp_s": self._message_stamp_seconds(message),
            }
            if self._nav2_simulation_enabled and modality in {"lidar", "odometry"} and topic in {"/scan", "/odom"}:
                observation["source"] = "ros2_simulation"
                observation["provenance"]["simulated"] = True
            self.on_observation(observation)
            with self._lock:
                self._status["sensor_input_count"] = int(self._status.get("sensor_input_count", 0)) + 1
                self._status["last_sensor_input_at"] = time.time()
                self._status["last_error"] = ""
            with self._lock:
                current = self._sensor_status.get(modality, {})
                current["count"] = int(current.get("count", 0)) + 1
                current["last_seen_at"] = time.time()
                self._sensor_status[modality] = current
        except Exception as exc:
            with self._lock:
                current = self._sensor_status.get(modality, {})
                current["last_error"] = str(exc)[:180]
                current["rejected_count"] = int(current.get("rejected_count", 0)) + 1
                self._sensor_status[modality] = current

    @staticmethod
    def _message_stamp_seconds(message):
        stamp = getattr(getattr(message, "header", None), "stamp", None)
        if stamp is None:
            return None
        return float(getattr(stamp, "sec", 0)) + float(getattr(stamp, "nanosec", 0)) * 1e-9

    @classmethod
    def normalize_sensor_message(cls, modality, message):
        """Convert standard ROS sensor messages to finite, provenance-ready observations."""
        def finite(value, label):
            value = float(value)
            if not math.isfinite(value):
                raise ValueError(f"{label} is not finite")
            return value

        header = getattr(message, "header", None)
        common = {
            "subject": f"sensor.{modality}",
            "kind": modality,
            "unit": "",
            "confidence": 1.0,
            "observed_at": time.time(),
        }
        if modality == "lidar":
            ranges = list(getattr(message, "ranges", []) or [])
            if not ranges:
                raise ValueError("LaserScan contains no ranges")
            stride = max(1, math.ceil(len(ranges) / 720))
            normalized = [finite(value, "range") if math.isfinite(float(value)) else None
                          for value in ranges[::stride]]
            common.update(value={
                "ranges_m": normalized,
                "angle_min_rad": finite(message.angle_min, "angle_min"),
                "angle_increment_rad": finite(message.angle_increment, "angle_increment") * stride,
                "range_min_m": finite(message.range_min, "range_min"),
                "range_max_m": finite(message.range_max, "range_max"),
                "sample_stride": stride,
                "original_sample_count": len(ranges),
            }, unit="m")
        elif modality == "imu":
            q = message.orientation
            sin_yaw = 2.0 * (finite(q.w, "orientation.w") * finite(q.z, "orientation.z") +
                             finite(q.x, "orientation.x") * finite(q.y, "orientation.y"))
            cos_yaw = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
            common.update(value={
                "orientation_xyzw": [finite(q.x, "orientation.x"), finite(q.y, "orientation.y"),
                                     finite(q.z, "orientation.z"), finite(q.w, "orientation.w")],
                "yaw_rad": math.atan2(sin_yaw, cos_yaw),
                "angular_velocity_rad_s": [finite(message.angular_velocity.x, "gyro.x"),
                                            finite(message.angular_velocity.y, "gyro.y"),
                                            finite(message.angular_velocity.z, "gyro.z")],
                "linear_acceleration_m_s2": [finite(message.linear_acceleration.x, "accel.x"),
                                             finite(message.linear_acceleration.y, "accel.y"),
                                             finite(message.linear_acceleration.z, "accel.z")],
            })
        elif modality == "gps":
            status = int(getattr(message.status, "status", -1))
            def optional_finite(value, label):
                try:
                    return finite(value, label)
                except (TypeError, ValueError):
                    return None
            latitude = optional_finite(message.latitude, "latitude")
            longitude = optional_finite(message.longitude, "longitude")
            altitude = optional_finite(message.altitude, "altitude")
            if status >= 0 and (latitude is None or longitude is None or
                                not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0):
                raise ValueError("valid GNSS fix has invalid coordinates")
            common.update(value={
                "fix_valid": status >= 0,
                "latitude_deg": latitude,
                "longitude_deg": longitude,
                "altitude_m": altitude,
                "status": status,
            }, unit="deg", confidence=1.0 if status >= 0 else 0.0)
        elif modality == "range":
            value = finite(message.range, "range")
            minimum = finite(message.min_range, "min_range")
            maximum = finite(message.max_range, "max_range")
            if minimum < 0 or maximum < minimum or not minimum <= value <= maximum:
                raise ValueError("Range measurement is outside its declared bounds")
            common.update(value={"range_m": value, "min_range_m": minimum,
                                 "max_range_m": maximum, "field_of_view_rad": finite(message.field_of_view, "field_of_view")},
                          unit="m")
        elif modality == "odometry":
            pose = message.pose.pose
            twist = message.twist.twist
            q = pose.orientation
            yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
            common.update(value={
                "position_m": [finite(pose.position.x, "position.x"), finite(pose.position.y, "position.y"),
                               finite(pose.position.z, "position.z")],
                "yaw_rad": finite(yaw, "yaw"),
                "linear_velocity_m_s": [finite(twist.linear.x, "velocity.x"),
                                         finite(twist.linear.y, "velocity.y"),
                                         finite(twist.linear.z, "velocity.z")],
                "angular_velocity_rad_s": [finite(twist.angular.x, "angular.x"),
                                           finite(twist.angular.y, "angular.y"),
                                           finite(twist.angular.z, "angular.z")],
                "child_frame_id": str(getattr(message, "child_frame_id", "") or ""),
            }, unit="m,m/s")
        else:
            raise ValueError(f"Unsupported ROS sensor modality: {modality}")
        common["frame_id"] = str(getattr(header, "frame_id", "") or "")
        return common

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
            simulation = self._nav2_simulation
            executor, node, context, rclpy = self._executor, self._node, self._context, self._rclpy
            self._executor = self._node = self._publisher = self._context = None
            self._body_sensor_publishers = {}
            self._body_sensor_status = {}
            self._thread = None
            self._nav2_client = None
            self._mock_nav2_client = None
            self._mock_nav2_server = None
            sensor_subscriptions, self._sensor_subscriptions = self._sensor_subscriptions, []
            self._nav2_simulation = None
            self._status.update(state="stopped", available=rclpy is not None)
        if simulation is not None:
            simulation.stop()
        if node is not None:
            for subscription in sensor_subscriptions:
                node.destroy_subscription(subscription)
        if executor is not None:
            executor.shutdown(timeout_sec=1.0)
        if node is not None:
            node.destroy_node()
        if context is not None and context.ok():
            context.shutdown()
