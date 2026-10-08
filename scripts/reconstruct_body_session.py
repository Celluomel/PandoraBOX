"""Build a Quest-ready 3D Gaussian asset from a real Body capture session.

This offline workstation job uses Nerfstudio (COLMAP + Splatfacto). It never
turns reconstruction output into planner or safety geometry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence
import uuid


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_CAPTURE_ROOT = ROOT / "data" / "body" / "reconstruction"
MAX_FRAMES = 500
MAX_CAPTURE_BYTES = 2 * 1024 * 1024 * 1024
MAX_ASSET_BYTES = 256 * 1024 * 1024


class ReconstructionError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _session_manifest(capture_root: Path, session_id: str) -> tuple[Path, dict]:
    if len(session_id) != 19 or session_id[10] != "-" or not all(
        c in "0123456789abcdef" for c in session_id.replace("-", "")
    ):
        raise ReconstructionError("invalid reconstruction session id")
    directory = (capture_root / session_id).resolve()
    if directory.parent != capture_root.resolve():
        raise ReconstructionError("session path escaped capture root")
    path = directory / "manifest.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconstructionError(f"cannot read capture manifest: {exc}") from exc
    if manifest.get("contract") != "body_reconstruction_session.v1":
        raise ReconstructionError("unsupported capture session contract")
    if manifest.get("state") not in {"ready_for_review", "insufficient_views"}:
        raise ReconstructionError("close the capture session before reconstruction")
    frames = manifest.get("frames")
    if not isinstance(frames, list) or len(frames) < 10:
        raise ReconstructionError("at least 10 captured views are required")
    if len(frames) > MAX_FRAMES:
        raise ReconstructionError(f"offline job is limited to {MAX_FRAMES} frames per run")
    if any(
        item.get("provenance", {}).get("simulated")
        or item.get("provenance", {}).get("replayed")
        for item in frames
    ):
        raise ReconstructionError("simulated or replayed frames cannot produce a real reconstruction")
    return directory, manifest


def _stage_images(session_dir: Path, manifest: dict, destination: Path) -> dict:
    total = 0
    images = destination / "images"
    images.mkdir(parents=True)
    for index, record in enumerate(manifest["frames"]):
        relative = Path(str(record.get("image") or ""))
        if relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != "images":
            raise ReconstructionError(f"frame {index} has an unsafe image path")
        source = (session_dir / relative).resolve()
        if source.parent != (session_dir / "images").resolve() or not source.is_file():
            raise ReconstructionError(f"frame {index} image is missing or outside its session")
        size = source.stat().st_size
        total += size
        if total > MAX_CAPTURE_BYTES:
            raise ReconstructionError("capture exceeds the 2 GiB offline-processing limit")
        expected = record.get("image_sha256")
        if not isinstance(expected, str) or sha256_file(source) != expected:
            raise ReconstructionError(f"frame {index} failed SHA-256 verification")
        suffix = source.suffix.lower()
        if suffix not in {".jpg", ".jpeg"}:
            raise ReconstructionError(f"frame {index} is not a JPEG")
        shutil.copyfile(source, images / f"{index:06d}.jpg")
    return {"frame_count": len(manifest["frames"]), "image_bytes": total}


def _run(command: Sequence[str], cwd: Path) -> None:
    print("+", subprocess.list2cmdline(list(command)), flush=True)
    try:
        subprocess.run(list(command), cwd=cwd, check=True)
    except FileNotFoundError as exc:
        raise ReconstructionError(
            f"required executable not found: {command[0]}; install COLMAP and Nerfstudio in the workstation environment"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ReconstructionError(f"command failed with exit code {exc.returncode}: {command[0]}") from exc


def _find_export(output_dir: Path) -> Path:
    candidates = [path for path in output_dir.rglob("*.ply") if path.is_file()]
    if len(candidates) != 1:
        raise ReconstructionError(f"expected exactly one exported PLY, found {len(candidates)}")
    asset = candidates[0]
    if asset.stat().st_size <= 0 or asset.stat().st_size > MAX_ASSET_BYTES:
        raise ReconstructionError("exported Gaussian PLY must be non-empty and <=256 MiB for Quest")
    # Reuse the Body's schema validator, which rejects ordinary point clouds.
    from body_runtime_host.worldmodel.reconstruction_capture import ReconstructionCaptureStore
    ReconstructionCaptureStore._validate_gaussian_ply(asset)
    return asset


def run(args: argparse.Namespace) -> Path:
    capture_root = Path(args.capture_root).resolve()
    session_dir, manifest = _session_manifest(capture_root, args.session_id)
    run_dir = Path(args.work_dir).resolve() if args.work_dir else session_dir / (
        "offline-reconstruction-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    )
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ReconstructionError(f"work directory already exists; choose a new path: {run_dir}") from exc
    staged = run_dir / "dataset"
    source_info = _stage_images(session_dir, manifest, staged)

    processed = run_dir / "nerfstudio-data"
    model_dir = run_dir / "models"
    exports = run_dir / "exports"
    if not os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    _run([
        args.ns_process_data, "images", "--data", str(staged / "images"),
        "--output-dir", str(processed), "--matching-method", "sequential",
        "--camera-type", "perspective", "--skip-image-processing", "--no-gpu",
    ], run_dir)
    train_command = [
        args.ns_train, "splatfacto", "--data", str(processed),
        "--output-dir", str(model_dir), "--max-num-iterations", str(args.iterations),
    ]
    if args.device:
        train_command.extend(["--machine.device-type", args.device])
    _run(train_command, run_dir)
    configs = list(model_dir.rglob("config.yml"))
    if len(configs) != 1:
        raise ReconstructionError(f"expected one Nerfstudio config.yml, found {len(configs)}")
    _run(
        [
            sys.executable,
            args.ns_export,
            "gaussian-splat",
            "--load-config",
            str(configs[0]),
            "--output-dir",
            str(exports),
        ],
        run_dir,
    )
    asset = _find_export(exports)

    provenance = {
        "capture_contract": manifest["contract"],
        "session_id": args.session_id,
        "source": "real_body_camera_capture",
        "simulated_or_replayed": False,
        "frame_count": source_info["frame_count"],
        "image_bytes": source_info["image_bytes"],
        "pose_strategy": "COLMAP visual SfM",
        "metric_scale": "unknown_without_measured_pose_or_range_constraint",
        "toolchain": {
            "nerfstudio": args.ns_train,
            "iterations": args.iterations,
            "camera_type": "perspective",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "safety_authoritative": False,
    }
    target_root = capture_root / "assets" / "current"
    target_root.parent.mkdir(parents=True, exist_ok=True)
    staging = target_root.parent / f".current-{uuid.uuid4().hex}.tmp"
    staging.mkdir()
    filename = "scene.ply"
    shutil.copyfile(asset, staging / filename)
    digest = sha256_file(staging / filename)
    (staging / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    body_manifest = {
        "contract": "body_gaussian_asset.v1",
        "asset_id": f"{args.session_id}-splatfacto",
        "file": filename,
        "format": "ply",
        "sha256": digest,
        "coordinate_frame": "reconstruction",
        "transform": {"position": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]},
        "provenance": "provenance.json",
    }
    (staging / "manifest.json").write_text(json.dumps(body_manifest, indent=2) + "\n", encoding="utf-8")

    from body_runtime_host.worldmodel.reconstruction_capture import ReconstructionCaptureStore
    validation_current = run_dir / "asset-validation-store" / "assets" / "current"
    validation_current.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(staging / filename, validation_current / filename)
    shutil.copyfile(staging / "manifest.json", validation_current / "manifest.json")
    status = ReconstructionCaptureStore(run_dir / "asset-validation-store").asset_status()
    if not status.get("available"):
        shutil.rmtree(staging, ignore_errors=True)
        raise ReconstructionError(f"Body rejected exported Gaussian asset: {status.get('message')}")

    backup = target_root.parent / f".previous-{uuid.uuid4().hex}"
    if target_root.exists():
        os.replace(target_root, backup)
    try:
        os.replace(staging, target_root)
    except Exception:
        if backup.exists() and not target_root.exists():
            os.replace(backup, target_root)
        raise
    print(json.dumps({"ok": True, "asset": str(target_root / filename), "asset_id": body_manifest["asset_id"], "sha256": digest, "quest_validation": status, "provenance": provenance}, indent=2))
    return target_root / filename


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id", help="closed real Body capture session ID")
    parser.add_argument("--capture-root", default=str(DEFAULT_CAPTURE_ROOT))
    parser.add_argument("--work-dir", help="temporary job directory (defaults inside session)")
    parser.add_argument("--iterations", type=int, default=15000)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--ns-process-data", default="ns-process-data")
    parser.add_argument("--ns-train", default="ns-train")
    parser.add_argument(
        "--ns-export",
        default=str(ROOT / "scripts" / "export_gaussian_splat.py"),
        help="Nerfstudio Gaussian export launcher (keeps mesh-only PyMeshLab optional)",
    )
    args = parser.parse_args()
    if not 1000 <= args.iterations <= 100000:
        parser.error("--iterations must be between 1000 and 100000")
    try:
        run(args)
    except ReconstructionError as exc:
        print(f"reconstruction failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
