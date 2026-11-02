import base64
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np

from body_runtime_host.runtime import BodyHost


class CameraMetricDistanceDiagnosticTests(unittest.TestCase):
    def test_same_frame_tv_distance_diagnostic_is_logged(self):
        now = time.time()
        raw = np.full((480, 640), 20000, dtype=np.uint16)
        person_box = (270, 100, 370, 450)
        tv_box = (400, 100, 600, 400)
        raw[person_box[1]:person_box[3], person_box[0]:person_box[2]] = 10000
        raw[tv_box[1]:tv_box[3], tv_box[0]:tv_box[2]] = 15000
        ok, encoded = cv2.imencode(".png", raw)
        self.assertTrue(ok)
        raw_png = base64.b64encode(encoded.tobytes()).decode("ascii")

        detections = [
            {"label": "person", "confidence": 0.9, "bbox": list(person_box)},
            {"label": "tv", "confidence": 0.8, "bbox": list(tv_box)},
        ]
        yolo = {"state": "ready", "frame_id": "yolo-frame-1", "captured_at": now,
                "detections": detections}
        radar_payload = {
            "timestamp": now, "source": "hlk_ld2450_ventuno_bridge",
            "targets": [{"target_id": 1, "position_m": [0.0, 1.8], "confidence": 0.9}],
        }
        radar_frame = SimpleNamespace(as_dict=lambda: radar_payload)

        host = BodyHost.__new__(BodyHost)
        host.camera_yolo_status = Mock(return_value=yolo)
        host.midas_metric_calibration = Mock(return_value={
            "available": True,
            "inverse_scale_per_relative_unit": 0.00004,
            "inverse_offset_per_m": 0.0001,
            "calibrated_range_m": [1.0, 3.0],
            "calibrated_relative_range": [1.0, 65535.0],
            "holdout_rmse_m": 0.2,
        })
        host._midas_service = SimpleNamespace(
            request_raw_output=Mock(),
            status=Mock(return_value={"depth_raw_png_base64": raw_png,
                                     "captured_at": now, "frame_id": "depth-frame-1"}),
        )
        host._yolox_service = SimpleNamespace(
            nearest_detection_result=Mock(return_value=yolo),
        )
        host._worldmodel = SimpleNamespace(source=SimpleNamespace(radar=SimpleNamespace(
            last_frame=radar_frame, last_ok=now,
        )))
        host.value = lambda _key, default=None: default
        host._camera_metric_cache_lock = threading.Lock()
        host._camera_metric_diagnostic_last_frame_id = None
        host._camera_metric_diagnostic_last_recorded_monotonic = 0.0
        records = []
        host.append_midas_calibration_trace = lambda payload: records.extend(payload["records"])

        result = host.camera_metric_yolo_status()

        diagnostic = result["metric_depth"]["distance_diagnostic"]
        self.assertIsNotNone(diagnostic, result)
        self.assertEqual(diagnostic["frame_id"], "yolo-frame-1")
        self.assertEqual(diagnostic["depth_frame_id"], "depth-frame-1")
        self.assertAlmostEqual(diagnostic["person_anchor"]["radar_forward_m"], 1.8)
        self.assertAlmostEqual(diagnostic["person_anchor"]["calibrated_forward_before_anchor_m"], 2.4994, places=3)
        self.assertAlmostEqual(diagnostic["person_anchor"]["scale_factor_diagnostic_only"], 0.7202, places=3)
        self.assertAlmostEqual(diagnostic["target"]["calibrated_forward_m"], 1.6664, places=3)
        self.assertFalse(diagnostic["target"]["radar_scale_applied_to_target"])
        tv_metric = result["detections"][1]["metric_depth"]
        self.assertAlmostEqual(tv_metric["forward_m"], 1.6664, places=3)
        self.assertEqual(tv_metric["source"], "paired_yolox_box_midas_calibrated")
        self.assertFalse(tv_metric["radar_track_associated"])
        person_metric = result["detections"][0]["metric_depth"]
        self.assertAlmostEqual(person_metric["forward_m"], 1.8, places=3)
        self.assertTrue(person_metric["radar_track_associated"])
        regions = diagnostic["target"]["midas_regions"]
        self.assertGreater(regions["bbox_raw_excluding_person"]["count"], 0)
        self.assertGreater(regions["surrounding_ring_raw_excluding_person"]["count"], 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["type"], "metric_distance_diagnostic")

        # TV diagnostics must also be produced and persisted when no fresh
        # radar/person association exists; those are the frames used by Lumina.
        radar_payload["timestamp"] = now - 0.5
        yolo["frame_id"] = "yolo-frame-2"
        host._camera_metric_diagnostic_last_frame_id = None
        host._camera_metric_diagnostic_last_recorded_monotonic = time.monotonic() - 2.0
        unanchored = host.camera_metric_yolo_status()
        unanchored_diag = unanchored["metric_depth"]["distance_diagnostic"]
        self.assertFalse(unanchored_diag["radar_person_match_available"])
        self.assertIsNone(unanchored_diag["person_anchor"])
        self.assertGreater(unanchored_diag["target"]["midas_regions"]["surrounding_ring_raw_excluding_person"]["count"], 0)
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
