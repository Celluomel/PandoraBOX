import argparse
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from body_runtime_host.worldmodel.reconstruction_capture import ReconstructionCaptureStore
from scripts import reconstruct_body_session as job


GAUSSIAN_PLY = (
    "ply\nformat ascii 1.0\nelement vertex 1\n"
    "property float x\nproperty float y\nproperty float z\n"
    "property float scale_0\nproperty float scale_1\nproperty float scale_2\n"
    "property float rot_0\nproperty float rot_1\nproperty float rot_2\nproperty float rot_3\n"
    "property float opacity\nproperty float f_dc_0\nproperty float f_dc_1\nproperty float f_dc_2\n"
    "end_header\n0 0 0 -3 -3 -3 1 0 0 0 1 0.2 0.1 0.0\n"
).encode("ascii")


def make_session(root: Path, *, simulated=False) -> str:
    store = ReconstructionCaptureStore(root)
    session = store.create("offline test")
    for index in range(10):
        image = b"\xff\xd8\xff" + f"frame-{index}".encode()
        store.capture(session["session_id"], {
            "timestamp": index,
            "simulated": simulated,
            "camera": {
                "image_base64": base64.b64encode(image).decode(),
                "frame_id": f"frame-{index}", "width": 640, "height": 480,
            },
        })
    store.close(session["session_id"])
    return session["session_id"]


class ReconstructionJobTests(unittest.TestCase):
    def test_end_to_end_job_publishes_valid_asset_with_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_root = Path(directory) / "captures"
            session_id = make_session(capture_root)
            work_dir = Path(directory) / "job"

            def fake_run(command, cwd):
                command = list(command)
                if command[0] == "ns-process-data":
                    Path(command[command.index("--output-dir") + 1]).mkdir(parents=True)
                elif command[0] == "ns-train":
                    model_root = Path(command[command.index("--output-dir") + 1])
                    config = model_root / "splatfacto" / "test" / "config.yml"
                    config.parent.mkdir(parents=True)
                    config.write_text("fixture", encoding="utf-8")
                elif Path(command[1]).name == "export_gaussian_splat.py":
                    output = Path(command[command.index("--output-dir") + 1])
                    output.mkdir(parents=True)
                    (output / "splat.ply").write_bytes(GAUSSIAN_PLY)

            args = argparse.Namespace(
                capture_root=str(capture_root), session_id=session_id,
                work_dir=str(work_dir), ns_process_data="ns-process-data",
                ns_train="ns-train",
                ns_export="export_gaussian_splat.py",
                iterations=1000,
                device="cuda",
            )
            with patch.object(job, "_run", side_effect=fake_run):
                published = job.run(args)

            self.assertEqual(published, capture_root / "assets" / "current" / "scene.ply")
            status = ReconstructionCaptureStore(capture_root).asset_status()
            self.assertTrue(status["available"], status)
            self.assertEqual(status["sha256"], hashlib.sha256(GAUSSIAN_PLY).hexdigest())
            provenance = json.loads((published.parent / "provenance.json").read_text())
            self.assertEqual(provenance["frame_count"], 10)
            self.assertEqual(provenance["metric_scale"], "unknown_without_measured_pose_or_range_constraint")
            self.assertFalse(provenance["safety_authoritative"])

    def test_simulated_capture_is_rejected_before_toolchain_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_root = Path(directory) / "captures"
            session_id = make_session(capture_root, simulated=True)
            args = argparse.Namespace(
                capture_root=str(capture_root), session_id=session_id,
                work_dir=str(Path(directory) / "job"), ns_process_data="ns-process-data",
                ns_train="ns-train",
                ns_export="export_gaussian_splat.py",
                iterations=1000,
                device="cuda",
            )
            with patch.object(job, "_run") as run_command:
                with self.assertRaisesRegex(job.ReconstructionError, "simulated or replayed"):
                    job.run(args)
            run_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
