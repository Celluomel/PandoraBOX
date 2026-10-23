# FNK0031 Custom FNHR Controller

This is an **opt-in replacement firmware** for the Freenove FNK0031 Crawling
Robot Controller V3.2. It uses Freenove's FNHR library for gait generation and
inverse kinematics. The stock V3.2 firmware remains untouched; uploading this
sketch replaces it and disables the Freenove Processing/Android/RF-remote
control path, as described by [Freenove's custom programming guide](https://docs.freenove.com/projects/fnk0031/en/latest/fnk0031/codes/tutorial/Programming.html).

## Scope

The sketch exposes one completed FNHR gait action per USB command. It is not a
continuous Nav2 `cmd_vel` controller: FNHR's `Crawl` implementation blocks
while the leg servos complete the gait sequence. A stop request cannot preempt
the sequence already executing. After a gait returns, the firmware enters
`SleepMode` after 1.2 seconds without another completed movement command. This
limits repeated movement after USB loss but is **not** an emergency stop and
does not bound the remaining time of an in-progress gait until that is measured
on the real robot.

## USB protocol

115200 baud, newline-delimited ASCII:

- `PING` -> `PONG FNK0031_NAV_V2`
- `CMD state` -> one `STATE` line containing uptime and six records of
  `(foot x, y, z in mm, joint A, B, C in degrees)`. These are FNHR's
  command-derived internal estimates; the controller has no servo feedback,
  and these values are not measured leg positions or body odometry.
- `CMD leg <1..6> <+5|-5>` -> moves only the selected leg by a 5 mm relative
  Z offset and returns `STARTED leg <n>` then `DONE leg <n>`. The Body HUD
  exposes this only as a board-only diagnostic after explicit confirmation;
  it does not enable general robot actuation.
- `CMD forward|backward|left|right|turn_left|turn_right` -> `STARTED <action>`
  then `DONE <action>` after the FNHR call returns.
- `CMD crawl <x> <y> <angle>` -> one FNHR `robot.Crawl(x, y, angle)` action.
- `CMD stop` -> `robot.SleepMode()` when the firmware is able to process the
  command.

Translation is clamped by FNHR to a 42 mm vector and turn angle to 18 degrees;
this sketch rejects values outside those bounds. The function names and bounds
are from the upstream FNHR source. They are not a calibrated map from ROS
velocity (m/s) to gait displacement or speed.

## Build and bench sequence

1. Select the Arduino Mega 2560-compatible target and the FNK0031 USB port.
   The FNHR V12.6 source and its CC BY-SA 3.0 license are included under
   `vendor/FNHR`. Install the `RF24` and `FlexiTimer2` Arduino libraries if
   they are not already available in the IDE; FNHR includes both.
2. Compile without uploading. This source has not yet been compiled against
   the locally installed AVR core and library versions.
3. Before upload, save the currently installed stock firmware and confirm the
   loss of the stock remote/Processing control path is acceptable.
4. First upload and test with no servos attached or with the chassis securely
   supported and servo power isolated. Verify `PING` and `CMD state`; the Body
   HUD's board-only leg check is limited to one 5 mm vertical step. Only after
   that bench check should an operator test a gait with an independent way to
   cut servo power.
5. Measure gait completion and stop latency before connecting any autonomous
   planner. Do not use this sketch for physical Nav2 until a velocity adapter,
   odometry, sensor transforms, map/localization, and independent E-stop have
   passed physical tests.

The sketch has not been compiled or run on a V3.2 controller in this workspace.
