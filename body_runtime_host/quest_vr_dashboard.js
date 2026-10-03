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
    this.grabForward = new THREE.Vector3(0, 0, -1);
    this.depthOffset = 0;
    this.frame = null;
    this.telemetry = null;
    this.controller = null;
    this.following = false;
    this.cameraBitmap = null;
    this.cameraMessage = 'CAMERA · WAITING';

    const canvas = document.createElement('canvas');
    canvas.width = 3072;
    canvas.height = 1152;
    this.canvas = canvas;
    this.context = canvas.getContext('2d');
    this.texture = new THREE.CanvasTexture(canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    const geometry = this.createArcGeometry(8.4, 0.18, 64);
    const panel = new THREE.Mesh(
      geometry,
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    panel.position.set(0, 0.05, -4.6);
    panel.renderOrder = 1000;
    this.root.add(panel);
    this.panels.push(panel);
    this.drawDashboard();
  }

  createArcGeometry(width, depth, segments) {
    const { BufferGeometry, Float32BufferAttribute } = this.THREE;
    const geometry = new BufferGeometry();
    const positions = [];
    const uvs = [];
    const indices = [];
    const angle = 1.9;
    const radius = width / (2 * Math.sin(angle / 2));
    for (let row = 0; row < 2; row += 1) {
      for (let column = 0; column <= segments; column += 1) {
        const u = column / segments;
        const theta = (u - 0.5) * angle;
        positions.push(Math.sin(theta) * radius, row === 0 ? 1.62 : -1.62, -radius * (1 - Math.cos(theta)) - (row === 0 ? 0 : depth));
        uvs.push(u, row === 0 ? 1 : 0);
      }
    }
    for (let column = 0; column < segments; column += 1) {
      const a = column;
      const b = column + segments + 1;
      indices.push(a, a + 1, b, a + 1, b + 1, b);
    }
    geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    return geometry;
  }

  update(frame) {
    this.frame = frame;
    this.drawDashboard();
  }

  updateTelemetry(telemetry) {
    this.telemetry = telemetry;
    this.drawDashboard();
  }

  updateController(controller) {
    this.controller = controller;
    this.drawDashboard();
  }

  setFollowing(following) {
    if (this.following === Boolean(following)) return;
    this.following = Boolean(following);
    this.drawDashboard();
  }

  panel(ctx, x, y, width, height, title, meta = '') {
    ctx.fillStyle = 'rgba(7, 16, 14, .92)';
    ctx.fillRect(x, y, width, height);
    ctx.strokeStyle = 'rgba(135, 206, 166, .48)';
    ctx.lineWidth = 2;
    ctx.strokeRect(x + 1, y + 1, width - 2, height - 2);
    ctx.fillStyle = '#a9e8c2';
    ctx.font = '600 25px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(title.toUpperCase(), x + 24, y + 29);
    if (meta) {
      ctx.fillStyle = '#83a594';
      ctx.font = '18px ui-monospace, monospace';
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
    const { width, height } = this.canvas;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(4, 12, 11, .94)';
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#76d6a1';
    ctx.lineWidth = 4;
    ctx.strokeRect(4, 4, width - 8, height - 8);

    const perception = this.frame?.perception || {};
    const fnk = this.controller || {};
    const xr = this.telemetry || {};
    this.drawTopTelemetry(ctx, perception, fnk, xr);
    const top = 182;
    const bottom = height - 86;
    const panelHeight = bottom - top;
    const margin = 28;
    const gap = 22;
    const cameraWidth = 570;
    const bodyWidth = 630;
    const sensorWidth = width - 2 * margin - 2 * gap - cameraWidth - bodyWidth;
    const cameraX = margin;
    const bodyX = cameraX + cameraWidth + gap;
    const sensorX = bodyX + bodyWidth + gap;
    this.drawCamera(ctx, cameraX, top, cameraWidth, panelHeight);
    this.drawBodyPanel(ctx, bodyX, top, bodyWidth, panelHeight, perception, fnk);
    this.drawSensorPanel(ctx, sensorX, top, sensorWidth, panelHeight, perception);
    ctx.fillStyle = this.grabbedController ? '#f0cd79' : '#91b6a0';
    ctx.font = '17px ui-monospace, monospace';
    ctx.textAlign = 'left';
    ctx.fillText(this.grabbedController
      ? 'HUD GRABBED · STICK ↑↓ DISTANCE · ←→ SCALE'
      : 'SQUEEZE GRIP TO MOVE HUD · STICK ↑↓ DISTANCE · ←→ SCALE', margin + 8, height - 28);
    ctx.textAlign = 'right';
    ctx.fillText(this.following ? 'CAMERA FOLLOW · BODY' : 'SCENE VIEW · FIXED', width - margin - 8, height - 28);
    this.texture.needsUpdate = true;
  }

  drawTopTelemetry(ctx, perception, fnk, xr) {
    const x = 28;
    const y = 24;
    const width = this.canvas.width - 56;
    const height = 136;
    this.panel(ctx, x, y, width, height, 'LIVE CONTROLLER TELEMETRY', 'QUEST INPUT + FNK0031');
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
      ctx.font = '15px ui-monospace, monospace';
      ctx.fillText(label, cellX + 18, y + 83);
      ctx.fillStyle = index < 3 ? '#e2f4e9' : '#b9ebcd';
      ctx.font = '600 23px ui-monospace, monospace';
      ctx.fillText(String(value).slice(0, 17), cellX + 18, y + 115);
    });
  }

  controllerText(controllers = [], hand) {
    const controller = controllers.find(item => item.handedness === hand);
    return controller ? `${Number(controller.x || 0).toFixed(1)}, ${Number(controller.y || 0).toFixed(1)}${controller.pressed ? ' · BTN' : ''}` : 'not detected';
  }

  drawCamera(ctx, x, y, width, height) {
    this.panel(ctx, x, y, width, height, 'Camera · egocentric', this.cameraBitmap ? 'LIVE' : 'BODY CAMERA');
    const imageX = x + 18;
    const imageY = y + 72;
    const imageWidth = width - 36;
    const imageHeight = height - 92;
    ctx.fillStyle = '#0b1512';
    ctx.fillRect(imageX, imageY, imageWidth, imageHeight);
    if (this.cameraBitmap) {
      const scale = Math.max(imageWidth / this.cameraBitmap.width, imageHeight / this.cameraBitmap.height);
      const drawWidth = this.cameraBitmap.width * scale;
      const drawHeight = this.cameraBitmap.height * scale;
      ctx.save();
      ctx.beginPath(); ctx.rect(imageX, imageY, imageWidth, imageHeight); ctx.clip();
      ctx.drawImage(this.cameraBitmap, imageX + (imageWidth - drawWidth) / 2, imageY + (imageHeight - drawHeight) / 2, drawWidth, drawHeight);
      ctx.restore();
    } else {
      ctx.fillStyle = '#bbd6c5';
      ctx.font = '600 22px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this.cameraMessage, imageX + imageWidth / 2, imageY + imageHeight / 2);
    }
  }

  drawBodyPanel(ctx, x, y, width, height, perception, fnk) {
    const position = perception.body?.position || [];
    const heading = Number(perception.body?.orientation || 0) * 180 / Math.PI;
    const objects = perception.objects || [];
    this.panel(ctx, x, y, width, height, 'Robot · body state', `${objects.length} OBJECTS`);
    const cx = x + 190;
    const cy = y + 258;
    this.drawHexapod(ctx, cx, cy, Number(fnk.body_heading_deg ?? heading), fnk.spikes || []);
    const metrics = [
      ['MAP POSITION', position.length >= 2 ? `${Number(position[0]).toFixed(2)}, ${Number(position[1]).toFixed(2)} m` : 'waiting'],
      ['BODY HEADING', `${Math.round(Number(fnk.compass_heading_deg ?? heading))}°`],
      ['LOCOMOTION', fnk.gait || 'idle'],
      ['CPG PHASE', Number.isFinite(Number(fnk.cpg_phase)) ? `${Math.round(Number(fnk.cpg_phase) * 180 / Math.PI)}°` : '—'],
      ['WALKING VERIFIED', fnk.locomotion_verified ? 'verified' : 'not measured'],
      ['WORLD MODEL', this.following ? 'following body' : 'scene overview'],
    ];
    metrics.forEach(([label, value], index) => {
      const rowY = y + 112 + index * 78;
      ctx.fillStyle = '#829d8d'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText(label, x + 370, rowY);
      ctx.fillStyle = '#def1e4'; ctx.font = '600 22px ui-monospace, monospace';
      ctx.fillText(String(value).slice(0, 24), x + 370, rowY + 34);
    });
    ctx.fillStyle = '#7e9889'; ctx.font = '16px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText(`controller step  ${fnk.step ?? '—'}    ·    recent spikes  ${(fnk.spikes || []).filter(Boolean).length}/18`, x + 28, y + height - 30);
  }

  drawHexapod(ctx, cx, cy, heading, spikes) {
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-heading * Math.PI / 180);
    ctx.strokeStyle = '#79c99a'; ctx.lineWidth = 10; ctx.lineCap = 'round';
    const legs = [[-1,-1],[0,-1],[1,-1],[-1,1],[0,1],[1,1]];
    legs.forEach(([side, front], index) => {
      const hipX = side * (index % 3 === 1 ? 9 : 28);
      const hipY = front * 28;
      const kneeX = side * 72;
      const footX = side * 116;
      const kneeY = front * 58;
      const footY = front * (92 + (spikes[index] ? 8 : 0));
      ctx.strokeStyle = spikes[index] ? '#ffd27a' : index < 3 ? '#76d5a0' : '#69bac2';
      ctx.beginPath(); ctx.moveTo(hipX, hipY); ctx.lineTo(kneeX, kneeY); ctx.lineTo(footX, footY); ctx.stroke();
      ctx.fillStyle = '#d9f2e3'; ctx.beginPath(); ctx.arc(footX, footY, 6, 0, Math.PI * 2); ctx.fill();
    });
    ctx.fillStyle = '#18352a'; ctx.strokeStyle = '#a0e5ba'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.roundRect(-40, -70, 80, 140, 24); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#dff5e7'; ctx.font = '600 15px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('FNK0031', 0, 0);
    ctx.fillStyle = '#f0ca76'; ctx.beginPath(); ctx.moveTo(0, -82); ctx.lineTo(-10, -62); ctx.lineTo(10, -62); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#829d8d'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'center';
    ctx.fillText('FRONT', cx, cy - 120);
  }

  drawSensorPanel(ctx, x, y, width, height, perception) {
    this.panel(ctx, x, y, width, height, 'Egocentric · spatial sensors', 'TOP VIEW · METRIC');
    const lidar = perception.sensor_projections?.lidar?.points || [];
    const radar = perception.modalities?.mmwave_radar?.targets || [];
    const inset = 20;
    const gap = 14;
    const mapWidth = (width - inset * 2 - gap) / 2;
    const mapHeight = height - 86;
    const mapY = y + 74;
    const dividerX = x + inset + mapWidth + gap / 2;
    ctx.strokeStyle = 'rgba(135, 206, 166, .22)';
    ctx.beginPath(); ctx.moveTo(dividerX, mapY + 8); ctx.lineTo(dividerX, y + height - 24); ctx.stroke();
    this.drawMetricMap(ctx, x + inset, mapY, mapWidth, mapHeight, lidar, radar, perception, 'LiDAR POINT CLOUD', 'lidar');
    this.drawMetricMap(ctx, x + inset + mapWidth + gap, mapY, mapWidth, mapHeight, lidar, radar, perception, 'mmWAVE TARGETS', 'radar');
  }

  drawMetricMap(ctx, x, y, width, height, lidar, radar, perception, title, mode) {
    ctx.fillStyle = '#9fc5ac'; ctx.font = '600 17px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(`${title}  ·  ${mode === 'lidar' ? lidar.length : radar.length}`, x + 6, y + 14);
    const mapTop = y + 32;
    const mapHeight = height - 42;
    const cx = x + width / 2;
    const cy = mapTop + mapHeight / 2;
    const radius = Math.min(width * 0.44, mapHeight * 0.44);
    const scale = radius / 6;
    ctx.save();
    ctx.beginPath(); ctx.rect(x, mapTop, width, mapHeight); ctx.clip();
    for (const meters of [1, 2, 3, 4, 5, 6]) {
      ctx.strokeStyle = meters % 2 === 0 ? 'rgba(120,190,150,.28)' : 'rgba(120,190,150,.13)';
      ctx.lineWidth = meters % 2 === 0 ? 2 : 1;
      ctx.beginPath(); ctx.arc(cx, cy, meters * scale, 0, 2 * Math.PI); ctx.stroke();
      if (meters % 2 === 0) {
        ctx.fillStyle = '#779586'; ctx.font = '13px ui-monospace, monospace'; ctx.textAlign = 'left';
        ctx.fillText(`${meters}m`, cx + 5, cy - meters * scale + 14);
      }
    }
    ctx.strokeStyle = 'rgba(120,190,150,.28)';
    for (const angle of [0, Math.PI / 2]) {
      ctx.beginPath(); ctx.moveTo(cx - Math.cos(angle) * radius, cy - Math.sin(angle) * radius); ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius); ctx.stroke();
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
      return { x: cx - left * scale, y: cy - forward * scale, distance };
    };
    if (mode === 'lidar') {
      for (const point of lidar) {
        const mapped = mapPoint([Number(point.x), Number(point.y)], lidarFrame, false);
        if (!mapped) continue;
        const intensity = Math.max(.2, Math.min(1, Number(point.intensity ?? .7)));
        ctx.fillStyle = `rgba(94, 221, 228, ${intensity})`;
        const dot = mapped.distance < 2 ? 4.5 : 3.2;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, dot, 0, Math.PI * 2); ctx.fill();
      }
    } else {
      for (const target of radar) {
        const mapped = mapPoint(target.position_m || target.position, radarFrame, false);
        if (!mapped) continue;
        const color = target.classification === 'mobile_obstacle' ? '#ef91c5' : '#f2ce73';
        const confidence = Math.max(.3, Math.min(1, Number(target.confidence ?? .7)));
        ctx.fillStyle = color; ctx.globalAlpha = confidence;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, 10, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1; ctx.strokeStyle = '#fff3cf'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#f8e8b8'; ctx.font = '13px ui-monospace, monospace'; ctx.textAlign = 'left';
        ctx.fillText(`${mapped.distance.toFixed(1)}m`, mapped.x + 13, mapped.y - 7);
      }
    }
    ctx.fillStyle = '#d9f5e4'; ctx.beginPath();
    ctx.moveTo(cx, cy - 17); ctx.lineTo(cx - 11, cy + 8); ctx.lineTo(cx + 11, cy + 8); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#779586'; ctx.font = '13px ui-monospace, monospace'; ctx.textAlign = 'right';
    ctx.fillText('BODY', x + width - 6, y + 14);
  }

  async setCameraFrame(frame) {
    const encoded = frame?.image_base64;
    if (!encoded || encoded.length > 5_000_000) {
      this.setCameraStatus(encoded ? 'FRAME TOO LARGE' : 'CAMERA · NO FRAME');
      return;
    }
    try {
      const bytes = Uint8Array.from(atob(encoded), character => character.charCodeAt(0));
      const bitmap = await createImageBitmap(new Blob([bytes], { type: frame.mime_type || 'image/jpeg' }));
      this.cameraBitmap?.close?.();
      this.cameraBitmap = bitmap;
      this.cameraMessage = 'LIVE';
      this.drawDashboard();
    } catch {
      this.setCameraStatus('CAMERA · DECODE ERROR');
    }
  }

  setCameraStatus(message) {
    this.cameraBitmap?.close?.();
    this.cameraBitmap = null;
    this.cameraMessage = message;
    this.drawDashboard();
  }

  setVisible(visible) { this.visible = Boolean(visible); }

  isControllerOverDashboard(controller, raycaster) {
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    return raycaster.intersectObjects(this.panels, false).length > 0;
  }

  beginAdjust(controller, inputSource) {
    if (!this.visible || this.grabbedController) return false;
    controller.updateMatrixWorld(true);
    controller.getWorldPosition(this.scratchPosition);
    controller.getWorldQuaternion(this.scratchQuaternion);
    this.grabOffsetPosition.copy(this.root.position).sub(this.scratchPosition).applyQuaternion(this.scratchQuaternion.clone().invert());
    this.grabOffsetQuaternion.copy(this.scratchQuaternion).invert().multiply(this.root.quaternion);
    this.grabbedController = controller;
    this.grabInputSource = inputSource || null;
    this.depthOffset = 0;
    this.headLocked = false;
    this.drawDashboard();
    return true;
  }

  endAdjust(controller) {
    if (this.grabbedController !== controller) return false;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.depthOffset = 0;
    this.drawDashboard();
    return true;
  }

  updateAdjustment(deltaSeconds = 1 / 90) {
    if (!this.grabbedController) return;
    this.grabbedController.getWorldPosition(this.scratchPosition);
    this.grabbedController.getWorldQuaternion(this.scratchQuaternion);
    this.scratchOffset.copy(this.grabOffsetPosition).applyQuaternion(this.scratchQuaternion);
    this.root.position.copy(this.scratchPosition).add(this.scratchOffset);
    this.root.quaternion.copy(this.scratchQuaternion).multiply(this.grabOffsetQuaternion);
    const axes = this.grabInputSource?.gamepad?.axes || [];
    const stickX = Number(axes.length >= 4 ? axes[2] : axes[0]) || 0;
    const stickY = Number(axes.length >= 4 ? axes[3] : axes[1]) || 0;
    const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
    if (Math.abs(stickY) > 0.12) this.depthOffset = Math.max(-1, Math.min(4, this.depthOffset - stickY * elapsed * 1.6));
    this.grabForward.set(0, 0, -1).applyQuaternion(this.scratchQuaternion);
    this.root.position.addScaledVector(this.grabForward, this.depthOffset);
    if (Math.abs(stickX) > 0.12) {
      this.userScale = Math.max(0.6, Math.min(2, this.userScale * Math.exp(stickX * elapsed * 0.9)));
      this.root.scale.setScalar(this.userScale);
    }
  }

  resetPose() {
    this.grabbedController = null;
    this.grabInputSource = null;
    this.headLocked = true;
    this.depthOffset = 0;
    this.userScale = 1;
    this.root.scale.setScalar(1);
    this.drawDashboard();
  }

  syncPose(xrCamera) {
    if (!this.headLocked) return;
    xrCamera.getWorldPosition(this.root.position);
    xrCamera.getWorldQuaternion(this.root.quaternion);
  }
}
