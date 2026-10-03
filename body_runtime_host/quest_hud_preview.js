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
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width * .45, height * .45);
  const scale = radius / 6;
  for (let meters = 1; meters <= 6; meters += 1) {
    ctx.strokeStyle = meters % 2 === 0 ? 'rgba(120,190,150,.3)' : 'rgba(120,190,150,.15)';
    ctx.lineWidth = Math.max(1, scaleFactor * (meters % 2 === 0 ? 1.5 : 1));
    ctx.beginPath(); ctx.arc(cx, cy, meters * scale, 0, 2 * Math.PI); ctx.stroke();
    if (meters % 2 === 0) {
      ctx.fillStyle = '#779586'; ctx.font = `${Math.round(10 * scaleFactor)}px ui-monospace,monospace`;
      ctx.textAlign = 'left'; ctx.fillText(`${meters}m`, cx + 4, cy - meters * scale + 12 * scaleFactor);
    }
  }
  ctx.strokeStyle = 'rgba(120,190,150,.25)';
  for (const angle of [0, Math.PI / 2]) {
    ctx.beginPath(); ctx.moveTo(cx - Math.cos(angle) * radius, cy - Math.sin(angle) * radius); ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius); ctx.stroke();
  }
  const perception = world?.perception || {};
  if (mode === 'lidar') {
    const points = perception.sensor_projections?.lidar?.points || [];
    for (const point of points) {
      const local = worldLocal([Number(point.x), Number(point.y)], perception, perception.sensor_projections?.lidar?.frame);
      if (!local || local.distance > 6.2) continue;
      const x = cx - local.left * scale; const y = cy - local.forward * scale;
      const intensity = Math.max(.2, Math.min(1, Number(point.intensity ?? .7)));
      ctx.fillStyle = `rgba(94,221,228,${intensity})`;
      ctx.beginPath(); ctx.arc(x, y, (local.distance < 2 ? 3.6 : 2.4) * scaleFactor, 0, 2 * Math.PI); ctx.fill();
    }
  } else {
    const targets = perception.modalities?.mmwave_radar?.targets || [];
    for (const target of targets) {
      const local = worldLocal(target.position_m || target.position, perception, perception.modalities?.mmwave_radar?.frame);
      if (!local || local.distance > 6.2) continue;
      const x = cx - local.left * scale; const y = cy - local.forward * scale;
      ctx.fillStyle = target.classification === 'mobile_obstacle' ? '#ed91c5' : '#efcb76';
      ctx.strokeStyle = '#fff0c1'; ctx.lineWidth = 2 * scaleFactor;
      ctx.beginPath(); ctx.arc(x, y, 6.5 * scaleFactor, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#f5e8bf'; ctx.font = `${Math.round(9 * scaleFactor)}px ui-monospace,monospace`; ctx.textAlign = 'left';
      ctx.fillText(`${local.distance.toFixed(1)}m`, x + 9 * scaleFactor, y - 5 * scaleFactor);
    }
  }
  ctx.fillStyle = '#d9f5e4';
  ctx.beginPath(); ctx.moveTo(cx, cy - 13 * scaleFactor); ctx.lineTo(cx - 8 * scaleFactor, cy + 7 * scaleFactor); ctx.lineTo(cx + 8 * scaleFactor, cy + 7 * scaleFactor); ctx.closePath(); ctx.fill();
}

function drawRobot() {
  const group = $('robot-drawing');
  const degrees = Number(controller?.body_heading_deg ?? world?.perception?.body?.orientation * 180 / Math.PI ?? 0);
  group.setAttribute('transform', `rotate(${-degrees} 180 155)`);
  const legs = $('robot-legs');
  const active = controller?.spikes || [];
  legs.innerHTML = Array.from({ length: 6 }, (_, index) => {
    const row = index < 3 ? -1 : 1;
    const column = index % 3;
    const hx = 180 + (column - 1) * 23;
    const hy = 155 + row * 42;
    const kx = 180 + (column - 1) * 55;
    const ky = 155 + row * 77;
    const fx = 180 + (column - 1) * 84;
    const fy = 155 + row * (active[index] ? 122 : 113);
    const color = active[index] ? '#efcb76' : row < 0 ? '#76d5a0' : '#69bac2';
    return `<g stroke="${color}" stroke-width="8" fill="none"><path d="M${hx} ${hy} L${kx} ${ky} L${fx} ${fy}"/><circle cx="${fx}" cy="${fy}" r="5" fill="${color}"/></g>`;
  }).join('');
  const neurons = $('robot-neurons');
  neurons.innerHTML = Array.from({ length: 18 }, (_, index) => {
    const x = 27 + index * 18;
    const firing = Boolean(active[index]);
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
