# Body ROS 2 bridge

The Body can bridge timestamped observations to and from a sourced ROS 2 installation. ROS 2 is an operating-system distribution with ABI-coupled Python packages; `rclpy` must not be installed from PyPI into the Body venv.

## Linux / VENTUNO Q

1. Configure the official ROS 2 apt repository for the board's Ubuntu release.
2. Set `ROS_DISTRO` to the installed distribution (for example `jazzy`).
3. Install the optional Body packages with `bash ./install_body_ros2.sh`, or set `BODY_INSTALL_ROS2=1` before `./start_body.sh`.
4. `start_body.sh` sources `/opt/ros/$ROS_DISTRO/setup.bash` before launching the Body venv.
5. Open **ROS 2 flow** at `http://127.0.0.1:8766/ros2` and enable the bridge.

On Windows, set `ROS2_INSTALL_PATH` to the ROS 2 installation directory containing `local_setup.bat`; `start_body.bat` loads that environment when present. The ROS 2 Windows installation itself follows the official ROS documentation.

## Topics

- `/body/observations` publishes `std_msgs/msg/String` with JSON `{ "schema": "pandorabox.body_observation.v1", "observation": { ... } }`.
- `/body/observations_in` accepts `std_msgs/msg/String` containing either that envelope or one observation object with a non-empty `subject`.
- Input and output topic names are configurable in Body settings and must differ.
- Incoming messages become timestamped Body observations and are forwarded through the existing Brain connector.
- This initial bridge deliberately has no motor-command topic. FNK0031 actuation remains behind its separate Body hardware and safety path.

The current bridge transports the Body observation contract; it does not yet adapt arbitrary ROS `Image`, `PointCloud2`, `Imu`, or `Odometry` topics. Dedicated typed sensor adapters and calibrated frame transforms remain a subsequent integration step.
