# VENTUNO Q Modulino Movement Bridge

Reads the Qwiic Modulino Movement (LSM6DSOX) on the VENTUNO Q STM32 and exposes
one local Arduino Router RPC, `body_imu_read`. The Body Linux process consumes
the RPC as a physical `imu` observation modality. Acceleration is reported in
g and angular rate in degrees per second, matching the Arduino sensor API.
The Body derives roll and pitch from gravity only while acceleration magnitude
is near 1 g. Angular velocity is displayed separately; the 6-axis Modulino has
no magnetometer, so it cannot provide an absolute compass heading.

Install the Arduino Modulino library, then compile on the Ventuno with:

```sh
arduino-cli lib install Arduino_Modulino
arduino-cli compile --fqbn arduino:zephyr:ventunoq firmware/ventuno_modulino_imu_bridge
```

The sketch does not use an external USB-UART or network sensor service. It
leaves the LD2450 UART and FNK0031 controller interfaces untouched. Flashing
this sketch replaces the currently loaded STM32 sketch; confirm the current
MCU application before uploading it.

After the bridge firmware is installed and Body runs on the VENTUNO Q, use
`Robots & hardware > Modulino Movement > Read sample` to verify physical data.
Enable the sensor there to add it to every Body observation; the Quest HUD
then reads the same `perception.modalities.imu` sample for its horizon display.
