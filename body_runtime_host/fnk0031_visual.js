// Estimated FNK0031 geometry. One visual model is shared by the Quest HUD and its 2D preview.
export function createFnk0031Visual(THREE) {
  const group = new THREE.Group();
  const chassis = new THREE.Group();
  group.add(chassis);
  const graphite = new THREE.MeshStandardMaterial({ color: '#48575c', metalness: .28, roughness: .38 });
  const dark = new THREE.MeshStandardMaterial({ color: '#263338', metalness: .2, roughness: .46 });
  const edge = new THREE.MeshStandardMaterial({ color: '#8da3a9', metalness: .36, roughness: .3 });
  const bracket = new THREE.MeshStandardMaterial({ color: '#c8d4d4', metalness: .26, roughness: .33 });
  const lens = new THREE.MeshStandardMaterial({ color: '#172c35', metalness: .25, roughness: .2, emissive: '#0b5b65', emissiveIntensity: .5 });
  const idleJoint = '#56b8b7';
  const activeJoint = '#f5d07e';

  function mesh(geometry, material, parent = chassis) {
    const object = new THREE.Mesh(geometry, material);
    parent.add(object);
    return object;
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
  const trim = mesh(new THREE.BoxGeometry(.44, .018, .025), new THREE.MeshStandardMaterial({ color: '#4fddbf', emissive: '#168c76', emissiveIntensity: .55 }));
  trim.position.set(0, .837, .05);
  for (const x of [-.32, .32]) {
    for (const z of [-.48, .48]) {
      const bolt = mesh(new THREE.CylinderGeometry(.025, .025, .012, 8), bracket);
      bolt.position.set(x, .752, z);
    }
  }
  const front = mesh(new THREE.BoxGeometry(.3, .18, .17), graphite);
  front.position.set(0, .65, .72);
  const frontLens = mesh(new THREE.CylinderGeometry(.072, .072, .038, 18), lens);
  frontLens.rotation.x = Math.PI / 2;
  frontLens.position.set(0, .66, .822);
  const antenna = mesh(new THREE.CylinderGeometry(.009, .014, .3, 8), edge);
  antenna.position.set(-.24, .93, -.32);
  const antennaCap = mesh(new THREE.SphereGeometry(.025, 10, 8), lens);
  antennaCap.position.set(-.24, 1.085, -.32);

  const up = new THREE.Vector3(0, 1, 0);
  const direction = new THREE.Vector3();
  function rod(material, radius) {
    return mesh(new THREE.CylinderGeometry(radius * .78, radius, 1, 9), material);
  }
  function placeRod(object, start, end) {
    direction.subVectors(end, start);
    object.position.copy(start).add(end).multiplyScalar(.5);
    object.quaternion.setFromUnitVectors(up, direction.clone().normalize());
    object.scale.y = direction.length();
  }

  const legs = [];
  for (let sideIndex = 0; sideIndex < 2; sideIndex += 1) {
    const side = sideIndex === 0 ? -1 : 1;
    for (let row = 0; row < 3; row += 1) {
      const physicalLeg = sideIndex === 0 ? row * 2 : row * 2 + 1;
      const root = new THREE.Group();
      chassis.add(root);
      const hip = mesh(new THREE.BoxGeometry(.27, .19, .23), dark, root);
      hip.position.set(side * .53, .56, (1 - row) * .45);
      const links = [rod(edge, .075), rod(bracket, .067), rod(graphite, .052)];
      for (const link of links) { chassis.remove(link); root.add(link); }
      const joints = Array.from({ length: 3 }, () => {
        const housing = mesh(new THREE.BoxGeometry(.18, .14, .15), graphite, root);
        const indicator = mesh(new THREE.SphereGeometry(.026, 10, 8), new THREE.MeshStandardMaterial({ color: idleJoint, emissive: idleJoint, emissiveIntensity: .28 }), root);
        return { housing, indicator };
      });
      const foot = mesh(new THREE.CylinderGeometry(.082, .095, .065, 12), dark, root);
      const footEdge = mesh(new THREE.CylinderGeometry(.077, .085, .012, 12), edge, root);
      legs.push({ side, row, physicalLeg, hip, links, joints, foot, footEdge });
    }
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
      const { side, row, physicalLeg } = leg;
      const values = jointTargets[physicalLeg] || [];
      const joint = index => {
        const value = Number(values[index] ?? servoTargets.get(physicalLeg * 3 + index + 1) ?? 0);
        return Number.isFinite(value) ? THREE.MathUtils.clamp(value, -1, 1) : 0;
      };
      const lift = THREE.MathUtils.clamp(Number(telemetry.foot_lift?.[physicalLeg]) || 0, 0, 1);
      const front = 1 - row;
      const points = [
        new THREE.Vector3(side * .55, .56, front * .45),
        new THREE.Vector3(side * (.75 + joint(0) * .035), .53, front * .48 + joint(0) * .035),
        new THREE.Vector3(side * (.99 + joint(1) * .05), .43 + lift * .16, front * .62),
        new THREE.Vector3(side * (1.20 + joint(2) * .045), .06 + lift * .25, front * .75),
      ];
      for (let index = 0; index < 3; index += 1) {
        placeRod(leg.links[index], points[index], points[index + 1]);
        leg.joints[index].housing.position.copy(points[index + 1]);
        leg.joints[index].indicator.position.copy(points[index + 1]).add(new THREE.Vector3(0, .075, 0));
        const active = Boolean(spikes[physicalLeg * 3 + index]);
        const color = active ? activeJoint : idleJoint;
        leg.joints[index].indicator.material.color.set(color);
        leg.joints[index].indicator.material.emissive.set(color);
        leg.joints[index].indicator.material.emissiveIntensity = active ? 1.1 : .28;
      }
      leg.foot.position.copy(points[3]);
      leg.footEdge.position.copy(points[3]);
      leg.footEdge.position.y += .04;
      leg.footEdge.material = Number(contacts[physicalLeg]) === 1 ? bracket : edge;
    }
  }

  setTelemetry();
  return { group, setTelemetry };
}
