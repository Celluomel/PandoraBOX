# VENTUNO Q Modulino Movement Bridge

Reads the Qwiic Modulino Movement (LSM6DSOX) on the VENTUNO Q STM32 and exposes
the local Arduino Router RPC `body_imu_read`. The Body Linux service calls the
local Router socket and publishes physical samples as `perception.modalities.imu`.
Acceleration is in g and angular velocity is in degrees per second. The 6-axis
IMU has no magnetometer, so it cannot provide absolute compass heading.

## No App Lab runtime dependency

The sketch is compiled and flashed directly with `arduino-cli`; it does not
need an App Lab app, Python brick, or App Lab startup configuration. Arduino
Router and the Body Runtime remain separate Linux services. Flashing writes the
sketch to the STM32, where it runs independently after upload.

On the VENTUNO Q, from the project checkout:

```sh
scripts/deploy_ventuno_modulino_imu.sh
```

The script compiles for `arduino:zephyr:ventunoq` and uploads over the board's
network uploader. Arduino CLI prompts for the upload password; it is not stored
in the repository. To build only, run:

```sh
arduino-cli compile --fqbn arduino:zephyr:ventunoq firmware/ventuno_modulino_imu_bridge
```

The sketch explicitly initializes `Wire1`, which is the Qwiic I2C bus on this
board. It retries Modulino initialization and serves `body_imu_read` through
`Bridge.provide_safe`, so I2C access happens in the sketch loop context.

## Verified on hardware

The direct CLI upload was tested on the VENTUNO Q with the App Lab app stopped
and no default app configured. The Body returned changing physical LSM6DSOX
samples (`simulated: false`) through its local Router connection.

This standalone IMU sketch replaces the STM32 sketch currently in flash. For
the combined persistent IMU + LD2450 image, use
`scripts/deploy_ventuno_sensor_bridge.sh`; it builds first and does not upload
unless explicitly passed `--upload`. The combined image requires UART7 to be
present in the generated Zephyr devicetree. Do not flash this standalone sketch
if you need both sensor RPCs.

After flashing, verify `/plugins/imu/status` on the Body reports
`available: true`, `simulated: false`, and a fresh timestamp. Enable the IMU in
Body sensor settings to include it in observations and the HUD horizon.
