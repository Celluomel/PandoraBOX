import math
import sys
import types
import unittest
from unittest.mock import patch

from body_runtime_host.ros2_bridge import BODY_SENSOR_PUBLISH_TOPICS, Ros2ObservationBridge


class _Vector:
    x = y = z = 0.0


class _Header:
    frame_id = ""
    stamp = None


class _Imu:
    def __init__(self):
        self.header = _Header()
        self.orientation = types.SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0)
        self.angular_velocity = _Vector()
        self.linear_acceleration = _Vector()
        self.orientation_covariance = [0.0] * 9
        self.angular_velocity_covariance = [0.0] * 9
        self.linear_acceleration_covariance = [0.0] * 9


class _Range:
    ULTRASOUND = 0
    INFRARED = 1

    def __init__(self):
        self.header = _Header()


class _NavSatFix:
    COVARIANCE_TYPE_UNKNOWN = 0

    def __init__(self):
        self.header = _Header()
        self.status = types.SimpleNamespace(status=-1, service=0)


class _PointCloud2:
    pass


class _Publisher:
    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


class Ros2BodySensorPublishTests(unittest.TestCase):
    def test_physical_sensor_modalities_publish_with_units_frames_and_no_echo(self):
        sensor_msg = types.ModuleType("sensor_msgs.msg")
        sensor_msg.Imu, sensor_msg.NavSatFix = _Imu, _NavSatFix
        sensor_msg.Range, sensor_msg.PointCloud2 = _Range, _PointCloud2
        sensor_package = types.ModuleType("sensor_msgs")
        sensor_package.msg = sensor_msg
        builtin_msg = types.ModuleType("builtin_interfaces.msg")
        builtin_msg.Time = lambda sec, nanosec: types.SimpleNamespace(sec=sec, nanosec=nanosec)
        builtin_package = types.ModuleType("builtin_interfaces")
        builtin_package.msg = builtin_msg
        cloud_module = types.ModuleType("sensor_msgs_py.point_cloud2")
        cloud_module.create_cloud_xyz32 = lambda header, points: types.SimpleNamespace(header=header, points=list(points))
        sensor_msgs_py = types.ModuleType("sensor_msgs_py")
        sensor_msgs_py.point_cloud2 = cloud_module
        modules = {
            "sensor_msgs": sensor_package,
            "sensor_msgs.msg": sensor_msg,
            "builtin_interfaces": builtin_package,
            "builtin_interfaces.msg": builtin_msg,
            "sensor_msgs_py": sensor_msgs_py,
            "sensor_msgs_py.point_cloud2": cloud_module,
        }
        publishers = {key: _Publisher() for key in BODY_SENSOR_PUBLISH_TOPICS}
        node = types.SimpleNamespace(get_clock=lambda: types.SimpleNamespace(
            now=lambda: types.SimpleNamespace(to_msg=lambda: types.SimpleNamespace(sec=0, nanosec=0))))
        bridge = Ros2ObservationBridge(lambda _: None)
        bridge._node = node
        bridge._body_sensor_publishers = publishers

        observation = {"modalities": {
            "imu": {"simulated": False, "available": True, "timestamp": 1000.25,
                    "frame": "imu_sensor", "attitude_valid": False,
                    "angular_velocity_dps": [0, 0, 90], "acceleration_g": [0, 0, 1]},
            "gps": {"simulated": False, "timestamp": 1000.5, "fix": True,
                    "latitude": 48.8, "longitude": 2.1, "altitude_m": 30},
            "tof": {"simulated": False, "available": True, "timestamp": 1000.5,
                    "distance_m": 0.8, "frame": "tof_front"},
            "ultrasonic": {"simulated": False, "timestamp": 1000.5, "sensors": [
                {"id": "front_left", "available": True, "distance_m": 0.45},
                {"id": "front_right", "available": False, "distance_m": None},
                {"id": "rear", "available": True, "distance_m": 1.2},
            ]},
            "mmwave_radar": {"simulated": False, "available": True, "timestamp": 1000.5,
                              "frame": "ld2450", "targets": [{"position_m": [1.0, -0.2, 0.0]}]},
        }}
        with patch.dict(sys.modules, modules):
            self.assertTrue(bridge.publish_body_sensor_observation(observation))

        imu = publishers["imu"].messages[0]
        self.assertAlmostEqual(imu.angular_velocity.z, math.pi / 2)
        self.assertAlmostEqual(imu.linear_acceleration.z, 9.80665)
        self.assertEqual(imu.orientation_covariance[0], -1.0)
        self.assertEqual(publishers["gps"].messages[0].status.status, 0)
        self.assertEqual(publishers["ultrasonic_front_left"].messages[0].range, 0.45)
        self.assertTrue(math.isinf(publishers["ultrasonic_front_right"].messages[0].range))
        self.assertEqual(publishers["ultrasonic_rear"].messages[0].header.frame_id, "hc_sr04_rear")
        cloud = publishers["mmwave_targets"].messages[0]
        self.assertEqual(cloud.header.frame_id, "ld2450")
        self.assertEqual(cloud.points, [(1.0, -0.2, 0.0)])


if __name__ == "__main__":
    unittest.main()
