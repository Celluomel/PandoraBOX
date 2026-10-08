"""Bounded, provenance-preserving camera-first reconstruction captures.

This stores inputs for an offline Gaussian reconstruction worker. It does not
claim that images alone provide metric geometry or that a splat is a safety map.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
import time
from typing import Any
import uuid


class ReconstructionCaptureStore:
    CONTRACT = "body_reconstruction_session.v1"
    MAX_IMAGE_BYTES = 12 * 1024 * 1024
    MAX_SESSION_BYTES = 2 * 1024 * 1024 * 1024
    MAX_FRAMES = 20_000
    MAX_GAUSSIAN_ASSET_BYTES = 256 * 1024 * 1024

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asset_validation_cache: tuple[tuple[str, int, int], dict[str, Any]] | None = None

    def create(self, name: str = "capture") -> dict[str, Any]:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(name).strip()).strip("-_")[:48] or "capture"
        session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        directory = self._session_dir(session_id)
        with self._lock:
            directory.mkdir(parents=False, exist_ok=False)
            (directory / "images").mkdir()
            manifest = {
                "contract": self.CONTRACT,
                "session_id": session_id,
                "name": safe_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "state": "capturing",
                "reconstruction": {
                    "appearance_source": "camera_images",
                    "pose_strategy": "provided_pose_or_offline_visual_sfm",
                    "metric_scale": "unresolved_without_metric_pose_or_range_sensor",
                    "lidar": "optional_future_constraint",
                    "safety_authoritative": False,
                },
                "frame_count": 0,
                "image_bytes": 0,
                "frames": [],
            }
            self._write_json(directory / "manifest.json", manifest)
        return self._public_manifest(manifest)

    def capture(self, session_id: str, frame: dict[str, Any]) -> dict[str, Any]:
        directory = self._session_dir(session_id)
        camera = frame.get("camera") if isinstance(frame, dict) else None
        camera = camera if isinstance(camera, dict) else {}
        encoded = camera.get("image_base64")
        if not isinstance(encoded, str) or not encoded:
            raise ValueError("camera image_base64 is required")
        try:
            image = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("camera image is not valid base64") from exc
        if not image.startswith(b"\xff\xd8\xff") or len(image) > self.MAX_IMAGE_BYTES:
            raise ValueError("camera image must be a JPEG no larger than 12 MiB")

        timestamp = self._finite(camera.get("captured_at", frame.get("timestamp")))
        frame_id = str(camera.get("frame_id") or frame.get("frame_id") or f"capture-{int(timestamp * 1000)}")[:160]
        pose = frame.get("body") if isinstance(frame.get("body"), dict) else {}
        pose = pose.get("pose") if isinstance(pose.get("pose"), dict) else {}
        pose_record = self._pose_record(pose)
        simulated = bool(frame.get("simulated", False))
        modalities = frame.get("modalities") if isinstance(frame.get("modalities"), dict) else {}
        sensor_data = {
            key: modalities[key]
            for key in ("imu", "lidar", "mmwave_radar", "gps", "odometry", "depth")
            if key in modalities
        }
        digest = hashlib.sha256(image).hexdigest()

        with self._lock:
            manifest = self._read_manifest(directory)
            if manifest.get("state") != "capturing":
                raise ValueError("reconstruction session is already closed")
            if manifest["frame_count"] >= self.MAX_FRAMES:
                raise ValueError("reconstruction session reached its frame limit")
            if manifest["image_bytes"] + len(image) > self.MAX_SESSION_BYTES:
                raise ValueError("reconstruction session reached its 2 GiB storage limit")
            if any(item.get("image_sha256") == digest for item in manifest["frames"]):
                return {"ok": True, "accepted": False, "reason": "duplicate_image", **self._public_manifest(manifest)}

            index = manifest["frame_count"]
            filename = f"{index:06d}.jpg"
            image_path = directory / "images" / filename
            self._write_bytes(image_path, image)
            record = {
                "index": index,
                "frame_id": frame_id,
                "timestamp": timestamp,
                "image": f"images/{filename}",
                "image_sha256": digest,
                "width": self._positive_int(camera.get("width")),
                "height": self._positive_int(camera.get("height")),
                "camera_source": str(camera.get("source") or "unknown")[:80],
                "camera_calibration": self._json_safe(camera.get("calibration") or {}),
                "pose": pose_record,
                "pose_status": (
                    "simulated" if pose_record and simulated
                    else "measured" if pose_record
                    else "unavailable_visual_sfm_required"
                ),
                "sensor_constraints": self._json_safe(sensor_data),
                "synchronization": self._json_safe(frame.get("synchronization") or {}),
                "provenance": {
                    "frame_source": str(frame.get("source") or "unknown")[:80],
                    "simulated": simulated,
                    "replayed": bool(frame.get("replayed", False)),
                },
            }
            manifest["frames"].append(record)
            manifest["frame_count"] += 1
            manifest["image_bytes"] += len(image)
            manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_json(directory / "manifest.json", manifest)

        return {"ok": True, "accepted": True, "frame": record, **self._public_manifest(manifest)}

    def close(self, session_id: str) -> dict[str, Any]:
        directory = self._session_dir(session_id)
        with self._lock:
            manifest = self._read_manifest(directory)
            manifest["state"] = "ready_for_review" if manifest["frame_count"] >= 10 else "insufficient_views"
            manifest["closed_at"] = datetime.now(timezone.utc).isoformat()
            manifest["readiness"] = self._readiness(manifest)
            self._write_json(directory / "manifest.json", manifest)
        return self._public_manifest(manifest)

    def list_sessions(self) -> dict[str, Any]:
        sessions = []
        for path in sorted(self.root.iterdir(), reverse=True):
            if not path.is_dir() or not re.fullmatch(r"\d{10}-[a-f0-9]{8}", path.name):
                continue
            try:
                sessions.append(self._public_manifest(self._read_manifest(path)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return {"contract": self.CONTRACT, "sessions": sessions[:100]}

    def worker_session_manifest(self, session_id: str) -> dict[str, Any]:
        """Return a closed, real capture session for the remote reconstruction worker."""
        directory = self._session_dir(session_id)
        manifest = self._read_manifest(directory)
        if manifest.get("state") not in {"ready_for_review", "insufficient_views"}:
            raise ValueError("capture session must be closed before worker download")
        if any(
            item.get("provenance", {}).get("simulated")
            or item.get("provenance", {}).get("replayed")
            for item in manifest.get("frames", [])
        ):
            raise ValueError("simulated or replayed sessions cannot be reconstructed as real captures")
        return manifest

    def worker_image_file(self, session_id: str, filename: str) -> Path:
        manifest = self.worker_session_manifest(session_id)
        if not re.fullmatch(r"\d{6}\.jpg", filename):
            raise ValueError("invalid capture image filename")
        relative = f"images/{filename}"
        record = next((item for item in manifest.get("frames", []) if item.get("image") == relative), None)
        if record is None:
            raise ValueError("image is not part of this capture session")
        path = self._session_dir(session_id) / relative
        if not path.is_file() or path.stat().st_size > self.MAX_IMAGE_BYTES:
            raise ValueError("capture image is missing or exceeds the image size limit")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record.get("image_sha256"):
            raise ValueError("capture image failed SHA-256 verification")
        return path

    def publish_asset(self, asset_path: str | Path, manifest: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
        """Validate and atomically publish a remote worker's Gaussian asset."""
        source = Path(asset_path).resolve()
        if not source.is_file() or source.stat().st_size <= 0 or source.stat().st_size > self.MAX_GAUSSIAN_ASSET_BYTES:
            raise ValueError("worker asset must be non-empty and no larger than 256 MiB")
        if not isinstance(manifest, dict) or manifest.get("contract") != "body_gaussian_asset.v1":
            raise ValueError("unsupported Gaussian asset manifest contract")
        if manifest.get("format") != "ply" or manifest.get("file") != "scene.ply":
            raise ValueError("worker publication must contain a scene.ply Gaussian PLY")
        expected = str(manifest.get("sha256") or "").lower()
        digest = hashlib.sha256()
        with source.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if not re.fullmatch(r"[a-f0-9]{64}", expected) or digest.hexdigest() != expected:
            raise ValueError("worker asset SHA-256 does not match its manifest")
        self._validate_gaussian_ply(source)
        transform = self._asset_transform(manifest.get("transform"))
        asset_id = str(manifest.get("asset_id") or "").strip()
        if not asset_id or len(asset_id) > 120:
            raise ValueError("worker asset manifest requires a valid asset_id")
        if not isinstance(provenance, dict) or provenance.get("simulated_or_replayed") is not False:
            raise ValueError("worker provenance must confirm a real, non-replayed capture")
        session_id = str(provenance.get("session_id") or "")
        source_manifest = self.worker_session_manifest(session_id)
        if provenance.get("capture_contract") != self.CONTRACT or provenance.get("frame_count") != source_manifest.get("frame_count"):
            raise ValueError("worker provenance does not match the closed Body capture session")
        safe_manifest = {
            "contract": "body_gaussian_asset.v1", "asset_id": asset_id,
            "file": "scene.ply", "format": "ply", "sha256": expected,
            "coordinate_frame": str(manifest.get("coordinate_frame") or "reconstruction")[:80],
            "transform": transform, "provenance": "provenance.json",
        }
        target_root = self.root / "assets" / "current"
        target_root.parent.mkdir(parents=True, exist_ok=True)
        staging = target_root.parent / f".current-{uuid.uuid4().hex}.tmp"
        staging.mkdir()
        try:
            import shutil
            shutil.copyfile(source, staging / "scene.ply")
            self._write_json(staging / "manifest.json", safe_manifest)
            self._write_json(staging / "provenance.json", provenance)
            backup = target_root.parent / f".previous-{uuid.uuid4().hex}"
            if target_root.exists():
                os.replace(target_root, backup)
            try:
                os.replace(staging, target_root)
            except Exception:
                if backup.exists() and not target_root.exists():
                    os.replace(backup, target_root)
                raise
        finally:
            if staging.exists():
                import shutil
                shutil.rmtree(staging, ignore_errors=True)
        with self._lock:
            self._asset_validation_cache = None
        status = self.asset_status()
        if not status.get("available"):
            raise ValueError(f"published asset did not pass Body validation: {status.get('message')}")
        return {"ok": True, "asset": status, "provenance": provenance}

    def asset_status(self) -> dict[str, Any]:
        """Validate the published local 3DGS asset before enabling Quest rendering."""
        manifest_path = self.root / "assets" / "current" / "manifest.json"
        if not manifest_path.is_file():
            return self._asset_unavailable("no_published_reconstruction", "No reconstructed 3DGS asset has been published.")
        try:
            stat = manifest_path.stat()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or manifest.get("contract") != "body_gaussian_asset.v1":
                raise ValueError("unsupported reconstruction asset contract")
            filename = manifest.get("file")
            if not isinstance(filename, str) or Path(filename).name != filename or filename in {"", ".", ".."}:
                raise ValueError("asset file must be a filename inside assets/current")
            asset_path = (manifest_path.parent / filename).resolve()
            if asset_path.parent != manifest_path.parent.resolve() or not asset_path.is_file():
                raise ValueError("published reconstruction file is missing or outside assets/current")
            suffix = asset_path.suffix.lower()
            if suffix not in {".ply", ".splat", ".ksplat"}:
                raise ValueError("supported 3DGS formats are .ply, .splat and .ksplat")
            declared_format = str(manifest.get("format") or suffix.lstrip(".")).lower().lstrip(".")
            if declared_format != suffix.lstrip("."):
                raise ValueError("manifest format does not match the asset filename")
            asset_stat = asset_path.stat()
            if asset_stat.st_size <= 0 or asset_stat.st_size > self.MAX_GAUSSIAN_ASSET_BYTES:
                raise ValueError("asset must be non-empty and no larger than 256 MiB for Quest loading")
            expected_digest = str(manifest.get("sha256") or "").lower()
            if not re.fullmatch(r"[a-f0-9]{64}", expected_digest):
                raise ValueError("manifest must include the asset SHA-256")
            cache_key = (
                str(manifest_path), stat.st_size, stat.st_mtime_ns,
                str(asset_path), asset_stat.st_size, asset_stat.st_mtime_ns, expected_digest,
            )
            with self._lock:
                cached = self._asset_validation_cache and self._asset_validation_cache[0] == cache_key
            if not cached:
                if suffix == ".ply":
                    self._validate_gaussian_ply(asset_path)
                digest = hashlib.sha256()
                with asset_path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != expected_digest:
                    raise ValueError("asset SHA-256 does not match its manifest")
            transform = self._asset_transform(manifest.get("transform"))
            result = {
                "contract": "body_gaussian_asset.v1",
                "available": True,
                "renderer_available": True,
                "reason": "ready",
                "asset_id": str(manifest.get("asset_id") or filename)[:120],
                "format": suffix.lstrip("."),
                "file_url": "/worldmodel/reconstruction/asset/file",
                "byte_length": asset_stat.st_size,
                "sha256": expected_digest,
                "transform": transform,
                "coordinate_frame": str(manifest.get("coordinate_frame") or "reconstruction")[:80],
                "message": f"Validated {suffix.lstrip('.').upper()} Gaussian reconstruction is ready for the Quest renderer.",
            }
            with self._lock:
                self._asset_validation_cache = (cache_key, result)
            return dict(result)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._asset_unavailable("invalid_reconstruction_asset", str(exc)[:240])

    def asset_file(self) -> Path | None:
        status = self.asset_status()
        if not status.get("available"):
            return None
        manifest_path = self.root / "assets" / "current" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return manifest_path.parent / manifest["file"]

    @staticmethod
    def _asset_unavailable(reason: str, message: str) -> dict[str, Any]:
        return {
            "contract": "body_gaussian_asset.v1",
            "available": False,
            "renderer_available": True,
            "reason": reason,
            "message": message,
        }

    @staticmethod
    def _validate_gaussian_ply(path: Path) -> None:
        with path.open("rb") as stream:
            header = stream.read(64 * 1024)
        end = header.find(b"end_header")
        if end < 0:
            raise ValueError("PLY header is missing or exceeds 64 KiB")
        text = header[:end].decode("ascii", errors="strict")
        properties = set(re.findall(r"^\s*property\s+\w+\s+(\w+)\s*$", text, re.MULTILINE))
        required = {"x", "y", "z", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3", "opacity", "f_dc_0", "f_dc_1", "f_dc_2"}
        if not required.issubset(properties):
            raise ValueError("PLY is not a Gaussian-splat PLY (missing scale/rotation/opacity/color fields)")
        if not re.search(r"^element\s+vertex\s+[1-9]\d*\s*$", text, re.MULTILINE):
            raise ValueError("Gaussian PLY has no vertices")

    @staticmethod
    def _asset_transform(value: Any) -> dict[str, list[float]]:
        value = value if isinstance(value, dict) else {}

        def vector(key: str, default: list[float], length: int) -> list[float]:
            raw = value.get(key, default)
            if not isinstance(raw, list) or len(raw) != length:
                raise ValueError(f"asset transform {key} must contain {length} numbers")
            result = [float(item) for item in raw]
            if not all(math.isfinite(item) for item in result):
                raise ValueError(f"asset transform {key} must be finite")
            return result

        scale = vector("scale", [1, 1, 1], 3)
        if any(item <= 0 or item > 1000 for item in scale):
            raise ValueError("asset scale values must be in (0, 1000]")
        return {
            "position": vector("position", [0, 0, 0], 3),
            "rotation": vector("rotation", [0, 0, 0, 1], 4),
            "scale": scale,
        }

    def _readiness(self, manifest: dict[str, Any]) -> dict[str, Any]:
        frames = manifest["frames"]
        known_pose_count = sum(item.get("pose_status") == "measured" for item in frames)
        calibrated_count = sum(bool(item.get("camera_calibration")) for item in frames)
        return {
            "image_count": len(frames),
            "minimum_views_met": len(frames) >= 10,
            "camera_calibration_present": calibrated_count == len(frames) and bool(frames),
            "measured_pose_count": known_pose_count,
            "pose_recovery_required": known_pose_count < 2,
            "metric_scale_available": known_pose_count >= 2 or any(
                not item.get("provenance", {}).get("simulated")
                and not item.get("provenance", {}).get("replayed")
                and _has_native_lidar(item.get("sensor_constraints", {}).get("lidar"))
                for item in frames
            ),
            "offline_reconstruction_candidate": len(frames) >= 10,
            "intrinsics_estimation_required": calibrated_count < len(frames),
            "note": "Visual reconstruction may use SfM-recovered poses; metric scale requires measured pose or range constraints. This dataset is never a safety map.",
        }

    def _session_dir(self, session_id: str) -> Path:
        if not re.fullmatch(r"\d{10}-[a-f0-9]{8}", str(session_id)):
            raise ValueError("invalid reconstruction session id")
        path = (self.root / session_id).resolve()
        if path.parent != self.root:
            raise ValueError("invalid reconstruction session path")
        return path

    @staticmethod
    def _pose_record(pose: dict[str, Any]) -> dict[str, Any] | None:
        try:
            pos = [float(value) for value in pose["position_m"][:3]]
            yaw = float(pose["yaw_rad"])
            if len(pos) != 3 or not all(map(lambda x: x == x and abs(x) != float("inf"), pos + [yaw])):
                return None
            return {
                "position_m": pos,
                "yaw_rad": yaw,
                "coordinate_frame": str(pose.get("coordinate_frame") or "unknown")[:80],
                "source": str(pose.get("position_source") or "unknown")[:80],
                "accuracy_m": pose.get("accuracy_m"),
            }
        except (KeyError, TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _finite(value: Any) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            result = time.time()
        if not (result == result and abs(result) != float("inf")):
            raise ValueError("frame timestamp must be finite")
        return result

    @staticmethod
    def _positive_int(value: Any) -> int | None:
        try:
            result = int(value)
            return result if result > 0 else None
        except (TypeError, ValueError, OverflowError):
            return None

    @classmethod
    def _json_safe(cls, value: Any, depth: int = 0) -> Any:
        if depth > 12:
            return "[depth-limited]"
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            return value if value == value and abs(value) != float("inf") else None
        if isinstance(value, dict):
            return {str(key)[:100]: cls._json_safe(item, depth + 1) for key, item in list(value.items())[:20_000]}
        if isinstance(value, (list, tuple)):
            return [cls._json_safe(item, depth + 1) for item in value[:50_000]]
        return str(value)[:200]

    @staticmethod
    def _write_bytes(path: Path, payload: bytes) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    @classmethod
    def _write_json(cls, path: Path, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        cls._write_bytes(path, data)

    @staticmethod
    def _read_manifest(directory: Path) -> dict[str, Any]:
        path = directory / "manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("contract") != ReconstructionCaptureStore.CONTRACT:
            raise ValueError("unsupported reconstruction session contract")
        return payload

    @staticmethod
    def _public_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in manifest.items() if key != "frames"} | {
            "frame_count": int(manifest.get("frame_count", 0)),
            "pose_count": sum(item.get("pose_status") == "measured" for item in manifest.get("frames", [])),
            "sensor_modalities": sorted({
                key for item in manifest.get("frames", [])
                for key in (item.get("sensor_constraints") or {})
            }),
            "readiness": manifest.get("readiness"),
        }


def _has_native_lidar(value: Any) -> bool:
    return isinstance(value, dict) and value.get("native") is True and bool(
        value.get("points") or value.get("returns")
    )
