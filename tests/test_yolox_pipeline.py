import unittest
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from body_runtime_host.yolox_worker import _decode_outputs
from body_runtime_host.yolox_service import YoloXService


class YoloXPipelineTests(unittest.TestCase):
    def test_vr_camera_keeps_live_frames_and_holds_recent_yolox_boxes(self):
        source = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "quest_vr.js").read_text()

        self.assertIn("await vrDashboard.setCameraFrame(frame, displayDetections)", source)
        self.assertIn("detectionAge <= 2.5", source)
        self.assertNotIn("/body/camera/yolo-frame?frame_id=", source)

    def test_decodes_candidates_and_maps_boxes_back_from_letterbox(self):
        rows = np.zeros((2, 85), dtype=np.float32)
        rows[0, :5] = [320, 320, 100, 100, 0.9]
        rows[0, 5] = 0.9
        rows[1, :5] = [321, 320, 100, 100, 0.8]
        rows[1, 5] = 0.8

        detections, ambiguous = _decode_outputs(
            [rows], 0.25, (640, 640), (640, 480), (0, 80), 1.0, 0.12
        )

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["label"], "person")
        self.assertAlmostEqual(detections[0]["bbox"][0], 270 / 640, places=3)
        self.assertAlmostEqual(detections[0]["bbox"][1], 190 / 480, places=3)
        self.assertFalse(ambiguous)

    def test_close_top_class_scores_request_vlm_fallback(self):
        rows = np.zeros((1, 85), dtype=np.float32)
        rows[0, :5] = [320, 320, 100, 100, 0.9]
        rows[0, 5] = 0.8
        rows[0, 6] = 0.76

        detections, ambiguous = _decode_outputs(
            [rows], 0.25, (640, 640), (640, 480), (0, 80), 1.0, 0.12
        )

        self.assertTrue(detections)
        self.assertTrue(ambiguous)
        self.assertEqual(detections[0]["alternatives"], [0.72, 0.684])

    def test_empty_postprocessed_output_is_no_detection_not_runtime_error(self):
        detections, ambiguous = _decode_outputs(
            [np.empty((0, 4)), np.empty((0,)), np.empty((0,), dtype=np.uint8)],
            0.25, (640, 640), (640, 480), (0, 80), 1.0,
        )

        self.assertEqual(detections, [])
        self.assertTrue(ambiguous)

    def test_quantized_ai_hub_split_outputs_are_decoded(self):
        detections, ambiguous = _decode_outputs(
            [np.array([[[270, 190, 370, 290]]]), np.array([[0.91]]), np.array([[0]], dtype=np.uint8)],
            0.25, (640, 640), (640, 480), (0, 80), 1.0,
        )

        self.assertEqual(detections[0]["label"], "person")
        self.assertEqual(detections[0]["bbox"], [0.42188, 0.22917, 0.57812, 0.4375])
        self.assertFalse(ambiguous)

    def test_ai_hub_dlc_class_ids_scores_boxes_output_order(self):
        classes = np.array([[0, 73, 56, 79, 3]], dtype=np.float32)
        boxes = np.array([[[20, 30, 80, 100], [120, 30, 180, 100],
                           [220, 30, 280, 100], [320, 30, 380, 100],
                           [420, 30, 480, 100]]], dtype=np.float32)
        scores = np.array([[0.83, 0.71, 0.19, 0.62, 0.10]], dtype=np.float32)

        detections, _ = _decode_outputs(
            [classes, boxes, scores], 0.25, (640, 640), (640, 480), (0, 80), 1.0,
        )

        self.assertEqual([item["class_id"] for item in detections], [0, 73, 79])
        self.assertEqual([item["label"] for item in detections], ["person", "book", "toothbrush"])
        self.assertEqual([item["confidence"] for item in detections], [0.83, 0.71, 0.62])

    def test_yolox_retains_recent_analyzed_frames_for_exact_lookup(self):
        service = YoloXService(lambda _key, default: default, lambda: {})
        service._analyzed_frames.update({
            f"frame-{index}": {"frame_id": f"frame-{index}", "image_base64": str(index)}
            for index in range(4)
        })

        self.assertEqual(service.analyzed_frame("frame-1")["image_base64"], "1")
        self.assertEqual(service.analyzed_frame()["frame_id"], "frame-3")
        self.assertIsNone(service.analyzed_frame("missing"))

    def test_worker_adds_ventuno_cdsp_runtime_search_path(self):
        service = YoloXService(lambda key, default: {
            "BODY_YOLO_PYTHON": "/fake/python",
            "BODY_YOLO_MODEL_PATH": "/fake/yolox.dlc",
            "BODY_YOLO_RUNTIME": "htp",
        }.get(key, default), lambda: {})
        with patch("body_runtime_host.yolox_service.os.path.isfile", return_value=True), \
             patch("body_runtime_host.yolox_service.subprocess.Popen") as popen:
            service._worker()

        env = popen.call_args.kwargs["env"]
        paths = env["ADSP_LIBRARY_PATH"].split(";")
        self.assertEqual([path.replace("\\", "/") for path in paths[:3]], [
            str(Path.home() / ".local" / "share" / "pandorabox" / "yolox-dsp").replace("\\", "/"),
            "/usr/lib/dsp/cdsp",
            "/usr/lib/rfsa/adsp",
        ])

    def test_yolox_installer_installs_system_qairt_and_v75_skeleton(self):
        installer = Path("install_body_yolox.sh").read_text(encoding="utf-8")
        self.assertIn("qairt-libs qairt-dsp-binaries", installer)
        self.assertIn("/usr/lib/dsp/cdsp/libQnnHtpV75Skel.so", installer)
        self.assertIn("libQnnHtpV75Skel.so.2", installer)
        self.assertIn("ADSP_LIBRARY_PATH", Path("body_runtime_host/yolox_service.py").read_text(encoding="utf-8"))
        self.assertIn("yolox-dsp", installer)
        self.assertNotIn("sudo ln -sfn", installer)

    def test_geniex_skeleton_is_restored_without_changing_yolox_runtime(self):
        setup = Path("configure_geniex_qairt.sh").read_text(encoding="utf-8")
        self.assertIn("geniex/qairt/htp-files", setup)
        self.assertIn("libQnnHtpV75Skel.so.2", setup)
        self.assertIn("yolox-infer/", setup)
        self.assertIn("yolox-dsp", Path("body_runtime_host/yolox_service.py").read_text(encoding="utf-8"))
        self.assertIn("systemctl --user restart geniex.service", setup)

    def test_percentage_scores_are_normalized_to_probability(self):
        rows = np.zeros((1, 85), dtype=np.float32)
        rows[0, :5] = [320, 320, 100, 100, 90]
        rows[0, 5] = 79

        detections, _ = _decode_outputs(
            [rows], 0.25, (640, 640), (640, 480), (0, 80), 1.0,
        )

        self.assertAlmostEqual(detections[0]["confidence"], 0.711, places=3)

    def test_dashboard_has_overlay_and_camera_settings_are_persisted(self):
        from body_runtime_host.body_gui import BODY_GUI_HTML
        from pathlib import Path

        dashboard = Path("body_runtime_host/quest_vr_dashboard.js").read_text(encoding="utf-8")
        quest = Path("body_runtime_host/quest_vr.js").read_text(encoding="utf-8")
        self.assertIn("yolox_enabled", BODY_GUI_HTML)
        self.assertIn("BODY_YOLO_ENABLED", Path("body_runtime_host/worldmodel/core.py").read_text(encoding="utf-8"))
        self.assertIn("strokeRect", dashboard)
        self.assertIn("const displaySource = source", dashboard)
        self.assertIn("fresh && Array.isArray(yolo.detections)", dashboard)
        self.assertIn("result.yolo || {}", quest)

    def test_2d_hud_preview_refreshes_live_video_and_holds_recent_boxes(self):
        preview_html = Path("body_runtime_host/quest_hud_preview.html").read_text(encoding="utf-8")
        preview_script = Path("body_runtime_host/quest_hud_preview.js").read_text(encoding="utf-8")
        self.assertIn('id="camera-yolo-overlay"', preview_html)
        self.assertIn("const yolo = result.yolo || {}", preview_script)
        self.assertIn("const displayFrame = {", preview_script)
        self.assertIn("const detections = fresh && Array.isArray(yolo.detections)", preview_script)
        self.assertNotIn("/body/camera/yolo-frame?frame_id=", preview_script)
        self.assertIn("setInterval(pollCamera, 150)", preview_script)
        self.assertIn("drawCameraYoloOverlay(displayFrame, detections)", preview_script)

    def test_camera_yolox_settings_are_written_to_body_config(self):
        from body_runtime_host.runtime import BodyHost

        config_path = Path(".tmp") / "yolox-persistence-test.json"
        config_path.parent.mkdir(exist_ok=True)
        config_path.unlink(missing_ok=True)
        try:
            with patch("body_runtime_host.runtime.CONFIG_PATH", config_path):
                host = BodyHost()
                host._configure_local_camera = lambda start=None: {"status": "stopped"}
                host._yolox_service.reconfigure = lambda: None
                host._midas_service.reconfigure = lambda: None
                host.update_camera_settings({
                    "yolox_enabled": True,
                    "yolox_runtime": "cpu",
                    "yolox_confidence": 0.42,
                    "yolox_vlm_fallback": False,
                    "midas_enabled": True,
                    "midas_interval_s": 3.5,
                })
                saved = json.loads(config_path.read_text(encoding="utf-8"))
                self.assertTrue(saved["BODY_YOLO_ENABLED"])
                self.assertEqual(saved["BODY_YOLO_RUNTIME"], "cpu")
                self.assertEqual(saved["BODY_YOLO_CONFIDENCE"], 0.42)
                self.assertFalse(saved["BODY_YOLO_VLM_FALLBACK"])
                self.assertTrue(saved["BODY_MIDAS_ENABLED"])
                self.assertEqual(saved["BODY_MIDAS_INTERVAL_S"], 3.5)
        finally:
            config_path.unlink(missing_ok=True)

    def test_midas_is_optional_and_requirements_are_declared_for_body_install(self):
        from body_runtime_host.midas_service import MiDaSDepthService

        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_INTERVAL_S": 2.0}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})
        service.start()
        self.assertEqual(service.status()["state"], "disabled")
        requirements = Path("body_requirements.txt").read_text(encoding="utf-8")
        installer = Path("start_body.sh").read_text(encoding="utf-8")
        self.assertIn("timm>=", requirements)
        self.assertNotIn("torch, timm", installer)


if __name__ == "__main__":
    unittest.main()
