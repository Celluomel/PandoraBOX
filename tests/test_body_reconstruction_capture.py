import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from body_runtime_host.worldmodel.reconstruction_capture import ReconstructionCaptureStore

TEMP_ROOT = Path(__file__).resolve().parents[1] / ".test-tmp"
TEMP_ROOT.mkdir(exist_ok=True)


def frame(image=b"\xff\xd8\xffcamera-frame", *, frame_id="frame-1", pose=None, modalities=None, simulated=False):
    return {
        "contract": "body_perception_frame.v2",
        "frame_id": frame_id,
        "timestamp": 12.5,
        "source": "camera_fixture",
        "simulated": simulated,
        "camera": {
            "image_base64": base64.b64encode(image).decode("ascii"),
            "mime_type": "image/jpeg", "width": 640, "height": 480,
            "frame_id": frame_id, "captured_at": 12.5,
            "source": "fixture_camera", "calibration": {"fx": 500, "fy": 500},
        },
        "body": {"pose": pose or {}},
        "modalities": modalities or {},
    }


class ReconstructionCaptureStoreTests(unittest.TestCase):
    def test_worker_can_read_only_a_closed_real_session_and_verified_images(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create("worker input")
            session_id = session["session_id"]
            image = b"\xff\xd8\xffframe-one"
            store.capture(session_id, frame(image=image))
            with self.assertRaisesRegex(ValueError, "closed"):
                store.worker_session_manifest(session_id)
            store.close(session_id)
            self.assertEqual(store.worker_session_manifest(session_id)["frame_count"], 1)
            self.assertEqual(store.worker_image_file(session_id, "000000.jpg").read_bytes(), image)
            with self.assertRaisesRegex(ValueError, "invalid capture image filename"):
                store.worker_image_file(session_id, "../manifest.json")
            (Path(directory) / session_id / "images" / "000000.jpg").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                store.worker_image_file(session_id, "000000.jpg")

    def test_worker_publish_validates_and_atomically_exposes_gaussian_asset(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create("worker publish provenance")
            for index in range(10):
                store.capture(session["session_id"], frame(image=b"\xff\xd8\xff" + f"publish-{index}".encode(), frame_id=f"publish-{index}"))
            store.close(session["session_id"])
            fields = "x y z scale_0 scale_1 scale_2 rot_0 rot_1 rot_2 rot_3 opacity f_dc_0 f_dc_1 f_dc_2".split()
            data = ("ply\nformat ascii 1.0\nelement vertex 1\n" + "".join(f"property float {name}\n" for name in fields) + "end_header\n0 0 0 -3 -3 -3 1 0 0 0 1 0.2 0.1 0.0\n").encode()
            source = Path(directory) / "worker.ply"
            source.write_bytes(data)
            manifest = {
                "contract": "body_gaussian_asset.v1", "asset_id": "session-splatfacto",
                "file": "scene.ply", "format": "ply", "sha256": hashlib.sha256(data).hexdigest(),
            }
            provenance = {
                "capture_contract": store.CONTRACT, "session_id": session["session_id"],
                "source": "real_body_camera_capture", "frame_count": 10,
                "simulated_or_replayed": False,
            }
            published = store.publish_asset(source, manifest, provenance)
            self.assertTrue(published["ok"])
            self.assertTrue(published["asset"]["available"])
            self.assertEqual(store.asset_file().read_bytes(), data)
            self.assertTrue((Path(directory) / "assets/current/provenance.json").is_file())

            with self.assertRaisesRegex(ValueError, "SHA-256"):
                store.publish_asset(source, {**manifest, "sha256": "0" * 64}, provenance)

    def test_asset_status_does_not_expose_simulation_as_real_gaussian_scene(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            status = ReconstructionCaptureStore(directory).asset_status()
            self.assertFalse(status["available"])
            self.assertTrue(status["renderer_available"])
            self.assertEqual(status["reason"], "no_published_reconstruction")

    def test_published_gaussian_ply_is_hash_checked_and_available_to_quest(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            current = Path(directory) / "assets" / "current"
            current.mkdir(parents=True)
            fields = "x y z scale_0 scale_1 scale_2 rot_0 rot_1 rot_2 rot_3 opacity f_dc_0 f_dc_1 f_dc_2".split()
            ply = "ply\nformat ascii 1.0\nelement vertex 1\n" + "".join(f"property float {name}\n" for name in fields)
            ply += "end_header\n0 0 0 -3 -3 -3 1 0 0 0 1 0.2 0.1 0.0\n"
            asset = ply.encode("ascii")
            (current / "room.ply").write_bytes(asset)
            (current / "manifest.json").write_text(json.dumps({
                "contract": "body_gaussian_asset.v1", "asset_id": "room-001",
                "file": "room.ply", "format": "ply",
                "sha256": hashlib.sha256(asset).hexdigest(),
                "coordinate_frame": "map", "transform": {"position": [1, 0, 2]},
            }), encoding="utf-8")

            status = store.asset_status()
            self.assertTrue(status["available"])
            self.assertTrue(status["renderer_available"])
            self.assertEqual(status["file_url"], "/worldmodel/reconstruction/asset/file")
            self.assertEqual(status["coordinate_frame"], "map")
            self.assertEqual(status["transform"]["position"], [1, 0, 2])
            self.assertEqual(store.asset_file(), current / "room.ply")

    def test_point_cloud_ply_and_hash_mismatch_are_not_renderable_assets(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            current = Path(directory) / "assets" / "current"
            current.mkdir(parents=True)
            asset = b"ply\nformat ascii 1.0\nelement vertex 1\nproperty float x\nproperty float y\nproperty float z\nend_header\n0 0 0\n"
            (current / "points.ply").write_bytes(asset)
            manifest_path = current / "manifest.json"
            base = {"contract": "body_gaussian_asset.v1", "file": "points.ply", "format": "ply", "sha256": hashlib.sha256(asset).hexdigest()}
            manifest_path.write_text(json.dumps(base), encoding="utf-8")
            self.assertFalse(store.asset_status()["available"])

            fields = "x y z scale_0 scale_1 scale_2 rot_0 rot_1 rot_2 rot_3 opacity f_dc_0 f_dc_1 f_dc_2".split()
            ply = "ply\nformat ascii 1.0\nelement vertex 1\n" + "".join(f"property float {name}\n" for name in fields) + "end_header\n0 0 0 -3 -3 -3 1 0 0 0 1 0.2 0.1 0.0\n"
            asset = ply.encode("ascii")
            (current / "points.ply").write_bytes(asset)
            manifest_path.write_text(json.dumps(base), encoding="utf-8")
            self.assertEqual(store.asset_status()["reason"], "invalid_reconstruction_asset")

    def test_manifest_cannot_escape_published_asset_directory(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            current = Path(directory) / "assets" / "current"
            current.mkdir(parents=True)
            (current / "manifest.json").write_text(json.dumps({
                "contract": "body_gaussian_asset.v1", "file": "../outside.ply", "format": "ply", "sha256": "0" * 64,
            }), encoding="utf-8")
            self.assertFalse(store.asset_status()["available"])

    def test_camera_only_session_is_saved_with_explicit_unknown_scale(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(Path(directory) / "sessions")
            session = store.create("hallway test")
            result = store.capture(session["session_id"], frame())
            closed = store.close(session["session_id"])
            self.assertTrue(result["accepted"])
            self.assertEqual(closed["state"], "insufficient_views")
            self.assertEqual(closed["reconstruction"]["metric_scale"], "unresolved_without_metric_pose_or_range_sensor")
            self.assertEqual(closed["readiness"]["pose_recovery_required"], True)
            self.assertEqual(closed["readiness"]["metric_scale_available"], False)
            self.assertTrue((Path(directory) / "sessions" / session["session_id"] / "images" / "000000.jpg").exists())

    def test_optional_lidar_and_measured_pose_are_preserved_as_constraints(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create()
            capture = frame(
                pose={"position_m": [1, 2, 0], "yaw_rad": 0.4, "coordinate_frame": "map", "position_source": "vio"},
                modalities={"lidar": {"source": "native", "points": [{"x": 1.2, "y": 0.1, "z": 0.0}]}},
            )
            result = store.capture(session["session_id"], capture)
            self.assertEqual(result["frame"]["pose_status"], "measured")
            self.assertEqual(result["frame"]["sensor_constraints"]["lidar"]["source"], "native")
            self.assertIn("lidar", store.list_sessions()["sessions"][0]["sensor_modalities"])

    def test_simulated_pose_and_replayed_lidar_do_not_claim_real_metric_scale(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create()
            sample = frame(
                pose={"position_m": [1, 2, 0], "yaw_rad": 0.4},
                modalities={"lidar": {"native": True, "points": [{"x": 1, "y": 0, "z": 0}]}},
                simulated=True,
            )
            store.capture(session["session_id"], sample)
            closed = store.close(session["session_id"])
            self.assertEqual(closed["readiness"]["measured_pose_count"], 0)
            self.assertFalse(closed["readiness"]["metric_scale_available"])

    def test_real_camera_frames_remain_eligible_with_explicitly_simulated_pose(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create("real camera, no physical odometry")
            sample = frame(
                image=b"\xff\xd8\xffreal-camera-frame",
                pose={"position_m": [1, 2, 0], "yaw_rad": 0.4, "position_source": "simulated_odometry"},
            )
            sample["camera"]["source"] = "pc_camera"
            sample["simulated"] = False
            sample["pose_simulated"] = True
            stored = store.capture(session["session_id"], sample)
            closed = store.close(session["session_id"])

            self.assertTrue(stored["accepted"])
            self.assertFalse(stored["frame"]["provenance"]["simulated"])
            self.assertTrue(stored["frame"]["provenance"]["pose_simulated"])
            self.assertEqual(stored["frame"]["pose_status"], "simulated")
            self.assertEqual(closed["readiness"]["measured_pose_count"], 0)
            self.assertEqual(store.worker_session_manifest(session["session_id"])["frame_count"], 1)

    def test_duplicate_image_is_not_recorded_twice(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create()
            self.assertTrue(store.capture(session["session_id"], frame())["accepted"])
            duplicate = store.capture(session["session_id"], frame(frame_id="another-frame"))
            self.assertFalse(duplicate["accepted"])
            self.assertEqual(duplicate["reason"], "duplicate_image")
            self.assertEqual(duplicate["frame_count"], 1)

    def test_rejects_invalid_image_and_path_traversal(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            store = ReconstructionCaptureStore(directory)
            session = store.create()
            with self.assertRaisesRegex(ValueError, "JPEG"):
                store.capture(session["session_id"], frame(image=b"not an image"))
            with self.assertRaisesRegex(ValueError, "session id"):
                store.close("../outside")


if __name__ == "__main__":
    unittest.main()
