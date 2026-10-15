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
    controls.innerHTML = `<div class="world-map-segment" id="world-map-source" role="group" aria-label="Map data source"><button type="button" data-source="simulation" aria-pressed="true">Simulation</button><button type="button" data-source="sensors" aria-pressed="false">Sensors</button></div><div class="world-map-segment" role="group" aria-label="Map rendering"><button type="button" data-render="2d" aria-pressed="true">2D</button><button type="button" data-render="3d" aria-pressed="false">3D</button></div><small id="world-map-state" role="status">Simulation · 2D</small>`;
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
    sensorPanel.innerHTML = `<div class="world-map-sensor-metrics"><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Visual odometry <b id="world-map-odometry-state">Waiting</b></span><span>Frame <b id="world-map-frame-state">—</b></span><span>SegFormer <b id="world-map-segmentation-state">disabled</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA · YOLOX + SEGFORMER</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><canvas id="world-map-segmentation-overlay" aria-label="SegFormer semantic classes overlaid on the camera frame" hidden></canvas><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div><label class="world-map-segmentation-toggle"><input id="world-map-segmentation-toggle" type="checkbox" checked> Segmentation overlay</label></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS · RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate">Calibrate with radar</button><small id="world-map-midas-calibration-status" role="status">Relative depth only · not calibrated in metres</small></div></div></div><section class="world-map-odometry-view" aria-label="Experimental visual odometry trajectory"><div class="world-map-sensor-heading"><span>VISUAL ODOMETRY · LOCAL TRAJECTORY</span><small id="world-map-odometry-map-status">Waiting for tracking</small></div><svg id="world-map-odometry-map" viewBox="0 0 640 260" role="img" aria-label="Top-down estimated Body trajectory in the local visual odometry frame"><rect class="odom-map-bg" x="0" y="0" width="640" height="260"/><g class="odom-grid"><path d="M40 45H600M40 85H600M40 125H600M40 165H600M40 205H600M80 25V225M160 25V225M240 25V225M320 25V225M400 25V225M480 25V225M560 25V225"/><path class="odom-axis" d="M40 205H600M320 25V225"/></g><text class="odom-axis-label" x="320" y="18" text-anchor="middle">FORWARD ↑</text><text class="odom-axis-label" x="320" y="249" text-anchor="middle">← LEFT · RIGHT →</text><g id="world-map-odometry-grid-labels"></g><polyline id="world-map-odometry-trail" points=""/><circle id="world-map-odometry-start" cx="320" cy="205" r="4"/><g id="world-map-odometry-body" transform="translate(320 205)"><path d="M0 -11 L7 8 L0 5 L-7 8 Z"/></g><text id="world-map-odometry-position" class="odom-position-label" x="332" y="200">0.00, 0.00 m</text><text id="world-map-odometry-empty" class="odom-empty-label" x="320" y="130" text-anchor="middle">Move the Body to trace its estimated path</text></svg><p class="world-map-odometry-footnote">Session-local estimate · visual odometry only · drift accumulates · not a persistent map</p></section><div id="world-map-sensor-3d" class="world-map-canvas world-map-sensor-cloud" hidden></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view · no simulation object positions are used.</p>`;
    const semanticPanel = document.createElement('div');
    semanticPanel.className = 'world-map-segmentation-classes';
    semanticPanel.id = 'world-map-segmentation-classes';
    semanticPanel.textContent = 'Waiting for SegFormer classes';
    sensorPanel.querySelector('.world-map-sensor-2d')?.after(semanticPanel);
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
      .world-map-sensor-metrics{display:flex;gap:18px;flex-wrap:wrap;padding:9px 0;color:#8eaa98;font:10px ui-monospace,monospace}
      .world-map-sensor-metrics b{color:#dceee3;font-weight:600}
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
      #world-map-segmentation-overlay,#world-map-yolo-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      #world-map-segmentation-overlay{opacity:.56;image-rendering:auto}
      .world-map-segmentation-toggle{display:flex;align-items:center;gap:7px;padding:7px 10px;color:#dceee3;font:11px ui-monospace,monospace}
      .world-map-segmentation-toggle input{accent-color:#34c9a2}
      .world-map-depth{display:flex;flex-direction:column}
      .world-map-segmentation-classes{display:flex;gap:7px 12px;flex-wrap:wrap;margin:0;padding:8px 10px;color:#dceee3;font:10px ui-monospace,monospace;line-height:1.6}
      .world-map-segmentation-classes span{display:inline-flex;align-items:center;gap:5px}
      .world-map-segmentation-classes i{width:8px;height:8px;flex:0 0 8px;border-radius:50%}
      .world-map-depth img{display:block;width:100%;height:100%;min-height:220px;max-height:500px;object-fit:contain;background:#020805}
      .world-map-depth>small{padding:7px 10px;color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-depth-calibration{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:8px 10px;border-top:1px solid #263e32}
      .world-map-depth-calibration button{border:1px solid #416b54;border-radius:3px;background:#10251a;color:#d9f5e5;padding:7px 10px;cursor:pointer}
      .world-map-depth-calibration button:disabled{opacity:.6;cursor:wait}
      .world-map-depth-calibration small{color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-empty{position:absolute;inset:0;display:grid;place-items:center;padding:20px;color:#91a79a;font:11px ui-monospace,monospace;text-align:center;pointer-events:none}
      .world-map-empty[hidden]{display:none}
      #world-map-segmentation-overlay[hidden]{display:none}
      .world-map-sensor-note{margin:9px 0 0;color:#a9c0b2;font-size:11px}
      .world-map-sensor-cloud{height:clamp(360px,54vh,620px)}
      @media(max-width:700px){.world-map-sensor-2d{grid-template-columns:minmax(0,1fr)}.world-map-depth img{max-height:320px}.world-map-controls{gap:7px}}
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
let activeSource = 'simulation';
let activeRender = '2d';
let latestWorld = null;
let sensorBusy = false;

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
  panel?.querySelector('.map-intro')?.replaceChildren(document.createTextNode(source === 'sensors'
    ? 'Live sensor view. Only captured camera frames, YOLOX detections and MiDaS relative depth are shown; simulation ground truth is excluded.'
    : 'Live Body position, orientation, objects, obstacles and current objective from the active simulation or observed world model.'));
  document.querySelectorAll('[data-source]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.source === source)));
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
  if (state) state.textContent = `${activeSource === 'simulation' ? 'Simulation' : 'Sensors'} · ${activeRender.toUpperCase()}`;
  const mapWrap = panel?.querySelector('.map-wrap');
  const simCanvas = byId('world-map-sim-3d');
  if (mapWrap && simCanvas && activeSource === 'simulation') {
    mapWrap.hidden = activeRender !== '2d';
    simCanvas.hidden = activeRender !== '3d';
  }
}

document.querySelectorAll('[data-source]').forEach((button) => button.addEventListener('click', () => setSource(button.dataset.source)));
document.querySelectorAll('[data-render]').forEach((button) => button.addEventListener('click', () => setRender(button.dataset.render)));
byId('world-map-midas-calibrate')?.addEventListener('click', () => void calibrateMetricDepth());
byId('world-map-segmentation-toggle')?.addEventListener('change', () => {
  void renderSemanticMask(latestSegmentation, latestCameraFrame);
});
void loadMetricCalibration();

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

async function renderSemanticMask(segmentation, cameraFrame) {
  const canvas = byId('world-map-segmentation-overlay');
  const classes = byId('world-map-segmentation-classes');
  const toggle = byId('world-map-segmentation-toggle');
  if (!canvas || !classes) return;
  const mask = segmentation?.mask_png_base64;
  const frameId = String(segmentation?.frame_id || '');
  const maskKey = frameId || String(segmentation?.captured_at || '');
  if (!toggle?.checked || !segmentationMatchesFrame(segmentation, cameraFrame)) {
    canvas.hidden = true;
    if (!toggle?.checked) return;
    classes.textContent = segmentation?.available && mask
      ? 'Waiting for a fresh SegFormer mask'
      : `${segmentation?.state === 'disabled' ? 'Enable SegFormer in Camera settings' : `SegFormer ${segmentation?.state || 'waiting'}`}${segmentation?.error ? ` · ${segmentation.error}` : ''}`;
    renderedSegmentationFrameId = '';
    return;
  }
  if (maskKey === renderedSegmentationFrameId) {
    canvas.hidden = false;
    return;
  }
  const image = new Image();
  image.src = `data:image/png;base64,${mask}`;
  await image.decode();
  if (maskKey !== String(latestSegmentation?.frame_id || latestSegmentation?.captured_at || '')
      || !segmentationMatchesFrame(latestSegmentation, latestCameraFrame)) return;
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
    pixels.data[index + 3] = 255;
  }
  context.putImageData(pixels, 0, 0);
  canvas.hidden = false;
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
    const [response, segmentationResponse] = await Promise.all([
      fetch('/body/camera/frame', { cache: 'no-store' }),
      fetch('/body/camera/segmentation', { cache: 'no-store' }),
    ]);
    const [frame, segmentation] = await Promise.all([response.json(), segmentationResponse.json()]);
    const currentCamera = frame.camera || {};
    const yolo = frame.yolo || {};
    latestCameraFrame = currentCamera;
    latestSegmentation = segmentation;
    latestSensorYolo = yolo;
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
    void renderSemanticMask(segmentation, currentCamera).catch((error) => {
      const classes = byId('world-map-segmentation-classes');
      if (classes) classes.textContent = `SegFormer overlay unavailable · ${error.message}`;
    });
    const detections = visibleYoloDetections(yolo);
    drawBoxes(detections, currentCamera.width || 640, currentCamera.height || 480);
    if (activeRender === '3d' && cloudDepthImage && yolo.frame_id !== cloudYoloFrameId) {
      drawDepthDetections(cloudDepthImage, detections);
      cloudYoloFrameId = yolo.frame_id || '';
    }
    byId('world-map-yolo-state').textContent = `${yolo.state || 'disabled'} · ${(yolo.detections || []).length} boxes${yolo.latency_ms != null ? ` · ${yolo.latency_ms} ms` : ''}`;
    const segmentationState = byId('world-map-segmentation-state');
    if (segmentationState) {
      const maskAge = Number(currentCamera.captured_at) - Number(segmentation.captured_at);
      const overlayStatus = segmentationMatchesFrame(segmentation, currentCamera)
        ? ` · overlay${Number.isFinite(maskAge) && maskAge > 0.25 ? ` · ${maskAge.toFixed(1)}s lag` : ''}` : '';
      segmentationState.textContent = `${segmentation.state || 'disabled'}${segmentation.device ? ` · ${segmentation.device}` : ''}${segmentation.latency_ms != null ? ` · ${segmentation.latency_ms} ms` : ''}${overlayStatus}`;
    }
    byId('world-map-frame-state').textContent = currentCamera.frame_id ? `${currentCamera.frame_id}${currentCamera.captured_at ? ` · ${Math.max(0, Date.now() / 1000 - currentCamera.captured_at).toFixed(1)}s` : ''}` : 'No frame';
    byId('world-map-sensor-note').textContent = `Sensor-only view · frame ${currentCamera.frame_id || 'unavailable'} · no simulation object positions or metric scale.`;
  } catch (error) {
    byId('world-map-sensor-note').textContent = `Sensor data unavailable: ${error.message}`;
  } finally {
    sensorBusy = false;
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
    const mapEmpty = byId('world-map-odometry-empty');
    if (mapStatus) mapStatus.textContent = odometry.state === 'tracking' ? 'TRACKING' : String(odometry.state || 'waiting').toUpperCase();
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
      if (mapEmpty) mapEmpty.hidden = visualOdometryTrail.length > 0;
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

function semanticColor(classId) {
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
      if (classMask) {
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
}, 150);
setInterval(() => {
  if (activeSource === 'sensors') void refreshVisualOdometry();
}, 500);
if (latestWorld) buildSimulation(latestWorld);
