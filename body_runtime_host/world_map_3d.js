import * as THREE from '../frontend/node_modules/three/build/three.module.js';

const byId = (id) => document.getElementById(id);
let latestSensorDepth = null;
let lastSensorDepthAt = 0;
let sensorDepthBusy = false;
let latestSensorYolo = null;
let latestSegmentation = null;
let latestCameraFrame = null;
let renderedSegmentationFrameId = '';
let displayedCameraFrameId = null;
let displayedYoloOverlayKey = '';
let cloudDepthImage = null;
let cloudBuildToken = 0;
let cloudYoloFrameId = '';
let cloudSegmentationFrameId = '';
let metricDepthCalibration = null;
let depthCalibrationBusy = false;
let depthCalibrationMessage = '';
const visualOdometryTrail = [];
let visualOdometryFrameId = '';
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
    sensorPanel.innerHTML = `<div class="world-map-sensor-metrics"><span>Camera <b id="world-map-camera-state">Waiting</b></span><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Visual odometry <b id="world-map-odometry-state">Waiting</b></span><span>SegFormer <b id="world-map-segmentation-state">disabled</b></span><span>Frame <b id="world-map-frame-state">—</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA · YOLOX</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS · RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate">Calibrate with radar</button><small id="world-map-midas-calibration-status" role="status">Relative depth only · not calibrated in metres</small></div></div></div><section class="world-map-odometry-view" aria-label="Experimental visual odometry trajectory"><div class="world-map-sensor-heading"><span>VISUAL ODOMETRY · LOCAL TRAJECTORY</span><small id="world-map-odometry-map-status">Waiting for tracking</small></div><svg id="world-map-odometry-map" viewBox="0 0 640 260" role="img" aria-label="Top-down estimated Body trajectory in the local visual odometry frame"><rect class="odom-map-bg" x="0" y="0" width="640" height="260"/><g class="odom-grid"><path d="M40 45H600M40 85H600M40 125H600M40 165H600M40 205H600M80 25V225M160 25V225M240 25V225M320 25V225M400 25V225M480 25V225M560 25V225"/><path class="odom-axis" d="M40 205H600M320 25V225"/></g><text class="odom-axis-label" x="320" y="18" text-anchor="middle">FORWARD ↑</text><text class="odom-axis-label" x="320" y="249" text-anchor="middle">← LEFT · RIGHT →</text><g id="world-map-odometry-grid-labels"></g><polyline id="world-map-odometry-trail" points=""/><circle id="world-map-odometry-start" cx="320" cy="205" r="4"/><g id="world-map-odometry-body" transform="translate(320 205)"><path d="M0 -11 L7 8 L0 5 L-7 8 Z"/></g><text id="world-map-odometry-position" class="odom-position-label" x="332" y="200">0.00, 0.00 m</text></svg><p class="world-map-odometry-footnote">Session-local estimate · drift accumulates · not a persistent map</p></section><section class="world-map-segmentation-panel" aria-label="SegFormer semantic segmentation"><div class="world-map-sensor-heading"><span>SEGFORMER · SEMANTIC MASK</span><small>Independent of camera preview</small></div><div class="world-map-segmentation-preview"><canvas id="world-map-segmentation-overlay" aria-label="Standalone SegFormer semantic class mask" hidden></canvas><span id="world-map-segmentation-empty" class="world-map-empty">Waiting for a SegFormer mask</span></div><div id="world-map-segmentation-classes" class="world-map-segmentation-classes">Waiting for SegFormer classes</div></section><div id="world-map-sensor-3d" class="world-map-canvas world-map-sensor-cloud" hidden></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view · no simulation object positions are used.</p>`;
    const liveReadouts = document.createElement('section');
    liveReadouts.id = 'world-map-live-readouts';
    liveReadouts.className = 'world-map-live-readouts';
    liveReadouts.innerHTML = `<article class="sensor-readout-card sensor-readout-wide"><header><strong>mmWave · LD2450</strong><small id="world-map-radar-state">Waiting</small></header><canvas id="world-map-radar-plot" height="190" aria-label="Live mmWave target positions and radial velocities"></canvas><div id="world-map-radar-targets" class="sensor-target-list">Waiting for radar data.</div></article><article class="sensor-readout-card"><header><strong>GPS / GNSS · D0/D1</strong><small id="world-map-gps-state">Waiting</small></header><div class="sensor-readout-values"><span>Position<b id="world-map-gps-position">No fix</b></span><span>Fix / quality<b id="world-map-gps-fix">—</b></span><span>Satellites<b id="world-map-gps-satellites">— used · — in view</b></span><span>HDOP / altitude<b id="world-map-gps-quality">—</b></span></div><div id="world-map-gps-signals" class="sensor-gps-signals" role="img" aria-label="GPS satellite signal strength by satellite"></div></article><article class="sensor-readout-card"><header><strong>Modulino Movement · IMU</strong><small id="world-map-imu-state">Waiting</small></header><div class="sensor-readout-values"><span>Roll<b id="world-map-imu-roll">—</b></span><span>Pitch<b id="world-map-imu-pitch">—</b></span><span>Yaw rate<b id="world-map-imu-yaw">—</b></span><span>Acceleration · g<b id="world-map-imu-accel">—</b></span><span>Angular rate · °/s<b id="world-map-imu-gyro">—</b></span></div><p class="sensor-readout-note">Six-axis IMU; yaw is relative angular rate, not a magnetic heading.</p></article><article class="sensor-readout-card"><header><strong>ToF · VL53L1X</strong><small id="world-map-tof-state">Waiting</small></header><div class="sensor-distance"><b id="world-map-tof-distance">—</b><span id="world-map-tof-meta">Forward single-beam range</span></div></article><article class="sensor-readout-card"><header><strong>LiDAR</strong><small id="world-map-lidar-state">No live source</small></header><p class="sensor-readout-note">No physical LiDAR stream is connected to this Body view. Any LiDAR volume shown in Simulation is virtual and is kept out of this live sensor view.</p></article><article class="sensor-readout-card"><header><strong>Ultrasonic · HC-SR04</strong><small id="world-map-ultrasonic-state">No live source</small></header><div class="sensor-readout-values sensor-range-channels"><span>Front-left<b id="world-map-ultrasonic-left">No data</b></span><span>Front-right<b id="world-map-ultrasonic-right">No data</b></span><span>Rear<b id="world-map-ultrasonic-rear">No data</b></span></div><p class="sensor-readout-note">Waiting for the ultrasonic firmware/gateway data channel; no simulated ranges are shown here.</p></article>`;
    const computeCard = document.createElement('article');
    computeCard.className = 'sensor-readout-card sensor-readout-wide';
    computeCard.innerHTML = `<header><strong>Compute & power</strong><small id="world-map-system-state">Sampling</small></header><div class="system-instrument-grid"><article class="system-instrument"><span class="system-instrument-label">CPU LOAD</span><div class="system-gauge" id="world-map-cpu-gauge" role="img" aria-label="CPU utilization"><div class="system-gauge-center"><strong id="world-map-system-cpu-value">—</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-cpu-temp">CPU temp · —</span></article><article class="system-instrument"><span class="system-instrument-label">CPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-cpu-temp-gauge" role="img" aria-label="Maximum CPU temperature"><div class="system-gauge-center"><strong id="world-map-system-cpu-temp-value">—</strong><small>°C</small></div></div><span class="system-instrument-foot">Hottest reported CPU sensor · 0–100 °C</span></article><article class="system-instrument"><span class="system-instrument-label">GPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-gpu-temp-gauge" role="img" aria-label="Maximum GPU temperature"><div class="system-gauge-center"><strong id="world-map-system-gpu-temp-value">—</strong><small>°C</small></div></div><span class="system-instrument-foot" id="world-map-system-gpu-meta">Load unavailable · — MHz</span></article><article class="system-instrument"><span class="system-instrument-label">MEMORY</span><div class="system-gauge" id="world-map-memory-gauge" role="img" aria-label="Memory utilization"><div class="system-gauge-center"><strong id="world-map-system-memory-value">—</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-memory-meta">— free</span></article><article class="system-instrument"><span class="system-instrument-label">BOARD INPUT</span><div class="system-gauge system-gauge-power" id="world-map-power-gauge" role="img" aria-label="Measured board input power"><div class="system-gauge-center"><strong id="world-map-system-power-value">—</strong><small>W</small></div></div><span class="system-instrument-foot" id="world-map-system-power-meta">INA232 · measured rail</span></article></div><div class="system-telemetry-strip"><div><span>GPU utilization</span><strong id="world-map-system-gpu-load">Unavailable</strong></div><div><span>GPU clock</span><strong id="world-map-system-gpu-clock">—</strong></div><div><span>Qualcomm HTP</span><strong id="world-map-system-htp">Waiting for inference status</strong></div><div><span>Energy since Body start</span><strong id="world-map-system-energy">—</strong></div></div><p id="world-map-system-note" class="sensor-readout-note">GPU/HTP usage percentages require kernel counters. Board input may exclude external motor loads.</p>`;
    liveReadouts.prepend(computeCard);
    sensorPanel.append(liveReadouts);
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
      .world-map-odometry-view{margin-top:12px;background:#07120f;border:1px solid #263e32}
      .world-map-odometry-view>.world-map-sensor-heading{display:flex;justify-content:space-between;gap:12px;align-items:center}
      .world-map-odometry-view>.world-map-sensor-heading small{color:#a9c0b2;font:10px ui-monospace,monospace}
      #world-map-odometry-map{display:block;width:100%;height:clamp(220px,28vh,300px);background:#07120f}
      .odom-map-bg{fill:#07120f}.odom-grid{fill:none;stroke:#254235;stroke-width:1}.odom-grid .odom-axis{stroke:#48745a;stroke-width:1.5}
      .odom-axis-label,.odom-empty-label{fill:#89a895;font:10px ui-monospace,monospace}.odom-position-label{fill:#dceee3;font:11px ui-monospace,monospace}
      #world-map-odometry-trail{fill:none;stroke:#42d6b1;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
      #world-map-odometry-start{fill:#edbd69;stroke:#07120f;stroke-width:2}#world-map-odometry-body path{fill:#75dfa2;stroke:#d9f5e5;stroke-width:1.5}
      .world-map-odometry-footnote{margin:0;padding:0 10px 9px;color:#89a895;font:10px ui-monospace,monospace}
      .world-map-sensor-2d{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(220px,.8fr);gap:12px;align-items:stretch}
      .world-map-camera,.world-map-depth{min-width:0;position:relative;background:#07120f;border:1px solid #263e32;overflow:hidden}
      .world-map-sensor-heading{padding:9px 11px;border-bottom:1px solid #263e32;color:#91c9aa;font:10px ui-monospace,monospace}
      .world-map-image-wrap{position:relative;display:grid;place-items:center;width:100%;aspect-ratio:4/3;max-height:500px;background:#020805;overflow:hidden}
      .world-map-image-wrap img{display:block;width:100%;height:100%;object-fit:fill}
      #world-map-yolo-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      .world-map-depth{display:flex;flex-direction:column}
      .world-map-segmentation-classes{display:flex;gap:7px 12px;flex-wrap:wrap;margin:0;padding:8px 10px;color:#b4c9bc;font:10px ui-monospace,monospace;line-height:1.6}
      .world-map-segmentation-classes span{display:inline-flex;align-items:center;gap:5px}
      .world-map-segmentation-classes i{width:8px;height:8px;flex:0 0 8px;border-radius:50%}
      .world-map-segmentation-panel{min-width:0;margin-top:12px;overflow:hidden;border:1px solid #263e32;background:#07120f}
      .world-map-segmentation-preview{position:relative;display:grid;min-height:180px;max-height:380px;place-items:center;overflow:hidden;background:#020805}
      #world-map-segmentation-overlay{display:block;width:100%;height:auto;max-height:380px;object-fit:contain}
      #world-map-segmentation-overlay[hidden]{display:none!important}
      .world-map-depth img{display:block;width:100%;height:100%;min-height:220px;max-height:500px;object-fit:contain;background:#020805}
      .world-map-depth>small{padding:7px 10px;color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-depth-calibration{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:8px 10px;border-top:1px solid #263e32}
      .world-map-depth-calibration button{border:1px solid #416b54;border-radius:3px;background:#10251a;color:#d9f5e5;padding:7px 10px;cursor:pointer}
      .world-map-depth-calibration button:disabled{opacity:.6;cursor:wait}
      .world-map-depth-calibration small{color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-empty{position:absolute;inset:0;display:grid;place-items:center;padding:20px;color:#91a79a;font:11px ui-monospace,monospace;text-align:center;pointer-events:none}
      .world-map-empty[hidden]{display:none}
      .world-map-sensor-note{margin:9px 0 0;color:#a9c0b2;font-size:11px}
      .world-map-sensor-cloud{height:clamp(360px,54vh,620px)}
      .world-map-live-readouts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}
      .sensor-readout-card{min-width:0;padding:14px;border:1px solid #d7e1da;background:#f7faf8;color:#1c2b22}
      .sensor-readout-card header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-bottom:9px;border-bottom:1px solid #d7e1da}
      .sensor-readout-card header strong{font:650 12px ui-monospace,monospace;color:#1b4734}
      .sensor-readout-card header small{font:10px ui-monospace,monospace;color:#5a7063;text-align:right}
      .sensor-readout-wide{grid-column:1/-1}
      #world-map-radar-plot{display:block;width:100%;height:190px;margin-top:8px;background:#07120f;border:1px solid #203b2d}
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
      .world-map-sensor-view{margin-top:12px}
      body.worldmodel-sensors-active .simulation-actions,
      body.worldmodel-sensors-active #view-worldmodel #wm-simulation-toggle,
      body.worldmodel-sensors-active #view-worldmodel .map-panel .panel-head>button[onclick="expandMap()"]{display:none!important}
      body.worldmodel-sensors-active #view-worldmodel>.stats,body.worldmodel-sensors-active #goal-success{display:none!important}
      @media(max-width:760px){.system-instrument-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip>div:nth-child(2){border-right:0}.system-telemetry-strip>div:nth-child(-n+2){border-bottom:1px solid #d7e1da}}
      @media(max-width:700px){.world-map-sensor-2d,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.sensor-readout-wide{grid-column:auto}.world-map-depth img{max-height:320px}.world-map-controls{gap:7px}}
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
  element.replaceChildren(renderer.domElement);
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
  element.addEventListener('pointerdown', (event) => {
    pointer = [event.clientX, event.clientY];
    camera.userData.userAdjusted = true;
    element.setPointerCapture(event.pointerId);
  });
  element.addEventListener('pointermove', (event) => {
    if (!pointer) return;
    const dx = event.clientX - pointer[0];
    const dy = event.clientY - pointer[1];
    pointer = [event.clientX, event.clientY];
    const offset = camera.position.clone().sub(camera.userData.target || new THREE.Vector3());
    const spherical = new THREE.Spherical().setFromVector3(offset);
    spherical.theta -= dx * 0.006;
    spherical.phi = THREE.MathUtils.clamp(spherical.phi + dy * 0.006, 0.12, Math.PI - 0.12);
    camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(camera.userData.target || new THREE.Vector3()));
    camera.lookAt(camera.userData.target || new THREE.Vector3());
    render();
  });
  element.addEventListener('pointerup', () => { pointer = null; });
  element.addEventListener('pointercancel', () => { pointer = null; });
  element.addEventListener('wheel', (event) => {
    event.preventDefault();
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
let cloud = makeRenderer(byId('world-map-sensor-3d'), '#06100d');
let cloudPoints = null;
let boxGroup = null;
let cloudFrameId = '';
let cloudCameraInitialized = false;
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
      if (cloudDepthImage) drawDepthDetections(cloudDepthImage, visibleYoloDetections(latestSensorYolo));
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
document.querySelectorAll('[data-render]').forEach((button) => button.addEventListener('click', () => setRender(button.dataset.render)));
byId('world-map-midas-calibrate')?.addEventListener('click', () => void calibrateMetricDepth());
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
  await image.decode();
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
    const classId = sourcePixels[index + 2];
    if (!palette.has(classId)) {
      const hex = semanticColor(classId).getHexString();
      palette.set(classId, [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)]);
    }
    const color = palette.get(classId);
    pixels.data[index] = color[0];
    pixels.data[index + 1] = color[1];
    pixels.data[index + 2] = color[2];
    pixels.data[index + 3] = sourcePixels[index + 3] || 255;
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

function relativeDepthToMeters(relativeDepth) {
  const calibration = metricDepthCalibration;
  if (!calibration?.available) return relativeDepth;
  const meters = Number(calibration.scale_m_per_relative_unit) * relativeDepth + Number(calibration.offset_m);
  return Math.max(0.2, Math.min(15, meters));
}

function updateMetricCalibrationStatus() {
  const status = byId('world-map-midas-calibration-status');
  if (!status || depthCalibrationBusy) return;
  if (depthCalibrationMessage) {
    status.textContent = depthCalibrationMessage;
    return;
  }
  if (metricDepthCalibration?.available) {
    const [near, far] = metricDepthCalibration.calibrated_range_m || [];
    status.textContent = `Persistent · ±${Number(metricDepthCalibration.rmse_m).toFixed(2)} m fit · ${metricDepthCalibration.sample_count} anchors · ${near}–${far} m. Applied to all YOLOX objects.`;
  } else {
  status.textContent = 'Uses time-matched camera, YOLOX, MiDaS and LD2450 samples. Move one visible person closer/farther to anchor all YOLOX objects.';
  }
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

function matchedRadarAnchor(detections, sample) {
  const source = String(sample?.source || '').toLowerCase();
  if (!source.startsWith('hlk_ld2450')) return null;
  const targets = Array.isArray(sample.targets) ? sample.targets : [];
  const people = (detections || []).filter(item => /person|human/i.test(String(item.label || item.class_name || item.class || ''))
    && Number(item.confidence ?? item.score ?? 0) >= 0.4 && Array.isArray(item.bbox) && item.bbox.length === 4);
  const matches = [];
  for (const target of targets) {
    const position = target.position_m || target.position;
    if (!Array.isArray(position) || position.length < 2) continue;
    const lateralRight = Number(position[0]);
    const forward = Number(position[1]);
    const distance = Math.hypot(lateralRight, forward);
    if (!Number.isFinite(distance) || distance < 0.25 || distance > 10 || forward <= 0) continue;
    const radarBearing = Math.atan2(lateralRight, forward);
    for (const detection of people) {
      const centerU = (Number(detection.bbox[0]) + Number(detection.bbox[2])) / 2;
      const cameraBearing = Math.atan((centerU - 0.5) * 2 * Math.tan(35 * Math.PI / 180));
      const error = Math.abs((cameraBearing - radarBearing) * 180 / Math.PI);
      if (error <= 15) matches.push({ detection, distance, error });
    }
  }
  matches.sort((a, b) => a.error - b.error);
  return matches[0] || null;
}

async function calibrateMetricDepth() {
  if (depthCalibrationBusy) return;
  const button = byId('world-map-midas-calibrate');
  const status = byId('world-map-midas-calibration-status');
  if (!button || !status) return;
  depthCalibrationBusy = true;
  depthCalibrationMessage = '';
  button.disabled = true;
  button.textContent = 'Calibrating…';
  status.textContent = 'For 60 seconds, keep one person visible and move them at least 0.8 m closer/farther (about 1–8 m).';
  const samples = [];
  const seen = new Set();
  const radarHistory = [];
  const diagnostics = { depth: 0, yolo: 0, radar: 0, bearing: 0 };
  let cachedFrameId = '';
  let cachedDepthImage = null;
  const stopAt = performance.now() + 60000;
  try {
    while (performance.now() < stopAt) {
      const [depthResponse, radarResponse] = await Promise.all([
        fetch('/body/camera/depth', { cache: 'no-store' }),
        fetch('/plugins/mmwave_radar/status', { cache: 'no-store' }),
      ]);
      if (!depthResponse.ok || !radarResponse.ok) throw new Error('MiDaS or radar endpoint is unavailable');
      const [depth, radarStatus] = await Promise.all([depthResponse.json(), radarResponse.json()]);
      const latestRadar = radarStatus.sample || {};
      if (radarStatus.available && Number(latestRadar.timestamp) > 0
          && String(latestRadar.source || '').toLowerCase().startsWith('hlk_ld2450')) {
        radarHistory.push(latestRadar);
        if (radarHistory.length > 120) radarHistory.shift();
      }
      if (!depth.frame_id || !depth.depth_gray_jpeg_base64) {
        status.textContent = `Waiting for MiDaS frame · ${samples.length} anchors collected.`;
        await new Promise(resolve => setTimeout(resolve, 350));
        continue;
      }
      diagnostics.depth += 1;
      let yoloResponse = await fetch(`/body/camera/yolo/status?nearest_to=${encodeURIComponent(depth.captured_at)}&max_delta_s=0.75`, { cache: 'no-store' });
      if (yoloResponse.status === 404) {
        status.textContent = `Waiting for aligned YOLOX · ${samples.length} anchors · frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, bearing ${diagnostics.bearing}.`;
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
      const synchronized = yolo.state === 'ready' && frameDelta <= 0.75
        && now - yoloAt <= 3.0 && now - depthAt <= 3.0
        && radarMatch && radarDelta <= 0.75;
      if (synchronized) {
        if (cachedFrameId !== depth.frame_id) {
          cachedDepthImage = await loadGrayDepth(depth.depth_gray_jpeg_base64);
          cachedFrameId = depth.frame_id;
        }
        const match = matchedRadarAnchor(yolo.detections, radarMatch.item);
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
            roi.push(cachedDepthImage.values[(y * cachedDepthImage.width + x) * 4] / 255);
          }
          roi.sort((a, b) => a - b);
          if (!roi.length) continue;
          const gray = roi[Math.floor(roi.length / 2)];
          samples.push({
            relative_depth: 1.1 + (1 - gray) * 5.8,
            distance_m: match.distance,
            bearing_error_deg: match.error,
            frame_delta_s: frameDelta,
            radar_delta_s: radarDelta,
          });
          seen.add(key);
        }
      }
      status.textContent = `Collecting synchronized anchors · ${samples.length} · frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, bearing ${diagnostics.bearing} · move nearer/farther.`;
      await new Promise(resolve => setTimeout(resolve, 350));
    }
    const response = await fetch('/body/camera/depth-calibration', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ samples }),
    });
    const result = await response.json();
    if (!response.ok || !result.available) throw new Error(result.error || 'Calibration was rejected');
    metricDepthCalibration = result;
    cloudFrameId = '';
    depthCalibrationMessage = '';
    lastSensorDepthAt = 0;
    await refreshSensorDepth();
  } catch (error) {
    depthCalibrationMessage = `Calibration not saved: ${error.message} · frames ${diagnostics.depth}, YOLO ${diagnostics.yolo}, radar ${diagnostics.radar}, bearing ${diagnostics.bearing}`;
  } finally {
    depthCalibrationBusy = false;
    button.disabled = false;
    button.textContent = metricDepthCalibration?.available ? 'Recalibrate with radar' : 'Calibrate with radar';
    updateMetricCalibrationStatus();
  }
}

async function refreshSensors() {
  if (sensorBusy || activeSource !== 'sensors') return;
  sensorBusy = true;
  try {
    const response = await fetch('/body/camera/frame', { cache: 'no-store' });
    const frame = await response.json();
    const currentCamera = frame.camera || {};
    const yolo = frame.yolo || {};
    latestCameraFrame = currentCamera;
    latestSensorYolo = yolo;
    const cameraState = byId('world-map-camera-state');
    if (cameraState) {
      const frameAge = Number(currentCamera.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(currentCamera.captured_at)) : Infinity;
      cameraState.textContent = currentCamera.image_base64
        ? `LIVE · ${currentCamera.width || '—'}×${currentCamera.height || '—'} · ${Number.isFinite(frameAge) ? frameAge.toFixed(1) + 's' : 'age —'}`
        : `${currentCamera.state || frame.status || 'NO FRAME'}`;
    }
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
    if (activeRender === '3d' && cloudDepthImage && yolo.frame_id !== cloudYoloFrameId) {
      drawDepthDetections(cloudDepthImage, detections);
      cloudYoloFrameId = yolo.frame_id || '';
    }
    byId('world-map-yolo-state').textContent = `${yolo.state || 'disabled'} · ${(yolo.detections || []).length} boxes${yolo.latency_ms != null ? ` · ${yolo.latency_ms} ms` : ''}`;
    byId('world-map-frame-state').textContent = currentCamera.frame_id ? `${currentCamera.frame_id}${currentCamera.captured_at ? ` · ${Math.max(0, Date.now() / 1000 - currentCamera.captured_at).toFixed(1)}s` : ''}` : 'No frame';
    byId('world-map-sensor-note').textContent = `Sensor-only view · frame ${currentCamera.frame_id || 'unavailable'} · no simulation object positions or metric scale.`;
  } catch (error) {
    byId('world-map-sensor-note').textContent = `Sensor data unavailable: ${error.message}`;
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
    byId('world-map-system-note').textContent = power.available
      ? `${power.source}. Temperature dials show the hottest reported sensor in each group. GPU/HTP utilization remains unavailable because the kernel exports no reliable busy counter.`
      : 'GPU/HTP utilization counters are unavailable. A battery-side shunt is needed to include external motor loads.';
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
    const moving = Number.isFinite(speed) && Math.abs(speed) >= .05;
    context.fillStyle = moving ? '#ed91c5' : '#efcb76';
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
    const targets = Array.isArray(sample.targets) ? sample.targets : [];
    const source = sample.source || status.protocol || status.port || 'LD2450';
    const age = Number(sample.timestamp) > 0 ? Math.max(0, Date.now() / 1000 - Number(sample.timestamp)) : NaN;
    byId('world-map-radar-state').textContent = status.available
      ? `${targets.length} targets · ${source}${Number.isFinite(age) ? ` · ${age.toFixed(1)}s` : ''}`
      : status.error || 'No data';
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
  } catch (error) {
    byId('world-map-radar-state').textContent = `Unavailable · ${error.message}`;
    byId('world-map-radar-targets').textContent = 'No live radar data.';
    drawLiveRadar();
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
    byId('world-map-gps-state').textContent = fix ? `FIX · ${status.transport || sample.transport || 'UART'}` : streaming ? 'UART live · no fix' : status.error || 'Offline';
    const latitude = Number(sample.latitude_deg ?? sample.latitude ?? sample.lat);
    const longitude = Number(sample.longitude_deg ?? sample.longitude ?? sample.lon ?? sample.lng);
    byId('world-map-gps-position').textContent = fix && Number.isFinite(latitude) && Number.isFinite(longitude) ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)}` : 'No valid fix';
    byId('world-map-gps-fix').textContent = `${fix ? 'Valid' : 'No fix'} · quality ${sample.fix_quality ?? '—'}`;
    byId('world-map-gps-satellites').textContent = `${sample.satellites ?? '—'} used · ${sample.satellites_in_view ?? '—'} in view`;
    byId('world-map-gps-quality').textContent = `HDOP ${displayNumber(sample.hdop)} · ${displayNumber(sample.altitude_m, 1, ' m')}`;
    const signals = Array.isArray(sample.satellite_signals) ? sample.satellite_signals : [];
    const plot = byId('world-map-gps-signals');
    plot.setAttribute('aria-label', `GPS satellite signal strength; ${signals.length} satellites reported`);
    plot.replaceChildren(...(signals.length ? signals.map(satellite => {
      const cn0 = Number(satellite.cn0_db_hz);
      const height = Number.isFinite(cn0) ? Math.max(3, Math.min(60, cn0)) : 3;
      const bar = document.createElement('div'); bar.className = 'sensor-gps-bar';
      const id = `${String(satellite.talker || 'GN').replace(/[^a-z0-9]/gi, '')}-${Number(satellite.svid) || '?'}`;
      const value = document.createElement('span'); value.textContent = Number.isFinite(cn0) ? cn0.toFixed(0) : '—';
      const fill = document.createElement('i'); fill.style.height = `${height}px`; fill.style.background = cn0 >= 35 ? '#3d9f70' : cn0 >= 25 ? '#c39738' : '#bd6559';
      const label = document.createElement('small'); label.textContent = id;
      bar.title = `${id} · C/N₀ ${displayNumber(cn0, 0, ' dB-Hz')} · az ${satellite.azimuth_deg ?? '—'}° · el ${satellite.elevation_deg ?? '—'}°`;
      bar.append(value, fill, label); return bar;
    }) : [Object.assign(document.createElement('span'), { className: 'sensor-readout-note', textContent: status.available ? 'No GSV satellite signal values in the current GPS sample.' : 'Waiting for GSV data from the GPS receiver.' })]));
  } catch (error) { byId('world-map-gps-state').textContent = `Unavailable · ${error.message}`; }
  finally { readoutBusy.gps = false; }
}

async function refreshLiveImu() {
  if (activeSource !== 'sensors' || readoutBusy.imu) return;
  readoutBusy.imu = true;
  try {
    const status = await sensorJson('/plugins/imu/status');
    const sample = status.sample || {};
    byId('world-map-imu-state').textContent = status.available
      ? `${sample.device || status.device || 'IMU'} · ${sample.attitude_valid ? 'attitude valid' : 'attitude invalid'}`
      : status.error || 'No data';
    byId('world-map-imu-roll').textContent = sample.attitude_valid ? displayNumber(sample.roll_deg, 1, '°') : 'Invalid';
    byId('world-map-imu-pitch').textContent = sample.attitude_valid ? displayNumber(sample.pitch_deg, 1, '°') : 'Invalid';
    byId('world-map-imu-yaw').textContent = displayNumber(sample.yaw_rate_dps ?? sample.angular_velocity_dps?.[2], 1, '°/s');
    const acceleration = sample.acceleration_g;
    byId('world-map-imu-accel').textContent = Array.isArray(acceleration) ? acceleration.map(value => displayNumber(value, 2)).join(' / ') : '—';
    const gyro = sample.angular_velocity_dps;
    byId('world-map-imu-gyro').textContent = Array.isArray(gyro) ? gyro.map(value => displayNumber(value, 1)).join(' / ') : '—';
  } catch (error) { byId('world-map-imu-state').textContent = `Unavailable · ${error.message}`; }
  finally { readoutBusy.imu = false; }
}

async function refreshLiveTof() {
  if (activeSource !== 'sensors' || readoutBusy.tof) return;
  readoutBusy.tof = true;
  try {
    const status = await sensorJson('/plugins/tof/status');
    const sample = status.sample || {};
    const available = status.available && sample.available !== false && !sample.simulated;
    byId('world-map-tof-state').textContent = available ? `${sample.device || status.sensor || 'VL53L1X'} · live` : status.error || 'No fresh measurement';
    byId('world-map-tof-distance').textContent = available ? displayNumber(sample.distance_m, 2, ' m') : 'No measurement';
    byId('world-map-tof-meta').textContent = available ? `${sample.frame || status.frame || 'body_front'} · ${displayNumber(sample.distance_mm, 0, ' mm')}` : status.transport || 'Forward single-beam range';
  } catch (error) { byId('world-map-tof-state').textContent = `Unavailable · ${error.message}`; }
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
      state.textContent = `${segmentation.state || 'disabled'}${segmentation.device ? ` · ${segmentation.device}` : ''}${segmentation.latency_ms != null ? ` · ${segmentation.latency_ms} ms` : ''}${age}`;
    }
  } catch (error) {
    const state = byId('world-map-segmentation-state');
    if (state) state.textContent = `SegFormer unavailable · ${error.message}`;
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
    const segmentation = latestSegmentation;
    latestSensorDepth = depth;
    latestSegmentation = segmentation;
    lastSensorDepthAt = performance.now();
    setImage(byId('world-map-depth-image'), byId('world-map-depth-empty'), depth.depth_jpeg_base64);
    const depthAge = Number(depth.captured_at) > 0
      ? ` · ${Math.max(0, Date.now() / 1000 - Number(depth.captured_at)).toFixed(1)}s old` : '';
    byId('world-map-midas-state').textContent = `${depth.state || 'disabled'}${depth.device ? ` · ${depth.device}` : ''}${depth.latency_ms != null ? ` · ${depth.latency_ms} ms` : ''}${depthAge}${depth.error ? ` · ${depth.error}` : ''}`;
    updateMetricCalibrationStatus();
    const alignedSegmentationFrameId = segmentationMatchesDepth(segmentation, depth)
      ? String(segmentation.frame_id || segmentation.captured_at || '') : '';
    if (depth.depth_gray_jpeg_base64 && activeRender === '3d'
        && (depth.frame_id !== cloudFrameId || alignedSegmentationFrameId !== cloudSegmentationFrameId)) {
      const depthFrameId = depth.frame_id;
      void rebuildDepthCloud(depth, segmentation)
        .then((updated) => {
          if (updated) {
            cloudFrameId = depthFrameId;
            cloudSegmentationFrameId = alignedSegmentationFrameId;
          }
        })
        .catch((error) => console.warn('Could not rebuild MiDaS depth cloud:', error));
    }
  } catch (error) {
    byId('world-map-midas-state').textContent = `unavailable · ${error.message}`;
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
    if (odometry.available) {
      const [forward = 0, lateral = 0] = odometry.position_m || [];
      status.textContent = `${forward.toFixed(2)}m fwd · ${lateral.toFixed(2)}m left · ${Math.round(odometry.confidence * 100)}% · experimental`;
      const frameId = String(odometry.frame_id || '');
      if (frameId && frameId !== visualOdometryFrameId) {
        visualOdometryFrameId = frameId;
        visualOdometryTrail.push({ forward, lateral });
        if (visualOdometryTrail.length > 600) visualOdometryTrail.shift();
      }
      renderVisualOdometryMap(odometry);
    } else {
      status.textContent = `${odometry.state || 'waiting'} · ${odometry.reason || 'need synchronized camera, MiDaS and radar calibration'}`;
      if (mapStatus) mapStatus.title = odometry.reason || '';
    }
  } catch (error) {
    const status = byId('world-map-odometry-state');
    if (status) status.textContent = `unavailable · ${error.message}`;
  } finally {
    visualOdometryBusy = false;
  }
}

function renderVisualOdometryMap(odometry) {
  const trail = byId('world-map-odometry-trail');
  const body = byId('world-map-odometry-body');
  const position = byId('world-map-odometry-position');
  if (!trail || !body || !position || !visualOdometryTrail.length) return;
  const width = 640, height = 260;
  const plot = { left: 56, right: 584, top: 32, bottom: 220 };
  const forwards = visualOdometryTrail.map(point => point.forward);
  const laterals = visualOdometryTrail.map(point => point.lateral);
  const minForward = Math.min(0, ...forwards), maxForward = Math.max(0, ...forwards);
  const minLateral = Math.min(0, ...laterals), maxLateral = Math.max(0, ...laterals);
  const spanForward = Math.max(2.0, maxForward - minForward + 0.8);
  const spanLateral = Math.max(2.8, maxLateral - minLateral + 0.8);
  const scale = Math.min((plot.bottom - plot.top) / spanForward, (plot.right - plot.left) / spanLateral);
  const centerLateral = (minLateral + maxLateral) / 2;
  const centerForward = (minForward + maxForward) / 2;
  const mapPoint = point => ({
    x: width / 2 - (point.lateral - centerLateral) * scale,
    y: (plot.top + plot.bottom) / 2 - (point.forward - centerForward) * scale,
  });
  trail.setAttribute('points', visualOdometryTrail.map(point => {
    const mapped = mapPoint(point);
    return `${mapped.x.toFixed(1)},${mapped.y.toFixed(1)}`;
  }).join(' '));
  const start = mapPoint(visualOdometryTrail[0]);
  const startMarker = byId('world-map-odometry-start');
  if (startMarker) {
    startMarker.setAttribute('cx', start.x.toFixed(1));
    startMarker.setAttribute('cy', start.y.toFixed(1));
  }
  const current = mapPoint(visualOdometryTrail.at(-1));
  body.setAttribute('transform', `translate(${current.x.toFixed(1)} ${current.y.toFixed(1)}) rotate(${(Number(odometry.yaw_rad) || 0) * 180 / Math.PI})`);
  position.setAttribute('x', Math.min(width - 130, current.x + 12).toFixed(1));
  position.setAttribute('y', Math.max(28, current.y - 12).toFixed(1));
  const [forward = 0, lateral = 0] = odometry.position_m || [];
  position.textContent = `${forward.toFixed(2)} fwd · ${lateral.toFixed(2)} left m`;
  const mapStatus = byId('world-map-odometry-map-status');
  if (mapStatus) mapStatus.textContent = `TRACKING · ${Number(odometry.speed_mps || 0).toFixed(2)} m/s · view ${spanLateral.toFixed(1)} × ${spanForward.toFixed(1)} m`;
}

function resizeCloud() {
  if (!cloud) return;
  const target = new THREE.Vector3(0, 0, -3);
  cloud.camera.userData.target = target;
  if (!cloudCameraInitialized) {
    cloud.camera.position.set(0, 1.6, 7);
    cloudCameraInitialized = true;
  }
  cloud.camera.lookAt(target);
  cloud.render();
}

function disposeCloudContent() {
  for (const item of [cloudPoints, boxGroup]) {
    if (!item) continue;
    cloud.scene.remove(item);
    item.traverse?.((node) => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach((entry) => entry.dispose());
      else {
        node.material?.map?.dispose();
        node.material?.dispose();
      }
    });
  }
  cloudPoints = null;
  boxGroup = null;
}

async function loadGrayDepth(base64) {
  const image = new Image();
  image.src = `data:image/jpeg;base64,${base64}`;
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
  const image = await loadGrayDepth(depth.depth_gray_jpeg_base64);
  const colorImage = depth.depth_jpeg_base64 ? await loadGrayDepth(depth.depth_jpeg_base64) : image;
  const classMask = segmentationMatchesDepth(segmentation, depth)
    ? await loadClassMask(segmentation.mask_png_base64) : null;
  if (token !== cloudBuildToken || activeSource !== 'sensors' || activeRender !== '3d') return false;
  cloudDepthImage = image;
  const stride = Math.max(2, Math.ceil(Math.max(image.width, image.height) / 140));
  const positions = [];
  const colorsArray = [];
  for (let y = 0; y < image.height; y += stride) {
    for (let x = 0; x < image.width; x += stride) {
      const index = (y * image.width + x) * 4;
      const relative = image.values[index] / 255;
      const distance = relativeDepthToMeters(1.1 + (1 - relative) * 5.8);
      const px = ((x / Math.max(1, image.width - 1)) - 0.5) * distance * 1.28;
      const py = (0.5 - y / Math.max(1, image.height - 1)) * distance * 0.96;
      positions.push(px, py, -distance);
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
        const classId = classMask.values[(maskY * classMask.width + maskX) * 4 + 2];
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
  disposeCloudContent();
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colorsArray, 3));
  cloudPoints = new THREE.Points(geometry, new THREE.PointsMaterial({ size: 0.035, vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 0.92 }));
  cloud.scene.add(cloudPoints);
  drawDepthDetections(image, visibleYoloDetections(latestSensorYolo));
  resizeCloud();
  return true;
}

function drawDepthDetections(image, detections) {
  if (!cloud || !image || activeRender !== '3d') return;
  if (boxGroup) {
    cloud.scene.remove(boxGroup);
    boxGroup.traverse((node) => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach((entry) => entry.dispose());
      else node.material?.dispose();
      if (node.material?.map) node.material.map.dispose();
    });
  }
  boxGroup = new THREE.Group();
  const colorsByKind = ['#55e7cc', '#f2bc65', '#e280ba', '#77d69c'];
  for (const [index, item] of (detections || []).entries()) {
    const bbox = item.bbox;
    if (!Array.isArray(bbox) || bbox.length < 4) continue;
    const [x1, y1, x2, y2] = bbox.map(Number);
    const sampleX = Math.max(0, Math.min(image.width - 1, Math.round((x1 + x2) * image.width / 2)));
    const sampleY = Math.max(0, Math.min(image.height - 1, Math.round((y1 + y2) * image.height / 2)));
    const gray = image.values[(sampleY * image.width + sampleX) * 4] / 255;
    const relativeDistance = 1.1 + (1 - gray) * 5.8;
    const distance = relativeDepthToMeters(relativeDistance);
    const width = Math.max(0.04, (x2 - x1) * distance * 1.28);
    const height = Math.max(0.04, (y2 - y1) * distance * 0.96);
    const centerX = (((x1 + x2) / 2) - 0.5) * distance * 1.28;
    const centerY = (0.5 - (y1 + y2) / 2) * distance * 0.96;
    const color = colorsByKind[index % colorsByKind.length];
    const materialBox = new THREE.LineBasicMaterial({ color, depthTest: false, transparent: true, opacity: 0.95 });
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(width, height, Math.max(0.035, distance * 0.035))), materialBox);
    edges.position.set(centerX, centerY, -distance);
    boxGroup.add(edges);
    const metricLabel = metricDepthCalibration?.available ? ` · ~${distance.toFixed(1)} m` : '';
    const label = makeLabel(`${item.label || item.class_name || item.class || 'object'} ${Math.round(Number(item.confidence ?? item.score ?? 0) * 100)}%${metricLabel}`, color);
    label.scale.set(Math.max(0.95, Math.min(2.0, width)), 0.25, 1);
    label.position.set(centerX, centerY + height / 2 + 0.17, -distance);
    boxGroup.add(label);
  }
  cloud.scene.add(boxGroup);
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
}, 250);
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
