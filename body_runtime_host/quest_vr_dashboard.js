export class QuestVRDashboard {
  constructor(THREE) {
    this.scene = new THREE.Scene();
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.visible = false;

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    this.context = canvas.getContext('2d');
    this.texture = new THREE.CanvasTexture(canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    const panel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.55, 0.78),
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    panel.position.set(0, -0.25, -1.65);
    panel.renderOrder = 1000;
    this.root.add(panel);
    this.update(null);
  }

  update(frame) {
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
    ctx.font = '600 46px system-ui';
    ctx.fillText('PANDORABOX · BODY STATUS', 44, 76);
    ctx.fillStyle = '#9fc5ac';
    ctx.font = '32px system-ui';

    const perception = frame?.perception || {};
    const position = perception.body?.position || [];
    const pose = position.length >= 2
      ? `Body  ${Number(position[0]).toFixed(2)}, ${Number(position[1]).toFixed(2)} m`
      : 'Body pose  waiting for perception';
    const objects = perception.objects?.length || 0;
    const lidar = perception.sensor_projections?.lidar?.points?.length || 0;
    const radar = perception.modalities?.mmwave_radar?.targets?.length || 0;
    const rows = [pose, `Scene objects  ${objects}`, `LiDAR points  ${lidar}`, `mmWave targets  ${radar}`];
    rows.forEach((row, index) => ctx.fillText(row, 52, 164 + index * 70));
    this.texture.needsUpdate = true;
  }

  setVisible(visible) {
    this.visible = Boolean(visible);
  }

  syncPose(xrCamera) {
    xrCamera.getWorldPosition(this.root.position);
    xrCamera.getWorldQuaternion(this.root.quaternion);
  }
}
