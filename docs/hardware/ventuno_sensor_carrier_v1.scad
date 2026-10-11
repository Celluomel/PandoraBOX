// Compact sensor carrier for Arduino UNO Q and ordered sensors.
// Units: mm. Front is +Y. This is a prototype carrier, not a chassis-specific mount.

$fn = 48;

plate_x = 200;
plate_y = 224;
plate_t = 4;
plate_corner_r = 5;

// UNO Q mechanical drawing: 160 x 100 mm, excluding the SoM heatsink/fan.
// The long board axis follows +Y so the sensor bar can sit beyond its front edge.
uno_x = 100;
uno_y = 160;
uno_stack_h = 25.8;
uno_post_h = 7;
uno_hole_d = 3.7;
uno_post_d = 6;
uno_center_x = 0;
uno_center_y = -22;

// Hole centers scaled from the supplied 160 x 100 mm mechanical drawing.
// Confirm the coordinates on the physical PCB before printing.
uno_holes = [
    [ 38, -76],
    [-46, -76],
    [-46,   9],
    [ 40,  77]
];

// Keep this footprint open above the carrier for USB-UART dongles and cables.
usb_clearance_x = 28;
usb_clearance_y = 28;

radar_width = 44;
radar_height = 15;
radar_z = 56;
radar_y = 91;

tof_width = 28.5;
tof_height = 23;
tof_z = 39;
tof_y = 72;

sonar_width = 45;
sonar_height = 20;
sonar_z = 38;
sonar_y = 108;
// HC-SR04 coverage: left, rear, right. Yaw 0 faces +Y; +90 faces -X.
sonar_positions = [[-88, 10, 90], [0, -88, 180], [88, 10, -90]];

imu_x = 41;
imu_y = 25.36;
imu_hole_dx = 32;
imu_hole_dy = 16;
imu_z = plate_t;
imu_center = [72, 80];

gps_tray_x = 50;
gps_tray_y = 46;
gps_tray_t = 2.4;
gps_z = 66;
gps_center = [0, -86];

module rounded_plate(x, y, h, r) {
    linear_extrude(height=h)
        hull() {
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * (x / 2 - r), sy * (y / 2 - r)])
                    circle(r=r);
        }
}

module base_plate() {
    // Open ladder frame: longitudinal edge rails and cross-members preserve load paths.
    for (x = [-plate_x / 2 + 4, plate_x / 2 - 4])
        translate([x, 0, plate_t / 2])
            cube([8, plate_y, plate_t], center=true);
    for (y = [-plate_y / 2 + 4, -104, -98, -13, 55, 72, 91, 108])
        translate([0, y, plate_t / 2])
            cube([plate_x, 8, plate_t], center=true);
    // Generic chassis attachment slots; measure the FNK0031 before fastening.
    for (x = [-plate_x / 2 + 10, plate_x / 2 - 10],
         y = [-plate_y / 2 + 10, plate_y / 2 - 10])
        translate([x, y, plate_t / 2])
            difference() {
                cube([12, 18, plate_t], center=true);
                hull() {
                    translate([0, -5, 0]) cylinder(d=3.4, h=plate_t + 1, center=true);
                    translate([0,  5, 0]) cylinder(d=3.4, h=plate_t + 1, center=true);
                }
    }
}

module uno_posts() {
    for (p = uno_holes) {
        translate([uno_center_x + p[0], uno_center_y + p[1], plate_t])
            difference() {
                cylinder(d=uno_post_d, h=uno_post_h);
                translate([0, 0, -0.1])
                    cylinder(d=uno_hole_d, h=uno_post_h + 0.2);
            }
    }
}

module ledge(x, y, z, sx, sy, sz) {
    translate([x, y, z]) cube([sx, sy, sz], center=true);
}

module vertical_sensor_rail(x, y, z, width, height, yaw=0) {
    // Two narrow rails grip the PCB edges and leave its antenna/optical face open.
    translate([x, y, z]) rotate([0, yaw, 0]) {
        ledge(0, 0, -height/2 + 1.2, width, 3, 2.4);
        ledge(-width/2 + 1, 0, 0, 2, 3, height);
        ledge( width/2 - 1, 0, 0, 2, 3, height);
        ledge(0, 0, height/2 - 1.2, width, 3, 2.4);
    }
}

module sonar_sensor_rail(x, y, z, yaw=0) {
    // HC-SR04 PCB rests on thin side lips; both transducers remain unobstructed.
    translate([x, y, z]) rotate([0, yaw, 0]) {
        ledge(0, 0, -sonar_height/2 + 1, sonar_width, 3, 2);
        ledge(-sonar_width/2 + 1, 0, 0, 2, 3, sonar_height);
        ledge( sonar_width/2 - 1, 0, 0, 2, 3, sonar_height);
    }
}

module sensor_mounts() {
    // Radar faces forward (+Y); the side/top edge rails do not cover its antenna.
    vertical_sensor_rail(0, radar_y, radar_z, radar_width + 4, radar_height + 4);
    for (x = [-radar_width/2 - 1, radar_width/2 + 1])
        translate([x, radar_y, plate_t])
            cube([3, 3, radar_z - radar_height/2 - plate_t], center=false);

    // ToF sits below the radar, with a clear optical path.
    vertical_sensor_rail(0, tof_y, tof_z, tof_width + 5, tof_height + 5);
    for (x = [-tof_width/2 - 1.5, tof_width/2 + 1.5])
        translate([x, tof_y, plate_t])
            cube([3, 3, tof_z - tof_height/2 - plate_t], center=false);

    // Ultrasonics are distributed around the perimeter: left, rear, and right.
    for (i = [0:2])
        sonar_sensor_rail(sonar_positions[i][0], sonar_positions[i][1],
                          sonar_z, sonar_positions[i][2]);
    for (i = [0:2])
        translate([sonar_positions[i][0] - 1.5, sonar_positions[i][1], plate_t])
            cube([3, 3, sonar_z - sonar_height/2 - plate_t], center=false);

    // Modulino Movement: four-hole mounting pattern, kept low and near the center.
    for (dx = [-imu_hole_dx/2, imu_hole_dx/2],
         dy = [-imu_hole_dy/2, imu_hole_dy/2])
        translate([imu_center[0] + dx, imu_center[1] + dy, imu_z + 1.6])
            difference() {
                cylinder(d=6, h=3.2, center=true);
                cylinder(d=3.4, h=3.4, center=true);
            }
    // GPS patch antenna tray: keep its ceramic face horizontal and sky-facing.
    translate([gps_center[0], gps_center[1], gps_z])
        rounded_plate(gps_tray_x, gps_tray_y, gps_tray_t, 3);
    // GPS risers sit behind the UNO Q rear edge, clear of side USB-UART ports.
    for (x = [-gps_tray_x/2 + 5, gps_tray_x/2 - 5]) {
        translate([gps_center[0] + x, gps_center[1] - gps_tray_y/2 + 2, plate_t])
            cube([2.4, 3, gps_z - plate_t], center=false);
        ledge(gps_center[0] + x, gps_center[1], gps_z - 1.5, 3, gps_tray_y - 8, 3);
    }
}

module board_reference() {
    // Simplified board envelope; heatsink/fan envelope must be measured separately.
    color([0.1, 0.45, 0.35, 0.28])
        translate([uno_center_x, uno_center_y,
                   plate_t + uno_post_h + uno_stack_h / 2])
            cube([uno_x, uno_y, uno_stack_h], center=true);
}

show_board = false;
base_plate();
uno_posts();
sensor_mounts();
if (show_board) board_reference();
