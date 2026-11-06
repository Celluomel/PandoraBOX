// Estimated FNK0031 geometry. Repeated leg parts use instancing to keep Quest
// draw calls low; this model reports commanded/estimated state, never encoder feedback.
export function createFnk0031Visual(THREE) {
  const group = new THREE.Group();
  const chassis = new THREE.Group();
  group.add(chassis);
  const graphite = new THREE.MeshStandardMaterial({ color: '#48575c', metalness: .28, roughness: .38 });
  const dark = new THREE.MeshStandardMaterial({ color: '#263338', metalness: .2, roughness: .46 });
  const edge = new THREE.MeshStandardMaterial({ color: '#8da3a9', metalness: .36, roughness: .3 });
  const bracket = new THREE.MeshStandardMaterial({ color: '#c8d4d4', metalness: .26, roughness: .33 });
  const lens = new THREE.MeshStandardMaterial({ color: '#172c35', metalness: .25, roughness: .2, emissive: '#0b5b65', emissiveIntensity: .5 });
  const trimMaterial = new THREE.MeshStandardMaterial({ color: '#4fddbf', emissive: '#168c76', emissiveIntensity: .55 });
  const indicatorMaterial = new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#ffffff', emissiveIntensity: .28, roughness: .48 });
  const instanceMaterial = new THREE.MeshStandardMaterial({ color: '#ffffff', metalness: .22, roughness: .42 });
  const idleJoint = new THREE.Color('#56b8b7');
  const activeJoint = new THREE.Color('#f5d07e');
  const darkFoot = new THREE.Color('#263338');
  const highlightedFoot = new THREE.Color('#f5d07e');
  const up = new THREE.Vector3(0, 1, 0);
  const direction = new THREE.Vector3();
  const instanceTransform = new THREE.Object3D();
  const colorScratch = new THREE.Color();

  function mesh(geometry, material, parent = chassis) {
    const object = new THREE.Mesh(geometry, material);
    parent.add(object);
    return object;
  }

  function instances(geometry, material, count, parent = chassis) {
    const object = new THREE.InstancedMesh(geometry, material, count);
    object.frustumCulled = false; // leg transforms change; avoid stale instance bounds.
    parent.add(object);
    return object;
  }

  function writeInstance(meshObject, index, position, quaternion = null, scale = null) {
    instanceTransform.position.copy(position);
    if (quaternion) instanceTransform.quaternion.copy(quaternion);
    else instanceTransform.quaternion.identity();
    if (scale) instanceTransform.scale.copy(scale);
    else instanceTransform.scale.set(1, 1, 1);
    instanceTransform.updateMatrix();
    meshObject.setMatrixAt(index, instanceTransform.matrix);
  }

  function placeRod(meshObject, instanceIndex, start, end) {
    direction.subVectors(end, start);
    const length = direction.length();
    instanceTransform.position.copy(start).add(end).multiplyScalar(.5);
    if (length > 1e-6) direction.multiplyScalar(1 / length);
    else direction.set(0, 1, 0);
    instanceTransform.quaternion.setFromUnitVectors(up, direction);
    instanceTransform.scale.set(1, length, 1);
    instanceTransform.updateMatrix();
    meshObject.setMatrixAt(instanceIndex, instanceTransform.matrix);
  }

  const lower = mesh(new THREE.CylinderGeometry(.48, .5, .105, 12), edge);
  lower.position.y = .56;
  lower.scale.z = 1.34;
  const shell = mesh(new THREE.CylinderGeometry(.52, .49, .15, 12), graphite);
  shell.position.y = .65;
  shell.scale.z = 1.34;
  const lid = mesh(new THREE.CylinderGeometry(.42, .42, .02, 12), dark);
  lid.position.y = .739;
  lid.scale.z = 1.38;
  const electronics = mesh(new THREE.BoxGeometry(.52, .085, .42), dark);
  electronics.position.set(0, .785, -.05);
  const trim = mesh(new THREE.BoxGeometry(.44, .018, .025), trimMaterial);
  trim.position.set(0, .837, .05);
  const bolts = instances(new THREE.CylinderGeometry(.025, .025, .012, 8), bracket, 4);
  let boltIndex = 0;
  for (const x of [-.32, .32]) {
    for (const z of [-.48, .48]) {
      writeInstance(bolts, boltIndex++, new THREE.Vector3(x, .752, z));
    }
  }
  bolts.instanceMatrix.needsUpdate = true;
  const front = mesh(new THREE.BoxGeometry(.3, .18, .17), graphite);
  front.position.set(0, .65, .72);
  const frontLens = mesh(new THREE.CylinderGeometry(.072, .072, .038, 18), lens);
  frontLens.rotation.x = Math.PI / 2;
  frontLens.position.set(0, .66, .822);
  const antenna = mesh(new THREE.CylinderGeometry(.009, .014, .3, 8), edge);
  antenna.position.set(-.24, .93, -.32);
  const antennaCap = mesh(new THREE.SphereGeometry(.025, 10, 8), lens);
  antennaCap.position.set(-.24, 1.085, -.32);

  const rodMeshes = [
    instances(new THREE.CylinderGeometry(.075 * .78, .075, 1, 9), edge, 6),
    instances(new THREE.CylinderGeometry(.067 * .78, .067, 1, 9), bracket, 6),
    instances(new THREE.CylinderGeometry(.052 * .78, .052, 1, 9), graphite, 6),
  ];
  const hips = instances(new THREE.BoxGeometry(.27, .19, .23), dark, 6);
  const jointHousings = instances(new THREE.BoxGeometry(.18, .14, .15), graphite, 18);
  const jointIndicators = instances(new THREE.SphereGeometry(.026, 10, 8), indicatorMaterial, 18);
  const feet = instances(new THREE.CylinderGeometry(.082, .095, .065, 12), instanceMaterial, 6);
  const footEdges = instances(new THREE.CylinderGeometry(.077, .085, .012, 12), instanceMaterial, 6);
  const legs = [];
  for (let sideIndex = 0; sideIndex < 2; sideIndex += 1) {
    const side = sideIndex === 0 ? -1 : 1;
    for (let row = 0; row < 3; row += 1) {
      const physicalLeg = sideIndex === 0 ? row * 2 : row * 2 + 1;
      const front = 1 - row;
      const hipPosition = new THREE.Vector3(side * .53, .56, front * .45);
      writeInstance(hips, physicalLeg, hipPosition);
      const points = Array.from({ length: 4 }, () => new THREE.Vector3());
      points[0].set(side * .55, .56, front * .45);
      const leg = { side, row, physicalLeg, hipPosition, points };
      legs[physicalLeg] = leg;
      // Initialize all instance matrices so no limb is culled or left at origin.
      points[1].set(side * .75, .53, front * .48);
      points[2].set(side * .99, .43, front * .62);
      points[3].set(side * 1.20, .06, front * .75);
      for (let segment = 0; segment < 3; segment += 1) {
        placeRod(rodMeshes[segment], physicalLeg, points[segment], points[segment + 1]);
        const jointIndex = physicalLeg * 3 + segment;
        writeInstance(jointHousings, jointIndex, points[segment + 1]);
        const indicatorPosition = points[segment + 1].clone();
        indicatorPosition.y += .075;
        writeInstance(jointIndicators, jointIndex, indicatorPosition);
        jointIndicators.setColorAt(jointIndex, idleJoint);
      }
      writeInstance(feet, physicalLeg, points[3]);
      const edgePosition = points[3].clone();
      edgePosition.y += .04;
      writeInstance(footEdges, physicalLeg, edgePosition);
      feet.setColorAt(physicalLeg, darkFoot);
      footEdges.setColorAt(physicalLeg, new THREE.Color('#8da3a9'));
    }
  }
  for (const object of [...rodMeshes, hips, jointHousings, jointIndicators, feet, footEdges]) {
    object.instanceMatrix.needsUpdate = true;
    if (object.instanceColor) object.instanceColor.needsUpdate = true;
  }

  const ring = mesh(new THREE.RingGeometry(1.11, 1.14, 56), new THREE.MeshBasicMaterial({ color: '#78cdb7', transparent: true, opacity: .28, side: THREE.DoubleSide }), group);
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = -.018;

  function setTelemetry(telemetry = {}) {
    const jointTargets = telemetry.joint_targets || [];
    const servoTargets = new Map((telemetry.servo_targets || []).map(item => [Number(item.index), Number(item.target)]));
    const spikes = telemetry.spikes || [];
    const contacts = telemetry.contact || [];
    for (const leg of legs) {
      const { side, row, physicalLeg, points } = leg;
      const values = jointTargets[physicalLeg] || [];
      const joint = index => {
        const value = Number(values[index] ?? servoTargets.get(physicalLeg * 3 + index + 1) ?? 0);
        return Number.isFinite(value) ? THREE.MathUtils.clamp(value, -1, 1) : 0;
      };
      const lift = THREE.MathUtils.clamp(Number(telemetry.foot_lift?.[physicalLeg]) || 0, 0, 1);
      const front = 1 - row;
      points[0].set(side * .55, .56, front * .45);
      points[1].set(side * (.75 + joint(0) * .035), .53, front * .48 + joint(0) * .035);
      points[2].set(side * (.99 + joint(1) * .05), .43 + lift * .16, front * .62);
      points[3].set(side * (1.20 + joint(2) * .045), .06 + lift * .25, front * .75);
      for (let index = 0; index < 3; index += 1) {
        placeRod(rodMeshes[index], physicalLeg, points[index], points[index + 1]);
        const jointIndex = physicalLeg * 3 + index;
        writeInstance(jointHousings, jointIndex, points[index + 1]);
        instanceTransform.position.copy(points[index + 1]);
        instanceTransform.position.y += .075;
        instanceTransform.quaternion.identity();
        instanceTransform.scale.set(1, 1, 1);
        instanceTransform.updateMatrix();
        jointIndicators.setMatrixAt(jointIndex, instanceTransform.matrix);
        colorScratch.copy(spikes[physicalLeg * 3 + index] ? activeJoint : idleJoint);
        jointIndicators.setColorAt(jointIndex, colorScratch);
      }
      writeInstance(feet, physicalLeg, points[3]);
      instanceTransform.position.copy(points[3]);
      instanceTransform.position.y += .04;
      instanceTransform.quaternion.identity();
      instanceTransform.scale.set(1, 1, 1);
      instanceTransform.updateMatrix();
      footEdges.setMatrixAt(physicalLeg, instanceTransform.matrix);
      feet.setColorAt(physicalLeg, darkFoot);
      footEdges.setColorAt(physicalLeg, Number(contacts[physicalLeg]) === 1 ? colorScratch.set('#c8d4d4') : colorScratch.set('#8da3a9'));
    }
    for (const object of [...rodMeshes, jointHousings, jointIndicators, feet, footEdges]) {
      object.instanceMatrix.needsUpdate = true;
      if (object.instanceColor) object.instanceColor.needsUpdate = true;
    }
  }

  function setEstimatedLegState(state, highlightedLeg = 0) {
    if (!Array.isArray(state?.legs)) return;
    const origins = [
      [-32, 50], [-46, 0], [-32, -50],
      [32, 50], [46, 0], [32, -50],
    ];
    for (const leg of legs) {
      const sample = state.legs[leg.physicalLeg];
      const foot = sample?.foot_position_mm;
      const angles = sample?.joint_angles_deg;
      const fx = Number(foot?.[0]), fy = Number(foot?.[1]), fz = Number(foot?.[2]);
      const alphaDeg = Number(angles?.[0]), betaDeg = Number(angles?.[1]);
      if (![fx, fy, fz, alphaDeg, betaDeg].every(Number.isFinite)) continue;
      const [originX, originZ] = origins[leg.physicalLeg];
      const alpha = alphaDeg * Math.PI / 180;
      const beta = betaDeg * Math.PI / 180;
      const d = 22.75, e = 55, c = 15.75;
      const points = leg.points;
      points[0].copy(leg.hipPosition);
      points[1].set((originX + d * Math.cos(alpha)) / 100, .56 + c / 100, (originZ + d * Math.sin(alpha)) / 100);
      const kneeRadius = d + e * Math.sin(beta);
      points[2].set((originX + kneeRadius * Math.cos(alpha)) / 100, .56 + (c + e * Math.cos(beta)) / 100, (originZ + kneeRadius * Math.sin(alpha)) / 100);
      points[3].set(fx / 100, .56 + fz / 100, fy / 100);
      for (let index = 0; index < 3; index += 1) {
        placeRod(rodMeshes[index], leg.physicalLeg, points[index], points[index + 1]);
        const jointIndex = leg.physicalLeg * 3 + index;
        writeInstance(jointHousings, jointIndex, points[index + 1]);
        instanceTransform.position.copy(points[index + 1]);
        instanceTransform.position.y += .075;
        instanceTransform.quaternion.identity();
        instanceTransform.scale.set(1, 1, 1);
        instanceTransform.updateMatrix();
        jointIndicators.setMatrixAt(jointIndex, instanceTransform.matrix);
      }
      writeInstance(feet, leg.physicalLeg, points[3]);
      instanceTransform.position.copy(points[3]);
      instanceTransform.position.y += .04;
      instanceTransform.quaternion.identity();
      instanceTransform.scale.set(1, 1, 1);
      instanceTransform.updateMatrix();
      footEdges.setMatrixAt(leg.physicalLeg, instanceTransform.matrix);
      const active = Number(highlightedLeg) === leg.physicalLeg + 1;
      feet.setColorAt(leg.physicalLeg, active ? highlightedFoot : darkFoot);
      footEdges.setColorAt(leg.physicalLeg, active ? colorScratch.copy(activeJoint) : colorScratch.copy(idleJoint));
    }
    for (const object of [...rodMeshes, jointHousings, jointIndicators, feet, footEdges]) {
      object.instanceMatrix.needsUpdate = true;
      if (object.instanceColor) object.instanceColor.needsUpdate = true;
    }
  }

  setTelemetry();
  return { group, setTelemetry, setEstimatedLegState };
}
