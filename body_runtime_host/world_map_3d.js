import * as THREE from '../frontend/node_modules/three/build/three.module.js';

const byId = (id) => document.getElementById(id);
const sourceStates = Object.create(null);
const staleAfterSeconds = { camera: 5, yolo: 5, midas: 5, odometry: 5, segmentation: 5, radar: 2, gps: 5, imu: 2, tof: 2 };
const physicalSources = ['camera', 'radar', 'gps', 'imu', 'tof', 'lidar', 'ultrasonic'];
const cameraRadarGeometry = { horizontalFovDeg: 70, yawOffsetDeg: 0, lateralOffsetM: 0, calibrated: false };
const maxCalibrationPairDeltaSeconds = 0.1;
const maxPersonBearingErrorDeg = 8;
function setFeedStatus(id, source, state, detail) {
  sourceStates[source] = state;
  const element = byId(id);
  if (element) {
    element.dataset.state = state;
    const stateLabel = state === 'live' ? 'LIVE' : state === 'stale' ? 'STALE' : state === 'offline' ? 'OFFLINE' : 'LOADING';
    element.textContent = detail.toUpperCase().startsWith(`${stateLabel} ·`) ? detail : `${stateLabel} · ${detail}`;
  }
  const tofCard = source === 'tof' ? element?.closest('.sensor-readout-card') : null;
  if (tofCard) {
    const offlinePill = document.querySelector('.world-map-offline-pill[data-source="tof"]');
    tofCard.hidden = state !== 'live';
    if (offlinePill) {
      offlinePill.hidden = state === 'live';
      const reason = offlinePill.querySelector('[data-offline-reason]');
      if (reason) reason.textContent = detail;
    }
  }
  const liveCount = physicalSources.filter(key => sourceStates[key] === 'live').length;
  const count = byId('world-map-summary-live');
  if (count) count.textContent = `${liveCount} / ${physicalSources.length}`;
}
const classifyAge = (source, age, available) => !available ? 'offline'
  : Number.isFinite(age) && age > staleAfterSeconds[source] ? 'stale' : 'live';
const sensorFetchFailures = new Set();
function setSensorFetchFailure(source, failed) {
  if (failed) sensorFetchFailures.add(source);
  else sensorFetchFailures.delete(source);
  const banner = byId('world-map-cloud-fetch');
  if (banner) banner.hidden = sensorFetchFailures.size === 0;
}
let latestSensorDepth = null;
let lastSensorDepthAt = 0;
let sensorDepthBusy = false;
let latestSensorYolo = null;
let cloudDepthYolo = null;
let latestSegmentation = null;
let latestCameraFrame = null;
let renderedSegmentationFrameId = '';
let displayedCameraFrameId = null;
let displayedYoloOverlayKey = '';
let cloudDepthImage = null;
let cloudBuildToken = 0;
let cloudBuildingKey = '';
let cloudSegmentationFrameId = '';
let metricDepthCalibration = null;
let depthCalibrationBusy = false;
let depthCalibrationMessage = '';
const visualOdometryTrail = [];
let visualOdometryFrameId = '';
let latestVisualOdometry = null;
let latestRadarSample = null;
let radarHistory = [];
let latestDepthCapturedAt = 0;
let imuHistory = [];
let cloudPointCount = 0;
let cloudLabelItems = [];

function imuAttitudeAt(timestamp, maxDelta = 0.2) {
  const target = Number(timestamp);
  if (!Number.isFinite(target)) return null;
  const samples = imuHistory.filter(sample => sample.attitude_valid
    && Number.isFinite(Number(sample.timestamp))
    && Number.isFinite(Number(sample.roll_deg))
    && Number.isFinite(Number(sample.pitch_deg)));
  if (!samples.length) return null;
  let before = null, after = null;
  for (const sample of samples) {
    const at = Number(sample.timestamp);
    if (at <= target && (!before || at > Number(before.timestamp))) before = sample;
    if (at >= target && (!after || at < Number(after.timestamp))) after = sample;
  }
  const angleDelta = (a, b) => ((b - a + 540) % 360) - 180;
  if (before && after && Number(after.timestamp) - Number(before.timestamp) <= 0.25) {
    const span = Number(after.timestamp) - Number(before.timestamp);
    const t = span > 0 ? (target - Number(before.timestamp)) / span : 0;
    const lerpAngle = (key) => Number(before[key]) + angleDelta(Number(before[key]), Number(after[key])) * t;
    return { roll_deg: lerpAngle('roll_deg'), pitch_deg: lerpAngle('pitch_deg'), timestamp: target };
  }
  const nearest = samples.reduce((best, sample) => !best
    || Math.abs(Number(sample.timestamp) - target) < Math.abs(Number(best.timestamp) - target) ? sample : best, null);
  return Math.abs(Number(nearest.timestamp) - target) <= maxDelta ? nearest : null;
}

function attitudeQuaternion(timestamp) {
  const attitude = imuAttitudeAt(timestamp);
  if (!attitude) return null;
  return new THREE.Quaternion().setFromEuler(new THREE.Euler(
    THREE.MathUtils.degToRad(Number(attitude.roll_deg)),
    THREE.MathUtils.degToRad(Number(attitude.pitch_deg)), 0, 'XYZ'));
}

function imuSampleAt(timestamp, maxDelta = 0.15) {
  const target = Number(timestamp);
  return imuHistory.reduce((best, sample) => {
    const age = Math.abs(Number(sample.timestamp) - target);
    return age <= maxDelta && (!best || age < best.age) ? { sample, age } : best;
  }, null)?.sample || null;
}

function radarSampleAt(timestamp, maxDelta = 0.1) {
  const target = Number(timestamp);
  return radarHistory.reduce((best, sample) => {
    const age = Math.abs(Number(sample.timestamp) - target);
    return age <= maxDelta && (!best || age < best.age) ? { sample, age } : best;
  }, null)?.sample || null;
}
const panel = document.querySelector('#view-worldmodel .map-panel');
if (panel) {
  const header = panel.querySelector('.panel-head');
  const mapLayout = panel.querySelector('.map-layout');
  const mapWrap = panel.querySelector('.map-wrap');
  const intro = panel.querySelector('.map-intro');
  if (header && mapLayout && mapWrap && !byId('world-map-source')) {
    const controls = document.createElement('div');
    controls.className = 'world-map-controls';
    controls.innerHTML = `<div class="world-map-segment" role="group" aria-label="Map rendering"><button type="button" data-render="2d" aria-pressed="true">2D</button><button type="button" data-render="3d" aria-pressed="false">3D</button></div><small id="world-map-state" role="status">Simulation · 2D</small>`;
    header.append(controls);
    const simCanvas = document.createElement('div');
    simCanvas.id = 'world-map-sim-3d';
    simCanvas.className = 'world-map-canvas';
    simCanvas.hidden = true;
    mapLayout.insertBefore(simCanvas, mapWrap);
    const sensorPanel = document.createElement('section');
    sensorPanel.id = 'world-map-sensor-view';
    sensorPanel.className = 'world-map-sensor-view';
    sensorPanel.hidden = true;
    sensorPanel.innerHTML = `<div class="world-map-sensor-metrics"><span>Camera <b id="world-map-camera-state">Waiting</b></span><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Visual odometry <b id="world-map-odometry-state">Waiting</b></span><span>SegFormer <b id="world-map-segmentation-state">disabled</b></span><span>Frame <b id="world-map-frame-state">—</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA · YOLOX</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS · RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate">Calibrate with radar</button><small id="world-map-midas-calibration-status" role="status">Relative depth only · not calibrated in metres</small></div></div></div><section class="world-map-odometry-view" aria-label="Experimental visual odometry trajectory"><div class="world-map-sensor-heading"><span>VISUAL ODOMETRY · LOCAL TRAJECTORY</span><small id="world-map-odometry-map-status">Waiting for tracking</small></div><div class="odom-plot"><canvas id="world-map-odometry-map" role="img" aria-label="Top-down estimated Body trajectory in the local visual odometry frame"></canvas><span class="odom-edge-label odom-forward">FORWARD ↑</span><span class="odom-edge-label odom-lateral">← LEFT · RIGHT →</span><span id="world-map-odometry-position" class="odom-position-label">0.00, 0.00 m</span></div><p class="world-map-odometry-footnote">Session-local estimate · drift accumulates · not a persistent map</p></section><section class="world-map-segmentation-panel" aria-label="SegFormer semantic segmentation"><div class="world-map-sensor-heading"><span>SEGFORMER · SEMANTIC MASK</span><small>Independent of camera preview</small></div><div class="world-map-segmentation-preview"><canvas id="world-map-segmentation-overlay" aria-label="Standalone SegFormer semantic class mask" hidden></canvas><span id="world-map-segmentation-empty" class="world-map-empty">Waiting for a SegFormer mask</span></div><div id="world-map-segmentation-classes" class="world-map-segmentation-classes">Waiting for SegFormer classes</div></section><div id="world-map-sensor-3d" class="world-map-sensor-cloud-layout" hidden><div id="world-map-sensor-3d-viewport" class="world-map-canvas world-map-sensor-cloud"><div class="world-map-cloud-hud"><span id="world-map-cloud-hud-points">0 points</span><span id="world-map-cloud-hud-depth">MiDaS —</span><span id="world-map-cloud-hud-age">Frame —</span><span id="world-map-cloud-hud-sync">Camera/depth —</span><span id="world-map-cloud-hud-fps">3D — FPS</span></div><div class="world-map-cloud-controls"><button type="button" data-cloud-action="reset" title="Reset camera to fit point cloud">Reset</button><button type="button" data-cloud-view="camera" title="Pinhole camera view; FOV is estimated unless intrinsics are provided">Camera</button><button type="button" data-cloud-view="top">Top</button><button type="button" data-cloud-view="side">Side</button><button type="button" data-cloud-view="follow">Follow</button><label>Point size <input id="world-map-cloud-point-size" type="range" min="10" max="50" value="25" aria-label="Point cloud point size"></label></div><div class="world-map-cloud-labels" aria-hidden="true"></div><div class="world-map-cloud-scale" hidden>1 m</div><div id="world-map-cloud-fetch" class="world-map-cloud-fetch" hidden>Sensor data unavailable: fetch failed, retrying</div></div><aside class="world-map-cloud-side"><strong>Scene layers</strong><label><input type="checkbox" data-cloud-layer="cloud" checked> MiDaS point cloud</label><label><input type="checkbox" data-cloud-layer="detections" checked> YOLOX detections</label><label><input type="checkbox" data-cloud-layer="radar" checked> mmWave targets (metres)</label><label><input type="checkbox" data-cloud-layer="odometry" checked> Odometry trail</label><strong>Depth units</strong><div class="world-map-depth-legend"><i></i><div><span>Near</span><span>Far</span></div></div><small id="world-map-cloud-depth-caption">Relative units · not metric</small><small>Radar markers use metres, independently scaled from an uncalibrated MiDaS cloud.</small><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate-3d">Calibrate with radar</button><small id="world-map-midas-calibration-status-3d" role="status">Relative depth only · not calibrated in metres</small></div><div class="world-map-cloud-axis" aria-label="XYZ orientation: X right, Y up, Z forward"><span>X →</span><span>Y ↑</span><span>Z ⊙</span></div></aside></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view · no simulation object positions are used.</p>`;
    sensorPanel.querySelector('[data-cloud-layer="radar"]').checked = true;
    sensorPanel.querySelector('#world-map-cloud-hud-fps').textContent = '3D — FPS';
    for (const id of ['world-map-camera-state', 'world-map-yolo-state', 'world-map-midas-state', 'world-map-odometry-state', 'world-map-segmentation-state', 'world-map-radar-state', 'world-map-gps-state', 'world-map-imu-state', 'world-map-tof-state']) {
      const state = byId(id);
      if (state) state.dataset.state = 'loading';
    }
    const liveReadouts = document.createElement('section');
    liveReadouts.id = 'world-map-live-readouts';
    liveReadouts.className = 'world-map-live-readouts';
    liveReadouts.innerHTML = `<article class="sensor-readout-card"><header><strong>mmWave · LD2450</strong><small id="world-map-radar-state">Waiting</small></header><canvas id="world-map-radar-plot" height="190" aria-label="Live mmWave target positions and radial velocities"></canvas><div id="world-map-radar-targets" class="sensor-target-list">Waiting for radar data.</div></article><article class="sensor-readout-card"><header><strong>GPS / GNSS · D0/D1</strong><small id="world-map-gps-state">Waiting</small></header><div class="sensor-readout-values"><span>Position<b id="world-map-gps-position">No fix</b></span><span>Fix / quality<b id="world-map-gps-fix">—</b></span><span>Satellites<b id="world-map-gps-satellites">— used · — in view</b></span><span>HDOP / altitude<b id="world-map-gps-quality">—</b></span></div><div id="world-map-gps-signals" class="sensor-gps-signals" role="img" aria-label="GPS satellite signal strength by satellite"></div></article><article class="sensor-readout-card"><header><strong>Modulino Movement · IMU</strong><small id="world-map-imu-state">Waiting</small></header><div id="world-map-imu-attitude" class="imu-attitude" role="img" aria-label="IMU attitude indicator based on roll and pitch"><div class="imu-attitude-disc" aria-hidden="true"><div class="imu-attitude-horizon"><span></span></div><i class="imu-attitude-mark"></i></div><div><b>ATTITUDE</b><small>Roll / pitch · no magnetic heading</small></div></div><div class="sensor-readout-values"><span>Roll<b id="world-map-imu-roll">—</b></span><span>Pitch<b id="world-map-imu-pitch">—</b></span><span>Yaw rate<b id="world-map-imu-yaw">—</b></span><span>Acceleration · g<b id="world-map-imu-accel">—</b></span><span>Angular rate · °/s<b id="world-map-imu-gyro">—</b></span></div><p class="sensor-readout-note">Six-axis IMU; yaw is relative angular rate, not a magnetic heading.</p></article><article class="sensor-readout-card"><header><strong>ToF · VL53L1X</strong><small id="world-map-tof-state">Waiting</small></header><div class="sensor-distance"><b id="world-map-tof-distance">—</b><span id="world-map-tof-meta">Forward single-beam range</span></div></article><article class="sensor-readout-card"><header><strong>LiDAR</strong><small id="world-map-lidar-state">No live source</small></header><p class="sensor-readout-note">No physical LiDAR stream is connected to this Body view. Any LiDAR volume shown in Simulation is virtual and is kept out of this live sensor view.</p></article><article class="sensor-readout-card"><header><strong>Ultrasonic · HC-SR04</strong><small id="world-map-ultrasonic-state">No live source</small></header><div class="sensor-readout-values sensor-range-channels"><span>Front-left<b id="world-map-ultrasonic-left">No data</b></span><span>Front-right<b id="world-map-ultrasonic-right">No data</b></span><span>Rear<b id="world-map-ultrasonic-rear">No data</b></span></div><p class="sensor-readout-note">Waiting for the ultrasonic firmware/gateway data channel; no simulated ranges are shown here.</p></article>`;
    const addSensorSubtitle = (stateId, source) => {
      const state = liveReadouts.querySelector(`#${stateId}`);
      const header = state?.closest('header');
      const title = header?.querySelector('strong');
      if (!state || !header || !title) return;
      const copy = document.createElement('div'); copy.className = 'sensor-heading-copy';
      title.title = source;
      const subtitle = document.createElement('span'); subtitle.className = 'sensor-card-source'; subtitle.textContent = source; subtitle.title = source;
      copy.append(title, subtitle);
      state.classList.add('sensor-state-chip');
      header.replaceChildren(copy, state);
    };
    addSensorSubtitle('world-map-radar-state', 'hlk_ld2450_ventuno_bridge');
    addSensorSubtitle('world-map-gps-state', 'Serial1 USART3 · D0/D1 via Ventuno STM32 Bridge');
    addSensorSubtitle('world-map-imu-state', 'Arduino Modulino Movement / LSM6DSOX');
    const computeCard = document.createElement('article');
    computeCard.id = 'world-map-compute-power';
    computeCard.className = 'sensor-readout-card world-map-compute-card';
    computeCard.innerHTML = `<header><strong>Compute & power</strong><small id="world-map-system-state">Sampling</small></header><div class="system-instrument-grid"><article class="system-instrument"><span class="system-instrument-label">CPU LOAD</span><div class="system-gauge" id="world-map-cpu-gauge" role="img" aria-label="CPU utilization"><div class="system-gauge-center"><strong id="world-map-system-cpu-value">—</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-cpu-temp">CPU temp · —</span></article><article class="system-instrument"><span class="system-instrument-label">CPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-cpu-temp-gauge" role="img" aria-label="Maximum CPU temperature"><div class="system-gauge-center"><strong id="world-map-system-cpu-temp-value">—</strong><small>°C</small></div></div><span class="system-instrument-foot">Hottest reported CPU sensor · 0–100 °C</span></article><article class="system-instrument"><span class="system-instrument-label">GPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-gpu-temp-gauge" role="img" aria-label="Maximum GPU temperature"><div class="system-gauge-center"><strong id="world-map-system-gpu-temp-value">—</strong><small>°C</small></div></div><span class="system-instrument-foot" id="world-map-system-gpu-meta">Load unavailable · — MHz</span></article><article class="system-instrument"><span class="system-instrument-label">MEMORY</span><div class="system-gauge" id="world-map-memory-gauge" role="img" aria-label="Memory utilization"><div class="system-gauge-center"><strong id="world-map-system-memory-value">—</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-memory-meta">— free</span></article><article class="system-instrument"><span class="system-instrument-label">BOARD INPUT</span><div class="system-gauge system-gauge-power" id="world-map-power-gauge" role="img" aria-label="Measured board input power"><div class="system-gauge-center"><strong id="world-map-system-power-value">—</strong><small>W</small></div></div><span class="system-instrument-foot" id="world-map-system-power-meta">INA232 · measured rail</span></article></div><div class="system-telemetry-strip"><div><span>GPU utilization</span><strong id="world-map-system-gpu-load">Unavailable</strong></div><div><span>GPU clock</span><strong id="world-map-system-gpu-clock">—</strong></div><div><span>Qualcomm HTP</span><strong id="world-map-system-htp">Waiting for inference status</strong></div><div><span>Energy since Body start</span><strong id="world-map-system-energy">—</strong></div></div><p id="world-map-system-note" class="sensor-readout-note">GPU/HTP usage percentages require kernel counters. Board input may exclude external motor loads.</p>`;
    sensorPanel.append(liveReadouts, computeCard);
    const visionGrid = sensorPanel.querySelector('.world-map-sensor-2d');
    const trajectory = sensorPanel.querySelector('.world-map-odometry-view');
    const segmentation = sensorPanel.querySelector('.world-map-segmentation-panel');
    const odometryCanvas = byId('world-map-odometry-map');
    if (odometryCanvas && typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(() => drawVisualOdometryMap()).observe(odometryCanvas.parentElement);
    }
    const visionFooter = document.createElement('div');
    visionFooter.className = 'world-map-vision-footer';
    visionFooter.append(sensorPanel.querySelector('#world-map-sensor-note'));
    visionGrid?.after(visionFooter);
    const radarCard = liveReadouts.querySelector('#world-map-radar-state')?.closest('.sensor-readout-card');
    radarCard?.classList.remove('sensor-readout-wide');
    if (trajectory) visionGrid?.append(trajectory);
    if (segmentation) visionGrid?.append(segmentation);
    const statusBar = document.createElement('div');
    statusBar.className = 'world-map-status-bar';
    statusBar.setAttribute('aria-label', 'Live Body and sensor status');
    statusBar.innerHTML = '<span>BODY <b id="world-map-body-status" data-state="loading">Connecting</b></span><span>BOARD INPUT <b id="world-map-summary-power">— W</b></span><span>ENERGY <b id="world-map-summary-energy">— Wh</b></span><span>LATEST FRAME <b id="world-map-summary-frame">—</b></span><span>SENSORS LIVE <b id="world-map-summary-live">0 / 7</b></span>';
    statusBar.append(sensorPanel.querySelector('#world-map-cloud-fetch'), sensorPanel.querySelector('.world-map-sensor-metrics'));
    sensorPanel.prepend(statusBar);
    const bodyMessage = document.querySelector('#message');
    const syncBodyStatus = () => {
      const text = bodyMessage?.textContent?.trim() || '';
      const connected = /connected/i.test(text) && !/disconnected|not connected/i.test(text);
      const target = byId('world-map-body-status');
      if (target) {
        target.textContent = text || 'Status unavailable';
        target.dataset.state = connected ? 'live' : text ? 'offline' : 'loading';
      }
    };
    if (bodyMessage) new MutationObserver(syncBodyStatus).observe(bodyMessage, { childList: true, characterData: true, subtree: true });
    syncBodyStatus();
    const offlineStrip = document.createElement('div');
    offlineStrip.className = 'world-map-offline-strip';
    offlineStrip.setAttribute('aria-label', 'Offline sensors');
    offlineStrip.innerHTML = '<strong>OFFLINE</strong>';
    const offlineState = (id, label, reason) => {
      const source = liveReadouts.querySelector(`#${id}`);
      const pill = document.createElement('span');
      pill.className = 'world-map-offline-pill';
      pill.title = reason;
      pill.innerHTML = `<b>${label}</b> <span>${reason}</span>`;
      if (source) {
        source.dataset.offlinePill = 'true';
        pill.prepend(source);
        source.dataset.state = 'offline';
        source.textContent = 'OFFLINE';
      }
      sourceStates[label === 'LiDAR' ? 'lidar' : 'ultrasonic'] = 'offline';
      offlineStrip.append(pill);
      return pill;
    };
    const lidarCard = liveReadouts.querySelector('#world-map-lidar-state')?.closest('.sensor-readout-card');
    const ultrasonicCard = liveReadouts.querySelector('#world-map-ultrasonic-state')?.closest('.sensor-readout-card');
    offlineState('world-map-lidar-state', 'LiDAR', 'No physical stream connected');
    offlineState('world-map-ultrasonic-state', 'HC-SR04', 'Waiting for firmware/gateway channel');
    const tofOfflinePill = document.createElement('span');
    tofOfflinePill.className = 'world-map-offline-pill';
    tofOfflinePill.dataset.source = 'tof';
    tofOfflinePill.innerHTML = '<b>ToF · VL53L1X</b> <span data-offline-reason>Sensor not detected</span>';
    offlineStrip.append(tofOfflinePill);
    const tofCard = liveReadouts.querySelector('#world-map-tof-state')?.closest('.sensor-readout-card');
    if (tofCard) {
      tofCard.hidden = true;
      tofCard.dataset.source = 'tof';
    }
    lidarCard?.remove();
    ultrasonicCard?.remove();
    const tofCardElement = liveReadouts.querySelector('#world-map-tof-state')?.closest('.sensor-readout-card');
    if (tofCardElement) tofCardElement.hidden = true;
    sensorPanel.append(offlineStrip);
    sensorPanel.querySelector('.world-map-segmentation-panel .world-map-sensor-heading small')?.remove();
    mapLayout.after(sensorPanel);
    const style = document.createElement('style');
    style.textContent = `
      .world-map-controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:10px 0 14px}
      .world-map-segment{display:inline-flex;border:1px solid #416b54;border-radius:4px;overflow:hidden}
      .world-map-segment button{border:0;border-radius:0;background:#101b16;padding:7px 12px;color:#a9c0b2}
      .world-map-segment button+button{border-left:1px solid #416b54}
      .world-map-segment button[aria-pressed="true"]{background:#1a3a29;color:#d9f5e5;box-shadow:inset 0 -2px #77d6a1}
      #world-map-state{color:#8eaa98;font:10px ui-monospace,monospace}
      .world-map-canvas{width:100%;height:clamp(300px,48vh,560px);min-height:280px;overflow:hidden;background:#07120f;border:1px solid #263e32;touch-action:none}
      .world-map-canvas canvas{display:block;width:100%;height:100%}
      .world-map-sensor-view[hidden],.world-map-canvas[hidden],.world-map-sensor-2d[hidden]{display:none!important}
      .map-layout[hidden],.map-layout>.map-wrap[hidden],.map-layout>.world-map-canvas[hidden]{display:none!important}
      .world-map-sensor-metrics{display:flex;gap:8px;flex-wrap:wrap;padding:10px 0;color:#64776c;font:10px ui-monospace,monospace}
      .world-map-sensor-metrics span{padding:6px 9px;border:1px solid #d7e1da;background:#f3f7f4}
      .world-map-sensor-metrics b{color:#183d2d;font-weight:650}
      .world-map-odometry-view{min-width:0;background:#07120f;border:1px solid #263e32}
      .world-map-odometry-view>.world-map-sensor-heading{display:flex;justify-content:space-between;gap:12px;align-items:center}
      .world-map-odometry-view>.world-map-sensor-heading small{color:#a9c0b2;font:10px ui-monospace,monospace}
      #world-map-odometry-map{display:block;width:100%;height:clamp(110px,13vh,150px);background:#07120f}
      .odom-map-bg{fill:#07120f}.odom-grid{fill:none;stroke:#254235;stroke-width:1}.odom-grid .odom-axis{stroke:#48745a;stroke-width:1.5}
      .odom-axis-label,.odom-empty-label{fill:#89a895;font:10px ui-monospace,monospace}.odom-position-label{fill:#dceee3;font:11px ui-monospace,monospace}
      #world-map-odometry-trail{fill:none;stroke:#42d6b1;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
      #world-map-odometry-start{fill:#edbd69;stroke:#07120f;stroke-width:2}#world-map-odometry-body path{fill:#75dfa2;stroke:#d9f5e5;stroke-width:1.5}
      .world-map-odometry-footnote{margin:0;padding:0 10px 9px;color:#89a895;font:10px ui-monospace,monospace}
      .world-map-sensor-2d{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:stretch}
      .world-map-analysis-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px;align-items:start}
      .world-map-analysis-stack{display:grid;min-width:0;gap:12px;align-content:start}
      .world-map-camera,.world-map-depth{min-width:0;position:relative;background:#07120f;border:1px solid #263e32;overflow:hidden}
      .world-map-sensor-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;min-width:0;padding:9px 11px;border-bottom:1px solid #263e32;color:#91c9aa;font:10px ui-monospace,monospace}
      .world-map-image-wrap{position:relative;display:grid;place-items:center;width:100%;aspect-ratio:4/3;max-height:500px;background:#020805;overflow:hidden}
      .world-map-image-wrap img{display:block;width:100%;height:100%;object-fit:fill}
      #world-map-yolo-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      .world-map-depth{display:flex;flex-direction:column}
      .world-map-segmentation-classes{display:flex;gap:7px 12px;flex-wrap:wrap;margin:0;padding:8px 10px;color:#b4c9bc;font:10px ui-monospace,monospace;line-height:1.6}
      .world-map-segmentation-classes span{display:inline-flex;align-items:center;gap:5px}
      .world-map-segmentation-classes i{width:8px;height:8px;flex:0 0 8px;border-radius:50%}
      .world-map-segmentation-panel{min-width:0;margin-top:12px;overflow:hidden;border:1px solid #263e32;background:#07120f}
      .world-map-segmentation-preview{position:relative;display:grid;width:100%;aspect-ratio:4/3;min-height:140px;justify-items:stretch;align-items:stretch;overflow:hidden;background:#020805}
      #world-map-segmentation-overlay{display:block;width:100%;height:100%;max-width:100%;object-fit:fill}
      #world-map-segmentation-overlay[hidden]{display:none!important}
      .world-map-depth img{display:block;width:100%;height:100%;min-height:220px;max-height:500px;object-fit:contain;background:#020805}
      .world-map-depth>small{padding:7px 10px;color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-depth-calibration{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:8px 10px;border-top:1px solid #263e32}
      .world-map-depth-calibration button{border:1px solid #416b54;border-radius:3px;background:#10251a;color:#d9f5e5;padding:7px 10px;cursor:pointer}
      .world-map-depth-calibration button:disabled{opacity:.6;cursor:wait}
      .world-map-depth-calibration small{color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-empty{position:absolute;inset:0;display:grid;place-items:center;padding:20px;color:#91a79a;font:11px ui-monospace,monospace;text-align:center;pointer-events:none}
      .world-map-empty[hidden]{display:none}
      .world-map-sensor-note{margin:0;color:#9aafc0;font:12px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-sensor-cloud-layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:16px;width:100%;margin-top:16px}
      .world-map-sensor-cloud-layout[hidden]{display:none!important}
      .world-map-sensor-cloud{position:relative;height:clamp(420px,60vh,720px);min-height:420px}
      .world-map-sensor-cloud.is-camera-view{width:min(100%,960px);height:auto;min-height:0;max-height:none;aspect-ratio:4/3;margin-inline:auto}
      .world-map-cloud-hud,.world-map-cloud-controls{position:absolute;z-index:3;display:flex;align-items:center;gap:8px;font:12px/1.3 ui-monospace,monospace}
      .world-map-cloud-hud{top:12px;left:12px;flex-wrap:wrap;max-width:55%;pointer-events:none}
      .world-map-cloud-hud span,.world-map-cloud-controls button,.world-map-cloud-controls label{padding:6px 8px;border:1px solid #263b50;border-radius:4px;background:#080e18ed;color:#e2edf5}
      .world-map-cloud-controls{top:54px;right:12px;flex-wrap:wrap;justify-content:flex-end;max-width:58%}
      .world-map-cloud-controls::before{content:"Shift/right drag: pan";padding:6px 8px;border:1px solid #263b50;border-radius:4px;background:#080e18ed;color:#9aafc0;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-controls button{cursor:pointer;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-controls button:hover{border-color:#00d6df}
      .world-map-cloud-controls label{display:flex;align-items:center;gap:6px}
      .world-map-cloud-controls input{width:72px;accent-color:#00d6df}
      .world-map-cloud-labels{position:absolute;inset:0;z-index:2;overflow:hidden;pointer-events:none}
      .world-map-cloud-object-label{position:absolute;max-width:180px;transform:translate(-50%,-100%);padding:4px 7px;border:1px solid #7290a3;border-radius:4px;background:#05070df2;color:#f4f8fb;font:12px/1.2 ui-sans-serif,system-ui,sans-serif;white-space:nowrap;text-shadow:0 1px #000}
      .world-map-cloud-object-label::after{position:absolute;top:100%;left:50%;height:9px;border-left:1px solid #a9c6d6;content:""}
      .world-map-cloud-radar-dot{position:absolute;width:16px;height:16px;transform:translate(-50%,-50%);border:2px solid #fff;border-radius:50%;background:#f2bc65;box-shadow:0 0 0 4px #f2bc6566,0 0 16px 5px #f2bc65;z-index:4}
      .world-map-cloud-radar-dot.is-moving{background:#ed35c5;box-shadow:0 0 0 4px #ed35c566,0 0 16px 5px #ed35c5}
      .world-map-cloud-radar-dot.is-ego-motion{background:#c9d4db;box-shadow:0 0 0 4px #c9d4db66,0 0 16px 5px #c9d4db}
      .world-map-cloud-scale{position:absolute;z-index:3;bottom:16px;left:16px;width:72px;border-top:2px solid #d7eaf4;color:#d7eaf4;text-align:center;font:12px ui-monospace,monospace}
      .world-map-cloud-scale[hidden]{display:none}
      .world-map-cloud-fetch{position:absolute;z-index:4;right:12px;bottom:12px;padding:7px 10px;border:1px solid #9f493c;border-radius:4px;background:#351510ed;color:#ffd6cc;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-status-bar .world-map-cloud-fetch{position:static;z-index:auto;order:8;flex-basis:100%;padding:7px 10px}
      .world-map-cloud-side{display:flex;min-width:0;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-text);font:14px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-side>strong{padding-bottom:8px;border-bottom:1px solid var(--wm-border);font-size:14px}
      .world-map-cloud-side label{display:flex;align-items:center;gap:8px;min-height:30px;color:var(--wm-muted)}
      .world-map-cloud-side input{accent-color:#00d6df}
      .world-map-depth-legend{display:grid;gap:6px}
      .world-map-depth-legend>i{height:12px;border-radius:2px;background:linear-gradient(90deg,#ed35c5,#4836d9,#00b8d4,#75e45b,#f8cb36,#ef4d27)}
      .world-map-depth-legend>div{display:flex;justify-content:space-between;color:var(--wm-muted);font-size:12px}
      .world-map-cloud-side small{color:var(--wm-muted);font-size:12px}
      .world-map-cloud-side .world-map-depth-calibration{display:grid;gap:8px;padding-top:10px;border-top:1px solid var(--wm-border)}
      .world-map-cloud-side .world-map-depth-calibration button{justify-self:start;padding:8px 10px;border:1px solid #126d76;border-radius:6px;background:#102b36;color:#bdf9f3;cursor:pointer;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-side .world-map-depth-calibration button:disabled{cursor:wait;opacity:.65}
      .world-map-cloud-axis{display:flex;gap:10px;margin-top:auto;padding-top:10px;border-top:1px solid var(--wm-border);color:#9cdce1;font:12px ui-monospace,monospace}
      @media(max-width:1100px){.world-map-sensor-cloud-layout{grid-template-columns:minmax(0,1fr)}.world-map-cloud-side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.world-map-cloud-side>strong,.world-map-cloud-axis{grid-column:1/-1}}
      @media(max-width:700px){.world-map-cloud-hud,.world-map-cloud-controls{position:static;max-width:none;padding:6px;background:#05070d}.world-map-cloud-controls{justify-content:flex-start}.world-map-cloud-hud{padding-top:8px}.world-map-cloud-side{grid-template-columns:minmax(0,1fr)}}
      .world-map-live-readouts{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:12px;margin-top:14px}
      .sensor-readout-card{min-width:0;padding:14px;border:1px solid #d7e1da;background:#f7faf8;color:#1c2b22}
      .sensor-readout-card header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-bottom:9px;border-bottom:1px solid #d7e1da}
      .sensor-readout-card header strong{font:650 12px ui-monospace,monospace;color:#1b4734}
      .sensor-readout-card header small{font:10px ui-monospace,monospace;color:#5a7063;text-align:right}
      .sensor-readout-wide{grid-column:1/-1}
      #world-map-radar-plot{display:block;width:100%;height:145px;margin-top:8px;background:#07120f;border:1px solid #203b2d}
      .sensor-target-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0 16px;color:#40574a;font:11px ui-monospace,monospace}
      .sensor-target-row{display:flex;justify-content:space-between;gap:12px;padding:8px 2px;border-top:1px solid #d7e1da}
      .sensor-readout-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 16px;padding:12px 0}
      .sensor-readout-values span{min-width:0;color:#63766b;font-size:10px}
      .sensor-readout-values b{display:block;margin-top:4px;color:#183d2d;font:600 12px ui-monospace,monospace;overflow-wrap:anywhere}
      .sensor-gps-signals{display:flex;align-items:flex-end;gap:8px;min-height:94px;overflow:auto;padding:8px 0 2px;border-top:1px solid #d7e1da}
      .sensor-gps-bar{flex:0 0 34px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;height:80px;color:#40574a;font:9px ui-monospace,monospace}
      .sensor-gps-bar i{display:block;width:15px;min-height:3px;border-radius:2px 2px 0 0}
      .sensor-distance{display:grid;gap:6px;padding:18px 0 8px}
      .sensor-distance b{font:650 30px ui-monospace,monospace;color:#183d2d}
      .sensor-distance span,.sensor-readout-note{color:#64776c;font-size:10px;line-height:1.5}
      .sensor-readout-note{margin:0}
      .system-instrument-grid{display:grid;grid-template-columns:repeat(5,minmax(112px,1fr));gap:12px;padding:14px 0}
      .system-instrument{display:flex;min-width:0;flex-direction:column;align-items:center;gap:8px;padding:12px 8px 10px;border:1px solid #d7e1da;background:#fff}
      .system-instrument-label{color:#526b5d;font:650 9px ui-monospace,monospace;letter-spacing:.08em}
      .system-gauge{--gauge-value:0;--gauge-color:#16855d;display:grid;width:92px;aspect-ratio:1;place-items:center;border-radius:50%;background:conic-gradient(from -90deg,var(--gauge-color) calc(var(--gauge-value)*1%),#e2eae5 0);position:relative}
      .system-gauge::before{position:absolute;inset:6px;border-radius:50%;background:#fff;content:""}
      .system-gauge-center{z-index:1;display:flex;align-items:baseline;gap:3px;color:#183d2d;font-family:ui-monospace,monospace}
      .system-gauge-center strong{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums}
      .system-gauge-center small{color:#63766b;font-size:10px}
      .system-gauge-temp{--gauge-color:#d58b32}
      .system-gauge-power{--gauge-color:#1787a0}
      .system-instrument-foot{min-height:24px;color:#63766b;font:9px/1.35 ui-monospace,monospace;text-align:center}
      .system-telemetry-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid #d7e1da;border-bottom:1px solid #d7e1da}
      .system-telemetry-strip>div{display:grid;gap:5px;min-width:0;padding:10px 12px;border-right:1px solid #d7e1da}
      .system-telemetry-strip>div:last-child{border-right:0}
      .system-telemetry-strip span{color:#63766b;font-size:9px}
      .system-telemetry-strip strong{color:#183d2d;font:650 11px ui-monospace,monospace;overflow-wrap:anywhere}
      .sensor-range-channels span{padding:8px;border:1px solid #d7e1da;background:#fff}
      #worldmodel-live-sensor-panels .map-panel{margin-bottom:14px}
      #worldmodel-live-sensor-panels .map-layout{min-height:0}
      #worldmodel-live-sensor-panels .map-intro{max-width:100ch;line-height:1.55}
      .world-map-sensor-view{--wm-gap:16px;--wm-section-gap:24px;container-type:inline-size;margin-top:12px}
      body.worldmodel-sensors-active .simulation-actions,
      body.worldmodel-sensors-active #view-worldmodel #wm-simulation-toggle,
      body.worldmodel-sensors-active #view-worldmodel .map-panel .panel-head>button[onclick="expandMap()"]{display:none!important}
      body.worldmodel-sensors-active #view-worldmodel>.stats,body.worldmodel-sensors-active #goal-success{display:none!important}
      @media(max-width:760px){.system-instrument-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip>div:nth-child(2){border-right:0}.system-telemetry-strip>div:nth-child(-n+2){border-bottom:1px solid #d7e1da}}
      @container (max-width:760px){.world-map-sensor-2d,.world-map-analysis-grid,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-analysis-grid{grid-template-columns:minmax(0,1fr)}.world-map-depth img{max-height:320px}}
      @media(max-width:700px){.world-map-sensor-2d,.world-map-analysis-grid,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-depth img{max-height:320px}.world-map-controls{gap:7px}}
      body.worldmodel-sensors-active,body.worldmodel-sensors-active #view-worldmodel,body.worldmodel-sensors-active #worldmodel-live-sensor-panels,body.worldmodel-sensors-active #view-worldmodel .shell{background:#05070d!important;color:#e2edf5!important}
      body.worldmodel-sensors-active #page-title,body.worldmodel-sensors-active #page-description,body.worldmodel-sensors-active #view-worldmodel h2,body.worldmodel-sensors-active #view-worldmodel .map-intro,body.worldmodel-sensors-active header.topbar .eyebrow{color:#e2edf5!important}
      body.worldmodel-sensors-active #page-description,body.worldmodel-sensors-active #view-worldmodel .map-intro,body.worldmodel-sensors-active header.topbar .eyebrow{color:#a9b9c8!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs{border-color:#263b50!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button{color:#a9b9c8!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button.active,body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button[aria-selected="true"]{color:#00d6df!important}
      body.worldmodel-sensors-active #view-worldmodel .world-map-status-bar{top:0}
      body.worldmodel-sensors-active .world-map-sensor-metrics{flex:1 1 420px;max-width:100%;flex-wrap:nowrap;gap:4px 9px;padding:0;margin-left:auto;overflow:hidden}
      body.worldmodel-sensors-active .world-map-sensor-metrics span{display:flex;min-width:0;gap:4px;padding:0;border:0;background:transparent;color:#9aafc0;font-size:11px;white-space:nowrap}
      body.worldmodel-sensors-active .world-map-sensor-metrics span:has(#world-map-frame-state){display:none}
      body.worldmodel-sensors-active .world-map-sensor-metrics b{max-width:112px;overflow:hidden;color:#e2edf5;text-overflow:ellipsis;white-space:nowrap}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="offline"]{color:#ff7373!important}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="stale"]{color:#ffb547!important}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="live"]{color:#39e59a!important}
      body.worldmodel-sensors-active .sensor-readout-card:has(.sensor-state-chip[data-state="stale"]) .sensor-readout-values,body.worldmodel-sensors-active .sensor-readout-card:has(.sensor-state-chip[data-state="stale"]) canvas{opacity:.55}
      body.worldmodel-sensors-active .world-map-live-readouts{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}
      body.worldmodel-sensors-active .system-gauge-center strong{font-size:15px!important}
      body.worldmodel-sensors-active .system-gauge{width:88px}
      body.worldmodel-sensors-active .system-gauge::after{right:-15px}
      body.worldmodel-sensors-active .sensor-readout-values b{overflow-wrap:normal;white-space:nowrap}
      body.worldmodel-sensors-active #world-map-gps-signals{overflow:hidden;scrollbar-width:none}
      body.worldmodel-sensors-active #world-map-gps-signals::-webkit-scrollbar{display:none}
      body.worldmodel-sensors-active #view-worldmodel>.stats,body.worldmodel-sensors-active #goal-success{display:none!important}
      body.worldmodel-sensors-active #view-worldmodel .shell{max-width:1680px;padding:76px 24px 24px}
      .world-map-sensor-view{--wm-bg:#05070d;--wm-surface:#0a0f1a;--wm-raised:#101b29;--wm-border:#263b50;--wm-text:#e2edf5;--wm-muted:#9aafc0;--wm-cyan:#00d6df;--wm-magenta:#ed35c5;color:var(--wm-text);margin-top:8px}
      .world-map-status-bar{position:sticky;top:0;z-index:8;scroll-margin-top:76px;display:flex;align-items:center;gap:clamp(14px,2.5vw,36px);flex-wrap:wrap;padding:10px 16px;margin:0 -2px 14px;border:1px solid var(--wm-border);border-radius:8px;background:rgba(5,7,13,.98);box-shadow:0 6px 18px #02060a44}
      .world-map-status-bar>span{display:grid;gap:3px;color:var(--wm-muted);font:12px/1.2 ui-sans-serif,system-ui,sans-serif}
      .world-map-status-bar b{color:var(--wm-text);font:600 14px/1.2 ui-monospace,monospace;font-variant-numeric:tabular-nums}
      [data-state="live"], [data-state="ready"]{color:#39e59a!important}[data-state="stale"]{color:#ffb547!important}[data-state="offline"]{color:#91a0ad!important}[data-state="loading"]{color:#68cfe0!important}
      .world-map-sensor-metrics{gap:8px;padding:8px 0 12px;color:var(--wm-muted);font:12px ui-monospace,monospace}
      .world-map-sensor-metrics span{padding:6px 9px;border:1px solid var(--wm-border);border-radius:6px;background:var(--wm-surface);color:var(--wm-muted)}
      .world-map-sensor-metrics b{color:var(--wm-text)}
      .world-map-sensor-2d{grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--wm-gap);align-items:stretch}
      .world-map-camera,.world-map-depth,.world-map-odometry-view,.world-map-segmentation-panel,.sensor-readout-card,.system-instrument{border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-text)}
      .world-map-camera,.world-map-depth,.world-map-odometry-view,.world-map-segmentation-panel{display:flex;flex-direction:column;min-width:0;aspect-ratio:4/3;overflow:hidden}
      .world-map-sensor-heading,.sensor-readout-card header{min-height:42px;padding:10px 12px;border-bottom:1px solid var(--wm-border);background:var(--wm-raised);color:var(--wm-cyan);font:600 12px/1.25 ui-sans-serif,system-ui,sans-serif}
      .world-map-sensor-heading small,.sensor-readout-card header small{color:var(--wm-muted);font:12px ui-monospace,monospace}
      .world-map-image-wrap,.world-map-segmentation-preview{width:100%;flex:1;aspect-ratio:auto;max-height:none;min-height:0;background:#02060a}
      .world-map-image-wrap img{object-fit:contain}
      .world-map-depth img{width:100%;height:0;flex:1;min-height:0;max-height:none;aspect-ratio:auto;object-fit:cover;background:#02060a}
      .world-map-depth-calibration{margin-top:auto;border-top:1px solid var(--wm-border)}
      .world-map-depth-calibration small,.world-map-odometry-footnote,.world-map-empty,.world-map-sensor-note{color:var(--wm-muted);font:12px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-depth-calibration button{border-color:#126d76;border-radius:6px;background:#102b36;color:#bdf9f3}
      .world-map-segmentation-panel{margin:0}
      .world-map-segmentation-preview{display:grid;flex:1}
      #world-map-segmentation-overlay{width:100%;height:100%;object-fit:cover}
      .world-map-segmentation-classes{gap:8px 14px;padding:10px 12px;color:var(--wm-muted);font:12px/1.5 ui-sans-serif,system-ui,sans-serif;border-top:1px solid var(--wm-border)}
      .world-map-vision-footer{grid-column:1/-1;padding:10px 12px;border-top:1px solid var(--wm-border);background:var(--wm-surface)}
      .world-map-vision-footer{margin-top:12px}
      .world-map-odometry-view{justify-content:flex-start}
      .odom-plot{position:relative;flex:1;min-height:0;background:#050b12}
      #world-map-odometry-map{display:block;width:100%;height:100%;background:#050b12}
      .odom-edge-label,.odom-position-label{position:absolute;z-index:1;color:#a9c2d0;font:12px ui-monospace,monospace;pointer-events:none}
      .odom-forward{top:8px;left:50%;transform:translateX(-50%)}
      .odom-lateral{bottom:8px;left:50%;transform:translateX(-50%)}
      .odom-position-label{top:8px;right:10px;padding:5px 7px;border-radius:4px;background:#0a0f1ae8;color:#00e2dd;font-size:12px;white-space:nowrap}
      .world-map-odometry-footnote{padding:8px 12px 10px;color:var(--wm-muted);font:12px/1.4 ui-sans-serif,system-ui,sans-serif}
      .world-map-live-readouts{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:var(--wm-gap);margin-top:var(--wm-section-gap);align-items:stretch}
      .world-map-compute-card{margin-top:var(--wm-section-gap)}
      .sensor-readout-card{display:flex;min-width:0;min-height:100%;flex-direction:column;padding:0 12px 12px}
      .sensor-readout-card[hidden],.world-map-offline-pill[hidden]{display:none!important}
      .sensor-readout-card header{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:10px;margin:0 -12px 8px;padding:8px 12px}
      .sensor-heading-copy{display:grid;min-width:0;gap:2px}
      .sensor-readout-card header strong{overflow:hidden;color:var(--wm-text);font:600 14px/1.25 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      .sensor-card-source{overflow:hidden;color:var(--wm-muted);font:12px/1.3 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      .sensor-readout-card header .sensor-state-chip{max-width:140px;overflow:hidden;padding:4px 7px;border:1px solid var(--wm-border);border-radius:999px;background:#0a0f1a;font:12px/1.2 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      #world-map-radar-plot{display:block;width:100%;height:auto;min-height:160px;flex:1;aspect-ratio:2/1;background:#050b12;border:1px solid var(--wm-border);border-radius:5px}
      .sensor-target-list{grid-template-columns:1fr;color:var(--wm-text);font:12px ui-monospace,monospace}
      .sensor-target-row{border-color:var(--wm-border)}
      .sensor-readout-values span,.sensor-distance span,.sensor-readout-note{color:var(--wm-muted);font-size:12px;line-height:1.45}
      .sensor-readout-values b{color:var(--wm-text);font:600 13px ui-monospace,monospace;white-space:nowrap}
      .sensor-readout-values span{display:grid;gap:4px;align-content:start}
      .sensor-gps-signals{display:grid;grid-template-columns:repeat(auto-fill,minmax(38px,1fr));align-items:end;gap:6px;min-height:100px;overflow:hidden;border-color:var(--wm-border)}
      .sensor-gps-bar{width:auto;height:84px;color:var(--wm-muted);font:12px ui-monospace,monospace}
      .sensor-gps-bar small{font-size:12px}
      .sensor-gps-more{align-self:center;justify-self:center;color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      .sensor-distance b{color:var(--wm-text);font-size:26px}
      .world-map-offline-strip{display:flex;align-items:center;gap:8px 14px;flex-wrap:wrap;margin-top:10px;padding:10px 12px;border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-offline-strip>strong{color:#91a0ad;font-size:12px}
      .world-map-offline-pill{display:inline-flex;align-items:center;gap:7px;padding:5px 8px;border:1px solid var(--wm-border);border-radius:5px;background:#080f17}
      .world-map-offline-pill b{color:var(--wm-text)}.world-map-offline-pill>span{color:var(--wm-muted)}
      .system-instrument-grid{grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;padding:12px 0}
      .system-instrument{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:12px 10px}
      .system-instrument-label{color:var(--wm-muted);font:600 12px ui-sans-serif,system-ui,sans-serif;text-align:center}
      .system-gauge{position:relative;width:88px;flex:none;background:conic-gradient(from -90deg,var(--gauge-color) calc(var(--gauge-value)*1%),#253544 0)}
      .system-gauge::before{inset:7px;background:var(--wm-surface)}
      .system-gauge::after{position:absolute;right:-17px;top:50%;transform:translateY(-50%);color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      #world-map-cpu-gauge::after,#world-map-memory-gauge::after{content:"%"}
      #world-map-cpu-temp-gauge::after,#world-map-gpu-temp-gauge::after{content:"°C"}
      #world-map-power-gauge::after{content:"W"}
      .system-gauge-center{align-items:center;justify-content:center;gap:0;color:var(--wm-text)}
      .system-gauge-center strong{font-size:16px}.system-gauge-center small{display:none}
      .system-instrument-foot{min-height:0;color:var(--wm-muted);font:12px/1.35 ui-sans-serif,system-ui,sans-serif;text-align:center}
      .imu-attitude{display:flex;align-items:center;justify-content:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--wm-border)}
      .imu-attitude-disc{position:relative;width:72px;aspect-ratio:1;overflow:hidden;flex:none;border:2px solid var(--wm-cyan);border-radius:50%;background:#10243a}
      .imu-attitude-horizon{position:absolute;left:-30%;top:-55%;width:160%;height:210%;transform:translateY(var(--imu-pitch,0px)) rotate(var(--imu-roll,0deg));background:linear-gradient(to bottom,#1747a3 0 50%,#69432f 50% 100%)}
      .imu-attitude-horizon span{position:absolute;left:0;right:0;top:50%;height:2px;background:#e0bc78}
      .imu-attitude-mark{position:absolute;left:50%;top:50%;width:25px;height:2px;transform:translate(-50%,-50%);background:#f3f7fb;box-shadow:0 0 0 2px #0b1420}
      .imu-attitude b{display:block;color:var(--wm-muted);font:600 12px ui-sans-serif,system-ui,sans-serif}
      .imu-attitude small{display:block;color:var(--wm-muted);font:12px/1.4 ui-sans-serif,system-ui,sans-serif}
      .system-telemetry-strip{border-color:var(--wm-border)}
      .system-telemetry-strip>div{border-color:var(--wm-border)}
      .system-telemetry-strip span{color:var(--wm-muted);font-size:12px}
      .system-telemetry-strip strong{color:var(--wm-text);font:600 13px ui-monospace,monospace}
      #world-map-system-note{padding:8px 0 0;color:#c3d2dc;font-size:12px}
      .sensor-range-channels span{border-color:var(--wm-border);background:#080f17}
      .world-map-calibration-guide{width:min(880px,calc(100vw - 32px));max-height:min(92vh,1000px);padding:0;border:1px solid #263b50;border-radius:8px;background:#0a0f1a;color:#e2edf5;box-shadow:0 24px 80px #000b}
      .world-map-calibration-guide::backdrop{background:#02060acc;backdrop-filter:blur(3px)}
      .world-map-calibration-guide__surface{display:grid;gap:14px;padding:20px;overflow:auto;max-height:min(92vh,1000px);font:14px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-calibration-guide header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:12px;border-bottom:1px solid #263b50}
      .world-map-calibration-guide h2{margin:0;color:#e2edf5;font-size:22px;line-height:1.2}
      .world-map-calibration-kicker{margin:0 0 5px;color:#00d6df;font-size:12px;font-weight:650}
      .world-map-calibration-close{width:36px;height:36px;border:1px solid #344a5e;border-radius:6px;background:#101b29;color:#e2edf5;font-size:22px;cursor:pointer}
      .world-map-calibration-intro{margin:0;color:#c3d2dc}
      .world-map-calibration-stages{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin:0;padding-left:24px}
      .world-map-calibration-stages li{padding:8px 10px;border-left:2px solid #263b50;background:#080e17}
      .world-map-calibration-stages li:nth-child(6){border-color:#00d6df;background:#0b1a22}
      .world-map-calibration-stages b,.world-map-calibration-stages span{display:block}
      .world-map-calibration-stages b{margin-bottom:3px;color:#e2edf5;font-size:14px}
      .world-map-calibration-stages span{color:#a9b9c8;font-size:12px}
      .world-map-calibration-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
      .world-map-calibration-checks label{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border:1px solid #263b50;border-radius:5px;color:#c3d2dc;font-size:12px}
      .world-map-calibration-checks input{margin-top:2px;accent-color:#00d6df}
      .world-map-calibration-caution{margin:0;padding:10px 12px;border-left:3px solid #ffb547;background:#201a0e;color:#f0d7a6;font-size:12px}
      .world-map-calibration-progress{min-height:20px;margin:0;color:#9aafc0;font:12px ui-monospace,monospace}
      .world-map-calibration-guide footer{display:flex;justify-content:flex-end;gap:8px;padding-top:12px;border-top:1px solid #263b50}
      .world-map-calibration-guide footer button{padding:9px 13px;border:1px solid #344a5e;border-radius:5px;background:#101b29;color:#e2edf5;font:600 14px ui-sans-serif,system-ui,sans-serif;cursor:pointer}
      .world-map-calibration-guide footer .primary{border-color:#087d86;background:#07535d;color:#e8ffff}
      @media(max-width:680px){.world-map-calibration-stages,.world-map-calibration-checks{grid-template-columns:minmax(0,1fr)}.world-map-calibration-guide__surface{padding:14px}}
      @media(max-width:980px){.world-map-live-readouts{grid-template-columns:repeat(2,minmax(0,1fr))}.system-instrument-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
      @media(max-width:640px){.world-map-sensor-2d,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-status-bar{position:static;gap:12px}.system-instrument-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.world-map-controls{gap:7px}}
    `;
    document.head.append(style);
  }
}

const material = (color, opacity = 1) => new THREE.MeshStandardMaterial({
  color, roughness: 0.82, metalness: 0.02, transparent: opacity < 1, opacity,
});
const colors = {
  target: '#efa678', chair: '#83b3d5', table: '#d3bd67',
  obstacle: '#a77ba5', mobile_obstacle: '#db83bf', object: '#a9c4b2',
};

function makeRenderer(element, background = '#07120f') {
  if (!element) return null;
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'low-power' });
  } catch (error) {
    element.textContent = `3D rendering unavailable: ${error.message}`;
    return null;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor(background, 1);
  element.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);
  const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 200);
  scene.add(new THREE.HemisphereLight('#d7f4e4', '#14231c', 2));
  const key = new THREE.DirectionalLight('#e4fff0', 2.2);
  key.position.set(-4, 10, 6);
  scene.add(key);
  const resize = () => {
    const width = Math.max(1, element.clientWidth);
    const height = Math.max(1, element.clientHeight);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(element);
  resize();
  let pointer = null;
  element.addEventListener('contextmenu', event => event.preventDefault());
  element.addEventListener('pointerdown', (event) => {
    pointer = { x: event.clientX, y: event.clientY, pan: event.button === 2 || event.shiftKey };
    camera.userData.userAdjusted = true;
    element.setPointerCapture(event.pointerId);
  });
  element.addEventListener('pointermove', (event) => {
    if (!pointer) return;
    const dx = event.clientX - pointer.x;
    const dy = event.clientY - pointer.y;
    pointer.x = event.clientX; pointer.y = event.clientY;
    const target = camera.userData.target || new THREE.Vector3();
    if (pointer.pan) {
      const scale = camera.position.distanceTo(target) * 0.0018;
      const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0);
      const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1);
      const shift = right.multiplyScalar(-dx * scale).add(up.multiplyScalar(dy * scale));
      camera.position.add(shift); target.add(shift); camera.userData.target = target;
    } else {
      const spherical = new THREE.Spherical().setFromVector3(camera.position.clone().sub(target));
      spherical.theta -= dx * 0.006;
      spherical.phi = THREE.MathUtils.clamp(spherical.phi + dy * 0.006, 0.12, Math.PI - 0.12);
      camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(target));
    }
    camera.lookAt(target);
    render();
  });
  element.addEventListener('pointerup', () => { pointer = null; });
  element.addEventListener('pointercancel', () => { pointer = null; });
  element.addEventListener('wheel', (event) => {
    event.preventDefault();
    camera.userData.userAdjusted = true;
    const target = camera.userData.target || new THREE.Vector3();
    const direction = camera.position.clone().sub(target);
    direction.multiplyScalar(THREE.MathUtils.clamp(1 + event.deltaY * 0.001, 0.82, 1.2));
    camera.position.copy(target).add(direction);
    render();
  }, { passive: false });
  const render = () => renderer.render(scene, camera);
  return { renderer, scene, camera, render, resize, observer };
}

const sim = makeRenderer(byId('world-map-sim-3d'));
let simRoot;
let simSignature = '';
let cloud = makeRenderer(byId('world-map-sensor-3d-viewport'), '#05070d');
let cloudPoints = null;
let boxGroup = null;
let cloudDetectionKey = '';
let cloudFrameId = '';
let cloudCameraInitialized = false;
let cloudCameraPlane = null;
let cloudCameraPlaneToken = 0;
let cloudPairedCameraFrameId = '';
let cloudRadarRenderKey = '';
const cloudGuides = new THREE.Group();
const cloudOriginGroup = new THREE.Group();
let cloudOriginStem = null;
let cloudCameraMountMarker = null;
let cloudOriginKey = '';
const cloudRadarGroup = new THREE.Group();
const cloudOdometryGroup = new THREE.Group();
if (cloud) {
  const positions = [], colors = [];
  for (let index = -10; index <= 10; index += 1) {
    const color = new THREE.Color(index % 5 === 0 ? '#426078' : '#23394a');
    positions.push(index, 0, 1, index, 0, -15, -10, 0, -4 + index, 10, 0, -4 + index);
    for (let vertex = 0; vertex < 4; vertex += 1) colors.push(color.r, color.g, color.b);
  }
  const grid = new THREE.BufferGeometry();
  grid.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  grid.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  cloudGuides.add(new THREE.LineSegments(grid, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.78 })));
  cloudOriginStem = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0.18, 0)]),
    new THREE.LineBasicMaterial({ color: '#9aafc0', transparent: true, opacity: 0.8 }),
  );
  cloudGuides.add(cloudOriginStem);
  cloudCameraMountMarker = new THREE.Mesh(new THREE.SphereGeometry(0.022, 12, 8), new THREE.MeshBasicMaterial({ color: '#62f1c1' }));
  cloudGuides.add(cloudCameraMountMarker);
  cloudOriginGroup.add(new THREE.Mesh(new THREE.SphereGeometry(0.025, 16, 10), new THREE.MeshBasicMaterial({ color: '#f4f7ff' })));
  const addAxis = (to, color) => {
    const direction = new THREE.Vector3(...to).normalize();
    cloudOriginGroup.add(new THREE.ArrowHelper(direction, new THREE.Vector3(), 0.2, color, 0.045, 0.028));
  };
  addAxis([1, 0, 0], '#ef6a73'); addAxis([0, 1, 0], '#62d994'); addAxis([0, 0, -1], '#66a8ff');
  const scale = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-0.5, 0.03, -2), new THREE.Vector3(0.5, 0.03, -2)]);
  cloudGuides.add(new THREE.Line(scale, new THREE.LineBasicMaterial({ color: '#d7eaf4' })));
  cloud.scene.add(cloudGuides, cloudOriginGroup, cloudRadarGroup, cloudOdometryGroup);
}
const cloudViewport = byId('world-map-sensor-3d-viewport');
cloudViewport?.querySelector('.world-map-cloud-axis span:last-child')?.replaceChildren('Z− · forward');
const cloudLabelRoot = cloudViewport?.querySelector('.world-map-cloud-labels');
let cloudFpsFrames = 0;
let cloudFpsStartedAt = performance.now();
if (cloud) {
  const baseRender = cloud.render;
  let lastCloudHudUpdate = 0;
  cloud.render = () => {
    baseRender();
    cloudFpsFrames += 1;
    updateCloudLabelPositions();
    const now = performance.now();
    if (now - lastCloudHudUpdate >= 500) {
      updateCloudHud();
      lastCloudHudUpdate = now;
    }
  };
  cloudViewport?.querySelector('[data-cloud-action="reset"]')?.addEventListener('click', () => { cloudViewport.classList.remove('is-camera-view'); cloud.camera.fov = 42; cloud.camera.userData.userAdjusted = false; cloudCameraInitialized = false; cloud.resize(); updateCloudHud(); updateCloudRadar(); updateCloudOdometry(); resizeCloud(); });
  cloudViewport?.querySelectorAll('[data-cloud-view]').forEach(button => button.addEventListener('click', () => setCloudPreset(button.dataset.cloudView)));
  cloudViewport?.querySelectorAll('[data-cloud-layer]').forEach(input => input.addEventListener('change', () => {
    const layer = input.dataset.cloudLayer;
    if (layer === 'cloud' && cloudPoints) cloudPoints.visible = input.checked;
    if (layer === 'detections') {
      if (boxGroup) boxGroup.visible = input.checked;
      if (input.checked && cloudDepthImage) drawDepthDetections(cloudDepthImage, latestSensorYolo || cloudDepthYolo);
    }
    if (layer === 'radar') updateCloudRadar(latestRadarSample, true);
    if (layer === 'odometry') cloudOdometryGroup.visible = input.checked;
    cloud.render();
  }));
  byId('world-map-cloud-point-size')?.addEventListener('input', event => { if (cloudPoints) cloudPoints.material.size = Number(event.target.value) / 1000; cloud.render(); });
}
let lastSensorCloudRenderAt = 0;
function animateSensorCloud(now) {
  if (activeSource === 'sensors' && activeRender === '3d' && cloud
      && now - lastSensorCloudRenderAt >= 1000 / 30) {
    lastSensorCloudRenderAt = now;
    cloud.render();
  }
  requestAnimationFrame(animateSensorCloud);
}
requestAnimationFrame(animateSensorCloud);
let activeSource = window.bodyWorldModelView === 'sensors' ? 'sensors' : 'simulation';
let activeRender = '2d';
let latestWorld = null;
let sensorBusy = false;
let sensorSegmentationBusy = false;

function makeFloor(scene, width, height) {
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(width, height), material('#0d1b15'));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.03;
  scene.add(floor);
  const grid = new THREE.GridHelper(Math.max(width, height), Math.ceil(Math.max(width, height) * 2), '#4e8d69', '#294c3a');
  grid.position.y = 0.005;
  scene.add(grid);
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(width, 0.08, height)), new THREE.LineBasicMaterial({ color: '#70b28a', transparent: true, opacity: 0.72 }));
  outline.position.y = 0.01;
  scene.add(outline);
}

function objectGeometry(item) {
  const kind = String(item.kind || 'object').toLowerCase();
  const size = Math.max(0.25, Math.min(2.2, Number(item.size) || 0.6));
  if (kind.includes('chair')) return new THREE.BoxGeometry(size * 1.15, 0.8, size * 1.05);
  if (kind.includes('table')) return new THREE.BoxGeometry(size * 1.6, 0.72, size * 1.4);
  if (kind.includes('obstacle')) return new THREE.CylinderGeometry(size * 0.52, size * 0.62, 1.15, 18);
  if (kind === 'target' || kind.includes('cup')) return new THREE.CylinderGeometry(size * 0.34, size * 0.42, 0.48, 18);
  return new THREE.BoxGeometry(size, Math.max(0.35, size), size);
}

function makeLabel(text, color = '#d8eee1') {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 96;
  const context = canvas.getContext('2d');
  context.font = '600 42px ui-monospace, monospace';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillStyle = '#06100de8';
  context.fillRect(0, 10, canvas.width, canvas.height - 20);
  context.fillStyle = color;
  context.fillText(String(text).slice(0, 32), canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(1.65, 0.31, 1);
  return sprite;
}

function buildSimulation(world) {
  if (!sim) return;
  const p = world?.perception || {};
  const state = world?.sim || {};
  const isSim = world?.mode === 'sim';
  const fallbackObjects = Object.entries(state.objects || {}).map(([id, item]) => ({
    id, label: id.replaceAll('_', ' '), kind: item.kind,
    position: [item.x, item.y, 0], size: id === 'cup' ? 0.4 : 0.8,
  }));
  const objects = isSim ? fallbackObjects : (Array.isArray(p.objects) ? p.objects : fallbackObjects);
  const body = isSim ? (state.body || [0, 0, 0]) : (p.body?.position || state.body || [0, 0, 0]);
  const width = Math.max(2, Number(state.width) || 12);
  const height = Math.max(2, Number(state.height) || 12);
  const shelf = state.shelf || [1, 9];
  const heading = isSim ? Number(state.heading_deg || 0) * Math.PI / 180 : Number(p.body?.orientation || 0);
  const signature = JSON.stringify([width, height, shelf, body, heading, objects.map((item) => [item.id, item.kind, item.position, item.size])]);
  if (signature === simSignature) return;
  simSignature = signature;
  if (simRoot) {
    sim.scene.remove(simRoot);
    simRoot.traverse((node) => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach((entry) => entry.dispose());
      else node.material?.dispose();
    });
  }
  simRoot = new THREE.Group();
  makeFloor(simRoot, width, height);
  const goal = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.035, 32), new THREE.MeshBasicMaterial({ color: '#79d8a0', transparent: true, opacity: 0.32 }));
  goal.position.set(Number(shelf[0]) - width / 2, 0.02, -(Number(shelf[1]) - height / 2));
  simRoot.add(goal);
  const goalLabel = makeLabel('GOAL', '#b9f5ce');
  goalLabel.position.set(goal.position.x, 0.35, goal.position.z);
  simRoot.add(goalLabel);
  const robot = new THREE.Group();
  robot.position.set(Number(body[0]) - width / 2, 0, -(Number(body[1]) - height / 2));
  const robotMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 0.32, 24), material('#8ee5b1'));
  robotMesh.position.y = 0.2;
  robot.add(robotMesh);
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.38, 16), material('#d8ffe5'));
  nose.rotation.z = -Math.PI / 2;
  nose.position.set(0.38, 0.24, 0);
  robot.add(nose);
  robot.rotation.y = -heading;
  simRoot.add(robot);
  const bodyLabel = makeLabel('BODY', '#b6f1d3');
  bodyLabel.position.set(robot.position.x, 0.82, robot.position.z);
  simRoot.add(bodyLabel);
  for (const item of objects) {
    const position = item.position || [0, 0, 0];
    const kind = String(item.kind || 'object').toLowerCase();
    const color = colors[kind] || colors.object;
    const mesh = new THREE.Mesh(objectGeometry(item), material(color, kind.includes('mobile') ? 0.92 : 1));
    const baseY = kind.includes('obstacle') ? 0.58 : kind === 'table' || kind === 'chair' ? 0.38 : 0.25;
    mesh.position.set(Number(position[0]) - width / 2, baseY, -(Number(position[1]) - height / 2));
    simRoot.add(mesh);
    const marker = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.025, 10), new THREE.MeshBasicMaterial({ color }));
    marker.position.set(mesh.position.x, 0.035, mesh.position.z);
    simRoot.add(marker);
    const label = makeLabel(item.label || item.kind || 'OBJECT', color);
    label.position.set(mesh.position.x, baseY + 0.86, mesh.position.z);
    simRoot.add(label);
  }
  sim.scene.add(simRoot);
  const target = new THREE.Vector3(0, 0, 0);
  sim.camera.userData.target = target;
  const distance = Math.max(width, height) * 1.3;
  if (!sim.camera.userData.userAdjusted) {
    sim.camera.position.set(0, distance * 0.62, distance);
    sim.camera.lookAt(target);
  }
  sim.render();
}

function setSource(source) {
  activeSource = source;
  const sensor = byId('world-map-sensor-view');
  const mapLayout = panel?.querySelector('.map-layout');
  if (sensor) sensor.hidden = source !== 'sensors';
  if (mapLayout) mapLayout.hidden = source === 'sensors';
  const expand = panel?.querySelector('.panel-head button[onclick="expandMap()"]');
  if (expand) expand.hidden = source === 'sensors';
  const title = panel?.querySelector('.panel-head h2');
  if (title) title.textContent = source === 'sensors' ? 'Live sensor observatory' : 'Simulation · world ground truth';
  panel?.querySelector('.map-intro')?.replaceChildren(document.createTextNode(source === 'sensors'
    ? 'Live hardware and perception feeds only. No simulator positions, virtual LiDAR returns or synthetic objects are included.'
    : 'Synthetic room, robot pose and object positions for controlled testing. These are simulation ground truth, not live sensor measurements.'));
  panel?.querySelector('.truth-note')?.toggleAttribute('hidden', source === 'sensors');
  document.querySelectorAll('.simulation-actions').forEach((node) => { node.hidden = source === 'sensors'; });
  if (source === 'sensors') void refreshSensors();
  else if (latestWorld) buildSimulation(latestWorld);
  updateMode();
}

function setRender(render) {
  activeRender = render;
  const mapWrap = panel?.querySelector('.map-wrap');
  const simCanvas = byId('world-map-sim-3d');
  const sensor2d = byId('world-map-sensor-2d');
  const sensor3d = byId('world-map-sensor-3d');
  if (activeSource === 'simulation') {
    if (mapWrap) mapWrap.hidden = render !== '2d';
    if (simCanvas) simCanvas.hidden = render !== '3d';
    if (mapWrap) mapWrap.classList.toggle('is-3d', render === '3d');
    if (latestWorld && render === '3d') requestAnimationFrame(() => { sim?.resize(); buildSimulation(latestWorld); sim?.render(); });
  } else {
    if (sensor2d) sensor2d.hidden = render !== '2d';
    if (sensor3d) sensor3d.hidden = render !== '3d';
    if (render === '3d') requestAnimationFrame(() => {
      resizeCloud();
      if (cloudDepthImage) drawDepthDetections(cloudDepthImage, latestSensorYolo || cloudDepthYolo);
      cloud?.render();
    });
  }
  document.querySelectorAll('[data-render]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.render === render)));
  updateMode();
}

function updateMode() {
  const state = byId('world-map-state');
  if (state) state.textContent = `${activeSource === 'simulation' ? 'Simulation' : 'Live sensors'} · ${activeRender.toUpperCase()}`;
  const mapWrap = panel?.querySelector('.map-wrap');
  const simCanvas = byId('world-map-sim-3d');
  if (mapWrap && simCanvas && activeSource === 'simulation') {
    mapWrap.hidden = activeRender !== '2d';
    simCanvas.hidden = activeRender !== '3d';
  }
}

window.addEventListener('body-worldmodel-viewchange', (event) => setSource(event.detail?.view === 'sensors' ? 'sensors' : 'simulation'));
window.addEventListener('resize', () => {
  if (activeSource === 'sensors' && activeRender === '3d') requestAnimationFrame(resizeCloud);
});
document.querySelectorAll('[data-render]').forEach((button) => button.addEventListener('click', () => setRender(button.dataset.render)));
byId('world-map-midas-calibrate')?.addEventListener('click', openDepthCalibrationGuide);
byId('world-map-midas-calibrate-3d')?.addEventListener('click', openDepthCalibrationGuide);
void loadMetricCalibration();
setSource(window.bodyWorldModelView === 'sensors' ? 'sensors' : 'simulation');

function drawBoxes(detections, width, height) {
  const svg = byId('world-map-yolo-overlay');
  svg.replaceChildren();
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  for (const item of detections || []) {
    const box = item.bbox;
    if (!Array.isArray(box) || box.length < 4) continue;
    const [x1, y1, x2, y2] = box.map(Number);
    if (![x1, y1, x2, y2].every(Number.isFinite)) continue;
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', String(x1 * width));
    rect.setAttribute('y', String(y1 * height));
    rect.setAttribute('width', String(Math.max(0, x2 - x1) * width));
    rect.setAttribute('height', String(Math.max(0, y2 - y1) * height));
    rect.setAttribute('fill', 'none');
    rect.setAttribute('stroke', '#62f1c1');
    rect.setAttribute('stroke-width', String(Math.max(width, height) * 0.004));
    svg.append(rect);
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', String(x1 * width));
    label.setAttribute('y', String(Math.max(16, y1 * height - 5)));
    label.setAttribute('fill', '#dffff1');
    label.setAttribute('font-size', String(Math.max(12, width * 0.026)));
    label.setAttribute('font-family', 'ui-monospace, monospace');
    label.setAttribute('paint-order', 'stroke');
    label.setAttribute('stroke', '#07120f');
    label.setAttribute('stroke-width', String(Math.max(2, width * 0.004)));
    label.textContent = `${item.label || item.class_name || item.class || 'object'} ${Math.round(Number(item.confidence || item.score || 0) * 100)}%`;
    svg.append(label);
  }
}

function visibleYoloDetections(yolo) {
  const age = Number(yolo?.captured_at) > 0 ? Date.now() / 1000 - Number(yolo.captured_at) : Infinity;
  return yolo?.state === 'ready' && age >= 0 && age <= 2.5 ? yolo.detections || [] : [];
}

function setImage(image, empty, base64, mime = 'image/jpeg') {
  if (base64) {
    image.src = `data:${mime};base64,${base64}`;
    image.hidden = false;
    empty.hidden = true;
  } else {
    image.removeAttribute('src');
    image.hidden = true;
    empty.hidden = false;
  }
}

async function renderSemanticMask(segmentation) {
  const canvas = byId('world-map-segmentation-overlay');
  const classes = byId('world-map-segmentation-classes');
  const empty = byId('world-map-segmentation-empty');
  if (!canvas || !classes || !empty) return;
  const mask = segmentation?.mask_png_base64;
  const frameId = String(segmentation?.frame_id || '');
  const maskKey = frameId || String(segmentation?.captured_at || '');
  if (!segmentation?.available || !mask) {
    canvas.hidden = true;
    empty.hidden = false;
    empty.textContent = `${segmentation?.state === 'disabled' ? 'Enable SegFormer in Camera settings' : `SegFormer ${segmentation?.state || 'waiting'}`}${segmentation?.error ? ` · ${segmentation.error}` : ''}`;
    classes.textContent = 'No semantic classes available';
    renderedSegmentationFrameId = '';
    return;
  }
  if (maskKey === renderedSegmentationFrameId) {
    canvas.hidden = false;
    empty.hidden = true;
    return;
  }
  const image = new Image();
  image.src = `data:image/png;base64,${mask}`;
  try { await image.decode(); } catch { return false; }
  if (maskKey !== String(latestSegmentation?.frame_id || latestSegmentation?.captured_at || '')) return;
  const source = document.createElement('canvas');
  source.width = image.naturalWidth;
  source.height = image.naturalHeight;
  const sourceContext = source.getContext('2d', { willReadFrequently: true });
  sourceContext.drawImage(image, 0, 0);
  const sourcePixels = sourceContext.getImageData(0, 0, source.width, source.height).data;
  canvas.width = source.width;
  canvas.height = source.height;
  const context = canvas.getContext('2d');
  const pixels = context.createImageData(canvas.width, canvas.height);
  const palette = new Map();
  for (let index = 0; index < sourcePixels.length; index += 4) {
    const classId = sourcePixels[index];
    if (!palette.has(classId)) {
      const hex = semanticColor(classId).getHexString();
      palette.set(classId, [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)]);
    }
    const color = palette.get(classId);
    pixels.data[index] = color[0];
    pixels.data[index + 1] = color[1];
    pixels.data[index + 2] = color[2];
    pixels.data[index + 3] = sourcePixels[index + 3];
  }
  context.putImageData(pixels, 0, 0);
  canvas.hidden = false;
  empty.hidden = true;
  renderedSegmentationFrameId = maskKey;
  const labels = (segmentation.classes || []).slice(0, 7).map(item => {
    const entry = document.createElement('span');
    const swatch = document.createElement('i');
    swatch.style.backgroundColor = `#${semanticColor(item.id).getHexString()}`;
    entry.append(swatch, `${item.label} ${Math.round(Number(item.ratio || 0) * 100)}%`);
    return entry;
  });
  classes.replaceChildren(...labels);
  if (!labels.length) classes.textContent = 'Mask available';
}

function segmentationMatchesFrame(segmentation, frame) {
  if (!segmentation?.available || !segmentation.mask_png_base64 || !frame?.image_base64) return false;
  if (segmentation.frame_id && frame.frame_id && segmentation.frame_id === frame.frame_id) return true;
  const segmentationTime = Number(segmentation.captured_at);
  const frameTime = Number(frame.captured_at);
  if (!Number.isFinite(segmentationTime) || !Number.isFinite(frameTime)) return false;
  const maskAge = frameTime - segmentationTime;
  return maskAge >= -0.25 && maskAge <= 2.5;
}

function relativeDepthToMeters(relativeDepth, calibration = metricDepthCalibration) {
  if (!calibration?.available) return relativeDepth;
  const inverseRange = Number(calibration.inverse_scale_per_relative_unit) * relativeDepth
    + Number(calibration.inverse_offset_per_m);
  if (!Number.isFinite(inverseRange) || inverseRange <= 0) return null;
  const meters = 1 / inverseRange;
  return Math.max(0.2, Math.min(15, meters));
}

function metricDepthEstimate(relativeDepth, calibration = metricDepthCalibration) {
  if (!calibration?.available) return null;
  const inverseRange = Number(calibration.inverse_scale_per_relative_unit) * relativeDepth
    + Number(calibration.inverse_offset_per_m);
  if (!Number.isFinite(inverseRange) || inverseRange <= 0) return null;
  const meters = 1 / inverseRange;
  if (!Number.isFinite(meters) || meters < 0.2 || meters > 15) return null;
  const range = calibration.calibrated_relative_range || [];
  const lo = Math.min(Number(range[0]), Number(range[1]));
  const hi = Math.max(Number(range[0]), Number(range[1]));
  return { meters, extrapolated: !Number.isFinite(lo) || !Number.isFinite(hi) || relativeDepth < lo || relativeDepth > hi };
}

function depthValueAt(image, pixelIndex) {
  const normalized = image.values[pixelIndex] / 255;
  if (Number.isFinite(image.rawMin) && Number.isFinite(image.rawMax)) {
    return image.rawMin + normalized * (image.rawMax - image.rawMin);
  }
  return normalized;
}

function depthForScene(image, pixelIndex, calibration) {
  const raw = depthValueAt(image, pixelIndex);
  const hasRawRange = Number.isFinite(image.rawMin) && Number.isFinite(image.rawMax);
  if (calibration?.available && hasRawRange) {
    const calibrated = relativeDepthToMeters(raw, calibration);
    if (Number.isFinite(calibrated)) return calibrated;
  }
  // MiDaS worker already percentile-normalizes grayscale depth; do not remap it
  // against a second, temporally smoothed frame histogram.
  const normalizedDepth = image.normalizedValues?.[pixelIndex] ?? image.values[pixelIndex];
  const disparity = THREE.MathUtils.clamp(normalizedDepth / 255, 0, 1);
  return 1 / THREE.MathUtils.lerp(1 / 8, 1 / 0.7, disparity);
}

function cameraIntrinsicsForImage(image) {
  const supplied = latestCameraFrame?.intrinsics || latestCameraFrame?.camera_intrinsics
    || latestSensorDepth?.intrinsics || latestSensorDepth?.camera_intrinsics || {};
  const width = Math.max(1, Number(image?.width) || 640);
  const height = Math.max(1, Number(image?.height) || 480);
  const sourceWidth = Number(supplied.width || supplied.image_width || width);
  const sourceHeight = Number(supplied.height || supplied.image_height || height);
  const scaleX = width / sourceWidth, scaleY = height / sourceHeight;
  const fx = Number(supplied.fx), fy = Number(supplied.fy);
  if (fx > 0 && fy > 0 && Number.isFinite(Number(supplied.cx)) && Number.isFinite(Number(supplied.cy))) {
    return { fx: fx * scaleX, fy: fy * scaleY, cx: Number(supplied.cx) * scaleX, cy: Number(supplied.cy) * scaleY, calibrated: true };
  }
  const nominalFx = width / (2 * Math.tan(THREE.MathUtils.degToRad(cameraRadarGeometry.horizontalFovDeg) / 2));
  return { fx: nominalFx, fy: nominalFx, cx: (width - 1) / 2, cy: (height - 1) / 2, calibrated: false };
}

function cameraPoint(u, v, z, intrinsics) {
  return new THREE.Vector3((u - intrinsics.cx) * z / intrinsics.fx,
    (intrinsics.cy - v) * z / intrinsics.fy, -z);
}

const cameraMountProfiles = {
  low_body_front: { heightM: 0.12 },
  level_body_front: { heightM: 0.35 },
  high_body_front: { heightM: 0.65 },
};

function cameraMountPose() {
  const profile = latestCameraFrame?.camera_profile || 'low_body_front';
  const mount = cameraMountProfiles[profile] || cameraMountProfiles.low_body_front;
  const reportedHeight = Number(latestCameraFrame?.camera_height_m
    ?? latestCameraFrame?.calibration?.height_m
    ?? latestSensorDepth?.camera_height_m);
  const heightM = Number.isFinite(reportedHeight) && reportedHeight > 0 && reportedHeight < 3
    ? reportedHeight : mount.heightM;
  const reportedPitch = Number(latestCameraFrame?.camera_pitch_deg
    ?? latestCameraFrame?.calibration?.pitch_deg
    ?? latestSensorDepth?.camera_pitch_deg);
  const elevationDeg = Number.isFinite(reportedPitch) ? reportedPitch : 0;
  const rotation = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0),
    THREE.MathUtils.degToRad(elevationDeg));
  return { profile, heightM, rotation, position: new THREE.Vector3(0, heightM, 0) };
}

function updateCloudOrigin(timestamp = latestDepthCapturedAt) {
  if (!cloud) return;
  const mount = cameraMountPose();
  const attitude = attitudeQuaternion(timestamp);
  cloudOriginGroup.quaternion.copy(attitude || new THREE.Quaternion());
  const reportedHeight = Number(latestCameraFrame?.camera_height_m
    ?? latestCameraFrame?.calibration?.height_m
    ?? latestSensorDepth?.camera_height_m);
  const heightIsMeasured = Number.isFinite(reportedHeight) && reportedHeight > 0;
  const key = `${mount.profile}:${mount.heightM}:${heightIsMeasured}`;
  if (key === cloudOriginKey) return;
  cloudOriginKey = key;
  cloudOriginGroup.position.set(0, mount.heightM, 0);
  if (cloudOriginStem) cloudOriginStem.scale.y = mount.heightM / 0.18;
  if (cloudCameraMountMarker) cloudCameraMountMarker.position.copy(mount.position);
  setCloudLayerLabels('origin', [{
    position: mount.position.clone(),
    text: `BODY SENSOR ORIGIN · ${mount.heightM.toFixed(2)} m above floor${heightIsMeasured ? '' : ' nominal'}`,
  }]);
  setCloudLayerLabels('camera-mount', [{
    position: mount.position.clone(),
    text: `CAMERA MOUNT · ${mount.profile.replace(/_/g, ' ')} · ${mount.heightM.toFixed(2)} m${heightIsMeasured ? '' : ' nominal'}`,
  }]);
}

updateCloudOrigin();

function bodyPointToScene(point, timestamp = latestDepthCapturedAt) {
  const origin = new THREE.Vector3(0, cameraMountPose().heightM, 0);
  const attitude = attitudeQuaternion(timestamp);
  const relativePoint = point.clone();
  if (attitude) relativePoint.applyQuaternion(attitude);
  return relativePoint.add(origin);
}

function cameraPointInBodyFrame(point, timestamp = latestDepthCapturedAt) {
  const mount = cameraMountPose();
  return bodyPointToScene(point.clone().applyQuaternion(mount.rotation), timestamp);
}

function applyCameraProjection() {
  if (!cloud || !cloudDepthImage) return;
  const intrinsics = cameraIntrinsicsForImage(cloudDepthImage);
  const width = cloudDepthImage.width, height = cloudDepthImage.height;
  const near = cloud.camera.near, far = cloud.camera.far;
  cloud.camera.projectionMatrix.makePerspective(
    -intrinsics.cx * near / intrinsics.fx,
    (width - intrinsics.cx) * near / intrinsics.fx,
    intrinsics.cy * near / intrinsics.fy,
    -(height - intrinsics.cy) * near / intrinsics.fy,
    near, far,
  );
  cloud.camera.projectionMatrixInverse.copy(cloud.camera.projectionMatrix).invert();
}

async function cameraFrameForDepth(depth) {
  if (!depth?.frame_id) return null;
  try {
    const response = await fetch(`/body/camera/yolo-frame?frame_id=${encodeURIComponent(depth.frame_id)}`, { cache: 'no-store' });
    if (!response.ok) return null;
    const result = await response.json();
    const frame = result.camera || {};
    return result.available && frame.frame_id === depth.frame_id && frame.image_base64 ? frame : null;
  } catch (error) {
    console.warn('Could not load camera pixels paired with MiDaS frame:', error);
    return null;
  }
}

async function yoloResultForDepth(depth) {
  if (latestSensorYolo?.frame_id === depth?.frame_id) return latestSensorYolo;
  if (!Number.isFinite(Number(depth?.captured_at))) return null;
  try {
    const query = new URLSearchParams({ nearest_to: String(depth.captured_at), max_delta_s: '0.75' });
    const response = await fetch(`/body/camera/yolo/status?${query}`, { cache: 'no-store' });
    if (!response.ok) return null;
    const result = await response.json();
    const delta = Math.abs(Number(result.captured_at) - Number(depth.captured_at));
    return result.state === 'ready' && Number.isFinite(delta) && delta <= 0.75
      ? { ...result, frame_delta_s: delta } : null;
  } catch (error) {
    console.warn('Could not find YOLOX detections near MiDaS frame:', error);
    return null;
  }
}

async function updateCloudCameraPlane(frame) {
  if (!cloud || !frame?.image_base64) return false;
  const token = ++cloudCameraPlaneToken;
  const image = new Image();
  image.src = `data:${frame.mime_type || 'image/jpeg'};base64,${frame.image_base64}`;
  await image.decode();
  if (token !== cloudCameraPlaneToken) return false;
  const intrinsics = cameraIntrinsicsForImage({ width: image.naturalWidth, height: image.naturalHeight });
  const distance = 80;
  const corners = [
    cameraPointInBodyFrame(cameraPoint(0, 0, distance, intrinsics), Number(frame.captured_at) || latestDepthCapturedAt),
    cameraPointInBodyFrame(cameraPoint(image.naturalWidth, 0, distance, intrinsics), Number(frame.captured_at) || latestDepthCapturedAt),
    cameraPointInBodyFrame(cameraPoint(0, image.naturalHeight, distance, intrinsics), Number(frame.captured_at) || latestDepthCapturedAt),
    cameraPointInBodyFrame(cameraPoint(image.naturalWidth, image.naturalHeight, distance, intrinsics), Number(frame.captured_at) || latestDepthCapturedAt),
  ];
  const texture = new THREE.Texture(image);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  if (cloudCameraPlane) {
    cloud.scene.remove(cloudCameraPlane);
    cloudCameraPlane.geometry.dispose();
    cloudCameraPlane.material.map?.dispose();
    cloudCameraPlane.material.dispose();
  }
  const planeGeometry = new THREE.BufferGeometry();
  planeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(corners.flatMap(point => point.toArray()), 3));
  planeGeometry.setAttribute('uv', new THREE.Float32BufferAttribute([0, 1, 1, 1, 0, 0, 1, 0], 2));
  planeGeometry.setIndex([0, 2, 1, 2, 3, 1]);
  cloudCameraPlane = new THREE.Mesh(planeGeometry,
    new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide, depthWrite: false }));
  cloudCameraPlane.userData.frameId = frame.frame_id;
  cloudCameraPlane.renderOrder = -1;
  cloudCameraPlane.visible = Boolean(cloudViewport?.classList.contains('is-camera-view'));
  cloud.scene.add(cloudCameraPlane);
  cloud.render();
  return true;
}

async function loadDepthFrame(depth) {
  const rawAvailable = depth?.depth_raw_png_base64
    && Number.isFinite(Number(depth.depth_raw_min)) && Number.isFinite(Number(depth.depth_raw_max));
  const image = await loadDepthImage(
    rawAvailable ? depth.depth_raw_png_base64 : depth.depth_gray_jpeg_base64,
    rawAvailable ? 'image/png' : 'image/jpeg',
  );
  if (rawAvailable) {
    image.rawMin = Number(depth.depth_raw_min);
    image.rawMax = Number(depth.depth_raw_max);
    const normalizedDepth = await loadGrayDepth(depth.depth_gray_jpeg_base64);
    if (normalizedDepth.width === image.width && normalizedDepth.height === image.height) {
      image.normalizedValues = normalizedDepth.values;
    }
  } else {
    image.normalizedValues = image.values;
  }
  image.frameId = String(depth.frame_id || '');
  image.capturedAt = Number(depth.captured_at) || 0;
  return image;
}

function updateMetricCalibrationStatus() {
  const statuses = ['world-map-midas-calibration-status', 'world-map-midas-calibration-status-3d']
    .map(byId).filter(Boolean);
  if (!statuses.length || depthCalibrationBusy) return;
  let message;
  if (depthCalibrationMessage) {
    message = depthCalibrationMessage;
  } else if (metricDepthCalibration?.available) {
    const [near, far] = metricDepthCalibration.calibrated_range_m || [];
    message = `MiDaS fit · holdout ±${Number(metricDepthCalibration.holdout_rmse_m).toFixed(2)} m · ${metricDepthCalibration.sample_count} anchors · ${near}–${far} m forward. Radar labels remain primary; camera alignment is approximate.`;
  } else {
    message = 'Not calibrated · ranges are relative, not metres. Track one person moving through several distances.';
  }
  statuses.forEach(status => { status.textContent = message; });
}

async function loadMetricCalibration() {
  try {
    const response = await fetch('/body/camera/depth-calibration', { cache: 'no-store' });
    if (response.ok) metricDepthCalibration = await response.json();
  } catch (error) {
    console.warn('Could not read persistent MiDaS calibration:', error);
  }
  updateMetricCalibrationStatus();
}

function matchedRadarAnchors(detections, sample, image = null) {
  const source = String(sample?.source || '').toLowerCase();
  if (!source.startsWith('hlk_ld2450')) return [];
  const targets = Array.isArray(sample.targets) ? sample.targets : [];
  const people = (detections || []).filter(item => /person|human/i.test(String(item.label || item.class_name || item.class || ''))
    && Number(item.confidence ?? item.score ?? 0) >= 0.4 && Array.isArray(item.bbox) && item.bbox.length === 4);
  const candidates = [];
  for (const [targetIndex, target] of targets.entries()) {
    const position = target.position_m || target.position;
    if (!Array.isArray(position) || position.length < 2) continue;
    const lateralRight = Number(position[0]);
    const forward = Number(position[1]);
    const radialRange = Math.hypot(lateralRight, forward);
    if (!Number.isFinite(radialRange) || radialRange < 0.25 || radialRange > 6 || forward <= 0
        || Math.abs(Math.atan2(lateralRight, forward)) > Math.PI / 3) continue;
    const cameraLateral = lateralRight - cameraRadarGeometry.lateralOffsetM;
    const radarBearing = Math.atan2(cameraLateral, forward) - THREE.MathUtils.degToRad(cameraRadarGeometry.yawOffsetDeg);
    for (const detection of people) {
      const centerU = (Number(detection.bbox[0]) + Number(detection.bbox[2])) / 2;
      const width = Number(image?.width) || Number(latestCameraFrame?.width) || 640;
      const intrinsics = cameraIntrinsicsForImage({ width, height: Number(image?.height) || 480 });
      const cameraBearing = Math.atan2(centerU * width - intrinsics.cx, intrinsics.fx);
      const error = Math.abs((cameraBearing - radarBearing) * 180 / Math.PI);
      if (error > maxPersonBearingErrorDeg) continue;
      candidates.push({
        detection,
        targetIndex,
        targetId: String(target.id || target.target_id || `target-${targetIndex}`),
        forward,
        radialRange,
        error,
        cost: error,
        lateralRight: cameraLateral,
      });
    }
  }
  candidates.sort((a, b) => a.cost - b.cost);
  // Keep only clear local winners, then greedily enforce one-to-one identity.
  const unambiguous = candidates.filter(candidate => {
    const sameDetection = candidates.filter(item => item.detection === candidate.detection).sort((a, b) => a.cost - b.cost);
    const sameTarget = candidates.filter(item => item.targetIndex === candidate.targetIndex).sort((a, b) => a.cost - b.cost);
    const clear = list => list[0] === candidate && (!list[1] || list[1].cost - candidate.cost >= 3);
    return clear(sameDetection) && clear(sameTarget);
  }).sort((a, b) => a.cost - b.cost);
  const usedDetections = new Set();
  const usedTargets = new Set();
  const selected = unambiguous;
  return selected.filter(candidate => {
    if (usedDetections.has(candidate.detection) || usedTargets.has(candidate.targetIndex)) return false;
    usedDetections.add(candidate.detection);
    usedTargets.add(candidate.targetIndex);
    return true;
  });
}

function openDepthCalibrationGuide() {
  if (depthCalibrationBusy) return;
  let dialog = byId('world-map-calibration-guide');
  if (!dialog) {
    dialog = document.createElement('dialog');
    dialog.id = 'world-map-calibration-guide';
    dialog.className = 'world-map-calibration-guide';
    dialog.setAttribute('aria-labelledby', 'world-map-calibration-title');
    dialog.innerHTML = `<form method="dialog" class="world-map-calibration-guide__surface">
      <header><div><p class="world-map-calibration-kicker">BODY · SENSOR CALIBRATION</p><h2 id="world-map-calibration-title">Radar + MiDaS calibration</h2></div><button class="world-map-calibration-close" value="cancel" aria-label="Close guide">×</button></header>
      <p class="world-map-calibration-intro">Follow the stages in order. This action collects radar-matched MiDaS anchors; it does not calibrate camera intrinsics or physically measure sensor alignment for you.</p>
      <ol class="world-map-calibration-stages">
        <li><b>0 · Prepare the rig</b><span>Rigidly fix camera, radar and IMU on a level floor. Measure camera height and camera-to-radar lateral offset. Mark 1–5 m on the camera axis and ±1 m at 2 m and 4 m.</span></li>
        <li><b>1 · IMU zero, about 5 s</b><span>Keep the robot still. The live IMU must report valid attitude, ready gyro bias, stable calibration and roll/pitch within ±5°. For a real mount zero, record level-floor roll/pitch offsets; the current fit only gates on low tilt.</span></li>
        <li><b>2 · Camera intrinsics · manual prerequisite</b><span>Calibrate at the live 640×480 resolution with 15–20 checkerboard views. Save fx, fy, cx, cy and distortion to calibration/camera.json; target RMS below 0.5 px (at most 1 px).</span></li>
        <li><b>3 · Camera ↔ radar alignment · manual prerequisite</b><span>At each tape mark, match a person’s camera bearing with radar atan2(x,y). Verify the mount yaw/lateral offset and keep error under 3°. Current automatic matching uses an approximate field of view; it does not fit these offsets.</span></li>
        <li><b>4 · Ground-plane check · optional</b><span>With measured camera height and IMU mount pitch, compare visible foot-point ranges to the tape marks. Target error under 0.2 m at 1–4 m. Not currently calculated by this button.</span></li>
        <li><b>5 · Fit MiDaS to radar · automated here</b><span>Stand still at several 1–5 m marks. The collector uses torso-region median depth, radar forward distance y, synchronized frames, a stable low-tilt IMU and unambiguous person matches. It needs at least 15 accepted anchors across four distance bands; the fit is robust and validates holdout data.</span></li>
        <li><b>6 · Validate · manual</b><span>Use tape marks omitted from fitting. Compare radar and MiDaS; test seated/cropped people too. Record the held-out RMSE. Treat predictions outside the fitted range as extrapolated.</span></li>
        <li><b>7 · Runtime</b><span>Radar remains the metric reference when a person is matched; MiDaS serves other objects. The rolling fit expires old anchors, so scene changes need fresh anchors. Recheck alignment after any impact/remount; redo intrinsics if lens or resolution changes.</span></li>
      </ol>
      <div class="world-map-calibration-checks"><label><input type="checkbox" data-calibration-check="rig"> Mounts are rigid; floor is level; tape marks are ready</label><label><input type="checkbox" data-calibration-check="imu"> Robot is stationary; IMU status is stable and low tilt</label><label><input type="checkbox" data-calibration-check="intrinsics"> I have verified the 640×480 camera intrinsics</label><label><input type="checkbox" data-calibration-check="alignment"> I have measured/verified camera-to-radar alignment</label></div>
      <p class="world-map-calibration-caution">Intrinsics and alignment are not currently enforced by the fitter: without those checks, bearing matches and resulting distances remain approximate. Do not interpret a good MiDaS fit as proof of geometric calibration.</p>
      <p id="world-map-calibration-guide-status" class="world-map-calibration-progress" role="status">Ready when the robot and target person are stationary.</p>
      <footer><button type="button" data-calibration-action="cancel">Cancel</button><button type="button" data-calibration-action="start" class="primary">Start 60-second collection</button></footer>
    </form>`;
    document.body.appendChild(dialog);
    dialog.querySelector('[data-calibration-action="cancel"]')?.addEventListener('click', () => dialog.close());
    dialog.querySelector('[data-calibration-action="start"]')?.addEventListener('click', () => {
      const unchecked = [...dialog.querySelectorAll('[data-calibration-check]')].filter(item => !item.checked);
      const status = byId('world-map-calibration-guide-status');
      if (unchecked.length) {
        status.textContent = `Verify the ${unchecked.length} unchecked prerequisite${unchecked.length === 1 ? '' : 's'}, or cancel and complete those calibration stages first.`;
        unchecked[0].focus();
        return;
      }
      dialog.close();
      void calibrateMetricDepth();
    });
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
  }
  dialog.showModal();
}

async function calibrateMetricDepth() {
  if (depthCalibrationBusy) return;
  const buttons = ['world-map-midas-calibrate', 'world-map-midas-calibrate-3d'].map(byId).filter(Boolean);
  const statuses = ['world-map-midas-calibration-status', 'world-map-midas-calibration-status-3d'].map(byId).filter(Boolean);
  if (!buttons.length || !statuses.length) return;
  const setMessage = message => statuses.forEach(status => { status.textContent = message; });
  depthCalibrationBusy = true;
  depthCalibrationMessage = '';
  buttons.forEach(button => { button.disabled = true; button.textContent = 'Calibrating…'; });
  setMessage('Collecting for 60 s: pause at several points from 1–5 m. Only synchronized, stationary, low-tilt radar/person matches count.');
  const samples = [];
  const seen = new Set();
  const radarHistory = [];
  const diagnostics = { depth: 0, yolo: 0, radar: 0, bearing: 0 };
  let cachedFrameId = '';
  let cachedDepthImage = null;
  let calibrationTargetId = null;
  const stopAt = performance.now() + 60000;
  try {
    while (performance.now() < stopAt) {
      const [depthResponse, radarResponse, imuResponse] = await Promise.all([
        fetch('/body/camera/depth', { cache: 'no-store' }),
        fetch('/plugins/mmwave_radar/status', { cache: 'no-store' }),
        fetch('/plugins/imu/status', { cache: 'no-store' }),
      ]);
      if (!depthResponse.ok || !radarResponse.ok || !imuResponse.ok) throw new Error('MiDaS, radar or IMU endpoint is unavailable');
      const [depth, radarStatus, imuStatus] = await Promise.all([depthResponse.json(), radarResponse.json(), imuResponse.json()]);
      if (Array.isArray(imuStatus.history)) imuHistory = imuStatus.history.slice(-256);
      const latestRadar = radarStatus.sample || {};
      if (radarStatus.available && Number(latestRadar.timestamp) > 0
          && String(latestRadar.source || '').toLowerCase().startsWith('hlk_ld2450')) {
        radarHistory.push(latestRadar);
        if (radarHistory.length > 120) radarHistory.shift();
      }
      if (!depth.frame_id || !depth.depth_raw_png_base64) {
        setMessage(`Waiting for raw MiDaS depth · ${samples.length} anchors collected.`);
        await new Promise(resolve => setTimeout(resolve, 350));
        continue;
      }
      diagnostics.depth += 1;
      let yoloResponse = await fetch(`/body/camera/yolo/status?nearest_to=${encodeURIComponent(depth.captured_at)}&max_delta_s=${maxCalibrationPairDeltaSeconds}`, { cache: 'no-store' });
      if (yoloResponse.status === 404) {
        setMessage(`Waiting for aligned YOLOX · ${samples.length} anchors · frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, matched ${diagnostics.bearing}.`);
        await new Promise(resolve => setTimeout(resolve, 350));
        continue;
      }
      if (!yoloResponse.ok) throw new Error('YOLOX endpoint is unavailable');
      const yolo = await yoloResponse.json();
      diagnostics.yolo += 1;
      const yoloAt = Number(yolo.captured_at);
      const depthAt = Number(depth.captured_at);
      const now = Date.now() / 1000;
      const frameDelta = Math.abs(yoloAt - depthAt);
      const anchorAt = (yoloAt + depthAt) / 2;
      const radarMatch = radarHistory.reduce((best, item) => {
        const delta = Math.abs(Number(item.timestamp) - anchorAt);
        return !best || delta < best.delta ? { item, delta } : best;
      }, null);
      const radarDelta = radarMatch?.delta ?? Infinity;
      if (radarMatch && radarDelta <= 0.75) diagnostics.radar += 1;
      const imuSample = imuSampleAt(anchorAt, 0.1);
      const imuDelta = imuSample ? Math.abs(Number(imuSample.timestamp) - anchorAt) : Infinity;
      const imuStationary = Boolean(imuStatus.available && imuSample?.calibration_stable
        && imuSample.attitude_valid && imuDelta <= 0.1
        && Math.abs(Number(imuSample.roll_deg)) <= 5
        && Math.abs(Number(imuSample.pitch_deg)) <= 5
        && now - Number(imuSample.timestamp) <= 0.5);
      const synchronized = yolo.state === 'ready' && frameDelta <= maxCalibrationPairDeltaSeconds
        && now - yoloAt <= 1.0 && now - depthAt <= 1.0
        && radarMatch && radarDelta <= maxCalibrationPairDeltaSeconds && imuStationary;
      if (synchronized) {
        if (cachedFrameId !== depth.frame_id) {
          cachedDepthImage = await loadDepthFrame(depth);
          cachedFrameId = depth.frame_id;
        }
        const candidates = matchedRadarAnchors(yolo.detections, radarMatch.item, cachedDepthImage);
        const match = calibrationTargetId
          ? candidates.find(item => item.targetId === calibrationTargetId) || null
          : candidates[0] || null;
        if (match && !calibrationTargetId) calibrationTargetId = match.targetId;
        if (match) diagnostics.bearing += 1;
        const key = `${depth.frame_id}|${yolo.frame_id}`;
        if (match && cachedDepthImage && !seen.has(key)) {
          const box = match.detection.bbox.map(Number);
          const x1 = Math.max(0, Math.min(cachedDepthImage.width - 1, Math.round((box[0] * 0.7 + box[2] * 0.3) * cachedDepthImage.width)));
          const x2 = Math.max(x1 + 1, Math.min(cachedDepthImage.width, Math.round((box[0] * 0.3 + box[2] * 0.7) * cachedDepthImage.width)));
          const y1 = Math.max(0, Math.min(cachedDepthImage.height - 1, Math.round((box[1] * 0.65 + box[3] * 0.35) * cachedDepthImage.height)));
          const y2 = Math.max(y1 + 1, Math.min(cachedDepthImage.height, Math.round((box[1] * 0.35 + box[3] * 0.65) * cachedDepthImage.height)));
          const roi = [];
          const step = Math.max(1, Math.floor(Math.min(x2 - x1, y2 - y1) / 8));
          for (let y = y1; y < y2; y += step) for (let x = x1; x < x2; x += step) {
            roi.push(depthValueAt(cachedDepthImage, (y * cachedDepthImage.width + x) * 4));
          }
          roi.sort((a, b) => a - b);
          if (!roi.length) continue;
          const rawDepth = roi[Math.floor(roi.length / 2)];
          const calibrationSample = {
            sample_id: `${depth.frame_id}|${yolo.frame_id}|${match.targetId}`,
            relative_depth: rawDepth,
            forward_m: match.forward,
            bearing_error_deg: match.error,
            frame_delta_s: frameDelta,
            radar_delta_s: radarDelta,
            imu_delta_s: imuDelta,
            stationary: true,
          };
          const postResponse = await fetch('/body/camera/depth-calibration', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sample: calibrationSample }),
          });
          if (!postResponse.ok) throw new Error('Rolling calibration endpoint rejected an anchor');
          const fit = await postResponse.json();
          if (!fit.accepted) {
            seen.add(key);
            continue;
          }
          samples.push(calibrationSample);
          seen.add(key);
          metricDepthCalibration = fit.available ? fit : null;
          depthCalibrationMessage = fit.available ? '' : (fit.reason || 'Collecting a wider set of stationary anchors.');
          updateMetricCalibrationStatus();
        }
      }
      setMessage(`Stationary anchors ${samples.length}/15 · aligned frames ${diagnostics.depth} · radar matches ${diagnostics.bearing} · IMU must confirm stable and <5° tilt · spread 1–5 m.`);
      await new Promise(resolve => setTimeout(resolve, 350));
    }
    if (!metricDepthCalibration?.available) throw new Error(`Fit not validated; collected ${samples.length} stationary anchors. Cover four or more distance bands from 1–5 m.`);
    cloudFrameId = '';
    depthCalibrationMessage = '';
    lastSensorDepthAt = 0;
    await refreshSensorDepth();
  } catch (error) {
    depthCalibrationMessage = `Calibration not saved: ${error.message} · frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, bearing ${diagnostics.bearing}`;
  } finally {
    depthCalibrationBusy = false;
    buttons.forEach(button => {
      button.disabled = false;
      button.textContent = metricDepthCalibration?.available ? 'Recalibrate with radar' : 'Calibrate with radar';
    });
    updateMetricCalibrationStatus();
  }
}

async function refreshSensors() {
  if (sensorBusy || activeSource !== 'sensors') return;
  sensorBusy = true;
  try {
    const response = await fetch('/body/camera/frame', { cache: 'no-store' });
    const frame = await response.json();
    setSensorFetchFailure('camera', false);
    const currentCamera = frame.camera || {};
    const yolo = frame.yolo || {};
    latestCameraFrame = currentCamera;
    updateCloudOrigin();
    latestSensorYolo = yolo;
    const cameraState = byId('world-map-camera-state');
    const frameAge = Number(currentCamera.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(currentCamera.captured_at)) : Infinity;
    if (cameraState) {
      cameraState.textContent = currentCamera.image_base64
        ? `LIVE · ${currentCamera.width || '—'}×${currentCamera.height || '—'} · ${Number.isFinite(frameAge) ? frameAge.toFixed(1) + 's' : 'age —'}`
        : `${currentCamera.state || frame.status || 'NO FRAME'}`;
    }
    setFeedStatus('world-map-camera-state', 'camera', classifyAge('camera', frameAge, Boolean(currentCamera.image_base64)), currentCamera.image_base64
      ? `LIVE · ${currentCamera.width || '—'}×${currentCamera.height || '—'} · ${Number.isFinite(frameAge) ? frameAge.toFixed(1) + 's' : 'age —'}`
      : `${currentCamera.state || frame.status || 'NO FRAME'}`);
    const cameraImage = byId('world-map-camera-image');
    const cameraEmpty = byId('world-map-camera-empty');
    if (currentCamera.frame_id !== displayedCameraFrameId) {
      setImage(cameraImage, cameraEmpty, currentCamera.image_base64, currentCamera.mime_type || 'image/jpeg');
      displayedCameraFrameId = currentCamera.frame_id;
    }
    const imageWrap = cameraImage?.parentElement;
    if (imageWrap && currentCamera.width && currentCamera.height) {
      imageWrap.style.aspectRatio = `${currentCamera.width}/${currentCamera.height}`;
    }
    const detections = visibleYoloDetections(yolo);
    const yoloOverlayKey = `${yolo.state || 'disabled'}:${yolo.frame_id || ''}:${detections.length}`;
    if (yoloOverlayKey !== displayedYoloOverlayKey) {
      drawBoxes(detections, currentCamera.width || 640, currentCamera.height || 480);
      displayedYoloOverlayKey = yoloOverlayKey;
    }
    if (activeRender === '3d' && cloudDepthImage) drawDepthDetections(cloudDepthImage, yolo);
    if (activeRender === '3d') updateCloudHud();
    const yoloDetail = `${yolo.state || 'disabled'} · ${(yolo.detections || []).length} boxes${yolo.latency_ms != null ? ` · ${yolo.latency_ms} ms` : ''}`;
    setFeedStatus('world-map-yolo-state', 'yolo', classifyAge('yolo', frameAge, yolo.state === 'ready' && Boolean(currentCamera.image_base64)), yoloDetail);
    const frameDetail = currentCamera.frame_id ? `${currentCamera.frame_id}${currentCamera.captured_at ? ` · ${frameAge.toFixed(1)}s` : ''}` : 'No frame';
    byId('world-map-frame-state').textContent = frameDetail;
    const frameSummary = byId('world-map-summary-frame');
    if (frameSummary) frameSummary.textContent = Number.isFinite(frameAge) ? `${frameAge.toFixed(1)} s` : '—';
    byId('world-map-sensor-note').textContent = `Sensor-only view · frame ${currentCamera.frame_id || 'unavailable'} · no simulation object positions or metric scale.`;
  } catch (error) {
    setFeedStatus('world-map-camera-state', 'camera', 'offline', `Offline · ${error.message}`);
    setFeedStatus('world-map-yolo-state', 'yolo', 'offline', 'Offline · waiting for camera frame');
    setSensorFetchFailure('camera', true);
    byId('world-map-sensor-note').textContent = latestCameraFrame?.frame_id
      ? `Sensor-only view · last camera frame ${latestCameraFrame.frame_id} is retained but not current.`
      : 'Sensor-only view · waiting for a current camera frame.';
  } finally {
    sensorBusy = false;
  }
}

async function sensorJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

const readoutBusy = { radar: false, gps: false, imu: false, tof: false };
let systemMetricsBusy = false;
const displayNumber = (value, digits = 1, suffix = '') => {
  const number = value === null || value === undefined || value === '' ? NaN : Number(value);
  return Number.isFinite(number) ? `${number.toFixed(digits)}${suffix}` : '—';
};

async function refreshSystemMetrics() {
  if (systemMetricsBusy || activeSource !== 'sensors') return;
  systemMetricsBusy = true;
  try {
    const metrics = await sensorJson('/system/metrics');
    const cpu = metrics.cpu || {}, gpu = metrics.gpu || {}, memory = metrics.memory || {}, power = metrics.power || {};
    byId('world-map-system-state').textContent = metrics.available ? 'Live · 1 s' : 'Partial telemetry';
    const setGauge = (id, value, max, label, suffix = '') => {
      const gauge = byId(id);
      const valid = value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
      const numeric = valid ? Math.max(0, Math.min(Number(max), Number(value))) : 0;
      gauge.style.setProperty('--gauge-value', valid ? String(numeric / Number(max) * 100) : '0');
      gauge.setAttribute('aria-label', `${label}: ${valid ? `${Number(value).toFixed(1)}${suffix}` : 'unavailable'}`);
    };
    setGauge('world-map-cpu-gauge', cpu.utilization_percent, 100, 'CPU utilization', '%');
    setGauge('world-map-cpu-temp-gauge', cpu.temperature_c, 100, 'Maximum CPU temperature', ' degrees Celsius');
    setGauge('world-map-gpu-temp-gauge', gpu.temperature_c, 100, 'Maximum GPU temperature', ' degrees Celsius');
    setGauge('world-map-memory-gauge', memory.used_percent, 100, 'Memory utilization', '%');
    byId('world-map-system-cpu-value').textContent = cpu.utilization_percent == null ? '—' : cpu.utilization_percent.toFixed(0);
    byId('world-map-system-cpu-temp-value').textContent = displayNumber(cpu.temperature_c, 1);
    byId('world-map-system-gpu-temp-value').textContent = displayNumber(gpu.temperature_c, 1);
    byId('world-map-system-cpu-temp').textContent = `Hottest CPU · ${displayNumber(cpu.temperature_c, 1, '°C')}`;
    const gpuClock = gpu.frequency_mhz == null ? '—' : `${gpu.frequency_mhz.toFixed(0)} MHz`;
    byId('world-map-system-gpu-meta').textContent = `${gpu.utilization_percent == null ? 'Load unavailable' : `${gpu.utilization_percent.toFixed(1)}% load`} · ${gpuClock}`;
    byId('world-map-system-gpu-load').textContent = gpu.utilization_percent == null ? 'Not exposed by kernel' : `${gpu.utilization_percent.toFixed(1)}%`;
    byId('world-map-system-gpu-clock').textContent = gpuClock;
    byId('world-map-system-memory-value').textContent = memory.used_percent == null ? '—' : memory.used_percent.toFixed(0);
    byId('world-map-system-memory-meta').textContent = memory.available_mb == null
      ? 'Free memory unavailable' : `${(memory.available_mb / 1024).toFixed(1)} / ${(memory.total_mb / 1024).toFixed(1)} GB free`;
    const powerScale = Math.max(20, Math.ceil((Number(power.watts) || 0) / 10) * 10);
    setGauge('world-map-power-gauge', power.watts, powerScale, 'Measured board input power', ' watts');
    byId('world-map-power-gauge').setAttribute('aria-label', power.available
      ? `Measured board input power: ${power.watts.toFixed(2)} watts on a 0 to ${powerScale} watt display scale`
      : 'Measured board input power unavailable');
    byId('world-map-system-power-value').textContent = power.available ? power.watts.toFixed(1) : '—';
    const summaryPower = byId('world-map-summary-power');
    const summaryEnergy = byId('world-map-summary-energy');
    if (summaryPower) summaryPower.textContent = power.available ? `${power.watts.toFixed(1)} W` : '— W';
    if (summaryEnergy) summaryEnergy.textContent = power.available ? `${power.energy_wh_session.toFixed(3)} Wh` : '— Wh';
    byId('world-map-system-power-meta').textContent = power.available
      ? `${power.voltage_v.toFixed(1)} V · ${power.current_a.toFixed(2)} A · scale 0–${powerScale} W`
      : 'Onboard power monitor unavailable';
    const yoloHtp = String(latestSensorYolo?.runtime || '').toLowerCase().includes('htp');
    const midasHtp = String(latestSensorDepth?.device || '').toLowerCase().includes('htp');
    byId('world-map-system-htp').textContent = yoloHtp || midasHtp
      ? `ACTIVE · YOLOX ${yoloHtp ? `${displayNumber(latestSensorYolo?.inference_ms, 0, ' ms')} HTP` : '—'} · MiDaS ${midasHtp ? `${displayNumber(latestSensorDepth?.inference_ms, 0, ' ms')} HTP` : '—'}`
      : 'Utilization counter unavailable';
    byId('world-map-system-energy').textContent = power.available
      ? `${power.energy_wh_session.toFixed(3)} Wh` : 'Unavailable';
    byId('world-map-system-note').textContent = `The INA232 monitors the onboard input rail; external motor loads may be excluded. Temperature dials show the hottest reported sensor in each group; GPU/HTP utilization is unavailable because the kernel exports no reliable busy counter.`;
  } catch (error) {
    byId('world-map-system-state').textContent = `Unavailable · ${error.message}`;
  } finally { systemMetricsBusy = false; }
}

function drawLiveRadar(sample = {}) {
  const canvas = byId('world-map-radar-plot');
  const context = canvas?.getContext('2d');
  if (!context) return;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, canvas.clientWidth);
  const height = Math.max(1, canvas.clientHeight);
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
  }
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  const left = 38, right = width - 22, top = 18, bottom = height - 28;
  const center = (left + right) / 2;
  context.strokeStyle = '#294c3a';
  context.fillStyle = '#8eaa98';
  context.font = '10px ui-monospace,monospace';
  for (let meters = 1; meters <= 6; meters += 1) {
    const y = bottom - (bottom - top) * meters / 6;
    context.globalAlpha = meters % 2 ? .55 : .9;
    context.beginPath(); context.moveTo(left, y); context.lineTo(right, y); context.stroke();
    context.fillText(`${meters}m`, 6, y + 3);
  }
  context.globalAlpha = 1;
  for (let angle = -60; angle <= 60; angle += 30) {
    const x = center + Math.tan(angle * Math.PI / 180) / Math.tan(Math.PI / 3) * (right - left) / 2;
    context.beginPath(); context.moveTo(x, top); context.lineTo(x, bottom); context.stroke();
    context.fillText(`${angle > 0 ? '+' : ''}${angle}°`, x - 10, height - 8);
  }
  context.fillStyle = '#b6f1d3';
  context.beginPath(); context.moveTo(center, bottom - 9); context.lineTo(center - 6, bottom + 1); context.lineTo(center + 6, bottom + 1); context.closePath(); context.fill();
  const targets = Array.isArray(sample.targets) ? sample.targets : [];
  for (const target of targets) {
    const position = target.position_m || target.position || [];
    const lateral = Number(position[0]);
    const forward = Number(position[1]);
    if (!Number.isFinite(lateral) || !Number.isFinite(forward) || forward < 0 || forward > 6) continue;
    const bearing = Math.atan2(lateral, forward);
    if (Math.abs(bearing) > Math.PI / 3) continue;
    const x = center + bearing / (Math.PI / 3) * (right - left) / 2;
    const y = bottom - forward / 6 * (bottom - top);
    const speed = Number(target.radial_speed_mps);
    const odometryAge = Number(latestVisualOdometry?.captured_at) > 0
      ? Date.now() / 1000 - Number(latestVisualOdometry.captured_at) : Infinity;
    const egoMotionLikely = latestVisualOdometry?.available && odometryAge <= 0.35
      && Number(latestVisualOdometry.confidence) >= 0.35
      && Number(latestVisualOdometry.speed_mps) >= 0.05;
    const moving = Number.isFinite(speed) && Math.abs(speed) >= .05 && !egoMotionLikely;
    context.fillStyle = egoMotionLikely ? '#9aa7ad' : moving ? '#ed91c5' : '#efcb76';
    context.beginPath(); context.arc(x, y, 5, 0, Math.PI * 2); context.fill();
    context.fillStyle = '#e7f4eb'; context.font = '10px ui-monospace,monospace';
    context.fillText(`${forward.toFixed(1)}m`, x + 8, y - 5);
  }
}

async function refreshLiveRadar() {
  if (activeSource !== 'sensors' || readoutBusy.radar) return;
  readoutBusy.radar = true;
  try {
    const status = await sensorJson('/plugins/mmwave_radar/status');
    const sample = status.sample || {};
    latestRadarSample = status.available ? sample : null;
    if (latestRadarSample?.timestamp && !radarHistory.some(item => item.timestamp === latestRadarSample.timestamp)) {
      radarHistory.push(latestRadarSample);
      radarHistory = radarHistory.filter(item => Date.now() / 1000 - Number(item.timestamp) <= 5).slice(-32);
    }
    const targets = Array.isArray(sample.targets) ? sample.targets : [];
    const age = Number(sample.timestamp) > 0 ? Math.max(0, Date.now() / 1000 - Number(sample.timestamp)) : NaN;
    const targetLabel = `${targets.length} target${targets.length === 1 ? '' : 's'}`;
    const radarDetail = `${targetLabel}${Number.isFinite(age) ? ` · ${age.toFixed(1)} s` : ''}`;
    setFeedStatus('world-map-radar-state', 'radar', classifyAge('radar', age, Boolean(status.available)), status.available
      ? radarDetail : status.error || 'No data');
    byId('world-map-radar-targets').replaceChildren(...(targets.length ? targets.map((target, index) => {
      const position = target.position_m || target.position || [];
      const velocity = target.velocity_mps || target.velocity || [];
      const lateral = Number(position[0]), forward = Number(position[1]);
      const row = document.createElement('div'); row.className = 'sensor-target-row';
      const name = document.createElement('span'); name.textContent = `${target.id || target.target_id || `Target ${index + 1}`} · ${target.classification || 'unclassified'}`;
      const values = document.createElement('b');
      values.textContent = `${Number.isFinite(forward) ? forward.toFixed(2) : '—'} m fwd · ${Number.isFinite(lateral) ? lateral.toFixed(2) : '—'} m lat · ${displayNumber(target.radial_speed_mps, 2, ' m/s')}`;
      row.append(name, values); row.title = `XY velocity ${displayNumber(velocity[0], 2)} / ${displayNumber(velocity[1], 2)} m/s · confidence ${displayNumber(target.confidence, 2)}`;
      return row;
    }) : [Object.assign(document.createElement('span'), { textContent: status.available ? 'No targets in current radar frame.' : 'Waiting for a live radar frame.' })]));
    drawLiveRadar(sample);
    updateCloudRadar(latestRadarSample);
  } catch (error) {
    latestRadarSample = null;
    setFeedStatus('world-map-radar-state', 'radar', 'offline', `Unavailable · ${error.message}`);
    byId('world-map-radar-state').textContent = `Unavailable · ${error.message}`;
    byId('world-map-radar-targets').textContent = 'No live radar data.';
    drawLiveRadar();
    updateCloudRadar(null);
  } finally { readoutBusy.radar = false; }
}

async function refreshLiveGps() {
  if (activeSource !== 'sensors' || readoutBusy.gps) return;
  readoutBusy.gps = true;
  try {
    const status = await sensorJson('/plugins/gps/status');
    const sample = status.sample || status.source_status?.sample || {};
    const diagnostic = status.source_status?.diagnostic || {};
    const streaming = Boolean(status.available || sample.connected || Number(diagnostic.bytes_received) > 0);
    const fix = sample.fix === true || sample.valid === true || Number(sample.fix_quality) > 0;
    const gpsAge = Number(sample.timestamp) > 0 ? Math.max(0, Date.now() / 1000 - Number(sample.timestamp)) : NaN;
    const gpsState = classifyAge('gps', gpsAge, streaming);
    setFeedStatus('world-map-gps-state', 'gps', gpsState, fix ? 'Fix valid' : streaming ? 'UART live · no fix' : status.error || 'Offline');
    const latitude = Number(sample.latitude_deg ?? sample.latitude ?? sample.lat);
    const longitude = Number(sample.longitude_deg ?? sample.longitude ?? sample.lon ?? sample.lng);
    byId('world-map-gps-position').textContent = fix && Number.isFinite(latitude) && Number.isFinite(longitude) ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)}` : 'No valid fix';
    byId('world-map-gps-fix').textContent = `${gpsState === 'stale' ? 'Stale fix' : gpsState === 'live' && fix ? 'Valid' : 'No fix'} · quality ${sample.fix_quality ?? '—'}`;
    byId('world-map-gps-satellites').textContent = `${sample.satellites ?? '—'} used · ${sample.satellites_in_view ?? '—'} in view`;
    byId('world-map-gps-quality').textContent = `HDOP ${displayNumber(sample.hdop)} · ${displayNumber(sample.altitude_m, 1, ' m')}`;
    const signals = Array.isArray(sample.satellite_signals) ? sample.satellite_signals : [];
    const plot = byId('world-map-gps-signals');
    plot.setAttribute('aria-label', `GPS satellite signal strength; ${signals.length} satellites reported`);
    const visibleSignals = signals.slice(0, 12);
    const bars = visibleSignals.map(satellite => {
      const cn0 = Number(satellite.cn0_db_hz);
      const height = Number.isFinite(cn0) ? Math.max(3, Math.min(60, cn0)) : 3;
      const bar = document.createElement('div'); bar.className = 'sensor-gps-bar';
      const id = `${String(satellite.talker || 'GN').replace(/[^a-z0-9]/gi, '')}-${Number(satellite.svid) || '?'}`;
      const value = document.createElement('span'); value.textContent = Number.isFinite(cn0) ? cn0.toFixed(0) : '—';
      const fill = document.createElement('i'); fill.style.height = `${height}px`; fill.style.background = cn0 >= 35 ? '#3d9f70' : cn0 >= 25 ? '#c39738' : '#bd6559';
      const label = document.createElement('small'); label.textContent = id;
      bar.title = `${id} · C/N₀ ${displayNumber(cn0, 0, ' dB-Hz')} · az ${satellite.azimuth_deg ?? '—'}° · el ${satellite.elevation_deg ?? '—'}°`;
      bar.append(value, fill, label); return bar;
    });
    if (signals.length > visibleSignals.length) {
      const more = document.createElement('span'); more.className = 'sensor-gps-more'; more.textContent = `+${signals.length - visibleSignals.length}`;
      more.title = `${signals.length - visibleSignals.length} additional satellites`; bars.push(more);
    }
    plot.replaceChildren(...(signals.length ? bars : [Object.assign(document.createElement('span'), { className: 'sensor-readout-note', textContent: status.available ? 'No GSV satellite signal values in the current GPS sample.' : 'Waiting for GSV data from the GPS receiver.' })]));
  } catch (error) { setFeedStatus('world-map-gps-state', 'gps', 'offline', `Unavailable · ${error.message}`); }
  finally { readoutBusy.gps = false; }
}

async function refreshLiveImu() {
  if (activeSource !== 'sensors' || readoutBusy.imu) return;
  readoutBusy.imu = true;
  try {
    const status = await sensorJson('/plugins/imu/status');
    const sample = status.sample || {};
    if (Array.isArray(status.history)) imuHistory = status.history.slice(-256);
    else if (sample.sequence != null && !imuHistory.some(item => item.sequence === sample.sequence)) {
      imuHistory.push(sample);
      imuHistory = imuHistory.slice(-256);
    }
    const imuAge = Number(sample.timestamp) > 0 ? Math.max(0, Date.now() / 1000 - Number(sample.timestamp)) : NaN;
    setFeedStatus('world-map-imu-state', 'imu', classifyAge('imu', imuAge, Boolean(status.available)), status.available
      ? `${sample.attitude_valid ? 'Fused attitude' : 'Fused attitude unavailable'} · ${sample.motion_state || 'motion unknown'}${sample.gyro_bias_ready ? ' · bias ready' : ' · bias warming'}`
      : status.error || 'No data');
    byId('world-map-imu-roll').textContent = sample.attitude_valid ? displayNumber(sample.roll_deg, 1, '°') : 'Invalid';
    byId('world-map-imu-pitch').textContent = sample.attitude_valid ? displayNumber(sample.pitch_deg, 1, '°') : 'Invalid';
    const attitude = byId('world-map-imu-attitude');
    if (attitude) {
      const roll = Number(sample.roll_deg);
      const pitch = Number(sample.pitch_deg);
      const valid = Boolean(sample.attitude_valid) && Number.isFinite(roll) && Number.isFinite(pitch);
      attitude.dataset.state = valid ? 'live' : 'offline';
      if (valid) {
        attitude.style.setProperty('--imu-roll', `${roll}deg`);
        attitude.style.setProperty('--imu-pitch', `${Math.max(-18, Math.min(18, pitch * 0.7))}px`);
      }
    }
    byId('world-map-imu-yaw').textContent = `${displayNumber(sample.yaw_relative_deg, 1, '°')} rel · ${displayNumber(sample.yaw_rate_dps ?? sample.angular_velocity_dps?.[2], 1, '°/s')}`;
    const acceleration = sample.acceleration_g;
    byId('world-map-imu-accel').textContent = Array.isArray(acceleration) ? acceleration.map(value => displayNumber(value, 2)).join(' / ') : '—';
    const gyro = sample.angular_velocity_dps;
    byId('world-map-imu-gyro').textContent = Array.isArray(gyro) ? gyro.map(value => displayNumber(value, 1)).join(' / ') : '—';
  } catch (error) { setFeedStatus('world-map-imu-state', 'imu', 'offline', `Unavailable · ${error.message}`); }
  finally { readoutBusy.imu = false; }
}

async function refreshLiveTof() {
  if (activeSource !== 'sensors' || readoutBusy.tof) return;
  readoutBusy.tof = true;
  try {
    const status = await sensorJson('/plugins/tof/status');
    const sample = status.sample || {};
    const tofAge = Number(sample.timestamp) > 0 ? Math.max(0, Date.now() / 1000 - Number(sample.timestamp)) : NaN;
    const available = status.available && sample.available !== false && !sample.simulated
      && !/sensor_not_detected/i.test(String(status.error || ''));
    const tofState = classifyAge('tof', tofAge, available);
    setFeedStatus('world-map-tof-state', 'tof', tofState, tofState === 'stale'
      ? `Stale · ${tofAge.toFixed(1)} s` : available ? `${sample.device || status.sensor || 'VL53L1X'} · live`
        : status.error || 'No fresh measurement');
    byId('world-map-tof-distance').textContent = available ? displayNumber(sample.distance_m, 2, ' m') : 'No measurement';
    byId('world-map-tof-meta').textContent = available ? `${sample.frame || status.frame || 'body_front'} · ${displayNumber(sample.distance_mm, 0, ' mm')}` : status.transport || 'Forward single-beam range';
  } catch (error) { setFeedStatus('world-map-tof-state', 'tof', 'offline', `Unavailable · ${error.message}`); }
  finally { readoutBusy.tof = false; }
}

async function refreshSensorSegmentation() {
  if (sensorSegmentationBusy || activeSource !== 'sensors') return;
  sensorSegmentationBusy = true;
  try {
    const response = await fetch('/body/camera/segmentation', { cache: 'no-store' });
    const segmentation = await response.json();
    latestSegmentation = segmentation;
    void renderSemanticMask(segmentation).catch((error) => {
      const classes = byId('world-map-segmentation-classes');
      if (classes) classes.textContent = `SegFormer mask unavailable · ${error.message}`;
    });
    const state = byId('world-map-segmentation-state');
    if (state) {
      const maskAge = Number(segmentation.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(segmentation.captured_at)) : NaN;
      const age = Number.isFinite(maskAge) ? ` · ${maskAge.toFixed(1)}s old` : '';
      const available = Boolean(segmentation.available || segmentation.mask_png_base64 || segmentation.class_mask);
      const feedState = classifyAge('segmentation', maskAge, available && segmentation.state !== 'disabled');
      setFeedStatus('world-map-segmentation-state', 'segmentation', feedState, `${segmentation.state || 'disabled'}${segmentation.device ? ` · ${segmentation.device}` : ''}${segmentation.latency_ms != null ? ` · ${segmentation.latency_ms} ms` : ''}${age}`);
    }
  } catch (error) {
    const state = byId('world-map-segmentation-state');
    if (state) setFeedStatus('world-map-segmentation-state', 'segmentation', 'offline', `SegFormer unavailable · ${error.message}`);
  } finally {
    sensorSegmentationBusy = false;
  }
}

async function refreshSensorDepth() {
  if (sensorDepthBusy || activeSource !== 'sensors'
      || (latestSensorDepth && performance.now() - lastSensorDepthAt < 250)) return;
  sensorDepthBusy = true;
  try {
    const response = await fetch('/body/camera/depth', { cache: 'no-store' });
    const depth = await response.json();
    setSensorFetchFailure('depth', false);
    const segmentation = latestSegmentation;
    latestSensorDepth = depth;
    latestSegmentation = segmentation;
    lastSensorDepthAt = performance.now();
    setImage(byId('world-map-depth-image'), byId('world-map-depth-empty'), depth.depth_jpeg_base64);
    const depthAge = Number(depth.captured_at) > 0
      ? ` · ${Math.max(0, Date.now() / 1000 - Number(depth.captured_at)).toFixed(1)}s old` : '';
    const ageSeconds = Number(depth.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(depth.captured_at)) : NaN;
    const midasState = classifyAge('midas', ageSeconds, Boolean(depth.depth_jpeg_base64) && depth.state !== 'disabled');
    setFeedStatus('world-map-midas-state', 'midas', midasState, `${depth.state || 'disabled'}${depth.device ? ` · ${depth.device}` : ''}${depth.latency_ms != null ? ` · ${depth.latency_ms} ms` : ''}${depthAge}${depth.error ? ` · ${depth.error}` : ''}`);
    if (cloudPoints) {
      cloudPoints.material.vertexColors = midasState !== 'stale';
      cloudPoints.material.color.set(midasState === 'stale' ? '#89939b' : '#ffffff');
      cloudPoints.material.opacity = midasState === 'stale' ? 0.38 : 0.92;
      cloudPoints.material.needsUpdate = true;
    }
    updateMetricCalibrationStatus();
    const alignedSegmentationFrameId = segmentationMatchesDepth(segmentation, depth)
      ? String(segmentation.frame_id || segmentation.captured_at || '') : '';
    const depthRenderKey = `${depth.frame_id || ''}:${Number(depth.captured_at) || 0}:${alignedSegmentationFrameId}`;
    const renderedKey = `${cloudFrameId}:${latestDepthCapturedAt}:${cloudSegmentationFrameId}`;
    if (depth.depth_gray_jpeg_base64 && activeRender === '3d'
        && depthRenderKey !== renderedKey && depthRenderKey !== cloudBuildingKey) {
      const depthFrameId = depth.frame_id;
      cloudBuildingKey = depthRenderKey;
      void rebuildDepthCloud(depth, segmentation)
        .then((updated) => {
          if (updated) {
            cloudFrameId = depthFrameId;
            cloudSegmentationFrameId = alignedSegmentationFrameId;
          }
        })
        .catch((error) => console.warn('Could not rebuild MiDaS depth cloud:', error))
        .finally(() => {
          if (cloudBuildingKey === depthRenderKey) cloudBuildingKey = '';
        });
    }
  } catch (error) {
    setFeedStatus('world-map-midas-state', 'midas', 'offline', `unavailable · ${error.message}`);
    if (cloudPoints) { cloudPoints.visible = false; cloud.render(); }
    setSensorFetchFailure('depth', true);
  } finally {
    sensorDepthBusy = false;
  }
}

let visualOdometryBusy = false;
async function refreshVisualOdometry() {
  if (visualOdometryBusy || activeSource !== 'sensors') return;
  visualOdometryBusy = true;
  try {
    const response = await fetch('/body/odometry/visual', { cache: 'no-store' });
    const odometry = await response.json();
    const status = byId('world-map-odometry-state');
    if (!status) return;
    const mapStatus = byId('world-map-odometry-map-status');
    if (mapStatus) {
      mapStatus.textContent = odometry.available ? 'TRACKING' : `${String(odometry.state || 'waiting').toUpperCase()} · LAST FIX RETAINED`;
      mapStatus.title = odometry.reason || '';
    }
    const odometryAge = Number(odometry.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(odometry.captured_at)) : NaN;
    const odometryState = classifyAge('odometry', odometryAge, Boolean(odometry.available));
    if (odometry.available) {
      const [forward = 0, lateral = 0] = odometry.position_m || [];
      setFeedStatus('world-map-odometry-state', 'odometry', odometryState, `${forward.toFixed(2)}m fwd · ${lateral.toFixed(2)}m left · ${Math.round(odometry.confidence * 100)}% · experimental`);
      const frameId = String(odometry.frame_id || '');
      if (frameId && frameId !== visualOdometryFrameId) {
        visualOdometryFrameId = frameId;
        visualOdometryTrail.push({ forward, lateral });
        if (visualOdometryTrail.length > 600) visualOdometryTrail.shift();
        updateCloudOdometry();
      }
      renderVisualOdometryMap(odometry);
    } else {
      setFeedStatus('world-map-odometry-state', 'odometry', 'offline', `${odometry.state || 'waiting'} · ${odometry.reason || 'need synchronized camera, MiDaS and radar calibration'}`);
      if (mapStatus) mapStatus.title = odometry.reason || '';
    }
  } catch (error) {
    const status = byId('world-map-odometry-state');
    if (status) setFeedStatus('world-map-odometry-state', 'odometry', 'offline', `unavailable · ${error.message}`);
  } finally {
    visualOdometryBusy = false;
  }
}

function renderVisualOdometryMap(odometry) {
  latestVisualOdometry = odometry;
  drawVisualOdometryMap();
  const mapStatus = byId('world-map-odometry-map-status');
  if (mapStatus) mapStatus.textContent = `TRACKING · ${Number(odometry.speed_mps || 0).toFixed(2)} m/s`;
}

function drawVisualOdometryMap() {
  const canvas = byId('world-map-odometry-map');
  const plot = canvas?.parentElement;
  if (!canvas || !plot) return;
  const bounds = plot.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const width = Math.round(bounds.width * dpr), height = Math.round(bounds.height * dpr);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = bounds.width, h = bounds.height;
  ctx.fillStyle = '#050b12';
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = '#1b3042';
  ctx.lineWidth = 1;
  for (let x = 0; x <= w; x += Math.max(48, w / 8)) {
    ctx.beginPath(); ctx.moveTo(Math.round(x) + 0.5, 0); ctx.lineTo(Math.round(x) + 0.5, h); ctx.stroke();
  }
  for (let y = 0; y <= h; y += Math.max(40, h / 6)) {
    ctx.beginPath(); ctx.moveTo(0, Math.round(y) + 0.5); ctx.lineTo(w, Math.round(y) + 0.5); ctx.stroke();
  }
  const inset = Math.min(28, w * 0.08);
  const plotArea = { left: inset, right: w - inset, top: inset, bottom: h - inset };
  const center = { x: w / 2, y: h * 0.68 };
  const forwardExtent = Math.max(1, ...visualOdometryTrail.map(point => Math.abs(point.forward)));
  const lateralExtent = Math.max(1.4, ...visualOdometryTrail.map(point => Math.abs(point.lateral)));
  const scale = Math.min((plotArea.right - plotArea.left) / (2 * lateralExtent), (center.y - plotArea.top) / forwardExtent, (plotArea.bottom - center.y) / forwardExtent);
  ctx.strokeStyle = '#00aeb8';
  ctx.beginPath(); ctx.moveTo(center.x, plotArea.top); ctx.lineTo(center.x, plotArea.bottom); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(plotArea.left, plotArea.bottom); ctx.lineTo(plotArea.right, plotArea.bottom); ctx.stroke();
  if (visualOdometryTrail.length > 1) {
    ctx.strokeStyle = '#ed35c5'; ctx.lineWidth = 2;
    ctx.beginPath();
    visualOdometryTrail.forEach((point, index) => {
      const x = center.x - point.lateral * scale, y = center.y - point.forward * scale;
      if (index) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    });
    ctx.stroke();
  }
  const current = latestVisualOdometry;
  const position = byId('world-map-odometry-position');
  const [forward = 0, lateral = 0] = current?.position_m || [];
  if (position) position.textContent = `${forward.toFixed(2)} m fwd · ${lateral.toFixed(2)} m left`;
  ctx.save();
  ctx.translate(center.x - lateral * scale, center.y - forward * scale);
  ctx.rotate(Number(current?.yaw_rad) || 0);
  ctx.fillStyle = '#00d6df'; ctx.strokeStyle = '#e8ffff'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(7, 8); ctx.lineTo(0, 5); ctx.lineTo(-7, 8); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
}

function resizeCloud() {
  if (!cloud) return;
  cloud.resize();
  if (cloudViewport?.classList.contains('is-camera-view')) applyCameraProjection();
  if (cloudPoints && (!cloudCameraInitialized || !cloud.camera.userData.userAdjusted)) {
    if (!cloudPoints.geometry.boundingBox) cloudPoints.geometry.computeBoundingBox();
    const bounds = cloudPoints.geometry.boundingBox;
    const target = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    const verticalFov = THREE.MathUtils.degToRad(cloud.camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * cloud.camera.aspect);
    const verticalDistance = size.y / (2 * Math.tan(verticalFov / 2));
    const horizontalDistance = size.x / (2 * Math.tan(horizontalFov / 2));
    const distance = Math.max(verticalDistance, horizontalDistance, 0.8) * 0.82 + size.z * 0.18;
    cloud.camera.userData.target = target;
    cloud.camera.position.copy(target).add(new THREE.Vector3(0, Math.max(0.2, size.y * 0.1), distance));
    cloudCameraInitialized = true;
  }
  cloud.camera.lookAt(cloud.camera.userData.target || new THREE.Vector3());
  cloud.render();
}

function setCloudPreset(preset) {
  if (!cloud || !cloudPoints) return;
  if (preset === 'camera') {
    cloudViewport?.classList.add('is-camera-view');
    cloud.resize();
    const intrinsics = cameraIntrinsicsForImage(cloudDepthImage);
    cloud.camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan((cloudDepthImage?.height || 480) / (2 * intrinsics.fy)));
    cloud.camera.userData.userAdjusted = true;
    const mount = cameraMountPose();
    const attitude = attitudeQuaternion(latestDepthCapturedAt) || new THREE.Quaternion();
    const cameraRotation = attitude.multiply(mount.rotation);
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(cameraRotation);
    cloud.camera.userData.target = mount.position.clone().add(forward);
    cloud.camera.position.copy(mount.position);
    cloud.camera.up.set(0, 1, 0).applyQuaternion(cameraRotation);
    cloud.camera.lookAt(cloud.camera.userData.target);
    applyCameraProjection();
    updateCloudRadar();
    updateCloudOdometry();
    updateCloudHud();
    const depthSnapshot = latestSensorDepth;
    if (depthSnapshot) {
      void cameraFrameForDepth(depthSnapshot).then(async frame => {
        if (latestSensorDepth?.frame_id !== depthSnapshot.frame_id) return false;
        if (frame) return updateCloudCameraPlane(frame);
        if (cloudCameraPlane) cloudCameraPlane.visible = false;
        updateCloudHud();
        return false;
      }).then(() => cloud.render()).catch(error => console.warn('Could not load camera-aligned 3D background:', error));
    }
    cloud.render();
    return;
  }
  cloudViewport?.classList.remove('is-camera-view');
  cloud.camera.fov = 42;
  cloud.resize();
  if (!cloudPoints.geometry.boundingBox) cloudPoints.geometry.computeBoundingBox();
  const bounds = cloudPoints.geometry.boundingBox;
  const target = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const distance = Math.max(size.x, size.y, size.z, 2) * 0.95;
  const offsets = {
    top: new THREE.Vector3(0, distance, -0.01),
    side: new THREE.Vector3(distance, Math.max(0.2, size.y * 0.12), 0),
    follow: new THREE.Vector3(0, Math.max(0.7, size.y * 0.24), distance * 0.78),
  };
  cloud.camera.userData.userAdjusted = true;
  cloud.camera.userData.target = target;
  cloud.camera.position.copy(target).add(offsets[preset] || offsets.follow);
  cloud.camera.up.set(0, preset === 'top' ? 0 : 1, preset === 'top' ? -1 : 0);
  cloud.camera.lookAt(target);
  updateCloudRadar();
  updateCloudOdometry();
  updateCloudHud();
  cloud.render();
}

function updateCloudHud() {
  const metricFrame = Boolean(metricDepthCalibration?.available && latestSensorDepth?.depth_raw_png_base64);
  const points = byId('world-map-cloud-hud-points');
  const depth = byId('world-map-cloud-hud-depth');
  const age = byId('world-map-cloud-hud-age');
  const sync = byId('world-map-cloud-hud-sync');
  const fps = byId('world-map-cloud-hud-fps');
  if (points) points.textContent = `${cloudPointCount.toLocaleString()} points`;
  if (depth) depth.textContent = `MiDaS ${latestSensorDepth?.latency_ms == null ? '—' : `${Number(latestSensorDepth.latency_ms).toFixed(1)} ms`}`;
  const renderedDepthAt = Number(cloudDepthImage?.capturedAt) || 0;
  const frameAge = renderedDepthAt > 0 ? Math.max(0, Date.now() / 1000 - renderedDepthAt) : NaN;
  if (age) age.textContent = Number.isFinite(frameAge) ? `Frame ${frameAge.toFixed(1)} s` : 'Frame —';
  if (sync) {
    const cameraAt = Number(latestCameraFrame?.captured_at);
    const depthAt = Number(cloudDepthImage?.capturedAt);
    const delta = cameraAt > 0 && depthAt > 0 ? Math.abs(cameraAt - depthAt) : NaN;
    const pairedState = cloudPairedCameraFrameId === cloudDepthImage?.frameId ? 'camera matched' : 'depth view';
    const frameId = String(cloudDepthImage?.frameId || '—').slice(-14);
    sync.textContent = Number.isFinite(delta)
      ? `D ${frameId} · camera Δ ${delta.toFixed(1)} s · MiDaS cloud · ${pairedState}`
      : `D ${frameId} · MiDaS cloud · ${pairedState}`;
  }
  const now = performance.now();
  const elapsed = now - cloudFpsStartedAt;
  if (fps && elapsed >= 500) {
    fps.textContent = `3D ${Math.round(cloudFpsFrames * 1000 / elapsed)} FPS`;
    cloudFpsFrames = 0; cloudFpsStartedAt = now;
  }
  const caption = byId('world-map-cloud-depth-caption');
  const intrinsics = cameraIntrinsicsForImage(cloudDepthImage);
  const fovText = intrinsics.calibrated ? 'camera intrinsics calibrated' : `camera FOV estimated ${cameraRadarGeometry.horizontalFovDeg}°`;
  if (caption) caption.textContent = metricFrame
    ? `Depth in metres · ${fovText}; radar remains independent`
    : `Relative units · shape only; ${fovText}; no metric scale`;
  const scale = cloudViewport?.querySelector('.world-map-cloud-scale');
  if (scale) scale.hidden = true;
  // The origin axes and reference grid remain useful for shape-only depth; only
  // their units change. Hide scene furniture in the pixel-aligned Camera preset.
  if (cloudGuides) cloudGuides.visible = !cloudViewport?.classList.contains('is-camera-view');
  if (cloudOriginGroup) cloudOriginGroup.visible = !cloudViewport?.classList.contains('is-camera-view');
  if (cloudCameraPlane) cloudCameraPlane.visible = Boolean(cloudViewport?.classList.contains('is-camera-view'));
}

function updateCloudLabelPositions() {
  if (!cloud || !cloudLabelRoot || !cloudViewport || cloudLabelRoot.hidden) return;
  const rect = cloudViewport.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  cloud.camera.updateMatrixWorld();
  const occupied = [];
  for (const item of cloudLabelItems) {
    const point = item.position.clone().project(cloud.camera);
    const label = item.element;
    const visible = point.z >= -1 && point.z <= 1 && point.x >= -1.15 && point.x <= 1.15 && point.y >= -1.15 && point.y <= 1.15;
    label.hidden = !visible;
    if (!visible) continue;
    const x = THREE.MathUtils.clamp((point.x + 1) * rect.width / 2, 8, rect.width - 8);
    if (item.marker) {
      label.style.left = `${x}px`;
      label.style.top = `${THREE.MathUtils.clamp((1 - point.y) * rect.height / 2, 10, rect.height - 10)}px`;
      continue;
    }
    let y = THREE.MathUtils.clamp((1 - point.y) * rect.height / 2 - 12, 36, rect.height - 24);
    label.style.left = `${x}px`;
    label.style.top = `${y}px`;
    const labelWidth = Math.min(label.offsetWidth || 150, rect.width - 16);
    const labelHeight = label.offsetHeight || 24;
    let tries = 0;
    while (tries < 12) {
      const candidate = { left: THREE.MathUtils.clamp(x - labelWidth / 2, 8, rect.width - labelWidth - 8), top: y - labelHeight, right: 0, bottom: y };
      candidate.right = candidate.left + labelWidth;
      const collides = occupied.some(other => candidate.left < other.right + 4 && candidate.right > other.left - 4 && candidate.top < other.bottom + 3 && candidate.bottom > other.top - 3);
      if (!collides) { occupied.push(candidate); label.style.left = `${candidate.left + labelWidth / 2}px`; break; }
      y = y - labelHeight - 5;
      if (y < labelHeight + 28) y = Math.min(rect.height - 8, y + (tries + 1) * (labelHeight + 5));
      label.style.top = `${y}px`;
      tries += 1;
    }
    if (tries === 12) label.hidden = true;
  }
}

function setCloudLayerLabels(layer, entries) {
  cloudLabelItems = cloudLabelItems.filter(item => item.layer !== layer);
  for (const entry of entries) {
    const element = document.createElement('span');
    element.className = entry.marker
      ? `world-map-cloud-radar-dot${entry.motionClass ? ` ${entry.motionClass}` : ''}`
      : 'world-map-cloud-object-label';
    element.textContent = entry.text || '';
    cloudLabelRoot?.append(element);
    cloudLabelItems.push({ ...entry, layer, element });
  }
  cloudLabelRoot?.querySelectorAll('.world-map-cloud-object-label,.world-map-cloud-radar-dot').forEach(element => {
    if (!cloudLabelItems.some(item => item.element === element)) element.remove();
  });
  updateCloudLabelPositions();
}

function updateCloudRadar(sample = latestRadarSample, force = false) {
  if (!cloud) return;
  const enabled = cloudViewport?.querySelector('[data-cloud-layer="radar"]')?.checked === true;
  const targets = sample?.targets || [];
  const targetKey = targets.map(target => {
    const position = target.position_m || target.position || [];
    return `${target.id || target.target_id || ''}:${position[0]}:${position[1]}:${target.radial_speed_mps}`;
  }).join('|');
  const sampleKey = `${enabled}:${sample?.timestamp || 'none'}:${targetKey}:${cloudViewport?.classList.contains('is-camera-view')}`;
  if (!force && sampleKey === cloudRadarRenderKey) return;
  cloudRadarRenderKey = sampleKey;
  clearCloudGroup(cloudRadarGroup);
  const labels = [];
  cloudRadarGroup.visible = enabled;
  for (const [index, target] of targets.entries()) {
    const position = target.position_m || target.position || [];
    const lateral = Number(position[0]), forward = Number(position[1]);
    if (!Number.isFinite(lateral) || !Number.isFinite(forward) || forward < 0 || forward > 12) continue;
    const point = bodyPointToScene(new THREE.Vector3(lateral, 0, -forward), sample.timestamp);
    updateCloudOrigin(sample.timestamp);
    const odometryAge = Number(latestVisualOdometry?.captured_at) > 0
      ? Date.now() / 1000 - Number(latestVisualOdometry.captured_at) : Infinity;
    const egoMotionLikely = latestVisualOdometry?.available && odometryAge <= 0.35
      && Number(latestVisualOdometry.confidence) >= 0.35
      && Number(latestVisualOdometry.speed_mps) >= 0.05;
    const moving = Math.abs(Number(target.radial_speed_mps) || 0) >= 0.05 && !egoMotionLikely;
    const markerColor = egoMotionLikely ? '#9aa7ad' : moving ? '#ed35c5' : '#f2bc65';
    // MiDaS points are dense and write depth; radar is an independent metric overlay.
    const halo = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 10), new THREE.MeshBasicMaterial({
      color: markerColor, transparent: true, opacity: 0.24, depthTest: false, depthWrite: false,
    }));
    halo.position.copy(point);
    halo.renderOrder = 20;
    cloudRadarGroup.add(halo);
    const marker = new THREE.Mesh(new THREE.SphereGeometry(0.055, 16, 12), new THREE.MeshBasicMaterial({
      color: markerColor, depthTest: false, depthWrite: false,
    }));
    marker.position.copy(point);
    marker.renderOrder = 21;
    cloudRadarGroup.add(marker);
    labels.push({ position: point, marker: true, motionClass: egoMotionLikely ? 'is-ego-motion' : moving ? 'is-moving' : '' });
    labels.push({ position: point.clone().add(new THREE.Vector3(0, 0.16, 0)), text: `${target.id || target.target_id || `Radar ${index + 1}`} · ${forward.toFixed(1)} m forward${egoMotionLikely ? ' · radial motion ego-uncompensated' : ''}` });
  }
  setCloudLayerLabels('radar', labels);
  if (activeRender === '3d') cloud.render();
}

function updateCloudOdometry() {
  if (!cloud) return;
  clearCloudGroup(cloudOdometryGroup);
  const enabled = cloudViewport?.querySelector('[data-cloud-layer="odometry"]')?.checked !== false
    && !cloudViewport?.classList.contains('is-camera-view');
  cloudOdometryGroup.visible = enabled;
  if (visualOdometryTrail.length < 2) return;
  const bodyHeight = cameraMountPose().heightM;
  const points = visualOdometryTrail.map(point => new THREE.Vector3(-point.lateral, bodyHeight, -point.forward));
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: '#ed35c5', linewidth: 2 }));
  cloudOdometryGroup.add(line);
  cloud.render();
}

function clearCloudGroup(group) {
  for (const child of [...group.children]) {
    group.remove(child);
    child.traverse?.(node => { node.geometry?.dispose(); node.material?.dispose?.(); });
  }
}

async function loadGrayDepth(base64) {
  return loadDepthImage(base64, 'image/jpeg');
}

async function loadDepthImage(base64, mimeType) {
  const image = new Image();
  image.src = `data:${mimeType};base64,${base64}`;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  return { width: canvas.width, height: canvas.height, values: context.getImageData(0, 0, canvas.width, canvas.height).data };
}

async function loadClassMask(base64) {
  if (!base64) return null;
  const image = new Image();
  image.src = `data:image/png;base64,${base64}`;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  return { width: canvas.width, height: canvas.height, values: context.getImageData(0, 0, canvas.width, canvas.height).data };
}

const semanticClassColors = new Map([
  [0, '#ef8354'],   // wall
  [3, '#00b4d8'],   // floor
  [5, '#9b5de5'],   // ceiling
  [12, '#ff4d6d'],  // person
  [14, '#ff9f1c'],  // door
  [15, '#ffd166'],  // table
  [17, '#70e000'],  // plant
  [19, '#00f5d4'],  // chair
  [22, '#e76f51'],  // painting
  [27, '#4361ee'],  // mirror
  [89, '#3a86ff'],  // television receiver
  [130, '#c77dff'], // screen
  [141, '#fb5607'], // crt screen
  [143, '#80ed99'], // monitor
]);

function semanticColor(classId) {
  if (semanticClassColors.has(Number(classId))) {
    return new THREE.Color(semanticClassColors.get(Number(classId)));
  }
  const hue = (Number(classId) * 137.508 + 18) % 360;
  return new THREE.Color().setHSL(hue / 360, 0.72, 0.58);
}

function segmentationMatchesDepth(segmentation, depth) {
  if (!segmentation?.available || !segmentation.mask_png_base64) return false;
  if (segmentation.frame_id && segmentation.frame_id === depth.frame_id) return true;
  const segmentationTime = Number(segmentation.captured_at);
  const depthTime = Number(depth.captured_at);
  return Number.isFinite(segmentationTime) && Number.isFinite(depthTime)
    && Math.abs(segmentationTime - depthTime) <= 0.25;
}

async function rebuildDepthCloud(depth, segmentation = latestSegmentation) {
  if (!cloud || !depth.depth_gray_jpeg_base64) return;
  const token = ++cloudBuildToken;
  const image = await loadDepthFrame(depth);
  const colorImage = depth.depth_jpeg_base64
    ? await loadGrayDepth(depth.depth_jpeg_base64) : image;
  const classMask = segmentationMatchesDepth(segmentation, depth)
    ? await loadClassMask(segmentation.mask_png_base64) : null;
  if (token !== cloudBuildToken || activeSource !== 'sensors' || activeRender !== '3d') return false;
  cloudDepthImage = image;
  cloudFrameId = String(depth.frame_id || '');
  cloudPairedCameraFrameId = '';
  cloudSegmentationFrameId = segmentationMatchesDepth(segmentation, depth)
    ? String(segmentation.frame_id || segmentation.captured_at || '') : '';
  cloudDepthYolo = null;
  latestDepthCapturedAt = Number(depth.captured_at) || 0;
  updateCloudOrigin(latestDepthCapturedAt);
  cloudCameraPlaneToken += 1;
  const frameCalibration = metricDepthCalibration;
  updateCloudHud();
  const intrinsics = cameraIntrinsicsForImage(image);
  const stride = Math.max(3, Math.ceil(Math.max(image.width, image.height) / 120));
  const positions = [];
  const colorsArray = [];
  for (let y = 0; y < image.height; y += stride) {
    for (let x = 0; x < image.width; x += stride) {
      const index = (y * image.width + x) * 4;
      const distance = depthForScene(image, index, frameCalibration);
      const point = cameraPointInBodyFrame(cameraPoint(x, y, distance, intrinsics), Number(depth.captured_at) || latestDepthCapturedAt);
      positions.push(point.x, point.y, point.z);
      const colorX = Math.min(colorImage.width - 1, Math.round(x * colorImage.width / image.width));
      const colorY = Math.min(colorImage.height - 1, Math.round(y * colorImage.height / image.height));
      const colorIndex = (colorY * colorImage.width + colorX) * 4;
      const classMaskIndex = classMask
        ? (Math.min(classMask.height - 1, Math.round(y * classMask.height / image.height)) * classMask.width
          + Math.min(classMask.width - 1, Math.round(x * classMask.width / image.width))) * 4
        : -1;
      if (classMask && classMask.values[classMaskIndex + 3] > 0) {
        const maskX = Math.min(classMask.width - 1, Math.round(x * classMask.width / image.width));
        const maskY = Math.min(classMask.height - 1, Math.round(y * classMask.height / image.height));
        const classId = classMask.values[(maskY * classMask.width + maskX) * 4];
        const semantic = semanticColor(classId);
        colorsArray.push(semantic.r, semantic.g, semantic.b);
      } else {
        colorsArray.push(
          colorImage.values[colorIndex] / 255,
          colorImage.values[colorIndex + 1] / 255,
          colorImage.values[colorIndex + 2] / 255,
        );
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colorsArray, 3));
  geometry.computeBoundingBox();
  cloudPointCount = positions.length / 3;
  const layerEnabled = cloudViewport?.querySelector('[data-cloud-layer="cloud"]')?.checked !== false;
  if (cloudPoints) {
    const previousGeometry = cloudPoints.geometry;
    cloudPoints.geometry = geometry;
    cloudPoints.visible = layerEnabled;
    previousGeometry.dispose();
  } else {
    cloudPoints = new THREE.Points(geometry, new THREE.PointsMaterial({ size: Number(byId('world-map-cloud-point-size')?.value || 25) / 1000, vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 0.92 }));
    cloudPoints.visible = layerEnabled;
    cloud.scene.add(cloudPoints);
  }
  updateCloudRadar();
  updateCloudOdometry();
  resizeCloud();
  // Camera RGB and YOLO pairing are optional overlays; neither may hold up
  // the depth geometry or cause the polling loop to cancel every rebuild.
  void yoloResultForDepth(depth).then(frameYolo => {
    if (token !== cloudBuildToken) return;
    cloudDepthYolo = frameYolo;
    drawDepthDetections(image, frameYolo, frameCalibration);
  }).catch(error => console.warn('Could not pair YOLOX with MiDaS frame:', error));
  const pairedFramePromise = cameraFrameForDepth(depth);
  void pairedFramePromise.then(async frame => {
    if (token !== cloudBuildToken || !frame?.image_base64) return;
    const sourceImage = await loadDepthImage(frame.image_base64, frame.mime_type || 'image/jpeg');
    if (token !== cloudBuildToken || cloudPoints?.geometry !== geometry) return;
    let pointIndex = 0;
    const colors = geometry.attributes.color.array;
    for (let y = 0; y < image.height; y += stride) {
      for (let x = 0; x < image.width; x += stride) {
        const maskX = classMask ? Math.min(classMask.width - 1, Math.round(x * classMask.width / image.width)) : 0;
        const maskY = classMask ? Math.min(classMask.height - 1, Math.round(y * classMask.height / image.height)) : 0;
        const maskIndex = classMask ? (maskY * classMask.width + maskX) * 4 : -1;
        if (!classMask || classMask.values[maskIndex + 3] === 0) {
          const sourceX = Math.min(sourceImage.width - 1, Math.round(x * sourceImage.width / image.width));
          const sourceY = Math.min(sourceImage.height - 1, Math.round(y * sourceImage.height / image.height));
          const sourceIndex = (sourceY * sourceImage.width + sourceX) * 4;
          colors[pointIndex * 3] = sourceImage.values[sourceIndex] / 255;
          colors[pointIndex * 3 + 1] = sourceImage.values[sourceIndex + 1] / 255;
          colors[pointIndex * 3 + 2] = sourceImage.values[sourceIndex + 2] / 255;
        }
        pointIndex += 1;
      }
    }
    cloudPairedCameraFrameId = frame.frame_id;
    geometry.attributes.color.needsUpdate = true;
    updateCloudHud();
    cloud.render();
  }).catch(error => console.warn('Could not color MiDaS cloud with paired camera frame:', error));
  if (cloudViewport?.classList.contains('is-camera-view')) {
    void pairedFramePromise.then(frame => {
      if (token === cloudBuildToken && frame) return updateCloudCameraPlane(frame);
      return false;
    }).then(() => cloud.render()).catch(error => console.warn('Could not load camera-aligned 3D background:', error));
  }
  return true;
}

function detectionDepthStats(image, bbox, calibration, identity) {
  const [x1, y1, x2, y2] = bbox.map(Number);
  const person = /person|human/i.test(identity);
  const insetX = person ? 0.25 : 0.15;
  const left = Math.max(0, Math.floor((x1 + (x2 - x1) * insetX) * image.width));
  const right = Math.min(image.width, Math.ceil((x2 - (x2 - x1) * insetX) * image.width));
  const top = Math.max(0, Math.floor((y1 + (y2 - y1) * (person ? 0.2 : 0.15)) * image.height));
  const bottom = Math.min(image.height, Math.ceil((y1 + (y2 - y1) * (person ? 0.72 : 0.85)) * image.height));
  const step = Math.max(1, Math.floor(Math.min(right - left, bottom - top) / 12));
  const values = [];
  for (let y = top; y < bottom; y += step) for (let x = left; x < right; x += step) {
    values.push(depthForScene(image, (y * image.width + x) * 4, calibration));
  }
  values.sort((a, b) => a - b);
  if (!values.length) return null;
  const quantile = q => values[Math.min(values.length - 1, Math.floor((values.length - 1) * q))];
  return { near: quantile(0.1), median: quantile(0.5), far: quantile(0.9) };
}

function drawDepthDetections(image, yolo, calibration = metricDepthCalibration) {
  if (!cloud || !image || activeRender !== '3d') return;
  const layerEnabled = cloudViewport?.querySelector('[data-cloud-layer="detections"]')?.checked !== false;
  const yoloAge = Number(yolo?.captured_at) > 0 ? Date.now() / 1000 - Number(yolo.captured_at) : Infinity;
  const yoloFrameDelta = yolo?.frame_delta_s != null && Number.isFinite(Number(yolo.frame_delta_s))
    ? Number(yolo.frame_delta_s)
    : Math.abs(Number(yolo?.captured_at) - Number(image.capturedAt));
  const frameMatches = Boolean(image.frameId && yolo?.frame_id === image.frameId)
    || Number.isFinite(yoloFrameDelta) && yoloFrameDelta <= 0.75;
  const detections = layerEnabled && frameMatches && yolo?.state === 'ready' && yoloAge >= 0 && yoloAge <= 2.5
    ? (yolo.detections || []) : [];
  const detectionKey = `${layerEnabled}:${cloudFrameId}:${yolo?.frame_id || ''}:${detections.length}:${Number(latestDepthCapturedAt).toFixed(3)}`;
  if (detectionKey === cloudDetectionKey) return;
  cloudDetectionKey = detectionKey;

  const nextGroup = new THREE.Group();
  const htmlLabels = [];
  const colorsByKind = ['#55e7cc', '#f2bc65', '#e280ba', '#77d69c'];
  const metricFrame = Boolean(calibration?.available && Number.isFinite(image.rawMin) && Number.isFinite(image.rawMax));
  const alignedRadarSample = frameMatches && metricFrame && yoloFrameDelta <= 0.15
    ? radarSampleAt(latestDepthCapturedAt, 0.1) : null;
  const radarMatches = alignedRadarSample ? matchedRadarAnchors(detections, alignedRadarSample, image) : [];
  for (const [index, item] of detections.entries()) {
    const bbox = item.bbox;
    if (!Array.isArray(bbox) || bbox.length < 4 || !bbox.every(value => Number.isFinite(Number(value)))) continue;
    const [x1, y1, x2, y2] = bbox.map(Number);
    const identity = String(item.label || item.class_name || item.class || 'object');
    const stats = detectionDepthStats(image, bbox, calibration, identity);
    if (!stats) continue;
    const radarAnchor = radarMatches.find(match => match.detection === item);
    const medianRange = frameMatches && metricFrame ? metricDepthEstimate(stats.median, calibration) : null;
    const medianDepth = radarAnchor ? radarAnchor.forward : stats.median;
    const observedSpan = Math.max(0, stats.far - stats.near);
    const maximumSpan = metricFrame
      ? Math.min(0.6, Math.max(0.15, medianDepth * 0.3))
      : Math.min(0.35, Math.max(0.02, medianDepth * 0.05));
    const depthSpan = Math.min(observedSpan, maximumSpan);
    const nearZ = Math.max(0.15, medianDepth - depthSpan / 2);
    const farZ = Math.max(nearZ + (metricFrame ? 0.03 : 0.01), medianDepth + depthSpan / 2);
    const intrinsics = cameraIntrinsicsForImage(image);
    const corners = [
      cameraPointInBodyFrame(cameraPoint(x1 * image.width, y1 * image.height, nearZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x2 * image.width, y1 * image.height, nearZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x2 * image.width, y2 * image.height, nearZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x1 * image.width, y2 * image.height, nearZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x1 * image.width, y1 * image.height, farZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x2 * image.width, y1 * image.height, farZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x2 * image.width, y2 * image.height, farZ, intrinsics), latestDepthCapturedAt),
      cameraPointInBodyFrame(cameraPoint(x1 * image.width, y2 * image.height, farZ, intrinsics), latestDepthCapturedAt),
    ];
    const edgeIndices = [0, 1, 1, 2, 2, 3, 3, 0, 4, 5, 5, 6, 6, 7, 7, 4, 0, 4, 1, 5, 2, 6, 3, 7];
    const material = new THREE.LineBasicMaterial({ color: colorsByKind[index % colorsByKind.length], depthTest: false, transparent: true, opacity: 0.95 });
    nextGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(edgeIndices.map(corner => corners[corner])), material,
    ));
    const labelPosition = cameraPointInBodyFrame(cameraPoint((x1 + x2) * image.width / 2, y1 * image.height, nearZ, intrinsics), latestDepthCapturedAt);
    const confidence = Math.round(Number(item.confidence ?? item.score ?? 0) * 100);
    const rangeLabel = radarAnchor
      ? `${radarAnchor.forward.toFixed(2)} m · radar measured`
      : medianRange
        ? `${medianRange.extrapolated ? '~' : ''}${medianRange.meters.toFixed(1)} m · MiDaS ${medianRange.extrapolated ? 'extrapolated' : 'est.'}`
        : frameMatches
          ? `${stats.median.toFixed(1)} relative units · MiDaS`
          : 'depth unpaired · relative shape only';
    const syncLabel = yolo?.frame_id !== image.frameId && yoloFrameDelta > 0.15
      ? ` · YOLOX Δ${yoloFrameDelta.toFixed(1)} s` : '';
    const depthAge = image.capturedAt > 0 ? Math.max(0, Date.now() / 1000 - image.capturedAt) : Infinity;
    const staleDepthLabel = depthAge > 1.25 ? ` · MiDaS stale ${depthAge.toFixed(1)} s` : '';
    htmlLabels.push({ position: labelPosition, text: `${identity} ${confidence}% · ${rangeLabel}${syncLabel}${staleDepthLabel}` });
  }

  if (boxGroup) {
    cloud.scene.remove(boxGroup);
    boxGroup.traverse(node => { node.geometry?.dispose(); node.material?.dispose?.(); });
  }
  boxGroup = nextGroup;
  boxGroup.visible = layerEnabled;
  cloud.scene.add(boxGroup);
  setCloudLayerLabels('detections', htmlLabels);
  cloud.render();
}

window.updateBodyWorldMap3D = (world) => {
  latestWorld = world;
  if (activeSource === 'simulation' && activeRender === '3d') buildSimulation(world);
};

setInterval(() => {
  if (activeSource === 'sensors') {
    void refreshSensors();
    void refreshSensorDepth();
  }
}, 75);
setInterval(() => {
  if (activeSource !== 'sensors') return;
  void refreshLiveRadar();
}, 100);
setInterval(() => { void refreshSystemMetrics(); }, 1000);
setInterval(() => {
  if (activeSource !== 'sensors') return;
  void refreshLiveGps();
  void refreshLiveImu();
  void refreshLiveTof();
}, 250);
setInterval(() => {
  if (activeSource === 'sensors') void refreshSensorSegmentation();
}, 500);
setInterval(() => {
  if (activeSource === 'sensors') void refreshVisualOdometry();
}, 250);
if (latestWorld) buildSimulation(latestWorld);
