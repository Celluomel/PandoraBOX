# UNO Q compact sensor carrier, prototype v1

This is a 200 x 224 mm open-frame sensor carrier around the Arduino UNO Q mechanical
envelope. The UNO Q board is 100 x 160 mm; the source drawing reports 25.8 mm
stack height without the SoM heatsink/fan. The base has four generic tie-down
slots, not an FNK0031-specific mount. Measure the robot's mounting points
before fastening the carrier to it.

## Layout

- UNO Q is held on four 3.7 mm-clearance standoffs, 7 mm above the carrier. The
  asymmetric hole centers are scaled from the supplied mechanical drawing and
  must be checked against the physical PCB before print.
- The simplified board envelope follows the published 100 x 160 mm outline.
  The SoM heatsink/fan height and its actual keep-out are not modeled yet.
- USB-UART dongles plug directly into the UNO Q. There is no enclosure or
  side wall around the board. Sensor brackets are lifted above the board's
  connector plane and the rear GPS risers sit outside its outline; keep dongle
  bodies and cables routed outward. Verify the actual dongle orientation before
  printing because the USB-UART adapter model and connector side are unknown.
- LD2450 radar is on the forward upright rails, facing +Y. Its antenna face and
  edges stay open.
- VL53L1X ToF is below the radar and faces +Y; do not put a cover across its
  emitter/receiver window.
- HC-SR04 boards are distributed to the left, rear, and right, rather than
  stacked along the forward sensor cluster. Read them sequentially to reduce
  acoustic cross-talk.
- Modulino Movement is mounted on the forward right extension, clear of the
  UNO Q side ports, using its 32 x 16 mm hole pattern. Keep its axes aligned
  with the robot frame during assembly.
- The NEO-M9N ceramic patch tray is elevated at the rear with the ceramic face
  upward. The flat tray is intended for tape/strap retention because the exact
  Amazon breakout outline is seller-dependent.

## Holder coordinates

Coordinates are in millimeters from the carrier center; +Y is forward and Z is
measured from the frame underside:

| Module | Center / orientation | Mounting |
| --- | --- | --- |
| LD2450 | (0, 91, 56), face +Y | Upright open-front cradle |
| VL53L1X | (0, 72, 39), face +Y | Upright open-front cradle |
| HC-SR04 left | (-88, 10, 38), yaw +90 deg, face -X | Open-transducer cradle |
| HC-SR04 rear | (0, -88, 38), yaw 180 deg, face -Y | Open-transducer cradle |
| HC-SR04 right | (88, 10, 38), yaw -90 deg, face +X | Open-transducer cradle |
| Modulino Movement | (72, 80) | 32 x 16 mm four-hole footprint |
| NEO-M9N | (0, -86), tray base Z=66 | Flat 50 x 46 mm tray, antenna up |

## Important fit limits

The structural frame is 200 x 224 mm; the angled sonar cradles extend the total
Y envelope to about 232 mm. Maximum height is 68.4 mm at the GPS tray. The UNO Q
outline is 100 x 160 mm per the supplied mechanical drawing. It shows a 25.8 mm
stack height excluding the SoM heatsink/fan. The drawing specifies four R1.85 mm
holes; their centers in this prototype are scaled from the top view rather than
copied from a fully dimensioned coordinate table, so they remain to be checked. The
Modulino Movement is 41 x 25.36 mm with 32 x 16 mm hole spacing.
The LD2450 PCB is 44 x 15 mm. The ToF tray is sized around the ordered
28.5 x 23 mm module. HC-SR04 and NEO-M9N breakouts can differ slightly between
vendors, so their rails/tray should be checked against the actual parts before
printing a final fit.

The STL is generated from the parametric layout as overlapping closed shells.
Inspect it in the intended slicer and enable mesh union/repair if needed. This is
a fit-check prototype, not a validated production mount. Confirm the hole-center
pattern, heatsink/fan envelope, connector clearances, USB-UART insertion and
cable bend radius, and FNK0031 attachment points against real hardware before
printing. The GPS tray is a flat support surface for tape/straps; breakout
retention is not yet vendor-specific.

## Export

Run `python generate_ventuno_carrier_stl.py` to regenerate
`ventuno_sensor_carrier_fitcheck.stl`. The `.scad` source is also available for
review and editing in OpenSCAD.

## Sources

- [Arduino UNO Q datasheet, mechanical information](https://docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf)
- [Arduino Modulino Movement datasheet](https://docs.arduino.cc/resources/datasheets/ABX00101-datasheet.pdf)
- [Hi-Link LD2450 product page](https://www.hlktech.com/Goods-226.html)
- [HLK-LD2450 hardware manual](https://h.hlktech.com/download/HLK-LD2450-24G/1/HLK%20LD2450%201T2R%E8%BF%90%E5%8A%A8%E7%9B%AE%E6%A0%87%E6%A3%80%E6%B5%8B%E8%BF%BD%E8%B8%AA%E6%A8%A1%E7%BB%84%E8%AF%B4%E6%98%8E%E4%B9%A6%20V1.02%20.pdf)
