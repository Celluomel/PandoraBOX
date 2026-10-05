# Body sensor bring-up: VENTUNO Q + FNK0031

## Hardware in the delivery

| Module | First connection target | Body role | Important constraint |
| --- | --- | --- | --- |
| HLK-LD2450 | VENTUNO Q, dedicated USB-UART adapter | Up to 3 moving metric targets | 5 V supply (>200 mA), 256000 baud, 3.3 V UART, 10 Hz |
| Arduino Modulino Movement (LSM6DSOX) | VENTUNO Q Qwiic | 3-axis acceleration and gyro | Qwiic/I2C is 3.3 V; confirm VENTUNO Q's Linux/MCU access path before selecting the reader |
| GPSV3-M9N | VENTUNO Q, dedicated USB-UART adapter for initial bring-up | Outdoor GNSS/map anchor | Check the breakout's input-voltage marking; the u-blox module itself is 2.7-3.6 V |
| VL53L1X breakout | VENTUNO Q MCU I2C/Qwiic only after pinout check | Short-range ToF distance/ROI | The sensor IC is 2.8 V; breakout voltage regulation and pull-ups vary by board |
| 3 x HC-SR04 | VENTUNO Q real-time MCU GPIO, not Linux GPIO | Narrow-beam short-range range checks | 5 V supply; ECHO is 5 V and needs a divider/level shifter before any 3.3 V input |
| Dupont and JST-SH leads | Wiring only | Prototyping | Connector fit does not guarantee matching pin order; verify every cable end-to-end |

The VENTUNO Q owns perception and sensor acquisition. The FNK0031 remains
stock FNHR firmware and the motor/servo controller. Keep its existing USB link
reserved for the FNK protocol. Do not attach new UART devices to that serial
link, overwrite its firmware, or assume that the FNK P3 port is available while
stock firmware is running.

## Physical topology

```text
HLK-LD2450 -- UART / USB-UART ----┐
GPSV3-M9N -- UART / USB-UART -----┤
Modulino Movement -- Qwiic/I2C ---┤--> VENTUNO Q Body Runtime
VL53L1X -- I2C (after breakout ---┤       -> body_perception_frame.v2
                  voltage check)  │       -> Body UI / world model / Brain API
HC-SR04 x3 -- conditioned GPIO ---┘
FNK0031 stock controller <------ dedicated USB FNHR command link
```

For initial UART tests, use one sensor at a time and a separate USB-UART
adapter per module. On Linux, configure stable `/dev/serial/by-id/...` paths,
not transient `/dev/ttyUSB0` numbering. Never connect a 5 V TX output to a
3.3 V-only input. The sensor grounds and VENTUNO ground must be common when
using UART/GPIO, while sensor power should come from a rail with measured
headroom rather than an unverified logic pin.

The LD2450 reports X lateral, Y forward in millimetres, and signed velocity in
centimetres/second. Body converts these to metres and metres/second in a
sensor-local frame, then applies a measured mounting transform before fusion.
The M9N fix is geographic, not local-map odometry: only use it outdoors and
anchor/project it with its reported accuracy. The Modulino Movement gives
acceleration and angular rate; it does not provide absolute heading by itself.

## Software readiness and staged validation

`body_requirements.txt` already includes `pyserial`. The Body currently has a
vendor-neutral mmWave JSON-over-HTTP adapter and accepts IMU/GNSS fields from
the robot gateway. Direct LD2450 UART and direct NMEA ingestion still need to
be connected to runtime configuration and the live perception frame. The
serial decoders in `body_runtime_host/sensor_serial.py` are parser groundwork,
not a claim that a physical module has already been acquired or tested.

1. Record exact breakout labels, cable pin order, device IDs and idle voltages.
2. Bring up the M9N outdoors alone; verify checksum-valid GGA/RMC, fix quality,
   satellites, HDOP and stale-data behavior.
3. Bring up LD2450 alone; validate signed X/Y and velocity using a person
   crossing left/right and approaching/receding at measured positions.
4. Connect Modulino Movement on Qwiic and verify raw axes, units, orientation
   and timestamping with stationary and hand-rotated tests.
5. Connect one VL53L1X and one HC-SR04 through verified voltage conditioning;
   confirm the MCU acquisition route and compare readings against a ruler.
6. Add the remaining two HC-SR04 sensors one at a time. Stagger pings by at
   least 60 ms per sensor to limit acoustic crosstalk.
7. Enable fusion only after each modality reports source, timestamp, frame,
   calibration, quality and stale/error state in the Body UI.
8. Run stationary sensor-only tests, then hand-carried tests with motors
   disabled. Physical actuation remains confirmation-gated until calibration
   and stopping behavior have been measured.

## Acceptance gates

- FNK USB controller remains discoverable and retains its stock remote behavior.
- No 5 V signal reaches a 3.3 V-only pin; no sensor is powered from an
  unverified rail.
- Every sensor has an independently visible online/offline/stale/error state.
- LD2450 positions and relative velocity use a documented robot-frame
  transform; the transform is calibrated rather than guessed from cable or
  board orientation.
- GNSS reports fix quality and uncertainty; no-fix coordinates are never
  treated as a valid robot pose.
- IMU angular velocity is integrated only with drift/uncertainty represented;
  it is not presented as absolute planar heading.
- Simulation and physical sensor frames are visibly distinguished in UI and
  logs.
