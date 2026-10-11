// Lightweight fit-check variant of the supplied hexapod carrier.
// Units: mm. Front is +Y. Dimensions marked provisional still require measurement.
$fn = 48;
part = "preview"; // preview | all | lower | upper | lower_front/center/rear | upper_front/center/rear | lower_joiner | upper_joiner | sensor parts
compact_print = false; // true: shorten deck to 205 mm for one-piece Ender 3 Pro prints

W = 160;
L = compact_print ? 205 : 230;
nose = 20;
rear_flat = 36;
t = 3.5;
gap = 55;
board_holes = [[-45,-75],[45,-75],[-45,75],[45,75]]; // provisional: replace with verified drawing coordinates
servo = [20.5, 40.5];
servo_y = [-63, 0, 63];
servo_x = 58;
ear_dy = 24.75;
posts = [[-54,-88],[54,-88],[-54,0],[54,0],[-54,88],[54,88]];
radar_y = 58;
tof_y = 82;
imu_y = -42;
gps_y = -80;
mast_h = 75;
tof_board = [28.5, 23, 1.6]; // ordered breakout envelope; verify board thickness/edge details

module outline() {
    polygon([[0, L/2], [W/2, L/2-nose], [W/2, -L/2+nose],
             [rear_flat, -L/2], [-rear_flat, -L/2],
             [-W/2, -L/2+nose], [-W/2, L/2-nose]]);
}

module rounded_slot(x, y, sx, sy, r=2.5) {
    translate([x, y, -1]) linear_extrude(t+2)
        hull()
            for (dx=[-1,1], dy=[-1,1])
                translate([dx*(sx/2-r), dy*(sy/2-r)]) circle(r=r);
}

module upper_vents() {
    // Narrow flank slots leave the central spine, radar-base web, perimeter,
    // and all post/sensor pads intact. Broad windows are omitted for the split.
    for (x=[-68,68], y=[-55,-25,5,35,65]) rounded_slot(x,y,7,18,2.5);
    // The broad windows near y=+/-30 are omitted so the split-plate joints
    // retain solid material around their M3 fasteners.
}

module lower_vents() {
    // Larger rounded vents beneath the raised board. Keep 10 mm transverse
    // webs and 8 mm longitudinal webs; the board-hole lands remain uncut.
    for (x=[-36,-12,12,36], y=[-55,55])
        rounded_slot(x,y,14,20,4);
}

module at_us() {
    a = atan2(nose, W/2);
    translate([46, L/2-nose, 0]) rotate([0,0,-a]) children();
    translate([-46, L/2-nose, 0]) rotate([0,0,a]) children();
    translate([0, -L/2, 0]) rotate([0,0,180]) children();
}

us_w = 52;
us_h = 26;
us_d = 11;
module us_holes(h=t+2) {
    for (s=[-1,1]) translate([s*25,-7,-1]) cylinder(d=3.2,h=h);
}
module us_mount() {
    difference() {
        union() {
            translate([-us_w/2,-us_d,0]) cube([us_w,us_d,us_h]);
            translate([-30,-14,0]) cube([60,14,3]);
        }
        for (s=[-1,1]) translate([s*13,1,us_h/2]) rotate([90,0,0]) cylinder(d=16.5,h=us_d+2);
        translate([-23.2,-us_d-1,us_h/2-10.5]) cube([46.4,us_d-2,21]);
        us_holes(6);
    }
}

module radar_holes(h=t+2) {
    for (x=[-26,26]) for (y=[-4.5,-19.5]) translate([x,y,-1]) cylinder(d=3.2,h=h);
}
module radar_tower() {
    rh=58;
    difference() {
        union() {
            translate([-22,-9,0]) cube([44,9,rh]);
            translate([-30,-24,0]) cube([60,24,3]);
        }
        translate([-17.75,-10,30]) cube([35.5,8.5,20.5]);
        translate([-6,-10,0]) cube([12,6,31]);
        radar_holes(6);
    }
}

module mast_holes(h=t+2) {
    for (i=[0:3]) rotate(45+i*90) translate([20,0,-1]) cylinder(d=3.2,h=h);
}
module lidar_mast() {
    difference() {
        union() {
            cylinder(d=50,h=3);
            cylinder(d=34,h=mast_h);
            translate([0,0,mast_h]) cylinder(d=72,h=4);
        }
        translate([0,0,-1]) cylinder(d=16,h=mast_h+6);
        for (i=[0:3]) rotate(45+i*90) translate([26,0,mast_h-1]) cylinder(d=3.2,h=6);
        mast_holes(6);
    }
}

module imu_holes(h=t+2) {
    for (x=[-7.5,7.5]) for (y=[-6,6]) translate([x,y,-1]) cylinder(d=3.2,h=h);
}
module imu_pad() {
    difference() {
        translate([-15,-13,0]) cube([30,26,4]);
        imu_holes(6);
    }
}

module gps_holes(h=t+2) {
    for (x=[-9,9]) for (y=[-9,9]) translate([x,y,-1]) cylinder(d=3.2,h=h);
}
module gps_mast() {
    difference() {
        union() {
            translate([-13,-13,0]) cube([26,26,3]);
            translate([-5,-5,0]) cube([10,10,40]);
            translate([-18,-18,40]) cube([36,36,3]);
        }
        gps_holes(6);
    }
}

module tof_holes(h=t+2) {
    for (s=[-1,1]) translate([s*17,-7,-1]) cylinder(d=3.2,h=h);
}
module tof_mount() {
    // Adjustable-size U cradle: optical face points forward (+Y), with no window across it.
    difference() {
        union() {
            translate([-20,-11,0]) cube([40,24,3]);
            translate([-18,3,3]) cube([2.5,4,23]);
            translate([15.5,3,3]) cube([2.5,4,23]);
            translate([-18,3,3]) cube([36,3,2]);
            translate([-18,3,24]) cube([5,4,2]);
            translate([13,3,24]) cube([5,4,2]);
        }
        for (s=[-1,1]) translate([s*17,-7,-1]) cylinder(d=3.2,h=5);
    }
}

module spacer() {
    difference() {
        cylinder(d=8,h=gap);
        translate([0,0,-1]) cylinder(d=3.4,h=gap+2);
    }
}

module lower() {
    difference() {
        linear_extrude(t) outline();
        lower_vents();
        for (s=[-1,1]) for (y=servo_y) {
            translate([s>0 ? servo_x : -(W/2+1),y-servo[1]/2,-1])
                cube([W/2+1-servo_x,servo[1],t+2]);
            for (e=[-1,1]) translate([s*(servo_x+servo[0]/2),y+e*ear_dy,-1]) cylinder(d=4,h=t+2);
        }
        for (p=board_holes) translate([p[0],p[1],-1]) cylinder(d=3.2,h=t+2);
        for (p=posts) translate([p[0],p[1],-1]) cylinder(d=3.4,h=t+2);
        translate([-20,-8,-1]) cube([40,16,t+2]);
    }
}

// Ender 3 Pro print kit: each deck is split into three pieces at y=+/-25 mm.
// Short underside splice plates join the sections with M3 screws and nuts.
joint_y = [-25, 25];
lower_joint_x = [-48, 0, 48];
upper_joint_x = [-50, 0, 50];
joint_bolt_offset = 8;

module lower_with_joint_holes() {
    difference() {
        lower();
        for (x=lower_joint_x, y=joint_y, dy=[-joint_bolt_offset,joint_bolt_offset])
            translate([x,y+dy,-1]) cylinder(d=3.3,h=t+2);
    }
}

module upper_with_joint_holes() {
    difference() {
        upper();
        for (x=upper_joint_x, y=joint_y, dy=[-joint_bolt_offset,joint_bolt_offset])
            translate([x,y+dy,-1]) cylinder(d=3.3,h=t+2);
    }
}

module clip_y(y0,y1) {
    intersection() {
        children();
        translate([-W/2-1,y0,-1]) cube([W+2,y1-y0,t+2]);
    }
}

module lower_piece(which) {
    if (which=="front") clip_y(25,L/2) lower_with_joint_holes();
    else if (which=="center") clip_y(-25,25) lower_with_joint_holes();
    else clip_y(-L/2,-25) lower_with_joint_holes();
}

module upper_piece(which) {
    if (which=="front") clip_y(25,L/2) upper_with_joint_holes();
    else if (which=="center") clip_y(-25,25) upper_with_joint_holes();
    else clip_y(-L/2,-25) upper_with_joint_holes();
}

module plate_joiner() {
    // 18 x 32 x 5 mm underside strap; two M3 fasteners per strap.
    difference() {
        translate([-9,-16,0]) cube([18,32,5]);
        for (y=[-8,8]) translate([0,y,-1]) cylinder(d=3.3,h=7);
    }
}

module upper() {
    difference() {
        linear_extrude(t) outline();
        upper_vents();
        for (p=posts) translate([p[0],p[1],-1]) cylinder(d=3.4,h=t+2);
        translate([0,0,-1]) cylinder(d=16,h=t+2);
        at_us() us_holes();
        translate([0,radar_y,0]) radar_holes();
        mast_holes();
        translate([0,imu_y,0]) imu_holes();
        translate([0,gps_y,0]) gps_holes();
        translate([0,tof_y,0]) tof_holes();
        translate([-12,85,-1]) cube([24,6,t+2]);
        translate([-12,-100,-1]) cube([24,6,t+2]);
    }
}

module spacers() {
    for (p=posts) translate([p[0],p[1],t]) spacer();
}

module sensor_assembly() {
    translate([0,tof_y,t]) tof_mount();
    at_us() us_mount();
    translate([0,radar_y,0]) radar_tower();
    lidar_mast();
    translate([0,imu_y,0]) imu_pad();
    translate([0,gps_y,0]) gps_mast();
}

module board_reference() {
    // Visual-only board envelope: 100 x 160 x 25.8 mm, heatsink/fan excluded.
    color([0.08,0.48,0.42,0.78])
        translate([0,0,t+7+25.8/2]) cube([100,160,25.8],center=true);
}

module assembly(include_board=false) {
    lower();
    spacers();
    translate([0,0,t+gap]) {
        upper();
        translate([0,0,t]) sensor_assembly();
    }
    if (include_board) board_reference();
}

if (part=="lower") lower();
else if (part=="upper") upper();
else if (part=="lower_front") lower_piece("front");
else if (part=="lower_center") lower_piece("center");
else if (part=="lower_rear") lower_piece("rear");
else if (part=="upper_front") upper_piece("front");
else if (part=="upper_center") upper_piece("center");
else if (part=="upper_rear") upper_piece("rear");
else if (part=="lower_joiner" || part=="upper_joiner") plate_joiner();
else if (part=="spacer") spacer();
else if (part=="us_mount") us_mount();
else if (part=="radar_tower") radar_tower();
else if (part=="lidar_mast") lidar_mast();
else if (part=="imu_pad") imu_pad();
else if (part=="gps_mast") gps_mast();
else if (part=="tof_mount") tof_mount();
else if (part=="all") assembly(false);
else assembly(true);
