import * as THREE from '../frontend/node_modules/three/build/three.module.js';
import { OrbitControls } from '../frontend/node_modules/three/examples/jsm/controls/OrbitControls.js';

const canvas = document.querySelector('#scene');
const statusNode = document.querySelector('#status');
const selectionNode = document.querySelector('#selection');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.xr.enabled = true;

const scene = new THREE.Scene();
scene.background = null;
const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.05, 100);
camera.position.set(0, 7.2, 10.5);
camera.lookAt(0, 0, -4);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(0, 0, -4);
orbit.enableDamping = true;
orbit.maxPolarAngle = Math.PI * 0.48;
orbit.minDistance = 3;
orbit.maxDistance = 24;

scene.add(new THREE.HemisphereLight('#d6f5e0', '#17231b', 2.0));
const keyLight = new THREE.DirectionalLight('#fff0d6', 2.2);
keyLight.position.set(-5, 10, 3);
scene.add(keyLight);

const world = new THREE.Group();
world.position.set(0, 0, -4);
scene.add(world);
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(16, 16),
  new THREE.MeshStandardMaterial({ color: '#14241b', roughness: 0.94, metalness: 0.02, side: THREE.DoubleSide, transparent: true, opacity: 0.2 }),
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.035;
world.add(floor);
world.add(new THREE.GridHelper(16, 32, '#4e8d69', '#294c3a'));

const roomLine = new THREE.LineSegments(
  new THREE.EdgesGeometry(new THREE.BoxGeometry(16, 0.08, 16)),
  new THREE.LineBasicMaterial({ color: '#70b28a', transparent: true, opacity: 0.55 }),
);
roomLine.position.set(0, 0.01, 0);
world.add(roomLine);
const objectsGroup = new THREE.Group();
world.add(objectsGroup);
const lidarGroup = new THREE.Group();
const radarGroup = new THREE.Group();
world.add(lidarGroup, radarGroup);
const selectionMarker = new THREE.Mesh(
  new THREE.RingGeometry(0.42, 0.5, 32),
  new THREE.MeshBasicMaterial({ color: '#b9f5ce', side: THREE.DoubleSide, transparent: true, opacity: 0.95 }),
);
selectionMarker.rotation.x = -Math.PI / 2;
selectionMarker.position.y = 0.025;
selectionMarker.visible = false;
world.add(selectionMarker);
let selectedLabel = null;
const raycaster = new THREE.Raycaster();
const selectable = [];
const controllerRays = [];
const colorByKind = { table: '#d3bd67', chair: '#83b3d5', obstacle: '#a77ba5', mobile_obstacle: '#db83bf', target: '#efa678' };
let lastFrame = null;
let basePosition = null;
let firstData = true;
let latestObjects = [];
let latestWorldStatus = null;
let showLidar = true;
let showRadar = true;
let followBody = false;
const dashboardGroup = new THREE.Group();
const dashboardButtons = [];
const dashboardTextures = new Map();
let cameraPollTimer = null;
let cameraPollInFlight = false;
let cameraFrameKey = null;
dashboardGroup.visible = false;
camera.add(dashboardGroup);

function dashboardTexture(id, title, detail = '', tone = 'normal') {
  let entry = dashboardTextures.get(id);
  if (!entry) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 256;
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthTest: false, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(0.43, 0.25), material);
    mesh.renderOrder = 20;
    mesh.userData.action = id;
    dashboardButtons.push(mesh);
    dashboardGroup.add(mesh);
    entry = { canvas, texture, mesh };
    dashboardTextures.set(id, entry);
  }
  const ctx = entry.canvas.getContext('2d');
  const color = tone === 'active' ? '#103d2a' : tone === 'disabled' ? '#202827' : '#0a2018';
  const stroke = tone === 'active' ? '#83e5ac' : tone === 'disabled' ? '#58645e' : '#6cbf8e';
  ctx.clearRect(0, 0, 512, 256);
  ctx.fillStyle = '#06100ee8';
  ctx.fillRect(4, 4, 504, 248);
  ctx.fillStyle = color;
  ctx.fillRect(12, 12, 488, 232);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 5;
  ctx.strokeRect(12, 12, 488, 232);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = tone === 'disabled' ? '#91a096' : '#e5f5eb';
  ctx.font = '600 40px system-ui';
  ctx.fillText(String(title).slice(0, 22), 256, 92);
  ctx.fillStyle = tone === 'disabled' ? '#87958c' : '#9dc9ad';
  ctx.font = '26px system-ui';
  ctx.fillText(String(detail).slice(0, 34), 256, 165);
  entry.texture.needsUpdate = true;
  return entry.mesh;
}

function dashboardBanner(text) {
  let entry = dashboardTextures.get('banner');
  if (!entry) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 112;
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1.55, 0.17), new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthTest: false }));
    mesh.position.set(0, 1.99, -1.65);
    mesh.renderOrder = 20;
    dashboardGroup.add(mesh);
    entry = { canvas, texture, mesh };
    dashboardTextures.set('banner', entry);
  }
  const ctx = entry.canvas.getContext('2d');
  ctx.clearRect(0, 0, 1024, 112);
  ctx.fillStyle = '#07130fec';
  ctx.fillRect(4, 4, 1016, 104);
  ctx.strokeStyle = '#70c997';
  ctx.lineWidth = 3;
  ctx.strokeRect(4, 4, 1016, 104);
  ctx.fillStyle = '#dff7e8';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '600 32px system-ui';
  ctx.fillText(String(text).slice(0, 70), 512, 56);
  entry.texture.needsUpdate = true;
}

function drawCameraPreview(frame) {
  let entry = dashboardTextures.get('camera-preview');
  if (!entry) {
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 360;
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthTest: false, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1.34, 0.75), material);
    mesh.position.set(0, 1.38, -1.65);
    mesh.renderOrder = 19;
    dashboardGroup.add(mesh);
    entry = { canvas, texture, mesh };
    dashboardTextures.set('camera-preview', entry);
  }
  const ctx = entry.canvas.getContext('2d');
  ctx.fillStyle = '#07130f';
  ctx.fillRect(0, 0, entry.canvas.width, entry.canvas.height);
  if (!frame) {
    ctx.fillStyle = '#dff7e8';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '600 26px system-ui';
    ctx.fillText('NO CAMERA FRAME · START CAMERA IN BODY VLM', 320, 180);
    entry.texture.needsUpdate = true;
    return;
  }
  const image = new Image();
  image.onload = () => {
    const scale = Math.min(entry.canvas.width / image.width, entry.canvas.height / image.height);
    const width = image.width * scale;
    const height = image.height * scale;
    ctx.fillStyle = '#07130f';
    ctx.fillRect(0, 0, entry.canvas.width, entry.canvas.height);
    ctx.drawImage(image, (entry.canvas.width - width) / 2, (entry.canvas.height - height) / 2, width, height);
    ctx.fillStyle = '#06100edb';
    ctx.fillRect(0, 0, entry.canvas.width, 42);
    ctx.fillStyle = '#e5f5eb';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.font = '600 22px system-ui';
    ctx.fillText(`BODY CAMERA · ${frame.width || image.width}×${frame.height || image.height}`, 14, 21);
    entry.texture.needsUpdate = true;
  };
  image.onerror = () => drawCameraPreview(null);
  image.src = `data:${frame.mime_type || 'image/jpeg'};base64,${frame.image_base64}`;
}

async function pollCameraFrame() {
  if (!renderer.xr.isPresenting || cameraPollInFlight) return;
  cameraPollInFlight = true;
  try {
    const response = await fetch('/body/camera/frame', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Camera frame HTTP ${response.status}`);
    const result = await response.json();
    const frame = result.camera || {};
    if (!result.available || !frame.image_base64) {
      cameraFrameKey = null;
      drawCameraPreview(null);
      return;
    }
    const key = `${frame.captured_at || frame.timestamp || ''}:${frame.image_base64.length}`;
    if (key !== cameraFrameKey) {
      cameraFrameKey = key;
      drawCameraPreview(frame);
    }
  } catch {
    drawCameraPreview(null);
  } finally {
    cameraPollInFlight = false;
  }
}

function startCameraPolling() {
  stopCameraPolling();
  void pollCameraFrame();
  cameraPollTimer = window.setInterval(pollCameraFrame, 125);
}

function stopCameraPolling() {
  if (cameraPollTimer !== null) window.clearInterval(cameraPollTimer);
  cameraPollTimer = null;
  cameraPollInFlight = false;
  cameraFrameKey = null;
}

function updateXRDashboard() {
  const status = latestWorldStatus || {};
  const perception = status.perception || {};
  const projections = perception.sensor_projections || {};
  const lidar = projections.lidar || {};
  const modalities = perception.modalities || {};
  const radar = modalities.mmwave_radar || {};
  const targets = radar.targets || [];
  const points = lidar.points || [];
  const source = status.source || {};
  const simulationAvailable = status.mode === 'sim' && source.source === 'sim_robot';
  const running = !!status.running;
  dashboardBanner(`LIVE · ${status.mode || 'offline'} · ${points.length} LiDAR · ${targets.length} RADAR`);
  const data = [
    ['simulation', running ? 'PAUSE SIM' : 'START SIM', simulationAvailable ? (running ? 'Running' : 'Simulator ready') : 'Simulation source required', simulationAvailable ? (running ? 'active' : 'normal') : 'disabled'],
    ['lidar', showLidar ? 'LiDAR ON' : 'LiDAR OFF', `${points.length} · ${lidar.source || 'no data'}`, showLidar ? 'active' : 'normal'],
    ['radar', showRadar ? 'mmW ON' : 'mmW OFF', `${targets.length} · ${radar.source || 'no data'}`, showRadar ? 'active' : 'normal'],
    ['follow', followBody ? 'FOLLOW ON' : 'FOLLOW BODY', simulationAvailable && running ? 'Track Body pose' : 'Start simulation first', simulationAvailable && running ? (followBody ? 'active' : 'normal') : 'disabled'],
    ['exit', 'EXIT TO UI', 'End immersive view', 'normal'],
  ];
  data.forEach(([id, title, detail, tone], index) => {
    const mesh = dashboardTexture(id, title, detail, id === 'simulation' && !simulationAvailable ? 'disabled' : tone);
    const angle = (index - 2) * 0.19;
    mesh.position.set(1.95 * Math.sin(angle), 0.72, -1.62 * Math.cos(angle));
    mesh.rotation.y = angle;
  });
}

async function sendJSON(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Body returned HTTP ${response.status}`);
  return result;
}

function applySceneView() {
  if (!followBody || !lastFrame?.perception) {
    world.position.set(0, 0, -4);
    world.rotation.y = 0;
    orbit.enabled = !renderer.xr.isPresenting;
    return;
  }
  const body = lastFrame.perception.body || {};
  const position = body.position || [0, 0, 0];
  const bx = (Number(position[0]) || 0) - (basePosition?.[0] || 0);
  const bz = -((Number(position[1]) || 0) - (basePosition?.[1] || 0));
  const yaw = Number(body.orientation) || 0;
  const rotation = Math.PI / 2 + yaw;
  const rx = Math.cos(rotation) * bx + Math.sin(rotation) * bz;
  const rz = -Math.sin(rotation) * bx + Math.cos(rotation) * bz;
  world.rotation.y = rotation;
  world.position.set(-rx, 0, -1.65 - rz);
  orbit.enabled = !renderer.xr.isPresenting;
}

function renderSensorLayers(perception) {
  const projections = perception.sensor_projections || {};
  const points = projections.lidar?.points || [];
  const lidarPositions = [];
  for (const point of points) {
    if (![point.x, point.y, point.z].every(value => Number.isFinite(Number(value)))) continue;
    lidarPositions.push(Number(point.x) - basePosition[0], Number(point.z) || 0.03, -(Number(point.y) - basePosition[1]));
  }
  lidarGroup.clear();
  if (lidarPositions.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(lidarPositions, 3));
    lidarGroup.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: '#71e4eb', size: 0.055, transparent: true, opacity: 0.9, depthTest: false })));
  }
  const radar = perception.modalities?.mmwave_radar || {};
  const radarPositions = [];
  for (const target of radar.targets || []) {
    const position = target.position_m || target.position || [];
    if (position.length < 2) continue;
    radarPositions.push(Number(position[0]) - basePosition[0], Number(position[2]) || 0.12, -(Number(position[1]) - basePosition[1]));
  }
  radarGroup.clear();
  if (radarPositions.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(radarPositions, 3));
    radarGroup.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: '#ffc36c', size: 0.13, transparent: true, opacity: 0.95, depthTest: false })));
  }
  lidarGroup.visible = showLidar;
  radarGroup.visible = showRadar;
  updateXRDashboard();
}

async function dashboardAction(action) {
  try {
    if (action === 'simulation') {
      const status = latestWorldStatus || {};
      if (status.mode !== 'sim' || status.source?.source !== 'sim_robot') {
        setStatus('Simulation control is disabled: select the simulated Body source first.', true);
        return;
      }
      await sendJSON('/worldmodel/run', { running: !status.running });
      await pollBody();
      setStatus(status.running ? 'World-model simulation paused.' : 'World-model simulation started.');
    } else if (action === 'lidar') {
      showLidar = !showLidar;
      lidarGroup.visible = showLidar;
      updateXRDashboard();
    } else if (action === 'radar') {
      showRadar = !showRadar;
      radarGroup.visible = showRadar;
      updateXRDashboard();
    } else if (action === 'follow') {
      const status = latestWorldStatus || {};
      if (status.mode !== 'sim' || status.source?.source !== 'sim_robot' || !status.running) {
        setStatus('Follow Body is available while the simulated Body is running.', true);
        return;
      }
      followBody = !followBody;
      applySceneView();
      updateXRDashboard();
    } else if (action === 'exit') {
      const session = renderer.xr.getSession();
      if (session) await session.end();
      window.location.assign('/worldmodel');
    }
  } catch (error) {
    setStatus(`Dashboard action failed: ${error.message}`, true);
  }
}

function setStatus(text, error = false) {
  statusNode.textContent = text;
  statusNode.style.color = error ? '#ffb7a5' : '#a9c3b2';
}

function labelSprite(text) {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 96;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#07110ddd';
  ctx.fillRect(0, 12, 512, 72);
  ctx.strokeStyle = '#73bd91';
  ctx.lineWidth = 3;
  ctx.strokeRect(2, 13, 508, 70);
  ctx.fillStyle = '#e0f4e7';
  ctx.font = 'bold 38px system-ui';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(text).slice(0, 24), 256, 48);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(1.25, 0.24, 1);
  return sprite;
}

function objectGeometry(item) {
  const kind = String(item.kind || 'object').toLowerCase();
  const width = Math.max(0.25, Math.min(2.2, Number(item.size) || 0.6));
  if (kind.includes('chair')) return new THREE.BoxGeometry(width * 1.15, 0.8, width * 1.05);
  if (kind.includes('table')) return new THREE.BoxGeometry(width * 1.6, 0.72, width * 1.4);
  if (kind.includes('obstacle') || kind === 'obstacle') return new THREE.CylinderGeometry(width * 0.52, width * 0.62, 1.15, 18);
  if (kind === 'target' || kind.includes('cup')) return new THREE.CylinderGeometry(width * 0.34, width * 0.42, 0.48, 18);
  return new THREE.BoxGeometry(width, Math.max(0.35, width), width);
}

function rebuildScene(frame) {
  selectionMarker.visible = false;
  if (selectedLabel) {
    world.remove(selectedLabel);
    selectedLabel.material.map?.dispose();
    selectedLabel.material.dispose();
    selectedLabel = null;
  }
  while (objectsGroup.children.length) {
    const child = objectsGroup.children.pop();
    child.traverse(node => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach(material => material.dispose());
      else node.material?.dispose();
    });
  }
  selectable.length = 0;
  const perception = frame.perception || {};
  const body = perception.body || {};
  const position = Array.isArray(body.position) ? body.position : [0, 0, 0];
  if (!basePosition) basePosition = [Number(position[0]) || 0, Number(position[1]) || 0, Number(position[2]) || 0];
  const bodyX = (Number(position[0]) || 0) - basePosition[0];
  const bodyZ = -((Number(position[1]) || 0) - basePosition[1]);
  const bodyMarker = new THREE.Group();
  bodyMarker.position.set(bodyX, 0, bodyZ);
  const bodyMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 0.32, 24), new THREE.MeshStandardMaterial({ color: '#8ee5b1', emissive: '#1a5736', emissiveIntensity: 0.55 }));
  bodyMesh.position.y = 0.2;
  bodyMarker.add(bodyMesh);
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.36, 16), new THREE.MeshStandardMaterial({ color: '#d8ffe5' }));
  nose.rotation.z = -Math.PI / 2;
  nose.position.set(0.38, 0.22, 0);
  bodyMarker.add(nose);
  const yaw = Number(body.orientation) || 0;
  bodyMarker.rotation.y = -yaw;
  const bodyLabel = labelSprite('BODY');
  bodyLabel.position.y = 0.85;
  bodyMarker.add(bodyLabel);
  objectsGroup.add(bodyMarker);

  latestObjects = Array.isArray(perception.objects) ? perception.objects : [];
  for (const item of latestObjects) {
    if (!Array.isArray(item.position)) continue;
    const px = (Number(item.position[0]) || 0) - basePosition[0];
    const pz = -((Number(item.position[1]) || 0) - basePosition[1]);
    const kind = String(item.kind || 'object').toLowerCase();
    const mesh = new THREE.Mesh(
      objectGeometry(item),
      new THREE.MeshStandardMaterial({ color: colorByKind[kind] || '#a9c4b2', roughness: 0.76, metalness: 0.02, emissive: colorByKind[kind] || '#a9c4b2', emissiveIntensity: kind.includes('mobile') ? 0.12 : 0.035 }),
    );
    mesh.position.set(px, kind.includes('obstacle') ? 0.58 : kind === 'table' || kind === 'chair' ? 0.38 : 0.25, pz);
    mesh.userData.entity = item;
    objectsGroup.add(mesh);
    selectable.push(mesh);
    const label = labelSprite(item.label || item.id || kind);
    label.position.set(px, 1.2, pz);
    objectsGroup.add(label);
  }
  const modal = perception.modalities || {};
  const source = perception.source || 'Body perception';
  document.querySelector('#source').textContent = String(source).replaceAll('_', ' ').slice(0, 24);
  document.querySelector('#pose').textContent = `(${Number(position[0] || 0).toFixed(1)}, ${Number(position[1] || 0).toFixed(1)}) · ${Math.round(yaw * 180 / Math.PI)}°`;
  const age = Number(perception.age_seconds || 0);
  document.querySelector('#age').textContent = `${age.toFixed(1)} s`;
  const sensorCount = Object.values(modal).filter(value => value && (value.available || value.status === 'available')).length;
  applySceneView();
  renderSensorLayers(perception);
  if (firstData) {
    setStatus(`${latestObjects.length} perceived objects · ${sensorCount} sensor modalities reporting · WebXR can be entered from this page`);
    firstData = false;
  } else if (age > 5) {
    setStatus(`Body observation is stale (${age.toFixed(1)} s). Showing last known scene.`, true);
  } else {
    setStatus(`${latestObjects.length} perceived objects · frame ${new Date(Number(perception.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString()}`);
  }
}

async function pollBody() {
  try {
    const response = await fetch('/worldmodel/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Body status HTTP ${response.status}`);
    const frame = await response.json();
    latestWorldStatus = frame;
    updateXRDashboard();
    if (!frame.perception?.available) {
      setStatus(frame.perception?.note || 'Body has not produced a perception frame yet.', true);
      return;
    }
    lastFrame = frame;
    rebuildScene(frame);
  } catch (error) {
    setStatus(`Cannot read Body perception: ${error.message}`, true);
  }
}

function selectAt(controller) {
  const ray = new THREE.Matrix4().extractRotation(controller.matrixWorld);
  raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
  raycaster.ray.direction.set(0, 0, -1).applyMatrix4(ray);
  scene.updateMatrixWorld(true);
  const dashboardHits = raycaster.intersectObjects(dashboardButtons, false);
  if (dashboardHits.length) {
    void dashboardAction(dashboardHits[0].object.userData.action);
    return;
  }
  const hits = raycaster.intersectObjects(selectable, false);
  if (!hits.length) return;
  const item = hits[0].object.userData.entity;
  const position = item.position || [];
  const relativeX = (Number(position[0]) || 0) - basePosition[0];
  const relativeZ = -((Number(position[1]) || 0) - basePosition[1]);
  selectionMarker.position.set(relativeX, 0.025, relativeZ);
  selectionMarker.visible = true;
  if (selectedLabel) {
    world.remove(selectedLabel);
    selectedLabel.material.map?.dispose();
    selectedLabel.material.dispose();
  }
  selectedLabel = labelSprite(`SELECTED · ${item.label || item.id || item.kind}`);
  selectedLabel.position.set(relativeX, 1.55, relativeZ);
  world.add(selectedLabel);
  selectionNode.innerHTML = `<b>${escapeText(item.label || item.id || 'Perceived object')}</b><small>${escapeText(item.kind || 'object')} · ${position.slice(0, 2).map(v => Number(v).toFixed(2)).join(', ')} m · source ${escapeText(item.position_source || 'perception')}<br>Selection only; no actuator command sent.</small>`;
}

function escapeText(value) {
  const element = document.createElement('span');
  element.textContent = String(value ?? '');
  return element.innerHTML;
}

for (let index = 0; index < 2; index += 1) {
  const controller = renderer.xr.getController(index);
  controller.addEventListener('select', () => selectAt(controller));
  const beam = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -4)]), new THREE.LineBasicMaterial({ color: '#b6f1d3' }));
  controller.add(beam);
  scene.add(controller);
  controllerRays.push(controller);
}

async function enterXR(mode) {
  if (!window.isSecureContext) {
    setStatus('WebXR needs a trusted HTTPS origin. Trust the Body proxy certificate on the Quest, then reopen this page.', true);
    return;
  }
  if (!navigator.xr) {
    setStatus('WebXR is unavailable in this browser. Use Meta Quest Browser and open the Body over trusted HTTPS.', true);
    return;
  }
  try {
    const supported = await navigator.xr.isSessionSupported(mode);
    if (!supported) throw new Error(`${mode} is not supported by this browser/device.`);
    const session = await navigator.xr.requestSession(mode, {
      optionalFeatures: ['local-floor', 'bounded-floor', 'hand-tracking'],
    });
    await renderer.xr.setSession(session);
    orbit.enabled = false;
    dashboardGroup.visible = true;
    drawCameraPreview(null);
    startCameraPolling();
    updateXRDashboard();
    document.querySelector('#enter-xr').textContent = mode === 'immersive-vr' ? 'Exit VR' : 'VR view';
    document.querySelector('#enter-ar').textContent = mode === 'immersive-ar' ? 'Exit passthrough' : 'Passthrough AR';
    setStatus(mode === 'immersive-ar'
      ? 'Passthrough is active. The Body map is an unaligned overlay; use the controller ray to operate the dashboard.'
      : 'VR is active. Use the controller ray to operate the dashboard.');
    session.addEventListener('end', () => {
      orbit.enabled = true;
      dashboardGroup.visible = false;
      stopCameraPolling();
      document.querySelector('#enter-xr').textContent = 'Enter VR';
      document.querySelector('#enter-ar').textContent = 'Passthrough AR';
      document.querySelector('#xr-input').textContent = 'Not in XR';
    }, { once: true });
  } catch (error) {
    setStatus(`Could not start ${mode}: ${error.message}`, true);
  }
}

document.querySelector('#enter-xr').addEventListener('click', () => enterXR('immersive-vr'));
document.querySelector('#enter-ar').addEventListener('click', () => enterXR('immersive-ar'));

document.querySelector('#recenter').addEventListener('click', () => {
  camera.position.set(0, 7.2, 10.5);
  orbit.target.set(0, 0, -4);
  orbit.update();
  renderer.xr.getReferenceSpace()?.reset?.();
});

window.addEventListener('resize', () => {
  const width = window.innerWidth;
  const height = window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden) stopCameraPolling();
  else if (renderer.xr.isPresenting) startCameraPolling();
});

setInterval(pollBody, 1200);
void pollBody();
renderer.setAnimationLoop(() => {
  if (!renderer.xr.isPresenting) orbit.update();
  const session = renderer.xr.getSession();
  if (session) {
    const xrCamera = renderer.xr.getCamera(camera);
    const headYaw = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ').y;
    const active = [...session.inputSources].filter(source => source.gamepad);
    const sticks = active.map(source => {
      const axes = source.gamepad.axes || [];
      const pressed = source.gamepad.buttons?.some(button => button.pressed) || false;
      return `${source.handedness || 'controller'} ${Number(axes[2] ?? axes[0] ?? 0).toFixed(1)},${Number(axes[3] ?? axes[1] ?? 0).toFixed(1)}${pressed ? ' · button' : ''}`;
    });
    const telemetry = `HEAD ${Math.round(headYaw * 180 / Math.PI)}° · ${sticks.join(' | ') || 'NO CONTROLLER'} · LIDAR ${latestWorldStatus?.perception?.sensor_projections?.lidar?.points?.length || 0} · RADAR ${latestWorldStatus?.perception?.modalities?.mmwave_radar?.targets?.length || 0}`;
    document.querySelector('#xr-input').textContent = telemetry;
    if (!renderer.userData.dashboardTelemetryAt || performance.now() - renderer.userData.dashboardTelemetryAt > 120) {
      dashboardBanner(telemetry);
      renderer.userData.dashboardTelemetryAt = performance.now();
    }
  }
  renderer.render(scene, camera);
});
