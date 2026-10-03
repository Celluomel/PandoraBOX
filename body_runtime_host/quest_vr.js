import * as THREE from '../frontend/node_modules/three/build/three.module.js';
import { OrbitControls } from '../frontend/node_modules/three/examples/jsm/controls/OrbitControls.js';
import { QuestVRDashboard } from './quest_vr_dashboard.js';

const canvas = document.querySelector('#scene');
const statusNode = document.querySelector('#status');
const selectionNode = document.querySelector('#selection');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.xr.enabled = true;
renderer.autoClear = false;

const scene = new THREE.Scene();
const vrDashboard = new QuestVRDashboard(THREE);
let cameraPollTimer = null;
let cameraPollInFlight = false;
let lastCameraFrameId = null;
scene.background = null;
const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.05, 100);
camera.position.set(6, 9, 7);
camera.lookAt(5, 0, -6);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.target.set(5, 0, -6);
orbit.enableDamping = true;
orbit.maxPolarAngle = Math.PI * 0.48;
orbit.minDistance = 3;
orbit.maxDistance = 24;

scene.add(new THREE.HemisphereLight('#d6f5e0', '#17231b', 2.0));
const keyLight = new THREE.DirectionalLight('#fff0d6', 2.2);
keyLight.position.set(-5, 10, 3);
scene.add(keyLight);

const world = new THREE.Group();
world.position.set(0, 0, 0);
scene.add(world);
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(14, 14),
  new THREE.MeshStandardMaterial({ color: '#14241b', roughness: 0.94, metalness: 0.02, side: THREE.DoubleSide, transparent: true, opacity: 0.2 }),
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -0.035;
world.add(floor);
let sceneGrid = new THREE.GridHelper(14, 28, '#4e8d69', '#294c3a');
world.add(sceneGrid);

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
let mapFrameKey = '';
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
let mapCenter = { x: 5, z: -6 };
function configureSceneFrame(frame, bodyPosition) {
  const source = frame.source || {};
  const reportedWidth = Number(source.width);
  const reportedHeight = Number(source.height);
  const objects = frame.perception?.objects || [];
  const xs = [Number(bodyPosition[0]) || 0, ...objects.map(item => Number(item.position?.[0])).filter(Number.isFinite)];
  const ys = [Number(bodyPosition[1]) || 0, ...objects.map(item => Number(item.position?.[1])).filter(Number.isFinite)];
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Number.isFinite(reportedWidth) && reportedWidth > 0 ? reportedWidth : Math.max(8, maxX - minX + 2);
  const height = Number.isFinite(reportedHeight) && reportedHeight > 0 ? reportedHeight : Math.max(8, maxY - minY + 2);
  const explicitOrigin = Number.isFinite(reportedWidth) && Number.isFinite(reportedHeight);
  const centerX = (explicitOrigin ? width / 2 : (minX + maxX) / 2) - basePosition[0];
  const centerY = (explicitOrigin ? height / 2 : (minY + maxY) / 2) - basePosition[1];
  const key = [width, height, centerX, centerY].join(':');
  if (key === mapFrameKey) return;
  mapFrameKey = key;

  const planeWidth = width + 2;
  const planeHeight = height + 2;
  floor.geometry.dispose();
  floor.geometry = new THREE.PlaneGeometry(planeWidth, planeHeight);
  floor.position.set(centerX, -0.035, -centerY);
  world.remove(sceneGrid);
  sceneGrid.geometry.dispose();
  sceneGrid.material.dispose();
  const gridSize = Math.max(planeWidth, planeHeight);
  sceneGrid = new THREE.GridHelper(gridSize, Math.ceil(gridSize * 2), '#4e8d69', '#294c3a');
  sceneGrid.position.set(centerX, 0, -centerY);
  world.add(sceneGrid);
  roomLine.geometry.dispose();
  roomLine.geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(width, 0.08, height));
  roomLine.position.set(centerX, 0.01, -centerY);

  const targetZ = -centerY;
  mapCenter = { x: centerX, z: targetZ };
  const distance = Math.max(width, height) * 1.3;
  orbit.target.set(centerX, 0, targetZ);
  camera.position.set(centerX, distance * 0.62, targetZ + distance);
  camera.lookAt(centerX, 0, targetZ);
  orbit.update();
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
}

function setStatus(text, error = false) {
  statusNode.textContent = text;
  statusNode.style.color = error ? '#ffb7a5' : '#a9c3b2';
}

async function pollCameraFrame() {
  if (!vrDashboard.visible || cameraPollInFlight) return;
  cameraPollInFlight = true;
  try {
    const response = await fetch('/body/camera/frame', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Camera frame HTTP ${response.status}`);
    const result = await response.json();
    const frame = result.camera || {};
    if (!result.available || !frame.image_base64) {
      lastCameraFrameId = null;
      vrDashboard.setCameraStatus(`CAMERA · ${String(result.status || 'NO FRAME').toUpperCase()}`);
      return;
    }
    const frameId = frame.frame_id || frame.captured_at || frame.timestamp;
    if (frameId !== lastCameraFrameId) {
      lastCameraFrameId = frameId;
      await vrDashboard.setCameraFrame(frame);
    }
  } catch (error) {
    vrDashboard.setCameraStatus('CAMERA · STREAM ERROR');
    setStatus(`Camera preview unavailable: ${error.message}`, true);
  } finally {
    cameraPollInFlight = false;
  }
}

function startCameraPolling() {
  stopCameraPolling();
  void pollCameraFrame();
  cameraPollTimer = window.setInterval(pollCameraFrame, 200);
}

function stopCameraPolling() {
  if (cameraPollTimer !== null) window.clearInterval(cameraPollTimer);
  cameraPollTimer = null;
  cameraPollInFlight = false;
  lastCameraFrameId = null;
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
  configureSceneFrame(frame, position);
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
  renderSensorLayers(perception);
  if (firstData) {
    setStatus(`${latestObjects.length} perceived objects · ${sensorCount} sensor modalities reporting · WebXR can be entered from this page`);
    firstData = false;
  } else if (age > 5) {
    setStatus(`Body observation is stale (${age.toFixed(1)} s). Showing last known scene.`, true);
  } else {
    setStatus(`${latestObjects.length} perceived objects · frame ${new Date(Number(perception.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString()}`);
  }
  vrDashboard.update(frame);
}

async function pollBody() {
  try {
    const response = await fetch('/worldmodel/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Body status HTTP ${response.status}`);
    const frame = await response.json();
    latestWorldStatus = frame;
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
    vrDashboard.setVisible(mode === 'immersive-vr');
    if (mode === 'immersive-vr') startCameraPolling();
    document.querySelector('#enter-xr').textContent = mode === 'immersive-vr' ? 'Exit VR' : 'VR view';
    document.querySelector('#enter-ar').textContent = mode === 'immersive-ar' ? 'Exit passthrough' : 'Passthrough AR';
    setStatus(mode === 'immersive-ar'
      ? 'Passthrough is active. The Body map is an unaligned overlay; controller input is telemetry only.'
      : 'VR is active. Controller input is telemetry only.');
    session.addEventListener('end', () => {
      orbit.enabled = true;
      scene.background = null;
      stopCameraPolling();
      vrDashboard.setVisible(false);
      document.querySelector('#enter-xr').textContent = 'Enter VR';
      document.querySelector('#enter-ar').textContent = 'Passthrough AR';
      document.querySelector('#xr-input').textContent = 'Not in XR';
    }, { once: true });
  } catch (error) {
    setStatus(`Could not start ${mode}: ${error.message}`, true);
  }
}

window.addEventListener('error', event => {
  setStatus(`VR page error: ${event.message || 'unknown JavaScript error'}`, true);
});
window.addEventListener('unhandledrejection', event => {
  setStatus(`VR page error: ${event.reason?.message || String(event.reason || 'unhandled async error')}`, true);
});
renderer.domElement.addEventListener('webglcontextlost', event => {
  event.preventDefault();
  setStatus('WebGL context lost. Exit VR and reload the Quest page.', true);
});

document.querySelector('#enter-xr').addEventListener('click', () => enterXR('immersive-vr'));
document.querySelector('#enter-ar').addEventListener('click', () => enterXR('immersive-ar'));

document.querySelector('#recenter').addEventListener('click', () => {
  const distance = Math.max(12, Number(latestWorldStatus?.source?.width) || 12, Number(latestWorldStatus?.source?.height) || 12) * 1.3;
  camera.position.set(mapCenter.x, distance * 0.62, mapCenter.z + distance);
  orbit.target.set(mapCenter.x, 0, mapCenter.z);
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

setInterval(pollBody, 1200);
void pollBody();
renderer.setAnimationLoop(() => {
  if (!renderer.xr.isPresenting) orbit.update();
  const session = renderer.xr.getSession();
  renderer.clear();
  renderer.render(scene, camera);
  if (session) {
    const xrCamera = renderer.xr.getCamera(camera);
    const headYaw = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ').y;
    const active = [...session.inputSources].filter(source => source.gamepad);
    const sticks = active.map(source => {
      const axes = source.gamepad.axes || [];
      const pressed = source.gamepad.buttons?.some(button => button.pressed) || false;
      return `${source.handedness || 'controller'} ${Number(axes[2] ?? axes[0] ?? 0).toFixed(1)},${Number(axes[3] ?? axes[1] ?? 0).toFixed(1)}${pressed ? ' · button' : ''}`;
    });
    const telemetry = `HEAD ${Math.round(headYaw * 180 / Math.PI)}° · ${sticks.join(' | ') || 'NO CONTROLLER'}`;
    document.querySelector('#xr-input').textContent = telemetry;
    if (vrDashboard.visible) {
      vrDashboard.syncPose(xrCamera);
      renderer.clearDepth();
      renderer.render(vrDashboard.scene, camera);
    }
  }
});
