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
    this.grabbedPanel = null;
    this.grabAnchorLocal = new THREE.Vector3();
    this.grabAnchorTarget = new THREE.Vector3();
    this.grabRayDirection = new THREE.Vector3(0, 0, -1);
    this.grabAnchorDistance = 0;
    this.grabPanelOffset = new THREE.Vector3();
    this.scratchPosition = new THREE.Vector3();
    this.scratchQuaternion = new THREE.Quaternion();
    this.facingMatrix = new THREE.Matrix4();
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
    this.gpsMapStickZoomAccumulator = 0;
    this.gpsMapPanController = null;
    this.gpsMapPanLastPoint = null;
    this.gpsMapPanLastAt = 0;
    this.gpsMapHoveredController = null;
    this.gpsMapActionHitAreas = {};
    this.grabbedWindow = 'hud';
    this.systemMetrics = null;
    this.powerWindowVisible = false;
    this.powerWindowWorldAnchored = false;
    this.powerWindowPose = null;
    this.powerWindowHeadOffsetPosition = new THREE.Vector3();
    this.powerWindowHeadOffsetQuaternion = new THREE.Quaternion();
    this.powerWindowWidthScale = 1;
    this.powerWindowHeightScale = 1;
    this.powerWindowActionHitAreas = {};
    this.powerWindowMessage = '';
    this.pendingBatteryLevel = null;
    this.powerStatus = null;
    this.lastPowerWindowPosePersistAt = 0;
    this.fnkVisible = false;
    this.fnkBoardOnlyConfirmed = false;
    this.fnkTab = 'control';
    this.fnkTeleopArmed = false;
    this.fnkSceneInputSelected = false;
    this.fnkDriveInFlight = false;
    this.fnkLastDriveAt = 0;
    this.fnkGyroCurrent = new THREE.Quaternion();
    this.fnkGyroBaseline = null;
    this.fnkGyroPoseBase = null;
    this.fnkGyroDelta = new THREE.Quaternion();
    this.fnkGyroAxis = new THREE.Vector3();
    this.fnkLeg = 1;
    this.fnkGait = 'tripod';
    this.fnkSpeed = 1;
    this.fnkPreviewPaused = false;
    this.fnkPreviewDemo = false;
    this.fnkPreviewKeys = { w: true };
    this.fnkPreviewVelocity = { x: 0, y: -1, turn: 0 };
    this.fnkPreviewDemoStartedAt = 0;
    this.fnkControllerInput = null;
    this.fnkPreviewIntensity = 0;
    this.fnkPreviewLastAt = 0;
    this.fnkGridOffset = { x: 0, y: 0, yaw: 0 };
    this.fnkBusy = false;
    this.fnkHardwareStatus = null;
    this.fnkLegState = null;
    this.fnkMessage = 'FNK0031 · WAITING FOR BOARD STATUS';
    this.fnkActionHitAreas = {};
    this.fnkRoot = new THREE.Group();
    this.fnkRoot.visible = false;
    this.scene.add(this.fnkRoot);
    this.fnkCanvas = document.createElement('canvas');
    this.fnkCanvas.width = 1200;
    this.fnkCanvas.height = 1120;
    this.fnkContext = this.fnkCanvas.getContext('2d');
    this.fnkTexture = new THREE.CanvasTexture(this.fnkCanvas);
    this.fnkTexture.colorSpace = THREE.SRGBColorSpace;
    this.fnkTexture.generateMipmaps = true;
    this.fnkTexture.minFilter = THREE.LinearMipmapLinearFilter;
    this.fnkTexture.magFilter = THREE.LinearFilter;
    this.fnkTexture.anisotropy = Math.min(8, Number(maxAnisotropy) || 1);
    this.fnkPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(2.8, 2.613),
      new THREE.MeshBasicMaterial({ map: this.fnkTexture, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.fnkPanel.renderOrder = 1200;
    this.fnkRoot.add(this.fnkPanel);
    this.panels.push(this.fnkPanel);
    this.fnkWorldAnchored = false;
    this.fnkPose = null;
    this.fnkHeadOffsetPosition = new THREE.Vector3();
    this.fnkHeadOffsetQuaternion = new THREE.Quaternion();
    this.fnkWidthScale = 1;
    this.fnkHeightScale = 1;
    this.lastFnkPosePersistAt = 0;
    this.loadSavedFnkPose();
    this.drawFnkControlWindow();
    this.worldUp = new THREE.Vector3(0, 1, 0);
    this.verticalOffset = new THREE.Vector3();
    this.sphereCenter = new THREE.Vector3();
    this.sphereCenterSet = false;
    this.surfaceDirection = new THREE.Vector3();
    this.orientationTarget = new THREE.Vector3();
    this.cameraFov = null;
    this.ultrasonicStatus = null;
    this.lastUltrasonicSamples = Object.create(null);
    this.sensorStatus = { camera: 'WAITING', yolo: 'WAITING', midas: 'WAITING' };
    this.sensorPointDensity = 100;
    this.sensorPointDensityHitArea = null;
    this.sensorDensityDragController = null;
    this.onSensorPointDensityChange = null;
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
      new THREE.PlaneGeometry(3.8, 2.7075),
      new THREE.MeshBasicMaterial({ map: this.gpsMapTexture, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.gpsMapPanel.renderOrder = 1100;
    this.gpsMapRoot.add(this.gpsMapPanel);
    this.scene.add(this.gpsMapRoot);
    this.panels.push(this.gpsMapPanel);
    this.loadSavedGpsMapPose();
    this.drawGpsMapWindow();
    this.powerWindowRoot = new THREE.Group();
    this.powerWindowRoot.visible = false;
    this.powerWindowCanvas = document.createElement('canvas');
    this.powerWindowCanvas.width = 1800;
    this.powerWindowCanvas.height = 1120;
    this.powerWindowContext = this.powerWindowCanvas.getContext('2d');
    this.powerWindowTexture = new THREE.CanvasTexture(this.powerWindowCanvas);
    this.powerWindowTexture.colorSpace = THREE.SRGBColorSpace;
    this.powerWindowTexture.generateMipmaps = true;
    this.powerWindowTexture.minFilter = THREE.LinearMipmapLinearFilter;
    this.powerWindowTexture.magFilter = THREE.LinearFilter;
    this.powerWindowTexture.anisotropy = Math.min(8, Number(maxAnisotropy) || 1);
    this.powerWindowPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(3.8, 2.364),
      new THREE.MeshBasicMaterial({ map: this.powerWindowTexture, depthTest: false, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.powerWindowPanel.renderOrder = 1150;
    this.powerWindowRoot.add(this.powerWindowPanel);
    this.scene.add(this.powerWindowRoot);
    this.panels.push(this.powerWindowPanel);
    this.loadSavedPowerWindowPose();
    this.drawPowerWindow();
    this.drawDashboard();
  }

  update(frame) {
    this.frame = frame;
    this.drawDashboard();
  }

  updateTelemetry(telemetry) {
    this.telemetry = telemetry;
    this.drawDashboard();
    if (this.fnkVisible) this.drawFnkControlWindow();
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
    if (!this.gpsMapVisible) {
      this.gpsMapPanController = null; this.gpsMapPanLastPoint = null; this.gpsMapHoveredController = null;
      this.gpsMapStickZoomAccumulator = 0;
    }
    this.drawDashboard();
    this.drawGpsMapWindow();
  }

  beginGpsMapPan(controller, raycaster) {
    if (!this.visible || !this.gpsMapVisible) return false;
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObject(this.gpsMapPanel, false)[0];
    if (!hit?.uv) return false;
    const point = { x: hit.uv.x * this.gpsMapCanvas.width, y: (1 - hit.uv.y) * this.gpsMapCanvas.height };
    if (point.x < 28 || point.x > this.gpsMapCanvas.width - 28
      || point.y < 132 || point.y > this.gpsMapCanvas.height - 32) return false;
    this.gpsMapPanController = controller;
    this.gpsMapPanLastPoint = point;
    this.gpsMapPanLastAt = performance.now();
    return true;
  }

  isGpsMapPanning(controller) { return this.gpsMapPanController === controller; }

  endGpsMapPan(controller) {
    if (this.gpsMapPanController !== controller) return false;
    this.gpsMapPanController = null; this.gpsMapPanLastPoint = null; this.gpsMapPanLastAt = 0;
    return true;
  }

  updateGpsMapHoverZoom(inputSources, deltaSeconds = 1 / 90) {
    if (!this.gpsMapVisible || !this.gpsMapHoveredController || this.grabbedController) {
      this.gpsMapStickZoomAccumulator = 0;
      return;
    }
    const right = inputSources.find(source => source.handedness === 'right' && source.gamepad);
    const axes = right?.gamepad?.axes || [];
    const first = [Number(axes[0]) || 0, Number(axes[1]) || 0];
    const second = [Number(axes[2]) || 0, Number(axes[3]) || 0];
    const stick = Math.hypot(...second) > Math.hypot(...first) ? second : first;
    const vertical = Math.abs(stick[1]) > 0.2 ? stick[1] : 0;
    const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
    this.gpsMapStickZoomAccumulator += -vertical * elapsed * 1.5;
    const steps = Math.trunc(this.gpsMapStickZoomAccumulator);
    if (!steps) return;
    const previousZoom = this.gpsMap.zoom;
    this.gpsMap.setZoom(previousZoom + steps);
    this.gpsMapStickZoomAccumulator -= steps;
    if (this.gpsMap.zoom !== previousZoom) this.drawGpsMapWindow();
  }

  setPowerWindowVisible(visible) {
    this.powerWindowVisible = Boolean(visible);
    this.powerWindowRoot.visible = this.visible && this.powerWindowVisible;
    this.drawDashboard(); this.drawPowerWindow();
  }

  resizePowerWindow(factor) {
    const multiplier = Number(factor);
    if (!Number.isFinite(multiplier) || multiplier <= 0) return;
    this.powerWindowWidthScale = Math.max(.45, Math.min(5, this.powerWindowWidthScale * multiplier));
    this.powerWindowHeightScale = Math.max(.45, Math.min(5, this.powerWindowHeightScale * multiplier));
    this.applyPowerWindowSize(); this.drawPowerWindow();
  }

  resetPowerWindowPose() {
    this.powerWindowRoot.position.set(0, 0, 0); this.powerWindowRoot.quaternion.identity();
    this.powerWindowWorldAnchored = false; this.powerWindowWidthScale = 1; this.powerWindowHeightScale = 1;
    this.powerWindowHeadOffsetPosition.set(0, 0, 0); this.powerWindowHeadOffsetQuaternion.identity();
    this.powerWindowPose = null; this.applyPowerWindowSize();
    try { localStorage.removeItem('pandorabox.quest-power-window-pose.v1'); } catch {}
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
      localStorage.removeItem('pandorabox.quest-gps-map-pose.v3');
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
    ctx.fillStyle = '#9db6b4'; ctx.font = '500 14px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText('TRIGGER DRAG · PAN MAP    RIGHT STICK ↑/↓ · ZOOM    LATERAL GRIP · MOVE WINDOW', 34, 108, 1040);

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

  drawPowerWindow() {
    const ctx = this.powerWindowContext;
    if (!ctx) return;
    const width = this.powerWindowCanvas.width, height = this.powerWindowCanvas.height;
    const status = this.powerStatus || {}, metrics = this.systemMetrics || {};
    const cpu = metrics.cpu || {}, gpu = metrics.gpu || {}, memory = metrics.memory || {}, power = metrics.power || {};
    const battery = status.battery_estimate || {};
    const mode = String(status.mode || 'UNKNOWN').toUpperCase();
    const level = Number(battery.level_percent_est);
    const remainingWh = Number(battery.remaining_wh_est);
    const meanWatts = Number(status.rolling_60s_mean_w_by_mode?.[mode]?.mean_w);
    const watts = meanWatts > 0 ? meanWatts : Number(power.watts ?? status.board_input_w);
    const remainingMinutes = Number.isFinite(remainingWh) && watts > 0 ? remainingWh / watts * 60 : NaN;
    const format = (value, digits = 1, suffix = '') => value === null || value === undefined || value === '' || !Number.isFinite(Number(value))
      ? '—' : `${Number(value).toFixed(digits)}${suffix}`;
    const clampLevel = value => Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
    if (this.pendingBatteryLevel === null && Number.isFinite(level)) this.pendingBatteryLevel = clampLevel(level);
    this.powerWindowActionHitAreas = {};
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#071116'; ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#33505a'; ctx.lineWidth = 2; ctx.strokeRect(2, 2, width - 4, height - 4);
    const text = (value, x, y, size, color = '#e2efef', weight = 500, align = 'left') => {
      ctx.fillStyle = color; ctx.font = `${weight} ${size}px ui-sans-serif,system-ui`; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.fillText(String(value), x, y);
    };
    const button = (key, x, y, w, h, label, selected = false, accent = false) => {
      ctx.fillStyle = selected ? '#087d43' : accent ? '#12382f' : '#101d22';
      ctx.strokeStyle = selected ? '#45d38a' : accent ? '#65dfbd' : '#40575d'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 10); ctx.fill(); ctx.stroke();
      text(label, x + w / 2, y + h / 2, 20, selected ? '#ffffff' : '#d5e5e5', 650, 'center');
      this.powerWindowActionHitAreas[key] = { x, y, width: w, height: h };
    };
    const card = (x, y, w, h, title) => {
      ctx.fillStyle = '#0d1a20'; ctx.strokeStyle = '#29444d'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 14); ctx.fill(); ctx.stroke();
      text(title.toUpperCase(), x + 24, y + 30, 19, '#8fa9ac', 650);
    };
    text('COMPUTE + POWER', 36, 44, 30, '#e2efef', 750);
    text(this.powerWindowMessage || (metrics.available ? 'LIVE · 1 S' : 'PARTIAL TELEMETRY'), width - 36, 44, 16, this.powerWindowMessage ? '#f0ad77' : '#77d7b0', 600, 'right');
    text('POWER MODE', 36, 93, 17, '#8fa9ac', 650);
    ['DEV', 'ATTENTIVE', 'IDLE'].forEach((value, index) => button(`power-mode-${value}`, 190 + index * 290, 68, 270, 54, value === 'ATTENTIVE' ? 'Attentive' : value, mode === value));

    card(30, 146, width - 60, 226, 'Battery estimate');
    const gaugeX = 152, gaugeY = 270, gaugeRadius = 74, gaugeStart = -Math.PI / 2;
    ctx.beginPath(); ctx.arc(gaugeX, gaugeY, gaugeRadius, 0, Math.PI * 2); ctx.strokeStyle = '#253544'; ctx.lineWidth = 18; ctx.stroke();
    if (Number.isFinite(level) && level > 0) {
      ctx.beginPath(); ctx.arc(gaugeX, gaugeY, gaugeRadius, gaugeStart, gaugeStart + Math.PI * 2 * Math.max(0, Math.min(100, level)) / 100);
      ctx.strokeStyle = '#16855d'; ctx.lineWidth = 18; ctx.lineCap = 'butt'; ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(gaugeX, gaugeY, gaugeRadius - 13, 0, Math.PI * 2); ctx.fillStyle = '#0a0f1a'; ctx.fill();
    text(Number.isFinite(level) ? `${level.toFixed(0)}%` : '—%', gaugeX, gaugeY - 2, 38, '#e2edf5', 750, 'center');
    text('BATTERY', gaugeX, gaugeY + 30, 13, '#9aafc0', 650, 'center');
    text(Number.isFinite(remainingWh) ? `${remainingWh.toFixed(1)} Wh estimated` : 'Energy estimate unavailable', 270, 238, 19, '#a8bcbd');
    text(Number.isFinite(remainingMinutes) ? `~${Math.floor(remainingMinutes / 60)} h ${Math.round(remainingMinutes % 60)} min remaining` : 'Runtime estimate unavailable', 850, 210, 24, '#e2efef', 650);
    text(`Battery input · ${this.pendingBatteryLevel === null ? '—' : `${this.pendingBatteryLevel}%`}`, 850, 254, 19, '#a8bcbd', 550);
    button('power-battery-down', 850, 285, 100, 54, '−5');
    button('power-battery-up', 960, 285, 100, 54, '+5');
    button('power-battery-save', 1070, 285, 205, 54, 'Set level', false, true);
    button('power-battery-full', 1285, 285, 205, 54, 'Battery full');

    const metricGaugeY = 388, gaugeH = 310, gap = 12, gaugeW = (width - 60 - gap * 4) / 5;
    const drawGauge = (index, title, value, max, unit, color, foot) => {
      const x = 30 + index * (gaugeW + gap), cx = x + gaugeW / 2, cy = metricGaugeY + 144, radius = 62;
      card(x, metricGaugeY, gaugeW, gaugeH, title);
      ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.strokeStyle = '#253544'; ctx.lineWidth = 16; ctx.stroke();
      const valid = value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
      if (valid) {
        const fraction = Math.max(0, Math.min(1, Number(value) / Number(max)));
        if (fraction > 0) { ctx.beginPath(); ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * fraction); ctx.strokeStyle = color; ctx.lineWidth = 16; ctx.lineCap = 'butt'; ctx.stroke(); }
      }
      ctx.beginPath(); ctx.arc(cx, cy, radius - 12, 0, Math.PI * 2); ctx.fillStyle = '#0a0f1a'; ctx.fill();
      text(valid ? format(value, title === 'CPU LOAD' || title === 'MEMORY' ? 0 : 1) : '—', cx, cy, 32, '#e2edf5', 700, 'center');
      text(unit, cx + radius + 10, cy, 13, '#9aafc0', 600, 'left');
      text(foot, cx, metricGaugeY + 254, 14, '#9aafc0', 500, 'center');
    };
    const powerScale = Math.max(20, Math.ceil((Number(power.watts) || 0) / 10) * 10);
    drawGauge(0, 'CPU LOAD', cpu.utilization_percent, 100, '%', '#16855d', `Hottest CPU · ${format(cpu.temperature_c, 1, '°C')}`);
    drawGauge(1, 'CPU TEMP', cpu.temperature_c, 100, '°C', '#d58b32', 'Hottest reported CPU sensor · 0–100 °C');
    drawGauge(2, 'GPU TEMP', gpu.temperature_c, 100, '°C', '#d58b32', `${gpu.utilization_percent == null ? 'Load unavailable' : `${format(gpu.utilization_percent, 1, '%')} load`} · ${format(gpu.frequency_mhz, 0, 'MHz')}`);
    drawGauge(3, 'MEMORY', memory.used_percent, 100, '%', '#16855d', memory.available_mb == null || memory.total_mb == null
      ? 'Free memory unavailable' : `${(memory.available_mb / 1024).toFixed(1)} / ${(memory.total_mb / 1024).toFixed(1)} GB free`);
    drawGauge(4, 'BOARD INPUT', power.available ? power.watts : null, powerScale, 'W', '#1787a0', power.available
      ? `${format(power.voltage_v, 1, ' V')} · ${format(power.current_a, 2, ' A')}` : 'Onboard power monitor unavailable');

    const sensorText = `${this.sensorStatus.yolo || ''} ${this.sensorStatus.midas || ''} ${this.yoloRuntime || ''}`.toLowerCase();
    const htpActive = sensorText.includes('htp');
    const yoloMs = this.yoloInferenceMs == null ? '—' : `${Number(this.yoloInferenceMs).toFixed(0)} ms`;
    const midasMatch = String(this.sensorStatus.midas || '').match(/([\d.]+)\s*ms/i);
    const midasMs = midasMatch ? `${Number(midasMatch[1]).toFixed(0)} ms` : '—';
    const htpText = htpActive ? `ACTIVE · YOLOX ${yoloMs} HTP · MiDaS ${midasMs} HTP` : 'Utilization counter unavailable';
    const telemetry = [
      ['GPU UTILIZATION', gpu.utilization_percent == null ? 'Not exposed by kernel' : format(gpu.utilization_percent, 1, '%')],
      ['GPU CLOCK', format(gpu.frequency_mhz, 0, ' MHz')],
      ['QUALCOMM HTP', htpText],
      ['ENERGY SINCE BODY START', power.available ? format(power.energy_wh_session, 3, ' Wh') : 'Unavailable'],
    ];
    const stripY = 716, stripH = 260, stripGap = 12, stripW = (width - 60 - stripGap * 3) / 4;
    telemetry.forEach(([label, value], index) => {
      const x = 30 + index * (stripW + stripGap); card(x, stripY, stripW, stripH, label);
      text(value, x + 22, stripY + 106, 22, '#e2edf5', 650);
    });
    text('GPU / HTP load depends on counters exposed by the system kernel.', 34, 1004, 14, '#839c9f');
    button('power-window-size-down', 30, 1030, 130, 54, 'SIZE −');
    button('power-window-reset', 174, 1030, 190, 54, 'RESET WINDOW');
    button('power-window-close', width - 500, 1030, 160, 54, 'CLOSE');
    button('power-window-size-up', width - 320, 1030, 290, 54, 'SIZE +');
    this.powerWindowTexture.needsUpdate = true;
  }

  loadSavedPowerWindowPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-power-window-pose.v1') || 'null');
      if (!Array.isArray(saved?.position) || saved.position.length !== 3 || !Array.isArray(saved?.quaternion) || saved.quaternion.length !== 4) return;
      const values = [...saved.position, ...saved.quaternion, saved.widthScale, saved.heightScale].map(Number);
      if (!values.every(Number.isFinite) || values.slice(0, 3).some(value => Math.abs(value) > 20)) return;
      this.powerWindowHeadOffsetPosition.fromArray(saved.position);
      this.powerWindowHeadOffsetQuaternion.fromArray(saved.quaternion).normalize();
      this.powerWindowWidthScale = Math.max(.45, Math.min(5, Number(saved.widthScale) || 1));
      this.powerWindowHeightScale = Math.max(.45, Math.min(5, Number(saved.heightScale) || 1));
      this.powerWindowPose = saved; this.applyPowerWindowSize();
    } catch {}
  }

  applyPowerWindowSize() { this.powerWindowPanel?.scale.set(this.powerWindowWidthScale, this.powerWindowHeightScale, 1); }

  persistPowerWindowPose(xrCamera, force = false) {
    if (!xrCamera || !this.powerWindowWorldAnchored || (!force && performance.now() - this.lastPowerWindowPosePersistAt < 750)) return;
    xrCamera.getWorldPosition(this.scratchPosition); xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.powerWindowHeadOffsetPosition.copy(this.powerWindowRoot.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.powerWindowHeadOffsetQuaternion.copy(inverseHead).multiply(this.powerWindowRoot.quaternion).normalize();
    this.powerWindowPose = { position: this.powerWindowHeadOffsetPosition.toArray(), quaternion: this.powerWindowHeadOffsetQuaternion.toArray(), widthScale: this.powerWindowWidthScale, heightScale: this.powerWindowHeightScale };
    try { localStorage.setItem('pandorabox.quest-power-window-pose.v1', JSON.stringify(this.powerWindowPose)); this.lastPowerWindowPosePersistAt = performance.now(); } catch {}
  }

  loadSavedGpsMapPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-gps-map-pose.v3') || 'null');
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

  orientWindowToSphere(windowRoot) {
    this.verticalOffset.copy(windowRoot.position).sub(this.sphereCenter);
    const radius = Math.max(0.01, this.verticalOffset.length());
    const horizontal = Math.hypot(this.verticalOffset.x, this.verticalOffset.z);
    const azimuthX = horizontal > 1e-4 ? this.verticalOffset.x / horizontal : 0;
    const azimuthZ = horizontal > 1e-4 ? this.verticalOffset.z / horizontal : 1;
    const elevation = this.THREE.MathUtils.clamp(Math.atan2(this.verticalOffset.y, horizontal), -Math.PI * 0.39, Math.PI * 0.39);
    this.surfaceDirection.set(azimuthX * Math.cos(elevation), Math.sin(elevation), azimuthZ * Math.cos(elevation));
    this.orientationTarget.copy(this.sphereCenter).addScaledVector(this.surfaceDirection, radius);
    this.facingMatrix.lookAt(this.sphereCenter, this.orientationTarget, this.worldUp);
    windowRoot.quaternion.setFromRotationMatrix(this.facingMatrix);
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
      localStorage.setItem('pandorabox.quest-gps-map-pose.v3', JSON.stringify(this.gpsMapPose));
      this.lastGpsMapPosePersistAt = performance.now();
    } catch {}
  }

  updatePowerStatus(status) {
    this.powerStatus = status || {};
    const mode = String(status?.mode || 'UNKNOWN').toUpperCase();
    const estimate = status?.battery_estimate || {};
    const level = Number(estimate.level_percent_est);
    const remainingWh = Number(estimate.remaining_wh_est);
    const modeMean = Number(status?.rolling_60s_mean_w_by_mode?.[mode]?.mean_w);
    const watts = modeMean > 0 ? modeMean : Number(status?.board_input_w);
    this.sensorStatus.power = Number.isFinite(level) ? `${mode} · ~${Math.round(level)}%` : mode;
    this.sensorStatus.runtime = Number.isFinite(remainingWh) && watts > 0
      ? `${Math.floor(remainingWh / watts)}H ${Math.floor((remainingWh / watts % 1) * 60)}M EST.` : '—';
    this.drawDashboard();
    this.drawPowerWindow();
  }

  updateSystemMetrics(metrics) {
    this.systemMetrics = metrics || {};
    this.drawPowerWindow();
  }

  setPowerWindowMessage(message = '') {
    this.powerWindowMessage = String(message || '');
    this.drawPowerWindow();
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
    this.yoloRuntime = String(result?.runtime || result?.device || '').toLowerCase();
    const inferenceMs = Number(result?.inference_ms ?? result?.latency_ms);
    this.yoloInferenceMs = Number.isFinite(inferenceMs) ? inferenceMs : null;
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
      ? `${this.grabbedWindow === 'gps-map' ? 'GPS MAP' : this.grabbedWindow === 'power' ? 'COMPUTE + POWER' : this.grabbedWindow === 'fnk' ? 'FNK CONTROL' : 'HUD'} GRABBED · PICKED POINT STAYS UNDER POINTER · STICKS RESIZE / ADJUST DISTANCE`
      : 'HOLD LATERAL GRIP TO MOVE WINDOWS · FRONT TRIGGER SELECTS BUTTONS / DRAGS DENSITY', margin + 8, height - 14);
    ctx.textAlign = 'right';
    ctx.fillText(this.following ? 'CAMERA FOLLOW · BODY' : 'SCENE VIEW · FIXED', width - margin - 8, height - 14);
    ctx.restore();
    this.texture.needsUpdate = true;
  }

  drawHudActions(ctx) {
    this.actionHitAreas = {};
    const buttonY = this.logicalHeight - 62;
    const simulationReady = this.frame?.mode === 'sim';
    const simulationRunning = Boolean(this.frame?.running);
    const simulationLabel = simulationRunning ? 'PAUSE SIMULATION' : 'START SIMULATION';
    const mapX = this.logicalWidth / 2 - 664;
    const powerX = this.logicalWidth / 2 - 472;
    const simulationX = this.logicalWidth / 2 - 280;
    const sensorX = this.logicalWidth / 2 - 20;
    const fnkX = this.logicalWidth / 2 + 240;
    const exitX = this.logicalWidth / 2 + 462;
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
    drawButton('gps-map', mapX, 180, this.gpsMapVisible ? 'CLOSE GPS MAP' : 'GPS MAP', 'rgba(31, 73, 77, .96)', '#78d8d0', '#e5fffa');
    drawButton('power-window', powerX, 180, this.powerWindowVisible ? 'CLOSE POWER' : 'COMPUTE + POWER', 'rgba(31, 73, 77, .96)', '#78d8d0', '#e5fffa');
    drawButton('simulation', simulationX, 248, this.actionBusy ? 'PLEASE WAIT' : simulationReady ? simulationLabel : 'SIMULATION OFFLINE', 'rgba(31, 105, 78, .96)', '#75edbd', '#e5fff3', simulationReady);
    drawButton('sensor-mode', sensorX, 248, this.sceneMode === 'sensors' ? 'SHOW SIMULATION' : 'SHOW LIVE SENSORS', 'rgba(31, 73, 77, .96)', '#78d8d0', '#e5fffa');
    drawButton('fnk-control', fnkX, 206, this.fnkVisible ? 'CLOSE GAIT LAB' : 'HEXAPOD GAIT LAB', 'rgba(31, 105, 78, .96)', '#75edbd', '#e5fff3');
    drawButton('exit', exitX, 206, this.actionBusy ? 'PLEASE WAIT' : 'EXIT VR', 'rgba(91, 53, 42, .96)', '#f0a888', '#fff0e8');
    this.sensorPointDensityHitArea = null;
    if (this.sceneMode === 'sensors') {
      const sliderX = this.logicalWidth / 2 + 850;
      const sliderWidth = this.logicalWidth - sliderX - 30;
      const trackY = buttonY - 18;
      const ratio = (this.sensorPointDensity - 60) / 100;
      const targetStep = Math.max(3, Math.ceil(640 / this.sensorPointDensity));
      const estimatedPoints = Math.ceil(640 / targetStep) * Math.ceil(480 / targetStep);
      this.sensorPointDensityHitArea = {
        x: sliderX - 18, y: trackY - 28, width: sliderWidth + 36, height: 58,
      };
      ctx.fillStyle = '#b7d2c5'; ctx.font = '600 17px ui-monospace, monospace';
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText('3D DOT DENSITY', sliderX, trackY - 17);
      ctx.textAlign = 'right'; ctx.fillStyle = '#e6fff4';
      ctx.fillText(`${estimatedPoints.toLocaleString()} PTS`, sliderX + sliderWidth, trackY - 17);
      ctx.fillStyle = '#24443a'; ctx.fillRect(sliderX, trackY, sliderWidth, 8);
      ctx.fillStyle = '#5be2bd'; ctx.fillRect(sliderX, trackY, sliderWidth * ratio, 8);
      for (let tick = 0; tick <= 10; tick += 1) {
        const tickX = sliderX + sliderWidth * tick / 10;
        ctx.fillStyle = '#9dc9b3'; ctx.fillRect(tickX - 1, trackY - 4, 2, 16);
      }
      const thumbX = sliderX + sliderWidth * ratio;
      ctx.beginPath(); ctx.arc(thumbX, trackY + 4, 12, 0, Math.PI * 2);
      ctx.fillStyle = '#e8fff4'; ctx.fill(); ctx.strokeStyle = '#36c99f'; ctx.lineWidth = 3; ctx.stroke();
      ctx.textAlign = 'left'; ctx.fillStyle = '#829d8d'; ctx.font = '500 12px ui-monospace, monospace';
      ctx.fillText('SPARSE', sliderX, trackY + 18);
      ctx.textAlign = 'right'; ctx.fillText('DENSE', sliderX + sliderWidth, trackY + 18);
    }
  }

  loadSavedFnkPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-fnk-pose.v1') || 'null');
      if (!Array.isArray(saved?.position) || saved.position.length !== 3
        || !Array.isArray(saved?.quaternion) || saved.quaternion.length !== 4) return;
      const values = [...saved.position, ...saved.quaternion, saved.widthScale, saved.heightScale].map(Number);
      if (!values.every(Number.isFinite) || values.slice(0, 3).some(value => Math.abs(value) > 20)) return;
      this.fnkHeadOffsetPosition.fromArray(saved.position);
      this.fnkHeadOffsetQuaternion.fromArray(saved.quaternion).normalize();
      this.fnkWidthScale = Math.max(.55, Math.min(3.5, Number(saved.widthScale) || 1));
      this.fnkHeightScale = Math.max(.55, Math.min(3.5, Number(saved.heightScale) || 1));
      this.fnkPose = saved;
      this.fnkPanel.scale.set(this.fnkWidthScale, this.fnkHeightScale, 1);
    } catch {}
  }

  persistFnkPose(xrCamera, force = false) {
    if (!xrCamera || !this.fnkWorldAnchored || (!force && performance.now() - this.lastFnkPosePersistAt < 750)) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.fnkHeadOffsetPosition.copy(this.fnkRoot.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.fnkHeadOffsetQuaternion.copy(inverseHead).multiply(this.fnkRoot.quaternion).normalize();
    this.fnkPose = {
      position: this.fnkHeadOffsetPosition.toArray(),
      quaternion: this.fnkHeadOffsetQuaternion.toArray(),
      widthScale: this.fnkWidthScale,
      heightScale: this.fnkHeightScale,
    };
    try { localStorage.setItem('pandorabox.quest-fnk-pose.v1', JSON.stringify(this.fnkPose)); } catch {}
    this.lastFnkPosePersistAt = performance.now();
  }

  setSensorPointDensityAt(canvasX) {
    const area = this.sensorPointDensityHitArea;
    if (!area) return false;
    const ratio = Math.max(0, Math.min(1, (canvasX - area.x - 18) / (area.width - 36)));
    const next = 60 + Math.round(ratio * 10) * 10;
    if (next === this.sensorPointDensity) return true;
    this.sensorPointDensity = next;
    this.drawDashboard();
    this.onSensorPointDensityChange?.(next);
    return true;
  }

  beginSensorPointDensityDrag(controller, raycaster) {
    if (!this.visible || this.sceneMode !== 'sensors') return false;
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObject(this.panel, false)[0];
    if (!hit?.uv || !this.sensorPointDensityHitArea) return false;
    const x = hit.uv.x * this.logicalWidth;
    const y = (1 - hit.uv.y) * this.logicalHeight;
    const area = this.sensorPointDensityHitArea;
    if (x < area.x || x > area.x + area.width || y < area.y || y > area.y + area.height) return false;
    this.sensorDensityDragController = controller;
    this.setSensorPointDensityAt(x);
    return true;
  }

  endSensorPointDensityDrag(controller) {
    if (this.sensorDensityDragController !== controller) return false;
    this.sensorDensityDragController = null;
    return true;
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
    if (this.powerWindowRoot) this.powerWindowRoot.visible = this.visible && this.powerWindowVisible;
    if (this.fnkRoot) this.fnkRoot.visible = this.visible && this.fnkVisible;
  }

  setFnkVisible(visible) {
    this.fnkVisible = Boolean(visible);
    if (!this.fnkVisible) this.setFnkTeleop(false);
    else { this.fnkSceneInputSelected = false; this.fnkControllerInput = null; }
    this.fnkRoot.visible = this.visible && this.fnkVisible;
    this.drawDashboard();
    this.drawFnkControlWindow();
  }

  updateFnkHardwareStatus(status) {
    this.fnkHardwareStatus = status || null;
    if (status?.estimated_leg_state) this.fnkLegState = status.estimated_leg_state;
    if (!this.fnkBusy && !this.fnkMessage.includes('ACK')) {
      this.fnkMessage = status?.connected
        ? status.firmware_profile === 'custom_fnhr_ascii_v2'
          ? 'BOARD ONLINE · FNHR STATE IS AN ESTIMATE'
          : `CONNECTED · ${status.firmware_profile || 'INCOMPATIBLE FIRMWARE'}`
        : `BOARD OFFLINE · ${status?.last_error || 'waiting for USB'}`;
    }
    this.drawFnkControlWindow();
  }

  selectFnkLeg(leg) {
    this.fnkLeg = Math.max(1, Math.min(6, Number(leg) || 1));
    this.drawFnkControlWindow();
  }

  toggleFnkBoardOnly() {
    this.fnkBoardOnlyConfirmed = !this.fnkBoardOnlyConfirmed;
    this.drawFnkControlWindow();
  }

  setFnkTab(tab) {
    const next = ['control', 'twist', 'calibration', 'installation'].includes(tab) ? tab : 'control';
    if (next !== this.fnkTab) this.fnkGyroBaseline = null;
    this.fnkTab = next;
    this.drawFnkControlWindow();
  }

  setFnkTeleop(enabled) {
    this.fnkTeleopArmed = Boolean(enabled);
    this.fnkSceneInputSelected = false;
    this.fnkGyroBaseline = null;
    const hw=this.fnkHardwareStatus||{};
    this.fnkMessage = this.fnkTeleopArmed
      ? (hw.connected&&hw.actuation_enabled?'ROBOT INPUT SELECTED · LEFT MENU RETURNS TO SCENE':'ROBOT INPUT SELECTED · HARDWARE ACTUATION BLOCKED')
      : 'PREVIEW INPUT SELECTED · QUEST STICKS CONTROL THE GAIT PREVIEW';
    this.drawFnkControlWindow();
  }

  toggleFnkTeleop() { this.setFnkTeleop(!this.fnkTeleopArmed); }

  updateFnkControllerOrientation(orientation) {
    if (!orientation || orientation.length !== 4) return;
    this.fnkGyroCurrent.set(orientation[0], orientation[1], orientation[2], orientation[3]).normalize();
    if (this.fnkVisible && this.fnkTab === 'twist' && !this.fnkGyroBaseline) {
      this.fnkGyroBaseline = this.fnkGyroCurrent.clone();
      this.fnkGyroPoseBase = { ...(this.fnkPoseValues || { x: 0, y: 0, z: 24, roll: 0, pitch: 0, yaw: 0 }) };
    }
  }

  disarmFnkTeleop(message = 'DISARMED · NO DRIVE COMMANDS') {
    this.fnkTeleopArmed = false;
    this.fnkGyroBaseline = null;
    this.fnkSceneInputSelected = true;
    this.fnkMessage = message;
    this.drawFnkControlWindow();
  }

  async sendFnkManualControl(payload, gyroTarget = null) {
    if (!this.fnkTeleopArmed || this.fnkDriveInFlight) return;
    const hw=this.fnkHardwareStatus||{};
    if(hw.connected!==true||hw.firmware_profile!=='custom_fnhr_ascii_v2'||hw.actuation_enabled!==true){this.fnkMessage='COMMAND BLOCKED · CHECK FNK USB / ACTUATION SETTING';this.drawFnkControlWindow();return;}
    this.fnkDriveInFlight = true;
    this.fnkLastDriveAt = performance.now();
    this.fnkMessage = `SENDING ${payload.mode.toUpperCase()} STEP · KEEP DEADMAN HELD`;
    this.drawFnkControlWindow();
    try {
      const response = await fetch('/plugins/fnk0031_wifi/manual-control', {
        method: 'POST', cache: 'no-store', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...payload, deadman: true }),
      });
      const result = await response.json();
      if (!response.ok || !result?.ok) throw new Error(result?.error || `HTTP ${response.status}`);
      if (gyroTarget && this.fnkGyroBaseline) this.fnkGyroBaseline.copy(gyroTarget);
      this.fnkMessage = `${result.ack} · OPERATOR COMMAND ACKNOWLEDGED`;
    } catch (error) {
      this.disarmFnkTeleop(`DRIVE DISARMED · ${error.message}`);
    } finally {
      this.fnkDriveInFlight = false;
      this.drawFnkControlWindow();
    }
  }

  sendFnkPadAction(action) {
    if (action === 'stop') {
      this.fnkPreviewKeys = {};
      this.fnkPreviewDemo = false;
      this.fnkControllerInput = null;
      this.fnkMessage = this.fnkTeleopArmed
        ? 'PREVIEW STOPPED · THE CURRENT FNHR GAIT STEP MAY FINISH'
        : 'STOP · WALK PREVIEW INPUT CLEARED';
      this.drawFnkControlWindow();
      return;
    }
    const keyForAction = { forward: 'w', backward: 's', left: 'a', right: 'd', 'turn-left': 'q', 'turn-right': 'e' };
    const key = keyForAction[action];
    if (!key) return;
    this.fnkPreviewKeys ||= {};
    this.fnkPreviewDemo = false;
    this.fnkPreviewKeys[key] = !this.fnkPreviewKeys[key];
    const enabled = this.fnkPreviewKeys[key];
    const v = 24 * this.fnkSpeed;
    const commands = {
      forward: { x: 0, y: v, angle: 0 }, backward: { x: 0, y: -v, angle: 0 },
      left: { x: -v, y: 0, angle: 0 }, right: { x: v, y: 0, angle: 0 },
      'turn-left': { x: 0, y: 0, angle: -12 * this.fnkSpeed },
      'turn-right': { x: 0, y: 0, angle: 12 * this.fnkSpeed },
    };
    const params = commands[action];
    this.fnkControllerInput = null;
    const hw=this.fnkHardwareStatus||{};
    if (!enabled) {
      this.fnkMessage = `WALK INPUT CLEARED · ${key.toUpperCase()}`;
    } else if (!this.fnkTeleopArmed) {
      this.fnkMessage = `WALK PREVIEW · ${key.toUpperCase()} LATCHED · COMBINE DIRECTIONS`;
    } else if(hw.connected!==true||hw.firmware_profile!=='custom_fnhr_ascii_v2'||hw.actuation_enabled!==true){
      this.fnkMessage='WALK PREVIEW · PHYSICAL COMMAND BLOCKED: FNK USB / ACTUATION DISABLED';
    } else {
      void this.sendFnkManualControl({ mode: 'crawl', ...params });
    }
    this.drawFnkControlWindow();
  }

  updateFnkStickControl(inputSources = []) {
    const right = inputSources.find(source => source.handedness === 'right');
    const left = inputSources.find(source => source.handedness === 'left');
    if (!this.fnkVisible || this.fnkSceneInputSelected) return false;
    const read = source => {
      const axes = source?.gamepad?.axes || [];
      const a = [Number(axes[0]) || 0, Number(axes[1]) || 0];
      const b = [Number(axes[2]) || 0, Number(axes[3]) || 0];
      return Math.hypot(...b) > Math.hypot(...a) ? b : a;
    };
    const dz = value => Math.abs(value) < 0.18 ? 0 : Math.sign(value) * (Math.abs(value) - 0.18) / 0.82;
    const [rx, ry] = read(right).map(dz);
    const [lx] = read(left).map(dz);
    const hw=this.fnkHardwareStatus||{};
    const crawlX = rx * 42;
    const crawlY = -ry * 42;
    const crawlScale = Math.max(1, Math.hypot(crawlX, crawlY) / 42);
    let move;
    let gyroTarget = null;
    let trigger = 0;
    if (this.fnkTab === 'twist') {
      if (!this.fnkGyroBaseline) { this.fnkControllerInput=null; return true; }
      this.fnkGyroDelta.copy(this.fnkGyroBaseline).invert().multiply(this.fnkGyroCurrent).normalize();
      // Three.js Quaternion has no getAxisAngle() method. Extract the shortest
      // rotation explicitly so controller motion cannot throw inside XR's frame loop.
      const q = this.fnkGyroDelta, hemisphere = q.w < 0 ? -1 : 1;
      const qw = Math.max(-1, Math.min(1, q.w * hemisphere));
      const radians = 2 * Math.acos(qw), sinHalf = Math.sqrt(Math.max(0, 1 - qw * qw));
      if (sinHalf < 1e-6) this.fnkGyroAxis.set(0, 0, 0);
      else this.fnkGyroAxis.set(q.x * hemisphere / sinHalf, q.y * hemisphere / sinHalf, q.z * hemisphere / sinHalf);
      const degrees = radians * 180 / Math.PI;
      const rotationScale = Math.min(1, 15 / Math.max(degrees, 0.001));
      trigger = Number(right?.gamepad?.buttons?.[0]?.value) || 0;
      const rxDeg=degrees < 1.5 ? 0 : this.fnkGyroAxis.x*degrees*rotationScale,ryDeg=degrees < 1.5 ? 0 : this.fnkGyroAxis.y*degrees*rotationScale,rzDeg=degrees < 1.5 ? 0 : this.fnkGyroAxis.z*degrees*rotationScale;
      const base=this.fnkGyroPoseBase||{x:0,y:0,z:24,roll:0,pitch:0,yaw:0};
      this.fnkPoseValues={x:base.x+rx*30,y:base.y-ry*30,z:base.z+trigger*21,roll:base.roll+rxDeg,pitch:base.pitch+ryDeg,yaw:base.yaw+rzDeg};
      this.fnkControllerInput={x:rx,y:-ry,angle:rzDeg/15};
      move = { mode: 'twist', x: rx * 30, y: -ry * 30, z: 24+trigger*21,
        rx: rxDeg, ry: ryDeg, rz: rzDeg };
      if (degrees >= 1.5) gyroTarget = this.fnkGyroCurrent.clone();
      if (!gyroTarget && Math.max(Math.abs(rx), Math.abs(ry), trigger) < 0.12) { this.fnkControllerInput=null; return true; }
    } else {
      move = { mode: 'crawl', x: crawlX / crawlScale, y: crawlY / crawlScale, angle: -lx * 18 };
      this.fnkControllerInput={x:rx,y:ry,angle:-lx};
      if (Math.max(Math.abs(rx), Math.abs(ry), Math.abs(lx)) < 0.12) this.fnkControllerInput=null;
    }
    const hasInput = this.fnkTab === 'twist'
      ? Math.max(Math.abs(rx), Math.abs(ry), trigger || 0, gyroTarget ? 1 : 0) >= 0.12
      : Math.max(Math.abs(rx), Math.abs(ry), Math.abs(lx)) >= 0.12;
    if (!hasInput) return true;
    if(hw.connected!==true||hw.firmware_profile!=='custom_fnhr_ascii_v2'||hw.actuation_enabled!==true){
      const pose=this.fnkTab==='twist'?`ROLL ${move.rx.toFixed(1)}° · PITCH ${move.ry.toFixed(1)}° · YAW ${move.rz.toFixed(1)}°`:`X ${move.x.toFixed(2)} · Y ${move.y.toFixed(2)} · TURN ${move.angle.toFixed(2)}`;
      this.fnkMessage=`CONTROLLER PREVIEW · ${pose}${this.fnkTeleopArmed?' · HARDWARE COMMANDS BLOCKED':''}`;
      return true;
    }
    if (this.fnkDriveInFlight || performance.now() - this.fnkLastDriveAt < 1600) return true;
    void this.sendFnkManualControl(move, gyroTarget);
    return true;
  }

  async sendFnkLegTest(direction) {
    if (this.fnkBusy || !this.fnkBoardOnlyConfirmed) return;
    this.fnkBusy = true;
    this.fnkMessage = `SENDING ${direction === 'lift' ? '+5' : '−5'} mm · LEG ${this.fnkLeg}`;
    this.drawFnkControlWindow();
    try {
      const response = await fetch('/plugins/fnk0031_wifi/leg-test', {
        method: 'POST',
        cache: 'no-store',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leg: this.fnkLeg, direction, board_only_confirmed: true }),
      });
      const result = await response.json();
      if (!response.ok || !result?.ok) throw new Error(result?.error || `HTTP ${response.status}`);
      this.fnkLegState = result.estimated_leg_state || this.fnkLegState;
      const delta = Number(result.reported_delta_z_mm);
      this.fnkMessage = `${result.ack || 'ACK'} · L${this.fnkLeg} · Z ${Number.isFinite(delta) ? `${delta > 0 ? '+' : ''}${delta.toFixed(1)} mm` : 'updated'} · ESTIMATE ONLY`;
    } catch (error) {
      this.fnkMessage = `COMMAND REJECTED · ${error.message}`;
    } finally {
      this.fnkBusy = false;
      this.drawFnkControlWindow();
    }
  }

  drawFnkGaitLab() {
    const c=this.fnkContext,w=this.fnkCanvas.width,h=this.fnkCanvas.height;if(!c)return;
    c.clearRect(0,0,w,h);c.fillStyle='#0a1018';c.fillRect(0,0,w,h);c.strokeStyle='#2b405c';c.lineWidth=3;c.strokeRect(3,3,w-6,h-6);
    const hw=this.fnkHardwareStatus||{},ready=hw.connected===true&&hw.firmware_profile==='custom_fnhr_ascii_v2';this.fnkActionHitAreas={};
    const btn=(key,x,y,bw,bh,label,on=true,sel=false)=>{c.globalAlpha=on?1:.48;c.fillStyle=sel?'#174e36':'#0d141d';c.strokeStyle=sel?'#4dff88':'#40536a';c.lineWidth=3;c.beginPath();c.roundRect(x,y,bw,bh,12);c.fill();c.stroke();c.fillStyle='#d6e4f0';c.font='650 24px ui-monospace,monospace';c.textAlign='center';c.textBaseline='middle';c.fillText(label,x+bw/2,y+bh/2,bw-16);c.globalAlpha=1;this.fnkActionHitAreas[key]={x,y,width:bw,height:bh,enabled:on};};
    const card=(x,y,bw,bh,label)=>{c.fillStyle='#0d141d';c.fillRect(x,y,bw,bh);c.strokeStyle='#2b405c';c.strokeRect(x,y,bw,bh);c.fillStyle='#8fa3b8';c.font='700 21px ui-monospace,monospace';c.textAlign='left';c.fillText(label.toUpperCase(),x+22,y+33);};
    c.fillStyle='#d6e4f0';c.font='700 38px system-ui';c.textAlign='left';c.fillText('Hexapod Gait Lab',30,54);
    c.fillStyle=ready?'#4dff88':'#ffb020';c.font='600 21px ui-monospace,monospace';c.fillText(`${ready?'FNK0031 · CONNECTED':'FNK0031 · BOARD OFFLINE'} · ACTUATION ${hw.actuation_enabled?'ON':'OFF'}`,32,100);
    // Left column: original Gait Lab stage, six-row gait cycle, then planted-foot pose view.
    card(24,135,990,520,'Top view · front is up');
    const cx=519,cy=405;c.fillStyle='#0b121b';c.fillRect(40,170,958,465);c.strokeStyle='#26384e';c.lineWidth=1;
    for(let n=1;n<=5;n++){c.beginPath();c.arc(cx,cy,n*67,0,Math.PI*2);c.stroke();}
    c.fillStyle='#d6e4f0';c.beginPath();c.roundRect(cx-48,cy-90,96,180,18);c.fill();c.fillStyle='#0a1018';c.beginPath();c.moveTo(cx-18,cy-90);c.lineTo(cx+18,cy-90);c.lineTo(cx,cy-116);c.fill();
    const phase=this.fnkPreviewPaused&&Number.isFinite(this.fnkPreviewPhase)?this.fnkPreviewPhase:((this.fnkPreviewPhase=((performance.now()/500)%1))), gaitOffset=this.fnkGait==='tripod'?[0,.5,0,.5,0,.5]:this.fnkGait==='ripple'?[.667,.167,.333,.833,0,.5]:[.333,.833,.167,.667,0,.5];
    for(let i=0;i<6;i++){const side=i%2?1:-1,row=Math.floor(i/2)-1,hipX=cx+side*44,hipY=cy+row*50,footX=cx+side*155,footY=hipY+row*35,legPhase=(phase+gaitOffset[i])%1,swing=legPhase<.33;
      c.strokeStyle=swing?'#ffb020':'#4dff88';c.lineWidth=8;c.setLineDash(swing?[12,8]:[]);c.beginPath();c.moveTo(hipX,hipY);c.lineTo((hipX+footX)/2,footY-10);c.lineTo(footX,footY);c.stroke();c.setLineDash([]);c.fillStyle=swing?'#0d141d':'#4dff88';c.beginPath();c.arc(footX,footY,10,0,Math.PI*2);c.fill();c.strokeStyle=swing?'#ffb020':'#4dff88';c.stroke();c.fillStyle='#8fa3b8';c.font='16px ui-monospace,monospace';c.textAlign='center';c.fillText(['L1','R1','L2','R2','L3','R3'][i],footX,footY+26);}
    card(24,670,990,340,'Gait cycle · one row per leg');
    const duty=this.fnkGait==='wave'?.833:this.fnkGait==='ripple'?.667:.5;
    for(let i=0;i<6;i++){const yy=720+i*38,off=gaitOffset[i];c.fillStyle='#8fa3b8';c.font='17px ui-monospace,monospace';c.textAlign='left';c.fillText(['L1','R1','L2','R2','L3','R3'][i],48,yy+16);c.fillStyle='#4dff88';c.fillRect(100,yy,850,24);c.strokeStyle='#ffb020';c.lineWidth=3;c.setLineDash([8,6]);const sx=100+off*850,sw=(1-duty)*850;c.strokeRect(sx,yy,sw,24);if(sx+sw>950)c.strokeRect(100,yy,sx+sw-950,24);c.setLineDash([]);const marker=100+((phase+off)%1)*850;c.strokeStyle='#d6e4f0';c.lineWidth=3;c.beginPath();c.moveTo(marker,yy-4);c.lineTo(marker,yy+29);c.stroke();}
    c.fillStyle='#8fa3b8';c.font='16px ui-monospace,monospace';c.fillText(`STANCE ${(duty*100).toFixed(0)}% · ${this.fnkGait.toUpperCase()} · filled green=stance · dashed amber=swing`,48,968);
    card(24,1025,990,390,'Body tilt · feet planted');
    const bodyY=1270,roll=(this.fnkGyroDelta?.x||0)*20,pitch=(this.fnkGyroDelta?.y||0)*20;
    for(const [gx,label,tilt] of [[240,'FRONT · ROLL',roll],[650,'SIDE · PITCH',pitch]]){c.strokeStyle='#40536a';c.lineWidth=3;c.beginPath();c.moveTo(gx-150,bodyY+65);c.lineTo(gx+150,bodyY+65);c.stroke();c.fillStyle='#4dff88';c.beginPath();c.arc(gx-140,bodyY+65,7,0,Math.PI*2);c.arc(gx+140,bodyY+65,7,0,Math.PI*2);c.fill();c.strokeStyle='#d6e4f0';c.lineWidth=12;c.beginPath();c.moveTo(gx-72,bodyY-tilt);c.lineTo(gx+72,bodyY+tilt);c.stroke();c.fillStyle='#8fa3b8';c.font='17px ui-monospace,monospace';c.textAlign='center';c.fillText(label,gx,bodyY+115);}
    // Right column: original Mode, movement pad, gait, speed and six leg status rows.
    card(1038,135,738,950,'Controls');c.fillStyle='#8fa3b8';c.font='700 20px ui-monospace,monospace';c.textAlign='left';c.fillText('MODE',1060,190);
    btn('tab-control',1060,210,332,74,'WALK',true,this.fnkTab==='control');btn('tab-twist',1404,210,350,74,'TWIST BODY',true,this.fnkTab==='twist');
    if(this.fnkTab==='control'){
      c.fillText('MOVEMENT · RIGHT STICK drives in Robot mode',1060,333);
      const p=[['turn-left','Q · TURN LEFT'],['forward','W · FORWARD'],['turn-right','E · TURN RIGHT'],['left','A · LEFT'],['backward','S · BACKWARD'],['right','D · RIGHT']];p.forEach(([k,l],i)=>{const col=i%3,row=Math.floor(i/3);btn(`drive-${k}`,1060+col*230,360+row*104,220,92,l,true);});
      btn('drive-stop',1060,574,220,56,'STOP',true);btn('demo-preview',1290,574,220,56,'DEMO',true,this.fnkPreviewDemo);btn('pause-preview',1520,574,234,56,this.fnkPreviewPaused?'RESUME':'PAUSE',true,this.fnkPreviewPaused);
      c.fillText('GAIT · PREVIEW ONLY',1060,680);['tripod','ripple','wave'].forEach((g,i)=>btn(`gait-${g}`,1060+i*230,700,220,62,g.toUpperCase(),true,this.fnkGait===g));
      c.fillText(`SPEED ${this.fnkSpeed.toFixed(2)}×`,1060,805);btn('speed-down',1060,825,220,60,'−');btn('speed-up',1290,825,220,60,'+');
      c.fillText('Demo and gait diagram are preview only; FNHR gait is firmware-defined.',1060,920,720);
      btn('teleop-arm',1060,975,332,76,this.fnkTeleopArmed?'ROBOT CONTROL · ON':'ROBOT CONTROL · OFF',true,this.fnkTeleopArmed);btn('teleop-stop',1404,975,350,76,'SCENE CONTROL',true);
    }else if(this.fnkTab==='twist'){
      c.fillText('BODY POSE · LEFT CONTROLLER ORIENTATION twists the body',1060,350);
      c.fillText('RIGHT STICK shifts X/Y · RIGHT TRIGGER changes body height',1060,405);
      c.fillText('Relative WebXR controller rotation is sent as bounded FNHR TwistBody steps.',1060,460,680);
      c.fillText('Front and side views show the requested body tilt over planted feet.',1060,510,680);
      btn('center-preview',1060,590,332,64,'CENTER PREVIEW',true);btn('sweep-preview',1404,590,350,64,'SWEEP DEMO · PREVIEW',true,this.fnkPreviewDemo);
      btn('teleop-arm',1060,975,332,76,this.fnkTeleopArmed?'ROBOT CONTROL · ON':'ROBOT CONTROL · OFF',true,this.fnkTeleopArmed);btn('teleop-stop',1404,975,350,76,'SCENE CONTROL',true);
    }else{
      c.fillText(this.fnkTab==='calibration'?'LEG STATUS · FNHR COMMAND ESTIMATES, NOT MEASURED FEEDBACK':'FNHR CUSTOM USB · 115200 BAUD',920,350);
    }
    card(1038,1100,738,315,'Leg status');
    labels.forEach((name,i)=>{const l=this.fnkLegState?.legs?.[i],col=i%2,row=Math.floor(i/2),x=1060+col*350,y=1155+row*78;c.fillStyle='#d6e4f0';c.font='15px ui-monospace,monospace';c.textAlign='left';c.fillText(l?`${name} · FOOT ${l.foot_position_mm?.map(n=>Number(n).toFixed(0)).join('/')||'—'} mm · JOINT ${l.joint_angles_deg?.map(n=>Number(n).toFixed(0)).join('/')||'—'}°`:`${name} · WAITING FOR FNHR ESTIMATE`,x,y,330);c.fillStyle='#2b405c';c.fillRect(x,y+13,320,8);if(l){c.fillStyle='#4dff88';c.fillRect(x,y+13,Math.min(320,Math.max(0,Number(l.foot_position_mm?.[2])||0)*3),8);}});
    c.fillStyle='#8fa3b8';c.font='17px ui-monospace,monospace';c.textAlign='left';c.fillText(`${this.fnkMessage} · estimated commanded state`,30,h-24,w-60);this.fnkTexture.needsUpdate=true;
  }

  drawFnkGaitLabExact() {
    const c = this.fnkContext, w = this.fnkCanvas.width, h = this.fnkCanvas.height;
    if (!c) return;
    const C = { bg: '#0a1018', panel: '#0d141d', stage: '#0b121b', line: '#2b405c', text: '#d6e4f0', muted: '#8fa3b8', swing: '#b85b00', stance: '#087d43', statusTrack: '#c4cedc', statusFill: '#43566e', modeIdle: '#f8fafc', modeInk: '#10243a' };
    const legs = [['L1', -1, -34], ['R1', 1, -34], ['L2', -1, 0], ['R2', 1, 0], ['L3', -1, 34], ['R3', 1, 34]];
    const twist = this.fnkTab === 'twist', gait = this.fnkGait || 'tripod';
    const gaitSpec = {
      tripod: { duty: .5, offsets: [0, .5, .5, 0, 0, .5] },
      ripple: { duty: 2 / 3, offsets: [2 / 3, 1 / 6, 1 / 3, 5 / 6, 0, .5] },
      wave: { duty: 5 / 6, offsets: [1 / 3, 5 / 6, 1 / 6, 2 / 3, 0, .5] },
    }[gait] || { duty: .5, offsets: [0, .5, .5, 0, 0, .5] };
    const duty = gaitSpec.duty, offsets = gaitSpec.offsets;
    const now = performance.now();
    const dt = this.fnkPreviewLastAt ? Math.min(.05, Math.max(0, (now - this.fnkPreviewLastAt) / 1000)) : 0;
    this.fnkPreviewLastAt = now;
    const latched = this.fnkPreviewDemo && !twist ? {} : { ...(this.fnkPreviewKeys || {}) };
    const combos = [['w'], ['s'], ['a'], ['d'], ['q'], ['e'], ['w', 'a'], ['w', 'd']];
    if (this.fnkPreviewDemo && !twist) {
      if (!this.fnkPreviewDemoStartedAt) this.fnkPreviewDemoStartedAt = now;
      for (const key of combos[Math.floor((now - this.fnkPreviewDemoStartedAt) / 3500) % combos.length]) latched[key] = true;
    }
    let tx = (latched.d ? 1 : 0) - (latched.a ? 1 : 0);
    let ty = (latched.s ? 1 : 0) - (latched.w ? 1 : 0);
    let norm = Math.hypot(tx, ty);
    if (norm > 1) { tx /= norm; ty /= norm; }
    let turn = (latched.q ? 1 : 0) - (latched.e ? 1 : 0);
    const stick = this.fnkControllerInput;
    if (stick && Math.max(Math.abs(stick.x || 0), Math.abs(stick.y || 0), Math.abs(stick.angle || 0)) > .02) {
      tx = Number(stick.x) || 0;
      ty = Number(stick.y) || 0;
      norm = Math.hypot(tx, ty);
      if (norm > 1) { tx /= norm; ty /= norm; }
      turn = Number(stick.angle) || 0;
    }
    turn = Math.max(-1, Math.min(1, turn));
    const moving = !twist && (Math.hypot(tx, ty) > 0 || turn !== 0);
    if (!this.fnkPreviewPaused) {
      const target = moving ? 1 : 0;
      this.fnkPreviewIntensity += (target - this.fnkPreviewIntensity) * Math.min(1, dt * 8);
      if (moving) {
        this.fnkPreviewVelocity = { x: tx, y: ty, turn };
        this.fnkPreviewPhase = (((this.fnkPreviewPhase || 0) + dt * (Number(this.fnkSpeed) || 1) / 2) % 1);
      }
      const m = this.fnkPreviewIntensity, v = this.fnkPreviewVelocity || { x: 0, y: 0, turn: 0 };
      if (!twist && m > .01) {
        const speed = Number(this.fnkSpeed) || 1, both = Math.hypot(v.x, v.y) > 0 && v.turn !== 0 ? .75 : 1;
        const stride = 34 * speed * m / duty * both;
        const yaw = this.fnkGridOffset.yaw || 0;
        this.fnkGridOffset.yaw = (yaw + v.turn * stride / 107 * dt) % (Math.PI * 2);
        this.fnkGridOffset.x = (this.fnkGridOffset.x + (v.x * stride * Math.cos(yaw) + v.y * stride * Math.sin(yaw)) * 2.2 * dt) % 48;
        this.fnkGridOffset.y = (this.fnkGridOffset.y + (-v.x * stride * Math.sin(yaw) + v.y * stride * Math.cos(yaw)) * 2.2 * dt) % 48;
      }
    }
    const phase = this.fnkPreviewPhase || 0;
    const hw = this.fnkHardwareStatus || {};
    const compatible = hw.connected === true && hw.firmware_profile === 'custom_fnhr_ascii_v2';
    this.fnkPoseValues ||= { x: 0, y: 0, z: 24, roll: 0, pitch: 0, yaw: 0 };
    if (twist && this.fnkPreviewDemo && !this.fnkPreviewPaused) {
      if (!this.fnkPreviewDemoStartedAt) this.fnkPreviewDemoStartedAt = now;
      const t = (now - this.fnkPreviewDemoStartedAt) / 1000;
      this.fnkPoseValues = { x: 20 * Math.sin(t * .9), y: 20 * Math.sin(t * .7 + 1), z: 24 + 8 * Math.sin(t * .5), roll: 10 * Math.sin(t * 1.1), pitch: 10 * Math.sin(t * .8 + 2), yaw: 20 * Math.sin(t * .6) };
    }
    this.fnkActionHitAreas = {};
    c.clearRect(0, 0, w, h); c.fillStyle = C.bg; c.fillRect(0, 0, w, h);
    const txt = (s, x, y, size = 14, color = C.text, weight = 500, align = 'left') => { c.fillStyle = color; c.font = `${weight} ${size}px ui-sans-serif,system-ui`; c.textAlign = align; c.textBaseline = 'middle'; c.fillText(String(s), x, y); };
    const card = (x, y, cw, ch) => { c.fillStyle = C.panel; c.strokeStyle = C.line; c.lineWidth = 1; c.beginPath(); c.roundRect(x, y, cw, ch, 12); c.fill(); c.stroke(); };
    const button = (key, x, y, bw, bh, label, selected = false, enabled = true) => { c.globalAlpha = enabled ? 1 : .48; c.fillStyle = selected ? C.stance : C.panel; c.strokeStyle = selected ? C.stance : C.line; c.lineWidth = 1; c.beginPath(); c.roundRect(x, y, bw, bh, 8); c.fill(); c.stroke(); txt(label, x + bw / 2, y + bh / 2, 14, selected ? C.bg : C.text, 500, 'center'); c.globalAlpha = 1; this.fnkActionHitAreas[key] = { x, y, width: bw, height: bh, enabled }; };
    const modeButton = (key, x, y, bw, bh, label, selected) => {
      c.fillStyle = selected ? C.stance : C.modeIdle; c.strokeStyle = selected ? C.stance : C.line; c.lineWidth = 1;
      c.beginPath(); c.roundRect(x, y, bw, bh, 8); c.fill(); c.stroke();
      txt(label, x + bw / 2, y + bh / 2, 14, selected ? '#ffffff' : C.modeInk, 600, 'center');
      this.fnkActionHitAreas[key] = { x, y, width: bw, height: bh, enabled: true };
    };
    const lab = (s, x, y) => txt(s.toUpperCase(), x, y, 12, C.muted, 500);
    const lx = 16, lw = 666, rx = 698, rw = 486, top = 112, innerX = rx + 16, innerW = rw - 32;
    txt('Hexapod Gait Lab', 16, 29, 22, C.text, 700);
    txt('Top view. Amber is swing (foot lifted); green is stance (foot planted). Click movement keys to latch, combine directions, or use the Quest sticks.', 16, 57, 13, C.muted);
    txt('Twist body shifts and tilts the chassis while the six feet stay planted.', 16, 78, 13, C.muted);
    txt(`${compatible ? 'FNK0031 · CONNECTED' : 'FNK0031 · BOARD OFFLINE'} · ACTUATION ${hw.actuation_enabled ? 'ON' : 'OFF'}`, w - 16, 29, 12, compatible ? C.stance : C.swing, 600, 'right');

    const previewMoves = ['FORWARD', 'BACKWARD', 'LEFT', 'RIGHT', 'TURN LEFT', 'TURN RIGHT', 'FORWARD + LEFT', 'FORWARD + RIGHT'];
    const activeMove = this.fnkPreviewDemo && !twist ? previewMoves[Math.floor((now - (this.fnkPreviewDemoStartedAt || now)) / 3500) % previewMoves.length]
      : moving ? (Math.abs(turn) > .05 ? (turn > 0 ? 'TURN LEFT' : 'TURN RIGHT') : ty < -.1 ? (tx < -.1 ? 'FORWARD + LEFT' : tx > .1 ? 'FORWARD + RIGHT' : 'FORWARD') : ty > .1 ? 'BACKWARD' : tx < 0 ? 'LEFT' : 'RIGHT') : 'IDLE';
    card(lx, top, lw, 625); txt(twist ? 'TWIST BODY' : activeMove, lx + 16, top + 22, 18, C.text, 700);
    txt(twist ? 'ALL SIX FEET PLANTED' : `${gait.toUpperCase()} · ${Math.round(duty * 100)}% stance`, lx + lw - 16, top + 22, 12, C.muted, 500, 'right');
    const stage = { x: 32, y: top + 48, w: 634, h: 554 }, scale = Math.min(stage.w / 640, stage.h / 560);
    c.fillStyle = C.stage; c.beginPath(); c.roundRect(stage.x, stage.y, stage.w, stage.h, 8); c.fill(); c.save(); c.beginPath(); c.rect(stage.x, stage.y, stage.w, stage.h); c.clip();
    c.translate(stage.x + (stage.w - 640 * scale) / 2, stage.y + (stage.h - 560 * scale) / 2); c.scale(scale, scale);
    if (!twist) {
      c.save(); c.translate(320, 285); c.rotate(this.fnkGridOffset.yaw || 0); c.translate(-320 - (this.fnkGridOffset.x || 0), -285 - (this.fnkGridOffset.y || 0));
      c.strokeStyle = C.line; c.lineWidth = 1; c.beginPath();
      for (let q = -1400; q <= 1400; q += 48) { c.moveTo(q, -1400); c.lineTo(q, 1400); c.moveTo(-1400, q); c.lineTo(1400, q); }
      c.stroke(); c.restore();
    } else {
      c.strokeStyle = C.line; c.lineWidth = 1; c.beginPath();
      for (let q = -1400; q <= 1400; q += 48) { c.moveTo(q, -1400); c.lineTo(q, 1400); c.moveTo(-1400, q); c.lineTo(1400, q); }
      c.stroke();
    }
    const P = this.fnkPoseValues, rr = Number(P.roll) * Math.PI / 180, pp = Number(P.pitch) * Math.PI / 180, yy = Number(P.yaw) * Math.PI / 180;
    const cr = Math.cos(rr), cp = Math.cos(pp), cy = Math.cos(yy), sy = Math.sin(yy), ox = twist ? Number(P.x) || 0 : 0, oy = twist ? -(Number(P.y) || 0) : 0;
    const dutySwing = 1 - duty, velocity = this.fnkPreviewVelocity || { x: 0, y: 0, turn: 0 };
    c.save(); c.translate(320, 285); c.scale(2.2, 2.2);
    const drawBody = (x, y, yaw, sx, syScale) => {
      c.save(); c.translate(x, y); c.rotate(-yaw); c.scale(sx, syScale); c.fillStyle = C.panel; c.strokeStyle = C.line; c.lineWidth = 1.5; c.beginPath(); c.roundRect(-28, -48, 56, 96, 14); c.fill(); c.stroke();
      c.fillStyle = C.text; c.beginPath(); c.moveTo(-8, -50); c.lineTo(8, -50); c.lineTo(0, -62); c.closePath(); c.fill();
      c.fillStyle = C.muted; c.font = '10px ui-monospace,Menlo,Consolas,monospace'; c.textAlign = 'center';
      [['L1', -14, -30], ['R1', 14, -30], ['L2', -14, 4], ['R2', 14, 4], ['L3', -14, 38], ['R3', 14, 38]].forEach(a => c.fillText(a[0], a[1], a[2])); c.restore();
    };
    const m = this.fnkPreviewIntensity || 0, both = Math.hypot(velocity.x, velocity.y) > 0 && velocity.turn !== 0 ? .75 : 1;
    legs.forEach((leg, i) => {
      const [, side, hy] = leg, fx = side * (hy === 0 ? 104 : 92), fy = hy < 0 ? -58 : hy > 0 ? 58 : 0, hx = side * 28;
      let hipX = hx, hipY = hy, footX = fx, footY = fy, swing = false, lift = 0, reach = 0;
      if (twist) {
        const x1 = hx * cr, y1 = hy * cp, z = -hx * Math.sin(rr) - hy * Math.sin(pp);
        hipX = ox + x1 * cy + y1 * sy; hipY = oy - x1 * sy + y1 * cy;
        const dx = fx - hipX, dy = fy - hipY, dz = (Number(P.z) || 24) + z;
        reach = Math.sqrt(dx * dx + dy * dy + dz * dz);
        const limited = reach > 105 || reach < 45;
        c.strokeStyle = limited ? C.swing : C.stance; c.fillStyle = c.strokeStyle;
        c.setLineDash(limited ? [4, 3] : []);
        c.beginPath(); c.moveTo(hipX, hipY); c.lineTo((hipX + fx) / 2 + side * 12, (hipY + fy) / 2); c.lineTo(fx, fy); c.stroke(); c.setLineDash([]);
        c.beginPath(); c.arc(fx, fy, 6, 0, Math.PI * 2); c.fill();
      } else {
        const lxLeg = velocity.x * both + velocity.turn * both * (fy / Math.hypot(fx, fy));
        const lyLeg = velocity.y * both + velocity.turn * both * (-fx / Math.hypot(fx, fy));
        const ph = (((phase - offsets[i]) % 1) + 1) % 1; swing = ph < dutySwing;
        let k = 0, u = 0;
        if (swing) { u = ph / dutySwing; k = 2 * u - 1; lift = Math.sin(Math.PI * u); }
        else { u = (ph - dutySwing) / duty; k = 1 - 2 * u; }
        if (m < .02) { swing = false; lift = 0; k = 0; }
        const amp = 34 * m, X = fx + lxLeg * k * amp, Y = fy + lyLeg * k * amp;
        footX = X; footY = Y;
        const color = swing ? C.swing : C.stance;
        c.strokeStyle = color; c.fillStyle = swing ? C.panel : C.stance; c.lineWidth = 2; c.setLineDash(swing ? [4, 3] : []);
        c.beginPath(); c.moveTo(hx, hy); c.lineTo((hx + X) / 2 + side * 12, (hy + Y) / 2); c.lineTo(X, Y); c.stroke(); c.setLineDash([]);
        c.strokeStyle = C.line; c.lineWidth = 1; c.setLineDash([2, 3]); c.beginPath(); c.moveTo(fx, fy); c.lineTo(fx - side * 34, fy); c.stroke(); c.setLineDash([]);
        c.beginPath(); c.arc(X, Y, 6 + 5 * lift, 0, Math.PI * 2); c.fill(); c.strokeStyle = color; c.stroke();
      }
      const barY = top + 0; // Keeps the per-leg values local to this draw pass.
      void barY;
      legs[i].reach = reach;
      legs[i].swing = swing;
      legs[i].progress = twist ? Math.min(1, reach / 105) : (((phase - offsets[i]) % 1) + 1) % 1;
    });
    drawBody(ox, oy, yy, cr, cp); c.restore(); c.restore();

    if (!twist) {
      const y = top + 641; card(lx, y, lw, 298); lab('Gait cycle, one row per leg', lx + 16, y + 24);
      const s = (lw - 34) / 640, tx0 = lx + 16 + 48 * s, tw = 580 * s, rowY = y + 47;
      const cycleSegments = (start, width) => {
        const a = ((start % 1) + 1) % 1, end = a + width;
        return end <= 1 ? [[a, end]] : [[a, 1], [0, end - 1]];
      };
      legs.forEach((leg, i) => {
        const yy0 = rowY + i * 26 * s, hh = 18 * s, off = offsets[i], swingWidth = dutySwing;
        txt(leg[0], lx + 16 + 12 * s, yy0 + hh / 2, 12, C.text);
        c.fillStyle = '#ffffff'; c.beginPath(); c.roundRect(tx0, yy0, tw, hh, 4); c.fill();
        c.strokeStyle = C.statusTrack; c.lineWidth = 1; c.beginPath(); c.roundRect(tx0, yy0, tw, hh, 4); c.stroke();
        cycleSegments(off + swingWidth, duty).forEach(seg => {
          const sx = tx0 + seg[0] * tw, sw = (seg[1] - seg[0]) * tw;
          c.fillStyle = C.stance; c.fillRect(sx, yy0 + 1, sw, hh - 2);
        });
        c.strokeStyle = C.swing; c.lineWidth = 1.5; c.setLineDash([5, 3]);
        const segments = cycleSegments(off, swingWidth);
        segments.forEach(seg => { c.beginPath(); c.roundRect(tx0 + seg[0] * tw, yy0, (seg[1] - seg[0]) * tw, hh, 4); c.stroke(); });
        c.setLineDash([]); const px = tx0 + (((phase - off) % 1) + 1) % 1 * tw;
        c.strokeStyle = C.text; c.lineWidth = 1.5; c.beginPath(); c.moveTo(px, yy0 - 3); c.lineTo(px, yy0 + hh + 3); c.stroke();
      });
      txt('Filled green: stance', lx + 16, y + 270, 13, C.stance);
      txt('Dashed amber: swing', lx + 182, y + 270, 13, C.swing, 500);
      const swingingNow = legs.filter((_, i) => ((((phase - offsets[i]) % 1) + 1) % 1) < dutySwing).map(l => l[0]).join(', ') || 'none';
      txt('Swinging: ' + swingingNow, lx + lw - 16, y + 270, 11, C.text, 500, 'right');
    } else {
      const y = top + 641; card(lx, y, lw, 270); lab('Body tilt, feet planted', lx + 16, y + 24);
      const ground = y + 218, scaleGauge = Math.min((lw - 26) / 640, 1.12), baseX = lx + (lw - 640 * scaleGauge) / 2;
      const gauge = (center, label, angle) => {
        const rr0 = Number(angle || 0) * Math.PI / 180, bodyY = ground - (Number(P.z) || 24) * 2.4 * scaleGauge;
        const half = 70 * scaleGauge, dx = half * Math.cos(rr0), dy = half * Math.sin(rr0), left = center - 160 * scaleGauge, right = center + 160 * scaleGauge;
        c.strokeStyle = C.line; c.lineWidth = 2; c.beginPath(); c.moveTo(left, ground); c.lineTo(right, ground); c.stroke();
        c.fillStyle = C.stance; c.beginPath(); c.arc(left + 5, ground, 5, 0, Math.PI * 2); c.arc(right - 5, ground, 5, 0, Math.PI * 2); c.fill();
        c.strokeStyle = C.stance; c.lineWidth = 2; c.beginPath(); c.moveTo(center - dx, bodyY - dy); c.lineTo(left + 5, ground); c.moveTo(center + dx, bodyY + dy); c.lineTo(right - 5, ground); c.stroke();
        c.strokeStyle = C.text; c.lineWidth = 7; c.beginPath(); c.moveTo(center - dx, bodyY - dy); c.lineTo(center + dx, bodyY + dy); c.stroke();
        txt(`${label} · ${Number(angle || 0).toFixed(1)}°`, center, y + 244, 11, C.muted, 500, 'center');
      };
      gauge(baseX + 160 * scaleGauge, 'FRONT VIEW · ROLL', P.roll);
      gauge(baseX + 480 * scaleGauge, 'SIDE VIEW (FRONT RIGHT) · PITCH', P.pitch);
    }

    const ctrlH = twist ? 500 : 505; card(rx, top, rw, ctrlH); lab('Mode', innerX, top + 24); const gap = 8, bw = (innerW - gap) / 2;
    modeButton('tab-control', innerX, top + 38, bw, 44, 'Walk', !twist); modeButton('tab-twist', innerX + bw + gap, top + 38, bw, 44, 'Twist body', twist);
    if (!twist) {
      lab('Movement', innerX, top + 103); const pg = 8, pw = (innerW - pg * 2) / 3, py = top + 116, ph = 60;
      [['turn-left', 'q', 'TURN LEFT'], ['forward', 'w', 'FORWARD'], ['turn-right', 'e', 'TURN RIGHT'], ['left', 'a', 'LEFT'], ['backward', 's', 'BACKWARD'], ['right', 'd', 'RIGHT']].forEach((a, i) => {
        const x = innerX + (i % 3) * (pw + pg), y = py + Math.floor(i / 3) * (ph + 8), selected = Boolean(latched[a[1]]);
        c.fillStyle = selected ? C.stance : C.panel; c.strokeStyle = selected ? C.stance : C.line; c.lineWidth = 1; c.beginPath(); c.roundRect(x, y, pw, ph, 8); c.fill(); c.stroke();
        txt(a[1].toUpperCase(), x + pw / 2, y + 20, 20, selected ? C.bg : C.text, 700, 'center'); txt(a[2], x + pw / 2, y + 43, 11, selected ? C.bg : C.text, 500, 'center'); this.fnkActionHitAreas[`drive-${a[0]}`] = { x, y, width: pw, height: ph, enabled: true };
      });
      const by = py + 2 * (ph + 8), rw3 = (innerW - 16) / 3;
      button('drive-stop', innerX, by, rw3, 44, 'Stop'); button('demo-preview', innerX + rw3 + 8, by, rw3, 44, 'Demo all movements', this.fnkPreviewDemo); button('pause-preview', innerX + 2 * (rw3 + 8), by, rw3, 44, this.fnkPreviewPaused ? 'Resume' : 'Pause', this.fnkPreviewPaused);
      lab('Gait', innerX, by + 62); ['tripod', 'ripple', 'wave'].forEach((g, i) => button(`gait-${g}`, innerX + i * (innerW + 16) / 3, by + 74, (innerW - 32) / 3, 44, g[0].toUpperCase() + g.slice(1), g === gait));
      const sy0 = by + 143, sx = innerX + 64, sw = innerW - 132, cy0 = sy0 + 14, speed = Math.max(.25, Math.min(2, Number(this.fnkSpeed) || 1)), knob = sx + (speed - .25) / 1.75 * sw;
      txt('Speed', innerX, cy0, 14, C.text); c.strokeStyle = C.line; c.lineWidth = 3; c.beginPath(); c.moveTo(sx, cy0); c.lineTo(sx + sw, cy0); c.stroke(); c.strokeStyle = C.stance; c.beginPath(); c.moveTo(sx, cy0); c.lineTo(knob, cy0); c.stroke(); c.fillStyle = C.stance; c.beginPath(); c.arc(knob, cy0, 7, 0, Math.PI * 2); c.fill(); txt(speed.toFixed(1) + '×', innerX + innerW, cy0, 14, C.text, 500, 'right'); this.fnkActionHitAreas['speed-slider'] = { x: sx - 10, y: sy0 - 10, width: sw + 20, height: 44, enabled: true };
    } else {
      lab('Body pose', innerX, top + 103); const fields = [['x', 'Shift X', -30, 30, ''], ['y', 'Shift forward', -30, 30, ''], ['z', 'Body height (ZBODY)', 10, 44, ''], ['roll', 'Roll', -15, 15, '°'], ['pitch', 'Pitch', -15, 15, '°'], ['yaw', 'Twist (yaw)', -25, 25, '°']];
      fields.forEach((d, i) => { const y = top + 126 + i * 38, labelW = 132, bx = innerX + labelW + 5, barW = innerW - labelW - 68, value = Number(P[d[0]]) || 0, f = Math.max(0, Math.min(1, (value - d[2]) / (d[3] - d[2]))), kn = bx + f * barW; txt(d[1], innerX, y + 7, 12, C.text); c.strokeStyle = C.line; c.lineWidth = 3; c.beginPath(); c.moveTo(bx, y + 7); c.lineTo(bx + barW, y + 7); c.stroke(); c.strokeStyle = C.stance; c.beginPath(); c.moveTo(bx, y + 7); c.lineTo(kn, y + 7); c.stroke(); c.fillStyle = C.stance; c.beginPath(); c.arc(kn, y + 7, 6, 0, Math.PI * 2); c.fill(); txt(value.toFixed(1) + d[4], innerX + innerW, y + 7, 11, C.text, 500, 'right'); this.fnkActionHitAreas[`pose-slider-${d[0]}`] = { x: bx - 8, y: y - 9, width: barW + 16, height: 32, enabled: true, min: d[2], max: d[3], barX: bx, barW };
      });
      button('center-preview', innerX, top + 376, bw, 44, 'Center'); button('sweep-preview', innerX + bw + gap, top + 376, bw, 44, 'Sweep demo', this.fnkPreviewDemo);
    }
    const armY = top + ctrlH - 58; button('teleop-arm', innerX, armY, bw, 44, this.fnkTeleopArmed ? 'Robot input on' : 'Robot input', this.fnkTeleopArmed); button('teleop-stop', innerX + bw + gap, armY, bw, 44, 'Scene input', this.fnkSceneInputSelected);
    const legY = top + ctrlH + 16, legH = 354; card(rx, legY, rw, legH); lab('Leg status', innerX, legY + 24);
    txt(twist ? 'Feet planted · green is within modeled reach; amber is outside the limit.' : 'Filled green: stance · dashed amber: swing · bar shows gait-cycle position.', innerX, legY + 45, 10, C.muted);
    legs.forEach((leg, i) => {
      const y = legY + 61 + i * 43, x = innerX, chipX = x + 36, chipW = 106, bx = x + 152, barW = innerW - 152, current = legs[i];
      c.strokeStyle = C.line; c.lineWidth = 1; c.beginPath(); c.moveTo(x, y + 36); c.lineTo(rx + rw - 16, y + 36); c.stroke();
      txt(leg[0], x, y + 15, 12, C.text, 700);
      const statusChip = (label, state) => {
        const isSwing = state === 'swing', isLimit = state === 'limit';
        c.fillStyle = isSwing || isLimit ? C.panel : C.stance;
        c.strokeStyle = isSwing || isLimit ? C.swing : C.stance; c.lineWidth = 1;
        c.setLineDash(isSwing || isLimit ? [3, 2] : []);
        c.beginPath(); c.roundRect(chipX, y + 4, chipW, 23, 12); c.fill(); c.stroke(); c.setLineDash([]);
        txt(label, chipX + chipW / 2, y + 15.5, 10, isSwing || isLimit ? C.swing : '#ffffff', 700, 'center');
      };
      const drawStatusBar = (progress, color) => {
        c.fillStyle = C.statusTrack; c.beginPath(); c.roundRect(bx, y + 11, barW, 8, 4); c.fill();
        const fillW = Math.max(0, Math.min(barW, barW * progress));
        if (fillW > 0) { c.fillStyle = color; c.beginPath(); c.roundRect(bx, y + 11, fillW, 8, 4); c.fill(); }
      };
      if (twist) {
        const limited = current.reach > 105 || current.reach < 45;
        statusChip(`${limited ? 'LIMIT' : 'REACH'} ${current.reach.toFixed(0)}`, limited ? 'limit' : 'reach');
        drawStatusBar(current.progress, C.statusFill);
      } else {
        const p = (((phase - offsets[i]) % 1) + 1) % 1, isSwing = p < dutySwing;
        statusChip(isSwing ? 'SWING' : 'STANCE', isSwing ? 'swing' : 'stance');
        drawStatusBar(p, C.statusFill);
      }
    });
    txt(this.fnkMessage || 'Kinematic preview · commanded estimates only; servos do not report measured leg positions.', 16, h - 24, 11, C.muted);
    this.fnkTexture.needsUpdate = true;
  }
  drawFnkGaitLabLegacy() {
    const c=this.fnkContext,w=this.fnkCanvas.width,h=this.fnkCanvas.height;if(!c)return;
    c.clearRect(0,0,w,h);c.fillStyle='#0a1018';c.fillRect(0,0,w,h);c.strokeStyle='#2b405c';c.lineWidth=3;c.strokeRect(3,3,w-6,h-6);
    c.fillStyle='#0d141d';c.fillRect(12,12,w-24,120);c.fillStyle='#d6e4f0';c.font='700 42px system-ui';c.textAlign='left';c.textBaseline='middle';c.fillText('HEXAPOD GAIT LAB',38,50);
    const hw=this.fnkHardwareStatus||{},ready=hw.connected===true&&hw.firmware_profile==='custom_fnhr_ascii_v2';c.font='600 22px ui-monospace,monospace';c.fillStyle=ready?'#4dff88':'#ffb020';c.fillText(`${ready?'FNK0031 CONNECTED':'BOARD NOT CONNECTED'} · ACTUATION ${hw.actuation_enabled?'ENABLED':'DISABLED'}`,40,94);
    this.fnkActionHitAreas={};const btn=(key,x,y,bw,bh,label,on=true,selected=false)=>{c.globalAlpha=on?1:.4;c.fillStyle=selected?'#174e36':'#101c2a';c.strokeStyle=selected?'#4dff88':'#40536a';c.lineWidth=3;c.beginPath();c.roundRect(x,y,bw,bh,10);c.fill();c.stroke();c.fillStyle='#d6e4f0';c.font='650 24px ui-monospace,monospace';c.textAlign='center';c.fillText(label,x+bw/2,y+bh/2,bw-14);c.globalAlpha=1;this.fnkActionHitAreas[key]={x,y,width:bw,height:bh,enabled:on};};
    btn('tab-control',30,148,210,66,'WALK',true,this.fnkTab==='control');btn('tab-twist',250,148,260,66,'TWIST BODY',true,this.fnkTab==='twist');btn('tab-calibration',520,148,230,66,'LEG STATUS',true,this.fnkTab==='calibration');btn('tab-installation',760,148,260,66,'CONNECTION',true,this.fnkTab==='installation');
    c.fillStyle='#0b121b';c.fillRect(30,235,980,840);c.fillRect(1030,235,740,840);
    if(this.fnkTab==='control'||this.fnkTab==='twist'){
      const twist=this.fnkTab==='twist';c.fillStyle='#8fa3b8';c.font='600 22px ui-monospace,monospace';c.textAlign='left';c.fillText(twist?'TWIST BODY · FEET PLANTED':'WALK · FNHR GAIT STEPS',55,275);
      const cx=515,cy=635;c.strokeStyle='#2b405c';c.lineWidth=2;for(let r=90;r<=270;r+=90){c.beginPath();c.arc(cx,cy,r,0,Math.PI*2);c.stroke();}c.fillStyle='#d6e4f0';c.beginPath();c.roundRect(cx-68,cy-118,136,236,22);c.fill();c.fillStyle='#0a1018';c.beginPath();c.moveTo(cx-24,cy-119);c.lineTo(cx+24,cy-119);c.lineTo(cx,cy-150);c.fill();
      for(let i=0;i<6;i++){const s=i%2?1:-1,row=Math.floor(i/2)-1,bx=cx+s*63,by=cy+row*65,fx=cx+s*205,fy=by+row*36;c.strokeStyle=(i+Math.floor(performance.now()/500))%2?'#4dff88':'#ffb020';c.lineWidth=9;c.setLineDash(c.strokeStyle==='#ffb020'?[14,9]:[]);c.beginPath();c.moveTo(bx,by);c.lineTo((bx+fx)/2,(by+fy)/2);c.lineTo(fx,fy);c.stroke();c.setLineDash([]);c.fillStyle=c.strokeStyle;c.beginPath();c.arc(fx,fy,11,0,Math.PI*2);c.fill();}
      if(!twist){[['turn-left','↶ TURN'],['forward','↑ FORWARD'],['turn-right','↷ TURN'],['left','← LEFT'],['stop','■ STOP'],['right','→ RIGHT'],['backward','↓ BACK']].forEach(([k,l],i)=>btn(`drive-${k}`,1080+(i%3)*220,320+Math.floor(i/3)*145,200,116,l,ready&&hw.actuation_enabled&&!this.fnkDriveInFlight));c.fillStyle='#8fa3b8';c.textAlign='left';c.font='20px ui-monospace,monospace';c.fillText(`GAIT PREVIEW · SPEED ${this.fnkSpeed.toFixed(1)}×`,1085,825);['tripod','ripple','wave'].forEach((g,i)=>btn(`gait-${g}`,1080+i*220,850,200,65,g.toUpperCase(),true,this.fnkGait===g));btn('speed-down',1080,940,200,60,'SPEED −',true);btn('speed-up',1300,940,200,60,'SPEED +',true);}
      else {c.fillStyle='#8fa3b8';c.textAlign='left';c.font='22px ui-monospace,monospace';c.fillText('LEFT CONTROLLER ORIENTATION → BODY TWIST',1085,355);c.fillText('RIGHT STICK → X/Y shift · RIGHT TRIGGER → height',1085,420);c.fillText('WebXR tracked pose · bounded FNHR twist steps',1085,485);}
      btn('teleop-arm',1080,690,310,80,this.fnkTeleopArmed?'ROBOT MODE ON':'SELECT ROBOT MODE',ready&&hw.actuation_enabled,this.fnkTeleopArmed);btn('teleop-stop',1405,690,310,80,'SCENE MODE',true);
      c.fillStyle='#8fa3b8';c.font='19px ui-monospace,monospace';c.textAlign='left';c.fillText('Left menu toggles robot/scene mode when exposed; this panel is the fallback.',1085,815,650);c.fillText('Orientation drives Twist Body; no synthetic gait telemetry is shown.',1085,1010,650);
    }else{c.fillStyle='#d6e4f0';c.font='25px ui-monospace,monospace';c.textAlign='left';c.fillText(this.fnkTab==='calibration'?'LEG STATUS · COMMAND ESTIMATES, NOT SERVO FEEDBACK':'FNHR CUSTOM USB · 115200 BAUD',60,310);(this.fnkLegState?.legs||[]).forEach((l,i)=>c.fillText(`LEG ${i+1} · FOOT ${l.foot_position_mm?.map(n=>Number(n).toFixed(1)).join(' / ')||'—'} mm · JOINT ${l.joint_angles_deg?.map(n=>Number(n).toFixed(1)).join(' / ')||'—'}°`,60,385+i*90));}
    c.fillStyle='#8fa3b8';c.font='18px ui-monospace,monospace';c.textAlign='left';c.fillText(this.fnkMessage.slice(0,120),35,h-25,w-70);this.fnkTexture.needsUpdate=true;
  }

  drawFnkControlWindow() {
    this.drawFnkGaitLabExact();
    return;
    // Legacy panel kept below for reference while the Gait Lab renderer is active.
    if (!this.fnkContext) return;
    const ctx = this.fnkContext;
    const width = this.fnkCanvas.width;
    const height = this.fnkCanvas.height;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#071216'; ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#6bd9bd'; ctx.lineWidth = 5; ctx.strokeRect(3, 3, width - 6, height - 6);
    ctx.fillStyle = '#11232a'; ctx.fillRect(8, 8, width - 16, 128);
    ctx.fillStyle = '#e7fff4'; ctx.font = '700 43px system-ui'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText('FREENOVE FNK0031', 42, 48);
    const hardware = this.fnkHardwareStatus || {};
    const compatible = hardware.connected === true && hardware.firmware_profile === 'custom_fnhr_ascii_v2';
    ctx.fillStyle = compatible ? '#65e6b1' : hardware.connected ? '#f2c477' : '#f18c83';
    ctx.font = '600 25px ui-monospace, monospace';
    ctx.fillText(compatible ? `CONNECTED · CUSTOM FNHR · ACTUATION ${hardware.actuation_enabled ? 'ENABLED' : 'DISABLED'}` : hardware.connected ? 'FIRMWARE PROFILE NOT SUPPORTED' : 'BOARD STATUS UNAVAILABLE', 44, 96);
    this.fnkActionHitAreas = {};
    const button = (key, x, y, w, h, label, enabled = true, selected = false) => {
      ctx.globalAlpha = enabled ? 1 : 0.42;
      ctx.fillStyle = selected ? '#18513f' : '#112a32'; ctx.strokeStyle = selected ? '#75edbd' : '#55717a'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.roundRect(x, y, w, h, 18); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#e5fff4'; ctx.font = '650 27px ui-monospace, monospace'; ctx.textAlign = 'center';
      ctx.fillText(label, x + w / 2, y + h / 2, w - 20); ctx.globalAlpha = 1;
      this.fnkActionHitAreas[key] = { x, y, width: w, height: h, enabled };
    };
    button('tab-control', 42, 150, 300, 72, 'CONTROL', true, this.fnkTab === 'control');
    button('tab-twist', 354, 150, 340, 72, 'TWIST BODY', true, this.fnkTab === 'twist');
    button('tab-calibration', 706, 150, 360, 72, 'CALIBRATION', true, this.fnkTab === 'calibration');
    button('tab-installation', 1078, 150, 360, 72, 'INSTALLATION', true, this.fnkTab === 'installation');
    if (this.fnkTab === 'control' || this.fnkTab === 'twist') {
      const twist = this.fnkTab === 'twist';
      ctx.fillStyle = '#a8c8be'; ctx.font = '600 26px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText(twist ? 'LEFT CONTROLLER ORIENTATION · BODY TWIST   |   RIGHT STICK · BODY XY' : 'RIGHT STICK · MOVE FORWARD / BACK / STRAFE   |   LEFT STICK · TURN', 48, 270, width - 100);
      ctx.fillStyle = '#f2c477'; ctx.font = '500 22px system-ui';
      ctx.fillText(twist ? 'Rotate the left controller to twist; right trigger sets body height.' : 'Select robot mode, then move the sticks. Release stops future gait steps.', 50, 316, width - 100);
      const armed = this.fnkTeleopArmed;
      button('teleop-arm', 48, 360, 440, 98, armed ? 'ROBOT CONTROL · ON' : 'ROBOT CONTROL · OFF', compatible && hardware.actuation_enabled === true && !this.fnkDriveInFlight, armed);
      button('teleop-stop', 512, 360, 360, 98, 'SCENE MODE / DISARM', compatible && armed, false);
      ctx.fillStyle = '#d3e9df'; ctx.font = '600 24px ui-monospace, monospace';
      ctx.fillText(armed ? 'LEFT CONTROLLER MENU TOGGLE · STICKS NOW CONTROL THE HEXAPOD' : 'LEFT MENU TOGGLE · OR SELECT ROBOT CONTROL ABOVE', 50, 510, width - 100);
      ctx.fillStyle = '#91aaa2'; ctx.font = '500 21px system-ui';
      ctx.fillText(twist ? 'Controller orientation is tracked by WebXR; each bounded change twists the body.' : 'Firmware gait calls block: stick release cannot interrupt a gait already in progress.', 50, 552, width - 100);
      const leftTelemetry = this.telemetry?.controllers?.find(item => item.handedness === 'left');
      ctx.fillText(`LEFT MENU INPUT: ${leftTelemetry?.menuButtonExposed ? 'EXPOSED TO WEBXR' : 'QUEST MAY RESERVE IT · PANEL TOGGLE AVAILABLE'} · ${leftTelemetry?.profile || 'CONTROLLER WAITING'}`, 50, 586, width - 100);
      const sticks = this.telemetry?.controllers || [];
      for (const [hand, cx] of [['left', 530], ['right', 1270]]) {
        const sample = sticks.find(item => item.handedness === hand);
        const cy = 720;
        ctx.beginPath(); ctx.arc(cx, cy, 94, 0, Math.PI * 2);
        ctx.fillStyle = '#0d2027'; ctx.fill(); ctx.strokeStyle = '#52766e'; ctx.lineWidth = 5; ctx.stroke();
        ctx.strokeStyle = '#28463f'; ctx.beginPath(); ctx.moveTo(cx - 72, cy); ctx.lineTo(cx + 72, cy); ctx.moveTo(cx, cy - 72); ctx.lineTo(cx, cy + 72); ctx.stroke();
        const sx = Math.max(-1, Math.min(1, Number(sample?.x) || 0));
        const sy = Math.max(-1, Math.min(1, Number(sample?.y) || 0));
        ctx.beginPath(); ctx.arc(cx + sx * 60, cy + sy * 60, 22, 0, Math.PI * 2);
        ctx.fillStyle = '#69e8c4'; ctx.fill();
        ctx.fillStyle = '#c4d9d1'; ctx.font = '600 23px ui-monospace, monospace'; ctx.textAlign = 'center';
        ctx.fillText(`${hand.toUpperCase()} STICK`, cx, cy + 135);
      }
    } else {
      ctx.fillStyle = '#a8c8be'; ctx.font = '600 27px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText(this.fnkTab === 'calibration' ? 'CALIBRATION' : 'INSTALLATION', 50, 290);
      ctx.fillStyle = '#d3e9df'; ctx.font = '500 24px system-ui';
      if (this.fnkTab === 'calibration') {
        ctx.fillText('Board-only leg diagnostic · command estimates only, not servo feedback.', 50, 344, width - 100);
        button('board-only', 48, 395, 760, 76, `${this.fnkBoardOnlyConfirmed ? '☑' : '☐'} BOARD ONLY · NO SERVOS ATTACHED`, true, this.fnkBoardOnlyConfirmed);
        for (let leg = 1; leg <= 6; leg += 1) button(`leg-${leg}`, 48 + (leg - 1) * 142, 490, 126, 70, `L${leg}`, true, this.fnkLeg === leg);
        button('lift', 48, 585, 360, 84, 'MOVE +5 mm Z', compatible && this.fnkBoardOnlyConfirmed && !this.fnkBusy);
        button('return', 426, 585, 360, 84, 'RETURN −5 mm Z', compatible && this.fnkBoardOnlyConfirmed && !this.fnkBusy);
      } else {
        ctx.fillText('Custom FNHR firmware replaces the stock Processing / radio control path. Uploading is not performed from VR.', 50, 344, width - 100);
        ctx.fillText('Connection: USB serial · 115200 baud · custom_fnhr_ascii_v2', 50, 420, width - 100);
      }
    }
    ctx.fillStyle = '#d3e9df'; ctx.font = '600 23px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText(this.fnkMessage.slice(0, 105), 50, 680, width - 100);
    const legs = this.fnkLegState?.legs || [];
    for (let leg = 1; leg <= 6; leg += 1) {
      const item = legs.find(value => Number(value.leg) === leg) || legs[leg - 1];
      const z = Number(item?.foot_position_mm?.[2]);
      const x = 48 + ((leg - 1) % 3) * 550;
      const y = 790 + Math.floor((leg - 1) / 3) * 90;
      ctx.fillStyle = this.fnkLeg === leg ? '#76e1b2' : '#96b9ad'; ctx.font = '600 23px ui-monospace, monospace';
      ctx.fillText(`L${leg} · Z ${Number.isFinite(z) ? `${z.toFixed(1)} mm` : '—'}`, x, y);
    }
    ctx.fillStyle = '#8ba9a0'; ctx.font = '500 20px system-ui';
    ctx.fillText('FNHR internal position estimate · not measured servo feedback · no gait commands from this panel', 48, height - 48);
    this.fnkTexture.needsUpdate = true;
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
    // The separate Gait Lab is an interactive window. Let its controls receive
    // clicks even when another dashboard surface happens to overlap in depth.
    const fnkHit = this.fnkVisible ? raycaster.intersectObject(this.fnkPanel, false)[0] : null;
    const hit = fnkHit || raycaster.intersectObjects(this.panels.filter(panel => (panel !== this.gpsMapPanel || this.gpsMapVisible)
      && (panel !== this.powerWindowPanel || this.powerWindowVisible)
      && (panel !== this.fnkPanel || this.fnkVisible)), false)[0];
    const mapPoint = hit?.object === this.gpsMapPanel && hit.uv
      ? { x: hit.uv.x * this.gpsMapCanvas.width, y: (1 - hit.uv.y) * this.gpsMapCanvas.height } : null;
    const inMapBody = mapPoint && mapPoint.x >= 28 && mapPoint.x <= this.gpsMapCanvas.width - 28
      && mapPoint.y >= 132 && mapPoint.y <= this.gpsMapCanvas.height - 32;
    if (inMapBody) this.gpsMapHoveredController = controller;
    else if (this.gpsMapHoveredController === controller) this.gpsMapHoveredController = null;
    if (this.gpsMapPanController === controller) {
      if (inMapBody) {
        const dx = mapPoint.x - (this.gpsMapPanLastPoint?.x ?? mapPoint.x);
        const dy = mapPoint.y - (this.gpsMapPanLastPoint?.y ?? mapPoint.y);
        const now = performance.now();
        if ((Math.abs(dx) + Math.abs(dy) > 1) && now - this.gpsMapPanLastAt >= 24) {
          this.gpsMap.panBy(dx, dy);
          this.drawGpsMapWindow();
          this.gpsMapPanLastAt = now;
        }
        this.gpsMapPanLastPoint = mapPoint;
      } else this.gpsMapPanLastPoint = null;
    }
    if (this.sensorDensityDragController === controller && hit?.object === this.panel && hit.uv) {
      const x = hit.uv.x * this.logicalWidth;
      const y = (1 - hit.uv.y) * this.logicalHeight;
      const area = this.sensorPointDensityHitArea;
      if (area && y >= area.y && y <= area.y + area.height
          && x >= area.x && x <= area.x + area.width) this.setSensorPointDensityAt(x);
    }
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
    return raycaster.intersectObjects(this.panels.filter(panel => (panel !== this.gpsMapPanel || this.gpsMapVisible)
      && (panel !== this.powerWindowPanel || this.powerWindowVisible)
      && (panel !== this.fnkPanel || this.fnkVisible)), false).length > 0;
  }

  activateAt(controller, raycaster) {
    if (!this.visible) return null;
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const fnkHit = this.fnkVisible ? raycaster.intersectObject(this.fnkPanel, false)[0] : null;
    const hit = fnkHit || raycaster.intersectObjects(this.panels.filter(panel => (panel !== this.gpsMapPanel || this.gpsMapVisible)
      && (panel !== this.powerWindowPanel || this.powerWindowVisible)
      && (panel !== this.fnkPanel || this.fnkVisible)), false)[0];
    if (!hit?.uv) return null;
    if (hit.object === this.gpsMapPanel) {
      const x = hit.uv.x * this.gpsMapCanvas.width;
      const y = (1 - hit.uv.y) * this.gpsMapCanvas.height;
      for (const [key, area] of Object.entries(this.gpsMapActionHitAreas)) {
        if (x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
      }
      return 'gps-map-window';
    }
    if (hit.object === this.powerWindowPanel) {
      const x = hit.uv.x * this.powerWindowCanvas.width;
      const y = (1 - hit.uv.y) * this.powerWindowCanvas.height;
      for (const [key, area] of Object.entries(this.powerWindowActionHitAreas)) {
        if (x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
      }
      return 'power-window-surface';
    }
    if (hit.object === this.fnkPanel) {
      const x = hit.uv.x * this.fnkCanvas.width;
      const y = (1 - hit.uv.y) * this.fnkCanvas.height;
      for (const [key, area] of Object.entries(this.fnkActionHitAreas)) {
        if (x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) {
          if (!area.enabled) return 'fnk-disabled';
          if (key === 'speed-slider') {
            this.fnkSpeed = .25 + Math.max(0,Math.min(1,(x-area.x-10)/(area.width-20)))*1.75;
            this.drawFnkControlWindow();
          } else if (key.startsWith('pose-slider-')) {
            const axis=key.slice('pose-slider-'.length),value=area.min+Math.max(0,Math.min(1,(x-area.barX)/area.barW))*(area.max-area.min);
            this.fnkPoseValues[axis]=value;
            if (this.fnkTeleopArmed) void this.sendFnkManualControl({mode:'twist',x:this.fnkPoseValues.x,y:this.fnkPoseValues.y,z:this.fnkPoseValues.z-24,rx:this.fnkPoseValues.roll,ry:this.fnkPoseValues.pitch,rz:this.fnkPoseValues.yaw});
            else this.fnkMessage='POSE PREVIEW · SELECT ROBOT INPUT TO SEND';
            this.drawFnkControlWindow();
          }
          return key;
        }
      }
      return 'fnk-window';
    }
    const x = hit.uv.x * this.logicalWidth;
    const y = (1 - hit.uv.y) * this.logicalHeight;
    const densityArea = this.sensorPointDensityHitArea;
    if (densityArea && x >= densityArea.x && x <= densityArea.x + densityArea.width
        && y >= densityArea.y && y <= densityArea.y + densityArea.height) {
      this.setSensorPointDensityAt(x);
      return 'sensor-point-density';
    }
    const cameraArea = this.cameraHitArea;
    if (cameraArea && x >= cameraArea.x && x <= cameraArea.x + cameraArea.width && y >= cameraArea.y && y <= cameraArea.y + cameraArea.height) return 'camera-background';
    for (const [key, area] of Object.entries(this.actionHitAreas)) {
      if (area.enabled && x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
    }
    return 'dashboard';
  }

  beginAdjust(controller, inputSource, aimController = controller, raycaster = null) {
    if (!this.visible || this.grabbedController || !raycaster || !aimController) return false;
    aimController.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(aimController.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(aimController.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation).normalize();
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObjects(this.panels.filter(panel => (panel !== this.gpsMapPanel || this.gpsMapVisible)
      && (panel !== this.powerWindowPanel || this.powerWindowVisible)
      && (panel !== this.fnkPanel || this.fnkVisible)), false)[0];
    if (!hit?.point || !hit.object) return false;
    const target = hit.object === this.gpsMapPanel ? 'gps-map'
      : hit.object === this.powerWindowPanel ? 'power'
        : hit.object === this.fnkPanel ? 'fnk' : 'hud';
    const root = target === 'gps-map' ? this.gpsMapRoot : target === 'power' ? this.powerWindowRoot : target === 'fnk' ? this.fnkRoot : this.root;
    root.updateMatrixWorld(true);
    this.grabbedPanel = hit.object;
    this.grabAnchorLocal.copy(hit.object.worldToLocal(hit.point.clone()));
    this.grabAnchorDistance = Math.max(0.2, hit.distance);
    this.grabbedController = controller;
    this.grabbedWindow = target;
    this.grabInputSource = inputSource || null;
    this.headLocked = false;
    this.worldAnchored = true;
    this.drawDashboard();
    return true;
  }

  endAdjust(controller, xrCamera = null) {
    if (this.grabbedController !== controller) return false;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.grabbedPanel = null;
    if (xrCamera) {
      if (this.grabbedWindow === 'gps-map') {
        this.persistGpsMapPose(xrCamera, true);
      } else if (this.grabbedWindow === 'power') {
        this.persistPowerWindowPose(xrCamera, true);
      } else if (this.grabbedWindow === 'fnk') {
        this.persistFnkPose(xrCamera, true);
      } else {
        this.persistPose(xrCamera, true);
      }
    }
    this.grabbedWindow = 'hud';
    this.drawDashboard();
    return true;
  }

  updateAdjustment(deltaSeconds = 1 / 90, inputSources = []) {
    if (!this.grabbedController) return;
    this.grabbedController.updateMatrixWorld(true);
    this.grabbedController.getWorldPosition(this.scratchPosition);
    this.grabbedController.getWorldQuaternion(this.scratchQuaternion);
    const targetRoot = this.grabbedWindow === 'gps-map' ? this.gpsMapRoot
      : this.grabbedWindow === 'power' ? this.powerWindowRoot
        : this.grabbedWindow === 'fnk' ? this.fnkRoot : this.root;
    if (!this.grabbedPanel) return;
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
    this.grabRayDirection.set(0, 0, -1).applyQuaternion(this.scratchQuaternion).normalize();
    if (Math.abs(depthInput) > 0.12) this.grabAnchorDistance = Math.max(0.2, Math.min(8, this.grabAnchorDistance - depthInput * elapsed * 1.8));
    if (this.grabbedWindow === 'gps-map') {
      if (Math.abs(widthInput) > 0.12) this.gpsMapWidthScale = Math.max(0.45, Math.min(5, this.gpsMapWidthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.gpsMapHeightScale = Math.max(0.45, Math.min(5, this.gpsMapHeightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.applyGpsMapSize();
    } else if (this.grabbedWindow === 'power') {
      if (Math.abs(widthInput) > 0.12) this.powerWindowWidthScale = Math.max(.45, Math.min(5, this.powerWindowWidthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.powerWindowHeightScale = Math.max(.45, Math.min(5, this.powerWindowHeightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.applyPowerWindowSize();
    } else if (this.grabbedWindow === 'fnk') {
      if (Math.abs(widthInput) > 0.12) this.fnkWidthScale = Math.max(0.55, Math.min(3.5, this.fnkWidthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.fnkHeightScale = Math.max(0.55, Math.min(3.5, this.fnkHeightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.fnkPanel.scale.set(this.fnkWidthScale, this.fnkHeightScale, 1);
    } else {
      if (Math.abs(widthInput) > 0.12) this.widthScale = Math.max(0.45, Math.min(5, this.widthScale * Math.exp(widthInput * elapsed * 2.8)));
      if (Math.abs(heightInput) > 0.12) this.heightScale = Math.max(0.45, Math.min(5, this.heightScale * Math.exp(-heightInput * elapsed * 2.8)));
      this.applyHudSize();
    }
    this.grabAnchorTarget.copy(this.scratchPosition).addScaledVector(this.grabRayDirection, this.grabAnchorDistance);
    // Reposition around the exact panel-local point picked at grab start. Recompute
    // orientation as its position changes so the panel remains tangent to the sphere.
    for (let pass = 0; pass < 3; pass += 1) {
      this.grabPanelOffset.copy(this.grabAnchorLocal).multiply(this.grabbedPanel.scale)
        .applyQuaternion(this.grabbedPanel.quaternion).add(this.grabbedPanel.position)
        .applyQuaternion(targetRoot.quaternion);
      targetRoot.position.copy(this.grabAnchorTarget).sub(this.grabPanelOffset);
      this.orientWindowToSphere(targetRoot);
    }
    this.grabPanelOffset.copy(this.grabAnchorLocal).multiply(this.grabbedPanel.scale)
      .applyQuaternion(this.grabbedPanel.quaternion).add(this.grabbedPanel.position)
      .applyQuaternion(targetRoot.quaternion);
    targetRoot.position.copy(this.grabAnchorTarget).sub(this.grabPanelOffset);
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
    if (!this.sphereCenterSet) {
      this.sphereCenter.copy(this.scratchPosition);
      this.sphereCenterSet = true;
    }
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
      }
      this.worldAnchored = true;
    }
    this.orientWindowToSphere(this.root);
    if (this.gpsMapVisible && !this.gpsMapWorldAnchored) {
      if (this.gpsMapPose) {
        this.gpsMapRoot.position.copy(this.gpsMapHeadOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
        this.gpsMapRoot.quaternion.copy(this.scratchQuaternion).multiply(this.gpsMapHeadOffsetQuaternion);
      } else {
        this.gpsMapRoot.position.copy(this.root.position).add(new this.THREE.Vector3(3.6, -0.08, -0.9).applyQuaternion(this.root.quaternion));
      }
      this.gpsMapWorldAnchored = true;
    }
    if (this.gpsMapWorldAnchored) this.orientWindowToSphere(this.gpsMapRoot);
    if (this.powerWindowVisible && !this.powerWindowWorldAnchored) {
      if (this.powerWindowPose) {
        this.powerWindowRoot.position.copy(this.powerWindowHeadOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
        this.powerWindowRoot.quaternion.copy(this.scratchQuaternion).multiply(this.powerWindowHeadOffsetQuaternion);
      } else {
        this.powerWindowRoot.position.copy(this.root.position).add(new this.THREE.Vector3(0, 2.7, -0.9).applyQuaternion(this.root.quaternion));
      }
      this.powerWindowWorldAnchored = true;
    }
    if (this.powerWindowVisible && this.powerWindowWorldAnchored) this.orientWindowToSphere(this.powerWindowRoot);
    if (this.fnkVisible && !this.fnkWorldAnchored) {
      if (this.fnkPose) {
        this.fnkRoot.position.copy(this.fnkHeadOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
        this.fnkRoot.quaternion.copy(this.scratchQuaternion).multiply(this.fnkHeadOffsetQuaternion);
      } else {
        this.fnkRoot.position.copy(this.root.position).add(new this.THREE.Vector3(-3.3, -0.12, -0.9).applyQuaternion(this.root.quaternion));
      }
      this.fnkWorldAnchored = true;
    }
    if (this.fnkVisible && this.fnkWorldAnchored) this.orientWindowToSphere(this.fnkRoot);
    // Windows keep world positions; their flat planes follow the sphere's local horizon, never headset pitch.
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
    this.persistPowerWindowPose(xrCamera);
    this.persistFnkPose(xrCamera);
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
