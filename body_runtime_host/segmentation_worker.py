"""Persistent Qualcomm QNN semantic-segmentation worker using JSON lines."""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time

import numpy as np


def _prepare_input(image_rgb: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    import cv2

    if len(shape) != 4 or shape[0] != 1:
        raise RuntimeError(f"unsupported segmentation input shape: {shape}")
    if shape[-1] == 3:
        height, width = shape[1:3]
        channels_last = True
    elif shape[1] == 3:
        height, width = shape[2:4]
        channels_last = False
    else:
        raise RuntimeError(f"unsupported segmentation input layout: {shape}")
    resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_LINEAR)
    tensor = resized.astype(np.float32) / 255.0
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    tensor = (tensor - mean) / std
    if not channels_last:
        tensor = tensor.transpose(2, 0, 1)
    return tensor[None, ...]


def _load_model(path: str, runtime_preference: str):
    from qai_appbuilder import LogLevel, QNNConfig, QNNContext, Runtime

    if not os.path.isfile(path):
        raise RuntimeError(f"SegFormer DLC not found: {path}")
    runtimes = [Runtime.HTP, Runtime.CPU] if runtime_preference == "htp_auto" else [
        Runtime.HTP if runtime_preference == "htp" else Runtime.CPU
    ]
    errors = []
    for runtime in runtimes:
        try:
            QNNConfig.Config(runtime=runtime, log_level=LogLevel.ERROR)
            model = QNNContext(model_name="body_segmentation", model_path=path)
            inputs = model.getInputShapes()
            if not inputs:
                raise RuntimeError("SegFormer reports no input tensor")
            selected = "htp" if runtime == Runtime.HTP else "cpu"
            return model, tuple(int(value) for value in inputs[0]), selected
        except Exception as exc:
            errors.append(f"{runtime}: {str(exc)[:160]}")
    raise RuntimeError("; ".join(errors))


def _decode_logits(
    outputs: object,
    class_count: int,
    target_size: tuple[int, int] | None = None,
) -> np.ndarray:
    return _decode_logits_with_confidence(outputs, class_count, target_size)[0]


def _decode_logits_with_confidence(
    outputs: object,
    class_count: int,
    target_size: tuple[int, int] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if isinstance(outputs, (list, tuple)):
        if not outputs:
            raise RuntimeError("SegFormer returned no outputs")
        outputs = outputs[0]
    logits = np.asarray(outputs, dtype=np.float32)
    logits = np.squeeze(logits)
    if logits.ndim != 3:
        raise RuntimeError(f"unsupported SegFormer output shape: {np.shape(outputs)}")
    if logits.shape[0] == class_count:
        class_first = logits
    elif logits.shape[-1] == class_count:
        class_first = logits.transpose(2, 0, 1)
    else:
        raise RuntimeError(f"no {class_count}-class axis in SegFormer output: {logits.shape}")
    if not np.isfinite(class_first).any():
        raise RuntimeError("SegFormer output contains no finite logits")
    class_first = np.nan_to_num(class_first, copy=False)
    native_max = np.max(class_first, axis=0)
    normalizer = np.zeros_like(native_max)
    for scores in class_first:
        normalizer += np.exp(scores - native_max)
    confidence = 1.0 / np.maximum(normalizer, np.finfo(np.float32).tiny)
    if target_size is None or class_first.shape[1:] == (target_size[1], target_size[0]):
        return class_first.argmax(axis=0).astype(np.uint8), confidence

    import cv2

    # Upscale each score plane before argmax so boundaries are interpolated
    # without allocating a full-resolution tensor for every semantic class.
    width, height = target_size
    mask = np.zeros((height, width), dtype=np.uint8)
    best_score = np.full((height, width), -np.inf, dtype=np.float32)
    for class_id, scores in enumerate(class_first):
        resized = cv2.resize(scores, (width, height), interpolation=cv2.INTER_LINEAR)
        np.copyto(mask, np.uint8(class_id), where=resized > best_score)
        np.maximum(best_score, resized, out=best_score)
    confidence = cv2.resize(confidence, (width, height), interpolation=cv2.INTER_LINEAR)
    return mask, np.clip(confidence, 0.0, 1.0)


def _summarize(
    mask: np.ndarray,
    labels: dict[str, str],
    confidence: np.ndarray | None = None,
) -> list[dict[str, object]]:
    valid = confidence > 0.35 if confidence is not None else np.ones(mask.shape, dtype=bool)
    ids, counts = np.unique(mask[valid], return_counts=True)
    total = max(1, int(valid.sum()))
    ranked = sorted(zip(ids.tolist(), counts.tolist()), key=lambda row: row[1], reverse=True)[:8]
    return [
        {"id": int(class_id), "label": labels.get(str(class_id), f"class_{class_id}"),
         "ratio": round(count / total, 4)}
        for class_id, count in ranked
    ]


def _run_inference(model, tensor, image_rgb, model_path, runtime_preference, input_shape, actual_runtime):
    try:
        return model.Inference([tensor]), model, input_shape, actual_runtime
    except Exception:
        if runtime_preference != "htp_auto" or actual_runtime != "htp":
            raise
        model, input_shape, actual_runtime = _load_model(model_path, "cpu")
        tensor = _prepare_input(image_rgb, input_shape)
        return model.Inference([tensor]), model, input_shape, actual_runtime


def main() -> None:
    import cv2

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--runtime", choices=("htp_auto", "htp", "cpu"), default="htp_auto")
    args = parser.parse_args()
    with open(args.taxonomy, encoding="utf-8") as handle:
        taxonomy = json.load(handle)
    labels = {str(index): str(label) for index, label in taxonomy["output_labels"].items()}
    class_count = len(labels)
    protocol_out = os.fdopen(os.dup(sys.stdout.fileno()), "w", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    model, input_shape, actual_runtime = _load_model(args.model, args.runtime)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            started = time.monotonic()
            raw = base64.b64decode(request["image_base64"], validate=True)
            image_bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image_bgr is None:
                raise RuntimeError("camera JPEG could not be decoded")
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            tensor = _prepare_input(image_rgb, input_shape)
            inference_started = time.monotonic()
            output, model, input_shape, actual_runtime = _run_inference(
                model, tensor, image_rgb, args.model, args.runtime, input_shape, actual_runtime,
            )
            inference_ms = (time.monotonic() - inference_started) * 1000.0
            mask, confidence = _decode_logits_with_confidence(
                output, class_count, (image_rgb.shape[1], image_rgb.shape[0]),
            )
            rgba_mask = np.zeros((*mask.shape, 4), dtype=np.uint8)
            rgba_mask[:, :, 0] = mask
            rgba_mask[:, :, 3] = np.clip((confidence - 0.35) * (255 / 0.4), 0, 255).astype(np.uint8)
            ok, encoded = cv2.imencode(".png", rgba_mask, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
            if not ok:
                raise RuntimeError("could not encode semantic class mask")
            protocol_out.write(json.dumps({
                "ok": True, "runtime": actual_runtime, "inference_ms": round(inference_ms, 1),
                "latency_ms": round((time.monotonic() - started) * 1000.0, 1),
                "frame_id": request.get("frame_id"), "captured_at": request.get("captured_at"),
                "width": int(image_rgb.shape[1]), "height": int(image_rgb.shape[0]),
                "mask_png_base64": base64.b64encode(encoded.tobytes()).decode("ascii"),
                "classes": _summarize(mask, labels, confidence),
            }, separators=(",", ":")) + "\n")
        except Exception as exc:
            protocol_out.write(json.dumps({"ok": False, "error": str(exc)[:300]}, separators=(",", ":")) + "\n")
        protocol_out.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.__stdout__.write(json.dumps({"ok": False, "error": str(exc)[:300]}) + "\n")
        sys.__stdout__.flush()
