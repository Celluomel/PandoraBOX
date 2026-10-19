# VENTUNO Q local sensor bridge

One persistent STM32 sketch exposes the Qwiic sensors and radar to Linux Body over the
VENTUNO Q's local Arduino Router Bridge:

- `body_imu_read()` returns raw acceleration (g) and angular velocity (deg/s).
- `body_tof_read()` returns the latest CQRobot VL53L1X front range in millimetres.
- `body_ultrasonic_read()` returns fresh ranges and per-channel diagnostics for
  three HC-SR04s: D2/D3 front-left, D4/D5 front-right, D6/D9 rear. Each ECHO
  input must have its own divider; D7/D8 stay reserved for the LD2450 UART.
- `body_ld2450_read()` returns the latest UART7 target frame, unchanged from
  the existing LD2450 bridge.
- `body_gps_read()` validates NMEA on `Serial1` / USART3 (D0 RX, D1 TX),
  reports UART byte/checksum counters, retains the latest GGA sentence, and
  publishes recent GSV sentences with per-satellite C/N0, azimuth, and elevation.

The Body must run on the VENTUNO Q because Arduino Router Bridge is local to
that device. Nothing here publishes sensor data to the LAN or changes the
Linux USB, FNK0031, or Body HTTP interfaces. GPS uses USART3 / `Serial1` at
38400 baud by default (`BODY_GPS_BAUD` overrides it); UART7 remains D7/RX
and D8/TX at 256000 baud. Modulino Movement and VL53L1X share Qwiic / Wire1;
the VL53L1X uses address 0x29. Since probing an absent ToF sensor interferes
with the Modulino on this shared bus, ToF probing is disabled by default. Enable
it only after connecting the sensor with `BODY_ENABLE_TOF=1` when deploying.
Body publishes its single forward beam as `perception.modalities.tof`, without
fabricating a range when the sensor is absent.

## Direct CLI build and deployment

This firmware is independent of App Lab. It initializes `Wire1` for the
Qwiic Modulino, reads GPS on `Serial1` and UART7 at 256000 baud, and provides
the local Router RPCs `body_imu_read`, `body_tof_read`, `body_ultrasonic_read`,
`body_ld2450_read`, and `body_gps_read`. Ultrasonic pings are sequenced at
least 60 ms apart, use non-blocking echo timing with a 30 ms timeout, and never
turn a missing echo into a zero-distance measurement. The Body configuration selects
`ventuno_bridge_ld2450`; the runtime adds parsed physical radar targets to
`perception.modalities.mmwave_radar` while retaining the current robot source.

From the project checkout on the VENTUNO Q, build without changing the running
STM32 firmware:

```sh
arduino-cli lib install Arduino_Modulino
arduino-cli lib install "Adafruit VL53L1X" "Adafruit BusIO"
scripts/deploy_ventuno_sensor_bridge.sh
```

Only after a successful build and wiring check, upload the combined image with
the direct Arduino CLI uploader:

```sh
scripts/deploy_ventuno_sensor_bridge.sh --upload
```

The direct upload targets the Ventuno STM32's nonvolatile flash. Do not use
`arduino-app-cli app start` / App Lab Run as the persistence mechanism: App Lab
loads its MCU sketch into volatile RAM, so that sketch disappears on a power
cycle. The Body Linux service starts independently; it does not need a default
App Lab app. The deployment script automatically stops the sensor App Lab app
and clears it as the default before uploading, so its RAM sketch cannot mask the
persistent firmware at boot. To clear that setting manually:

```sh
arduino-app-cli properties set default none
arduino-app-cli properties get default
```

The direct upload deliberately uses `arduino:zephyr:ventunoq` (the Ventuno core's
nonvolatile flash target), not App Lab's RAM-loaded sketch mode. Keep the
combined source in this repository and rerun the direct upload whenever it
changes.

The build stages only the `.ino` before compiling so Arduino CLI does not try
to resolve the cloud `sketch.yaml` profile on the device. ToF probing stays off
until the sensor is physically connected; then deploy with:

```sh
BODY_ENABLE_TOF=1 scripts/deploy_ventuno_sensor_bridge.sh --upload
```

For an isolated hardware check of the ToF (which temporarily disables IMU
sampling on the shared Qwiic bus), use:

```sh
BODY_ENABLE_IMU=0 BODY_ENABLE_TOF=1 scripts/deploy_ventuno_sensor_bridge.sh --upload
```

Restore IMU sampling afterward with `BODY_ENABLE_IMU=1 BODY_ENABLE_TOF=0`.

The upload replaces the STM32 image, so use this combined sketch rather than
the standalone IMU or radar sketches. The upload tool prompts for credentials;
the script stores none. `scripts/configure_ventuno_uart7.sh` backs up the
installed variant overlay before enabling UART7. If compilation still reports
that `uart7` is absent from the generated devicetree, the installed Arduino
Zephyr core's precompiled variant must be rebuilt with that overlay; do not
flash a different sketch as a workaround.

## Verify

After upload and a full power cycle, enable the physical radar in Body's
**Sensor device selection** and choose **Ventuno STM32 UART · local Bridge**. Confirm the
selector reports fresh UART7 frames and targets. Check `/plugins/gps/status`
for D0/D1 UART byte counts, NMEA checksum validation, GPS fix state, satellites
used/in view, and per-satellite C/N0 from GSV. Signal values are in dB-Hz;
azimuth/elevation are included when the receiver provides them. Check `/worldmodel/status`
for the real `mmwave_radar` and `tof` modalities, `/plugins/imu/status` for
the IMU, `/plugins/tof/status` for the VL53L1X, and
`/plugins/ultrasonic/status` for all three HC-SR04 channels.
Neither source fabricates targets when its bridge is unavailable or stale.

The LSM6DSOX is a 6-axis IMU without a magnetometer. The Body derives roll and
pitch from gravity when the acceleration magnitude is near 1 g and reports
gyro rotation rates separately; it cannot provide absolute compass heading.
