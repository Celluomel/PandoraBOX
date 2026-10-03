const $ = id => document.getElementById(id);
let world = null;
let controller = null;
let cameraFrameId = null;
let cameraBusy = false;

function setText(id, value) { $(id).textContent = String(value); }

function resizeCanvas(canvas) {
  const bounds = canvas.getBoundingClientRect();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(bounds.width * ratio));
  const height = Math.max(1, Math.round(bounds.height * ratio));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  return { width, height, ratio };
}

function worldLocal(position, perception, frameName, assumeWorld = false) {
  if (!Array.isArray(position) || position.length < 2) return null;
  let forward = Number(position[0]);
  let left = Number(position[1]);
  const body = perception.sensor_projections?.frame?.body || perception.body?.position || [0, 0, 0];
  const yaw = Number(perception.sensor_projections?.frame?.yaw_rad ?? perception.body?.orientation ?? 0);
  if (assumeWorld || /^(body_world|world|map|local_map|odom)$/i.test(frameName || '')) {
    const dx = forward - Number(body[0] || 0);
    const dy = left - Number(body[1] || 0);
    forward = Math.cos(yaw) * dx + Math.sin(yaw) * dy;
    left = -Math.sin(yaw) * dx + Math.cos(yaw) * dy;
  }
  return { forward, left, distance: Math.hypot(forward, left) };
}

function drawMap(canvas, mode) {
  const { width, height } = resizeCanvas(canvas);
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#08110f'; ctx.fillRect(0, 0, width, height);
  const scaleFactor = Math.min(width, height) / 440;
  const lidarMode = mode === 'lidar';
  const cx = width / 2;
  const radius = Math.min(width * .44, height * .83);
  const cy = lidarMode ? height - 12 * scaleFactor : height - 12 * scaleFactor;
  const scale = radius / 6;
  ctx.strokeStyle = 'rgba(120,190,150,.18)';
  ctx.lineWidth = Math.max(1, scaleFactor);
  if (lidarMode) {
    for (let meters = 1; meters <= 6; meters += 1) {
      ctx.strokeStyle = meters % 2 === 0 ? 'rgba(120,190,150,.3)' : 'rgba(120,190,150,.15)';
      ctx.beginPath(); ctx.arc(cx, cy, meters * scale, Math.PI, Math.PI * 2); ctx.stroke();
    }
    for (let spoke = 0; spoke <= 12; spoke += 1) {
      const angle = Math.PI + spoke * Math.PI / 12;
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius); ctx.stroke();
    }
    ctx.fillStyle = '#a8c3b1'; ctx.font = `${Math.round(8 * scaleFactor)}px ui-monospace,monospace`; ctx.textAlign = 'center';
    ctx.fillText('LEFT', cx - radius + 8 * scaleFactor, cy + 3 * scaleFactor);
    ctx.fillText('FRONT', cx, cy - radius + 10 * scaleFactor);
    ctx.fillText('RIGHT', cx + radius - 8 * scaleFactor, cy + 3 * scaleFactor);
  } else {
    const top = 10 * scaleFactor;
    const left = 24 * scaleFactor;
    const right = width - 12 * scaleFactor;
    const bottom = height - 22 * scaleFactor;
    ctx.fillStyle = 'rgba(15,34,30,.46)'; ctx.fillRect(left, top, right - left, bottom - top);
    for (let i = 0; i <= 6; i += 1) {
      const gx = left + (right - left) * i / 6;
      const gy = top + (bottom - top) * i / 6;
      ctx.strokeStyle = i % 2 === 0 ? 'rgba(120,190,150,.25)' : 'rgba(120,190,150,.12)';
      ctx.beginPath(); ctx.moveTo(gx, top); ctx.lineTo(gx, bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(left, gy); ctx.lineTo(right, gy); ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(94,221,228,.45)'; ctx.beginPath(); ctx.moveTo(cx, top); ctx.lineTo(cx, bottom); ctx.stroke();
    ctx.fillStyle = '#a8c3b1'; ctx.font = `${Math.round(8 * scaleFactor)}px ui-monospace,monospace`; ctx.textAlign = 'center';
    ctx.fillText('LEFT', left, bottom + 10 * scaleFactor); ctx.fillText('FORWARD · 6 M', cx, top + 10 * scaleFactor); ctx.fillText('RIGHT', right, bottom + 10 * scaleFactor);
  }
  const perception = world?.perception || {};
  if (mode === 'lidar') {
    const points = perception.sensor_projections?.lidar?.points || [];
    const returns = points.map(point => ({
      point,
      local: worldLocal([Number(point.x), Number(point.y)], perception, perception.sensor_projections?.lidar?.frame),
    })).filter(item => item.local && item.local.distance <= 6.2).map(item => ({
      ...item,
      x: cx - item.local.left * scale,
      y: cy - item.local.forward * scale,
    })).sort((a, b) => Math.atan2(a.y - cy, a.x - cx) - Math.atan2(b.y - cy, b.x - cx));
    ctx.save(); ctx.setLineDash([3 * scaleFactor, 4 * scaleFactor]);
    ctx.strokeStyle = 'rgba(94,221,228,.38)'; ctx.lineWidth = Math.max(1, scaleFactor);
    for (let index = 0; index < returns.length; index += 1) {
      const current = returns[index]; const next = returns[(index + 1) % returns.length];
      if (current.local.forward < 0 || next.local.forward < 0) continue;
      const a = Math.atan2(current.y - cy, current.x - cx);
      const b = Math.atan2(next.y - cy, next.x - cx);
      const gap = (b - a + Math.PI * 2) % (Math.PI * 2);
      if (gap > .75 || Math.abs(current.local.distance - next.local.distance) > .7) continue;
      ctx.beginPath(); ctx.moveTo(current.x, current.y); ctx.lineTo(next.x, next.y); ctx.stroke();
    }
    ctx.restore();
    for (const { point, local, x, y } of returns) {
      const intensity = Math.max(.2, Math.min(1, Number(point.intensity ?? .7)));
      if (local.forward < 0) continue;
      const dot = (local.distance < 2 ? 3.6 : 2.8) * scaleFactor;
      ctx.fillStyle = `rgba(94,221,228,${intensity * .2})`;
      ctx.beginPath(); ctx.arc(x, y, dot * 2.5, 0, 2 * Math.PI); ctx.fill();
      ctx.fillStyle = `rgba(94,221,228,${intensity})`;
      ctx.beginPath(); ctx.arc(x, y, dot, 0, 2 * Math.PI); ctx.fill();
    }
  } else {
    const targets = perception.modalities?.mmwave_radar?.targets || [];
    for (const target of targets) {
      const local = worldLocal(target.position_m || target.position, perception, perception.modalities?.mmwave_radar?.frame);
      if (!local || local.distance > 6.2) continue;
      const left = 24 * scaleFactor; const right = width - 12 * scaleFactor;
      const top = 10 * scaleFactor; const bottom = height - 22 * scaleFactor;
      if (local.forward < 0 || Math.abs(local.left) > 6) continue;
      const x = cx - local.left * ((right - left) / 12); const y = bottom - local.forward * ((bottom - top) / 6);
      const color = target.classification === 'mobile_obstacle' ? '#ed91c5' : '#efcb76';
      const confidence = Math.max(.3, Math.min(1, Number(target.confidence ?? .7)));
      ctx.strokeStyle = color; ctx.globalAlpha = .2 + confidence * .2; ctx.lineWidth = 1.5 * scaleFactor;
      ctx.beginPath(); ctx.arc(x, y, (11 + (1 - confidence) * 8) * scaleFactor, 0, 2 * Math.PI); ctx.stroke();
      ctx.globalAlpha = 1;
      const velocity = target.velocity_mps || target.velocity || [0, 0];
      let forwardSpeed = Number(velocity[0] || 0); let leftSpeed = Number(velocity[1] || 0);
      const radarFrame = perception.modalities?.mmwave_radar?.frame || 'body';
      if (/^(body_world|world|map|local_map|odom)$/i.test(radarFrame)) {
        const yaw = Number(perception.sensor_projections?.frame?.yaw_rad ?? perception.body?.orientation ?? 0);
        const worldForward = forwardSpeed;
        forwardSpeed = Math.cos(yaw) * worldForward + Math.sin(yaw) * leftSpeed;
        leftSpeed = -Math.sin(yaw) * worldForward + Math.cos(yaw) * leftSpeed;
      }
      const rangeRate = (local.forward * forwardSpeed + local.left * leftSpeed) / Math.max(local.distance, .1);
      const bearingRate = (-local.forward * leftSpeed + local.left * forwardSpeed) / Math.max(local.distance ** 2, .01);
      const vectorX = bearingRate * ((right - left) / 2) / (Math.PI / 3) * .5;
      const vectorY = -rangeRate * ((bottom - top) / 6) * .5;
      if (Math.hypot(vectorX, vectorY) > 3 * scaleFactor) {
        ctx.strokeStyle = color; ctx.lineWidth = 2 * scaleFactor;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + vectorX, y + vectorY); ctx.stroke();
      }
      ctx.fillStyle = color; ctx.strokeStyle = '#fff0c1'; ctx.lineWidth = 1.5 * scaleFactor;
      ctx.beginPath(); ctx.arc(x, y, 5.5 * scaleFactor, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
      const speed = Math.hypot(Number(velocity[0] || 0), Number(velocity[1] || 0));
      ctx.fillStyle = color; ctx.font = `600 ${Math.round(8 * scaleFactor)}px ui-monospace,monospace`; ctx.textAlign = 'center';
      ctx.fillText(target.classification === 'mobile_obstacle' ? 'M' : '•', x, y - 8 * scaleFactor);
    }
  }
  if (lidarMode) {
    ctx.fillStyle = '#d9f5e4';
    ctx.beginPath(); ctx.moveTo(cx, cy - 13 * scaleFactor); ctx.lineTo(cx - 8 * scaleFactor, cy + 7 * scaleFactor); ctx.lineTo(cx + 8 * scaleFactor, cy + 7 * scaleFactor); ctx.closePath(); ctx.fill();
  } else {
    const originY = height - 22 * scaleFactor;
    ctx.strokeStyle = '#d9f5e4'; ctx.fillStyle = '#08110f'; ctx.lineWidth = Math.max(1, scaleFactor);
    ctx.beginPath(); ctx.roundRect(cx - 7 * scaleFactor, originY - 13 * scaleFactor, 14 * scaleFactor, 11 * scaleFactor, 3 * scaleFactor); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx - 4 * scaleFactor, originY - 13 * scaleFactor); ctx.lineTo(cx, originY - 20 * scaleFactor); ctx.lineTo(cx + 4 * scaleFactor, originY - 13 * scaleFactor); ctx.stroke();
  }
}

function drawRobot() {
  const group = $('robot-drawing');
  const heading = Number(controller?.body_heading_deg ?? (world?.perception?.body?.orientation ?? 0) * 180 / Math.PI);
  const visualHeading = ((90 - heading) % 360 + 360) % 360;
  group.setAttribute('transform', `rotate(${visualHeading} 180 155)`);
  const legs = $('robot-legs');
  const spikes = controller?.spikes || [];
  const jointsByPhysicalLeg = controller?.joint_targets || [];
  const visualToPhysicalLeg = [0, 2, 4, 1, 3, 5];
  legs.innerHTML = Array.from({ length: 6 }, (_, index) => {
    const row = index % 3;
    const side = index < 3 ? -1 : 1;
    const longitudinal = row - 1;
    const hx = 180 + side * 39;
    const hy = 105 + row * 50;
    const physicalLeg = visualToPhysicalLeg[index];
    const [coxa = 0, femur = 0, tibia = 0] = jointsByPhysicalLeg[physicalLeg] || [];
    const lift = Number(controller?.foot_lift?.[physicalLeg] || 0);
    const coxaX = hx + side * (24 + Number(coxa) * 4);
    const coxaY = hy + Number(coxa) * 4;
    const femurX = coxaX + side * (31 + Number(femur) * 3);
    const femurY = coxaY + longitudinal * (9 + Number(femur) * 3);
    const footX = femurX + side * (34 + Number(tibia) * 3);
    const footY = femurY + longitudinal * (11 + Number(tibia) * 4) - Math.max(0, lift) * 10;
    const legColor = spikes.slice(physicalLeg * 3, physicalLeg * 3 + 3).some(Boolean) ? '#efcb76' : side < 0 ? '#76d5a0' : '#69bac2';
    const points = [[coxaX, coxaY], [femurX, femurY], [footX, footY]];
    const links = [[hx, hy, coxaX, coxaY], [coxaX, coxaY, femurX, femurY], [femurX, femurY, footX, footY]];
    const servoMarkup = points.map(([x, y], joint) => {
      const servoId = index * 3 + joint + 1;
      const servoColor = ['#83cbd1', '#9ce0b4', '#efcb76'][joint];
      const anchor = side < 0 ? 'end' : 'start';
      return `<circle cx="${x}" cy="${y}" r="4.3" fill="${servoColor}" stroke="#07110d" stroke-width="1.5"/><text x="${x + side * 5}" y="${y - 6}" text-anchor="${anchor}" fill="${servoColor}" font-size="6" font-family="monospace">${String(servoId).padStart(2, '0')}</text>`;
    }).join('');
    const linkMarkup = links.map(([x1, y1, x2, y2], segment) => `<path d="M${x1} ${y1} L${x2} ${y2}" stroke="${segment === 2 ? legColor : '#92b8a1'}" stroke-width="${segment === 2 ? 6 : 7}" stroke-linecap="round"/>`).join('');
    return `<g>${linkMarkup}${servoMarkup}<circle cx="${footX}" cy="${footY}" r="5.5" fill="${legColor}" stroke="#07110d" stroke-width="1.5"/><text x="${footX + side * 8}" y="${footY + 3}" text-anchor="${side < 0 ? 'end' : 'start'}" fill="#dcebe2" font-size="7" font-family="monospace">L${index + 1}</text></g>`;
  }).join('');
  const neurons = $('robot-neurons');
  neurons.innerHTML = Array.from({ length: 18 }, (_, index) => {
    const x = 27 + index * 18;
    const firing = Boolean(spikes[index]);
    const groupColor = index < 6 ? '#80dfaa' : index < 12 ? '#86cbd2' : '#c6a2e8';
    return `<circle cx="${x}" cy="278" r="${firing ? 4.3 : 2.6}" fill="${firing ? '#efcb76' : groupColor}" opacity="${firing ? 1 : .58}"/>`;
  }).join('');
}

function updateStatus() {
  if (!world?.perception?.available) {
    setText('status', world?.perception?.note || 'Waiting for Body perception…');
    return;
  }
  const perception = world.perception;
  const lidarCount = perception.sensor_projections?.lidar?.points?.length || 0;
  const radarCount = perception.modalities?.mmwave_radar?.targets?.length || 0;
  setText('status', `${perception.source || 'Body'} · observation ${Number(perception.age_seconds || 0).toFixed(1)} s old · ${lidarCount} LiDAR returns · ${radarCount} radar targets`);
  setText('connection', world.running ? 'Body connected · simulation running' : 'Body connected · simulation paused');
  setText('object-count', `${(perception.objects || []).length} OBJECTS`);
  const p = perception.body?.position || [];
  setText('position', p.length > 1 ? `${Number(p[0]).toFixed(2)}, ${Number(p[1]).toFixed(2)} m` : 'waiting');
  setText('body-heading', `${Math.round(Number(controller?.compass_heading_deg ?? (Number(perception.body?.orientation || 0) * 180 / Math.PI)))}°`);
  setText('body-gait', controller?.gait || 'idle');
  setText('verified', controller?.locomotion_verified ? 'verified' : 'not measured');
  setText('follow-state', world.running ? 'SIMULATION · RUNNING' : 'SCENE VIEW · FIXED');
  setText('gait', controller?.gait || 'waiting');
  setText('phase', Number.isFinite(Number(controller?.cpg_phase)) ? `${Math.round(Number(controller.cpg_phase) * 180 / Math.PI)}°` : '—');
  setText('spikes', `${(controller?.spikes || []).filter(Boolean).length} / 18`);
  setText('heading', Number.isFinite(Number(controller?.compass_heading_deg ?? controller?.body_heading_deg)) ? `${Math.round(Number(controller?.compass_heading_deg ?? controller?.body_heading_deg))}°` : '—');
  setText('steps', controller?.step ?? controller?.worldmodel_step ?? '—');
  setText('head', 'not in XR');
  setText('left', 'not in XR'); setText('right', 'not in XR');
  setText('lidar-count', `${lidarCount} pts`); setText('radar-count', `${radarCount} targets`);
  drawRobot(); drawMap($('lidar-map'), 'lidar'); drawMap($('radar-map'), 'radar');
}

async function poll() {
  try {
    const [worldResponse, controllerResponse] = await Promise.all([
      fetch('/worldmodel/status', { cache: 'no-store' }),
      fetch('/plugins/fnk0031_wifi/controller', { cache: 'no-store' }),
    ]);
    if (!worldResponse.ok) throw new Error(`World model HTTP ${worldResponse.status}`);
    world = await worldResponse.json();
    if (controllerResponse.ok) controller = await controllerResponse.json();
    updateStatus();
  } catch (error) {
    setText('connection', 'Body unavailable'); setText('status', error.message);
  }
}

async function pollCamera() {
  if (cameraBusy) return;
  cameraBusy = true;
  try {
    const response = await fetch('/body/camera/frame', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Camera HTTP ${response.status}`);
    const result = await response.json();
    const frame = result.camera || {};
    if (!result.available || !frame.image_base64) {
      $('camera-empty').hidden = false;
      $('camera-empty').textContent = `CAMERA ${String(result.status || 'UNAVAILABLE').toUpperCase()}`;
      $('camera-state').textContent = 'NO FRAME'; $('camera-source').textContent = 'Body camera · no frame'; $('camera-size').textContent = 'resolution —'; cameraFrameId = null; return;
    }
    const id = frame.frame_id || frame.captured_at || frame.timestamp;
    if (id !== cameraFrameId) {
      cameraFrameId = id;
      $('camera').src = `data:${frame.mime_type || 'image/jpeg'};base64,${frame.image_base64}`;
      $('camera-empty').hidden = true; $('camera-state').textContent = 'LIVE';
      $('camera-source').textContent = frame.source || result.source || 'Body camera · live';
      $('camera-size').textContent = Number(frame.width) > 0 && Number(frame.height) > 0 ? `${frame.width} × ${frame.height}` : 'resolution unavailable';
    }
  } catch {
    $('camera-empty').hidden = false; $('camera-state').textContent = 'UNAVAILABLE';
  } finally { cameraBusy = false; }
}

window.addEventListener('resize', updateStatus);
void poll(); void pollCamera();
setInterval(poll, 800); setInterval(pollCamera, 400);
