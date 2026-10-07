"""ROS 2 sensor and base simulation used to exercise a real Nav2 stack safely."""

from __future__ import annotations

import math
import os
import time


class Nav2Simulation:
    """Publish a small metric world and integrate Nav2 velocity commands in software."""

    SIZE = 160
    RESOLUTION = 0.1
    ORIGIN = -8.0
    OBSTACLES = (
        (2.02, -0.48, 2.98, 0.48),
        (2.18, 0.88, 2.82, 1.52),
    )

    def __init__(self, node):
        from geometry_msgs.msg import TransformStamped, Twist, TwistStamped
        from nav_msgs.msg import OccupancyGrid, Odometry
        from rclpy.duration import Duration
        from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import LaserScan
        from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

        self.node = node
        distro = os.environ.get("ROS_DISTRO", "").lower()
        self._last_tick = time.monotonic()
        self._last_cmd = 0.0
        self._vx = self._vy = self._wz = 0.0
        self.x, self.y, self.yaw = 0.5, 0.0, 0.0
        self._scan_angles = tuple(math.radians(deg) for deg in range(-180, 180, 2))

        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._map_pub = node.create_publisher(OccupancyGrid, "/map", map_qos)
        self._odom_pub = node.create_publisher(Odometry, "/odom", 10)
        self._scan_pub = node.create_publisher(LaserScan, "/scan", 10)
        self._tf = TransformBroadcaster(node)
        self._static_tf = StaticTransformBroadcaster(node)
        # ROS 2 distributions expose only one command type on a topic. Jazzy's
        # Nav2 controller publishes TwistStamped; older distributions use Twist.
        if distro in {"jazzy", "kilted", "rolling"}:
            self._twist_sub = None
            self._stamped_sub = node.create_subscription(TwistStamped, "/cmd_vel", self._receive_stamped, 10)
        else:
            self._twist_sub = node.create_subscription(Twist, "/cmd_vel", self._receive_twist, 10)
            self._stamped_sub = None

        static = TransformStamped()
        static.header.frame_id = "map"
        static.child_frame_id = "odom"
        static.transform.rotation.w = 1.0
        laser = TransformStamped()
        laser.header.frame_id = "base_link"
        laser.child_frame_id = "laser_link"
        laser.transform.translation.x = 0.12
        laser.transform.rotation.w = 1.0
        self._static_tf.sendTransform([static, laser])
        self._map = self._make_map(OccupancyGrid)
        self._timer = node.create_timer(0.05, self._tick)

    @classmethod
    def _occupied(cls, x: float, y: float) -> bool:
        if not (cls.ORIGIN <= x < cls.ORIGIN + cls.SIZE * cls.RESOLUTION
                and cls.ORIGIN <= y < cls.ORIGIN + cls.SIZE * cls.RESOLUTION):
            return True
        return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in cls.OBSTACLES)

    @classmethod
    def _make_map(cls, message_type):
        from std_msgs.msg import Header

        grid = message_type()
        grid.header = Header()
        grid.header.frame_id = "map"
        grid.info.resolution = cls.RESOLUTION
        grid.info.width = cls.SIZE
        grid.info.height = cls.SIZE
        grid.info.origin.position.x = cls.ORIGIN
        grid.info.origin.position.y = cls.ORIGIN
        grid.info.origin.orientation.w = 1.0
        grid.data = [
            100 if cls._occupied(cls.ORIGIN + (i % cls.SIZE + 0.5) * cls.RESOLUTION,
                                 cls.ORIGIN + (i // cls.SIZE + 0.5) * cls.RESOLUTION)
            else 0
            for i in range(cls.SIZE * cls.SIZE)
        ]
        return grid

    def _receive_twist(self, msg):
        self._set_velocity(msg.linear.x, msg.linear.y, msg.angular.z)

    def _receive_stamped(self, msg):
        twist = msg.twist
        self._set_velocity(twist.linear.x, twist.linear.y, twist.angular.z)

    def _set_velocity(self, vx, vy, wz):
        self._vx = max(-0.15, min(0.15, float(vx)))
        self._vy = max(-0.10, min(0.10, float(vy)))
        self._wz = max(-0.45, min(0.45, float(wz)))
        self._last_cmd = time.monotonic()

    def _ray_range(self, angle):
        step = 0.04
        distance = 0.12
        while distance <= 8.0:
            wx = self.x + math.cos(self.yaw + angle) * distance
            wy = self.y + math.sin(self.yaw + angle) * distance
            if self._occupied(wx, wy):
                return distance
            distance += step
        return math.inf

    def _tick(self):
        from geometry_msgs.msg import TransformStamped
        from nav_msgs.msg import Odometry
        from sensor_msgs.msg import LaserScan

        now_mono = time.monotonic()
        dt = min(0.1, max(0.0, now_mono - self._last_tick))
        self._last_tick = now_mono
        if now_mono - self._last_cmd > 0.35:
            self._vx = self._vy = self._wz = 0.0
        cos_yaw, sin_yaw = math.cos(self.yaw), math.sin(self.yaw)
        self.x += (cos_yaw * self._vx - sin_yaw * self._vy) * dt
        self.y += (sin_yaw * self._vx + cos_yaw * self._vy) * dt
        self.yaw = math.atan2(math.sin(self.yaw + self._wz * dt), math.cos(self.yaw + self._wz * dt))

        stamp = self.node.get_clock().now().to_msg()
        if not getattr(self, "_map_sent", False):
            self._map.header.stamp = stamp
            self._map_pub.publish(self._map)
            self._map_sent = True

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        odom.twist.twist.linear.x = self._vx
        odom.twist.twist.linear.y = self._vy
        odom.twist.twist.angular.z = self._wz
        self._odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = "odom"
        transform.child_frame_id = "base_link"
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation.z = math.sin(self.yaw / 2.0)
        transform.transform.rotation.w = math.cos(self.yaw / 2.0)
        self._tf.sendTransform(transform)

        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = "laser_link"
        scan.angle_min = self._scan_angles[0]
        scan.angle_max = self._scan_angles[-1]
        scan.angle_increment = math.radians(2)
        scan.time_increment = 0.0
        scan.scan_time = 0.05
        scan.range_min = 0.12
        scan.range_max = 8.0
        scan.ranges = [self._ray_range(angle) for angle in self._scan_angles]
        self._scan_pub.publish(scan)

    def status(self):
        return {
            "enabled": True,
            "simulation_only": True,
            "topics": ["/map", "/scan", "/odom", "/tf", "/cmd_vel"],
            "pose": {"x": round(self.x, 3), "y": round(self.y, 3), "yaw_rad": round(self.yaw, 3)},
            "last_cmd_age_s": round(time.monotonic() - self._last_cmd, 3) if self._last_cmd else None,
            "note": "Synthetic world only; velocity commands do not reach FNK hardware.",
        }

    def stop(self):
        self._timer.cancel()
        self.node.destroy_timer(self._timer)
        if self._twist_sub is not None:
            self.node.destroy_subscription(self._twist_sub)
        if self._stamped_sub is not None:
            self.node.destroy_subscription(self._stamped_sub)
        self.node.destroy_publisher(self._map_pub)
        self.node.destroy_publisher(self._odom_pub)
        self.node.destroy_publisher(self._scan_pub)
