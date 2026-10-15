import unittest
from unittest.mock import patch

import numpy as np

from body_runtime_host.segmentation_service import SemanticSegmentationService
from body_runtime_host.segmentation_worker import _decode_logits, _run_inference, _summarize


class SemanticSegmentationTests(unittest.TestCase):
    def test_service_is_disabled_by_default_and_prefers_htp_with_cpu_fallback(self):
        service = SemanticSegmentationService(lambda _key, default: default, lambda: {})
        settings = service.settings()
        self.assertFalse(settings["enabled"])
        self.assertEqual(settings["runtime"], "htp_auto")
        self.assertEqual(settings["state"], "disabled")

    def test_invalid_runtime_is_safely_normalized(self):
        service = SemanticSegmentationService(
            lambda key, default: "cuda" if key == "BODY_SEGMENTATION_RUNTIME" else default,
            lambda: {},
        )
        self.assertEqual(service.settings()["runtime"], "htp_auto")

    def test_decodes_class_first_logits_and_summarizes_labels(self):
        logits = np.zeros((1, 3, 2, 2), dtype=np.float32)
        logits[:, 2, :, 0] = 5
        logits[:, 1, 0, 1] = 4
        mask = _decode_logits([logits], 3)
        np.testing.assert_array_equal(mask, [[2, 1], [2, 0]])
        classes = _summarize(mask, {"1": "wall", "2": "floor"})
        self.assertEqual(classes[0]["label"], "floor")
        self.assertEqual(classes[0]["ratio"], 0.5)

    def test_decodes_class_last_logits(self):
        logits = np.zeros((2, 2, 3), dtype=np.float32)
        logits[..., 0] = 1
        logits[0, 1, 2] = 4
        mask = _decode_logits(logits, 3)
        np.testing.assert_array_equal(mask, [[0, 2], [0, 0]])

    def test_inference_failure_on_htp_reloads_cpu_only_in_auto_mode(self):
        class FailingHtp:
            def Inference(self, _inputs):
                raise RuntimeError("HTP unavailable")

        class CpuModel:
            def Inference(self, inputs):
                return inputs[0]

        cpu_model = CpuModel()
        image = np.zeros((8, 8, 3), dtype=np.uint8)
        tensor = np.zeros((1, 3, 4, 4), dtype=np.float32)
        with patch("body_runtime_host.segmentation_worker._load_model", return_value=(cpu_model, (1, 3, 4, 4), "cpu")) as load:
            with patch("body_runtime_host.segmentation_worker._prepare_input", return_value=tensor):
                output, model, shape, runtime = _run_inference(
                    FailingHtp(), tensor, image, "model.dlc", "htp_auto", (1, 3, 4, 4), "htp",
                )
        load.assert_called_once_with("model.dlc", "cpu")
        self.assertIs(model, cpu_model)
        self.assertEqual(shape, (1, 3, 4, 4))
        self.assertEqual(runtime, "cpu")
        self.assertEqual(output.shape, tensor.shape)

    def test_htp_only_mode_does_not_silently_fall_back(self):
        class FailingHtp:
            def Inference(self, _inputs):
                raise RuntimeError("HTP unavailable")

        with self.assertRaisesRegex(RuntimeError, "HTP unavailable"):
            _run_inference(
                FailingHtp(), np.zeros((1, 1)), np.zeros((1, 1, 3)),
                "model.dlc", "htp", (1, 1), "htp",
            )


if __name__ == "__main__":
    unittest.main()
