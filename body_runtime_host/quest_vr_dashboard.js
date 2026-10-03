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
      new THREE.PlaneGeometry(1.08, 0.5),
      new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    panel.position.set(0.56, 0.72, -1.9);
    panel.renderOrder = 1000;
    this.root.add(panel);

    const cameraCanvas = document.createElement('canvas');
    cameraCanvas.width = 640;
    cameraCanvas.height = 360;
    this.cameraContext = cameraCanvas.getContext('2d');
    this.cameraTexture = new THREE.CanvasTexture(cameraCanvas);
    this.cameraTexture.colorSpace = THREE.SRGBColorSpace;
    const cameraPanel = new THREE.Mesh(
      new THREE.PlaneGeometry(1.08, 0.608),
      new THREE.MeshBasicMaterial({ map: this.cameraTexture, transparent: true, depthTest: false, side: THREE.DoubleSide }),
    );
    cameraPanel.position.set(-0.56, 0.72, -1.9);
    cameraPanel.renderOrder = 1000;
    this.root.add(cameraPanel);
    this.drawCameraMessage('CAMERA · WAITING');
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

  syncPose(xrCamera) {
    xrCamera.getWorldPosition(this.root.position);
    xrCamera.getWorldQuaternion(this.root.quaternion);
  }
}
