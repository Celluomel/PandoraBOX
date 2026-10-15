import unittest
from unittest.mock import patch

import numpy as np

from body_runtime_host.segmentation_service import SemanticSegmentationService
from body_runtime_host.segmentation_worker import _decode_logits, _decode_logits_with_confidence, _run_inference, _summarize


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

    def test_confidence_uses_pixelwise_softmax_and_filters_uncertain_summary_classes(self):
        logits = np.zeros((1, 3, 2, 2), dtype=np.float32)
        logits[0, 1, 0, 0] = 5
        mask, confidence = _decode_logits_with_confidence(logits, 3)
        self.assertEqual(mask[0, 0], 1)
        self.assertGreater(confidence[0, 0], 0.9)
        self.assertLess(confidence[0, 1], 0.4)
        classes = _summarize(mask, {"0": "wall", "1": "person"}, confidence)
        self.assertEqual(classes, [{"id": 1, "label": "person", "ratio": 1.0}])

    def test_resizes_class_scores_before_selecting_full_resolution_labels(self):
        class FakeCv2:
            INTER_LINEAR = 1

            @staticmethod
            def resize(scores, size, interpolation):
                self.assertEqual(interpolation, FakeCv2.INTER_LINEAR)
                width, height = size
                return np.repeat(np.repeat(scores, height // scores.shape[0], axis=0),
                                 width // scores.shape[1], axis=1)

        logits = np.zeros((1, 2, 2, 2), dtype=np.float32)
        logits[0, 0, :, 0] = 2
        logits[0, 1, :, 1] = 2
        with patch.dict("sys.modules", {"cv2": FakeCv2}):
            mask = _decode_logits(logits, 2, target_size=(8, 4))
        self.assertEqual(mask.shape, (4, 8))
        self.assertTrue(np.all(mask[:, :4] == 0))
        self.assertTrue(np.all(mask[:, 4:] == 1))
        self.assertEqual(set(np.unique(mask)), {0, 1})

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
