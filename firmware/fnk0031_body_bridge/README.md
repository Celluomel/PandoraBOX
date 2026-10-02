# FNK0031 Body USB bridge (legacy custom-firmware option)

**Do not upload this sketch for the stock-firmware USB integration.** The Body
now speaks FNHR's existing framed binary protocol over the FNK0031 USB serial
port. The stock `robot.Start(true)` firmware can therefore keep its Freenove
Wi-Fi/Processing controls and RF24 remote active while the Ventuno Q remains on
the normal LAN and connects to the FNK0031 by USB.

This sketch remains only as an alternative for installations that deliberately
choose exclusive Body control and accept losing the built-in Freenove controls.

This sketch keeps gait and servo-level behavior inside Freenove's FNHR library.
The Body can request only `forward`, `backward`, `turn_left`, `turn_right`, and
`stop`; the sketch maps those names to the corresponding high-level `FNHR`
methods. It contains no per-servo commands and does not expose arbitrary
`MoveBody`, `TwistBody`, or `LegMoveToRelatively` calls.

## Install

1. Install the Freenove FNHR Arduino library and its required dependencies.
2. Open `FNK0031BodyBridge.ino` in Arduino IDE.
3. Select the FNK0031-compatible **Arduino Mega 2560** board and the USB serial
   port belonging to the FNK0031 control board.
4. Compile first. Upload only when the robot is secured and its servos are
   disconnected for initial protocol validation.
5. In Body > Robots & hardware, select **Direct USB serial · FNHR firmware**,
   choose the matching port, save, and use **Check USB connection**. The check
   sends only `PING`; physical actuation remains separately disabled by default.

## Serial contract

115200 baud, newline-delimited ASCII:

- `PING` -> `PONG FNK0031_BODY_V1`
- `CMD forward|backward|turn_left|turn_right|stop` -> `STARTED <action>`, then
  `DONE <action>` after the FNHR call returns

The firmware starts with `robot.Start(false)`, so its own sketch remains the
controller; FNHR's built-in Processing/Android/remote communication loop is not
enabled. It emits no pose, odometry, IMU, or battery measurements. This legacy
text protocol is not used by the current Body USB driver.

The startup/handshake is not a physical-motion test. Keep the Body's physical
actuation toggle off until the firmware, linkage, power, and emergency-stop
behavior have been reviewed on the assembled robot.
