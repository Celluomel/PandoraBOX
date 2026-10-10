(() => {
  const nav = document.querySelector('.sidebar .nav');
  const main = document.querySelector('main.shell');
  if (!nav || !main || document.getElementById('view-navigation')) return;
  const item = document.createElement('button');
  item.id = 'nav-navigation';
  item.type = 'button';
  item.textContent = '06  ROS 2 & Navigation';
  nav.insertBefore(item, document.getElementById('nav-runtime'));
  const runtimeItem = document.getElementById('nav-runtime');
  if (runtimeItem) runtimeItem.textContent = '07  Runtime';

  const view = document.createElement('section');
  view.id = 'view-navigation';
  view.className = 'view navops';
  view.hidden = true;
  view.innerHTML = `
    <div class="navops-head"><div><span class="navops-kicker">BODY / ROS 2 / NAV2</span><h2>Navigation console</h2>
      <p id="navops-summary">Connecting to the Body ROS 2 bridge…</p></div>
      <div class="navops-actions"><button id="navops-start" type="button">Start Nav2</button><button id="navops-stop" type="button">Stop Nav2</button><button id="navops-route" type="button">Run test route</button></div></div>
    <div class="navops-switch" role="tablist" aria-label="Navigation console views">
      <button id="navops-tab-map" type="button" role="tab" aria-selected="true" aria-controls="navops-page-map">Navigation</button>
      <button id="navops-tab-ros" type="button" role="tab" aria-selected="false" aria-controls="navops-page-ros">ROS 2 channels</button></div>
    <div class="navops-metrics" aria-live="polite">
      <div class="navops-metric"><span>ROS 2 bridge</span><strong id="navops-bridge">Connecting</strong><small id="navops-domain">Domain —</small></div>
      <div class="navops-metric"><span>Nav2 action</span><strong id="navops-action">—</strong><small id="navops-stack">Stack —</small></div>
      <div class="navops-metric"><span>Odometry</span><strong id="navops-pose">—</strong><small id="navops-heading">Heading —</small></div>
      <div class="navops-metric"><span>Command isolation</span><strong id="navops-isolation">—</strong><small>FNK actuation disconnected</small></div></div>
    <div id="navops-page-map" class="navops-hidden" role="tabpanel" aria-labelledby="navops-tab-map">
      <div class="navops-layout">
        <section class="navops-tool"><div class="navops-tool-head"><b>Local metric map</b><small id="navops-map-source">NO MAP SOURCE</small></div>
          <div class="navops-map-wrap"><canvas id="navops-map" aria-label="Metric navigation map, simulated obstacles, laser returns and robot pose"></canvas>
            <div id="navops-map-empty" class="navops-map-empty"><strong>No navigation map</strong><small>Enable ROS 2 and synthetic inputs in ROS 2 channels to view the safe Nav2 test world.</small></div></div>
          <div class="navops-map-foot"><span>MAP FRAME · METRES · X FORWARD</span><span id="navops-map-count">0 LASER RETURNS</span></div></section>
        <div class="navops-side"><section class="navops-tool"><div class="navops-tool-head"><b>Body camera</b><small id="navops-camera-state">NO FRAME</small></div>
          <div class="navops-camera-stage"><img id="navops-camera-image" alt="Current Body camera frame"><span id="navops-camera-empty">Camera stream unavailable</span></div>
          <div class="navops-readouts"><div><small>Frame</small><b id="navops-camera-size">—</b></div><div><small>Source</small><b id="navops-camera-source">—</b></div></div></section>
          <section class="navops-tool"><div class="navops-tool-head"><b>Sensor inputs</b><small>ROS 2 SUBSCRIPTIONS</small></div><div id="navops-sensors" class="navops-sensor-list"></div></section></div></div>
      <div class="navops-bottom"><section class="navops-tool"><div class="navops-tool-head"><b>Navigation readiness</b><small>LIVE PREFLIGHT</small></div><div id="navops-preflight" class="navops-lines"></div></section>
        <section class="navops-tool"><div class="navops-tool-head"><b>Test route</b><small>GOAL 5.0, 0.0 · MAP</small></div><div id="navops-result" class="navops-lines"><div class="navops-line"><span>Last result</span><b>Not run in this session</b></div></div></section></div></div>
    <div id="navops-page-ros" class="navops-hidden" role="tabpanel" aria-labelledby="navops-tab-ros" hidden>
      <div class="navops-bottom" style="margin-top:0"><section class="navops-tool"><div class="navops-tool-head"><b>Bridge configuration</b><small>PERSISTED ON BODY</small></div>
        <div class="navops-settings"><label class="check wide"><input id="navops-enable" type="checkbox"> Enable ROS 2 observation bridge</label>
          <label class="check wide"><input id="navops-synthetic" type="checkbox"> Publish synthetic Nav2 map, scan, odometry and TF</label>
          <label>Observation output<input id="navops-publish" type="text"></label><label>Observation input<input id="navops-input" type="text"></label>
          <label>IMU topic<input id="navops-topic-imu" type="text"></label><label>GPS topic<input id="navops-topic-gps" type="text"></label>
          <label>LiDAR topic<input id="navops-topic-lidar" type="text"></label><label>Odometry topic<input id="navops-topic-odometry" type="text"></label>
          <label>Range topic<input id="navops-topic-range" type="text"></label><div><button id="navops-save" type="button">Save ROS 2 settings</button></div>
          <small class="wide navops-alert">Synthetic topics are for software-only Nav2 tests. They cannot move the FNK0031.</small></div></section>
        <section class="navops-tool"><div class="navops-tool-head"><b>ROS graph and safety</b><small id="navops-graph-count">0 TOPICS</small></div><div id="navops-graph" class="navops-lines"></div></section></div></div>
    <p id="navops-message" class="navops-message" role="status" aria-live="polite"></p>`;
  main.appendChild(view);
  const el = id => document.getElementById('navops-' + id);
  let selectedTab = 'map';
  let settings = null;
  let visual = null;
  let busy = false;
  let settingsDirty = false;
  let lastCameraAt = 0;
  let trail = [];
  let lastRefresh = 0;
  const text = (id, value) => { const node = el(id); if (node) node.textContent = String(value ?? '—'); };
  const message = (value, error = false) => { text('message', value); el('message').classList.toggle('error', error); };
  const request = async (path, payload) => {
    const response = await fetch(path, payload === undefined ? {cache:'no-store'} : {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload), cache:'no-store'
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw Error(data.error || `${path}: HTTP ${response.status}`);
    return data;
  };
  function setTab(tab) {
    selectedTab = tab;
    el('page-map').hidden = tab !== 'map';
    el('page-ros').hidden = tab !== 'ros';
    for (const key of ['map', 'ros']) el('tab-' + key).setAttribute('aria-selected', String(key === tab));
    if (tab === 'map') drawMap();
  }
  function setRows(id, rows) {
    const parent = el(id);
    parent.replaceChildren();
    for (const [label, value] of rows) {
      const row = document.createElement('div'); row.className = 'navops-line';
      const a = document.createElement('span'); a.textContent = label;
      const b = document.createElement('b'); b.textContent = value;
      row.append(a, b); parent.append(row);
    }
  }
  function drawMap() {
    const canvas = el('map');
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
    const c = canvas.getContext('2d'); c.scale(dpr, dpr);
    const w = rect.width, h = rect.height;
    c.fillStyle = '#0a171c'; c.fillRect(0, 0, w, h);
    const scale = Math.min((w - 55) / 8, (h - 45) / 5.5);
    const center = visual?.pose || {x:2.5,y:0};
    const cx = Math.max(2.5, Math.min(4, center.x));
    const toScreen = (x,y) => [w/2 + (x-cx)*scale, h/2 - y*scale];
    c.lineWidth = 1;
    for (let x = -8; x <= 8; x += .5) {
      const px = toScreen(x,0)[0]; c.strokeStyle = x === 0 ? '#3b665f' : '#1b3237';
      c.beginPath(); c.moveTo(px,0); c.lineTo(px,h); c.stroke();
    }
    for (let y = -8; y <= 8; y += .5) {
      const py = toScreen(0,y)[1]; c.strokeStyle = y === 0 ? '#3b665f' : '#1b3237';
      c.beginPath(); c.moveTo(0,py); c.lineTo(w,py); c.stroke();
    }
    c.fillStyle = '#668b89'; c.font = '10px ui-monospace,monospace';
    for (let x = 0; x <= 6; x++) { const px = toScreen(x,0)[0]; if (px>8 && px<w-20) c.fillText(`${x} m`,px+4,h-10); }
    if (!visual?.available) return;
    for (const [x0,y0,x1,y1] of visual.map?.obstacles || []) {
      const [px,py] = toScreen(x0,y1); c.fillStyle = '#725e5e'; c.fillRect(px,py,(x1-x0)*scale,(y1-y0)*scale);
      c.strokeStyle = '#d9a093'; c.strokeRect(px,py,(x1-x0)*scale,(y1-y0)*scale);
    }
    const [gx,gy] = toScreen(5,0); c.strokeStyle = '#e9c37b'; c.lineWidth = 2;
    c.beginPath(); c.arc(gx,gy,11,0,Math.PI*2); c.stroke();
    c.beginPath(); c.moveTo(gx-17,gy); c.lineTo(gx+17,gy); c.moveTo(gx,gy-17); c.lineTo(gx,gy+17); c.stroke();
    const pose = visual.pose || {x:0,y:0,yaw_rad:0};
    c.strokeStyle = '#57bda8'; c.lineWidth = 2; c.beginPath();
    trail.forEach((point,i) => { const [px,py] = toScreen(point.x,point.y); if (i) c.lineTo(px,py); else c.moveTo(px,py); }); c.stroke();
    const laserX = pose.x + .12*Math.cos(pose.yaw_rad), laserY = pose.y + .12*Math.sin(pose.yaw_rad);
    c.fillStyle = '#65d9e0';
    for (const [angle,distance] of visual.scan?.returns || []) {
      const [px,py] = toScreen(laserX+distance*Math.cos(pose.yaw_rad+angle),laserY+distance*Math.sin(pose.yaw_rad+angle));
      c.fillRect(px-1,py-1,2,2);
    }
    const [rx,ry] = toScreen(pose.x,pose.y); c.save(); c.translate(rx,ry); c.rotate(-pose.yaw_rad);
    c.fillStyle = '#79e9b5'; c.beginPath(); c.moveTo(17,0); c.lineTo(-11,-9); c.lineTo(-7,0); c.lineTo(-11,9); c.closePath(); c.fill(); c.restore();
    c.fillStyle = '#c8ede0'; c.fillText('BODY',rx-12,ry+26); c.fillText('GOAL',gx-12,gy-23);
  }
  function renderStatus(data) {
    settings = data;
    const status = data.status || {}, sim = status.nav2_simulation || {}, preflight = status.nav2_preflight || {};
    text('bridge', data.enabled ? (status.available ? 'Online' : 'Unavailable') : 'Disabled');
    text('domain', `Domain ${status.domain_id ?? '0'} · ${status.ros_distro || 'ROS not sourced'}`);
    text('action', status.nav2_server_available ? 'Ready' : status.nav2_packages_available ? 'No server' : 'Not installed');
    text('stack', `Stack ${data.nav2_stack?.state || 'stopped'}`);
    const pose = sim.pose;
    text('pose', pose ? `${Number(pose.x).toFixed(2)}, ${Number(pose.y).toFixed(2)} m` : 'No odometry');
    text('heading', pose ? `Heading ${(Number(pose.yaw_rad)*180/Math.PI).toFixed(0)}° · synthetic` : 'Heading —');
    text('isolation', sim.enabled ? (sim.cmd_vel_hardware_isolated ? 'Verified' : 'Blocked') : 'No command');
    text('summary', sim.enabled ? 'Synthetic Nav2 world running · physical FNK motion is not connected' :
      data.enabled ? 'ROS 2 bridge connected · no navigation map active' : 'ROS 2 bridge is disabled');
    const running = data.nav2_stack?.state === 'running';
    el('start').disabled = busy || running || !data.enabled || !data.nav2_simulation_enabled || !status.available;
    el('stop').disabled = busy || !running;
    el('route').disabled = busy || !running || !sim.cmd_vel_hardware_isolated;
    el('route').title = !sim.cmd_vel_hardware_isolated ? 'Blocked until /cmd_vel has only the synthetic base as subscriber' :
      'Run the isolated synthetic obstacle course; no FNK motor command';
    const sensorRows = [['imu','IMU'],['gps','GPS'],['lidar','LiDAR'],['odometry','Odometry'],['range','Range']];
    const sensorParent = el('sensors'); sensorParent.replaceChildren();
    for (const [key,label] of sensorRows) {
      const sensor = status.sensor_subscriptions?.[key] || {};
      const row = document.createElement('div'); row.className = 'navops-sensor';
      const name = document.createElement('b'); name.textContent = label;
      const state = document.createElement('span'); state.textContent = sensor.count ? `${sensor.count} messages` : (sensor.state || 'No feed');
      const topic = document.createElement('small'); topic.textContent = `${sensor.topic || data.sensor_topics?.[key] || 'No topic'}${sensor.error ? ' · ' + sensor.error : ''}`;
      row.append(name,state,topic); sensorParent.append(row);
    }
    setRows('preflight', [
      ['Nav2 packages',status.nav2_packages_available ? 'Installed' : 'Unavailable'],
      ['Action server',status.nav2_server_available ? 'Connected' : 'No server'],
      ['Synthetic topics',sim.enabled ? 'Publishing' : 'Stopped'],
      ['/cmd_vel subscribers',sim.cmd_vel_subscribers?.length === undefined ? 'Unknown' : String(sim.cmd_vel_subscribers.length)],
      ['Safety',sim.cmd_vel_hardware_isolated ? 'Isolated from FNK' : 'Route blocked'],
      ['Preflight',preflight.ready ? 'Ready' : (preflight.blockers || []).slice(0,2).join('; ') || 'Not ready'],
    ]);
    const topics = status.sensor_topics || data.sensor_topics || {};
    text('graph-count',`${Object.keys(topics).length + 5} CHANNELS`);
    setRows('graph', [
      ['Observation output', data.publish_topic || '—'], ['Observation input', data.input_topic || '—'],
      ['Map',sim.enabled ? '/map · synthetic' : 'No publisher'], ['Laser scan',sim.enabled ? '/scan · synthetic' : topics.lidar || '—'],
      ['Odometry',sim.enabled ? '/odom · synthetic' : topics.odometry || '—'],
      ['Transform',sim.enabled ? '/tf · synthetic' : 'No publisher'], ['Velocity command','/cmd_vel · isolation gated'],
    ]);
    if (!settingsDirty) {
      el('enable').checked = !!data.enabled; el('synthetic').checked = !!data.nav2_simulation_enabled;
      el('publish').value = data.publish_topic || ''; el('input').value = data.input_topic || '';
      for (const [key] of sensorRows) if (!el('topic-'+key).matches(':focus')) el('topic-'+key).value = data.sensor_topics?.[key] || '';
    }
  }
  function renderVisual(data) {
    visual = data;
    el('map-empty').hidden = !!data.available;
    if (!data.available) {
      el('map-empty').querySelector('small').textContent = data.reason || 'No map source';
      trail = [];
    } else if (data.pose) {
      const last = trail[trail.length-1];
      if (!last || Math.hypot(last.x-data.pose.x,last.y-data.pose.y) > .03) {
        trail.push({x:data.pose.x,y:data.pose.y}); if (trail.length > 400) trail.shift();
      }
    }
    text('map-source',data.available ? 'SYNTHETIC MAP + SCAN' : 'NO MAP SOURCE');
    text('map-count',`${data.scan?.returns?.length || 0} LASER RETURNS`);
    drawMap();
  }
  async function refreshCamera() {
    if (Date.now() - lastCameraAt < 3500) return;
    lastCameraAt = Date.now();
    try {
      const data = await request('/body/camera/frame');
      const frame = data.camera || {}, img = el('camera-image');
      if (data.available && frame.image_base64) {
        img.src = `data:${frame.mime_type || 'image/jpeg'};base64,${frame.image_base64}`;
        text('camera-state','LIVE BODY FRAME'); text('camera-size',`${frame.width || '—'} × ${frame.height || '—'}`);
        text('camera-source',frame.source || 'Body');
      } else { img.removeAttribute('src'); text('camera-state','NO FRAME'); text('camera-size','—'); text('camera-source',data.status || 'Unavailable'); }
    } catch (_) { el('camera-image').removeAttribute('src'); text('camera-state','UNAVAILABLE'); }
  }
  async function refresh() {
    if (currentView !== 'navigation' || document.hidden || busy) return;
    try {
      const [data,map] = await Promise.all([request('/ros2/settings'),request('/ros2/visualization')]);
      renderStatus(data); renderVisual(map); lastRefresh = Date.now();
      if (selectedTab === 'map') void refreshCamera();
    } catch (error) { message('Body status unavailable: ' + error.message,true); }
  }
  async function action(path, label) {
    if (busy) return;
    busy = true; for (const id of ['start','stop','route','save']) el(id).disabled = true;
    message(label + '…');
    try {
      const result = await request(path,{});
      if (path.endsWith('route-test')) {
        setRows('result', [['Status',result.status || 'unknown'],['Elapsed',`${result.elapsed_s ?? '—'} s`],
          ['Final error',`${result.position_error_m ?? '—'} m`],['Hardware actuation','No']]);
        message(`Test route ${result.status} in ${result.elapsed_s} s · ${result.position_error_m} m final error`);
      } else message(label + ' complete.');
    } catch (error) { message(label + ' failed: ' + error.message,true); }
    finally { busy = false; await refresh(); }
  }
  async function save() {
    if (busy) return;
    const sensor_topics = {};
    for (const key of ['imu','gps','lidar','odometry','range']) sensor_topics[key] = el('topic-'+key).value.trim();
    const payload = {enabled:el('enable').checked,nav2_simulation_enabled:el('synthetic').checked,
      publish_topic:el('publish').value.trim(),input_topic:el('input').value.trim(),sensor_topics};
    busy = true; el('save').disabled = true;
    try { await request('/ros2/settings',payload); settingsDirty = false; message('ROS 2 settings saved on Body.'); }
    catch (error) { message('Settings not saved: ' + error.message,true); }
    finally { busy = false; el('save').disabled = false; await refresh(); }
  }
  el('tab-map').onclick = () => setTab('map'); el('tab-ros').onclick = () => setTab('ros');
  el('page-ros').addEventListener('input', event => { if (event.target.matches('input')) settingsDirty = true; });
  el('page-ros').addEventListener('change', event => { if (event.target.matches('input')) settingsDirty = true; });
  el('start').onclick = () => action('/ros2/nav2/simulation/start','Start Nav2');
  el('stop').onclick = () => action('/ros2/nav2/simulation/stop','Stop Nav2');
  el('route').onclick = () => action('/ros2/nav2/simulation/route-test','Test route');
  el('save').onclick = save;
  item.onclick = () => showView('navigation');
  const previousShowView = showView;
  showView = function(page) {
    if (page !== 'navigation') { view.hidden = true; item.classList.remove('active'); previousShowView(page); return; }
    currentView = 'navigation'; document.body.dataset.view = 'navigation';
    document.querySelectorAll('.view').forEach(section => { section.hidden = true; });
    view.hidden = false;
    document.querySelectorAll('.sidebar .nav button').forEach(button => button.classList.toggle('active',button === item));
    text('summary','Connecting to Body ROS 2 bridge…');
    document.getElementById('page-breadcrumb').textContent = 'ROS 2 / NAVIGATION';
    document.getElementById('page-title').textContent = 'ROS 2 & Navigation';
    document.getElementById('page-description').textContent = 'Live topics, navigation state and an isolated Nav2 test world.';
    document.title = 'ROS 2 & Navigation · Body';
    history.replaceState(null,'','/navigation');
    if (Date.now() - lastRefresh > 700) void refresh();
    drawMap(); window.scrollTo({top:0,behavior:'instant'});
  };
  window.addEventListener('resize', drawMap);
  setInterval(refresh,2000);
  if (window.__bodyInitialPath === '/navigation') showView('navigation');
})();
