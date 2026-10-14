import * as THREE from '../frontend/node_modules/three/build/three.module.js';

const byId = (id) => document.getElementById(id);
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
    mapWrap.append(simCanvas);
    const sensorPanel = document.createElement('section');
    sensorPanel.id = 'world-map-sensor-view';
    sensorPanel.className = 'world-map-sensor-view';
    sensorPanel.hidden = true;
    sensorPanel.innerHTML = `<div class="world-map-sensor-metrics"><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Frame <b id="world-map-frame-state">—</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA · YOLOX</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS · RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><small>Relative depth only · not calibrated in metres</small></div></div><div id="world-map-sensor-3d" class="world-map-canvas world-map-sensor-cloud" hidden></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view · no simulation object positions are used.</p>`;
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
      .map-layout[hidden],.map-wrap>svg[hidden]{display:none!important}
      .world-map-sensor-metrics{display:flex;gap:18px;flex-wrap:wrap;padding:9px 0;color:#8eaa98;font:10px ui-monospace,monospace}
      .world-map-sensor-metrics b{color:#dceee3;font-weight:600}
      .world-map-sensor-2d{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(220px,.8fr);gap:12px;align-items:stretch}
      .world-map-camera,.world-map-depth{min-width:0;position:relative;background:#07120f;border:1px solid #263e32;overflow:hidden}
      .world-map-sensor-heading{padding:9px 11px;border-bottom:1px solid #263e32;color:#91c9aa;font:10px ui-monospace,monospace}
      .world-map-image-wrap{position:relative;display:grid;place-items:center;min-height:220px;max-height:500px;background:#020805;overflow:hidden}
      .world-map-image-wrap img{display:block;width:100%;max-height:500px;object-fit:contain}
      #world-map-yolo-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      .world-map-depth{display:flex;flex-direction:column}
      .world-map-depth img{display:block;width:100%;height:100%;min-height:220px;max-height:500px;object-fit:contain;background:#020805}
      .world-map-depth>small{padding:7px 10px;color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-empty{position:absolute;inset:0;display:grid;place-items:center;padding:20px;color:#91a79a;font:11px ui-monospace,monospace;text-align:center;pointer-events:none}
      .world-map-empty[hidden]{display:none}
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
  return { renderer, scene, camera, render, observer };
}

const sim = makeRenderer(byId('world-map-sim-3d'));
let simRoot;
let simSignature = '';
let cloud = makeRenderer(byId('world-map-sensor-3d'), '#06100d');
let cloudPoints = null;
let boxGroup = null;
let cloudFrameId = '';
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
  const map = byId('map');
  const simCanvas = byId('world-map-sim-3d');
  const sensor2d = byId('world-map-sensor-2d');
  const sensor3d = byId('world-map-sensor-3d');
  if (activeSource === 'simulation') {
    if (map) map.hidden = render !== '2d';
    if (simCanvas) simCanvas.hidden = render !== '3d';
    if (mapWrap) mapWrap.classList.toggle('is-3d', render === '3d');
    if (latestWorld && render === '3d') requestAnimationFrame(() => { buildSimulation(latestWorld); sim?.render(); });
  } else {
    if (sensor2d) sensor2d.hidden = render !== '2d';
    if (sensor3d) sensor3d.hidden = render !== '3d';
    if (render === '3d') requestAnimationFrame(() => { resizeCloud(); cloud?.render(); });
  }
  document.querySelectorAll('[data-render]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.render === render)));
  updateMode();
}

function updateMode() {
  const state = byId('world-map-state');
  if (state) state.textContent = `${activeSource === 'simulation' ? 'Simulation' : 'Sensors'} · ${activeRender.toUpperCase()}`;
  const map = byId('map');
  const simCanvas = byId('world-map-sim-3d');
  if (map && simCanvas && activeSource === 'simulation') {
    map.hidden = activeRender !== '2d';
    simCanvas.hidden = activeRender !== '3d';
  }
}

document.querySelectorAll('[data-source]').forEach((button) => button.addEventListener('click', () => setSource(button.dataset.source)));
document.querySelectorAll('[data-render]').forEach((button) => button.addEventListener('click', () => setRender(button.dataset.render)));

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

async function refreshSensors() {
  if (sensorBusy || activeSource !== 'sensors') return;
  sensorBusy = true;
  try {
    const [frame, depth] = await Promise.all([
      fetch('/body/camera/frame', { cache: 'no-store' }).then((response) => response.json()),
      fetch('/body/camera/depth', { cache: 'no-store' }).then((response) => response.json()),
    ]);
    const currentCamera = frame.camera || {};
    const yolo = frame.yolo || {};
    let displayCamera = currentCamera;
    if (yolo.frame_id) {
      try {
        const analyzed = await fetch(`/body/camera/yolo-frame?frame_id=${encodeURIComponent(yolo.frame_id)}`, { cache: 'no-store' });
        if (analyzed.ok) displayCamera = (await analyzed.json()).camera || currentCamera;
      } catch (_) {}
    }
    const cameraImage = byId('world-map-camera-image');
    const cameraEmpty = byId('world-map-camera-empty');
    setImage(cameraImage, cameraEmpty, displayCamera.image_base64, displayCamera.mime_type || 'image/jpeg');
    drawBoxes(yolo.frame_id === displayCamera.frame_id ? yolo.detections : [], displayCamera.width || 640, displayCamera.height || 480);
    byId('world-map-yolo-state').textContent = `${yolo.state || 'disabled'} · ${(yolo.detections || []).length} boxes${yolo.latency_ms != null ? ` · ${yolo.latency_ms} ms` : ''}`;
    byId('world-map-frame-state').textContent = displayCamera.frame_id ? `${displayCamera.frame_id}${displayCamera.captured_at ? ` · ${Math.max(0, Date.now() / 1000 - displayCamera.captured_at).toFixed(1)}s` : ''}` : 'No frame';
    const depthImage = byId('world-map-depth-image');
    const depthEmpty = byId('world-map-depth-empty');
    setImage(depthImage, depthEmpty, depth.depth_jpeg_base64);
    byId('world-map-midas-state').textContent = `${depth.state || 'disabled'}${depth.latency_ms != null ? ` · ${depth.latency_ms} ms` : ''}${depth.error ? ` · ${depth.error}` : ''}`;
    byId('world-map-sensor-note').textContent = `Sensor-only view · frame ${displayCamera.frame_id || 'unavailable'} · depth ${depth.depth_type || 'relative'} · no simulation object positions or metric scale.`;
    if (depth.depth_gray_jpeg_base64 && depth.frame_id !== cloudFrameId) {
      await rebuildDepthCloud(depth, yolo.frame_id === depth.frame_id ? yolo.detections || [] : []);
      cloudFrameId = depth.frame_id;
    }
  } catch (error) {
    byId('world-map-sensor-note').textContent = `Sensor data unavailable: ${error.message}`;
  } finally {
    sensorBusy = false;
  }
}

function resizeCloud() {
  if (!cloud) return;
  const target = new THREE.Vector3(0, 0, -3);
  cloud.camera.userData.target = target;
  if (!cloudPoints) cloud.camera.position.set(0, 1.6, 7);
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
      else node.material?.dispose();
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

async function rebuildDepthCloud(depth, detections) {
  if (!cloud || !depth.depth_gray_jpeg_base64) return;
  const image = await loadGrayDepth(depth.depth_gray_jpeg_base64);
  const stride = Math.max(2, Math.ceil(Math.max(image.width, image.height) / 140));
  const positions = [];
  const colorsArray = [];
  const colorsByKind = ['#55e7cc', '#f2bc65', '#e280ba', '#77d69c'];
  for (let y = 0; y < image.height; y += stride) {
    for (let x = 0; x < image.width; x += stride) {
      const index = (y * image.width + x) * 4;
      const relative = image.values[index] / 255;
      const distance = 1.1 + (1 - relative) * 5.8;
      const px = ((x / Math.max(1, image.width - 1)) - 0.5) * distance * 1.28;
      const py = (0.5 - y / Math.max(1, image.height - 1)) * distance * 0.96;
      positions.push(px, py, -distance);
      const color = new THREE.Color().setHSL(0.47 - relative * 0.3, 0.64, 0.49 + relative * 0.13);
      colorsArray.push(color.r, color.g, color.b);
    }
  }
  disposeCloudContent();
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colorsArray, 3));
  cloudPoints = new THREE.Points(geometry, new THREE.PointsMaterial({ size: 0.035, vertexColors: true, sizeAttenuation: true, transparent: true, opacity: 0.92 }));
  cloud.scene.add(cloudPoints);
  boxGroup = new THREE.Group();
  for (const [index, item] of (detections || []).entries()) {
    const bbox = item.bbox;
    if (!Array.isArray(bbox) || bbox.length < 4) continue;
    const [x1, y1, x2, y2] = bbox.map(Number);
    const sampleX = Math.max(0, Math.min(image.width - 1, Math.round((x1 + x2) * image.width / 2)));
    const sampleY = Math.max(0, Math.min(image.height - 1, Math.round((y1 + y2) * image.height / 2)));
    const gray = image.values[(sampleY * image.width + sampleX) * 4] / 255;
    const distance = 1.1 + (1 - gray) * 5.8;
    const width = Math.max(0.04, (x2 - x1) * distance * 1.28);
    const height = Math.max(0.04, (y2 - y1) * distance * 0.96);
    const centerX = (((x1 + x2) / 2) - 0.5) * distance * 1.28;
    const centerY = (0.5 - (y1 + y2) / 2) * distance * 0.96;
    const materialBox = new THREE.LineBasicMaterial({ color: colorsByKind[index % colorsByKind.length] });
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(width, height, Math.max(0.035, distance * 0.035))), materialBox);
    edges.position.set(centerX, centerY, -distance);
    boxGroup.add(edges);
  }
  cloud.scene.add(boxGroup);
  resizeCloud();
}

window.updateBodyWorldMap3D = (world) => {
  latestWorld = world;
  if (activeSource === 'simulation' && activeRender === '3d') buildSimulation(world);
};

setInterval(() => { if (activeSource === 'sensors') void refreshSensors(); }, 1200);
if (latestWorld) buildSimulation(latestWorld);
