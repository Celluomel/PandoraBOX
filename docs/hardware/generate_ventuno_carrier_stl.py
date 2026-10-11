"""Generate a binary STL fit-check model for the UNO Q sensor carrier.

Meshes are closed primitive shells that overlap at their joints. Slicers usually
union these during slicing; inspect the mesh in the intended slicer before print.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path


OUT = Path(__file__).with_name("ventuno_sensor_carrier_fitcheck.stl")
TRIANGLES: list[tuple[tuple[float, float, float], ...]] = []


def quad(a, b, c, d):
    TRIANGLES.extend(((a, b, c), (a, c, d)))


def box(cx, cy, cz, sx, sy, sz, yaw=0):
    x0, x1 = -sx / 2, sx / 2
    y0, y1 = -sy / 2, sy / 2
    z0, z1 = -sz / 2, sz / 2
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def p(x, y, z):
        return (cx + x * c - y * s, cy + x * s + y * c, cz + z)

    quad(p(x0, y0, z0), p(x0, y0, z1), p(x0, y1, z1), p(x0, y1, z0))
    quad(p(x1, y0, z0), p(x1, y1, z0), p(x1, y1, z1), p(x1, y0, z1))
    quad(p(x0, y0, z0), p(x1, y0, z0), p(x1, y0, z1), p(x0, y0, z1))
    quad(p(x0, y1, z0), p(x0, y1, z1), p(x1, y1, z1), p(x1, y1, z0))
    quad(p(x0, y0, z0), p(x0, y1, z0), p(x1, y1, z0), p(x1, y0, z0))
    quad(p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1))


def tube(cx, cy, z0, outer_d, inner_d, height, sides=32):
    outer, inner = outer_d / 2, inner_d / 2
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        ob0 = (cx + outer * math.cos(a0), cy + outer * math.sin(a0), z0)
        ob1 = (cx + outer * math.cos(a1), cy + outer * math.sin(a1), z0)
        ot0 = (ob0[0], ob0[1], z0 + height)
        ot1 = (ob1[0], ob1[1], z0 + height)
        ib0 = (cx + inner * math.cos(a0), cy + inner * math.sin(a0), z0)
        ib1 = (cx + inner * math.cos(a1), cy + inner * math.sin(a1), z0)
        it0 = (ib0[0], ib0[1], z0 + height)
        it1 = (ib1[0], ib1[1], z0 + height)
        quad(ob0, ob1, ot1, ot0)
        quad(ib0, it0, it1, ib1)
        quad(ot0, ot1, it1, it0)
        quad(ob0, ib0, ib1, ob1)


def centered_box(x, y, z0, sx, sy, sz):
    box(x, y, z0 + sz / 2, sx, sy, sz)


def slot_pad(cx, cy):
    # 12 x 18 mm landing pad around a 3.4 x 10 mm open-ended mounting slot.
    for dx in (-3.85, 3.85):
        centered_box(cx + dx, cy, 0, 4.3, 18, 4)
    for dy in (-7, 7):
        centered_box(cx, cy + dy, 0, 12, 4, 4)


def upright_cradle(cx, cy, z_center, width, height, depth=3):
    # Open-front U cradle with a narrow top retaining lip.
    centered_box(cx, cy, z_center - height / 2 + 1.2, width, depth, 2.4)
    for x in (-width / 2 + 1, width / 2 - 1):
        box(cx + x, cy, z_center, 2, depth, height)
    centered_box(cx, cy, z_center + height / 2 - 1.2, width, depth, 2.4)


def build():
    plate_x, plate_y, plate_t = 200, 224, 4

    # Load-bearing open ladder base and cross-members beneath mounting points.
    for x in (-96, 96):
        box(x, 0, 2, 8, plate_y, plate_t)
    for y in (-108, -104, -98, -13, 55, 72, 91, 108):
        box(0, y, 2, plate_x, 8, plate_t)
    for x in (-90, 90):
        for y in (-102, 102):
            slot_pad(x, y)

    # UNO Q M3 clearance standoffs; coordinates scaled from the supplied drawing.
    board_x, board_y = 0, -22
    for x, y in ((38, -76), (-46, -76), (-46, 9), (40, 77)):
        tube(board_x + x, board_y + y, plate_t, 6, 3.7, 7)

    # LD2450 upright forward-facing cradle and twin load posts.
    upright_cradle(0, 91, 56, 48, 19)
    for x in (-24, 24):
        centered_box(x, 91, 4, 3, 3, 43)

    # VL53L1X forward-facing upright cradle, below the radar.
    upright_cradle(0, 72, 39, 33.5, 28, depth=3)
    for x in (-17, 17):
        centered_box(x, 72, 4, 3, 3, 24)

    # Spread ultrasonic coverage around the carrier instead of stacking modules
    # in the forward sensor cluster: left, rear, and right.
    sonar_positions = ((-88, 10, 90), (0, -88, 180), (88, 10, -90))
    for x, y, yaw in sonar_positions:
        bottom_z = 28
        box(x, y, bottom_z + 1, 45, 3, 2, yaw)
        for dx in (-22, 22):
            box(x + dx * math.cos(math.radians(yaw)),
                y + dx * math.sin(math.radians(yaw)),
                38, 2, 3, 20, yaw)
        centered_box(x, y, 4, 3, 3, 24)

    # Modulino Movement footprint and four through-clearance bosses on side wing.
    imu_cx, imu_cy = 72, 80
    for dx in (-16, 16):
        for dy in (-8, 8):
            tube(imu_cx + dx, imu_cy + dy, plate_t, 6, 3.4, 3.2)

    # Rear GPS carrier tray and rear-edge risers, away from side USB ports.
    gps_cx, gps_cy, gps_z = 0, -86, 66
    box(gps_cx, gps_cy, gps_z + 1.2, 50, 46, 2.4)
    for x in (-20, 20):
        centered_box(x, -105, 4, 3, 3, gps_z - 4)
        box(x, gps_cy, gps_z - 1.5, 3, 38, 3)


def write_stl():
    build()
    xs = [p[0] for tri in TRIANGLES for p in tri]
    ys = [p[1] for tri in TRIANGLES for p in tri]
    zs = [p[2] for tri in TRIANGLES for p in tri]
    header = b"PandoraBOX UNO Q sensor carrier fit-check; mm".ljust(80, b" ")
    with OUT.open("wb") as stream:
        stream.write(header)
        stream.write(struct.pack("<I", len(TRIANGLES)))
        for tri in TRIANGLES:
            a, b, c = tri
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            norm = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            stream.write(struct.pack("<12fH", nx / norm, ny / norm, nz / norm,
                                     *tri[0], *tri[1], *tri[2], 0))
    print(f"{OUT.name}: {len(TRIANGLES)} triangles, {OUT.stat().st_size} bytes")
    print(f"bounds mm: X {min(xs):.1f}..{max(xs):.1f}, "
          f"Y {min(ys):.1f}..{max(ys):.1f}, Z {min(zs):.1f}..{max(zs):.1f}")


if __name__ == "__main__":
    write_stl()
