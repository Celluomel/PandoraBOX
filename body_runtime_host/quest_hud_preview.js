import * as THREE from '../frontend/node_modules/three/build/three.module.js';
import { createFnk0031Visual } from './fnk0031_visual.js';

const $ = id => document.getElementById(id);
let world = null;
let controller = null;
let liveImu = null;
let lastValidImu = null;
let lastValidImuAt = 0;
let liveTof = null;
let liveRadar = null;
let liveGps = null;
let liveUltrasonic = null;
let ultrasonicStatusReceived = false;
const lastUltrasonicSamples = Object.create(null);
let cameraFrameId = null;
let cameraBusy = false;
let cameraDisplayKey = null;
let imuBusy = false;
let tofBusy = false;
let robotVisual = null;
let robotRenderer = null;
let robotScene = null;
let robotCamera = null;

function renderRobotVisual() {
  if (!robotRenderer) return;
  const area = $('robot-3d').parentElement;
  const width = Math.max(1, area.clientWidth);
  const height = Math.max(1, area.clientHeight);
  robotCamera.aspect = width / height;
  robotCamera.updateProjectionMatrix();
  robotRenderer.setSize(width, height, false);
  robotRenderer.render(robotScene, robotCamera);
}

function initRobotVisual() {
  try {
    const target = $('robot-3d');
    robotRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
    robotRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    robotRenderer.outputColorSpace = THREE.SRGBColorSpace;
    robotRenderer.setClearColor('#07120f', 0);
    target.appendChild(robotRenderer.domElement);
    robotScene = new THREE.Scene();
    robotScene.add(new THREE.HemisphereLight('#ebfaf5', '#1a2828', 2.1));
    const key = new THREE.DirectionalLight('#e2f7ed', 2.7);
    key.position.set(-2, 4, 5);
    robotScene.add(key);
    const rim = new THREE.DirectionalLight('#72cde1', 1.4);
    rim.position.set(3, 2, -3);
    robotScene.add(rim);
    robotVisual = createFnk0031Visual(THREE);
    robotVisual.group.rotation.y = -.28;
    robotScene.add(robotVisual.group);
    robotCamera = new THREE.PerspectiveCamera(38, 1, .1, 40);
    robotCamera.position.set(1.8, 1.65, 4.3);
    robotCamera.lookAt(0, .52, 0);
    target.parentElement.classList.add('model-ready');
    renderRobotVisual();
  } catch (error) {
    robotRenderer?.dispose();
    robotRenderer = null;
    robotVisual = null;
    console.warn('FNK0031 3D preview unavailable; showing schematic.', error);
  }
}

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

function radarTargetToHud(target, radar) {
  const position = target.position_m || target.position || [];
  const velocity = target.velocity_mps || target.velocity || [0, 0];
  if (/^hlk_ld2450/i.test(String(radar.source || ''))) {
    return {
      position: [Number(position[1]), -Number(position[0]), Number(position[2] || 0)],
      velocity: [Number(velocity[1] || 0), -Number(velocity[0] || 0)],
    };
  }
  return { position, velocity };
}

function drawMap(canvas, mode) {
  const { width, height, ratio } = resizeCanvas(canvas);
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#08110f'; ctx.fillRect(0, 0, width, height);
  const scaleFactor = Math.min(width, height) / 440;
  const lidarMode = mode === 'lidar';
  const cx = width / 2;
  const radius = Math.min(width * .44, height * .83);
  const cy = lidarMode ? height - 12 * scaleFactor : height - 12 * scaleFactor;
  const scale = radius / 6;
  const top = 10 * scaleFactor;
  const left = 24 * scaleFactor;
  const right = width - 12 * scaleFactor;
  const bottom = height - 22 * scaleFactor;
  const lateralLimit = Math.tan(Math.PI / 3) * 6;
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
    ctx.fillText(`-${lateralLimit.toFixed(1)} m`, left + 12 * scaleFactor, bottom + 10 * scaleFactor);
    ctx.fillText('0 m · FORWARD 6 m', cx, top + 10 * scaleFactor);
    ctx.fillText(`+${lateralLimit.toFixed(1)} m`, right - 12 * scaleFactor, bottom + 10 * scaleFactor);
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
    const radar = liveRadar?.sample || perception.modalities?.mmwave_radar || {};
    const targets = radar.targets || [];
    for (const target of targets) {
      const hudTarget = radarTargetToHud(target, radar);
      const local = worldLocal(hudTarget.position, perception, radar.frame);
      if (!local || local.distance > 6.2) continue;
      const left = 24 * scaleFactor; const right = width - 12 * scaleFactor;
      const top = 10 * scaleFactor; const bottom = height - 22 * scaleFactor;
      const bearing = Math.atan2(-local.left, local.forward);
      if (local.forward < 0 || Math.abs(bearing) > Math.PI / 3 || Math.abs(local.left) > lateralLimit) continue;
      const x = cx - local.left * ((right - left) / (2 * lateralLimit)); const y = bottom - local.forward * ((bottom - top) / 6);
      const velocity = hudTarget.velocity;
      const radialSpeed = Number(target.radial_speed_mps);
      const classification = String(target.classification || '').toLowerCase();
      const isMoving = /moving|mobile/.test(classification)
        || (Number.isFinite(radialSpeed) && Math.abs(radialSpeed) >= 0.05)
        || Math.hypot(Number(velocity[0] || 0), Number(velocity[1] || 0)) >= 0.05;
      const color = isMoving ? '#ed91c5' : '#efcb76';
      const confidence = Math.max(.3, Math.min(1, Number(target.confidence ?? .7)));
      ctx.strokeStyle = color; ctx.globalAlpha = .2 + confidence * .2; ctx.lineWidth = 1.5 * scaleFactor;
      ctx.beginPath(); ctx.arc(x, y, (11 + (1 - confidence) * 8) * scaleFactor, 0, 2 * Math.PI); ctx.stroke();
      ctx.globalAlpha = 1;
      let forwardSpeed = Number(velocity[0] || 0); let leftSpeed = Number(velocity[1] || 0);
      const radarFrame = radar.frame || 'body';
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
      ctx.fillStyle = color; ctx.font = `600 ${Math.round(8 * scaleFactor)}px ui-monospace,monospace`; ctx.textAlign = 'center';
      ctx.fillText(isMoving ? 'M' : '•', x, y - 8 * scaleFactor);
      {
        const rangeLabel = `${local.distance.toFixed(2)} m`;
        const speedLabel = Number.isFinite(radialSpeed) ? `${radialSpeed >= 0 ? '+' : ''}${radialSpeed.toFixed(2)} m/s` : '';
        const speedFont = Math.max(14 * ratio, Math.round(15 * scaleFactor));
        const labelPadding = 4 * ratio;
        const labelWidth = speedFont * Math.max(rangeLabel.length, speedLabel.length) * .62 + labelPadding * 2;
        const labelHeight = speedFont * (speedLabel ? 2 : 1) + labelPadding * 2;
        const labelGap = 10 * ratio;
        ctx.font = `600 ${speedFont}px ui-monospace,monospace`; ctx.textAlign = 'left';
        const preferredX = x > cx ? x - labelGap - labelWidth : x + labelGap;
        const labelX = Math.max(left, Math.min(right - labelWidth, preferredX));
        const labelY = Math.max(top + labelHeight, Math.min(bottom - labelPadding, y + speedFont * .35));
        ctx.fillStyle = 'rgba(4, 13, 11, .92)'; ctx.fillRect(labelX - labelPadding, labelY - labelHeight, labelWidth, labelHeight);
        ctx.fillStyle = color; ctx.fillText(rangeLabel, labelX, labelY - (speedLabel ? speedFont : 0));
        if (speedLabel) ctx.fillText(speedLabel, labelX, labelY);
      }
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

function drawTofRangeBar(sample = liveTof || world?.perception?.modalities?.tof || {}) {
  const marker = $('tof-marker');
  const value = $('tof-value');
  const track = marker?.parentElement;
  if (!marker || !value || !track) return;
  const distance = Number(sample.distance_m);
  const ageSeconds = Date.now() / 1000 - Number(sample.timestamp || 0);
  const fresh = sample.available === true && Number.isFinite(distance)
    && distance >= 0 && distance <= 4 && !sample.simulated
    && Number.isFinite(ageSeconds) && ageSeconds >= -1 && ageSeconds <= 2.5;
  value.textContent = fresh ? `${distance.toFixed(2)}m` : 'WAIT';
  marker.style.top = fresh ? `${100 - Math.max(0, Math.min(100, distance / 4 * 100))}%` : '100%';
  track.setAttribute('aria-valuenow', fresh ? distance.toFixed(2) : '0');
  track.setAttribute('aria-valuetext', fresh ? `${distance.toFixed(2)} metres` : 'No current measurement');
  value.style.color = fresh ? (distance < 0.5 ? '#f17c70' : distance < 1.2 ? '#efcb76' : '#bcebd0') : '#91a79b';
}

function drawUltrasonicRanges(modalities = world?.perception?.modalities || {}) {
  const group = ultrasonicStatusReceived
    ? (liveUltrasonic?.sample || {})
    : (modalities.ultrasonic || modalities.hc_sr04 || {});
  const samples = Array.isArray(group) ? group : Array.isArray(group.sensors) ? group.sensors : [];
  const keys = ['front_left', 'front_right', 'rear'];
  const now = Date.now();
  for (const sample of samples) {
    const key = String(sample?.id || sample?.position || '').toLowerCase();
    const distance = Number(sample?.distance_m ?? (Number(sample?.distance_mm) / 1000));
    if (keys.includes(key) && sample.available === true && Number.isFinite(distance) && distance > 0 && distance <= 4 && !sample.simulated) {
      lastUltrasonicSamples[key] = { sample, measurementAt: now - (Number(sample.age_ms) || 0) };
    }
  }
  for (const card of document.querySelectorAll('[data-ultrasonic]')) {
    const key = card.dataset.ultrasonic;
    const currentSample = group[key] || samples.find(item => String(item?.id || item?.position || '').toLowerCase() === key)
      || samples[keys.indexOf(key)] || {};
    const currentDistance = Number(currentSample.distance_m ?? (Number(currentSample.distance_mm) / 1000));
    const currentValid = currentSample.available === true && Number.isFinite(currentDistance)
      && currentDistance > 0 && currentDistance <= 4 && !currentSample.simulated;
    const retained = lastUltrasonicSamples[key];
    const retainedAge = retained ? now - retained.measurementAt : Infinity;
    const held = !currentValid && retainedAge <= 1200;
    const sample = currentValid ? currentSample : held ? retained.sample : currentSample;
    const distance = Number(sample.distance_m ?? (Number(sample.distance_mm) / 1000));
    const available = sample.available === true && Number.isFinite(distance) && distance > 0 && distance <= 4 && !sample.simulated;
    const value = card.querySelector('.ultrasonic-value');
    const fill = card.querySelector('.ultrasonic-fill');
    value.textContent = available ? `${held || (Number.isFinite(retainedAge) && retainedAge > 600) ? '~' : ''}${distance.toFixed(2)}m` : 'WAIT';
    value.classList.toggle('sensor-wait', !available);
    value.style.color = available ? (held || (Number.isFinite(retainedAge) && retainedAge > 600) ? '#efcb76' : distance < .35 ? '#f17c70' : distance < .8 ? '#efcb76' : '#bcebd0') : '';
    fill.style.width = available ? `${Math.max(0, Math.min(100, distance / 4 * 100))}%` : '0%';
    fill.style.background = available ? (held || (Number.isFinite(retainedAge) && retainedAge > 600) ? '#efcb76' : distance < .35 ? '#f17c70' : distance < .8 ? '#efcb76' : '#63d7ae') : '';
  }
}

function drawRobot() {
  if (robotVisual) {
    robotVisual.setTelemetry(controller || {});
    renderRobotVisual();
    return;
  }
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

function drawNavigation(perception = world?.perception || {}, telemetry = controller || {}) {
  const modalities = perception.modalities || {};
  const imuSource = liveImu?.available ? liveImu.sample : (modalities.imu || telemetry.imu || {});
  const unwrap = value => value?.data && typeof value.data === 'object' ? value.data : value || {};
  const imu = unwrap(imuSource);
  const gps = unwrap(liveGps?.sample || liveGps?.source_status?.sample || modalities.gps || modalities.gnss || perception.body?.geo || telemetry.gps);
  const number = value => value === null || value === undefined || value === '' ? NaN : Number(value);
  const unit = imu.angle_unit || imu.unit || (imuSource === telemetry.imu ? 'rad' : '');
  const degrees = (value, sourceUnit) => Number.isFinite(number(value)) ? (String(sourceUnit).toLowerCase().includes('rad') ? number(value) * 180 / Math.PI : number(value)) : NaN;
  const pitch = degrees(imu.pitch_deg ?? imu.pitch_rad ?? imu.pitch, imu.pitch_deg !== undefined ? 'deg' : unit);
  const roll = degrees(imu.roll_deg ?? imu.roll_rad ?? imu.roll, imu.roll_deg !== undefined ? 'deg' : unit);
  const hasImu = Number.isFinite(pitch) && Number.isFinite(roll);
  setText('nav-attitude-value', hasImu ? `R ${roll.toFixed(1)}° · P ${pitch.toFixed(1)}°` : 'NO IMU DATA');
  const imuUnavailable = liveImu?.available ? 'ACQUIRING ATTITUDE'
    : !liveImu ? 'Waiting for IMU'
    : liveImu.error?.includes('404') ? 'Body update required'
      : !liveImu.enabled ? 'Enable Modulino in Robot hardware'
      : !liveImu.bridge_available ? 'No local Arduino Bridge'
        : liveImu.error ? 'Bridge or sensor unavailable' : 'Waiting for sample';
  const imuAge = lastValidImuAt ? (Date.now() - lastValidImuAt) / 1000 : Infinity;
  setText('nav-attitude-source', hasImu
    ? `${String(imu.source || imuSource.source || 'IMU').toUpperCase()}${liveImu?.held_for_s ? ` · HOLD ${liveImu.held_for_s.toFixed(1)}s` : ''}`
    : lastValidImu && imuAge <= 2.5 ? `LAST VALID · ${imuAge.toFixed(1)}s`
      : imuUnavailable);

  const heading = number(telemetry.magnetic_heading_deg ?? telemetry.compass_heading_deg);
  const moving = number(telemetry.speed_mps ?? perception.body?.velocity_mps) > .4;
  const course = number(gps.course_deg);
  const yawRad = number(perception.body?.orientation);
  const headingDeg = Number.isFinite(heading) ? heading : moving && Number.isFinite(course) ? course : Number.isFinite(yawRad) ? 90 - yawRad * 180 / Math.PI : NaN;
  const headingSource = Number.isFinite(number(telemetry.magnetic_heading_deg)) ? 'MAG' : Number.isFinite(heading) ? String(telemetry.heading_source || 'ODOM').toUpperCase() : moving && Number.isFinite(course) ? 'GPS COG' : 'EST';
  setText('nav-heading-value', Number.isFinite(headingDeg) ? `${Math.round((headingDeg % 360 + 360) % 360)}°` : '—°');
  setText('nav-heading-source', `CAP · ${headingSource}`);

  const lat = number(gps.latitude_deg ?? gps.latitude ?? gps.lat);
  const lon = number(gps.longitude_deg ?? gps.longitude ?? gps.lon ?? gps.lng);
  const quality = number(gps.fix_quality ?? gps.fixQuality);
  const hasFix = Number.isFinite(lat) && Math.abs(lat) <= 90 && Number.isFinite(lon) && Math.abs(lon) <= 180
    && (gps.fix === true || gps.valid === true || gps.status === 'fix' || gps.status === 'valid' || quality > 0);
  const accuracy = number(gps.horizontal_accuracy_m ?? gps.accuracy_m);
  const hdop = number(gps.hdop);
  const satellites = number(gps.satellites);
  const satellitesInView = number(gps.satellites_in_view);
  const gpsDiagnostic = liveGps?.source_status?.diagnostic || {};
  const streamOnline = Boolean(gps.connected || liveGps?.available || Number(gpsDiagnostic.bytes_received) > 0);
  const state = hasFix ? 'FIX' : streamOnline ? 'UART LIVE · NO FIX' : 'NO GPS DATA';
  $('nav-gps').innerHTML = `<small>GPS · ${state}</small>${hasFix ? `${lat.toFixed(6)}°, ${lon.toFixed(6)}°` : streamOnline ? 'WAITING FOR FIX' : 'CHECK D0/D1'}<small>${Number.isFinite(satellites) ? `${satellites} USED` : 'USED —'}${Number.isFinite(satellitesInView) ? ` · ${satellitesInView} VIEW` : ''}${Number.isFinite(hdop) ? ` · HDOP ${hdop.toFixed(1)}` : ''}</small>`;
  const signals = Array.isArray(gps.satellite_signals) ? gps.satellite_signals.slice(0, 6) : [];
  $('nav-gps-satellites').innerHTML = signals.map(satellite => {
    const cn0 = number(satellite.cn0_db_hz);
    const height = Number.isFinite(cn0) ? Math.max(2, Math.min(20, cn0 * .34)) : 2;
    const tone = cn0 >= 35 ? '#69d49c' : cn0 >= 25 ? '#efcb76' : '#e88775';
    const id = `${String(satellite.talker || 'GN').replace(/[^A-Z0-9]/gi, '')}-${Math.round(number(satellite.svid) || 0)}`;
    const title = `${id} · C/N₀ ${Number.isFinite(cn0) ? cn0.toFixed(0) : '—'} dB-Hz · az ${satellite.azimuth_deg ?? '—'}° · el ${satellite.elevation_deg ?? '—'}°`;
    return `<div class="gps-signal" title="${title}"><span>${Number.isFinite(cn0) ? cn0.toFixed(0) : '—'}</span><i style="height:${height}px;background:${tone}"></i><span>${id}</span></div>`;
  }).join('');

  const canvas = $('nav-horizon');
  const { width, height, ratio } = resizeCanvas(canvas);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const w = width / ratio; const h = height / ratio;
  const cx = w / 2; const cy = h / 2; const radius = Math.max(12, Math.min(w, h) * .31);
  ctx.clearRect(0, 0, w, h);
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = '#173b43'; ctx.fillRect(cx - radius, cy - radius, radius * 2, radius);
  ctx.fillStyle = '#665743'; ctx.fillRect(cx - radius, cy, radius * 2, radius);
  ctx.translate(cx, cy); if (hasImu) ctx.rotate(-roll * Math.PI / 180);
  ctx.translate(0, hasImu ? Math.max(-radius * .65, Math.min(radius * .65, pitch * .85)) : 0);
  ctx.strokeStyle = '#d7eee6'; ctx.lineWidth = 1.4;
  ctx.beginPath(); ctx.moveTo(-radius * .8, 0); ctx.lineTo(radius * .8, 0); ctx.stroke();
  for (const deg of [-30, -20, -10, 10, 20, 30]) { const yy = deg * radius / 42; const half = deg % 20 === 0 ? radius * .24 : radius * .15; ctx.beginPath(); ctx.moveTo(-half, yy); ctx.lineTo(half, yy); ctx.stroke(); }
  ctx.restore();
  ctx.strokeStyle = '#9ce5ba'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = '#f0f5e9'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(cx - radius * .28, cy); ctx.lineTo(cx - radius * .1, cy); ctx.lineTo(cx, cy + radius * .08); ctx.lineTo(cx + radius * .1, cy); ctx.lineTo(cx + radius * .28, cy); ctx.stroke();
  const ring = radius + 15;
  ctx.strokeStyle = 'rgba(169,232,194,.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(cx, cy, ring, 0, Math.PI * 2); ctx.stroke();
  ctx.save(); ctx.translate(cx, cy);
  for (let bearing = 0; bearing < 360; bearing += 15) {
    const angle = (-90 + bearing - (Number.isFinite(headingDeg) ? headingDeg : 0)) * Math.PI / 180;
    const major = bearing % 45 === 0;
    ctx.strokeStyle = major ? '#a9e8c2' : 'rgba(169,232,194,.55)'; ctx.lineWidth = major ? 1.5 : 1;
    ctx.beginPath(); ctx.moveTo(Math.cos(angle) * (ring - (major ? 6 : 3)), Math.sin(angle) * (ring - (major ? 6 : 3))); ctx.lineTo(Math.cos(angle) * (ring - 1), Math.sin(angle) * (ring - 1)); ctx.stroke();
    if (bearing % 90 === 0) {
      ctx.fillStyle = '#d5eee1'; ctx.font = '8px ui-monospace,monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(['N', 'E', 'S', 'W'][bearing / 90], Math.cos(angle) * (ring - 12), Math.sin(angle) * (ring - 12));
    }
  }
  ctx.restore();
  const pointerY = cy - ring;
  ctx.fillStyle = '#59e0bc'; ctx.beginPath(); ctx.moveTo(cx, pointerY - 4); ctx.lineTo(cx - 4, pointerY + 3); ctx.lineTo(cx, pointerY + 1); ctx.lineTo(cx + 4, pointerY + 3); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#e8f7ee'; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(cx - 6, pointerY - 6); ctx.lineTo(cx + 6, pointerY - 6); ctx.moveTo(cx, pointerY - 9); ctx.lineTo(cx, pointerY - 3); ctx.stroke();
}

function updateStatus() {
  drawNavigation();
  drawTofRangeBar(liveTof || world?.perception?.modalities?.tof || {});
  const radar = liveRadar?.sample || world?.perception?.modalities?.mmwave_radar || {};
  const radarCount = radar.targets?.length || 0;
  setText('radar-count', `${radarCount} targets`);
  setText('lidar-count', `${world?.perception?.sensor_projections?.lidar?.points?.length || 0} pts`);
  drawMap($('radar-map'), 'radar');
  if (!world?.perception?.available) {
    setText('status', world?.perception?.note || 'Waiting for Body perception…');
    drawUltrasonicRanges({});
    return;
  }
  const perception = world.perception;
  const lidarCount = perception.sensor_projections?.lidar?.points?.length || 0;
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
  setText('lidar-count', `${lidarCount} pts`);
  drawRobot(); drawMap($('lidar-map'), 'lidar');
  drawUltrasonicRanges(perception.modalities || {});
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
    const frameKey = String(id);
    const displayFrame = {
      id: frameKey,
      src: `data:${frame.mime_type || 'image/jpeg'};base64,${frame.image_base64}`,
      width: Number(frame.width) || 640,
      height: Number(frame.height) || 480,
      source: frame.source || result.source || 'Body camera · live',
      capturedAt: Number(frame.captured_at) || 0,
    };

    const yolo = result.yolo || {};
    const detectionId = yolo.state === 'ready' && yolo.frame_id != null ? String(yolo.frame_id) : '';
    const fresh = Number(yolo.captured_at) > 0 && Math.abs(Date.now() / 1000 - Number(yolo.captured_at)) < 2.5;
    const detections = fresh && Array.isArray(yolo.detections) ? yolo.detections : [];
    const displayKey = `${frameKey}:${detectionId}:${detections.length}`;
    if (displayKey === cameraDisplayKey) return;
    cameraDisplayKey = displayKey;
    cameraFrameId = displayFrame.id;
    $('camera').src = displayFrame.src;
    $('camera-empty').hidden = true;
    $('camera-state').textContent = detections.length ? `LIVE · ${detections.length} YOLO` : 'LIVE';
    $('camera-source').textContent = displayFrame.source;
    $('camera-size').textContent = `${displayFrame.width} × ${displayFrame.height}`;
    drawCameraYoloOverlay(displayFrame, detections);
  } catch {
    $('camera-empty').hidden = false; $('camera-state').textContent = 'UNAVAILABLE';
  } finally { cameraBusy = false; }
}

function drawCameraYoloOverlay(frame, detections) {
  const canvas = $('camera-yolo-overlay');
  const context = canvas.getContext('2d');
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const bounds = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(bounds.width * ratio));
  canvas.height = Math.max(1, Math.round(bounds.height * ratio));
  context.clearRect(0, 0, canvas.width, canvas.height);
  if (!detections.length) return;
  const frameAspect = frame.width / Math.max(1, frame.height);
  const canvasAspect = canvas.width / Math.max(1, canvas.height);
  const contentWidth = frameAspect > canvasAspect ? canvas.width : canvas.height * frameAspect;
  const contentHeight = frameAspect > canvasAspect ? canvas.width / frameAspect : canvas.height;
  const offsetX = (canvas.width - contentWidth) / 2;
  const offsetY = (canvas.height - contentHeight) / 2;
  context.lineWidth = Math.max(2 * ratio, canvas.width / 320);
  context.font = `600 ${Math.max(14 * ratio, canvas.width / 32)}px system-ui, sans-serif`;
  for (const detection of detections) {
    const box = detection?.bbox;
    if (!Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite)) continue;
    const [x1, y1, x2, y2] = box.map(value => Math.max(0, Math.min(1, value)));
    const x = offsetX + x1 * contentWidth, y = offsetY + y1 * contentHeight;
    const width = (x2 - x1) * contentWidth, height = (y2 - y1) * contentHeight;
    if (width < 2 || height < 2) continue;
    context.strokeStyle = '#42f5bd';
    context.strokeRect(x, y, width, height);
    const confidence = Number(detection.confidence);
    const label = `${String(detection.label || 'object')} ${Number.isFinite(confidence) ? Math.round(confidence * 100) : 0}%`;
    const labelHeight = Math.max(20 * ratio, canvas.width / 28);
    const labelY = Math.max(0, y - labelHeight);
    context.fillStyle = '#06231c';
    context.fillRect(x, labelY, context.measureText(label).width + 10 * ratio, labelHeight);
    context.fillStyle = '#a7ffdf';
    context.fillText(label, x + 5 * ratio, labelY + labelHeight * 0.72);
  }
}

async function pollImu() {
  if (imuBusy) return;
  imuBusy = true;
  try {
    const response = await fetch('/plugins/imu/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`IMU status HTTP ${response.status}`);
    const status = { ...(await response.json()), endpoint_available: true };
    const sample = status.sample;
    if (status.available && sample?.attitude_valid !== false
        && Number.isFinite(Number(sample?.roll_deg)) && Number.isFinite(Number(sample?.pitch_deg))) {
      lastValidImu = sample;
      lastValidImuAt = Date.now();
    }
    const heldFor = (Date.now() - lastValidImuAt) / 1000;
    liveImu = status.available && sample?.attitude_valid !== false
      ? status
      : lastValidImu && heldFor <= 2.5
        ? { ...status, available: true, sample: lastValidImu, held_for_s: heldFor }
        : status;
    drawNavigation();
  } catch (error) {
    liveImu = { available: false, endpoint_available: false, error: error.message };
    drawNavigation();
  } finally { imuBusy = false; }
}

let gpsBusy = false;
async function pollGps() {
  if (gpsBusy) return;
  gpsBusy = true;
  try {
    const response = await fetch('/plugins/gps/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`GPS status HTTP ${response.status}`);
    liveGps = await response.json();
  } catch (error) {
    liveGps = { available: false, error: error.message };
  } finally {
    drawNavigation();
    gpsBusy = false;
  }
}

async function pollTof() {
  if (tofBusy) return;
  tofBusy = true;
  try {
    const response = await fetch('/plugins/tof/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`ToF status HTTP ${response.status}`);
    const status = await response.json();
    liveTof = status.available && status.sample?.available ? status.sample : null;
  } catch {
    liveTof = null;
  } finally {
    drawTofRangeBar(liveTof || world?.perception?.modalities?.tof || {});
    tofBusy = false;
  }
}

let ultrasonicBusy = false;
async function pollUltrasonic() {
  if (ultrasonicBusy) return;
  ultrasonicBusy = true;
  try {
    const response = await fetch('/plugins/ultrasonic/status', { cache: 'no-store', credentials: 'same-origin' });
    if (!response.ok) throw new Error(`Ultrasonic status HTTP ${response.status}`);
    liveUltrasonic = await response.json();
  } catch (error) {
    liveUltrasonic = { available: false, sample: { sensors: [] }, error: error.message };
  } finally {
    ultrasonicStatusReceived = true;
    drawUltrasonicRanges();
    ultrasonicBusy = false;
  }
}

let radarBusy = false;
async function pollRadar() {
  if (radarBusy) return;
  radarBusy = true;
  try {
    const response = await fetch('/plugins/mmwave_radar/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`mmWave status HTTP ${response.status}`);
    const status = await response.json();
    liveRadar = status.available && status.sample ? status : { ...status, sample: null };
  } catch (error) {
    liveRadar = { available: false, sample: null, error: error.message };
  } finally {
    const radar = liveRadar?.sample || {};
    const targets = radar.targets || [];
    setText('radar-count', `${targets.length} targets`);
    drawMap($('radar-map'), 'radar');
    if (world?.perception?.available) {
      const perception = world.perception;
      const lidarCount = perception.sensor_projections?.lidar?.points?.length || 0;
      setText('status', `${perception.source || 'Body'} · observation ${Number(perception.age_seconds || 0).toFixed(1)} s old · ${lidarCount} LiDAR returns · ${targets.length} radar targets`);
    } else if (liveRadar?.error) {
      setText('status', `Waiting for Body perception · mmWave ${liveRadar.error}`);
    } else if (liveRadar?.available) {
      setText('status', `Waiting for Body perception · mmWave live · ${targets.length} targets`);
    }
    radarBusy = false;
  }
}

initRobotVisual();
window.addEventListener('resize', updateStatus);
void poll(); void pollCamera(); void pollImu(); void pollTof(); void pollRadar(); void pollGps(); void pollUltrasonic();
setInterval(poll, 800); setInterval(pollCamera, 150); setInterval(pollImu, 1000); setInterval(pollTof, 1000); setInterval(pollRadar, 500); setInterval(pollGps, 1500); setInterval(pollUltrasonic, 500);
