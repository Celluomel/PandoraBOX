import { createFnk0031Visual } from './fnk0031_visual.js';
import { QuestGpsMap } from './quest_gps_map.js';

export class QuestVRDashboard {
  constructor(THREE, maxAnisotropy = 1) {
    this.THREE = THREE;
    this.scene = new THREE.Scene();
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.scene.add(new THREE.HemisphereLight('#e6f6f0', '#152224', 2.2));
    const modelLight = new THREE.DirectionalLight('#d5f8ea', 2.8);
    modelLight.position.set(-2, 4, 5);
    this.scene.add(modelLight);
    const edgeLight = new THREE.DirectionalLight('#86d9e8', 1.1);
    edgeLight.position.set(3, 2, -2);
    this.scene.add(edgeLight);
    this.panels = [];
    this.visible = false;
    this.headLocked = false;
    this.worldAnchored = false;
    this.anchorForward = new THREE.Vector3(0, 0, -1);
    this.hudTargetPosition = new THREE.Vector3();
    this.hudTargetQuaternion = new THREE.Quaternion();
    this.hudTowardVector = new THREE.Vector3();
    this.lastYoloUpdateAt = 0;
    this.yoloFrameId = '';
    this.yoloCapturedAt = 0;
    this.yoloState = 'waiting';
    this.yoloDetections = [];
    this.widthScale = 1;
    this.heightScale = 1;
    this.headOffsetPosition = new THREE.Vector3();
    this.headOffsetQuaternion = new THREE.Quaternion();
    this.lastPosePersistAt = 0;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.grabOffsetPosition = new THREE.Vector3();
    this.grabOffsetQuaternion = new THREE.Quaternion();
    this.scratchPosition = new THREE.Vector3();
    this.scratchQuaternion = new THREE.Quaternion();
    this.scratchOffset = new THREE.Vector3();
    this.headUp = new THREE.Vector3(0, 1, 0);
    this.facingMatrix = new THREE.Matrix4();
    this.grabForward = new THREE.Vector3(0, 0, -1);
    this.depthOffset = 0;
    this.cachedPose = null;
    this.frame = null;
    this.sceneMode = 'simulation';
    this.telemetry = null;
    this.imuStatus = null;
    this.gpsStatus = null;
    this.gpsMap = new QuestGpsMap(() => { this.drawDashboard(); this.drawGpsMapWindow(); });
    this.gpsMapVisible = false;
    this.gpsMapWorldAnchored = false;
    this.gpsMapPose = null;
    this.gpsMapHeadOffsetPosition = new THREE.Vector3();
    this.gpsMapHeadOffsetQuaternion = new THREE.Quaternion();
    this.gpsMapWidthScale = 1;
    this.gpsMapHeightScale = 1;
    this.gpsMapActionHitAreas = {};
    this.grabbedWindow = 'hud';
    this.hudBaseQuaternion = new THREE.Quaternion();
    this.gpsMapBaseQuaternion = new THREE.Quaternion();
    this.viewForward = new THREE.Vector3(0, 0, -1);
    this.panelRight = new THREE.Vector3(1, 0, 0);
    this.viewPitchQuaternion = new THREE.Quaternion();
    this.worldUp = new THREE.Vector3(0, 1, 0);
    this.verticalOffset = new THREE.Vector3();
    this.cameraFov = null;
    this.ultrasonicStatus = null;
    this.lastUltrasonicSamples = Object.create(null);
    this.sensorStatus = { camera: 'WAITING', yolo: 'WAITING', midas: 'WAITING' };
    this.controller = null;
    this.following = false;
    this.actionHitAreas = {};
    this.actionBusy = false;
    this.cameraBitmap = null;
    this.cameraMessage = 'CAMERA · WAITING';
    this.cameraBackgroundActive = false;
    this.cameraHitArea = null;

    const canvas = document.createElement('canvas');
    const renderScale = 4 / 3;
    canvas.width = 4096;
    canvas.height = 1536;
    this.canvas = canvas;
    this.context = canvas.getContext('2d');
    this.context.setTransform(renderScale, 0, 0, renderScale, 0, 0);
    this.logicalWidth = 3072;
    this.logicalHeight = 1152;
    this.loadSavedPose();
    this.texture = new THREE.CanvasTexture(canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.generateMipmaps = true;
    this.texture.minFilter = THREE.LinearMipmapLinearFilter;
    this.texture.magFilter = THREE.LinearFilter;
    this.texture.anisotropy = Math.min(8, Number(maxAnisotropy) || 1);
    const geometry = new THREE.PlaneGeometry(3.1, 1.1625, 1, 1);
    const panel = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    panel.position.set(0, 0, -0.9);
    this.panel = panel;
    panel.renderOrder = 1000;
    this.root.add(panel);
    this.panels.push(panel);
    this.robotVisual = createFnk0031Visual(THREE);
    this.robotVisual.group.position.set(-0.36, -0.04, -0.84);
    this.robotVisual.group.scale.setScalar(.24);
    this.robotVisual.group.renderOrder = 1001;
    this.robotVisual.group.traverse(object => {
      if (!object.isMesh) return;
      // The translucent HUD panel is in Three.js's transparent pass; keep the model in that pass after it.
      object.material.transparent = true;
      object.renderOrder = 1001;
    });
    this.root.add(this.robotVisual.group);
    this.applyHudSize();
    this.pointerRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.045, 0.009, 8, 32),
      new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.pointerRotation = new THREE.Matrix4();
    this.pointerNormal = new THREE.Vector3();
    this.pointerForward = new THREE.Vector3(0, 0, 1);
    this.pointerRing.visible = false;
    this.pointerRing.renderOrder = 2001;
    panel.add(this.pointerRing);

    this.gpsMapCanvas = document.createElement('canvas');
    this.gpsMapCanvas.width = 2048;
    this.gpsMapCanvas.height = 1460;
    this.gpsMapContext = this.gpsMapCanvas.getContext('2d');
    this.gpsMapTexture = new THREE.CanvasTexture(this.gpsMapCanvas);
    this.gpsMapTexture.colorSpace = THREE.SRGBColorSpace;
    this.gpsMapTexture.generateMipmaps = true;
    this.gpsMapTexture.minFilter = THREE.LinearMipmapLinearFilter;
    this.gpsMapTexture.magFilter = THREE.LinearFilter;
    this.gpsMapTexture.anisotropy = Math.min(8, Number(maxAnisotropy) || 1);
    this.gpsMapRoot = new THREE.Group();
    this.gpsMapRoot.visible = false;
    this.gpsMapPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.9, 1.35375),
      new THREE.MeshBasicMaterial({ map: this.gpsMapTexture, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.gpsMapPanel.renderOrder = 1100;
    this.gpsMapRoot.add(this.gpsMapPanel);
    this.scene.add(this.gpsMapRoot);
    this.panels.push(this.gpsMapPanel);
    this.loadSavedGpsMapPose();
    this.drawGpsMapWindow();
    this.drawDashboard();
  }

  update(frame) {
    this.frame = frame;
    this.drawDashboard();
  }

  updateTelemetry(telemetry) {
    this.telemetry = telemetry;
    this.drawDashboard();
  }

  updateImuStatus(status) {
    this.imuStatus = status || null;
    const sample = this.imuStatus?.sample || {};
    this.sensorStatus.imu = this.imuStatus?.available && sample.attitude_valid ? 'ATTITUDE OK' : 'NO FRESH SAMPLE';
    this.drawDashboard();
  }

  updateGpsStatus(status) {
    this.gpsStatus = status || null;
    const sample = this.gpsStatus?.sample || this.gpsStatus?.source_status?.sample || {};
    const inView = Number(sample.satellites_in_view);
    this.sensorStatus.gps = this.gpsStatus?.available
      ? `${sample.fix === true || Number(sample.fix_quality) > 0 ? 'FIX' : 'NO FIX'} · ${Number.isFinite(inView) ? `${inView} SV` : 'GSV —'}`
      : 'OFFLINE';
    this.drawDashboard();
    this.drawGpsMapWindow();
  }

  setGpsMapVisible(visible) {
    this.gpsMapVisible = Boolean(visible);
    this.gpsMapRoot.visible = this.visible && this.gpsMapVisible;
    this.drawDashboard();
    this.drawGpsMapWindow();
  }

  resetGpsMapPose() {
    this.gpsMapRoot.position.set(0, 0, 0);
    this.gpsMapRoot.quaternion.identity();
    this.gpsMapWorldAnchored = false;
    this.gpsMapWidthScale = 1;
    this.gpsMapHeightScale = 1;
    this.gpsMapHeadOffsetPosition.set(0, 0, 0);
    this.gpsMapHeadOffsetQuaternion.identity();
    this.gpsMapPose = null;
    this.applyGpsMapSize();
    try {
      localStorage.removeItem('pandorabox.quest-gps-map-pose.v2');
      localStorage.removeItem('pandorabox.quest-gps-map-pose.v1');
    } catch {}
  }

  resizeHud(factor) {
    const multiplier = Number(factor);
    if (!Number.isFinite(multiplier) || multiplier <= 0) return;
    this.widthScale = Math.max(0.45, Math.min(5, this.widthScale * multiplier));
    this.heightScale = Math.max(0.45, Math.min(5, this.heightScale * multiplier));
    this.applyHudSize();
    this.drawDashboard();
  }

  resizeGpsMap(factor) {
    const multiplier = Number(factor);
    if (!Number.isFinite(multiplier) || multiplier <= 0) return;
    this.gpsMapWidthScale = Math.max(0.45, Math.min(5, this.gpsMapWidthScale * multiplier));
    this.gpsMapHeightScale = Math.max(0.45, Math.min(5, this.gpsMapHeightScale * multiplier));
    this.applyGpsMapSize();
    this.drawGpsMapWindow();
  }

  drawGpsMapWindow() {
    if (!this.gpsMapContext) return;
    const ctx = this.gpsMapContext;
    const width = this.gpsMapCanvas.width;
    const height = this.gpsMapCanvas.height;
    const sample = this.gpsStatus?.sample || this.gpsStatus?.source_status?.sample || {};
    const latitude = Number(sample.latitude_deg ?? sample.latitude ?? sample.lat);
    const longitude = Number(sample.longitude_deg ?? sample.longitude ?? sample.lon ?? sample.lng);
    const validFix = (sample.fix === true || sample.valid === true || sample.status === 'fix' || Number(sample.fix_quality) > 0)
      && Number.isFinite(latitude) && Math.abs(latitude) <= 90
      && Number.isFinite(longitude) && Math.abs(longitude) <= 180;
    let fixTimestamp = Number(sample.timestamp ?? this.gpsStatus?.timestamp);
    if (fixTimestamp > 1e12) fixTimestamp /= 1000;
    const fixAge = Number.isFinite(fixTimestamp) ? Math.max(0, Date.now() / 1000 - fixTimestamp) : NaN;
    const currentFix = validFix && (!Number.isFinite(fixAge) || fixAge <= 5);
    const accuracy = Number(sample.horizontal_accuracy_m ?? sample.accuracy_m);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#071216'; ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = '#0e1a20'; ctx.fillRect(0, 0, width, 118);
    ctx.strokeStyle = 'rgba(126,209,193,.55)'; ctx.lineWidth = 3; ctx.strokeRect(2, 2, width - 4, height - 4);
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#d0eee4'; ctx.font = '700 31px system-ui'; ctx.fillText('GNSS position', 34, 43);
    ctx.fillStyle = validFix ? '#64e4be' : '#f0c26f'; ctx.font = '600 20px ui-monospace, monospace';
    const meta = validFix
      ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)} · ${sample.satellites ?? '—'} SV · ${Number.isFinite(accuracy) ? `±${accuracy.toFixed(1)} m` : 'accuracy —'}`
      : this.gpsStatus?.available ? 'UART LIVE · WAITING FOR VALID FIX' : 'NO VALID GNSS FIX';
    ctx.fillText(meta, 34, 83, 570);

    this.gpsMapActionHitAreas = {};
    const drawButton = (key, x, buttonWidth, label, selected = false) => {
      const y = 28, buttonHeight = 54;
      ctx.fillStyle = selected ? '#12382f' : '#101d22';
      ctx.strokeStyle = selected ? '#65dfbd' : '#40575d';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x, y, buttonWidth, buttonHeight, 10); ctx.fill(); ctx.stroke();
      ctx.fillStyle = selected ? '#b5f4dc' : '#c5d8d5';
      ctx.font = '650 19px ui-monospace, monospace'; ctx.textAlign = 'center';
      ctx.fillText(label, x + buttonWidth / 2, y + buttonHeight / 2, buttonWidth - 12);
      this.gpsMapActionHitAreas[key] = { x, y, width: buttonWidth, height: buttonHeight };
    };
    drawButton('gps-map-streets', 650, 132, 'Map', this.gpsMap.layer === 'streets');
    drawButton('gps-map-satellite', 790, 162, 'Satellite', this.gpsMap.layer === 'satellite');
    drawButton('gps-map-center', 960, 190, 'Center GPS');
    drawButton('gps-map-zoom-out', 1160, 70, '−');
    drawButton('gps-map-zoom-level', 1238, 112, `Z ${this.gpsMap.zoom}`);
    drawButton('gps-map-zoom-in', 1358, 70, '+');
    drawButton('gps-map-reset', 1436, 174, 'RESET WINDOW');
    drawButton('gps-map-close', 1618, 112, 'CLOSE');
    drawButton('gps-map-size-down', 1740, 116, 'SIZE −');
    drawButton('gps-map-size-up', 1864, 116, 'SIZE +');

    if (this.gpsMapVisible) {
      this.gpsMap.draw(ctx, {
        x: 28, y: 132, width: width - 56, height: height - 164,
        latitude: validFix ? latitude : NaN,
        longitude: validFix ? longitude : NaN,
        accuracyM: accuracy,
      });
      const fixText = currentFix
        ? `Fix valid · ${latitude.toFixed(6)}, ${longitude.toFixed(6)} · ${Number.isFinite(fixAge) ? `${fixAge.toFixed(1)} s old` : 'age unavailable'}`
        : validFix
          ? `No current fix · showing last valid position · ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
          : 'Waiting for a valid GPS fix';
      ctx.fillStyle = 'rgba(5,12,12,.9)'; ctx.fillRect(28, height - 27, width - 56, 25);
      ctx.fillStyle = currentFix ? '#75e2b4' : '#edc875'; ctx.font = '600 16px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText(fixText, 38, height - 10, 1110);
      ctx.fillStyle = '#d8e6df'; ctx.textAlign = 'right'; ctx.font = '14px system-ui';
      ctx.fillText(this.gpsMap.layer === 'satellite'
        ? 'Tiles © Esri · Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community'
        : '© OpenStreetMap contributors', width - 38, height - 10, 850);
    } else {
      ctx.fillStyle = '#0b151a'; ctx.fillRect(28, 132, width - 56, height - 164);
      ctx.fillStyle = '#9db6b4'; ctx.font = '600 22px ui-monospace, monospace'; ctx.textAlign = 'center';
      ctx.fillText('GPS MAP WINDOW CLOSED', width / 2, height / 2);
    }
    this.gpsMapTexture.needsUpdate = true;
  }

  loadSavedGpsMapPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-gps-map-pose.v2') || 'null');
      if (!Array.isArray(saved?.position) || saved.position.length !== 3
        || !Array.isArray(saved?.quaternion) || saved.quaternion.length !== 4) return;
      const values = [...saved.position, ...saved.quaternion, saved.widthScale, saved.heightScale].map(Number);
      if (!values.every(Number.isFinite) || values.slice(0, 3).some(value => Math.abs(value) > 20)) return;
      this.gpsMapHeadOffsetPosition.fromArray(saved.position);
      this.gpsMapHeadOffsetQuaternion.fromArray(saved.quaternion).normalize();
      this.gpsMapWidthScale = Math.max(.45, Math.min(5, Number(saved.widthScale) || 1));
      this.gpsMapHeightScale = Math.max(.45, Math.min(5, Number(saved.heightScale) || 1));
      this.gpsMapPose = saved;
      this.applyGpsMapSize();
    } catch {}
  }

  applyGpsMapSize() {
    this.gpsMapPanel?.scale.set(this.gpsMapWidthScale, this.gpsMapHeightScale, 1);
  }

  persistGpsMapPose(xrCamera, force = false) {
    if (!xrCamera || !this.gpsMapWorldAnchored || (!force && performance.now() - this.lastGpsMapPosePersistAt < 750)) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.gpsMapHeadOffsetPosition.copy(this.gpsMapRoot.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.gpsMapHeadOffsetQuaternion.copy(inverseHead).multiply(this.gpsMapRoot.quaternion).normalize();
    this.gpsMapPose = {
      position: this.gpsMapHeadOffsetPosition.toArray(),
      quaternion: this.gpsMapHeadOffsetQuaternion.toArray(),
      widthScale: this.gpsMapWidthScale,
      heightScale: this.gpsMapHeightScale,
    };
    try {
      localStorage.setItem('pandorabox.quest-gps-map-pose.v2', JSON.stringify(this.gpsMapPose));
      this.lastGpsMapPosePersistAt = performance.now();
    } catch {}
  }

  updatePowerStatus(status) {
    const previous = this.sensorStatus.power;
    const mode = String(status?.mode || 'UNKNOWN').toUpperCase();
    const estimate = status?.battery_estimate || {};
    const level = Number(estimate.level_percent_est);
    const remainingWh = Number(estimate.remaining_wh_est);
    const modeMean = Number(status?.rolling_60s_mean_w_by_mode?.[mode]?.mean_w);
    const watts = modeMean > 0 ? modeMean : Number(status?.board_input_w);
    this.sensorStatus.power = Number.isFinite(level) ? `${mode} · ~${Math.round(level)}%` : mode;
    this.sensorStatus.runtime = Number.isFinite(remainingWh) && watts > 0
      ? `${Math.floor(remainingWh / watts)}H ${Math.floor((remainingWh / watts % 1) * 60)}M EST.` : '—';
    if (previous !== this.sensorStatus.power) this.drawDashboard();
  }

  updateDepthIntrinsics(intrinsics, width, height) {
    const fx = Number(intrinsics?.fx);
    const fy = Number(intrinsics?.fy);
    const imageWidth = Number(width);
    const imageHeight = Number(height);
    if (!(fx > 0 && fy > 0 && imageWidth > 0 && imageHeight > 0)) return;
    const cameraFov = {
      horizontalDeg: 2 * Math.atan(imageWidth / (2 * fx)) * 180 / Math.PI,
      verticalDeg: 2 * Math.atan(imageHeight / (2 * fy)) * 180 / Math.PI,
      calibrated: Boolean(intrinsics.calibrated),
    };
    if (this.cameraFov
      && Math.abs(this.cameraFov.horizontalDeg - cameraFov.horizontalDeg) < 0.05
      && Math.abs(this.cameraFov.verticalDeg - cameraFov.verticalDeg) < 0.05
      && this.cameraFov.calibrated === cameraFov.calibrated) return;
    this.cameraFov = cameraFov;
    this.drawDashboard();
  }

  updateUltrasonicStatus(status) {
    this.ultrasonicStatus = status || null;
    this.drawDashboard();
  }

  updateYoloResult(result) {
    const detections = Array.isArray(result?.detections) ? result.detections : [];
    const updatedAt = Date.now();
    this.yoloState = String(result?.state || 'unknown').toLowerCase();
    const frameId = String(result?.frame_id || result?.captured_at || '');
    let changed = false;
    if (detections.length && frameId !== this.yoloFrameId) {
      this.yoloDetections = detections.slice(0, 12);
      this.yoloFrameId = frameId;
      this.yoloCapturedAt = Number(result.captured_at) || 0;
      this.lastYoloUpdateAt = updatedAt;
      changed = true;
    } else if (updatedAt - this.lastYoloUpdateAt > 5000) {
      changed = this.yoloDetections.length > 0;
      this.yoloDetections = [];
    }
    if (changed) this.drawDashboard();
  }

  updateSensorStatus(status) {
    this.sensorStatus = { ...this.sensorStatus, ...status };
    this.drawDashboard();
  }

  updateController(controller) {
    this.controller = controller;
    this.robotVisual.setTelemetry(controller || {});
    this.drawDashboard();
  }

  setFollowing(following) {
    if (this.following === Boolean(following)) return;
    this.following = Boolean(following);
    this.drawDashboard();
  }

  drawPanel(ctx, x, y, width, height, title, meta = '') {
    const radius = 38;
    ctx.fillStyle = 'rgba(13, 23, 29, .88)';
    ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); ctx.fill();
    ctx.strokeStyle = 'rgba(126, 209, 193, .48)';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(x + 1, y + 1, width - 2, height - 2, radius - 1); ctx.stroke();
    ctx.fillStyle = '#d0eee4';
    ctx.font = '700 30px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(title.toUpperCase(), x + 24, y + 29);
    ctx.fillStyle = '#64e4be';
    ctx.fillRect(x + 14, y + 15, 5, 26);
    if (meta) {
      ctx.fillStyle = '#83a594';
      ctx.font = '600 22px ui-monospace, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(meta, x + width - 22, y + 29);
    }
    ctx.strokeStyle = 'rgba(135, 206, 166, .22)';
    ctx.beginPath();
    ctx.moveTo(x + 22, y + 56);
    ctx.lineTo(x + width - 22, y + 56);
    ctx.stroke();
  }

  drawDashboard() {
    const ctx = this.context;
    const width = this.logicalWidth;
    const height = this.logicalHeight;
    ctx.clearRect(0, 0, width, height);
    const frameInset = 5;
    const frameRadius = 58;
    ctx.beginPath();
    ctx.roundRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2, frameRadius);
    ctx.fillStyle = 'rgba(7, 18, 22, .87)';
    ctx.fill();
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2, frameRadius);
    ctx.clip();
    ctx.fillStyle = 'rgba(7, 18, 22, .87)';
    ctx.fillRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2);
    ctx.strokeStyle = '#80dfc6';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.roundRect(frameInset + 2, frameInset + 2, width - (frameInset + 2) * 2, height - (frameInset + 2) * 2, frameRadius - 2);
    ctx.stroke();

    const perception = this.frame?.perception || {};
    const fnk = this.controller || {};
    const xr = this.telemetry || {};
    const top = 24;
    const bottom = height - 68;
    const panelHeight = bottom - top;
    const margin = 30;
    const gap = 20;
    const cameraWidth = 720;
    const bodyWidth = 900;
    const sensorWidth = 660;
    const coverageWidth = width - 2 * margin - 3 * gap - cameraWidth - bodyWidth - sensorWidth;
    const cameraX = margin;
    const bodyX = cameraX + cameraWidth + gap;
    const sensorX = bodyX + bodyWidth + gap;
    const coverageX = sensorX + sensorWidth + gap;
    this.drawCamera(ctx, cameraX, top, cameraWidth, panelHeight);
    this.drawBodyPanel(ctx, bodyX, top, bodyWidth, panelHeight, perception, fnk, xr);
    this.drawSensorPanel(ctx, sensorX, top, sensorWidth, panelHeight, perception);
    this.drawCoveragePanel(ctx, coverageX, top, coverageWidth, panelHeight, perception);
    this.drawHudActions(ctx);
    ctx.fillStyle = this.grabbedController ? '#f0cd79' : '#91b6a0';
    ctx.font = '600 21px ui-monospace, monospace';
    ctx.textAlign = 'left';
    ctx.fillText(this.grabbedController
      ? 'HUD GRABBED · GRAB STICK ↑↓ DEPTH / ←→ WIDTH · OTHER STICK ↑↓ HEIGHT · MOVE HAND TO REPOSITION'
      : 'HOLD GRIP TO EDIT · MOVE HAND TO POSITION · GRAB STICK: DEPTH + WIDTH · OTHER STICK: HEIGHT', margin + 8, height - 28);
    ctx.textAlign = 'right';
    ctx.fillText(this.following ? 'CAMERA FOLLOW · BODY' : 'SCENE VIEW · FIXED', width - margin - 8, height - 28);
    ctx.restore();
    this.texture.needsUpdate = true;
  }

  drawHudActions(ctx) {
    const buttonY = this.logicalHeight - 62;
    const simulationReady = this.frame?.mode === 'sim';
    const simulationRunning = Boolean(this.frame?.running);
    const simulationLabel = simulationRunning ? 'PAUSE SIMULATION' : 'START SIMULATION';
    const mapX = this.logicalWidth / 2 - 568;
    const simulationX = this.logicalWidth / 2 - 300;
    const sensorX = this.logicalWidth / 2 + 24;
    const exitX = this.logicalWidth / 2 + 340;
    const drawButton = (key, x, width, label, fill, stroke, textColor, enabled = true) => {
      const height = 48;
      this.actionHitAreas[key] = { x: x - 16, y: buttonY - 12, width: width + 32, height: height + 24, enabled: enabled && !this.actionBusy };
      ctx.globalAlpha = enabled ? 1 : 0.42;
      ctx.fillStyle = fill;
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x, buttonY, width, height, 18); ctx.fill(); ctx.stroke();
      ctx.fillStyle = textColor;
      ctx.font = '700 22px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, x + width / 2, buttonY + height / 2);
      ctx.globalAlpha = 1;
    };
    drawButton('hud-size-down', this.logicalWidth / 2 - 856, 132, 'HUD SIZE −', 'rgba(28, 48, 47, .96)', '#78d8d0', '#e5fffa');
    drawButton('hud-size-up', this.logicalWidth / 2 - 716, 132, 'HUD SIZE +', 'rgba(28, 48, 47, .96)', '#78d8d0', '#e5fffa');
    drawButton('gps-map', mapX, 204, this.gpsMapVisible ? 'CLOSE GPS MAP' : 'GPS MAP', 'rgba(31, 73, 77, .96)', '#78d8d0', '#e5fffa');
    drawButton('simulation', simulationX, 300, this.actionBusy ? 'PLEASE WAIT' : simulationReady ? simulationLabel : 'SIMULATION OFFLINE', 'rgba(31, 105, 78, .96)', '#75edbd', '#e5fff3', simulationReady);
    drawButton('sensor-mode', sensorX, 300, this.sceneMode === 'sensors' ? 'SHOW SIMULATION' : 'SHOW LIVE SENSORS', 'rgba(31, 73, 77, .96)', '#78d8d0', '#e5fffa');
    drawButton('exit', exitX, 220, this.actionBusy ? 'PLEASE WAIT' : 'EXIT VR', 'rgba(91, 53, 42, .96)', '#f0a888', '#fff0e8');
  }

  drawTopTelemetry(ctx, perception, fnk, xr) {
    const x = 28;
    const y = 24;
    const width = this.logicalWidth - 56;
    const height = 136;
    this.drawPanel(ctx, x, y, width, height, 'LIVE CONTROLLER TELEMETRY', 'QUEST INPUT + FNK0031');
    const entries = [
      ['HEAD', xr.headingDegrees == null ? '—' : `${xr.headingDegrees}°`],
      ['LEFT CONTROLLER', this.controllerText(xr.controllers, 'left')],
      ['RIGHT CONTROLLER', this.controllerText(xr.controllers, 'right')],
      ['FNK GAIT', fnk.gait || (fnk.active ? 'active' : 'waiting')],
      ['CPG PHASE', Number.isFinite(Number(fnk.cpg_phase)) ? `${Math.round(Number(fnk.cpg_phase) * 180 / Math.PI)}°` : '—'],
      ['ACTIVE SPIKES', `${(fnk.spikes || []).filter(Boolean).length} / 18`],
      ['FNK HEADING', Number.isFinite(Number(fnk.compass_heading_deg ?? fnk.body_heading_deg)) ? `${Math.round(Number(fnk.compass_heading_deg ?? fnk.body_heading_deg))}°` : '—'],
      ['CTRL STEPS', fnk.step == null ? '—' : String(fnk.step)],
    ];
    const cellWidth = width / entries.length;
    entries.forEach(([label, value], index) => {
      const cellX = x + index * cellWidth;
      if (index) {
        ctx.strokeStyle = 'rgba(135, 206, 166, .19)';
        ctx.beginPath(); ctx.moveTo(cellX, y + 69); ctx.lineTo(cellX, y + height - 12); ctx.stroke();
      }
      ctx.textAlign = 'left';
      ctx.fillStyle = '#839e8d';
      ctx.font = '600 19px ui-monospace, monospace';
      ctx.fillText(label, cellX + 18, y + 83);
      ctx.fillStyle = index < 3 ? '#e2f4e9' : '#b9ebcd';
      ctx.font = '700 28px ui-monospace, monospace';
      ctx.fillText(String(value).slice(0, 17), cellX + 18, y + 115);
    });
  }

  controllerText(controllers = [], hand) {
    const controller = controllers.find(item => item.handedness === hand);
    return controller ? `${Number(controller.x || 0).toFixed(1)}, ${Number(controller.y || 0).toFixed(1)}${controller.pressed ? ' · BTN' : ''}` : 'not detected';
  }

  drawCamera(ctx, x, y, width, height) {
    this.drawPanel(ctx, x, y, width, height, 'Camera · egocentric', this.cameraBackgroundActive ? 'BACKGROUND ON' : this.cameraBitmap ? 'LIVE' : 'BODY CAMERA');
    const imageX = x + 18;
    const imageWidth = width - 36;
    const imageHeight = Math.min(height - 228, imageWidth * .78);
    const imageY = y + 72 + Math.max(0, (height - 92 - imageHeight) / 2);
    this.cameraHitArea = { x: imageX, y: imageY, width: imageWidth, height: imageHeight };
    ctx.fillStyle = '#0b1512';
    ctx.beginPath(); ctx.roundRect(imageX, imageY, imageWidth, imageHeight, 20); ctx.fill();
    if (this.cameraBitmap && !this.cameraBackgroundActive) {
      const scale = Math.max(imageWidth / this.cameraBitmap.width, imageHeight / this.cameraBitmap.height);
      const drawWidth = this.cameraBitmap.width * scale;
      const drawHeight = this.cameraBitmap.height * scale;
      ctx.save();
      ctx.beginPath(); ctx.roundRect(imageX, imageY, imageWidth, imageHeight, 20); ctx.clip();
      ctx.drawImage(this.cameraBitmap, imageX + (imageWidth - drawWidth) / 2, imageY + (imageHeight - drawHeight) / 2, drawWidth, drawHeight);
      ctx.restore();
      this.drawYoloOverlay(ctx, imageX, imageY, imageWidth, imageHeight, scale,
        imageX + (imageWidth - drawWidth) / 2, imageY + (imageHeight - drawHeight) / 2);
      ctx.fillStyle = 'rgba(4, 13, 11, .78)';
      ctx.beginPath(); ctx.roundRect(imageX + 16, imageY + imageHeight - 48, 390, 34, 12); ctx.fill();
      ctx.fillStyle = '#d9f5e4'; ctx.font = '700 19px ui-monospace, monospace';
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText(this.cameraBackgroundActive ? 'TRIGGER · RESTORE 3D VIEW' : 'TRIGGER · USE AS 3D BACKGROUND', imageX + 28, imageY + imageHeight - 31);
    } else if (this.cameraBackgroundActive) {
      ctx.fillStyle = 'rgba(4, 13, 11, .72)';
      ctx.beginPath(); ctx.roundRect(imageX + 16, imageY + 16, imageWidth - 32, imageHeight - 32, 18); ctx.fill();
      ctx.fillStyle = '#d9f5e4'; ctx.font = '700 24px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('CAMERA · SCENE BACKGROUND', imageX + imageWidth / 2, imageY + imageHeight / 2 - 14);
      ctx.fillStyle = '#a9c3b2'; ctx.font = '600 21px ui-monospace, monospace';
      ctx.fillText('TRIGGER TO RESTORE 3D VIEW', imageX + imageWidth / 2, imageY + imageHeight / 2 + 24);
    } else {
      ctx.fillStyle = '#bbd6c5';
      ctx.font = '700 27px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this.cameraMessage, imageX + imageWidth / 2, imageY + imageHeight / 2);
    }
    this.drawDetectionSummary(ctx, x + 18, imageY + imageHeight + 18, imageWidth, y + height - 18);
  }

  detectionColor(label) {
    const key = String(label || '').toLowerCase();
    if (key === 'person') return '#63e6a8';
    if (['tv', 'tvmonitor', 'monitor'].includes(key)) return '#f0c26f';
    if (['chair', 'couch', 'bed'].includes(key)) return '#b99aff';
    if (['car', 'bicycle', 'motorcycle', 'bus', 'truck'].includes(key)) return '#6bd4ed';
    return '#70e0cf';
  }

  drawYoloOverlay(ctx, imageX, imageY, imageWidth, imageHeight, scale, offsetX, offsetY) {
    const age = this.yoloCapturedAt && this.cameraCapturedAt ? Math.abs(this.yoloCapturedAt - this.cameraCapturedAt) : Infinity;
    const frameMatches = this.yoloFrameId && this.cameraFrameId && this.yoloFrameId === this.cameraFrameId;
    const timeMatches = Number.isFinite(age) && age <= 0.2;
    const paired = this.yoloState === 'ready' && (frameMatches || timeMatches);
    if (!this.yoloDetections.length || (!paired && Date.now() - this.lastYoloUpdateAt > 5000)) return;
    const labels = [];
    this.yoloDetections.forEach((detection, index) => {
      const box = detection.bbox;
      if (!Array.isArray(box) || box.length !== 4 || !box.every(value => Number.isFinite(Number(value)))) return;
      const [x1, y1, x2, y2] = box.map(value => Math.max(0, Math.min(1, Number(value))));
      if (x2 <= x1 || y2 <= y1) return;
      const left = offsetX + x1 * this.cameraBitmap.width * scale;
      const top = offsetY + y1 * this.cameraBitmap.height * scale;
      const right = offsetX + x2 * this.cameraBitmap.width * scale;
      const bottom = offsetY + y2 * this.cameraBitmap.height * scale;
      const color = this.detectionColor(detection.label || detection.class_name);
      const clippedLeft = Math.max(imageX, left);
      const clippedTop = Math.max(imageY, top);
      const clippedRight = Math.min(imageX + imageWidth, right);
      const clippedBottom = Math.min(imageY + imageHeight, bottom);
      if (clippedRight <= clippedLeft || clippedBottom <= clippedTop) return;
      ctx.save();
      ctx.globalAlpha = paired ? 0.96 : 0.56;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(3, imageWidth / 360);
      ctx.strokeRect(clippedLeft, clippedTop, clippedRight - clippedLeft, clippedBottom - clippedTop);
      ctx.font = '700 18px ui-monospace, monospace';
      const label = `${paired ? '' : 'LAST SEEN · '}${detection.label || detection.class_name || 'object'} ${Math.round(Number(detection.confidence || detection.score || 0) * 100)}%`;
      const labelWidth = ctx.measureText(label).width + 14;
      const labelY = Math.max(imageY + 20, top - 6 - labels.filter(item => Math.abs(item.x - left) < labelWidth && Math.abs(item.y - top) < 28).length * 26);
      labels.push({ x: left, y: labelY });
      ctx.fillStyle = color;
      ctx.fillRect(Math.max(imageX, left), labelY - 22, Math.min(labelWidth, imageX + imageWidth - Math.max(imageX, left)), 24);
      ctx.fillStyle = '#07120e';
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText(label, Math.max(imageX, left) + 7, labelY - 10, imageWidth - 14);
      ctx.restore();
    });
  }

  drawDetectionSummary(ctx, x, y, width, bottom) {
    const rows = this.yoloDetections.slice(0, 3);
    const top = y;
    const cardGap = 10;
    const cardWidth = (width - cardGap * 2) / 3;
    const cardHeight = Math.min(94, Math.max(58, bottom - top));
    rows.forEach((detection, index) => {
      const cardX = x + index * (cardWidth + cardGap);
      const label = String(detection.label || detection.class_name || 'object');
      ctx.fillStyle = 'rgba(7,18,22,.88)';
      ctx.strokeStyle = this.detectionColor(label);
      ctx.beginPath(); ctx.roundRect(cardX, top, cardWidth, cardHeight, 10); ctx.fill(); ctx.stroke();
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = this.detectionColor(label);
      ctx.font = '700 20px ui-monospace, monospace';
      ctx.fillText(label.toUpperCase(), cardX + 12, top + 24, cardWidth - 24);
      ctx.fillStyle = '#d3e2dc'; ctx.font = '600 17px ui-monospace, monospace';
      ctx.fillText(`${Math.round(Number(detection.confidence || detection.score || 0) * 100)}%${Date.now() - this.lastYoloUpdateAt > 250 ? ' · LAST SEEN' : ' · LIVE'}`, cardX + 12, top + 54, cardWidth - 24);
    });
    if (!rows.length) {
      ctx.fillStyle = '#9db8a7'; ctx.font = '600 18px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText('YOLOX · WAITING FOR DETECTIONS', x + 8, top + 26, width - 16);
    }
  }

  drawBodyPanel(ctx, x, y, width, height, perception, fnk, xr) {
    const position = perception.body?.position || [];
    const heading = Number(perception.body?.orientation || 0) * 180 / Math.PI;
    const objects = perception.objects || [];
    this.drawPanel(ctx, x, y, width, height, 'Body telemetry', `${objects.length} OBJECTS`);
    ctx.strokeStyle = 'rgba(113, 209, 194, .24)';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(x + 267, y + 620, 270, 72, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(x + 267, y + 620, 205, 52, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#a5bdba'; ctx.font = '600 20px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText('FNK0031 · ESTIMATED 3D MODEL', x + 56, y + 718);
    ctx.fillStyle = '#6bdac1'; ctx.fillRect(x + 56, y + 729, 100, 3);
    const headingDeg = Number(fnk.compass_heading_deg ?? fnk.body_heading_deg ?? heading);
    const headingX = x + width * .75;
    const headingY = y + 245;
    ctx.strokeStyle = 'rgba(169,232,194,.52)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(headingX, headingY, 47, 0, Math.PI * 2); ctx.stroke();
    ctx.save(); ctx.translate(headingX, headingY); ctx.rotate(-headingDeg * Math.PI / 180);
    ctx.fillStyle = '#59e0bc'; ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(-12, 13); ctx.lineTo(0, 7); ctx.lineTo(12, 13); ctx.closePath(); ctx.fill(); ctx.restore();
    ctx.fillStyle = '#829d8d'; ctx.font = '600 19px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText('HEADING', headingX + 70, headingY - 18);
    ctx.fillStyle = '#e4f4ea'; ctx.font = '600 42px system-ui';
    ctx.fillText(Number.isFinite(headingDeg) ? `${Math.round(headingDeg)}°` : '—', headingX + 70, headingY + 28);
    const velocity = perception.body?.velocity_mps ?? perception.motion?.velocity_mps ?? perception.modalities?.odometry?.velocity_mps;
    const speed = Array.isArray(velocity) ? Math.hypot(...velocity.map(Number)) : Number(velocity);
    ctx.fillStyle = '#829d8d'; ctx.font = '600 19px ui-monospace, monospace'; ctx.fillText('BODY SPEED', headingX + 8, headingY + 112);
    ctx.fillStyle = '#e4f4ea'; ctx.font = '600 32px system-ui';
    ctx.fillText(Number.isFinite(speed) ? `${speed.toFixed(2)} m/s` : '— m/s', headingX + 8, headingY + 153);
    this.drawNavigationInstruments(ctx, x, y, width, headingX, perception, fnk, headingDeg, speed);
    const spikes = (fnk.spikes || []).filter(Boolean).length;
    const servoTargets = fnk.servo_targets || [];
    const bars = [['SERVO TARGETS', `${servoTargets.length}/18`, servoTargets.length / 18], ['SNN ACTIVE', `${spikes}/18`, spikes / 18]];
    bars.forEach(([label, value, ratio], index) => {
      const rowY = y + height - 210 + index * 66;
      ctx.fillStyle = 'rgba(8,20,17,.78)'; ctx.strokeStyle = 'rgba(135,206,166,.32)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.roundRect(x + 28, rowY, width - 56, 52, 12); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#a5ddba'; ctx.font = '600 18px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.fillText(label, x + 50, rowY + 31);
      const bx = x + 265; const bw = width - 390;
      ctx.fillStyle = '#243a32'; ctx.fillRect(bx, rowY + 21, bw, 11);
      ctx.fillStyle = '#58e3ba'; ctx.fillRect(bx, rowY + 21, bw * Math.max(0, Math.min(1, ratio)), 11);
      ctx.fillStyle = '#dff4e6'; ctx.textAlign = 'right'; ctx.font = '700 20px ui-monospace, monospace'; ctx.fillText(value, x + width - 42, rowY + 32);
    });
    const left = this.controllerText(xr.controllers, 'left');
    const right = this.controllerText(xr.controllers, 'right');
    ctx.fillStyle = '#a8c3b1'; ctx.textAlign = 'left'; ctx.font = '600 18px ui-monospace, monospace';
    ctx.fillText(`GAIT ${fnk.gait || 'waiting'}   ·   CPG ${Number.isFinite(Number(fnk.cpg_phase)) ? `${Math.round(Number(fnk.cpg_phase) * 180 / Math.PI)}°` : '—'}   ·   STEP ${fnk.step ?? '—'}`, x + 32, y + height - 38);
    ctx.textAlign = 'right'; ctx.fillText(`L ${left}   R ${right}`, x + width - 28, y + height - 38);
  }

  drawNavigationInstruments(ctx, x, y, width, headingX, perception, fnk, fallbackHeading, speed) {
    const modalities = perception.modalities || {};
    const unwrap = value => value?.data && typeof value.data === 'object' ? value.data : value || {};
    const imuSourceData = this.imuStatus?.enabled
      ? (this.imuStatus.available ? this.imuStatus.sample : {})
      : (modalities.imu || fnk.imu || {});
    const imu = unwrap(imuSourceData);
    const gps = unwrap(this.gpsStatus?.sample || this.gpsStatus?.source_status?.sample || modalities.gps || modalities.gnss || perception.body?.geo || fnk.gps);
    const asNumber = value => value === null || value === undefined || value === '' ? NaN : Number(value);
    const angleDeg = (value, unit) => {
      const n = asNumber(value);
      if (!Number.isFinite(n)) return NaN;
      return /rad/i.test(String(unit || '')) ? n * 180 / Math.PI : n;
    };
    const imuUnit = imu.angle_unit || imu.unit || (imuSourceData === fnk.imu ? 'rad' : '');
    const pitch = angleDeg(imu.pitch_deg ?? imu.pitch_rad ?? imu.pitch, imu.pitch_deg !== undefined ? 'deg' : imuUnit);
    const roll = angleDeg(imu.roll_deg ?? imu.roll_rad ?? imu.roll, imu.roll_deg !== undefined ? 'deg' : imuUnit);
    const hasAttitude = Number.isFinite(pitch) && Number.isFinite(roll);
    const yawRate = asNumber(imu.yaw_rate_dps ?? imu.angular_velocity_dps?.[2]);
    const gpsLat = asNumber(gps.latitude_deg ?? gps.latitude ?? gps.lat);
    const gpsLon = asNumber(gps.longitude_deg ?? gps.longitude ?? gps.lon ?? gps.lng);
    const fixQuality = asNumber(gps.fix_quality ?? gps.fixQuality);
    const explicitFix = gps.fix === true || gps.valid === true || gps.status === 'fix' || gps.status === 'valid';
    const hasGps = Number.isFinite(gpsLat) && Math.abs(gpsLat) <= 90 && Number.isFinite(gpsLon) && Math.abs(gpsLon) <= 180
      && (explicitFix || (Number.isFinite(fixQuality) && fixQuality > 0));
    const gpsAccuracy = asNumber(gps.horizontal_accuracy_m ?? gps.accuracy_m);
    const gpsHdop = asNumber(gps.hdop);
    const satelliteSignals = Array.isArray(gps.satellite_signals) ? gps.satellite_signals : [];
    const imuSource = String(imu.source || modalities.imu?.source || 'IMU').toUpperCase();
    const imuUnavailable = this.imuStatus?.error?.includes('404') ? 'BODY UPDATE REQUIRED'
      : !this.imuStatus?.enabled ? 'WAITING FOR ATTITUDE'
        : this.imuStatus.bridge_available === false ? 'NO LOCAL ARDUINO BRIDGE'
        : this.imuStatus.error ? 'BRIDGE / SENSOR UNAVAILABLE' : 'WAITING FOR IMU SAMPLE';
    const centerX = x + width * .84;
    const centerY = y + 565;
    const radius = 82;
    const heading = Number.isFinite(asNumber(fnk.magnetic_heading_deg)) ? asNumber(fnk.magnetic_heading_deg)
      : Number.isFinite(asNumber(fnk.compass_heading_deg)) ? asNumber(fnk.compass_heading_deg)
        : Number.isFinite(asNumber(gps.course_deg)) && Number(speed) > .4 ? asNumber(gps.course_deg) : 90 - fallbackHeading;
    const headingSource = Number.isFinite(asNumber(fnk.magnetic_heading_deg)) ? 'MAG'
      : Number.isFinite(asNumber(fnk.compass_heading_deg)) ? (fnk.heading_source || 'ODOM').toString().toUpperCase()
        : Number.isFinite(asNumber(gps.course_deg)) && Number(speed) > .4 ? 'GPS COG' : 'EST';

    ctx.fillStyle = '#a5bdba'; ctx.font = '600 19px ui-monospace, monospace'; ctx.textAlign = 'center';
    ctx.fillText('ATTITUDE · 3D HORIZON + AZIMUTH', centerX, centerY - radius - 48);
    ctx.save();
    ctx.beginPath(); ctx.arc(centerX, centerY, radius, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = '#173b43'; ctx.fillRect(centerX - radius, centerY - radius, radius * 2, radius);
    ctx.fillStyle = '#665743'; ctx.fillRect(centerX - radius, centerY, radius * 2, radius);
    ctx.translate(centerX, centerY);
    if (hasAttitude) ctx.rotate(-roll * Math.PI / 180);
    const horizonOffset = hasAttitude ? Math.max(-radius * .72, Math.min(radius * .72, pitch * 1.7)) : 0;
    ctx.translate(0, horizonOffset);
    ctx.strokeStyle = '#d7eee6'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-radius * .82, 0); ctx.lineTo(radius * .82, 0); ctx.stroke();
    for (const degrees of [-30, -20, -10, 10, 20, 30]) {
      const lineY = degrees * 1.7;
      const half = degrees % 20 === 0 ? 25 : 15;
      ctx.beginPath(); ctx.moveTo(-half, lineY); ctx.lineTo(half, lineY); ctx.stroke();
    }
    ctx.restore();
    ctx.strokeStyle = '#a9e8c2'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(centerX, centerY, radius, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = '#e8f7ee'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(centerX - 25, centerY); ctx.lineTo(centerX - 9, centerY); ctx.lineTo(centerX, centerY + 7); ctx.lineTo(centerX + 9, centerY); ctx.lineTo(centerX + 25, centerY); ctx.stroke();
    this.drawAzimuthRing(ctx, centerX, centerY, radius + 18, heading);
    ctx.fillStyle = hasAttitude ? '#e4f4ea' : '#f0cd79'; ctx.font = '18px ui-monospace, monospace';
    ctx.textAlign = 'center';
    ctx.fillText(hasAttitude ? `${imuSource} · R ${roll.toFixed(1)}° · P ${pitch.toFixed(1)}°` : `IMU · ${imuUnavailable}`, centerX, centerY + radius + 23);
    ctx.fillText(`HDG ${Number.isFinite(heading) ? `${Math.round((heading % 360 + 360) % 360)}°` : '—'} · ${headingSource}`, centerX, centerY + radius + 47);
    ctx.fillStyle = Number.isFinite(yawRate) ? '#9ec8b5' : '#829d8d'; ctx.font = '16px ui-monospace, monospace';
    ctx.fillText(Number.isFinite(yawRate) ? `YAW RATE ${yawRate.toFixed(1)}°/s · NO MAGNETOMETER` : 'YAW RATE · NO IMU DATA', centerX, centerY + radius + 69);

    const gpsX = centerX;
    const gpsY = y + 742;
    ctx.textAlign = 'center'; ctx.fillStyle = '#a5bdba'; ctx.font = '600 18px ui-monospace, monospace';
    ctx.fillText('GPS POSITION', gpsX, gpsY);
    ctx.fillStyle = hasGps ? '#59e0bc' : '#f0cd79'; ctx.font = '17px ui-monospace, monospace';
    ctx.fillText(hasGps ? `${gpsLat.toFixed(6)}°, ${gpsLon.toFixed(6)}°` : 'NO VALID FIX', gpsX, gpsY + 28);
    ctx.fillStyle = '#829d8d'; ctx.font = '16px ui-monospace, monospace';
    const satelliteCount = asNumber(gps.satellites);
    const gpsStreamOnline = Boolean(this.gpsStatus?.available || gps.connected || Number(this.gpsStatus?.source_status?.diagnostic?.bytes_received) > 0);
    ctx.fillText(hasGps ? `FIX${Number.isFinite(gpsAccuracy) ? ` · ±${gpsAccuracy.toFixed(1)} m` : Number.isFinite(gpsHdop) ? ` · HDOP ${gpsHdop.toFixed(1)}` : ''}` : gpsStreamOnline ? 'UART LIVE · WAITING FOR FIX' : 'NO GPS DATA · CHECK D0/D1', gpsX, gpsY + 51);
    const inView = asNumber(gps.satellites_in_view);
    ctx.fillText(`${Number.isFinite(satelliteCount) ? `${satelliteCount} USED` : 'USED —'} · ${Number.isFinite(inView) ? `${inView} IN VIEW` : 'VIEW —'}`, gpsX, gpsY + 74);
    const plottedSignals = satelliteSignals.slice(0, 10);
    if (plottedSignals.length) {
      const barWidth = 13;
      const gap = 7;
      const chartWidth = plottedSignals.length * (barWidth + gap) - gap;
      const startX = gpsX - chartWidth / 2;
      const baselineY = gpsY + 126;
      ctx.strokeStyle = 'rgba(169,232,194,.28)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(startX - 5, baselineY); ctx.lineTo(startX + chartWidth + 5, baselineY); ctx.stroke();
      plottedSignals.forEach((satellite, index) => {
        const cn0 = asNumber(satellite.cn0_db_hz);
        const barHeight = Number.isFinite(cn0) ? Math.max(2, Math.min(35, cn0 * .58)) : 2;
        ctx.fillStyle = cn0 >= 35 ? '#69d49c' : cn0 >= 25 ? '#efcb76' : '#e88775';
        const bx = startX + index * (barWidth + gap);
        ctx.fillRect(bx, baselineY - barHeight, barWidth, barHeight);
        ctx.fillStyle = '#dcebe2'; ctx.font = '10px ui-monospace, monospace'; ctx.textAlign = 'center';
        ctx.fillText(Number.isFinite(cn0) ? `${Math.round(cn0)}` : '—', bx + barWidth / 2, baselineY - barHeight - 3);
        ctx.fillStyle = '#829d8d'; ctx.font = '9px ui-monospace, monospace';
        ctx.fillText(String(satellite.svid).slice(-3), bx + barWidth / 2, baselineY + 12);
      });
    } else {
      ctx.fillStyle = '#829d8d'; ctx.font = '14px ui-monospace, monospace';
      ctx.fillText('WAITING FOR GSV SIGNAL DATA', gpsX, gpsY + 112);
    }
  }

  drawAzimuthRing(ctx, cx, cy, radius, heading) {
    ctx.strokeStyle = 'rgba(169,232,194,.55)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke();
    ctx.save(); ctx.translate(cx, cy);
    for (let bearing = 0; bearing < 360; bearing += 15) {
      const angle = (-90 + bearing - (Number(heading) || 0)) * Math.PI / 180;
      const major = bearing % 45 === 0;
      const inner = radius - (major ? 13 : 7);
      ctx.strokeStyle = major ? '#a9e8c2' : 'rgba(169,232,194,.55)'; ctx.lineWidth = major ? 2 : 1;
      ctx.beginPath(); ctx.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner); ctx.lineTo(Math.cos(angle) * (radius - 2), Math.sin(angle) * (radius - 2)); ctx.stroke();
      if (bearing % 90 === 0) {
        ctx.fillStyle = '#e4f4ea'; ctx.font = '700 20px ui-monospace, monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(['N', 'E', 'S', 'W'][bearing / 90], Math.cos(angle) * (radius - 23), Math.sin(angle) * (radius - 23));
      }
    }
    ctx.restore();
    const indexY = cy - radius;
    ctx.fillStyle = '#59e0bc'; ctx.beginPath(); ctx.moveTo(cx, indexY - 7); ctx.lineTo(cx - 7, indexY + 5); ctx.lineTo(cx, indexY + 2); ctx.lineTo(cx + 7, indexY + 5); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#e8f7ee'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cx - 10, indexY - 11); ctx.lineTo(cx + 10, indexY - 11); ctx.moveTo(cx, indexY - 16); ctx.lineTo(cx, indexY - 6); ctx.stroke();
  }

  drawHexapod(ctx, cx, cy, heading, fnk, scale = 1) {
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(Math.PI / 2 - heading * Math.PI / 180); ctx.scale(scale, scale);
    ctx.lineCap = 'round';
    const visualToPhysical = [0, 2, 4, 1, 3, 5];
    const jointColors = ['#83cbd1', '#9ce0b4', '#efcb76'];
    const servoTargets = new Map((fnk.servo_targets || []).map(target => [Number(target.index), Number(target.target)]));
    const jointsByPhysicalLeg = fnk.joint_targets || [];
    visualToPhysical.forEach((physicalLeg, index) => {
      const side = index < 3 ? -1 : 1;
      const row = index % 3;
      const longitudinal = row - 1;
      const hipX = side * 35;
      const hipY = longitudinal * 52;
      const jointValues = jointsByPhysicalLeg[physicalLeg] || [];
      const valueAt = joint => {
        const fallback = servoTargets.get(index * 3 + joint + 1) ?? 0;
        const value = Number(jointValues[joint] ?? fallback);
        return Number.isFinite(value) ? Math.max(-1, Math.min(1, value)) : 0;
      };
      const [coxa, femur, tibia] = [0, 1, 2].map(valueAt);
      const lift = Number(fnk.foot_lift?.[physicalLeg] || 0);
      const points = [
        [hipX + side * (24 + coxa * 5), hipY + coxa * 5],
        [hipX + side * (59 + coxa * 5 + femur * 5), hipY + longitudinal * (12 + femur * 5)],
        [hipX + side * (94 + coxa * 5 + femur * 5 + tibia * 5), hipY + longitudinal * (25 + femur * 5 + tibia * 7) - Math.max(0, lift) * 12],
      ];
      const legColor = Number(fnk.contact?.[physicalLeg]) === 1 ? '#76d5a0' : '#efcb76';
      const chain = [[hipX, hipY], ...points];
      chain.slice(1).forEach((point, joint) => {
        ctx.strokeStyle = joint === 2 ? legColor : '#91ad9c';
        ctx.lineWidth = joint === 2 ? 8 : 10;
        ctx.beginPath(); ctx.moveTo(...chain[joint]); ctx.lineTo(...point); ctx.stroke();
        ctx.fillStyle = jointColors[joint];
        ctx.beginPath(); ctx.arc(point[0], point[1], 7, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#07110d'; ctx.lineWidth = 2; ctx.stroke();
        const servoId = String(index * 3 + joint + 1).padStart(2, '0');
        ctx.fillStyle = jointColors[joint]; ctx.font = '12px ui-monospace, monospace';
        ctx.textAlign = side < 0 ? 'right' : 'left';
        ctx.fillText(servoId, point[0] + side * 10, point[1] - 9);
      });
      const foot = points[2];
      ctx.fillStyle = legColor; ctx.beginPath(); ctx.arc(foot[0], foot[1], 5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#dcebe2'; ctx.font = '13px ui-monospace, monospace';
      ctx.textAlign = side < 0 ? 'right' : 'left';
      ctx.fillText(`L${index + 1}`, foot[0] + side * 17, foot[1] + 5);
    });
    ctx.fillStyle = '#18352a'; ctx.strokeStyle = '#a0e5ba'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.roundRect(-40, -70, 80, 140, 24); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#dff5e7'; ctx.font = '600 15px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('FNK0031', 0, 0);
    ctx.fillStyle = '#f0ca76'; ctx.beginPath(); ctx.moveTo(0, -82); ctx.lineTo(-10, -62); ctx.lineTo(10, -62); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#829d8d'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'center';
    ctx.fillText('FRONT', cx, cy - 120);
    ctx.fillStyle = '#9db8a7'; ctx.font = '13px ui-monospace, monospace';
    ctx.fillText('18 SERVO JOINTS · COXA / FEMUR / TIBIA', cx, cy + 150);
  }

  drawSensorPanel(ctx, x, y, width, height, perception) {
    const live = this.sceneMode === 'sensors';
    this.drawPanel(ctx, x, y, width, height, 'Egocentric sensors', live ? 'LIVE BODY SENSORS' : 'SIMULATION · VIRTUAL RANGES');
    const lidar = perception.sensor_projections?.lidar?.points || [];
    const radar = perception.modalities?.mmwave_radar?.targets || [];
    const tof = perception.modalities?.tof || {};
    const inset = 20;
    const gap = 14;
    const mapWidth = width - inset * 2;
    const tofHeight = 124;
    const modalities = { ...(perception.modalities || {}) };
    if (this.sceneMode === 'sensors' && this.ultrasonicStatus) modalities.ultrasonic = this.ultrasonicStatus.sample || {};
    const ultrasonic = modalities.ultrasonic || {};
    const radarSample = modalities.mmwave_radar || {};
    const radarAge = Number(radarSample.age_ms);
    const tofAge = Number(tof.age_ms);
    const statusFor = sample => sample?.available === true
      ? `${Number(sample.distance_m ?? Number(sample.distance_mm) / 1000).toFixed(2)} M · ${Number(sample.age_ms || 0) > 750 ? 'STALE' : 'LIVE'}`
      : sample?.error || 'NO DATA';
    this.sensorStatus.radar = radarSample.available || (radarSample.targets || []).length
      ? `${(radarSample.targets || []).length} TARGETS · ${Number.isFinite(radarAge) ? `${(radarAge / 1000).toFixed(1)}S` : 'LIVE'}` : 'NO TARGET';
    this.sensorStatus.tof = tof.available ? `${Number(tof.distance_m).toFixed(2)} M · ${Number.isFinite(tofAge) ? `${(tofAge / 1000).toFixed(1)}S` : 'LIVE'}` : tof.error || 'NO DATA';
    this.sensorStatus.ultrasonicFrontLeft = statusFor(ultrasonic.front_left || {});
    this.sensorStatus.ultrasonicFrontRight = statusFor(ultrasonic.front_right || {});
    this.sensorStatus.ultrasonicRear = statusFor(ultrasonic.rear || {});
    this.drawSensorStatusStrip(ctx, x + inset, y + 67, mapWidth, live);
    const mapHeight = (height - 172 - tofHeight - gap * 2) / 2;
    const mapY = y + 142;
    const tofY = mapY + mapHeight * 2 + gap * 2;
    ctx.strokeStyle = 'rgba(135, 206, 166, .22)';
    ctx.beginPath(); ctx.roundRect(x + inset, mapY, mapWidth, mapHeight, 20); ctx.stroke();
    ctx.beginPath(); ctx.roundRect(x + inset, mapY + mapHeight + gap, mapWidth, mapHeight, 20); ctx.stroke();
    ctx.beginPath(); ctx.roundRect(x + inset, tofY, mapWidth, tofHeight, 18); ctx.stroke();
    this.drawMetricMap(ctx, x + inset, mapY, mapWidth, mapHeight, lidar, radar, perception, 'LiDAR', 'lidar');
    this.drawMetricMap(ctx, x + inset, mapY + mapHeight + gap, mapWidth, mapHeight, lidar, radar, perception, 'mmWave', 'radar');
    this.drawRangeSensorStrip(ctx, x + inset + 12, tofY + 12, mapWidth - 24, tofHeight - 24, tof, modalities);
  }

  drawCoveragePanel(ctx, x, y, width, height, perception) {
    const live = this.sceneMode === 'sensors';
    this.drawPanel(ctx, x, y, width, height, 'Coverage · field of view', live ? 'LIVE RETURNS · ANGLES CONFIGURABLE' : 'SENSOR CONFIGURATION');
    const plotWidth = Math.min(300, width * 0.47);
    const plotX = x + 18;
    const plotY = y + 82;
    const plotHeight = Math.min(height - 210, 620);
    const cx = plotX + plotWidth / 2;
    const cy = plotY + plotHeight * 0.48;
    const radius = Math.min(plotWidth * 0.43, plotHeight * 0.39);
    const scale = radius / 6;
    const colors = { radar: '#f0c26f', camera: '#68d8ed', tof: '#65e2c2', left: '#a7df78', right: '#6bd4d0', rear: '#ba9cff' };
    const anglePoint = (bearing, distance) => {
      const angle = (bearing - 90) * Math.PI / 180;
      return { x: cx + Math.cos(angle) * distance, y: cy + Math.sin(angle) * distance };
    };
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = 'rgba(40,55,49,.2)'; ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
    ctx.strokeStyle = 'rgba(120,151,137,.12)'; ctx.lineWidth = 1;
    for (let offset = -radius * 2; offset <= radius * 2; offset += 12) {
      ctx.beginPath(); ctx.moveTo(cx - radius, cy + offset); ctx.lineTo(cx + radius, cy + offset + radius * 2); ctx.stroke();
    }
    ctx.restore();
    const drawSector = (bearing, halfAngle, range, color, dashed = false, alpha = 0.15) => {
      const start = (bearing - halfAngle - 90) * Math.PI / 180;
      const end = (bearing + halfAngle - 90) * Math.PI / 180;
      const reach = Math.min(radius, range * scale);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, reach, start, end); ctx.closePath();
      ctx.fillStyle = color; ctx.globalAlpha = alpha; ctx.fill(); ctx.globalAlpha = 1;
      ctx.strokeStyle = color; ctx.lineWidth = dashed ? 2 : 1.5; ctx.setLineDash(dashed ? [6, 5] : []); ctx.stroke(); ctx.setLineDash([]);
    };
    drawSector(0, 60, 6, colors.radar, false, 0.12);
    const cameraHalfFov = (this.cameraFov?.horizontalDeg || 70) / 2;
    drawSector(0, cameraHalfFov, 5.5, colors.camera, true, 0.08);
    drawSector(0, 7, 4, colors.tof, false, 0.3);
    drawSector(-25, 15, 4, colors.left, false, 0.2);
    drawSector(25, 15, 4, colors.right, false, 0.2);
    drawSector(180, 15, 4, colors.rear, false, 0.2);
    for (let meters = 1; meters <= 6; meters += 1) {
      ctx.beginPath(); ctx.arc(cx, cy, meters * scale, 0, Math.PI * 2);
      ctx.strokeStyle = meters === 6 ? 'rgba(240,194,111,.48)' : 'rgba(151,177,166,.22)'; ctx.lineWidth = 1; ctx.stroke();
      if (meters % 2 === 0 || meters === 1) {
        ctx.fillStyle = '#9cb2aa'; ctx.font = '13px ui-monospace, monospace'; ctx.textAlign = 'center';
        ctx.fillText(`${meters}`, cx + 12, cy - meters * scale + 16);
      }
    }
    for (let bearing = 0; bearing < 360; bearing += 30) {
      const point = anglePoint(bearing, radius);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(point.x, point.y); ctx.strokeStyle = 'rgba(151,177,166,.14)'; ctx.stroke();
    }
    const robot = anglePoint(0, 0);
    ctx.fillStyle = '#e7f1ec'; ctx.beginPath(); ctx.moveTo(robot.x, robot.y - 12); ctx.lineTo(robot.x - 9, robot.y + 10); ctx.lineTo(robot.x + 9, robot.y + 10); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#dce9e4'; ctx.font = '600 14px ui-monospace, monospace'; ctx.textAlign = 'center';
    ctx.fillText('FRONT', cx, cy - radius - 20); ctx.fillText('REAR', cx, cy + radius + 28);
    ctx.textAlign = 'left'; ctx.fillText('LEFT', cx - radius - 30, cy + 5); ctx.textAlign = 'right'; ctx.fillText('RIGHT', cx + radius + 30, cy + 5);

    const radar = perception.modalities?.mmwave_radar || {};
    const frame = perception.sensor_projections?.frame || {};
    const bodyPosition = frame.body || perception.body?.position || [0, 0, 0];
    const yaw = Number(frame.yaw_rad ?? perception.body?.orientation ?? 0);
    const isLd2450 = /^hlk_ld2450/i.test(String(radar.source || ''));
    for (const target of Array.isArray(radar.targets) ? radar.targets : []) {
      const p = target.position_m || target.position || [];
      const radarPosition = isLd2450 ? [Number(p[1]), -Number(p[0]), Number(p[2] || 0)] : p;
      const local = this.sensorLocal(radarPosition, radar.frame || 'body', bodyPosition, yaw);
      if (!local || local.forward < 0 || local.distance > 6) continue;
      const marker = anglePoint(Math.atan2(-local.left, local.forward) * 180 / Math.PI, local.distance * scale);
      ctx.fillStyle = colors.radar; ctx.beginPath(); ctx.arc(marker.x, marker.y, 7, 0, Math.PI * 2); ctx.fill();
    }
    const tof = perception.modalities?.tof || {};
    const tofDistance = Number(tof.distance_m);
    if (tof.available === true && Number.isFinite(tofDistance) && tofDistance > 0 && tofDistance <= 4) {
      const marker = anglePoint(0, tofDistance * scale); ctx.fillStyle = colors.tof; ctx.beginPath(); ctx.arc(marker.x, marker.y, 6, 0, Math.PI * 2); ctx.fill();
    }
    const ultrasonic = this.ultrasonicStatus?.sample || perception.modalities?.ultrasonic || {};
    [['front_left', -25, colors.left], ['front_right', 25, colors.right], ['rear', 180, colors.rear]].forEach(([key, bearing, color]) => {
      const sample = ultrasonic[key] || {};
      const distance = Number(sample.distance_m ?? Number(sample.distance_mm) / 1000);
      if (sample.available !== true || !Number.isFinite(distance) || distance <= 0 || distance > 4) return;
      const marker = anglePoint(bearing, distance * scale); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(marker.x, marker.y, 6, 0, Math.PI * 2); ctx.fill();
    });

    const coverageLegend = [
      ['RADAR', colors.radar], ['CAMERA', colors.camera], ['ToF', colors.tof], ['HC-SR04 ×3', colors.left],
    ];
    coverageLegend.forEach(([label, color], index) => {
      const slotWidth = width / coverageLegend.length;
      const lx = x + 18 + index * slotWidth;
      const ly = y + height - 58;
      ctx.fillStyle = color; ctx.fillRect(lx, ly - 7, 12, 12);
      ctx.fillStyle = '#c6d6d0'; ctx.font = '600 12px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText(label, lx + 18, ly, slotWidth - 24);
    });

    const textX = x + plotWidth + 32;
    const textWidth = x + width - 24 - textX;
    const titleY = y + 92;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#92aaa2'; ctx.font = '600 14px ui-monospace, monospace';
    ctx.fillText('DISPLAY TIER', textX, titleY); ctx.fillText('FIELD', textX + 100, titleY); ctx.fillText('USE', textX + 198, titleY);
    ctx.strokeStyle = 'rgba(135,206,166,.22)'; ctx.beginPath(); ctx.moveTo(textX, titleY + 18); ctx.lineTo(textX + textWidth, titleY + 18); ctx.stroke();
    const rows = [
      ['Primary', '36° × 27°', 'camera, detections'],
      ['Secondary', '24° × 18°', 'lists, tables'],
      ['Tertiary', '16° × 12°', 'status, pose'],
      ['Body text', '≥ 1.2°', '≈ 2.5 cm min.'],
    ];
    rows.forEach((row, index) => {
      const rowY = titleY + 43 + index * 38;
      ctx.fillStyle = '#d3e2dc'; ctx.font = '15px ui-monospace, monospace'; ctx.fillText(row[0], textX, rowY);
      ctx.fillStyle = '#c6d6d0'; ctx.fillText(row[1], textX + 100, rowY);
      ctx.fillStyle = '#aebfba'; ctx.font = '13px ui-monospace, monospace'; ctx.fillText(row[2], textX + 198, rowY, Math.max(40, textWidth - 198));
      ctx.strokeStyle = 'rgba(135,206,166,.14)'; ctx.beginPath(); ctx.moveTo(textX, rowY + 17); ctx.lineTo(textX + textWidth, rowY + 17); ctx.stroke();
    });
    const cameraFovText = this.cameraFov
      ? `CAMERA ${this.cameraFov.calibrated ? 'INTRINSICS' : 'NOMINAL'} · H ${this.cameraFov.horizontalDeg.toFixed(1)}° · V ${this.cameraFov.verticalDeg.toFixed(1)}°`
      : 'CAMERA FOV · NOMINAL 70° · AWAITING DEPTH INTRINSICS';
    ctx.fillStyle = this.cameraFov?.calibrated ? colors.camera : '#f0c26f';
    ctx.font = '600 12px ui-monospace, monospace';
    ctx.fillText(cameraFovText, textX, titleY + 194, textWidth);
    ctx.fillStyle = '#829d8d'; ctx.font = '12px ui-monospace, monospace';
    ctx.fillText('1.2 M REFERENCE · TUNE MINIMUM TEXT HEIGHT ON DEVICE', textX, titleY + 213, textWidth);
    const bulletY = titleY + 246;
    const lines = [
      ['CAMERA WINDOW', this.cameraFov?.calibrated ? 'Dashed frustum uses depth-frame camera intrinsics; cloud is clipped to that view.' : 'Dashed frustum is nominal until camera intrinsics are supplied; cloud remains camera-framed.'],
      ['SENSOR-ALIGNED', 'Front sensors point forward; rear ultrasonic is behind the robot. Close-behind cues should be haptic or audio.'],
      ['BLIND SECTORS', 'Hatching means no coverage. Radar is not a 360° sensor.'],
      ['INTERACTION', 'Primary within ±30°, secondary within ±60°; keep wrist edges nonessential.'],
      ['DEPTH HONESTY', 'MiDaS remains relative until its radar calibration is validated.'],
    ];
    const wrap = (text, maxWidth, font) => {
      ctx.font = font; const words = text.split(' '); const result = []; let line = '';
      for (const word of words) { const candidate = line ? `${line} ${word}` : word; if (line && ctx.measureText(candidate).width > maxWidth) { result.push(line); line = word; } else line = candidate; }
      if (line) result.push(line); return result;
    };
    let lineY = bulletY;
    for (const [label, detail] of lines) {
      ctx.fillStyle = '#65e2c2'; ctx.font = '700 13px ui-monospace, monospace'; ctx.fillText(`• ${label}`, textX, lineY);
      lineY += 21;
      const detailLines = wrap(detail, textWidth - 12, '14px system-ui');
      ctx.fillStyle = '#b5c7c0'; ctx.font = '14px system-ui';
      detailLines.forEach(line => { ctx.fillText(line, textX + 12, lineY, textWidth - 14); lineY += 19; });
      lineY += 8;
    }
    const legendY = Math.min(y + height - 96, lineY + 8);
    const legend = [['VALID', '#60e0bd'], ['NO ECHO · CLEAR', '#8dbdff'], ['TOO CLOSE', '#ff8278'], ['STALE', '#f0c26f'], ['OFFLINE', '#91a79b']];
    legend.forEach(([label, color], index) => {
      const column = index % 2; const row = Math.floor(index / 2);
      const lx = textX + column * (textWidth / 2); const ly = legendY + row * 27;
      ctx.fillStyle = color; ctx.beginPath(); ctx.arc(lx + 5, ly, 5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#bdccc7'; ctx.font = '12px ui-monospace, monospace'; ctx.fillText(label, lx + 17, ly, textWidth / 2 - 20);
    });
    ctx.fillStyle = '#829d8d'; ctx.font = '12px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText('ANGLES / MOUNT OFFSETS ARE CONFIGURABLE ASSUMPTIONS', x + 22, y + height - 28, width - 44);
  }

  drawSensorStatusStrip(ctx, x, y, width, live) {
    const items = live ? [
      ['CAMERA', this.sensorStatus.camera || this.cameraMessage],
      ['YOLOX', this.sensorStatus.yolo || 'WAITING'],
      ['MiDaS', this.sensorStatus.midas || 'WAITING'],
      ['RADAR', this.sensorStatus.radar || 'WAITING'],
      ['ToF', this.sensorStatus.tof || 'WAITING'],
      ['US FRONT-L', this.sensorStatus.ultrasonicFrontLeft || 'WAITING'],
      ['US FRONT-R', this.sensorStatus.ultrasonicFrontRight || 'WAITING'],
      ['US REAR', this.sensorStatus.ultrasonicRear || 'WAITING'],
      ['GPS', this.sensorStatus.gps || 'WAITING'],
      ['IMU', this.sensorStatus.imu || 'WAITING'],
      ['POWER · EST.', this.sensorStatus.power || 'WAITING'],
      ['RUNTIME · EST.', this.sensorStatus.runtime || '—'],
    ] : [['SOURCE', 'SIMULATION'], ['RANGE', 'VIRTUAL'], ['GPS', 'SIM'], ['IMU', 'SIM'], ['LIVE INPUTS', 'NOT SHOWN']];
    const gap = 6;
    const columns = 6;
    const itemWidth = (width - gap * (columns - 1)) / columns;
    items.forEach(([label, value], index) => {
      const row = Math.floor(index / columns);
      const column = index % columns;
      const bx = x + column * (itemWidth + gap);
      const by = y + row * 34;
      const state = String(value);
      const ok = !/WAIT|NO FIX|OFFLINE|ERROR|FAIL|UNAVAILABLE|INVALID/i.test(state)
        && /LIVE|OK|FIX|READY|HTP|CPU|OBJECTS|MS/i.test(state);
      ctx.fillStyle = 'rgba(8,20,17,.78)';
      ctx.strokeStyle = ok ? 'rgba(99,215,174,.36)' : 'rgba(135,154,143,.28)';
      ctx.beginPath(); ctx.roundRect(bx, by, itemWidth, 30, 7); ctx.fill(); ctx.stroke();
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#9fc5ac'; ctx.font = '600 11px ui-monospace, monospace';
      ctx.fillText(label, bx + 8, by + 10);
      ctx.fillStyle = ok ? '#bcebd0' : '#efcb76'; ctx.font = '600 12px ui-monospace, monospace';
      ctx.fillText(state.slice(0, 22), bx + 8, by + 22, itemWidth - 16);
    });
  }

  drawRangeSensorStrip(ctx, x, y, width, height, tof, modalities) {
    const tofWidth = 48;
    this.drawTofRangeBar(ctx, x, y, tofWidth, height, tof);
    const ultrasonic = modalities.ultrasonic || modalities.hc_sr04 || {};
    const samples = Array.isArray(ultrasonic) ? ultrasonic : Array.isArray(ultrasonic.sensors) ? ultrasonic.sensors : [];
    const positions = ['front_left', 'front_right', 'rear'];
    const now = Date.now();
    const names = ['US · FRONT-L', 'US · FRONT-R', 'US · REAR'];
    const gap = 10;
    const cardWidth = (width - tofWidth - gap * 3) / 3;
    positions.forEach((key, index) => {
      const currentSample = ultrasonic[key] || samples.find(item => String(item?.id || item?.position || '').toLowerCase() === key) || samples[index] || {};
      const currentDistance = Number(currentSample.distance_m ?? (Number(currentSample.distance_mm) / 1000));
      const currentValid = currentSample.available === true && !currentSample.simulated
        && Number.isFinite(currentDistance) && currentDistance > 0 && currentDistance <= 4;
      if (currentValid) {
        this.lastUltrasonicSamples[key] = { sample: currentSample, measurementAt: now - (Number(currentSample.age_ms) || 0) };
      }
      const retained = this.lastUltrasonicSamples[key];
      const retainedAge = retained ? now - retained.measurementAt : Infinity;
      const held = !currentValid && retainedAge <= 3000;
      const sample = currentValid ? currentSample : held ? retained.sample : currentSample;
      const distance = Number(sample.distance_m ?? (Number(sample.distance_mm) / 1000));
      const fresh = sample.available === true && !sample.simulated && Number.isFinite(distance) && distance > 0 && distance <= 4;
      const showHeld = held || (Number.isFinite(retainedAge) && retainedAge > 600);
      const error = String(currentSample.error || sample.error || '');
      const rangeState = error === 'too_close' ? 'TOO CLOSE <2 cm'
        : error === 'no_echo' ? 'NO ECHO'
          : error === 'echo_timeout' ? 'ECHO TIMEOUT'
            : error === 'too_far' ? 'BEYOND 4 m' : 'WAITING';
      const cardX = x + tofWidth + gap + index * (cardWidth + gap);
      ctx.strokeStyle = 'rgba(135,206,166,.2)'; ctx.strokeRect(cardX, y, cardWidth, height);
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#9fc5ac';
      ctx.font = '600 13px ui-monospace, monospace'; ctx.fillText(names[index], cardX + cardWidth / 2, y + 18);
      ctx.fillStyle = fresh ? (showHeld ? '#efcb76' : distance < .35 ? '#f17c70' : distance < .8 ? '#efcb76' : '#bcebd0') : error === 'too_close' ? '#f17c70' : '#91a79b';
      ctx.font = '600 18px ui-monospace, monospace'; ctx.fillText(fresh ? `${showHeld ? '~' : ''}${distance.toFixed(2)} m` : rangeState, cardX + cardWidth / 2, y + height * .52, cardWidth - 8);
      const trackX = cardX + 10; const trackY = y + height - 23; const trackWidth = Math.max(1, cardWidth - 20);
      ctx.fillStyle = 'rgba(120,190,150,.12)'; ctx.fillRect(trackX, trackY, trackWidth, 7);
      if (fresh || error === 'too_close') { ctx.fillStyle = error === 'too_close' ? '#f17c70' : showHeld ? '#efcb76' : distance < .35 ? '#f17c70' : distance < .8 ? '#efcb76' : '#63d7ae'; ctx.globalAlpha = showHeld ? .65 : 1; ctx.fillRect(trackX, trackY, trackWidth * (error === 'too_close' ? .01 : Math.min(1, distance / 4)), 7); ctx.globalAlpha = 1; }
      ctx.strokeStyle = 'rgba(135,206,166,.35)'; ctx.strokeRect(trackX, trackY, trackWidth, 7);
      ctx.fillStyle = '#91a79b'; ctx.font = '9px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.fillText('0m', trackX, y + height - 7); ctx.textAlign = 'right'; ctx.fillText('4m', trackX + trackWidth, y + height - 7);
    });
  }

  drawTofRangeBar(ctx, x, y, width, height, sample) {
    const distance = Number(sample?.distance_m);
    const fresh = sample?.available === true && !sample?.simulated
      && Number.isFinite(distance) && distance >= 0 && distance <= 4;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#9fc5ac';
    ctx.font = '600 13px ui-monospace, monospace';
    ctx.fillText('ToF', x + width / 2, y + 5);
    ctx.textAlign = 'center';
    ctx.fillStyle = fresh ? (distance < .5 ? '#f17c70' : distance < 1.2 ? '#efcb76' : '#bcebd0') : '#91a79b';
    ctx.fillText(fresh ? `${distance.toFixed(2)}m` : 'WAIT', x + width / 2, y + 23);
    const trackX = x + width / 2 - 4;
    const trackY = y + 40;
    const trackHeight = Math.max(10, height - 52);
    ctx.fillStyle = 'rgba(231,118,104,.72)'; ctx.fillRect(trackX, trackY + trackHeight * .82, 8, trackHeight * .18);
    ctx.fillStyle = 'rgba(231,189,104,.62)'; ctx.fillRect(trackX, trackY + trackHeight * .7, 8, trackHeight * .12);
    ctx.fillStyle = 'rgba(99,215,174,.42)'; ctx.fillRect(trackX, trackY, 8, trackHeight * .7);
    ctx.strokeStyle = 'rgba(135,206,166,.35)'; ctx.lineWidth = 1; ctx.strokeRect(trackX, trackY, 8, trackHeight);
    ctx.textAlign = 'center'; ctx.font = '10px ui-monospace, monospace'; ctx.fillStyle = '#91a79b';
    ctx.fillText('4', x + width / 2, trackY - 8); ctx.fillText('0', x + width / 2, trackY + trackHeight + 8);
    if (fresh) {
      const markerY = trackY + trackHeight * (1 - Math.max(0, Math.min(1, distance / 4)));
      ctx.fillStyle = '#f4fff7'; ctx.fillRect(trackX - 4, markerY - 2, 16, 4);
    }
  }

  drawMetricMap(ctx, x, y, width, height, lidar, radar, perception, title, mode) {
    ctx.fillStyle = '#9fc5ac'; ctx.font = '600 17px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(`${title}  ·  ${mode === 'lidar' ? lidar.length : radar.length}`, x + 6, y + 14);
    const mapTop = y + 32;
    const mapHeight = height - 42;
    const cx = x + width / 2;
    const cy = mode === 'lidar' ? mapTop + mapHeight - 12 : mapTop + mapHeight - 24;
    const radius = Math.min(width * 0.46, mapHeight * 0.92);
    const scale = radius / 6;
    ctx.save();
    ctx.beginPath(); ctx.rect(x, mapTop, width, mapHeight); ctx.clip();
    ctx.strokeStyle = 'rgba(120,190,150,.18)';
    const plotLeft = x + 26;
    const plotRight = x + width - 18;
    const plotTop = mapTop + 12;
    const plotBottom = mode === 'lidar' ? cy : mapTop + mapHeight - 24;
    if (mode === 'lidar') {
      for (let meters = 1; meters <= 6; meters += 1) {
        ctx.strokeStyle = meters % 2 === 0 ? 'rgba(120,190,150,.28)' : 'rgba(120,190,150,.13)';
        ctx.beginPath(); ctx.arc(cx, cy, meters * scale, Math.PI, Math.PI * 2); ctx.stroke();
      }
      for (let spoke = 0; spoke <= 12; spoke += 1) {
        const angle = Math.PI + spoke * Math.PI / 12;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius); ctx.stroke();
      }
      ctx.fillStyle = '#a8c3b1'; ctx.font = '16px ui-monospace, monospace'; ctx.textAlign = 'center';
      ctx.fillText('LEFT', plotLeft, cy - 3); ctx.fillText('FRONT', cx, plotTop + 12); ctx.fillText('RIGHT', plotRight, cy - 3);
    } else {
      ctx.fillStyle = 'rgba(15,34,30,.46)'; ctx.fillRect(plotLeft, plotTop, plotRight - plotLeft, plotBottom - plotTop);
      for (let i = 0; i <= 6; i += 1) {
        const gx = plotLeft + (plotRight - plotLeft) * i / 6;
        const gy = plotTop + (plotBottom - plotTop) * i / 6;
        ctx.strokeStyle = i % 2 === 0 ? 'rgba(120,190,150,.25)' : 'rgba(120,190,150,.12)';
        ctx.beginPath(); ctx.moveTo(gx, plotTop); ctx.lineTo(gx, plotBottom); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(plotLeft, gy); ctx.lineTo(plotRight, gy); ctx.stroke();
      }
      ctx.fillStyle = '#a8c3b1'; ctx.font = '16px ui-monospace, monospace'; ctx.textAlign = 'center';
      ctx.fillText('−60°', plotLeft, plotBottom + 14); ctx.fillText('0°', cx, plotBottom + 14); ctx.fillText('+60°', plotRight, plotBottom + 14);
      ctx.textAlign = 'left'; ctx.fillText('RANGE', plotLeft + 6, plotTop + 14);
    }
    const frame = perception.sensor_projections?.frame || {};
    const bodyPosition = frame.body || perception.body?.position || [0, 0, 0];
    const yaw = Number(frame.yaw_rad ?? perception.body?.orientation ?? 0);
    const lidarFrame = String(perception.sensor_projections?.lidar?.frame || 'body_world').toLowerCase();
    const radarFrame = String(perception.modalities?.mmwave_radar?.frame || 'body').toLowerCase();
    const mapPoint = (position, sourceFrame, assumeWorld) => {
      if (!Array.isArray(position) || position.length < 2) return null;
      let forward = Number(position[0]);
      let left = Number(position[1]);
      const world = /^(body_world|world|map|local_map|odom)$/.test(sourceFrame) || assumeWorld;
      if (world) {
        const dx = forward - Number(bodyPosition[0] || 0);
        const dy = left - Number(bodyPosition[1] || 0);
        forward = Math.cos(yaw) * dx + Math.sin(yaw) * dy;
        left = -Math.sin(yaw) * dx + Math.cos(yaw) * dy;
      }
      const distance = Math.hypot(forward, left);
      if (![forward, left].every(Number.isFinite) || distance > 6.2) return null;
      return { x: cx - left * scale, y: cy - forward * scale, distance, forward, left };
    };
    if (mode === 'lidar') {
      const returns = lidar.map(point => ({
        point,
        mapped: mapPoint([Number(point.x), Number(point.y)], lidarFrame, false),
      })).filter(item => item.mapped).sort((a, b) => Math.atan2(a.mapped.y - cy, a.mapped.x - cx) - Math.atan2(b.mapped.y - cy, b.mapped.x - cx));
      ctx.save();
      ctx.setLineDash([5, 6]);
      ctx.strokeStyle = 'rgba(94, 221, 228, .38)';
      ctx.lineWidth = 2;
      for (let index = 0; index < returns.length; index += 1) {
        const current = returns[index].mapped;
        const next = returns[(index + 1) % returns.length].mapped;
        if (returns[index].mapped.forward < 0 || next.forward < 0) continue;
        const angleCurrent = Math.atan2(current.y - cy, current.x - cx);
        const angleNext = Math.atan2(next.y - cy, next.x - cx);
        const angleGap = (angleNext - angleCurrent + Math.PI * 2) % (Math.PI * 2);
        if (angleGap > 0.75 || Math.abs(current.distance - next.distance) > 0.7) continue;
        ctx.beginPath(); ctx.moveTo(current.x, current.y); ctx.lineTo(next.x, next.y); ctx.stroke();
      }
      ctx.restore();
      for (const { point, mapped } of returns) {
        if (mapped.forward < 0) continue;
        const intensity = Math.max(.2, Math.min(1, Number(point.intensity ?? .7)));
        const dot = mapped.distance < 2 ? 5 : 3.5;
        ctx.fillStyle = `rgba(94, 221, 228, ${intensity * .2})`;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, dot * 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = `rgba(94, 221, 228, ${intensity})`;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, dot, 0, Math.PI * 2); ctx.fill();
      }
      ctx.fillStyle = '#83a99a'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText('Measured returns · dashed links show local continuity', x + 6, y + height - 5);
    } else {
      for (const target of radar) {
        const position = target.position_m || target.position || [];
        const velocity = target.velocity_mps || target.velocity || [0, 0];
        const isLd2450 = /^hlk_ld2450/i.test(String(perception.modalities?.mmwave_radar?.source || ''));
        const radarPosition = isLd2450 ? [Number(position[1]), -Number(position[0]), Number(position[2] || 0)] : position;
        const radarVelocity = isLd2450 ? [Number(velocity[1] || 0), -Number(velocity[0] || 0)] : velocity;
        const local = this.sensorLocal(radarPosition, radarFrame, bodyPosition, yaw);
        if (!local || local.forward < 0 || local.distance > 6.2) continue;
        const bearing = Math.atan2(-local.left, local.forward);
        if (Math.abs(bearing) > Math.PI / 3) continue;
        const mapped = { x: cx + (bearing / (Math.PI / 3)) * ((plotRight - plotLeft) / 2), y: plotBottom - (local.distance / 6) * (plotBottom - plotTop), distance: local.distance };
        const radialSpeed = Number(target.radial_speed_mps);
        const classification = String(target.classification || '').toLowerCase();
        const isMoving = /moving|mobile/.test(classification)
          || (Number.isFinite(radialSpeed) && Math.abs(radialSpeed) >= 0.05)
          || Math.hypot(Number(radarVelocity[0] || 0), Number(radarVelocity[1] || 0)) >= 0.05;
        const color = isMoving ? '#ef91c5' : '#f2ce73';
        const confidence = Math.max(.3, Math.min(1, Number(target.confidence ?? .7)));
        ctx.strokeStyle = color; ctx.globalAlpha = .18 + confidence * .2; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, 24 + (1 - confidence) * 18, 0, Math.PI * 2); ctx.stroke();
        ctx.globalAlpha = 1;
        let forwardSpeed = Number(radarVelocity[0] || 0);
        let leftSpeed = Number(radarVelocity[1] || 0);
        if (/^(body_world|world|map|local_map|odom)$/.test(radarFrame)) {
          const worldForward = forwardSpeed;
          forwardSpeed = Math.cos(yaw) * worldForward + Math.sin(yaw) * leftSpeed;
          leftSpeed = -Math.sin(yaw) * worldForward + Math.cos(yaw) * leftSpeed;
        }
        const rangeRate = (local.forward * forwardSpeed + local.left * leftSpeed) / Math.max(local.distance, .1);
        const bearingRate = (-local.forward * leftSpeed + local.left * forwardSpeed) / Math.max(local.distance ** 2, .01);
        const vectorX = bearingRate * ((plotRight - plotLeft) / 2) / (Math.PI / 3) * .5;
        const vectorY = -rangeRate * ((plotBottom - plotTop) / 6) * .5;
        if (Math.hypot(vectorX, vectorY) > 3) {
          const endX = mapped.x + vectorX;
          const endY = mapped.y + vectorY;
          ctx.strokeStyle = color; ctx.lineWidth = 4;
          ctx.beginPath(); ctx.moveTo(mapped.x, mapped.y); ctx.lineTo(endX, endY); ctx.stroke();
          const angle = Math.atan2(vectorY, vectorX);
          ctx.beginPath(); ctx.moveTo(endX, endY);
          ctx.lineTo(endX - 10 * Math.cos(angle - .5), endY - 10 * Math.sin(angle - .5));
          ctx.lineTo(endX - 10 * Math.cos(angle + .5), endY - 10 * Math.sin(angle + .5));
          ctx.closePath(); ctx.fillStyle = color; ctx.fill();
        }
        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(mapped.x, mapped.y, 8, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#fff3cf'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#f8e8b8'; ctx.font = '600 15px ui-monospace, monospace'; ctx.textAlign = 'center';
        ctx.fillText(isMoving ? 'M' : '•', mapped.x, mapped.y - 12);
        {
          const rangeLabel = `${local.distance.toFixed(2)} m`;
          const speedLabel = Number.isFinite(radialSpeed) ? `${radialSpeed >= 0 ? '+' : ''}${radialSpeed.toFixed(2)} m/s` : '';
          const speedFont = 14;
          const labelPadding = 4;
          const labelWidth = speedFont * Math.max(rangeLabel.length, speedLabel.length) * .62 + labelPadding * 2;
          const labelHeight = speedFont * (speedLabel ? 2 : 1) + labelPadding * 2;
          const labelGap = 10;
          ctx.font = `600 ${speedFont}px ui-monospace, monospace`; ctx.textAlign = 'left';
          const preferredX = mapped.x > cx ? mapped.x - labelGap - labelWidth : mapped.x + labelGap;
          const labelX = Math.max(plotLeft, Math.min(plotRight - labelWidth, preferredX));
          const labelY = Math.max(plotTop + labelHeight, Math.min(plotBottom - labelPadding, mapped.y + speedFont * .35));
          ctx.fillStyle = 'rgba(4, 13, 11, .92)'; ctx.fillRect(labelX - labelPadding, labelY - labelHeight, labelWidth, labelHeight);
          ctx.fillStyle = color; ctx.fillText(rangeLabel, labelX, labelY - (speedLabel ? speedFont : 0));
          if (speedLabel) ctx.fillText(speedLabel, labelX, labelY);
        }
      }
      ctx.fillStyle = '#83a99a'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText('Target range · radial speed labels · arrows use XY velocity', x + 6, y + height - 5);
    }
    if (mode === 'lidar') {
      ctx.fillStyle = '#d9f5e4'; ctx.beginPath();
      ctx.moveTo(cx, cy - 17); ctx.lineTo(cx - 11, cy + 8); ctx.lineTo(cx + 11, cy + 8); ctx.closePath(); ctx.fill();
    } else {
      ctx.strokeStyle = '#d9f5e4'; ctx.fillStyle = '#0b1512'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(cx - 9, plotBottom - 16, 18, 15, 4); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - 5, plotBottom - 15); ctx.lineTo(cx, plotBottom - 24); ctx.lineTo(cx + 5, plotBottom - 15); ctx.stroke();
    }
    ctx.restore();
    ctx.fillStyle = '#779586'; ctx.font = '13px ui-monospace, monospace'; ctx.textAlign = 'right';
    ctx.fillText('BODY', x + width - 6, y + 14);
  }

  sensorLocal(position, sourceFrame, bodyPosition, yaw) {
    if (!Array.isArray(position) || position.length < 2) return null;
    let forward = Number(position[0]);
    let left = Number(position[1]);
    if (/^(body_world|world|map|local_map|odom)$/i.test(sourceFrame || '')) {
      const dx = forward - Number(bodyPosition[0] || 0);
      const dy = left - Number(bodyPosition[1] || 0);
      forward = Math.cos(yaw) * dx + Math.sin(yaw) * dy;
      left = -Math.sin(yaw) * dx + Math.cos(yaw) * dy;
    }
    return { forward, left, distance: Math.hypot(forward, left) };
  }

  async setCameraFrame(frame) {
    const encoded = frame?.image_base64;
    if (!encoded || encoded.length > 5_000_000) {
      this.setCameraStatus(encoded ? 'FRAME TOO LARGE' : 'CAMERA · NO FRAME');
      return;
    }
    try {
      const bytes = Uint8Array.from(atob(encoded), character => character.charCodeAt(0));
      const source = await createImageBitmap(new Blob([bytes], { type: frame.mime_type || 'image/jpeg' }));
      const displaySource = source;
      const bitmap = await createImageBitmap(displaySource);
      this.cameraBitmap?.close?.();
      this.cameraBitmap = bitmap;
      this.cameraFrameId = String(frame.frame_id || '');
      this.cameraCapturedAt = Number(frame.captured_at) || 0;
      this.cameraMessage = 'LIVE';
      this.sensorStatus.camera = `LIVE · ${frame.width || bitmap.width}×${frame.height || bitmap.height}`;
      this.drawDashboard();
    } catch {
      this.setCameraStatus('CAMERA · DECODE ERROR');
    }
  }

  setCameraStatus(message, preserveFrame = false) {
    if (!preserveFrame) {
      this.cameraBitmap?.close?.();
      this.cameraBitmap = null;
    }
    this.cameraMessage = message;
    this.sensorStatus.camera = message.replace(/^CAMERA\s*·\s*/i, '');
    this.drawDashboard();
  }

  setVisible(visible) {
    this.visible = Boolean(visible);
    if (this.gpsMapRoot) this.gpsMapRoot.visible = this.visible && this.gpsMapVisible;
  }

  setSceneMode(mode) {
    this.sceneMode = mode === 'sensors' ? 'sensors' : 'simulation';
    this.drawDashboard();
  }

  setCameraBackgroundActive(active) {
    this.cameraBackgroundActive = Boolean(active);
    this.drawDashboard();
  }

  setActionBusy(busy) {
    this.actionBusy = Boolean(busy);
    this.drawDashboard();
  }

  clearPointer() {
    this.pointerRing.visible = false;
  }

  updatePointer(controller, raycaster) {
    if (!this.visible) return null;
    controller.updateMatrixWorld(true);
    const rotation = this.pointerRotation.extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObjects(this.panels.filter(panel => panel !== this.gpsMapPanel || this.gpsMapVisible), false)[0];
    if (!hit) { this.pointerRing.visible = false; return null; }
    const panel = hit.object;
    if (this.pointerRing.parent !== panel) panel.add(this.pointerRing);
    const localPoint = panel.worldToLocal(hit.point.clone());
    const normal = this.pointerNormal.set(0, 0, 1);
    this.pointerRing.position.copy(localPoint).addScaledVector(normal, 0.012);
    this.pointerRing.quaternion.setFromUnitVectors(this.pointerForward, normal);
    this.pointerRing.visible = true;
    return hit;
  }

  isControllerOverDashboard(controller, raycaster) {
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    return raycaster.intersectObjects(this.panels.filter(panel => panel !== this.gpsMapPanel || this.gpsMapVisible), false).length > 0;
  }

  activateAt(controller, raycaster) {
    if (!this.visible) return null;
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObjects(this.panels.filter(panel => panel !== this.gpsMapPanel || this.gpsMapVisible), false)[0];
    if (!hit?.uv) return null;
    if (hit.object === this.gpsMapPanel) {
      const x = hit.uv.x * this.gpsMapCanvas.width;
      const y = (1 - hit.uv.y) * this.gpsMapCanvas.height;
      for (const [key, area] of Object.entries(this.gpsMapActionHitAreas)) {
        if (x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
      }
      return 'gps-map-window';
    }
    const x = hit.uv.x * this.logicalWidth;
    const y = (1 - hit.uv.y) * this.logicalHeight;
    const cameraArea = this.cameraHitArea;
    if (cameraArea && x >= cameraArea.x && x <= cameraArea.x + cameraArea.width && y >= cameraArea.y && y <= cameraArea.y + cameraArea.height) return 'camera-background';
    for (const [key, area] of Object.entries(this.actionHitAreas)) {
      if (area.enabled && x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
    }
    return 'dashboard';
  }

  beginAdjust(controller, inputSource, aimController = controller, raycaster = null) {
    if (!this.visible || this.grabbedController) return false;
    let target = 'hud';
    if (raycaster && aimController) {
      aimController.updateMatrixWorld(true);
      const rotation = new this.THREE.Matrix4().extractRotation(aimController.matrixWorld);
      raycaster.ray.origin.setFromMatrixPosition(aimController.matrixWorld);
      raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
      this.scene.updateMatrixWorld(true);
      if (this.gpsMapVisible && this.gpsMapRoot.visible && raycaster.intersectObject(this.gpsMapPanel, false).length) target = 'gps-map';
    }
    const root = target === 'gps-map' ? this.gpsMapRoot : this.root;
    controller.updateMatrixWorld(true);
    controller.getWorldPosition(this.scratchPosition);
    controller.getWorldQuaternion(this.scratchQuaternion);
    this.grabOffsetPosition.copy(root.position).sub(this.scratchPosition).applyQuaternion(this.scratchQuaternion.clone().invert());
    this.grabOffsetQuaternion.copy(this.scratchQuaternion).invert().multiply(root.quaternion);
    this.grabbedController = controller;
    this.grabbedWindow = target;
    this.grabInputSource = inputSource || null;
    this.depthOffset = 0;
    this.headLocked = false;
    this.worldAnchored = true;
    this.drawDashboard();
    return true;
  }

  endAdjust(controller, xrCamera = null) {
    if (this.grabbedController !== controller) return false;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.depthOffset = 0;
    if (xrCamera) {
      if (this.grabbedWindow === 'gps-map') {
        this.gpsMapBaseQuaternion.copy(this.gpsMapRoot.quaternion);
        this.persistGpsMapPose(xrCamera, true);
      } else {
        this.hudBaseQuaternion.copy(this.root.quaternion);
        this.persistPose(xrCamera, true);
      }
    }
    this.grabbedWindow = 'hud';
    this.drawDashboard();
    return true;
  }

  updateAdjustment(deltaSeconds = 1 / 90, inputSources = []) {
    if (!this.grabbedController) return;
    this.grabbedController.getWorldPosition(this.scratchPosition);
    this.grabbedController.getWorldQuaternion(this.scratchQuaternion);
    this.scratchOffset.copy(this.grabOffsetPosition).applyQuaternion(this.scratchQuaternion);
    const targetRoot = this.grabbedWindow === 'gps-map' ? this.gpsMapRoot : this.root;
    targetRoot.position.copy(this.scratchPosition).add(this.scratchOffset);
    targetRoot.quaternion.copy(this.scratchQuaternion).multiply(this.grabOffsetQuaternion);
    const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
    const stick = source => {
      const axes = source?.gamepad?.axes || [];
      const first = [Number(axes[0]) || 0, Number(axes[1]) || 0];
      const second = [Number(axes[2]) || 0, Number(axes[3]) || 0];
      return Math.hypot(...second) > Math.hypot(...first) ? second : first;
    };
    const [widthInput, depthInput] = stick(this.grabInputSource);
    const otherSource = inputSources.find(source => source !== this.grabInputSource && source.handedness !== this.grabInputSource?.handedness);
    const [, heightInput] = stick(otherSource);
    this.grabForward.set(0, 0, -1).applyQuaternion(this.scratchQuaternion);
    if (Math.abs(depthInput) > 0.12) this.depthOffset = Math.max(-1, Math.min(4, this.depthOffset - depthInput * elapsed * 1.8));
    targetRoot.position.addScaledVector(this.grabForward, this.depthOffset);
    if (this.grabbedWindow === 'gps-map') {
      if (Math.abs(widthInput) > 0.12) this.gpsMapWidthScale = Math.max(0.45, Math.min(5, this.gpsMapWidthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.gpsMapHeightScale = Math.max(0.45, Math.min(5, this.gpsMapHeightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.applyGpsMapSize();
    } else {
      if (Math.abs(widthInput) > 0.12) this.widthScale = Math.max(0.45, Math.min(5, this.widthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.heightScale = Math.max(0.45, Math.min(5, this.heightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.applyHudSize();
    }
  }

  applyHudSize() {
    if (!this.panel || !this.robotVisual) return;
    this.panel.scale.set(this.widthScale, this.heightScale, 1);
    this.robotVisual.group.position.x = -0.36 * this.widthScale;
    this.robotVisual.group.position.y = -0.04 * this.heightScale;
    this.robotVisual.group.scale.setScalar(0.24 * Math.min(this.widthScale, this.heightScale));
  }

  resetPose() {
    this.grabbedController = null;
    this.grabInputSource = null;
    this.headLocked = false;
    this.worldAnchored = false;
    this.depthOffset = 0;
    this.widthScale = 1;
    this.heightScale = 1;
    this.headOffsetPosition.set(0, 0, 0);
    this.headOffsetQuaternion.identity();
    this.cachedPose = null;
    this.applyHudSize();
    try { localStorage.removeItem('pandorabox.quest-hud-pose.v1'); } catch {}
    this.drawDashboard();
  }

  syncPose(xrCamera) {
    if (this.grabbedController) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    if (this.headLocked) {
      this.headLocked = false;
      this.worldAnchored = false;
    }
    this.anchorForward.set(0, 0, -1).applyQuaternion(this.scratchQuaternion);
    this.anchorForward.y = 0;
    if (this.anchorForward.lengthSq() > 0.0001) this.anchorForward.normalize();
    if (!this.worldAnchored) {
      if (this.cachedPose) {
        this.root.position.copy(this.headOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
        this.root.quaternion.copy(this.scratchQuaternion).multiply(this.headOffsetQuaternion);
      } else {
        this.root.position.copy(this.scratchPosition).addScaledVector(this.anchorForward, 0.9);
        this.root.position.y += -0.02;
        this.facingMatrix.lookAt(this.scratchPosition, this.root.position, this.worldUp);
        this.root.quaternion.setFromRotationMatrix(this.facingMatrix);
      }
      this.hudBaseQuaternion.copy(this.root.quaternion);
      this.worldAnchored = true;
    }
    if (this.gpsMapVisible && !this.gpsMapWorldAnchored) {
      if (this.gpsMapPose) {
        this.gpsMapRoot.position.copy(this.gpsMapHeadOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
        this.gpsMapRoot.quaternion.copy(this.scratchQuaternion).multiply(this.gpsMapHeadOffsetQuaternion);
      } else {
        this.gpsMapRoot.position.copy(this.root.position).add(new this.THREE.Vector3(2.65, -0.08, -0.9).applyQuaternion(this.hudBaseQuaternion));
        this.gpsMapRoot.quaternion.copy(this.hudBaseQuaternion);
      }
      this.gpsMapBaseQuaternion.copy(this.gpsMapRoot.quaternion);
      this.gpsMapWorldAnchored = true;
    }
    // Keep each window fixed in world position and yaw, while pitching its flat plane
    // with the viewer's vertical look angle so it faces the horizon or upper/lower sphere.
    this.viewForward.set(0, 0, -1).applyQuaternion(this.scratchQuaternion);
    const gazePitch = Math.asin(this.THREE.MathUtils.clamp(this.viewForward.y, -0.8660254, 0.8660254));
    this.verticalOffset.copy(this.scratchPosition).sub(this.root.position);
    const hudPitch = this.THREE.MathUtils.clamp(gazePitch + Math.atan2(this.verticalOffset.y, Math.max(0.25, Math.hypot(this.verticalOffset.x, this.verticalOffset.z))), -Math.PI / 3, Math.PI / 3);
    this.viewPitchQuaternion.setFromAxisAngle(this.panelRight, hudPitch);
    this.root.quaternion.copy(this.hudBaseQuaternion).multiply(this.viewPitchQuaternion);
    if (this.gpsMapWorldAnchored) {
      this.verticalOffset.copy(this.scratchPosition).sub(this.gpsMapRoot.position);
      const mapPitch = this.THREE.MathUtils.clamp(gazePitch + Math.atan2(this.verticalOffset.y, Math.max(0.25, Math.hypot(this.verticalOffset.x, this.verticalOffset.z))), -Math.PI / 3, Math.PI / 3);
      this.viewPitchQuaternion.setFromAxisAngle(this.panelRight, mapPitch);
      this.gpsMapRoot.quaternion.copy(this.gpsMapBaseQuaternion).multiply(this.viewPitchQuaternion);
    }
    // Keep the HUD world-anchored; the wearer can reposition it explicitly by grabbing it.
  }

  loadSavedPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-hud-pose.v1') || 'null');
      if (!Array.isArray(saved?.position) || saved.position.length !== 3 || !Array.isArray(saved?.quaternion) || saved.quaternion.length !== 4) return;
      const values = [...saved.position, ...saved.quaternion, saved.scale].map(Number);
      if (!values.every(Number.isFinite) || values.slice(0, 3).some(value => Math.abs(value) > 20)) return;
      this.headOffsetPosition.fromArray(saved.position);
      this.headOffsetQuaternion.fromArray(saved.quaternion).normalize();
      const legacyScale = Number(saved.scale) || 1;
      this.widthScale = Math.max(0.45, Math.min(5, Number(saved.widthScale ?? legacyScale)));
      this.heightScale = Math.max(0.45, Math.min(5, Number(saved.heightScale ?? legacyScale)));
      this.cachedPose = this.makeSavedPose();
      this.headLocked = false;
      this.worldAnchored = false;
    } catch {}
  }

  persistPose(xrCamera, force = false) {
    if (!xrCamera) return;
    this.persistGpsMapPose(xrCamera);
    if (this.headLocked || (!force && performance.now() - this.lastPosePersistAt < 750)) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.headOffsetPosition.copy(this.root.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.headOffsetQuaternion.copy(inverseHead).multiply(this.root.quaternion).normalize();
    this.cachedPose = this.makeSavedPose();
    this.writeSavedPose();
  }

  cachePose(xrCamera) {
    if (!xrCamera || this.headLocked) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.headOffsetPosition.copy(this.root.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.headOffsetQuaternion.copy(inverseHead).multiply(this.root.quaternion).normalize();
    this.cachedPose = this.makeSavedPose();
  }

  makeSavedPose() {
    return {
      position: this.headOffsetPosition.toArray(),
      quaternion: this.headOffsetQuaternion.toArray(),
      widthScale: this.widthScale,
      heightScale: this.heightScale,
      scale: Math.sqrt(this.widthScale * this.heightScale),
    };
  }

  writeSavedPose() {
    if (!this.cachedPose) return;
    try {
      localStorage.setItem('pandorabox.quest-hud-pose.v1', JSON.stringify(this.cachedPose));
      this.lastPosePersistAt = performance.now();
    } catch {}
  }

  flushSavedPose() {
    if (!this.headLocked && this.cachedPose) this.writeSavedPose();
  }

  leaveSession() {
    this.flushSavedPose();
    this.grabbedController = null;
    this.grabInputSource = null;
  }
}
