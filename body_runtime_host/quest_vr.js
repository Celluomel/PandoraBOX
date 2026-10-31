import * as THREE from '../frontend/node_modules/three/build/three.module.js';
import { OrbitControls } from '../frontend/node_modules/three/examples/jsm/controls/OrbitControls.js';
import * as GaussianSplats3D from '../frontend/node_modules/@mkkellogg/gaussian-splats-3d/build/gaussian-splats-3d.module.js';
import { QuestVRDashboard } from './quest_vr_dashboard.js';
import {
  cloudGrid, decodeGray16Png, fillDepthCloud, intrinsicsFor, mountFor, sampleDepthMeters, yoloMatchesDepth,
} from './depth_projection.js';

const canvas = document.querySelector('#scene');
const statusNode = document.querySelector('#status');
const selectionNode = document.querySelector('#selection');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.xr.enabled = true;
renderer.autoClear = false;
renderer.info.autoReset = false;
const xrParams = new URLSearchParams(window.location.search);
const xrRenderSettings = {
  foveation: Math.min(1, Math.max(0, Number(xrParams.get('foveation') ?? 1))),
  scale: Math.min(1.5, Math.max(0.5, Number(xrParams.get('scale') ?? 1))),
};
if (!Number.isFinite(xrRenderSettings.foveation)) xrRenderSettings.foveation = 1;
if (!Number.isFinite(xrRenderSettings.scale)) xrRenderSettings.scale = 1;
const perfStats = { last: 0, frames: 0, sum: 0, max: 0, previous: 0 };
function perfTick(time) {
  if (perfStats.previous) {
    const delta = time - perfStats.previous;
    perfStats.frames++; perfStats.sum += delta; perfStats.max = Math.max(perfStats.max, delta);
  }
  perfStats.previous = time;
  if (!perfStats.last) perfStats.last = time;
  if (time - perfStats.last >= 5000 && perfStats.frames) {
    const info = renderer.info;
    console.info('[quest-perf]', {
      meanFrameMs: Number((perfStats.sum / perfStats.frames).toFixed(2)), maxFrameMs: Number(perfStats.max.toFixed(2)),
      calls: info.render.calls, triangles: info.render.triangles, points: info.render.points,
      foveation: xrRenderSettings.foveation, scale: xrRenderSettings.scale,
    });
    perfStats.last = time; perfStats.frames = 0; perfStats.sum = 0; perfStats.max = 0;
  }
  renderer.info.reset();
}

const scene = new THREE.Scene();
const vrDashboard = new QuestVRDashboard(THREE, renderer.capabilities.getMaxAnisotropy());
const hudPreview = new URLSearchParams(window.location.search).get('hud_preview') === '1';
if (hudPreview) vrDashboard.setVisible(true);
const cameraBackgroundTexture = new THREE.Texture();
cameraBackgroundTexture.colorSpace = THREE.SRGBColorSpace;
cameraBackgroundTexture.repeat.set(1, -1);
cameraBackgroundTexture.offset.set(0, 1);
let cameraBackgroundActive = false;
let cameraArcAspect = null;
let cameraArcWorldScale = null;
const cameraArcRoot = new THREE.Group();
const cameraArcMaterial = new THREE.MeshBasicMaterial({ map: cameraBackgroundTexture, side: THREE.DoubleSide, depthTest: false, depthWrite: false });
const cameraArc = new THREE.Mesh(new THREE.BufferGeometry(), cameraArcMaterial);
cameraArc.visible = false;
cameraArc.renderOrder = -1000;
cameraArcRoot.add(cameraArc);
let cameraPollTimer = null;
let cameraPollInFlight = false;
let imuPollInFlight = false;
let lastCameraFrameId = null;
let lastDashboardTelemetryAt = 0;
let lastFnkTelemetryAt = 0;
let xrFollowYaw = null;
let xrSceneFollowing = false;
const xrSceneOffset = new THREE.Vector3();
let xrSceneYawOffset = 0;
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
  new THREE.MeshLambertMaterial({ color: '#14241b', side: THREE.DoubleSide, transparent: true, opacity: 0.2 }),
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
const bodyGroup = new THREE.Group();
world.add(bodyGroup);
const sensorSceneGroup = new THREE.Group();
sensorSceneGroup.visible = false;
world.add(sensorSceneGroup);
const sensorGround = new THREE.Group();
const sensorGroundPlane = new THREE.Mesh(
  new THREE.PlaneGeometry(4.2, 4.2),
  new THREE.MeshLambertMaterial({ color: '#14241b', side: THREE.DoubleSide, transparent: true, opacity: 0.14 }),
);
sensorGroundPlane.rotation.x = -Math.PI / 2;
sensorGroundPlane.position.y = -0.035;
sensorGround.add(sensorGroundPlane);
const sensorGroundGrid = new THREE.GridHelper(4.2, 14, '#4e8d69', '#294c3a');
sensorGroundGrid.position.y = 0.005;
sensorGround.add(sensorGroundGrid);
sensorSceneGroup.add(sensorGround);
function createSensorPointMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    vertexColors: true,
    uniforms: {
      uSizeM: { value: 0.04 },
      uViewportHeight: { value: 1 },
      uOpacity: { value: 0.94 },
      uFadeNear: { value: 2.0 },
      uFadeFar: { value: 6.0 },
      uStale: { value: 0 },
    },
    vertexShader: `
      uniform float uSizeM;
      uniform float uViewportHeight;
      uniform float uFadeNear;
      uniform float uFadeFar;
      varying vec3 vColor;
      varying float vFade;
      void main() {
        vColor = color;
        vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
        float dist = max(0.1, -viewPosition.z);
        gl_Position = projectionMatrix * viewPosition;
        gl_PointSize = clamp(uSizeM * uViewportHeight * 0.5 * projectionMatrix[1][1] / dist, 2.0, 24.0);
        vFade = 1.0 - 0.55 * smoothstep(uFadeNear, uFadeFar, dist);
      }
    `,
    fragmentShader: `
      uniform float uOpacity;
      uniform float uStale;
      varying vec3 vColor;
      varying float vFade;
      void main() {
        float r = length(gl_PointCoord - vec2(0.5));
        if (r > 0.5) discard;
        float alpha = (1.0 - smoothstep(0.3, 0.5, r)) * uOpacity * vFade * (1.0 - 0.6 * uStale);
        gl_FragColor = vec4(vColor, alpha);
      }
    `,
  });
}
const sensorDepthCloud = new THREE.Points(new THREE.BufferGeometry(), createSensorPointMaterial());
sensorDepthCloud.frustumCulled = false;
sensorSceneGroup.add(sensorDepthCloud);
const sensorObjectGroup = new THREE.Group();
sensorSceneGroup.add(sensorObjectGroup);
const sensorRadarGroup = new THREE.Group();
sensorSceneGroup.add(sensorRadarGroup);
const sensorBodyMarker = new THREE.Group();
sensorSceneGroup.add(sensorBodyMarker);
const sensorBodyMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(0.12, 0.14, 0.14, 24),
  new THREE.MeshLambertMaterial({ color: '#8ee5b1', emissive: '#1a5736', emissiveIntensity: 0.55 }),
);
sensorBodyMesh.position.y = 0.07;
sensorBodyMarker.add(sensorBodyMesh);
const sensorBodyNose = new THREE.Mesh(
  new THREE.ConeGeometry(0.06, 0.18, 16),
  new THREE.MeshLambertMaterial({ color: '#d8ffe5' }),
);
sensorBodyNose.rotation.x = -Math.PI / 2;
sensorBodyNose.position.set(0, 0.08, -0.17);
sensorBodyMarker.add(sensorBodyNose);
const sensorBodyLabel = labelSprite('BODY · SENSOR ORIGIN');
sensorBodyLabel.scale.set(0.9, 0.17, 1);
sensorBodyLabel.position.set(0, 0.43, 0);
sensorBodyMarker.add(sensorBodyLabel);
const semanticSplatGroup = new THREE.Group();
world.add(semanticSplatGroup);
const semanticSplatNodes = new Map();
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
const controllerRayRotation = new THREE.Matrix4();
const controllerRayNormal = new THREE.Vector3(0, 0, 1);
const reticleDirection = new THREE.Vector3();
const selectable = [];
const controllerRays = [];
const colorByKind = { table: '#d3bd67', chair: '#83b3d5', obstacle: '#a77ba5', mobile_obstacle: '#db83bf', target: '#efa678' };
let lastFrame = null;
let sceneRenderKey = '';
let basePosition = null;
let firstData = true;
let latestObjects = [];
let latestWorldStatus = null;
let gaussianAssetStatus = null;
let gaussianViewer = null;
let gaussianLoadPromise = null;
let activeSceneMode = 'simulation';
let sensorDepthPollInFlight = false;
let sensorYoloPollInFlight = false;
let sensorRadarPollInFlight = false;
let ultrasonicPollInFlight = false;
let sensorFrameId = '';
let sensorDepthValues = null;
let sensorDepthFrame = null;
let sensorDepthIntrinsics = null;
let sensorDepthHeightM = 0.12;
let sensorDepthCapturedAt = 0;
let sensorCloudBuffers = null;
const sensorPointViewport = new THREE.Vector2();
let latestSensorYolo = {};
let latestSensorDepthStatus = null;
let sensorMetricCalibration = null;
let sensorCalibrationCheckedAt = 0;
let sensorYoloFrameId = '';
let sensorYoloLastPairedAt = 0;
let sensorYoloNoDetectionSince = 0;
let sensorYoloDisplayedCount = 0;
let sensorRadarSignature = '';
let sensorViewInitialized = false;
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
  const simulationRunning = activeSceneMode === 'simulation'
    && status.mode === 'sim'
    && status.source?.source === 'sim_robot'
    && status.running === true;
  const position = status.perception?.body?.position;
  if (!simulationRunning || !Array.isArray(position) || !basePosition) {
    if (xrSceneFollowing) {
      xrSceneFollowing = false;
      vrDashboard.setFollowing(false);
    }
    world.position.copy(xrSceneOffset);
    world.rotation.set(0, xrSceneYawOffset, 0);
    world.scale.set(1, 1, 1);
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
  xrFollowTarget.copy(xrFollowHeadPosition).addScaledVector(xrFollowForward, 3.0);
  xrFollowTarget.y -= 1.35;
  xrFollowTarget.add(xrSceneOffset);
  const sceneYaw = xrFollowYaw + Math.PI / 2 + xrSceneYawOffset;
  xrFollowBodyOffset.set(
    Number(position[0] || 0) - basePosition[0],
    0,
    -(Number(position[1] || 0) - basePosition[1]),
  ).applyAxisAngle(xrFollowYawAxis, sceneYaw).multiplyScalar(scale);
  world.rotation.set(0, sceneYaw, 0);
  world.scale.setScalar(scale);
  world.position.copy(xrFollowTarget).sub(xrFollowBodyOffset);
}

function readThumbstick(gamepad) {
  const axes = gamepad?.axes || [];
  const primary = [Number(axes[0]) || 0, Number(axes[1]) || 0];
  const secondary = [Number(axes[2]) || 0, Number(axes[3]) || 0];
  return Math.hypot(...secondary) > Math.hypot(...primary) ? secondary : primary;
}

function applyDeadzone(value, deadzone = 0.16) {
  const magnitude = Math.abs(value);
  if (magnitude <= deadzone) return 0;
  return Math.sign(value) * Math.min(1, (magnitude - deadzone) / (1 - deadzone));
}

function updateXRLocomotion(inputSources, xrCamera, deltaSeconds) {
  if (vrDashboard.grabbedController) return;
  const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
  if (!elapsed) return;
  const sources = [...inputSources].filter(source => source.gamepad);
  const left = sources.find(source => source.handedness === 'left');
  const right = sources.find(source => source.handedness === 'right');
  const fallback = sources[0];
  const moveStick = readThumbstick((left || fallback)?.gamepad);
  const turnStick = right ? readThumbstick(right.gamepad) : [0, 0];
  const moveX = applyDeadzone(moveStick[0]);
  const moveForward = -applyDeadzone(moveStick[1]);
  const headYaw = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ').y;
  const move = new THREE.Vector3(moveX, 0, -moveForward).applyAxisAngle(xrFollowYawAxis, headYaw);
  xrSceneOffset.addScaledVector(move, -2.4 * elapsed);
  xrSceneYawOffset -= applyDeadzone(turnStick[0]) * 1.35 * elapsed;
}

async function pollCameraFrame() {
  if (!vrDashboard.visible || cameraPollInFlight) return;
  cameraPollInFlight = true;
  try {
    const response = await fetch('/body/camera/image', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Camera frame HTTP ${response.status}`);
    const result = await response.json();
    const frame = result.camera || {};
    if (!result.available || !frame.image_base64) {
      vrDashboard.setCameraStatus(`CAMERA · ${String(result.status || 'NO FRAME').toUpperCase()}`, true);
      return;
    }
    const frameId = frame.frame_id || frame.captured_at || frame.timestamp;
    if (String(frameId) === String(lastCameraFrameId)) return;
    lastCameraFrameId = frameId;
    await vrDashboard.setCameraFrame(frame);
    if (cameraBackgroundActive && vrDashboard.cameraBitmap) {
      cameraBackgroundTexture.image = vrDashboard.cameraBitmap;
      cameraBackgroundTexture.needsUpdate = true;
      updateCameraArcGeometry(vrDashboard.cameraBitmap);
    }
  } catch (error) {
    vrDashboard.setCameraStatus('CAMERA · RECONNECTING', true);
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
  c.width = 640;
  c.height = 96;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#07110ddd';
  ctx.fillRect(0, 12, 640, 72);
  ctx.strokeStyle = '#73bd91';
  ctx.lineWidth = 3;
  ctx.strokeRect(2, 13, 636, 70);
  ctx.fillStyle = '#e0f4e7';
  ctx.font = 'bold 38px system-ui';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(text).slice(0, 32), 320, 48);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(1.25, 0.24, 1);
  return sprite;
}

function disposeChildren(group) {
  while (group.children.length) {
    const child = group.children[group.children.length - 1];
    group.remove(child);
    child.traverse(node => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach(material => material.dispose());
      else { node.material?.map?.dispose(); node.material?.dispose(); }
    });
  }
}

async function decodeSensorImage(encoded, mime = 'image/jpeg') {
  if (!encoded) return null;
  const bytes = Uint8Array.from(atob(encoded), character => character.charCodeAt(0));
  const bitmap = await createImageBitmap(new Blob([bytes], { type: mime }));
  const canvas = document.createElement('canvas');
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(bitmap, 0, 0);
  bitmap.close();
  return { width: canvas.width, height: canvas.height, pixels: context.getImageData(0, 0, canvas.width, canvas.height).data };
}

async function refreshSensorMetricCalibration() {
  const now = Date.now();
  if (now - sensorCalibrationCheckedAt < 10000) return;
  sensorCalibrationCheckedAt = now;
  try {
    const response = await fetch('/body/camera/depth-calibration', { cache: 'no-store', credentials: 'same-origin' });
    if (response.ok) sensorMetricCalibration = await response.json();
  } catch (error) {
    console.warn('Could not load persistent MiDaS metric calibration:', error);
  }
}

function updateSensorPointUniforms() {
  const uniforms = sensorDepthCloud.material.uniforms;
  let height = 0;
  if (renderer.xr.isPresenting) {
    const eye = renderer.xr.getCamera().cameras?.[0];
    height = eye?.viewport?.height || eye?.viewport?.h || 0;
  }
  if (!height) height = renderer.getDrawingBufferSize(sensorPointViewport).y;
  uniforms.uViewportHeight.value = height || 1;
  const age = sensorDepthCapturedAt > 0 ? Date.now() / 1000 - sensorDepthCapturedAt : 0;
  uniforms.uStale.value = Math.min(1, Math.max(0, (age - 1.0) / 3.0));
}

function buildSensorDepthCloud(depth, depthImage, colorImage) {
  if (!depthImage?.width || !colorImage?.pixels) return false;
  const grid = cloudGrid(depthImage.width, depthImage.height);
  if (!sensorCloudBuffers || sensorCloudBuffers.count !== grid.count) {
    sensorCloudBuffers = {
      count: grid.count,
      positions: new Float32Array(grid.count * 3),
      colors: new Float32Array(grid.count * 3),
    };
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(sensorCloudBuffers.positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(sensorCloudBuffers.colors, 3));
    sensorDepthCloud.geometry.dispose();
    sensorDepthCloud.geometry = geometry;
  }
  const mount = mountFor(null, depth);
  const intrinsics = intrinsicsFor(depthImage.width, depthImage.height, depth.intrinsics || depth.camera_intrinsics || {});
  vrDashboard.updateDepthIntrinsics(intrinsics, depthImage.width, depthImage.height);
  const count = fillDepthCloud({
    depth: depthImage, color: colorImage, grid, intrinsics, calibration: sensorMetricCalibration,
    heightM: mount.heightM, positions: sensorCloudBuffers.positions, colors: sensorCloudBuffers.colors,
  });
  const geometry = sensorDepthCloud.geometry;
  geometry.setDrawRange(0, count);
  geometry.getAttribute('position').needsUpdate = true;
  geometry.getAttribute('color').needsUpdate = true;
  sensorDepthValues = depthImage;
  sensorDepthFrame = depth;
  sensorDepthIntrinsics = intrinsics;
  sensorDepthHeightM = mount.heightM;
  sensorDepthCapturedAt = Number(depth.captured_at) || 0;
  sensorYoloFrameId = '';
  updateSensorYolo(latestSensorYolo);
  return true;
}

function updateSensorYolo(yolo) {
  const pairing = yoloMatchesDepth(yolo, sensorDepthFrame);
  const now = Date.now();
  const detections = pairing.ok ? yolo.detections || [] : [];
  if (!pairing.ok || !sensorDepthValues || !sensorDepthIntrinsics) {
    if (sensorYoloDisplayedCount && now - sensorYoloLastPairedAt <= 1400) return sensorYoloDisplayedCount;
    if (sensorYoloDisplayedCount) {
      disposeChildren(sensorObjectGroup);
      sensorYoloDisplayedCount = 0;
      sensorYoloFrameId = '';
    }
    return 0;
  }
  if (!detections.length) {
    if (!sensorYoloNoDetectionSince) sensorYoloNoDetectionSince = now;
    if (sensorYoloDisplayedCount && now - sensorYoloNoDetectionSince < 700) return sensorYoloDisplayedCount;
    if (sensorYoloDisplayedCount) disposeChildren(sensorObjectGroup);
    sensorYoloDisplayedCount = 0;
    sensorYoloFrameId = '';
    return 0;
  }
  sensorYoloNoDetectionSince = 0;
  const frameId = `${yolo.frame_id || yolo.captured_at}|${sensorDepthFrame?.frame_id}|${sensorMetricCalibration?.available ? 'cal' : 'rel'}`;
  sensorYoloLastPairedAt = now;
  if (frameId === sensorYoloFrameId) return sensorYoloDisplayedCount;
  sensorYoloFrameId = frameId;
  disposeChildren(sensorObjectGroup);
  sensorYoloDisplayedCount = 0;
  const width = sensorDepthValues.width;
  const height = sensorDepthValues.height;
  const { fx, fy, cx, cy } = sensorDepthIntrinsics;
  const color = '#55e7cc';
  for (const detection of detections) {
    const box = detection.bbox;
    if (!Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite)) continue;
    const [x1, y1, x2, y2] = box.map(value => Math.max(0, Math.min(1, Number(value))));
    if (x2 <= x1 || y2 <= y1) continue;
    const u = (x1 + x2) / 2;
    const v = (y1 + y2) / 2;
    const sample = sampleDepthMeters(sensorDepthValues, u, v, sensorMetricCalibration);
    const z = sample.meters;
    const boxWidth = Math.max(0.08, (x2 - x1) * width * z / fx);
    const boxHeight = Math.max(0.08, (y2 - y1) * height * z / fy);
    const centerX = (u * (width - 1) - cx) * z / fx;
    const centerY = sensorDepthHeightM + (cy - v * (height - 1)) * z / fy;
    const boxGeometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(boxWidth, boxHeight, Math.max(0.04, z * 0.025)));
    const labelName = String(detection.label || detection.class_name || '').toLowerCase();
    const detectionColor = labelName === 'person' ? '#63e6a8'
      : ['tv', 'tvmonitor', 'monitor'].includes(labelName) ? '#f0c26f'
        : ['chair', 'couch', 'bed'].includes(labelName) ? '#b99aff'
          : ['car', 'bicycle', 'motorcycle', 'bus', 'truck'].includes(labelName) ? '#6bd4ed' : color;
    const outline = new THREE.LineSegments(boxGeometry, new THREE.LineBasicMaterial({ color: detectionColor, depthTest: false, transparent: true, opacity: 0.95 }));
    outline.position.set(centerX, centerY, -z);
    outline.renderOrder = 3;
    sensorObjectGroup.add(outline);
    const confidence = Math.round(Number(detection.confidence || detection.score || 0) * 100);
    const distanceText = sample.calibrated ? `${z.toFixed(1)} m` : 'rel.';
    const label = labelSprite(`${detection.label || detection.class_name || 'object'} ${confidence}% · ${distanceText}`);
    label.scale.set(Math.max(0.9, Math.min(1.8, boxWidth)), 0.24, 1);
    label.position.set(centerX, centerY + boxHeight / 2 + 0.16, -z);
    label.renderOrder = 4;
    sensorObjectGroup.add(label);
    sensorYoloDisplayedCount += 1;
  }
  return sensorYoloDisplayedCount;
}

function updateSensorRadar(perception) {
  const radar = perception?.modalities?.mmwave_radar || {};
  const targets = Array.isArray(radar.targets) ? radar.targets : [];
  const bodyPosition = perception?.body?.position || [0, 0, 0];
  const yaw = Number(perception?.body?.orientation || 0);
  const sourceFrame = String(radar.frame || 'body').toLowerCase();
  const isLd2450 = /^hlk_ld2450/i.test(String(radar.source || ''));
  const signature = JSON.stringify([radar.source, sourceFrame, latestSensorYolo.frame_id, targets.map(target => [target.id, target.position_m || target.position, target.velocity_mps || target.velocity, target.radial_speed_mps, target.classification])]);
  if (signature === sensorRadarSignature) return targets.length;
  sensorRadarSignature = signature;
  disposeChildren(sensorRadarGroup);
  for (const target of targets) {
    const rawPosition = target.position_m || target.position || [];
    const rawVelocity = target.velocity_mps || target.velocity || [0, 0];
    const position = isLd2450 ? [Number(rawPosition[1]), -Number(rawPosition[0]), Number(rawPosition[2] || 0)] : rawPosition;
    const local = vrDashboard.sensorLocal(position, sourceFrame, bodyPosition, yaw);
    if (!local || !Number.isFinite(local.forward) || !Number.isFinite(local.left)) continue;
    const velocity = isLd2450 ? [Number(rawVelocity[1] || 0), -Number(rawVelocity[0] || 0)] : rawVelocity;
    const radial = Number(target.radial_speed_mps);
    const yoloMatch = isLd2450 ? matchRadarTargetToYolo(rawPosition) : null;
    const rawClass = String(target.classification || 'unknown');
    const classification = /^(unknown|target|object)$/i.test(rawClass) && yoloMatch
      ? String(yoloMatch.label || yoloMatch.class_name || yoloMatch.class || 'person')
      : rawClass;
    const moving = /moving|mobile/i.test(String(target.classification || ''))
      || (Number.isFinite(radial) && Math.abs(radial) >= 0.05)
      || Math.hypot(Number(velocity[0] || 0), Number(velocity[1] || 0)) >= 0.05;
    const color = moving ? '#ef91c5' : '#f2ce73';
    const marker = new THREE.Mesh(new THREE.SphereGeometry(0.085, 12, 10), new THREE.MeshBasicMaterial({ color }));
    marker.position.set(-local.left, 0.12, -local.forward);
    sensorRadarGroup.add(marker);
    const speedText = Number.isFinite(radial) ? ` ${radial >= 0 ? '+' : ''}${radial.toFixed(2)} m/s` : '';
    const label = labelSprite(`${classification}${speedText}`);
    label.position.set(-local.left, 0.38, -local.forward);
    sensorRadarGroup.add(label);
  }
  return targets.length;
}

function matchRadarTargetToYolo(radarPosition) {
  if (!sensorDepthValues || !Array.isArray(radarPosition) || radarPosition.length < 2) return null;
  if (!sensorDepthIntrinsics || !yoloMatchesDepth(latestSensorYolo, sensorDepthFrame).ok) return null;
  const lateral = Number(radarPosition[0]);
  const forward = Number(radarPosition[1]);
  if (!Number.isFinite(lateral) || !Number.isFinite(forward) || forward <= 0) return null;
  const radarRange = Math.hypot(lateral, forward);
  const radarBearing = Math.atan2(lateral, forward);
  const detections = latestSensorYolo?.state === 'ready' ? latestSensorYolo.detections || [] : [];
  let best = null;
  for (const detection of detections) {
    const box = detection.bbox;
    const confidence = Number(detection.confidence ?? detection.score ?? 0);
    if (!Array.isArray(box) || box.length !== 4 || confidence < 0.4) continue;
    const u = (Number(box[0]) + Number(box[2])) / 2;
    if (!Number.isFinite(u)) continue;
    const cameraBearing = Math.atan((u * (sensorDepthValues.width - 1) - sensorDepthIntrinsics.cx) / sensorDepthIntrinsics.fx);
    const bearingError = Math.abs(cameraBearing - radarBearing);
    if (bearingError > 14 * Math.PI / 180) continue;
    const v = (Number(box[1]) + Number(box[3])) / 2;
    const visual = sampleDepthMeters(sensorDepthValues, u, v, sensorMetricCalibration);
    if (!visual.calibrated) continue;
    const visualRange = visual.meters;
    const rangeTolerance = Math.max(0.65, radarRange * 0.3);
    const rangeError = Math.abs(visualRange - radarRange);
    if (rangeError > rangeTolerance) continue;
    const score = bearingError / (14 * Math.PI / 180) + rangeError / rangeTolerance;
    if (!best || score < best.score) best = { ...detection, score };
  }
  return best;
}

function updateSensorReadout(depth, yoloCount, radarCount) {
  const age = Number(depth?.captured_at) > 0 ? Math.max(0, Date.now() / 1000 - Number(depth.captured_at)) : Infinity;
  document.querySelector('#source').textContent = 'LIVE SENSORS';
  document.querySelector('#pose').textContent = 'Sensor origin · heading uncalibrated';
  document.querySelector('#age').textContent = Number.isFinite(age) ? `${age.toFixed(1)} s` : '—';
  const rangeStatus = sensorMetricCalibration?.available ? 'calibrated YOLOX ranges' : 'relative depth; calibrate for metres';
  setStatus(`Live sensor scene · MiDaS ${depth?.runtime || depth?.state || 'waiting'}${depth?.inference_ms != null ? ` ${Number(depth.inference_ms).toFixed(1)} ms` : ''} · ${yoloCount} YOLOX labels · ${radarCount} mmWave targets · ${rangeStatus}`);
  vrDashboard.updateSensorStatus({
    yolo: `${latestSensorYolo?.state || 'READY'} · ${yoloCount} OBJECTS${latestSensorYolo?.latency_ms != null ? ` · ${Number(latestSensorYolo.latency_ms).toFixed(0)} MS` : ''}`,
    midas: `${depth?.state || depth?.runtime || 'WAITING'} · ${depth?.runtime || '—'}${depth?.inference_ms != null ? ` · ${Number(depth.inference_ms).toFixed(0)} MS` : ''}${Number.isFinite(age) ? ` · ${age.toFixed(0)}S` : ''}`,
  });
}

async function pollSensorDepth() {
  if (sensorDepthPollInFlight || activeSceneMode !== 'sensors') return;
  sensorDepthPollInFlight = true;
  try {
    await refreshSensorMetricCalibration();
    const response = await fetch('/body/camera/depth', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error('MiDaS endpoint unavailable');
    const depth = await response.json();
    latestSensorDepthStatus = depth;
    if (depth.frame_id && depth.frame_id !== sensorFrameId && depth.depth_gray_jpeg_base64) {
      const colorPromise = decodeSensorImage(depth.depth_jpeg_base64 || depth.depth_gray_jpeg_base64);
      let depthImage = null;
      if (depth.depth_raw_png_base64) {
        try { depthImage = await decodeGray16Png(depth.depth_raw_png_base64); }
        catch (error) { console.warn('Could not decode raw 16-bit MiDaS depth; using 8-bit preview:', error); }
      }
      if (!depthImage) {
        const gray = await decodeSensorImage(depth.depth_gray_jpeg_base64);
        if (gray?.pixels) depthImage = { width: gray.width, height: gray.height, pixels: gray.pixels };
      }
      const color = await colorPromise;
      if (depthImage && color && buildSensorDepthCloud(depth, depthImage, color)) sensorFrameId = depth.frame_id;
    }
    const yoloCount = updateSensorYolo(latestSensorYolo);
    updateSensorReadout(depth, yoloCount, sensorRadarTargetCount);
  } catch (error) {
    setStatus(`Live MiDaS scene unavailable: ${error.message}`, true);
  } finally {
    sensorDepthPollInFlight = false;
  }
}

async function pollSensorYolo() {
  if (sensorYoloPollInFlight || activeSceneMode !== 'sensors') return;
  sensorYoloPollInFlight = true;
  try {
    const response = await fetch('/body/camera/yolo/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error('YOLOX endpoint unavailable');
    latestSensorYolo = await response.json();
    vrDashboard.updateYoloResult(latestSensorYolo);
    const yoloCount = updateSensorYolo(latestSensorYolo);
    updateSensorReadout(latestSensorDepthStatus, yoloCount, sensorRadarTargetCount);
  } catch (error) {
    console.warn('Could not refresh VR YOLOX detections:', error);
  } finally {
    sensorYoloPollInFlight = false;
  }
}

let sensorRadarTargetCount = 0;
async function pollSensorRadar() {
  if (sensorRadarPollInFlight || activeSceneMode !== 'sensors') return;
  sensorRadarPollInFlight = true;
  try {
    const response = await fetch('/plugins/mmwave_radar/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error('mmWave endpoint unavailable');
    const radarStatus = await response.json();
    const radarSample = radarStatus.sample || {};
    const bodyPerception = latestWorldStatus?.perception || {};
    sensorRadarTargetCount = updateSensorRadar({
      body: bodyPerception.body,
      modalities: { mmwave_radar: radarSample },
    });
  } catch (error) {
    console.warn('Could not refresh VR mmWave targets:', error);
  } finally {
    sensorRadarPollInFlight = false;
  }
}

async function pollUltrasonicStatus() {
  if (ultrasonicPollInFlight || activeSceneMode !== 'sensors') return;
  ultrasonicPollInFlight = true;
  try {
    const response = await fetch('/plugins/ultrasonic/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error('Ultrasonic endpoint unavailable');
    vrDashboard.updateUltrasonicStatus(await response.json());
  } catch (error) {
    vrDashboard.updateUltrasonicStatus({ available: false, sample: null, error: error.message });
  } finally {
    ultrasonicPollInFlight = false;
  }
}

function pollSensorScene() {
  if (activeSceneMode !== 'sensors') return;
  void pollSensorDepth();
  void pollSensorYolo();
  void pollSensorRadar();
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

function semanticSeed(value) {
  let hash = 2166136261;
  for (const char of String(value)) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
  return () => {
    hash += 0x6D2B79F5;
    let n = hash;
    n = Math.imul(n ^ (n >>> 15), n | 1);
    n ^= n + Math.imul(n ^ (n >>> 7), n | 61);
    return ((n ^ (n >>> 14)) >>> 0) / 4294967296;
  };
}

function updateGaussianPreview(points, group) {
  const center = group.center_m || [];
  if (!Array.isArray(center) || center.length < 2) return false;
  const cx = Number(center[0]);
  const cy = Number(center[1]);
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return false;
  const confidence = Number(group.confidence);
  const extentValue = Number(group.extent_m);
  const extent = Math.max(0.12, Math.min(1.2, Number.isFinite(extentValue) ? extentValue : 0.4));
  const signature = JSON.stringify([cx, cy, center[2], extent, confidence, group.label, group.role]);
  points.userData.semanticGroup = group;
  if (points.userData.semanticSignature === signature) return true;

  const random = semanticSeed(group.entity_id);
  const positions = points.geometry.getAttribute('position').array;
  const sizes = points.geometry.getAttribute('splatSize').array;
  for (let i = 0; i < 96; i += 1) {
    const angle = random() * Math.PI * 2;
    const radius = Math.sqrt(-2 * Math.log(Math.max(0.0001, random()))) * extent * 0.31;
    const offset = i * 3;
    positions[offset] = cx - basePosition[0] + Math.cos(angle) * radius;
    positions[offset + 1] = 0.38 + (random() - 0.5) * extent * 0.52;
    positions[offset + 2] = -(cy - basePosition[1]) + Math.sin(angle) * radius;
    sizes[i] = 0.035 + random() * 0.055;
  }
  points.geometry.getAttribute('position').needsUpdate = true;
  points.geometry.getAttribute('splatSize').needsUpdate = true;
  points.material.uniforms.confidence.value = Number.isFinite(confidence)
    ? Math.max(0, Math.min(1, confidence)) : 0.5;
  points.userData.semanticSignature = signature;
  return true;
}

function createGaussianPreview(group) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(96 * 3), 3));
  geometry.setAttribute('splatSize', new THREE.Float32BufferAttribute(new Float32Array(96), 1));
  const points = new THREE.Points(geometry, new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: { tint: { value: new THREE.Color('#55ead1') }, confidence: { value: 0.5 } },
    vertexShader: `attribute float splatSize; uniform float confidence; varying float vConfidence; void main(){ vec4 mvPosition=modelViewMatrix*vec4(position,1.0); gl_Position=projectionMatrix*mvPosition; gl_PointSize=clamp(splatSize*210.0/max(0.2,-mvPosition.z),2.0,22.0); vConfidence=confidence; }`,
    fragmentShader: `uniform vec3 tint; varying float vConfidence; void main(){ float r=length(gl_PointCoord-vec2(0.5)); float a=exp(-r*r*18.0)*(1.0-smoothstep(0.08,0.5,r))*mix(0.35,0.82,vConfidence); if(a<0.015) discard; gl_FragColor=vec4(tint,a); }`,
  }));
  updateGaussianPreview(points, group);
  return points;
}

function rebuildScene(frame) {
  const perception = frame.perception || {};
  const body = perception.body || {};
  const position = Array.isArray(body.position) ? body.position : [0, 0, 0];
  const objects = Array.isArray(perception.objects) ? perception.objects.filter(item => item && typeof item === 'object') : [];
  const semanticSplatScene = perception.semantic_splats || {};
  const semanticGroups = Array.isArray(semanticSplatScene.groups)
    ? semanticSplatScene.groups.filter(group => group && typeof group === 'object') : [];
  const renderKey = JSON.stringify({
    pose: [position[0], position[1], body.orientation],
    objects: objects.map(item => [item.id, item.label, item.kind, item.size,
      item.position?.[0], item.position?.[1], item.position?.[2]]),
    semantic: semanticGroups.map(group => [group.entity_id, group.center_m, group.extent_m,
      group.confidence, group.label, group.role, group.description, group.attributes,
      group.relations, group.image_region]),
  });
  if (renderKey === sceneRenderKey) {
    updateSceneStatus(frame, perception, objects, semanticGroups, semanticSplatScene);
    vrDashboard.update(frame);
    return;
  }
  sceneRenderKey = renderKey;
  selectionMarker.visible = false;
  if (selectedLabel) {
    world.remove(selectedLabel);
    selectedLabel.material.map?.dispose();
    selectedLabel.material.dispose();
    selectedLabel = null;
  }
  while (objectsGroup.children.length) {
    const child = objectsGroup.children[objectsGroup.children.length - 1];
    objectsGroup.remove(child);
    child.traverse(node => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach(material => material.dispose());
      else node.material?.dispose();
    });
  }
  selectable.length = 0;
  if (!basePosition) basePosition = [Number(position[0]) || 0, Number(position[1]) || 0, Number(position[2]) || 0];
  configureSceneFrame(frame, position);
  const bodyX = (Number(position[0]) || 0) - basePosition[0];
  const bodyZ = -((Number(position[1]) || 0) - basePosition[1]);
  const bodyMarker = new THREE.Group();
  bodyMarker.position.set(bodyX, 0, bodyZ);
  const bodyMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 0.32, 24), new THREE.MeshLambertMaterial({ color: '#8ee5b1', emissive: '#1a5736', emissiveIntensity: 0.55 }));
  bodyMesh.position.y = 0.2;
  bodyMarker.add(bodyMesh);
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.36, 16), new THREE.MeshLambertMaterial({ color: '#d8ffe5' }));
  nose.rotation.z = -Math.PI / 2;
  nose.position.set(0.38, 0.22, 0);
  bodyMarker.add(nose);
  const yaw = Number(body.orientation) || 0;
  bodyMarker.rotation.y = yaw;
  const bodyLabel = labelSprite('BODY');
  bodyLabel.position.y = 0.85;
  bodyMarker.add(bodyLabel);
  while (bodyGroup.children.length) {
    const child = bodyGroup.children[bodyGroup.children.length - 1];
    bodyGroup.remove(child);
    child.traverse(node => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach(material => material.dispose());
      else { node.material?.map?.dispose(); node.material?.dispose(); }
    });
  }
  bodyGroup.add(bodyMarker);

  latestObjects = objects;
  const semanticByEntity = new Map(semanticGroups.map(group => [String(group.entity_id), group]));
  for (const item of latestObjects) {
    if (!Array.isArray(item.position)) continue;
    const px = (Number(item.position[0]) || 0) - basePosition[0];
    const pz = -((Number(item.position[1]) || 0) - basePosition[1]);
    const kind = String(item.kind || 'object').toLowerCase();
    const mesh = new THREE.Mesh(
      objectGeometry(item),
      new THREE.MeshLambertMaterial({ color: colorByKind[kind] || '#a9c4b2', emissive: colorByKind[kind] || '#a9c4b2', emissiveIntensity: kind.includes('mobile') ? 0.12 : 0.035 }),
    );
    mesh.position.set(px, kind.includes('obstacle') ? 0.58 : kind === 'table' || kind === 'chair' ? 0.38 : 0.25, pz);
    mesh.userData.entity = item;
    mesh.userData.semanticGroup = semanticByEntity.get(String(item.id)) || null;
    objectsGroup.add(mesh);
    selectable.push(mesh);
    const label = labelSprite(item.label || item.id || kind);
    label.position.set(px, 1.2, pz);
    objectsGroup.add(label);
  }
  const activeSplatIds = new Set();
  for (const group of semanticGroups) {
    const id = String(group.entity_id || '');
    if (!id) continue;
    activeSplatIds.add(id);
    let points = semanticSplatNodes.get(id);
    if (!points) {
      points = createGaussianPreview(group);
      semanticSplatNodes.set(id, points);
      semanticSplatGroup.add(points);
    } else {
      updateGaussianPreview(points, group);
    }
  }
  for (const [id, points] of semanticSplatNodes) {
    if (activeSplatIds.has(id)) continue;
    semanticSplatGroup.remove(points);
    points.geometry.dispose();
    points.material.dispose();
    semanticSplatNodes.delete(id);
  }
  updateSceneStatus(frame, perception, latestObjects, semanticGroups, semanticSplatScene);
  vrDashboard.update(frame);
}

function updateSceneStatus(frame, perception, objects, semanticGroups, semanticSplatScene) {
  const body = perception.body || {};
  const position = Array.isArray(body.position) ? body.position : [0, 0, 0];
  const yaw = Number(body.orientation) || 0;
  const modal = perception.modalities || {};
  const source = perception.source || 'Body perception';
  document.querySelector('#source').textContent = String(source).replaceAll('_', ' ').slice(0, 24);
  document.querySelector('#pose').textContent = `(${Number(position[0] || 0).toFixed(1)}, ${Number(position[1] || 0).toFixed(1)}) · ${Math.round(yaw * 180 / Math.PI)}°`;
  const age = Number(perception.age_seconds || 0);
  document.querySelector('#age').textContent = `${age.toFixed(1)} s`;
  const sensorCount = Object.values(modal).filter(value => value && (value.available || value.status === 'available')).length;
  if (firstData) {
    const semanticStatus = semanticGroups.length
      ? ` · ${semanticGroups.length} VLM Gaussian groups${semanticSplatScene.preview_only ? ' · SIM PREVIEW' : ''}` : '';
    setStatus(`${objects.length} perceived objects · ${sensorCount} sensor modalities reporting${semanticStatus} · WebXR can be entered from this page`);
    firstData = false;
  } else if (age > 5) {
    setStatus(`Body observation is stale (${age.toFixed(1)} s). Showing last known scene.`, true);
  } else {
    const semanticStatus = semanticGroups.length
      ? ` · ${semanticGroups.length} VLM Gaussian groups${semanticSplatScene.preview_only ? ' · SIM PREVIEW' : ''}` : '';
    setStatus(`${objects.length} perceived objects${semanticStatus} · frame ${new Date(Number(perception.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString()}`);
  }
}

async function pollBody() {
  try {
    const response = await fetch('/worldmodel/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Body status HTTP ${response.status}`);
    const frame = await response.json();
    latestWorldStatus = frame;
    syncSimulationControl(frame);
    if (activeSceneMode === 'sensors') {
      vrDashboard.update(frame);
      return;
    }
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

async function pollImuStatus() {
  if (imuPollInFlight) return;
  imuPollInFlight = true;
  try {
    const response = await fetch('/plugins/imu/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`IMU status HTTP ${response.status}`);
    vrDashboard.updateImuStatus(await response.json());
  } catch (error) {
    vrDashboard.updateImuStatus({ enabled: true, available: false, bridge_available: null, error: error.message });
  } finally { imuPollInFlight = false; }
}

let gpsPollInFlight = false;
async function pollGpsStatus() {
  if (gpsPollInFlight) return;
  gpsPollInFlight = true;
  try {
    const response = await fetch('/plugins/gps/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`GPS status HTTP ${response.status}`);
    vrDashboard.updateGpsStatus(await response.json());
  } catch (error) {
    vrDashboard.updateGpsStatus({ available: false, error: error.message });
  } finally { gpsPollInFlight = false; }
}

let powerStatusPollInFlight = false;
async function pollPowerStatus() {
  if (powerStatusPollInFlight) return;
  powerStatusPollInFlight = true;
  try {
    const response = await fetch('/body/power-mode', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Power status HTTP ${response.status}`);
    vrDashboard.updatePowerStatus(await response.json());
  } catch (error) {
    vrDashboard.updatePowerStatus({ mode: 'OFFLINE' });
  } finally {
    powerStatusPollInFlight = false;
  }
}

function syncSimulationControl(frame = latestWorldStatus) {
  const button = document.querySelector('#quest-simulation');
  if (!button) return;
  const available = frame?.mode === 'sim';
  button.disabled = !available || vrDashboard.actionBusy;
  button.textContent = !available ? 'Simulation unavailable' : frame.running ? 'Pause simulation' : 'Start simulation';
  button.setAttribute('aria-pressed', String(Boolean(frame?.running)));
}

async function refreshGaussianAssetStatus() {
  const button = document.querySelector('#scene-mode-gaussian');
  if (!button) return;
  try {
    const response = await fetch('/worldmodel/reconstruction/asset', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Asset status HTTP ${response.status}`);
    gaussianAssetStatus = await response.json();
    const ready = gaussianAssetStatus.available === true && gaussianAssetStatus.renderer_available === true;
    button.disabled = !ready;
    button.title = gaussianAssetStatus.message || (ready ? 'Switch to the reconstructed Gaussian scene' : 'Real 3DGS view is not ready');
    button.textContent = ready ? 'Real 3DGS view' : 'Real 3DGS view · unavailable';
  } catch (error) {
    gaussianAssetStatus = null;
    button.disabled = true;
    button.title = `Cannot check for a reconstructed scene: ${error.message}`;
    button.textContent = 'Real 3DGS view · unavailable';
  }
}

async function loadGaussianReconstruction() {
  if (gaussianViewer?.splatRenderReady) return gaussianViewer;
  if (gaussianLoadPromise) return gaussianLoadPromise;
  gaussianLoadPromise = (async () => {
    const host = document.createElement('div');
    host.setAttribute('aria-hidden', 'true');
    host.style.cssText = 'position:fixed;inset:0;opacity:0;pointer-events:none;z-index:-1';
    document.body.appendChild(host);
    const viewer = new GaussianSplats3D.Viewer({
      rootElement: host,
      threeScene: scene,
      renderer,
      camera,
      selfDrivenMode: false,
      useBuiltInControls: false,
      webXRMode: GaussianSplats3D.WebXRMode.VR,
      webXRSessionInit: { optionalFeatures: ['local-floor', 'bounded-floor'] },
      sharedMemoryForWorkers: false,
      gpuAcceleratedSort: false,
      integerBasedSort: true,
      renderMode: GaussianSplats3D.RenderMode.Always,
      sceneRevealMode: GaussianSplats3D.SceneRevealMode.Instant,
      sphericalHarmonicsDegree: 0,
      optimizeSplatData: true,
      inMemoryCompressionLevel: 1,
      freeIntermediateSplatData: true,
      logLevel: GaussianSplats3D.LogLevel.None,
    });
    gaussianViewer = viewer;
    const format = {
      ply: GaussianSplats3D.SceneFormat.Ply,
      splat: GaussianSplats3D.SceneFormat.Splat,
      ksplat: GaussianSplats3D.SceneFormat.KSplat,
    }[gaussianAssetStatus.format];
    await viewer.addSplatScene(gaussianAssetStatus.file_url, {
      format,
      progressiveLoad: true,
      showLoadingUI: false,
      position: gaussianAssetStatus.transform.position,
      rotation: gaussianAssetStatus.transform.rotation,
      scale: gaussianAssetStatus.transform.scale,
      splatAlphaRemovalThreshold: 1,
    });
    if (!viewer.splatRenderReady) throw new Error('Gaussian renderer did not finish preparing the asset');
    return viewer;
  })().catch(async error => {
    await gaussianViewer?.dispose().catch(() => {});
    gaussianViewer = null;
    throw error;
  }).finally(() => { gaussianLoadPromise = null; });
  return gaussianLoadPromise;
}

async function selectSceneMode(mode) {
  const planar = document.querySelector('#scene-mode-simulation');
  const sensors = document.querySelector('#scene-mode-sensors');
  const gaussian = document.querySelector('#scene-mode-gaussian');
  if (mode === 'sensors') {
    activeSceneMode = 'sensors';
    vrDashboard.setSceneMode('sensors');
    if (!sensorViewInitialized) {
      await refreshSensorMetricCalibration();
      const calibratedFarRange = Number(sensorMetricCalibration?.calibrated_range_m?.[1]);
      const frameRange = sensorMetricCalibration?.available && Number.isFinite(calibratedFarRange)
        ? Math.max(1.5, Math.min(5, calibratedFarRange + 0.5)) : 6.9;
      orbit.target.set(0, 0.55, -frameRange * 0.42);
      camera.position.set(0, 0.55 + frameRange * 0.42, frameRange * 1.05);
      camera.lookAt(orbit.target);
      orbit.update();
      sensorViewInitialized = true;
    }
    world.visible = true;
    floor.visible = false;
    sceneGrid.visible = false;
    roomLine.visible = false;
    bodyGroup.visible = false;
    objectsGroup.visible = false;
    semanticSplatGroup.visible = false;
    sensorSceneGroup.visible = true;
    sensorGround.visible = true;
    planar?.setAttribute('aria-pressed', 'false');
    sensors?.setAttribute('aria-pressed', 'true');
    gaussian?.setAttribute('aria-pressed', 'false');
    setStatus('Connecting live MiDaS, YOLOX and mmWave sensors…');
    void pollSensorScene();
    return;
  }
  if (mode === 'gaussian') {
    if (!gaussianAssetStatus?.available || !gaussianAssetStatus?.renderer_available) {
      setStatus(gaussianAssetStatus?.message || 'No renderable real 3DGS reconstruction is available yet.', true);
      return;
    }
    gaussian.disabled = true;
    gaussian.textContent = 'Loading real reconstruction…';
    setStatus(`Loading ${gaussianAssetStatus.asset_id} · ${(gaussianAssetStatus.byte_length / (1024 * 1024)).toFixed(1)} MiB`);
    try {
      await loadGaussianReconstruction();
      activeSceneMode = 'gaussian';
      vrDashboard.setSceneMode('simulation');
      world.visible = false;
      bodyGroup.visible = true;
      objectsGroup.visible = true;
      semanticSplatGroup.visible = true;
      sensorSceneGroup.visible = false;
      floor.visible = true;
      sceneGrid.visible = true;
      roomLine.visible = true;
      planar?.setAttribute('aria-pressed', 'false');
      sensors?.setAttribute('aria-pressed', 'false');
      gaussian?.setAttribute('aria-pressed', 'true');
      setStatus(`Real 3D Gaussian reconstruction · ${gaussianAssetStatus.coordinate_frame} · visualization only, not a safety map`);
    } catch (error) {
      activeSceneMode = 'simulation';
      vrDashboard.setSceneMode('simulation');
      world.visible = true;
      bodyGroup.visible = true;
      objectsGroup.visible = true;
      semanticSplatGroup.visible = true;
      sensorSceneGroup.visible = false;
      floor.visible = true;
      sceneGrid.visible = true;
      roomLine.visible = true;
      planar?.setAttribute('aria-pressed', 'true');
      sensors?.setAttribute('aria-pressed', 'false');
      gaussian?.setAttribute('aria-pressed', 'false');
      setStatus(`Could not load real reconstruction: ${error.message}`, true);
    } finally {
      gaussian.disabled = !(gaussianAssetStatus?.available && gaussianAssetStatus?.renderer_available);
      gaussian.textContent = 'Real 3DGS view';
    }
    return;
  }
  activeSceneMode = 'simulation';
  vrDashboard.setSceneMode('simulation');
  world.visible = true;
  bodyGroup.visible = true;
  objectsGroup.visible = true;
  semanticSplatGroup.visible = true;
  sensorSceneGroup.visible = false;
  floor.visible = true;
  sceneGrid.visible = true;
  roomLine.visible = true;
  planar?.setAttribute('aria-pressed', 'true');
  sensors?.setAttribute('aria-pressed', 'false');
  gaussian?.setAttribute('aria-pressed', 'false');
  setStatus('Planar Body world-model view selected.');
}

function selectAt(controller) {
  const hudAction = vrDashboard.visible ? vrDashboard.activateAt(controller, raycaster) : null;
  if (hudAction === 'simulation') {
    void toggleSimulationFromHud();
    return;
  }
  if (hudAction === 'sensor-mode') {
    void selectSceneMode(activeSceneMode === 'sensors' ? 'simulation' : 'sensors');
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
  const hitObject = hits[0].object;
  const item = hitObject.userData.entity;
  const semantic = hitObject.userData.semanticGroup;
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
  const semanticDetails = semantic
    ? `<br>VLM · ${escapeText(semantic.role || semantic.kind || 'described')} · ${Number.isFinite(Number(semantic.confidence)) ? `${Math.round(Number(semantic.confidence) * 100)}% confidence` : 'confidence unavailable'}${semantic.description ? `<br>${escapeText(semantic.description)}` : ''}`
    : '<br>No grounded VLM annotation for this object.';
  selectionNode.innerHTML = `<b>${escapeText(item.label || item.id || 'Perceived object')}</b><small>${escapeText(item.kind || 'object')} · ${position.slice(0, 2).map(v => Number(v).toFixed(2)).join(', ')} m · source ${escapeText(item.position_source || 'perception')}${semanticDetails}<br>Selection only; no actuator command sent.</small>`;
}

function updateControllerPointer(controller, beam, reticle) {
  controller.updateMatrixWorld(true);
  const rotation = controllerRayRotation.extractRotation(controller.matrixWorld);
  raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
  raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);

  const hudHit = vrDashboard.updatePointer(controller, raycaster);
  const sceneHit = hudHit ? null : raycaster.intersectObjects(selectable, false)[0];
  const hit = hudHit || sceneHit;
  const distance = hit ? hit.distance : 4;
  beam.scale.z = Math.max(0.05, distance / 4);
  reticle.visible = Boolean(sceneHit);
  if (sceneHit) {
    reticle.position.copy(sceneHit.point).addScaledVector(raycaster.ray.direction, -0.008);
    reticle.quaternion.setFromUnitVectors(controllerRayNormal, reticleDirection.copy(raycaster.ray.direction).negate());
  }
}

async function toggleSimulationFromHud() {
  if (latestWorldStatus?.mode !== 'sim') {
    setStatus('World Model simulation controls are unavailable in the current Body mode.', true);
    return;
  }
  if (vrDashboard.actionBusy) return;
  const running = latestWorldStatus.running === true;
  vrDashboard.setActionBusy(true);
  syncSimulationControl();
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
    setStatus(nowRunning ? 'World Model simulation running · left stick moves through the scene, right stick turns.' : 'World Model simulation paused · left stick moves through the scene, right stick turns.');
  } catch (error) {
    setStatus(`Simulation control failed: ${error.message}`, true);
  } finally {
    vrDashboard.setActionBusy(false);
    syncSimulationControl();
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
  if (!anchorCameraArcInScene()) return;
  cameraArc.visible = true;
  cameraBackgroundActive = true;
  vrDashboard.setCameraBackgroundActive(true);
  setStatus('Live camera arc anchored in the planar scene, 12 m out. It stays put as the Body turns; turn your head to look around it.');
}

function anchorCameraArcInScene() {
  const bodyPose = latestWorldStatus?.perception?.body;
  const position = bodyPose?.position;
  if (!Array.isArray(position) || !basePosition) {
    setStatus('Camera arc cannot be anchored: Body scene pose is unavailable.', true);
    return false;
  }
  cameraArcRoot.position.set(
    (Number(position[0]) || 0) - basePosition[0],
    0.75,
    -((Number(position[1]) || 0) - basePosition[1]),
  );
  cameraArcRoot.rotation.set(0, -Math.PI / 2 - (Number(bodyPose.orientation) || 0), 0);
  return true;
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
  const beam = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -4)]),
    new THREE.LineBasicMaterial({ color: '#d5ffea', transparent: true, opacity: 0.95, depthTest: false }),
  );
  beam.renderOrder = 2000;
  const reticle = new THREE.Mesh(
    new THREE.TorusGeometry(0.045, 0.009, 8, 32),
    new THREE.MeshBasicMaterial({ color: '#ffffff', depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
  );
  reticle.visible = false;
  reticle.renderOrder = 2001;
  controller.add(beam);
  scene.add(reticle);
  scene.add(controller);
  scene.add(grip);
  controllerRays.push({ controller, beam, reticle });
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
    renderer.xr.setFramebufferScaleFactor(xrRenderSettings.scale);
    renderer.xr.setFoveation(xrRenderSettings.foveation);
    await renderer.xr.setSession(session);
    orbit.enabled = false;
    vrDashboard.setVisible(mode === 'immersive-vr');
    if (mode === 'immersive-vr') startCameraPolling();
    document.querySelector('#enter-xr').textContent = mode === 'immersive-vr' ? 'Exit VR' : 'VR view';
    document.querySelector('#enter-ar').textContent = mode === 'immersive-ar' ? 'Exit passthrough' : 'Passthrough AR';
    setStatus(mode === 'immersive-ar'
      ? 'Passthrough is active. The Body map is an unaligned overlay; controller input is telemetry only.'
      : 'VR is active. Left stick moves through the scene; right stick turns. Hold either controller grip to reposition the HUD.');
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
      xrSceneOffset.set(0, 0, 0);
      xrSceneYawOffset = 0;
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
window.addEventListener('pagehide', () => vrDashboard.flushSavedPose());
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') vrDashboard.flushSavedPose();
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
document.querySelector('#quest-simulation').addEventListener('click', () => toggleSimulationFromHud());
document.querySelector('#scene-mode-simulation').addEventListener('click', () => selectSceneMode('simulation'));
document.querySelector('#scene-mode-sensors').addEventListener('click', () => selectSceneMode('sensors'));
document.querySelector('#scene-mode-gaussian').addEventListener('click', () => selectSceneMode('gaussian'));
void refreshGaussianAssetStatus();
setInterval(refreshGaussianAssetStatus, 10000);
void pollImuStatus();
setInterval(pollImuStatus, 1000);
void pollGpsStatus();
setInterval(pollGpsStatus, 1500);
void pollPowerStatus();
setInterval(pollPowerStatus, 5000);
window.__pbQuestReady = true;
if (statusNode.textContent === 'Starting 3D scene…') setStatus('3D renderer ready · connecting to Body world model…');

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
setInterval(pollSensorScene, 120);
setInterval(() => { if (activeSceneMode === 'sensors') void pollSensorYolo(); }, 220);
setInterval(() => { if (activeSceneMode === 'sensors') void pollSensorRadar(); }, 800);
setInterval(() => { if (activeSceneMode === 'sensors') void pollUltrasonicStatus(); }, 500);
void pollBody();
let previousFrameAt = 0;
renderer.setAnimationLoop(time => {
  perfTick(time);
  updateSensorPointUniforms();
  const deltaSeconds = previousFrameAt ? (time - previousFrameAt) / 1000 : 1 / 90;
  previousFrameAt = time;
  if (!renderer.xr.isPresenting) orbit.update();
  const session = renderer.xr.getSession();
  renderer.clear();
  if (session) {
    const xrCamera = renderer.xr.getCamera(camera);
    updateXRSceneFollow(xrCamera);
    const headYaw = new THREE.Euler().setFromQuaternion(xrCamera.quaternion, 'YXZ').y;
    const active = [...session.inputSources].filter(source => source.gamepad);
    if (!vrDashboard.grabbedController) updateXRLocomotion(active, xrCamera, deltaSeconds);
    vrDashboard.clearPointer();
    for (const ray of controllerRays) updateControllerPointer(ray.controller, ray.beam, ray.reticle);
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
  if (activeSceneMode === 'gaussian' && gaussianViewer?.splatRenderReady) {
    gaussianViewer.splatMesh.position.copy(world.position);
    gaussianViewer.splatMesh.quaternion.copy(world.quaternion);
    gaussianViewer.splatMesh.scale.copy(world.scale);
    gaussianViewer.splatMesh.updateMatrix();
    gaussianViewer.camera = session ? renderer.xr.getCamera(camera) : camera;
    gaussianViewer.update();
    gaussianViewer.render();
  } else {
    renderer.render(scene, camera);
  }
  if ((session || hudPreview) && vrDashboard.visible) {
    const xrCamera = session ? renderer.xr.getCamera(camera) : camera;
    vrDashboard.updateAdjustment(deltaSeconds, session ? [...session.inputSources].filter(source => source.gamepad) : []);
    vrDashboard.syncPose(xrCamera);
    vrDashboard.cachePose(xrCamera);
    vrDashboard.persistPose(xrCamera);
    renderer.clearDepth();
    renderer.render(vrDashboard.scene, camera);
  }
});
