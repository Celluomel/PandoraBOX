// Shared MiDaS depth -> 3D projection helpers used by the web viewer and the Quest VR viewer.
// Pure functions (no THREE dependency). decodeGray16Png needs DecompressionStream, atob and Blob.

export const DEPTH_PRIOR_NEAR_M = 0.7;
export const DEPTH_PRIOR_FAR_M = 5.5;
export const NOMINAL_HFOV_DEG = 70;
export const MAX_DETECTION_PAIR_DELTA_S = 0.2;
export const CALIBRATED_MIN_M = 0.2;
export const CALIBRATED_MAX_M = 15;

export const CAMERA_MOUNT_PROFILES = {
  low_body_front: { heightM: 0.12 },
  level_body_front: { heightM: 0.35 },
  high_body_front: { heightM: 0.65 },
};

const clamp01 = value => (value < 0 ? 0 : value > 1 ? 1 : value);

/** Uncalibrated depth: fixed inverse-depth prior. disparity01: 1 = nearest, 0 = farthest. */
export function disparityToPriorMeters(disparity01, nearM = DEPTH_PRIOR_NEAR_M, farM = DEPTH_PRIOR_FAR_M) {
  const d = clamp01(Number.isFinite(Number(disparity01)) ? Number(disparity01) : 0);
  const inverse = 1 / farM + d * (1 / nearM - 1 / farM);
  return 1 / inverse;
}

/** Calibrated depth from raw 16-bit MiDaS samples (midas_metric_calibration.v4, inverse_affine). */
export function rawDepthToMeters(raw, calibration) {
  if (!calibration?.available) return null;
  const inverse = Number(calibration.inverse_scale_per_relative_unit) * Number(raw)
    + Number(calibration.inverse_offset_per_m);
  if (!Number.isFinite(inverse) || inverse <= 0) return null;
  return Math.max(CALIBRATED_MIN_M, Math.min(CALIBRATED_MAX_M, 1 / inverse));
}

/** Camera intrinsics scaled to the depth image; nominal pinhole when none are supplied. */
export function intrinsicsFor(width, height, supplied = {}, hfovDeg = NOMINAL_HFOV_DEG) {
  const w = Math.max(1, Number(width) || 640);
  const h = Math.max(1, Number(height) || 480);
  const sourceWidth = Number(supplied.width || supplied.image_width || w);
  const sourceHeight = Number(supplied.height || supplied.image_height || h);
  const scaleX = w / sourceWidth;
  const scaleY = h / sourceHeight;
  const fx = Number(supplied.fx);
  const fy = Number(supplied.fy);
  if (fx > 0 && fy > 0 && Number.isFinite(Number(supplied.cx)) && Number.isFinite(Number(supplied.cy))) {
    return { fx: fx * scaleX, fy: fy * scaleY, cx: Number(supplied.cx) * scaleX, cy: Number(supplied.cy) * scaleY, calibrated: true };
  }
  const nominalFx = w / (2 * Math.tan((hfovDeg * Math.PI / 180) / 2));
  return { fx: nominalFx, fy: nominalFx, cx: (w - 1) / 2, cy: (h - 1) / 2, calibrated: false };
}

/** Writes a camera-frame point (x right, y up, -z forward) into out[offset..offset+2]. */
export function pixelToCamera(u, v, z, intrinsics, out, offset = 0) {
  out[offset] = ((u - intrinsics.cx) * z) / intrinsics.fx;
  out[offset + 1] = ((intrinsics.cy - v) * z) / intrinsics.fy;
  out[offset + 2] = -z;
  return out;
}

/** Camera mount height and pitch from reported values, else the nominal profile. */
export function mountFor(cameraFrame, depthFrame) {
  const profile = cameraFrame?.camera_profile || depthFrame?.camera_profile || 'low_body_front';
  const nominal = (CAMERA_MOUNT_PROFILES[profile] || CAMERA_MOUNT_PROFILES.low_body_front).heightM;
  const reported = Number(cameraFrame?.camera_height_m ?? cameraFrame?.calibration?.height_m ?? depthFrame?.camera_height_m);
  const heightMeasured = Number.isFinite(reported) && reported > 0 && reported < 3;
  const pitch = Number(cameraFrame?.camera_pitch_deg ?? cameraFrame?.calibration?.pitch_deg ?? depthFrame?.camera_pitch_deg);
  return { profile, heightM: heightMeasured ? reported : nominal, heightMeasured, pitchDeg: Number.isFinite(pitch) ? pitch : 0 };
}

/** A detection result is usable for a depth frame only if frame ids match or capture times are close. */
export function yoloMatchesDepth(yolo, depth, maxDeltaS = MAX_DETECTION_PAIR_DELTA_S) {
  if (!yolo || yolo.state !== 'ready' || !depth) return { ok: false, deltaS: null, exact: false };
  if (yolo.frame_id && depth.frame_id && String(yolo.frame_id) === String(depth.frame_id)) {
    return { ok: true, deltaS: 0, exact: true };
  }
  const yoloAt = Number(yolo.captured_at);
  const depthAt = Number(depth.captured_at);
  if (!Number.isFinite(yoloAt) || !Number.isFinite(depthAt)) return { ok: false, deltaS: null, exact: false };
  const deltaS = Math.abs(yoloAt - depthAt);
  return { ok: deltaS <= maxDeltaS, deltaS, exact: false };
}

/** Grid used for the point cloud: at most ~targetMax samples along the longer image side. */
export function cloudGrid(width, height, targetMax = 100) {
  const step = Math.max(3, Math.ceil(Math.max(width, height) / targetMax));
  const cols = Math.ceil(width / step);
  const rows = Math.ceil(height / step);
  return { step, cols, rows, count: cols * rows };
}

function disparityAt(depth, index) {
  if (depth.normalizedDepth) return depth.normalizedDepth[index];
  return depth.pixels ? depth.pixels[index * 4] / 255 : 0;
}

/** Depth in metres at normalised image coordinates; median of 3x3 to suppress noise. */
export function sampleDepthMeters(depth, u01, v01, calibration) {
  const x0 = Math.round(clamp01(u01) * (depth.width - 1));
  const y0 = Math.round(clamp01(v01) * (depth.height - 1));
  const disparities = [];
  const raws = [];
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      const x = Math.min(depth.width - 1, Math.max(0, x0 + dx));
      const y = Math.min(depth.height - 1, Math.max(0, y0 + dy));
      const index = y * depth.width + x;
      disparities.push(disparityAt(depth, index));
      if (depth.rawValues) raws.push(depth.rawValues[index]);
    }
  }
  const median = values => values.slice().sort((a, b) => a - b)[Math.floor(values.length / 2)];
  if (calibration?.available && raws.length) {
    const metres = rawDepthToMeters(median(raws), calibration);
    if (metres != null) return { meters: metres, calibrated: true };
  }
  return { meters: disparityToPriorMeters(median(disparities)), calibrated: false };
}

/**
 * Fills preallocated position/colour buffers (no allocation). Returns the number of points written.
 * depth: { width, height, normalizedDepth?, rawValues?, pixels? }, color: { width, height, pixels(RGBA) }.
 */
export function fillDepthCloud({ depth, color, grid, intrinsics, calibration, heightM, positions, colors }) {
  let n = 0;
  const colorScaleX = (color.width - 1) / Math.max(1, depth.width - 1);
  const colorScaleY = (color.height - 1) / Math.max(1, depth.height - 1);
  const useCalibration = Boolean(calibration?.available && depth.rawValues);
  for (let v = 0; v < depth.height; v += grid.step) {
    for (let u = 0; u < depth.width; u += grid.step) {
      if (n >= grid.count) return n;
      const index = v * depth.width + u;
      let z = null;
      if (useCalibration) z = rawDepthToMeters(depth.rawValues[index], calibration);
      if (z == null) z = disparityToPriorMeters(disparityAt(depth, index));
      const p = n * 3;
      positions[p] = ((u - intrinsics.cx) * z) / intrinsics.fx;
      positions[p + 1] = heightM + ((intrinsics.cy - v) * z) / intrinsics.fy;
      positions[p + 2] = -z;
      const cx = Math.min(color.width - 1, Math.round(u * colorScaleX));
      const cy = Math.min(color.height - 1, Math.round(v * colorScaleY));
      const ci = (cy * color.width + cx) * 4;
      colors[p] = color.pixels[ci] / 255;
      colors[p + 1] = color.pixels[ci + 1] / 255;
      colors[p + 2] = color.pixels[ci + 2] / 255;
      n++;
    }
  }
  return n;
}

/** Decodes the 16-bit grayscale PNG sent by the MiDaS worker (non-interlaced, color type 0). */
export async function decodeGray16Png(base64) {
  if (typeof DecompressionStream === 'undefined') throw new Error('PNG decompression is unavailable');
  const bytes = Uint8Array.from(atob(base64), char => char.charCodeAt(0));
  const signature = [137, 80, 78, 71, 13, 10, 26, 10];
  if (!signature.every((value, index) => bytes[index] === value)) throw new Error('Invalid PNG signature');
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let width = 0, height = 0, bitDepth = 0, colorType = -1, interlace = 0;
  const chunks = [];
  for (let offset = 8; offset + 12 <= bytes.length;) {
    const length = view.getUint32(offset);
    const type = String.fromCharCode(...bytes.subarray(offset + 4, offset + 8));
    const start = offset + 8, end = start + length;
    if (end + 4 > bytes.length) throw new Error('Truncated PNG chunk');
    if (type === 'IHDR') {
      width = view.getUint32(start); height = view.getUint32(start + 4);
      bitDepth = bytes[start + 8]; colorType = bytes[start + 9]; interlace = bytes[start + 12];
    } else if (type === 'IDAT') chunks.push(bytes.subarray(start, end));
    offset = end + 4;
    if (type === 'IEND') break;
  }
  if (!width || !height || bitDepth !== 16 || colorType !== 0 || interlace !== 0) {
    throw new Error('Expected non-interlaced 16-bit grayscale PNG');
  }
  const compressed = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.length, 0));
  let cursor = 0;
  for (const chunk of chunks) { compressed.set(chunk, cursor); cursor += chunk.length; }
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('deflate'));
  const scanlines = new Uint8Array(await new Response(stream).arrayBuffer());
  const rowBytes = width * 2;
  if (scanlines.length !== (rowBytes + 1) * height) throw new Error('Unexpected PNG scanline size');
  const decoded = new Uint8Array(rowBytes * height);
  const paeth = (a, b, c) => { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); return pa <= pb && pa <= pc ? a : pb <= pc ? b : c; };
  for (let y = 0; y < height; y++) {
    const filter = scanlines[y * (rowBytes + 1)];
    const source = y * (rowBytes + 1) + 1, target = y * rowBytes;
    for (let x = 0; x < rowBytes; x++) {
      const raw = scanlines[source + x], left = x >= 2 ? decoded[target + x - 2] : 0;
      const up = y > 0 ? decoded[target + x - rowBytes] : 0;
      const upperLeft = y > 0 && x >= 2 ? decoded[target + x - rowBytes - 2] : 0;
      const predictor = filter === 0 ? 0 : filter === 1 ? left : filter === 2 ? up
        : filter === 3 ? Math.floor((left + up) / 2) : filter === 4 ? paeth(left, up, upperLeft) : NaN;
      if (!Number.isFinite(predictor)) throw new Error(`Unsupported PNG filter ${filter}`);
      decoded[target + x] = (raw + predictor) & 255;
    }
  }
  const rawValues = new Float32Array(width * height);
  const histogram = new Uint32Array(65536);
  for (let i = 0; i < rawValues.length; i++) {
    const value = (decoded[i * 2] << 8) | decoded[i * 2 + 1];
    rawValues[i] = value; histogram[value]++;
  }
  const quantile = q => {
    const target = Math.floor((rawValues.length - 1) * q);
    let sum = 0;
    for (let i = 0; i < histogram.length; i++) { sum += histogram[i]; if (sum > target) return i; }
    return 65535;
  };
  const low = quantile(0.02), high = Math.max(low + 1, quantile(0.98));
  const normalizedDepth = new Float32Array(rawValues.length);
  for (let i = 0; i < rawValues.length; i++) normalizedDepth[i] = clamp01((rawValues[i] - low) / (high - low));
  return { width, height, rawValues, normalizedDepth };
}
