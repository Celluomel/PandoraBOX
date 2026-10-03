export class QuestVRDashboard {
  constructor(THREE) {
    this.THREE = THREE;
    this.scene = new THREE.Scene();
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.panels = [];
    this.visible = false;
    this.headLocked = true;
    this.userScale = 1;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.grabOffsetPosition = new THREE.Vector3();
    this.grabOffsetQuaternion = new THREE.Quaternion();
    this.scratchPosition = new THREE.Vector3();
    this.scratchQuaternion = new THREE.Quaternion();
    this.scratchOffset = new THREE.Vector3();

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    this.context = canvas.getContext('2d');
    this.texture = new THREE.CanvasTexture(canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    const panel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.65, 0.76),
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    panel.position.set(0, 0.42, -3.2);
    panel.renderOrder = 1000;
    this.root.add(panel);
    this.panels.push(panel);

    const cameraCanvas = document.createElement('canvas');
    cameraCanvas.width = 640;
    cameraCanvas.height = 360;
    this.cameraContext = cameraCanvas.getContext('2d');
    this.cameraTexture = new THREE.CanvasTexture(cameraCanvas);
    this.cameraTexture.colorSpace = THREE.SRGBColorSpace;
    const cameraPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.75, 0.984),
      new THREE.MeshBasicMaterial({ map: this.cameraTexture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    cameraPanel.position.set(-1.72, 0.42, -3);
    cameraPanel.rotation.y = 0.42;
    cameraPanel.renderOrder = 1000;
    this.root.add(cameraPanel);
    this.panels.push(cameraPanel);
    this.drawCameraMessage('CAMERA · WAITING');

    const sensorCanvas = document.createElement('canvas');
    sensorCanvas.width = 1024;
    sensorCanvas.height = 512;
    this.sensorContext = sensorCanvas.getContext('2d');
    this.sensorTexture = new THREE.CanvasTexture(sensorCanvas);
    this.sensorTexture.colorSpace = THREE.SRGBColorSpace;
    const sensorPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.9, 0.95),
      new THREE.MeshBasicMaterial({ map: this.sensorTexture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    sensorPanel.position.set(1.72, 0.42, -3);
    sensorPanel.rotation.y = -0.42;
    sensorPanel.renderOrder = 1000;
    this.root.add(sensorPanel);
    this.panels.push(sensorPanel);
    this.frame = null;
    this.telemetry = null;
    this.following = false;
    this.update(null);
  }

  update(frame) {
    this.frame = frame;
    this.drawStatus();
    this.drawSensorViews(frame?.perception || {});
  }

  updateTelemetry(telemetry) {
    this.telemetry = telemetry;
    this.drawStatus();
  }

  setFollowing(following) {
    if (this.following === Boolean(following)) return;
    this.following = Boolean(following);
    this.drawStatus();
  }

  drawStatus() {
    const ctx = this.context;
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#07120ff0';
    ctx.fillRect(8, 8, canvas.width - 16, canvas.height - 16);
    ctx.strokeStyle = '#72d5a1';
    ctx.lineWidth = 5;
    ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#e1f6e9';
    ctx.font = '600 43px system-ui';
    ctx.fillText('BODY STATUS', 44, 62);
    ctx.fillStyle = '#9fc5ac';
    ctx.font = '30px system-ui';

    const perception = this.frame?.perception || {};
    const position = perception.body?.position || [];
    const pose = position.length >= 2
      ? `Body  ${Number(position[0]).toFixed(2)}, ${Number(position[1]).toFixed(2)} m`
      : 'Body pose  waiting for perception';
    const objects = perception.objects?.length || 0;
    ctx.fillText(pose, 52, 135);
    ctx.fillText(`Scene objects  ${objects}`, 52, 190);
    ctx.fillText(`View  ${this.following ? 'FOLLOW BODY' : 'FIXED SCENE'}`, 52, 238);
    ctx.fillStyle = '#e1f6e9';
    ctx.font = '600 28px system-ui';
    ctx.fillText('LIVE CONTROLLER TELEMETRY', 52, 292);
    ctx.fillStyle = '#9fc5ac';
    ctx.font = '28px system-ui';
    const telemetry = this.telemetry || {};
    ctx.fillText(`Head  ${telemetry.headingDegrees ?? '--'}°`, 52, 348);
    const controllers = telemetry.controllers || [];
    for (const [index, hand] of ['left', 'right'].entries()) {
      const controller = controllers.find(item => item.handedness === hand);
      const row = controller
        ? `${hand === 'left' ? 'L' : 'R'} ctrl  ${controller.x.toFixed(1)}, ${controller.y.toFixed(1)}${controller.pressed ? ' · button' : ''}`
        : `${hand === 'left' ? 'L' : 'R'} ctrl  not detected`;
      ctx.fillText(row, 52, 405 + index * 50);
    }
    ctx.fillStyle = '#74a989';
    ctx.font = '20px system-ui';
    ctx.fillText('POINT + HOLD GRIP · MOVE  |  STICK ↑↓ · SCALE', 52, 493);
    this.texture.needsUpdate = true;
  }

  drawSensorViews(perception) {
    const ctx = this.sensorContext;
    const { width, height } = ctx.canvas;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#07120ff0';
    ctx.fillRect(6, 6, width - 12, height - 12);
    ctx.strokeStyle = '#72d5a1';
    ctx.lineWidth = 4;
    ctx.strokeRect(8, 8, width - 16, height - 16);
    ctx.fillStyle = '#e1f6e9';
    ctx.font = '600 31px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText('EGOCENTRIC SENSORS', 28, 42);
    ctx.strokeStyle = '#284a39';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(width / 2, 68);
    ctx.lineTo(width / 2, height - 18);
    ctx.stroke();
    this.drawSensorPlot(ctx, 18, 70, width / 2 - 28, height - 92, 'LiDAR · WORLD MODEL', perception.sensor_projections?.lidar?.points || [], 'lidar', perception);
    this.drawSensorPlot(ctx, width / 2 + 10, 70, width / 2 - 28, height - 92, 'mmWAVE · TARGETS', perception.modalities?.mmwave_radar?.targets || [], 'radar', perception);
    this.sensorTexture.needsUpdate = true;
  }

  drawSensorPlot(ctx, x, y, width, height, title, points, kind, perception) {
    ctx.fillStyle = '#9fc5ac';
    ctx.font = '600 23px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(`${title}  ·  ${points.length}`, x + width / 2, y + 18);
    const centerX = x + width / 2;
    const bodyY = y + height - 20;
    const radius = Math.min(width * 0.43, height * 0.69);
    const scale = radius / 6;
    ctx.strokeStyle = '#284a39';
    ctx.lineWidth = 2;
    for (const meters of [2, 4, 6]) {
      ctx.beginPath();
      ctx.arc(centerX, bodyY, meters * scale, Math.PI, Math.PI * 2);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(centerX - 6 * scale, bodyY);
    ctx.lineTo(centerX + 6 * scale, bodyY);
    ctx.stroke();
    ctx.fillStyle = '#b6f1d3';
    ctx.beginPath();
    ctx.moveTo(centerX, bodyY - 12);
    ctx.lineTo(centerX - 10, bodyY + 8);
    ctx.lineTo(centerX + 10, bodyY + 8);
    ctx.closePath();
    ctx.fill();

    const frame = perception.sensor_projections?.frame || {};
    const bodyPosition = frame.body || perception.body?.position || [0, 0, 0];
    const yaw = Number(frame.yaw_rad ?? perception.body?.orientation ?? 0);
    const sourceFrame = String(kind === 'lidar'
      ? perception.sensor_projections?.lidar?.frame || 'body_world'
      : perception.modalities?.mmwave_radar?.frame || 'body').toLowerCase();
    const localFrame = /^(body|base_link|base_footprint|sensor|lidar)$/.test(sourceFrame);
    const globalFrame = /^(body_world|world|map|local_map|odom)$/.test(sourceFrame);
    const toScreen = position => {
      if (!Array.isArray(position) || position.length < 2) return null;
      let forward = Number(position[0]);
      let left = Number(position[1]);
      if (globalFrame || (!localFrame && kind === 'lidar')) {
        const dx = forward - Number(bodyPosition[0] || 0);
        const dy = left - Number(bodyPosition[1] || 0);
        forward = Math.cos(yaw) * dx + Math.sin(yaw) * dy;
        left = -Math.sin(yaw) * dx + Math.cos(yaw) * dy;
      }
      if (![forward, left].every(Number.isFinite) || Math.hypot(forward, left) > 6.5) return null;
      return [centerX - left * scale, bodyY - forward * scale];
    };

    for (const point of points) {
      const position = kind === 'lidar' ? [Number(point.x), Number(point.y)] : point.position_m || point.position;
      const mapped = toScreen(position);
      if (!mapped) continue;
      if (kind === 'lidar') {
        const intensity = Math.max(0.25, Math.min(1, Number(point.intensity ?? 0.6)));
        ctx.fillStyle = `rgba(105, 224, 230, ${intensity})`;
        ctx.beginPath();
        ctx.arc(mapped[0], mapped[1], 3.5, 0, Math.PI * 2);
        ctx.fill();
      } else {
        const confidence = Math.max(0.25, Math.min(1, Number(point.confidence ?? 0.6)));
        ctx.fillStyle = point.classification === 'mobile_obstacle' ? `rgba(240, 168, 215, ${confidence})` : `rgba(240, 202, 118, ${confidence})`;
        ctx.strokeStyle = '#fff3c2';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(mapped[0], mapped[1], 7, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    }
  }

  drawCameraMessage(message) {
    const ctx = this.cameraContext;
    const canvas = ctx.canvas;
    ctx.fillStyle = '#07120f';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#e1f6e9';
    ctx.font = '600 27px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    this.cameraTexture.needsUpdate = true;
  }

  async setCameraFrame(frame) {
    const encoded = frame?.image_base64;
    if (!encoded || encoded.length > 5_000_000) {
      this.drawCameraMessage(encoded ? 'FRAME TOO LARGE' : 'CAMERA · NO FRAME');
      return;
    }
    try {
      const bytes = Uint8Array.from(atob(encoded), character => character.charCodeAt(0));
      const bitmap = await createImageBitmap(new Blob([bytes], { type: frame.mime_type || 'image/jpeg' }));
      const ctx = this.cameraContext;
      const canvas = ctx.canvas;
      const scale = Math.min(canvas.width / bitmap.width, canvas.height / bitmap.height);
      const width = bitmap.width * scale;
      const height = bitmap.height * scale;
      ctx.fillStyle = '#07120f';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(bitmap, (canvas.width - width) / 2, (canvas.height - height) / 2, width, height);
      bitmap.close();
      this.cameraTexture.needsUpdate = true;
    } catch {
      this.drawCameraMessage('CAMERA · DECODE ERROR');
    }
  }

  setCameraStatus(message) {
    this.drawCameraMessage(message);
  }

  setVisible(visible) {
    this.visible = Boolean(visible);
  }

  isControllerOverDashboard(controller, raycaster) {
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    return raycaster.intersectObjects(this.panels, false).length > 0;
  }

  beginAdjust(controller, raycaster, inputSource) {
    if (!this.isControllerOverDashboard(controller, raycaster)) return false;
    controller.getWorldPosition(this.scratchPosition);
    controller.getWorldQuaternion(this.scratchQuaternion);
    this.grabOffsetPosition.copy(this.root.position).sub(this.scratchPosition)
      .applyQuaternion(this.scratchQuaternion.clone().invert());
    this.grabOffsetQuaternion.copy(this.scratchQuaternion).invert().multiply(this.root.quaternion);
    this.grabbedController = controller;
    this.grabInputSource = inputSource || null;
    this.headLocked = false;
    return true;
  }

  endAdjust(controller) {
    if (this.grabbedController !== controller) return;
    this.grabbedController = null;
    this.grabInputSource = null;
  }

  updateAdjustment(deltaSeconds = 1 / 90) {
    if (!this.grabbedController) return;
    this.grabbedController.getWorldPosition(this.scratchPosition);
    this.grabbedController.getWorldQuaternion(this.scratchQuaternion);
    this.scratchOffset.copy(this.grabOffsetPosition).applyQuaternion(this.scratchQuaternion);
    this.root.position.copy(this.scratchPosition).add(this.scratchOffset);
    this.root.quaternion.copy(this.scratchQuaternion).multiply(this.grabOffsetQuaternion);
    const axes = this.grabInputSource?.gamepad?.axes || [];
    const scaleAxis = Number(axes[3] ?? axes[1] ?? 0);
    if (Math.abs(scaleAxis) > 0.12) {
      const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
      this.userScale = Math.max(0.65, Math.min(1.8, this.userScale * Math.exp(-scaleAxis * elapsed * 0.8)));
      this.root.scale.setScalar(this.userScale);
    }
  }

  resetPose() {
    this.grabbedController = null;
    this.grabInputSource = null;
    this.headLocked = true;
    this.userScale = 1;
    this.root.scale.setScalar(1);
  }

  syncPose(xrCamera) {
    if (!this.headLocked) return;
    xrCamera.getWorldPosition(this.root.position);
    xrCamera.getWorldQuaternion(this.root.quaternion);
  }
}
