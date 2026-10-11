import unittest
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from body_runtime_host.yolox_worker import _decode_outputs


class YoloXPipelineTests(unittest.TestCase):
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
        self.assertIn("cameraSourceFrames", dashboard)
        self.assertIn("cameraDetectionFrameId", dashboard)
        self.assertIn("result.yolo || {}", quest)

    def test_2d_hud_preview_overlays_boxes_on_the_matching_camera_frame(self):
        preview_html = Path("body_runtime_host/quest_hud_preview.html").read_text(encoding="utf-8")
        preview_script = Path("body_runtime_host/quest_hud_preview.js").read_text(encoding="utf-8")
        self.assertIn('id="camera-yolo-overlay"', preview_html)
        self.assertIn("const yolo = result.yolo || {}", preview_script)
        self.assertIn("cameraFrames.get(detectionId)", preview_script)
        self.assertIn("/body/camera/yolo-frame?frame_id=", preview_script)
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
                host.update_camera_settings({
                    "yolox_enabled": True,
                    "yolox_runtime": "cpu",
                    "yolox_confidence": 0.42,
                    "yolox_vlm_fallback": False,
                })
                saved = json.loads(config_path.read_text(encoding="utf-8"))
                self.assertTrue(saved["BODY_YOLO_ENABLED"])
                self.assertEqual(saved["BODY_YOLO_RUNTIME"], "cpu")
                self.assertEqual(saved["BODY_YOLO_CONFIDENCE"], 0.42)
                self.assertFalse(saved["BODY_YOLO_VLM_FALLBACK"])
        finally:
            config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
