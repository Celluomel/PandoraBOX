# VENTUNO Q local sensor bridge

One persistent STM32 sketch exposes both sensors to Linux Body over the
VENTUNO Q's local Arduino Router Bridge:

- `body_imu_read()` returns raw acceleration (g) and angular velocity (deg/s).
- `body_ld2450_read()` returns the latest UART7 target frame, unchanged from
  the existing LD2450 bridge.

The Body must run on the VENTUNO Q because Arduino Router Bridge is local to
that device. Nothing here publishes sensor data to the LAN or changes the
Linux USB, GPS USART3, FNK0031, or Body HTTP interfaces. UART7 remains D7/RX
and D8/TX at 256000 baud; Qwiic remains dedicated to Modulino Movement.

## Direct CLI build and deployment

This firmware is independent of App Lab. It initializes `Wire1` for the
Qwiic Modulino, reads UART7 at 256000 baud, and provides the local Router RPCs
`body_imu_read` and `body_ld2450_read`. The Body configuration selects
`ventuno_bridge_ld2450`; the runtime adds parsed physical radar targets to
`perception.modalities.mmwave_radar` while retaining the current robot source.

From the project checkout on the VENTUNO Q, build without changing the running
STM32 firmware:

```sh
arduino-cli lib install Arduino_Modulino
scripts/deploy_ventuno_sensor_bridge.sh
```

Only after a successful build and wiring check, upload the combined image:

```sh
scripts/deploy_ventuno_sensor_bridge.sh --upload
```

The upload replaces the STM32 image, so use this combined sketch rather than
the standalone IMU or radar sketches. The upload tool prompts for credentials;
the script stores none. `scripts/configure_ventuno_uart7.sh` backs up the
installed variant overlay before enabling UART7. If compilation still reports
that `uart7` is absent from the generated devicetree, the installed Arduino
Zephyr core's precompiled variant must be rebuilt with that overlay; do not
flash a different sketch as a workaround.

## Verify

After upload/reboot, enable the physical radar in Body's **Sensor device
selection** and choose **Ventuno STM32 UART · local Bridge**. Confirm the
selector reports fresh UART7 frames and targets. Check `/worldmodel/status`
for the real `mmwave_radar` modality and `/plugins/imu/status` for the IMU.
Neither source fabricates targets when its bridge is unavailable or stale.

The LSM6DSOX is a 6-axis IMU without a magnetometer. The Body derives roll and
pitch from gravity when the acceleration magnitude is near 1 g and reports
gyro rotation rates separately; it cannot provide absolute compass heading.
