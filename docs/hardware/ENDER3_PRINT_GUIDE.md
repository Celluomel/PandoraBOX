# Ender 3 Pro print kit

The full-size 160 x 230 mm decks do not fit on a 220 x 220 mm Ender 3 Pro bed, even diagonally: the actual chamfered outline still has a minimum 230 mm projected span. The standard kit divides each deck into front, center, and rear sections at y = +/-25 mm.

The export script also creates a separate compact, one-piece option at 160 x 205 mm. It preserves the board, servo, spacer, and central sensor mounting coordinates, while moving the front/rear ultrasonic holder anchors with the shortened outline. This changes the chassis length by 25 mm; dry-fit the board, wires, robot frame, and sensors before choosing it. Its 205 mm bed span leaves about 7.5 mm per end on a nominal 220 mm bed before any brim/skirt clearance.

## Export

Run `docs/hardware/export_ender3_kit.ps1` from PowerShell with OpenSCAD's command-line executable (`openscad.com`). For example:

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\hardware\export_ender3_kit.ps1
```

The script writes the split kit to `artifacts/hexapode_chassis/ender3_kit/` and compact alternatives to `artifacts/hexapode_chassis/ender3_kit/one_piece_205mm/`. The `light_all.stl` file is an assembled fit-check model; do not send it to the slicer as one print.

## Parts and assembly

- Print one each: `lower_front`, `lower_center`, `lower_rear`, `upper_front`, `upper_center`, `upper_rear`.
- Print six `lower_joiner` straps and six `upper_joiner` straps. Each deck has three straps at each of its two seams.
- Print the sensor parts separately. The three ultrasonic holders use three copies of `us_mount`.
- For a one-piece chassis instead, print `one_piece_205mm/lower_205mm.stl` and `one_piece_205mm/upper_205mm.stl`; do not also print the six split deck sections or their joiners.
- Join each seam with the straps on the underside, using M3 screws, washers, and nuts. M3 x 16 mm is a reasonable starting length for the 3.5 mm deck plus 5 mm strap and nut; confirm screw engagement and clearance before assembly.
- Reassemble the lower and upper decks with the six 55 mm spacers as in the fit-check model.

## Slicer setup and cautions

Place each plate section flat on the bed. A 0.4 mm nozzle, 0.2 mm layers, 4 perimeters, 5 top/bottom layers, and 25-35% gyroid infill are conservative prototype settings. PETG is a reasonable starting material for a chassis prototype; inspect the servo-pocket lands and splice areas before loading the robot.

This is a fit-check/prototype, not a validated load-rated chassis. The board hole coordinates and several module dimensions are still marked provisional in the SCAD source. Verify the Ventuno Q with its heatsink/fan, actual sensors, servo dimensions, cable exits, and all fastener clearances before printing the complete set. Do not mount powered servos or operate the robot until the joints and plate strength have been physically checked.
