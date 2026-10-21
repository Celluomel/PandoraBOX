const TILE_SIZE = 256;
const MAX_MERCATOR_LAT = 85.05112878;

export class QuestGpsMap {
  constructor(onTileLoad = () => {}) {
    this.tiles = new Map();
    this.onTileLoad = onTileLoad;
  }

  loadTile(zoom, x, y) {
    const count = 2 ** zoom;
    const wrappedX = (x % count + count) % count;
    const key = `${zoom}/${wrappedX}/${y}`;
    if (this.tiles.has(key)) return this.tiles.get(key);
    const tile = { image: null, failed: false };
    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.onload = () => { tile.image = image; this.onTileLoad(); };
    image.onerror = () => { tile.failed = true; this.onTileLoad(); };
    image.src = `https://tile.openstreetmap.org/${zoom}/${wrappedX}/${y}.png`;
    tile.imageElement = image;
    this.tiles.set(key, tile);
    if (this.tiles.size > 96) this.tiles.delete(this.tiles.keys().next().value);
    return tile;
  }

  draw(ctx, { x, y, width, height, latitude, longitude, accuracyM = NaN }) {
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, Math.min(12, height * .08));
    ctx.clip();
    ctx.fillStyle = '#101b1b';
    ctx.fillRect(x, y, width, height);

    if (!Number.isFinite(latitude) || Math.abs(latitude) > 90
      || !Number.isFinite(longitude) || Math.abs(longitude) > 180) {
      ctx.fillStyle = '#a0b1ad';
      ctx.font = '600 12px ui-monospace,monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('NO VALID GNSS FIX · MAP HIDDEN', x + width / 2, y + height / 2);
      ctx.restore();
      return;
    }

    const zoom = 16;
    const worldSize = TILE_SIZE * 2 ** zoom;
    const clampedLatitude = Math.max(-MAX_MERCATOR_LAT, Math.min(MAX_MERCATOR_LAT, latitude));
    const sinLatitude = Math.sin(clampedLatitude * Math.PI / 180);
    const centerX = (longitude + 180) / 360 * worldSize;
    const centerY = (.5 - Math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * Math.PI)) * worldSize;
    const left = centerX - width / 2;
    const top = centerY - height / 2;
    const firstTileX = Math.floor(left / TILE_SIZE);
    const lastTileX = Math.floor((left + width) / TILE_SIZE);
    const firstTileY = Math.max(0, Math.floor(top / TILE_SIZE));
    const lastTileY = Math.min(2 ** zoom - 1, Math.floor((top + height) / TILE_SIZE));
    let loaded = false;

    for (let tileY = firstTileY; tileY <= lastTileY; tileY += 1) {
      for (let tileX = firstTileX; tileX <= lastTileX; tileX += 1) {
        const tile = this.loadTile(zoom, tileX, tileY);
        if (!tile.image) continue;
        loaded = true;
        ctx.drawImage(tile.image, x + tileX * TILE_SIZE - left, y + tileY * TILE_SIZE - top, TILE_SIZE, TILE_SIZE);
      }
    }

    if (!loaded) {
      ctx.strokeStyle = '#334746';
      ctx.lineWidth = 1;
      for (let offset = -height; offset < width; offset += 28) {
        ctx.beginPath(); ctx.moveTo(x + offset, y); ctx.lineTo(x + offset + height, y + height); ctx.stroke();
      }
      ctx.fillStyle = '#a0b1ad';
      ctx.font = '600 11px ui-monospace,monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('MAP TILES UNAVAILABLE', x + width / 2, y + height / 2);
    }

    const metersPerPixel = 156543.03392 * Math.cos(clampedLatitude * Math.PI / 180) / 2 ** zoom;
    const accuracyRadius = Number.isFinite(accuracyM) && accuracyM > 0
      ? Math.max(4, Math.min(Math.min(width, height) * .42, accuracyM / metersPerPixel)) : 5;
    const markerX = x + width / 2;
    const markerY = y + height / 2;
    ctx.fillStyle = 'rgba(14, 79, 69, .2)';
    ctx.beginPath(); ctx.arc(markerX, markerY, accuracyRadius, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#57e0bd'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(markerX, markerY, accuracyRadius, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#57e0bd';
    ctx.beginPath(); ctx.arc(markerX, markerY, 4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#f4fff9';
    ctx.beginPath(); ctx.arc(markerX, markerY, 1.4, 0, Math.PI * 2); ctx.fill();

    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.font = '10px ui-monospace,monospace';
    ctx.fillStyle = 'rgba(5, 12, 12, .78)';
    ctx.fillRect(x + 4, y + height - 18, Math.min(width - 8, 156), 14);
    ctx.fillStyle = '#d8e6df';
    ctx.fillText('© OpenStreetMap contributors', x + 8, y + height - 6, width - 16);
    ctx.restore();
  }
}
