"""Fetch a Body capture over HTTPS, reconstruct it on this host, publish to Body."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import reconstruct_body_session as reconstruction


def _request(url: str, token: str, context: ssl.SSLContext, *, data: bytes | None = None, headers: dict | None = None):
    request_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    request_headers.update(headers or {})
    request = Request(url, data=data, headers=request_headers, method="POST" if data is not None else "GET")
    with urlopen(request, timeout=60, context=context) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _body_url(value: str) -> str:
    from urllib.parse import urlsplit
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Body URL must be an HTTPS origin/path without embedded credentials, query, or fragment")
    return value.rstrip("/")


def run(args: argparse.Namespace) -> dict:
    token = str(args.token or os.environ.get("BODY_RECONSTRUCTION_WORKER_TOKEN", "")).strip()
    if not token and args.token_file:
        token_path = Path(args.token_file).expanduser()
        try:
            for line in token_path.read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition("=")
                if separator and key.strip() == "BODY_RECONSTRUCTION_WORKER_TOKEN":
                    token = value.strip()
                    break
        except FileNotFoundError:
            pass
    if len(token) < 32:
        raise ValueError("set BODY_RECONSTRUCTION_WORKER_TOKEN to the shared 32+ character secret")
    if not re.fullmatch(r"[0-9a-f]{10}-[0-9a-f]{8}", args.session_id):
        raise ValueError("invalid reconstruction session id")
    body = _body_url(args.body_url)
    context = ssl.create_default_context(cafile=args.ca_cert or None)
    root = Path(args.capture_root).resolve()
    session_dir = root / args.session_id
    images_dir = session_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    base = f"{body}/worldmodel/reconstruction/worker/sessions/{quote(args.session_id)}"
    raw, _ = _request(base, token, context)
    manifest = json.loads(raw)
    if manifest.get("contract") != "body_reconstruction_session.v1" or manifest.get("session_id") != args.session_id:
        raise ValueError("Body returned an incompatible capture manifest")
    if manifest.get("state") not in {"ready_for_review", "insufficient_views"}:
        raise ValueError("Body capture must be closed before reconstruction")
    frames = manifest.get("frames")
    if not isinstance(frames, list) or not 10 <= len(frames) <= reconstruction.MAX_FRAMES:
        raise ValueError(f"worker requires 10 to {reconstruction.MAX_FRAMES} frames")
    if any(item.get("provenance", {}).get("simulated") or item.get("provenance", {}).get("replayed") for item in frames):
        raise ValueError("simulated/replayed Body frames are rejected")
    (session_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    total = 0
    for index, frame in enumerate(frames):
        relative = str(frame.get("image") or "")
        expected_name = f"images/{index:06d}.jpg"
        if relative != expected_name:
            raise ValueError(f"unexpected capture image path at frame {index}")
        image, content_type = _request(f"{base}/images/{index:06d}.jpg", token, context)
        if content_type.split(";", 1)[0].strip().lower() != "image/jpeg":
            raise ValueError(f"Body returned a non-JPEG frame {index}")
        if len(image) > reconstruction.MAX_CAPTURE_BYTES - total:
            raise ValueError("Body capture exceeds the 2 GiB worker limit")
        if hashlib.sha256(image).hexdigest() != frame.get("image_sha256"):
            raise ValueError(f"frame {index} failed SHA-256 validation after network transfer")
        (images_dir / f"{index:06d}.jpg").write_bytes(image)
        total += len(image)
        print(f"Downloaded frame {index + 1}/{len(frames)} ({total / (1024 * 1024):.1f} MiB)", flush=True)

    job_args = argparse.Namespace(
        capture_root=str(root), session_id=args.session_id, work_dir=args.work_dir,
        ns_process_data=args.ns_process_data, ns_train=args.ns_train,
        ns_export=args.ns_export, iterations=args.iterations, device=args.device,
    )
    asset_path = reconstruction.run(job_args)
    manifest_path = asset_path.parent / "manifest.json"
    provenance_path = asset_path.parent / "provenance.json"
    asset_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    headers = {
        "Content-Type": "application/octet-stream",
        "X-Body-Asset-Manifest": base64.b64encode(json.dumps(asset_manifest, separators=(",", ":")).encode()).decode(),
        "X-Body-Asset-Provenance": base64.b64encode(json.dumps(provenance, separators=(",", ":")).encode()).decode(),
    }
    with asset_path.open("rb") as stream:
        request = Request(
            f"{body}/worldmodel/reconstruction/worker/assets", data=stream.read(), headers={
                "Authorization": f"Bearer {token}", "Accept": "application/json", **headers,
            }, method="POST",
        )
    with urlopen(request, timeout=180, context=context) as response:
        published = json.loads(response.read())
    if not published.get("ok") or not published.get("asset", {}).get("available"):
        raise ValueError(f"Body rejected the reconstructed asset: {published}")
    return {"ok": True, "body": body, "session_id": args.session_id, "asset": published["asset"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id")
    parser.add_argument("--body-url", required=True, help="HTTPS Body origin, e.g. https://192.168.0.14")
    parser.add_argument("--ca-cert", help="trusted Caddy internal root CA certificate")
    parser.add_argument("--token", help="prefer BODY_RECONSTRUCTION_WORKER_TOKEN environment variable")
    parser.add_argument("--token-file", default=str(Path.home() / ".config" / "pandorabox" / "reconstruction-worker.env"))
    parser.add_argument("--capture-root", default=str(Path.home() / ".cache" / "pandorabox" / "reconstruction"))
    parser.add_argument("--work-dir")
    parser.add_argument("--iterations", type=int, default=15000)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--ns-process-data", default="ns-process-data")
    parser.add_argument("--ns-train", default="ns-train")
    parser.add_argument("--ns-export", default=str(Path(__file__).resolve().with_name("export_gaussian_splat.py")))
    args = parser.parse_args()
    if not 1000 <= args.iterations <= 100000:
        parser.error("--iterations must be between 1000 and 100000")
    try:
        print(json.dumps(run(args), indent=2))
    except (OSError, ValueError, HTTPError, URLError, json.JSONDecodeError, reconstruction.ReconstructionError) as exc:
        print(f"remote reconstruction failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
