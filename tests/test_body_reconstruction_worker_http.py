import json
import socket
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import MagicMock, patch

import body_runtime_host.runtime as brt
from body_runtime_host.worldmodel.reconstruction_capture import ReconstructionCaptureStore
from scripts import run_remote_reconstruction as remote_job

GAUSSIAN_PLY = (
    "ply\nformat ascii 1.0\nelement vertex 1\n"
    "property float x\nproperty float y\nproperty float z\n"
    "property float scale_0\nproperty float scale_1\nproperty float scale_2\n"
    "property float rot_0\nproperty float rot_1\nproperty float rot_2\nproperty float rot_3\n"
    "property float opacity\nproperty float f_dc_0\nproperty float f_dc_1\nproperty float f_dc_2\n"
    "end_header\n0 0 0 -3 -3 -3 1 0 0 0 1 0.2 0.1 0.0\n"
).encode("ascii")


class ReconstructionWorkerHttpTests(unittest.TestCase):
    def test_remote_job_downloads_hash_checked_frames_and_returns_asset(self):
        temp_root = Path(__file__).resolve().parents[1] / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        session_id = "1791483072-1234abcd"
        images = {index: b"\xff\xd8\xff" + f"network-frame-{index}".encode() for index in range(10)}
        frames = []
        for index, image in images.items():
            frames.append({
                "image": f"images/{index:06d}.jpg",
                "image_sha256": __import__("hashlib").sha256(image).hexdigest(),
                "provenance": {"simulated": False, "replayed": False},
            })
        manifest = {
            "contract": "body_reconstruction_session.v1", "session_id": session_id,
            "state": "ready_for_review", "frame_count": len(frames), "frames": frames,
        }
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            capture_root = Path(directory) / "captures"
            args = remote_job.argparse.Namespace(
                token="worker-secret-" + "x" * 32, body_url="https://body.local",
                session_id=session_id, ca_cert=None, capture_root=str(capture_root),
                work_dir=None, iterations=1000, device="cuda", ns_process_data="ns-process-data",
                ns_train="ns-train", ns_export="export_gaussian_splat.py",
            )

            def fake_request(url, token, context, *, data=None, headers=None):
                if url.endswith("/" + session_id):
                    return json.dumps(manifest).encode(), "application/json"
                index = int(url.rsplit("/", 1)[-1].split(".", 1)[0])
                return images[index], "image/jpeg"

            def fake_reconstruct(_args):
                asset_dir = capture_root / session_id / "assets" / "current"
                asset_dir.mkdir(parents=True)
                asset = asset_dir / "scene.ply"
                asset.write_bytes(GAUSSIAN_PLY)
                digest = __import__("hashlib").sha256(GAUSSIAN_PLY).hexdigest()
                asset_manifest = {
                    "contract": "body_gaussian_asset.v1", "asset_id": session_id + "-splatfacto",
                    "file": "scene.ply", "format": "ply", "sha256": digest,
                }
                provenance = {
                    "capture_contract": "body_reconstruction_session.v1", "session_id": session_id,
                    "source": "real_body_camera_capture", "frame_count": 10,
                    "simulated_or_replayed": False,
                }
                (asset_dir / "manifest.json").write_text(json.dumps(asset_manifest), encoding="utf-8")
                (asset_dir / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
                return asset

            published = {"ok": True, "asset": {"available": True, "asset_id": session_id + "-splatfacto"}}
            response = MagicMock()
            response.__enter__.return_value = response
            response.read.return_value = json.dumps(published).encode()
            with patch.object(remote_job, "_request", side_effect=fake_request), \
                    patch.object(remote_job.reconstruction, "run", side_effect=fake_reconstruct), \
                    patch.object(remote_job, "urlopen", return_value=response) as upload:
                result = remote_job.run(args)
            self.assertTrue(result["ok"])
            self.assertEqual(result["asset"]["asset_id"], session_id + "-splatfacto")
            request = upload.call_args.args[0]
            self.assertEqual(request.full_url, "https://body.local/worldmodel/reconstruction/worker/assets")
            self.assertEqual((capture_root / session_id / "images/000009.jpg").read_bytes(), images[9])

    def test_worker_routes_require_token_and_stream_only_manifest_images(self):
        temp_root = Path(__file__).resolve().parents[1] / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            original_config = brt.CONFIG_PATH
            original_load_dotenv = brt._load_dotenv
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
            brt.CONFIG_PATH = Path(directory) / "config.json"
            brt.CONFIG_PATH.write_text(json.dumps({
                "BODY_HOST": "127.0.0.1", "BODY_PORT": port,
                "BODY_RECONSTRUCTION_WORKER_TOKEN": "worker-secret-" + "x" * 32,
            }), encoding="utf-8")
            brt._load_dotenv = lambda: None
            host = brt.BodyHost()
            host._reconstruction_capture = ReconstructionCaptureStore(Path(directory) / "captures")
            session = host._reconstruction_capture.create("http fixture")
            session_id = session["session_id"]
            image = b"\xff\xd8\xffhttp-frame"
            import base64 as _base64
            host._reconstruction_capture.capture(session_id, {
                "camera": {"image_base64": _base64.b64encode(image).decode(), "width": 4, "height": 3},
            })
            host._reconstruction_capture.close(session_id)
            try:
                host._start_http_endpoint()
                base = f"http://127.0.0.1:{port}/worldmodel/reconstruction/worker/sessions/{session_id}"
                with self.assertRaises(HTTPError) as denied:
                    urlopen(base, timeout=3)
                self.assertEqual(denied.exception.code, 401)

                headers = {"Authorization": f"Bearer {host.config['BODY_RECONSTRUCTION_WORKER_TOKEN']}"}
                with urlopen(Request(base, headers=headers), timeout=3) as response:
                    manifest = json.loads(response.read())
                self.assertEqual(manifest["contract"], "body_reconstruction_session.v1")
                image_url = f"{base}/images/000000.jpg"
                with urlopen(Request(image_url, headers=headers), timeout=3) as response:
                    self.assertEqual(response.headers.get_content_type(), "image/jpeg")
                    self.assertEqual(response.read(), image)
            finally:
                host.stop_event.set()
                if host.http_server is not None:
                    host.http_server.shutdown()
                    host.http_server.server_close()
                brt.CONFIG_PATH = original_config
                brt._load_dotenv = original_load_dotenv


if __name__ == "__main__":
    unittest.main()
