# Body ROS 2 and Nav2 status

The repository currently contains two different integration levels. The Body has a ROS 2 observation bridge and a Nav2 simulation. It does **not** yet contain a physical FNK0031 Nav2 bringup, and the simulation passing is not evidence that the robot can navigate safely.

ROS 2 is an operating-system distribution with ABI-coupled Python packages; `rclpy` must not be installed from PyPI into the Body venv.

## Linux / VENTUNO Q

1. Configure the official ROS 2 apt repository for the board's Ubuntu release.
2. Set `ROS_DISTRO` to the installed distribution (for example `jazzy`).
3. Install the optional Body packages with `bash ./install_body_ros2.sh`, or set `BODY_INSTALL_ROS2=1` before `./start_body.sh`.
4. `start_body.sh` sources `/opt/ros/$ROS_DISTRO/setup.bash` before launching the Body venv.
5. Open **ROS 2 flow** at `http://127.0.0.1:8766/ros2` and enable the bridge.

On Windows, set `ROS2_INSTALL_PATH` to the ROS 2 installation directory containing `local_setup.bat`; `start_body.bat` loads that environment when present. The ROS 2 Windows installation itself follows the official ROS documentation.

## What works today

The physical target is the **Freenove FNK0031 Crawling Robot Controller V3.2** on its stock FNHR firmware over USB. The Body and hexapod are one rigidly attached platform: camera, MiDaS, IMU, GNSS, LD2450, ToF, and HC-SR04 are robot-mounted sensors, not a second ROS robot. The Body's typed publishers are the robot sensor publishers. This co-location does not by itself define each sensor's measured translation/rotation relative to `base_link`; those transforms still need to be entered and verified.

- `/body/observations` publishes `std_msgs/msg/String` with JSON `{ "schema": "pandorabox.body_observation.v1", "observation": { ... } }`.
- `/body/observations_in` accepts `std_msgs/msg/String` containing either that envelope or one observation object with a non-empty `subject`.
- Input and output topic names are configurable in Body settings and must differ.
- Incoming String messages and subscribed typed `Imu`, `NavSatFix`, `LaserScan`, `Odometry`, and `Range` messages become Body observations and are forwarded through the existing Brain connector.
- Typed sensor subscriptions use ROS 2's sensor-data QoS profile when running in a sourced ROS environment.
- When the Body world model is running, its existing observation cycle publishes typed outputs for available physical modalities: `/body/sensors/imu`, `/body/sensors/gps/fix`, `/body/sensors/tof/front`, `/body/sensors/ultrasonic/{front_left,front_right,rear}`, and `/body/sensors/mmwave/targets` (`PointCloud2`). These outputs do not trigger additional hardware polls. The published rate is therefore the world-model sampling rate (default 2 s), not a navigation/control rate; unavailable/no-echo ranges are represented as `+Inf`, and radar points retain the source frame without an invented transform.
- The Nav2 route-test launch uses synthetic `/map`, `/scan`, `/odom`, and TF inputs plus a software base that consumes `/cmd_vel`. The command-isolation check only protects that synthetic route test.
- `physical_nav2_preflight` intentionally remains blocked until the hardware interfaces below exist. Package presence, a visible action server, or a successful synthetic route does not make the physical robot ready.

## Physical FNK0031 blockers

The bridge publishes the robot-mounted Body sensor samples as typed ROS messages, but only when the world model is running, and only at its current observation cadence. This is not a validated navigation-rate obstacle stream. The FNK0031 V3.2 stock FNHR USB interface reports `pose_available: false` and supports discrete, blocking gait/action orders, not a bounded continuous `cmd_vel` stream. The six-axis IMU provides attitude/rates but cannot provide planar position by itself. The repository has no physical map/localization bringup, robot description, calibrated sensor-to-base transforms, or integrated physical emergency-stop controller.

Consequently, there is no honest physical Nav2 test to run yet. Before one, the robot needs:

1. A measured planar odometry source (for example a validated visual odometry or external tracking solution) and verified `map -> odom -> base_link` transforms. GNSS is not a substitute for indoor local odometry.
2. A hardware publisher/adapter that exposes timestamped, calibrated obstacle observations in the correct frames. The LD2450 and three HC-SR04 readings must not be mislabeled as a 360-degree `LaserScan`; use their actual coverage, or a compatible real 2D lidar.
3. A continuous velocity/gait adapter with command limits, a deadman/watchdog, defined zero-command behavior, hardware feedback, and exclusive command ownership. The stock discrete FNHR orders are not suitable for Nav2's periodic velocity output.
4. A physical robot footprint and Nav2 costmap/controller parameters validated against the actual gait, dimensions, braking distance, update rates, and sensor blind zones.
5. An independent emergency stop and staged low-speed test procedure. Software preflight is not a certified safety system.

The current parameters in `deploy/nav2_fnk_sim_params.yaml` are explicitly for the simulated world. Do not use them as a physical robot configuration.

## Readiness semantics

`nav2_preflight` reports visible ROS packages, the NavigateToPose action server, and required graph types including `/map`, `/odom`, `/tf`, `/scan`, and `/cmd_vel`; this is still graph-only. `physical_nav2_preflight` additionally reports recent typed Body sample activity and repository-level hardware blockers, and currently returns `ready: false`. The actual hardware must remain stationary until the physical preflight, transforms, sensor freshness, command watchdog, and emergency-stop tests have all been validated on the robot.
