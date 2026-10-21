import test from 'node:test';
import assert from 'node:assert/strict';
import zlib from 'node:zlib';
import {
  disparityToPriorMeters, rawDepthToMeters, intrinsicsFor, pixelToCamera, mountFor,
  yoloMatchesDepth, cloudGrid, fillDepthCloud, sampleDepthMeters, decodeGray16Png,
} from '../../body_runtime_host/depth_projection.js';

const near = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) <= eps, `${a} != ${b}`);

test('prior maps disparity 1 -> 0.7 m, 0 -> 5.5 m, monotonic', () => {
  near(disparityToPriorMeters(1), 0.7); near(disparityToPriorMeters(0), 5.5);
  let last = Infinity;
  for (let d = 0; d <= 1.0001; d += 0.1) { const z = disparityToPriorMeters(d); assert.ok(z < last); last = z; }
  near(disparityToPriorMeters(2), 0.7); near(disparityToPriorMeters(NaN), 5.5);
});

test('calibrated depth uses the inverse-affine fit and clamps', () => {
  const cal = { available: true, inverse_scale_per_relative_unit: 2e-5, inverse_offset_per_m: -0.8 };
  near(rawDepthToMeters(50000, cal), 1 / (2e-5 * 50000 - 0.8));
  assert.equal(rawDepthToMeters(10, cal), null);
  assert.equal(rawDepthToMeters(50000, { available: false }), null);
  const tiny = { available: true, inverse_scale_per_relative_unit: 0, inverse_offset_per_m: 100 };
  near(rawDepthToMeters(1, tiny), 0.2);
});

test('intrinsics: supplied are rescaled, nominal otherwise', () => {
  const s = intrinsicsFor(320, 240, { fx: 500, fy: 500, cx: 320, cy: 240, width: 640, height: 480 });
  assert.equal(s.calibrated, true); near(s.fx, 250); near(s.cx, 160);
  const n = intrinsicsFor(640, 480, {});
  assert.equal(n.calibrated, false); near(n.fx, 640 / (2 * Math.tan(35 * Math.PI / 180)));
});

test('pixelToCamera follows x right, y up, -z forward', () => {
  const i = { fx: 100, fy: 100, cx: 50, cy: 50 };
  const out = pixelToCamera(75, 25, 2, i, new Float32Array(3));
  near(out[0], 0.5); near(out[1], 0.5); near(out[2], -2);
});

test('mount height: reported wins, else nominal profile', () => {
  assert.equal(mountFor({}, {}).heightM, 0.12);
  assert.equal(mountFor({ camera_height_m: 0.4 }, {}).heightM, 0.4);
  assert.equal(mountFor({ camera_height_m: 9 }, {}).heightMeasured, false);
});

test('yolo pairing: frame id, close time, too old, not ready', () => {
  const depth = { frame_id: 'a', captured_at: 100 };
  assert.equal(yoloMatchesDepth({ state: 'ready', frame_id: 'a' }, depth).exact, true);
  assert.equal(yoloMatchesDepth({ state: 'ready', frame_id: 'b', captured_at: 100.15 }, depth).ok, true);
  assert.equal(yoloMatchesDepth({ state: 'ready', frame_id: 'b', captured_at: 101.5 }, depth).ok, false);
  assert.equal(yoloMatchesDepth({ state: 'stale', frame_id: 'a' }, depth).ok, false);
});

test('fillDepthCloud writes in place without allocating and respects calibration', () => {
  const w = 12, h = 9;
  const depth = { width: w, height: h, normalizedDepth: new Float32Array(w * h).fill(1), rawValues: new Float32Array(w * h).fill(50000) };
  const color = { width: w, height: h, pixels: new Uint8ClampedArray(w * h * 4).fill(255) };
  const grid = cloudGrid(w, h);
  const positions = new Float32Array(grid.count * 3), colors = new Float32Array(grid.count * 3);
  const intr = intrinsicsFor(w, h, {});
  let n = fillDepthCloud({ depth, color, grid, intrinsics: intr, calibration: null, heightM: 0.12, positions, colors });
  assert.equal(n, grid.count); near(positions[2], -0.7); near(colors[0], 1);
  const cal = { available: true, inverse_scale_per_relative_unit: 2e-5, inverse_offset_per_m: -0.5 };
  n = fillDepthCloud({ depth, color, grid, intrinsics: intr, calibration: cal, heightM: 0.12, positions, colors });
  near(positions[2], -1 / (2e-5 * 50000 - 0.5));
});

test('sampleDepthMeters: median of neighbours, calibrated flag', () => {
  const w = 5, h = 5;
  const d = new Float32Array(w * h).fill(0.5); d[12] = 1; // outlier at the centre
  const depth = { width: w, height: h, normalizedDepth: d };
  const out = sampleDepthMeters(depth, 0.5, 0.5, null);
  assert.equal(out.calibrated, false); near(out.meters, disparityToPriorMeters(0.5));
});

function makePng16(width, height, valueAt, filterFor = () => 0) {
  const rowBytes = width * 2, raw = Buffer.alloc((rowBytes + 1) * height);
  const pix = Buffer.alloc(rowBytes * height);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) pix.writeUInt16BE(valueAt(x, y), y * rowBytes + x * 2);
  for (let y = 0; y < height; y++) {
    const f = filterFor(y); raw[y * (rowBytes + 1)] = f;
    for (let x = 0; x < rowBytes; x++) {
      const cur = pix[y * rowBytes + x], left = x >= 2 ? pix[y * rowBytes + x - 2] : 0, up = y > 0 ? pix[(y - 1) * rowBytes + x] : 0;
      raw[y * (rowBytes + 1) + 1 + x] = (cur - (f === 0 ? 0 : f === 1 ? left : f === 2 ? up : 0)) & 255;
    }
  }
  const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const body = Buffer.concat([Buffer.from(type), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(zlib.crc32(body) >>> 0); return Buffer.concat([len, body, crc]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4); ihdr[8] = 16; ihdr[9] = 0;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

test('decodeGray16Png round-trips values with filters 0, 1 and 2', async () => {
  const f = y => y % 3;
  const png = makePng16(7, 6, (x, y) => 1000 + x * 4000 + y * 300, f);
  const image = await decodeGray16Png(png.toString('base64'));
  assert.equal(image.width, 7); assert.equal(image.height, 6);
  for (let y = 0; y < 6; y++) for (let x = 0; x < 7; x++) assert.equal(image.rawValues[y * 7 + x], 1000 + x * 4000 + y * 300);
  assert.ok(image.normalizedDepth.every(v => v >= 0 && v <= 1));
});
