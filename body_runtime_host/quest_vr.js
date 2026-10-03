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
const cameraBackgroundTexture = new THREE.Texture();
cameraBackgroundTexture.colorSpace = THREE.SRGBColorSpace;
cameraBackgroundTexture.repeat.set(1, -1);
cameraBackgroundTexture.offset.set(0, 1);
let cameraBackgroundActive = false;
let cameraArcAspect = null;
let cameraArcWorldScale = null;
const cameraArcRoot = new THREE.Group();
const cameraArcMaterial = new THREE.MeshBasicMaterial({ map: cameraBackgroundTexture, side: THREE.DoubleSide, depthWrite: false });
const cameraArc = new THREE.Mesh(new THREE.BufferGeometry(), cameraArcMaterial);
cameraArc.visible = false;
cameraArc.renderOrder = -1;
cameraArcRoot.add(cameraArc);
let cameraPollTimer = null;
let cameraPollInFlight = false;
let lastCameraFrameId = null;
let lastDashboardTelemetryAt = 0;
let lastFnkTelemetryAt = 0;
let xrFollowYaw = null;
let xrSceneFollowing = false;
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
world.add(cameraArcRoot);
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

function setStatus(text, error = false) {
  statusNode.textContent = text;
  statusNode.style.color = error ? '#ffb7a5' : '#a9c3b2';
}

const xrFollowHeadPosition = new THREE.Vector3();
const xrFollowForward = new THREE.Vector3();
const xrFollowTarget = new THREE.Vector3();
const xrFollowBodyOffset = new THREE.Vector3();
const xrFollowYawAxis = new THREE.Vector3(0, 1, 0);

function updateXRSceneFollow(xrCamera) {
  const status = latestWorldStatus || {};
  const simulationRunning = status.mode === 'sim'
    && status.source?.source === 'sim_robot'
    && status.running === true;
  const position = status.perception?.body?.position;
  if (!simulationRunning || !Array.isArray(position) || !basePosition) {
    if (xrSceneFollowing) {
      world.position.set(0, 0, 0);
      world.rotation.set(0, 0, 0);
      world.scale.set(1, 1, 1);
      xrSceneFollowing = false;
      vrDashboard.setFollowing(false);
    }
    xrFollowYaw = null;
    return;
  }

  if (!xrSceneFollowing) {
    const orientation = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ');
    xrFollowYaw = orientation.y;
    xrSceneFollowing = true;
    vrDashboard.setFollowing(true);
  }

  const scale = 0.4;
  xrCamera.getWorldPosition(xrFollowHeadPosition);
  xrFollowForward.set(-Math.sin(xrFollowYaw), 0, -Math.cos(xrFollowYaw));
  xrFollowTarget.copy(xrFollowHeadPosition).addScaledVector(xrFollowForward, 5.5);
  xrFollowTarget.y -= 1.35;
  xrFollowBodyOffset.set(
    Number(position[0] || 0) - basePosition[0],
    0,
    -(Number(position[1] || 0) - basePosition[1]),
  ).applyAxisAngle(xrFollowYawAxis, xrFollowYaw).multiplyScalar(scale);
  world.rotation.set(0, xrFollowYaw, 0);
  world.scale.setScalar(scale);
  world.position.copy(xrFollowTarget).sub(xrFollowBodyOffset);
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
      if (cameraBackgroundActive) toggleCameraBackground();
      vrDashboard.setCameraStatus(`CAMERA · ${String(result.status || 'NO FRAME').toUpperCase()}`);
      return;
    }
    const frameId = frame.frame_id || frame.captured_at || frame.timestamp;
    if (frameId !== lastCameraFrameId) {
      lastCameraFrameId = frameId;
      await vrDashboard.setCameraFrame(frame);
      if (cameraBackgroundActive && vrDashboard.cameraBitmap) {
        cameraBackgroundTexture.image = vrDashboard.cameraBitmap;
        cameraBackgroundTexture.needsUpdate = true;
        updateCameraArcGeometry(vrDashboard.cameraBitmap);
      }
    }
  } catch (error) {
    if (cameraBackgroundActive) toggleCameraBackground();
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
  const hudAction = vrDashboard.visible ? vrDashboard.activateAt(controller, raycaster) : null;
  if (hudAction === 'simulation') {
    void toggleSimulationFromHud();
    return;
  }
  if (hudAction === 'exit') {
    void exitVrFromHud();
    return;
  }
  if (hudAction === 'camera-background') {
    toggleCameraBackground();
    return;
  }
  if (hudAction === 'dashboard') return;
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

async function toggleSimulationFromHud() {
  if (latestWorldStatus?.mode !== 'sim') {
    setStatus('World Model simulation controls are unavailable in the current Body mode.', true);
    return;
  }
  if (vrDashboard.actionBusy) return;
  const running = latestWorldStatus.running === true;
  vrDashboard.setActionBusy(true);
  setStatus(running ? 'Pausing World Model simulation…' : 'Starting World Model simulation…');
  try {
    const response = await fetch('/worldmodel/run', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ running: !running, shuffle: !running }),
    });
    if (!response.ok) throw new Error(`World Model HTTP ${response.status}`);
    const result = await response.json();
    if (typeof result.running === 'boolean') {
      latestWorldStatus = { ...latestWorldStatus, ...result };
      vrDashboard.update(latestWorldStatus);
    }
    await pollBody();
    const nowRunning = latestWorldStatus?.running === true;
    setStatus(nowRunning ? 'World Model simulation running.' : 'World Model simulation paused.');
  } catch (error) {
    setStatus(`Simulation control failed: ${error.message}`, true);
  } finally {
    vrDashboard.setActionBusy(false);
  }
}

async function exitVrFromHud() {
  const session = renderer.xr.getSession();
  if (!session) {
    setStatus('No active VR session to exit.', true);
    return;
  }
  setStatus('Exiting VR…');
  try {
    vrDashboard.persistPose(renderer.xr.getCamera(camera), true);
    await session.end();
  } catch (error) {
    setStatus(`Could not exit VR: ${error.message}`, true);
  }
}

function toggleCameraBackground() {
  if (cameraBackgroundActive) {
    cameraBackgroundActive = false;
    cameraArc.visible = false;
    vrDashboard.setCameraBackgroundActive(false);
    setStatus('Standard 3D VR view restored.');
    return;
  }
  if (!vrDashboard.cameraBitmap) {
    setStatus('Camera background unavailable: no live camera frame.', true);
    return;
  }
  cameraBackgroundTexture.image = vrDashboard.cameraBitmap;
  cameraBackgroundTexture.needsUpdate = true;
  updateCameraArcGeometry(vrDashboard.cameraBitmap);
  cameraArc.visible = true;
  cameraBackgroundActive = true;
  vrDashboard.setCameraBackgroundActive(true);
  setStatus('Live camera arc is anchored to the Body in the planar scene, 12 m out. Turn your head to look around it.');
}

function updateCameraArcGeometry(bitmap) {
  const aspect = Math.max(0.5, Math.min(3, Number(bitmap?.width) / Math.max(1, Number(bitmap?.height)) || 16 / 9));
  const worldScale = Math.max(0.01, Math.abs(Number(world.scale.x) || 1));
  if (cameraArcAspect !== null && Math.abs(aspect - cameraArcAspect) < 0.01 && Math.abs(worldScale - cameraArcWorldScale) < 0.005) return;
  cameraArcAspect = aspect;
  cameraArcWorldScale = worldScale;
  const radius = 12 / worldScale;
  const halfAngle = Math.PI * 0.305;
  const width = 2 * radius * Math.sin(halfAngle);
  const height = width / aspect;
  const segments = 72;
  const positions = [];
  const uvs = [];
  const indices = [];
  for (let row = 0; row < 2; row += 1) {
    for (let column = 0; column <= segments; column += 1) {
      const u = column / segments;
      const angle = (u * 2 - 1) * halfAngle;
      positions.push(radius * Math.sin(angle), (row === 0 ? -0.5 : 0.5) * height, -radius * Math.cos(angle));
      uvs.push(u, row);
    }
  }
  for (let column = 0; column < segments; column += 1) {
    const bottom = column;
    const top = column + segments + 1;
    indices.push(bottom, bottom + 1, top, bottom + 1, top + 1, top);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  cameraArc.geometry.dispose();
  cameraArc.geometry = geometry;
}

function escapeText(value) {
  const element = document.createElement('span');
  element.textContent = String(value ?? '');
  return element.innerHTML;
}

for (let index = 0; index < 2; index += 1) {
  const controller = renderer.xr.getController(index);
  const grip = renderer.xr.getControllerGrip(index);
  controller.addEventListener('select', () => selectAt(controller));
  controller.addEventListener('squeezestart', event => {
    try {
      vrDashboard.beginAdjust(grip, event.data);
    } catch (error) {
      setStatus(`HUD adjustment failed: ${error.message}`, true);
    }
  });
  controller.addEventListener('squeezeend', () => {
    vrDashboard.endAdjust(grip, renderer.xr.isPresenting ? renderer.xr.getCamera(camera) : null);
  });
  const beam = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -4)]), new THREE.LineBasicMaterial({ color: '#b6f1d3' }));
  controller.add(beam);
  scene.add(controller);
  scene.add(grip);
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
      : 'VR is active. HUD is about 4 m ahead. Hold either controller grip anywhere to move it; stick up/down changes distance, left/right changes size.');
    session.addEventListener('end', () => {
      orbit.enabled = true;
      cameraBackgroundActive = false;
      cameraArc.visible = false;
      vrDashboard.setCameraBackgroundActive(false);
      world.position.set(0, 0, 0);
      world.rotation.set(0, 0, 0);
      world.scale.set(1, 1, 1);
      xrSceneFollowing = false;
      xrFollowYaw = null;
      vrDashboard.setFollowing(false);
      vrDashboard.leaveSession();
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
  vrDashboard.resetPose();
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
let previousFrameAt = 0;
renderer.setAnimationLoop(time => {
  const deltaSeconds = previousFrameAt ? (time - previousFrameAt) / 1000 : 1 / 90;
  previousFrameAt = time;
  if (!renderer.xr.isPresenting) orbit.update();
  const session = renderer.xr.getSession();
  renderer.clear();
  if (session) {
    const xrCamera = renderer.xr.getCamera(camera);
    updateXRSceneFollow(xrCamera);
    const headYaw = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ').y;
    if (cameraBackgroundActive) {
      const bodyPose = latestWorldStatus?.perception?.body;
      const position = bodyPose?.position;
      if (Array.isArray(position) && basePosition) {
        cameraArcRoot.position.set(
          (Number(position[0]) || 0) - basePosition[0],
          0.75,
          -((Number(position[1]) || 0) - basePosition[1]),
        );
        cameraArcRoot.rotation.set(0, -Math.PI / 2 - (Number(bodyPose.orientation) || 0), 0);
        updateCameraArcGeometry(vrDashboard.cameraBitmap);
      }
    }
    const active = [...session.inputSources].filter(source => source.gamepad);
    const controllers = active.map(source => {
      const axes = source.gamepad.axes || [];
      const primaryMagnitude = Math.hypot(Number(axes[0]) || 0, Number(axes[1]) || 0);
      const secondaryMagnitude = Math.hypot(Number(axes[2]) || 0, Number(axes[3]) || 0);
      const axisOffset = secondaryMagnitude > primaryMagnitude ? 2 : 0;
      const pressed = source.gamepad.buttons?.some(button => button.pressed) || false;
      return {
        handedness: source.handedness || 'controller',
        x: Number(axes[axisOffset] ?? 0),
        y: Number(axes[axisOffset + 1] ?? 0),
        pressed,
      };
    });
    const headingDegrees = Math.round(headYaw * 180 / Math.PI);
    const telemetry = `HEAD ${headingDegrees}° · ${controllers.map(item => `${item.handedness} ${item.x.toFixed(1)},${item.y.toFixed(1)}${item.pressed ? ' · button' : ''}`).join(' | ') || 'NO CONTROLLER'}`;
    document.querySelector('#xr-input').textContent = telemetry;
    if (vrDashboard.visible && performance.now() - lastDashboardTelemetryAt >= 200) {
      vrDashboard.updateTelemetry({ headingDegrees, controllers });
      lastDashboardTelemetryAt = performance.now();
    }
    if (vrDashboard.visible && performance.now() - lastFnkTelemetryAt >= 500) {
      lastFnkTelemetryAt = performance.now();
      fetch('/plugins/fnk0031_wifi/controller', { cache: 'no-store', credentials: 'same-origin' })
        .then(response => response.ok ? response.json() : null)
        .then(controllerStatus => { if (controllerStatus) vrDashboard.updateController(controllerStatus); })
        .catch(() => {});
    }
  }
  renderer.render(scene, camera);
  if (session && vrDashboard.visible) {
    const xrCamera = renderer.xr.getCamera(camera);
    vrDashboard.updateAdjustment(deltaSeconds);
    vrDashboard.syncPose(xrCamera);
    vrDashboard.persistPose(xrCamera);
    renderer.clearDepth();
    renderer.render(vrDashboard.scene, camera);
  }
});
