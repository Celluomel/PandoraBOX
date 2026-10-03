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
    this.grabForward = new THREE.Vector3(0, 0, -1);
    this.depthOffset = 0;
    this.frame = null;
    this.telemetry = null;
    this.controller = null;
    this.following = false;
    this.actionHitAreas = {};
    this.actionBusy = false;
    this.cameraBitmap = null;
    this.cameraMessage = 'CAMERA · WAITING';
    this.cameraBackgroundActive = false;
    this.cameraHitArea = null;

    const canvas = document.createElement('canvas');
    canvas.width = 3072;
    canvas.height = 1152;
    this.canvas = canvas;
    this.context = canvas.getContext('2d');
    this.loadSavedPose();
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
        positions.push(Math.sin(theta) * radius, row === 0 ? 1.62 : -1.62, radius * (1 - Math.cos(theta)) - (row === 0 ? 0 : depth));
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
    const radius = 32;
    ctx.fillStyle = 'rgba(7, 16, 14, .92)';
    ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); ctx.fill();
    ctx.strokeStyle = 'rgba(135, 206, 166, .48)';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(x + 1, y + 1, width - 2, height - 2, radius - 1); ctx.stroke();
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
    const frameInset = 5;
    const frameRadius = 58;
    ctx.beginPath();
    ctx.roundRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2, frameRadius);
    ctx.fillStyle = 'rgba(4, 12, 11, .94)';
    ctx.fill();
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2, frameRadius);
    ctx.clip();
    ctx.fillStyle = 'rgba(4, 12, 11, .94)';
    ctx.fillRect(frameInset, frameInset, width - frameInset * 2, height - frameInset * 2);
    ctx.strokeStyle = '#76d6a1';
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
    const cameraWidth = 930;
    const bodyWidth = 1040;
    const sensorWidth = width - 2 * margin - 2 * gap - cameraWidth - bodyWidth;
    const cameraX = margin;
    const bodyX = cameraX + cameraWidth + gap;
    const sensorX = bodyX + bodyWidth + gap;
    this.drawCamera(ctx, cameraX, top, cameraWidth, panelHeight);
    this.drawBodyPanel(ctx, bodyX, top, bodyWidth, panelHeight, perception, fnk, xr);
    this.drawSensorPanel(ctx, sensorX, top, sensorWidth, panelHeight, perception);
    this.drawHudActions(ctx);
    ctx.fillStyle = this.grabbedController ? '#f0cd79' : '#91b6a0';
    ctx.font = '17px ui-monospace, monospace';
    ctx.textAlign = 'left';
    ctx.fillText(this.grabbedController
      ? 'HUD GRABBED · STICK ↑↓ PUSH / PULL · ←→ RESIZE · MOVE HAND TO REPOSITION'
      : 'HOLD GRIP TO EDIT · MOVE HAND TO POSITION · STICK TO ADJUST DEPTH / SIZE', margin + 8, height - 28);
    ctx.textAlign = 'right';
    ctx.fillText(this.following ? 'CAMERA FOLLOW · BODY' : 'SCENE VIEW · FIXED', width - margin - 8, height - 28);
    ctx.restore();
    this.texture.needsUpdate = true;
  }

  drawHudActions(ctx) {
    const buttonY = this.canvas.height - 62;
    const simulationReady = this.frame?.mode === 'sim';
    const simulationRunning = Boolean(this.frame?.running);
    const simulationLabel = simulationRunning ? 'PAUSE SIMULATION' : 'START SIMULATION';
    const simulationX = this.canvas.width / 2 - 360;
    const exitX = this.canvas.width / 2 + 40;
    const drawButton = (key, x, width, label, fill, stroke, textColor, enabled = true) => {
      const height = 48;
      this.actionHitAreas[key] = { x: x - 16, y: buttonY - 12, width: width + 32, height: height + 24, enabled: enabled && !this.actionBusy };
      ctx.globalAlpha = enabled ? 1 : 0.42;
      ctx.fillStyle = fill;
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect(x, buttonY, width, height, 18); ctx.fill(); ctx.stroke();
      ctx.fillStyle = textColor;
      ctx.font = '700 18px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, x + width / 2, buttonY + height / 2);
      ctx.globalAlpha = 1;
    };
    drawButton('simulation', simulationX, 320, this.actionBusy ? 'PLEASE WAIT' : simulationReady ? simulationLabel : 'SIMULATION OFFLINE', 'rgba(31, 105, 78, .96)', '#75edbd', '#e5fff3', simulationReady);
    drawButton('exit', exitX, 260, this.actionBusy ? 'PLEASE WAIT' : 'EXIT VR', 'rgba(91, 53, 42, .96)', '#f0a888', '#fff0e8');
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
    this.panel(ctx, x, y, width, height, 'Camera · egocentric', this.cameraBackgroundActive ? 'BACKGROUND ON' : this.cameraBitmap ? 'LIVE' : 'BODY CAMERA');
    const imageX = x + 18;
    const imageWidth = width - 36;
    const imageHeight = Math.min(height - 112, imageWidth * .78);
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
      ctx.fillStyle = 'rgba(4, 13, 11, .78)';
      ctx.beginPath(); ctx.roundRect(imageX + 16, imageY + imageHeight - 48, 390, 34, 12); ctx.fill();
      ctx.fillStyle = '#d9f5e4'; ctx.font = '600 15px ui-monospace, monospace';
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText(this.cameraBackgroundActive ? 'TRIGGER · RESTORE 3D VIEW' : 'TRIGGER · USE AS 3D BACKGROUND', imageX + 28, imageY + imageHeight - 31);
    } else if (this.cameraBackgroundActive) {
      ctx.fillStyle = 'rgba(4, 13, 11, .72)';
      ctx.beginPath(); ctx.roundRect(imageX + 16, imageY + 16, imageWidth - 32, imageHeight - 32, 18); ctx.fill();
      ctx.fillStyle = '#d9f5e4'; ctx.font = '700 24px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('CAMERA · SCENE BACKGROUND', imageX + imageWidth / 2, imageY + imageHeight / 2 - 14);
      ctx.fillStyle = '#a9c3b2'; ctx.font = '17px ui-monospace, monospace';
      ctx.fillText('TRIGGER TO RESTORE 3D VIEW', imageX + imageWidth / 2, imageY + imageHeight / 2 + 24);
    } else {
      ctx.fillStyle = '#bbd6c5';
      ctx.font = '600 22px ui-monospace, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this.cameraMessage, imageX + imageWidth / 2, imageY + imageHeight / 2);
    }
  }

  drawBodyPanel(ctx, x, y, width, height, perception, fnk, xr) {
    const position = perception.body?.position || [];
    const heading = Number(perception.body?.orientation || 0) * 180 / Math.PI;
    const objects = perception.objects || [];
    this.panel(ctx, x, y, width, height, 'Body telemetry', `${objects.length} OBJECTS`);
    const cx = x + 270;
    const cy = y + 360;
    this.drawHexapod(ctx, cx, cy, Number(fnk.body_heading_deg ?? heading), fnk, 1.3);
    const headingDeg = Number(fnk.compass_heading_deg ?? fnk.body_heading_deg ?? heading);
    const headingX = x + width * .75;
    const headingY = y + 245;
    ctx.strokeStyle = 'rgba(169,232,194,.52)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(headingX, headingY, 47, 0, Math.PI * 2); ctx.stroke();
    ctx.save(); ctx.translate(headingX, headingY); ctx.rotate(-headingDeg * Math.PI / 180);
    ctx.fillStyle = '#59e0bc'; ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(-12, 13); ctx.lineTo(0, 7); ctx.lineTo(12, 13); ctx.closePath(); ctx.fill(); ctx.restore();
    ctx.fillStyle = '#829d8d'; ctx.font = '15px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText('HEADING', headingX + 70, headingY - 18);
    ctx.fillStyle = '#e4f4ea'; ctx.font = '600 42px system-ui';
    ctx.fillText(Number.isFinite(headingDeg) ? `${Math.round(headingDeg)}°` : '—', headingX + 70, headingY + 28);
    const velocity = perception.body?.velocity_mps ?? perception.motion?.velocity_mps ?? perception.modalities?.odometry?.velocity_mps;
    const speed = Array.isArray(velocity) ? Math.hypot(...velocity.map(Number)) : Number(velocity);
    ctx.fillStyle = '#829d8d'; ctx.font = '15px ui-monospace, monospace'; ctx.fillText('BODY SPEED', headingX + 8, headingY + 112);
    ctx.fillStyle = '#e4f4ea'; ctx.font = '600 32px system-ui';
    ctx.fillText(Number.isFinite(speed) ? `${speed.toFixed(2)} m/s` : '— m/s', headingX + 8, headingY + 153);
    const spikes = (fnk.spikes || []).filter(Boolean).length;
    const servoTargets = fnk.servo_targets || [];
    const bars = [['SERVO TARGETS', `${servoTargets.length}/18`, servoTargets.length / 18], ['SNN ACTIVE', `${spikes}/18`, spikes / 18]];
    bars.forEach(([label, value, ratio], index) => {
      const rowY = y + height - 210 + index * 66;
      ctx.fillStyle = 'rgba(8,20,17,.78)'; ctx.strokeStyle = 'rgba(135,206,166,.32)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.roundRect(x + 28, rowY, width - 56, 52, 12); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#a5ddba'; ctx.font = '14px ui-monospace, monospace'; ctx.textAlign = 'left'; ctx.fillText(label, x + 50, rowY + 31);
      const bx = x + 265; const bw = width - 390;
      ctx.fillStyle = '#243a32'; ctx.fillRect(bx, rowY + 21, bw, 11);
      ctx.fillStyle = '#58e3ba'; ctx.fillRect(bx, rowY + 21, bw * Math.max(0, Math.min(1, ratio)), 11);
      ctx.fillStyle = '#dff4e6'; ctx.textAlign = 'right'; ctx.font = '600 16px ui-monospace, monospace'; ctx.fillText(value, x + width - 42, rowY + 32);
    });
    const left = this.controllerText(xr.controllers, 'left');
    const right = this.controllerText(xr.controllers, 'right');
    ctx.fillStyle = '#7e9889'; ctx.textAlign = 'left'; ctx.font = '14px ui-monospace, monospace';
    ctx.fillText(`GAIT ${fnk.gait || 'waiting'}   ·   CPG ${Number.isFinite(Number(fnk.cpg_phase)) ? `${Math.round(Number(fnk.cpg_phase) * 180 / Math.PI)}°` : '—'}   ·   STEP ${fnk.step ?? '—'}`, x + 32, y + height - 38);
    ctx.textAlign = 'right'; ctx.fillText(`L ${left}   R ${right}`, x + width - 28, y + height - 38);
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
    this.panel(ctx, x, y, width, height, 'Egocentric sensors', 'METRIC · 6 M');
    const lidar = perception.sensor_projections?.lidar?.points || [];
    const radar = perception.modalities?.mmwave_radar?.targets || [];
    const inset = 20;
    const gap = 14;
    const mapWidth = width - inset * 2;
    const mapHeight = (height - 94 - gap) / 2;
    const mapY = y + 72;
    ctx.strokeStyle = 'rgba(135, 206, 166, .22)';
    ctx.beginPath(); ctx.roundRect(x + inset, mapY, mapWidth, mapHeight, 20); ctx.stroke();
    ctx.beginPath(); ctx.roundRect(x + inset, mapY + mapHeight + gap, mapWidth, mapHeight, 20); ctx.stroke();
    this.drawMetricMap(ctx, x + inset, mapY, mapWidth, mapHeight, lidar, radar, perception, 'LiDAR', 'lidar');
    this.drawMetricMap(ctx, x + inset, mapY + mapHeight + gap, mapWidth, mapHeight, lidar, radar, perception, 'mmWave', 'radar');
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
      ctx.fillStyle = '#a8c3b1'; ctx.font = '12px ui-monospace, monospace'; ctx.textAlign = 'center';
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
      ctx.fillStyle = '#a8c3b1'; ctx.font = '12px ui-monospace, monospace'; ctx.textAlign = 'center';
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
      ctx.fillStyle = '#83a99a'; ctx.font = '12px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText('Measured returns · dashed links show local continuity', x + 6, y + height - 5);
    } else {
      for (const target of radar) {
        const local = this.sensorLocal(target.position_m || target.position, radarFrame, bodyPosition, yaw);
        if (!local || local.forward < 0 || local.distance > 6.2) continue;
        const bearing = Math.atan2(-local.left, local.forward);
        if (Math.abs(bearing) > Math.PI / 3) continue;
        const mapped = { x: cx + (bearing / (Math.PI / 3)) * ((plotRight - plotLeft) / 2), y: plotBottom - (local.distance / 6) * (plotBottom - plotTop), distance: local.distance };
        const color = target.classification === 'mobile_obstacle' ? '#ef91c5' : '#f2ce73';
        const confidence = Math.max(.3, Math.min(1, Number(target.confidence ?? .7)));
        ctx.strokeStyle = color; ctx.globalAlpha = .18 + confidence * .2; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(mapped.x, mapped.y, 24 + (1 - confidence) * 18, 0, Math.PI * 2); ctx.stroke();
        ctx.globalAlpha = 1;
        const velocity = target.velocity_mps || target.velocity || [0, 0];
        let forwardSpeed = Number(velocity[0] || 0);
        let leftSpeed = Number(velocity[1] || 0);
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
        ctx.fillStyle = '#f8e8b8'; ctx.font = '600 12px ui-monospace, monospace'; ctx.textAlign = 'center';
        ctx.fillText(target.classification === 'mobile_obstacle' ? 'M' : '•', mapped.x, mapped.y - 12);
      }
      ctx.fillStyle = '#83a99a'; ctx.font = '12px ui-monospace, monospace'; ctx.textAlign = 'left';
      ctx.fillText('Target range · direction vectors use measured velocity', x + 6, y + height - 5);
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
      const bitmap = await createImageBitmap(new Blob([bytes], { type: frame.mime_type || 'image/jpeg' }));
      this.cameraBitmap?.close?.();
      this.cameraBitmap = bitmap;
      this.cameraMessage = 'LIVE';
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
    this.drawDashboard();
  }

  setVisible(visible) { this.visible = Boolean(visible); }

  setCameraBackgroundActive(active) {
    this.cameraBackgroundActive = Boolean(active);
    this.drawDashboard();
  }

  setActionBusy(busy) {
    this.actionBusy = Boolean(busy);
    this.drawDashboard();
  }

  isControllerOverDashboard(controller, raycaster) {
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    return raycaster.intersectObjects(this.panels, false).length > 0;
  }

  activateAt(controller, raycaster) {
    if (!this.visible) return null;
    controller.updateMatrixWorld(true);
    const rotation = new this.THREE.Matrix4().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    this.scene.updateMatrixWorld(true);
    const hit = raycaster.intersectObjects(this.panels, false)[0];
    if (!hit?.uv) return null;
    const x = hit.uv.x * this.canvas.width;
    const y = (1 - hit.uv.y) * this.canvas.height;
    const cameraArea = this.cameraHitArea;
    if (cameraArea && x >= cameraArea.x && x <= cameraArea.x + cameraArea.width && y >= cameraArea.y && y <= cameraArea.y + cameraArea.height) return 'camera-background';
    for (const [key, area] of Object.entries(this.actionHitAreas)) {
      if (area.enabled && x >= area.x && x <= area.x + area.width && y >= area.y && y <= area.y + area.height) return key;
    }
    return 'dashboard';
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

  endAdjust(controller, xrCamera = null) {
    if (this.grabbedController !== controller) return false;
    this.grabbedController = null;
    this.grabInputSource = null;
    this.depthOffset = 0;
    if (xrCamera) this.persistPose(xrCamera, true);
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
    const primaryMagnitude = Math.hypot(Number(axes[0]) || 0, Number(axes[1]) || 0);
    const secondaryMagnitude = Math.hypot(Number(axes[2]) || 0, Number(axes[3]) || 0);
    const axisOffset = secondaryMagnitude > primaryMagnitude ? 2 : 0;
    const stickX = Number(axes[axisOffset]) || 0;
    const stickY = Number(axes[axisOffset + 1]) || 0;
    const elapsed = Math.max(0, Math.min(0.05, Number(deltaSeconds) || 0));
    this.grabForward.set(0, 0, -1).applyQuaternion(this.scratchQuaternion);
    if (Math.abs(stickY) > 0.12) this.depthOffset = Math.max(-1, Math.min(4, this.depthOffset - stickY * elapsed * 1.8));
    this.root.position.addScaledVector(this.grabForward, this.depthOffset);
    if (Math.abs(stickX) > 0.12) {
      this.userScale = Math.max(0.45, Math.min(2.5, this.userScale * Math.exp(stickX * elapsed * 1.1)));
      this.root.scale.setScalar(this.userScale);
    }
  }

  resetPose() {
    this.grabbedController = null;
    this.grabInputSource = null;
    this.headLocked = true;
    this.depthOffset = 0;
    this.userScale = 1;
    this.headOffsetPosition.set(0, 0, 0);
    this.headOffsetQuaternion.identity();
    this.root.scale.setScalar(1);
    try { localStorage.removeItem('pandorabox.quest-hud-pose.v1'); } catch {}
    this.drawDashboard();
  }

  syncPose(xrCamera) {
    if (this.grabbedController) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    if (this.headLocked) {
      this.root.position.copy(this.scratchPosition);
      this.root.quaternion.copy(this.scratchQuaternion);
      return;
    }
    this.root.position.copy(this.headOffsetPosition).applyQuaternion(this.scratchQuaternion).add(this.scratchPosition);
    this.root.quaternion.copy(this.scratchQuaternion).multiply(this.headOffsetQuaternion);
  }

  loadSavedPose() {
    try {
      const saved = JSON.parse(localStorage.getItem('pandorabox.quest-hud-pose.v1') || 'null');
      if (!Array.isArray(saved?.position) || saved.position.length !== 3 || !Array.isArray(saved?.quaternion) || saved.quaternion.length !== 4) return;
      const values = [...saved.position, ...saved.quaternion, saved.scale].map(Number);
      if (!values.every(Number.isFinite) || values.slice(0, 3).some(value => Math.abs(value) > 20)) return;
      this.headOffsetPosition.fromArray(saved.position);
      this.headOffsetQuaternion.fromArray(saved.quaternion).normalize();
      this.userScale = Math.max(0.45, Math.min(2.5, Number(saved.scale)));
      this.root.scale.setScalar(this.userScale);
      this.headLocked = false;
    } catch {}
  }

  persistPose(xrCamera, force = false) {
    if (!xrCamera || this.headLocked || (!force && performance.now() - this.lastPosePersistAt < 750)) return;
    xrCamera.getWorldPosition(this.scratchPosition);
    xrCamera.getWorldQuaternion(this.scratchQuaternion);
    const inverseHead = this.scratchQuaternion.clone().invert();
    this.headOffsetPosition.copy(this.root.position).sub(this.scratchPosition).applyQuaternion(inverseHead);
    this.headOffsetQuaternion.copy(inverseHead).multiply(this.root.quaternion).normalize();
    const pose = {
      position: this.headOffsetPosition.toArray(),
      quaternion: this.headOffsetQuaternion.toArray(),
      scale: this.userScale,
    };
    try {
      localStorage.setItem('pandorabox.quest-hud-pose.v1', JSON.stringify(pose));
      this.lastPosePersistAt = performance.now();
    } catch {}
  }

  leaveSession() {
    this.grabbedController = null;
    this.grabInputSource = null;
  }
}
