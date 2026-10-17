"""Persistent Qualcomm QNN MiDaS worker; reads and writes JSON lines."""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time

import numpy as np


def _prepare_input(image_rgb: np.ndarray, shape: tuple[int, ...]) -> tuple[np.ndarray, float, tuple[int, int]]:
    import cv2

    if len(shape) != 4 or shape[0] != 1:
        raise RuntimeError(f"unsupported MiDaS input shape: {shape}")
    channels_last = shape[-1] == 3
    if channels_last:
        height, width = shape[1:3]
    elif shape[1] == 3:
        height, width = shape[2:4]
    else:
        raise RuntimeError(f"unsupported MiDaS input layout: {shape}")
    original_h, original_w = image_rgb.shape[:2]
    scale = min(width / original_w, height / original_h)
    resized_w = max(1, int(original_w * scale))
    resized_h = max(1, int(original_h * scale))
    resized = cv2.resize(image_rgb, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR)
    pad_x = (width - resized_w) // 2
    pad_y = (height - resized_h) // 2
    canvas = np.zeros((height, width, 3), dtype=np.float32)
    canvas[pad_y:pad_y + resized_h, pad_x:pad_x + resized_w] = resized.astype(np.float32) / 255.0
    tensor = canvas if channels_last else canvas.transpose(2, 0, 1)
    return tensor[None, ...], scale, (pad_x, pad_y)


def _restore_depth(output: np.ndarray, image_size: tuple[int, int], scale: float,
                   padding: tuple[int, int]) -> np.ndarray:
    import cv2

    depth = np.squeeze(np.asarray(output, dtype=np.float32))
    if depth.ndim != 2 or not np.isfinite(depth).any():
        raise RuntimeError(f"invalid MiDaS output shape or values: {np.shape(output)}")
    depth = np.nan_to_num(depth, copy=False)
    height, width = depth.shape
    pad_x, pad_y = padding
    content_w = max(1, min(width - pad_x, int(image_size[0] * scale)))
    content_h = max(1, min(height - pad_y, int(image_size[1] * scale)))
    depth = depth[pad_y:pad_y + content_h, pad_x:pad_x + content_w]
    return cv2.resize(depth, image_size, interpolation=cv2.INTER_LINEAR)


def _load_model(path: str, runtime_preference: str):
    from qai_appbuilder import LogLevel, QNNConfig, QNNContext, Runtime

    if not os.path.isfile(path):
        raise RuntimeError(f"MiDaS HTP DLC not found: {path}")
    runtimes = [Runtime.HTP, Runtime.CPU] if runtime_preference == "htp_auto" else [
        Runtime.HTP if runtime_preference == "htp" else Runtime.CPU
    ]
    errors = []
    for runtime in runtimes:
        try:
            QNNConfig.Config(runtime=runtime, log_level=LogLevel.ERROR)
            model = QNNContext(model_name="body_midas", model_path=path)
            input_shapes = model.getInputShapes()
            if not input_shapes:
                raise RuntimeError("MiDaS model reports no input tensor")
            actual_runtime = "htp" if runtime == Runtime.HTP else "cpu"
            return model, tuple(int(value) for value in input_shapes[0]), actual_runtime
        except Exception as exc:
            errors.append(f"{runtime}: {str(exc)[:180]}")
    raise RuntimeError("; ".join(errors))


def main() -> None:
    import cv2

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--runtime", choices=("htp_auto", "htp", "cpu"), default="htp_auto")
    args = parser.parse_args()
    protocol_out = os.fdopen(os.dup(sys.stdout.fileno()), "w", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    model, input_shape, actual_runtime = _load_model(args.model, args.runtime)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            total_started = time.monotonic()
            raw = base64.b64decode(request["image_base64"], validate=True)
            image_bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image_bgr is None:
                raise RuntimeError("camera JPEG could not be decoded")
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            tensor, scale, padding = _prepare_input(image_rgb, input_shape)
            inference_started = time.monotonic()
            try:
                output = model.Inference([tensor])
            except Exception:
                if args.runtime != "htp_auto" or actual_runtime != "htp":
                    raise
                model = None
                model, input_shape, actual_runtime = _load_model(args.model, "cpu")
                tensor, scale, padding = _prepare_input(image_rgb, input_shape)
                output = model.Inference([tensor])
            inference_ms = (time.monotonic() - inference_started) * 1000.0
            if isinstance(output, (list, tuple)):
                output = output[0]
            depth = _restore_depth(output, (image_rgb.shape[1], image_rgb.shape[0]), scale, padding)
            low, high = np.percentile(depth, (2, 98))
            normalized = np.clip((depth - low) / max(float(high - low), 1e-6), 0.0, 1.0)
            gray = np.asarray(normalized * 255.0, dtype=np.uint8)
            raw_low = float(np.min(depth))
            raw_high = float(np.max(depth))
            raw_span = max(raw_high - raw_low, 1e-12)
            raw_u16 = np.rint(np.clip((depth - raw_low) / raw_span, 0.0, 1.0) * 65535.0).astype(np.uint16)
            colored = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
            gray_ok, gray_encoded = cv2.imencode(".jpg", gray, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
            color_ok, color_encoded = cv2.imencode(".jpg", colored, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            raw_ok, raw_encoded = cv2.imencode(".png", raw_u16, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
            if not gray_ok or not color_ok or not raw_ok:
                raise RuntimeError("could not encode MiDaS depth output")
            protocol_out.write(json.dumps({
                "ok": True, "runtime": actual_runtime, "inference_ms": round(inference_ms, 1),
                "latency_ms": round((time.monotonic() - total_started) * 1000.0, 1),
                "frame_id": request.get("frame_id"), "captured_at": request.get("captured_at"),
                "width": int(image_rgb.shape[1]), "height": int(image_rgb.shape[0]),
                "depth_gray_jpeg_base64": base64.b64encode(gray_encoded.tobytes()).decode("ascii"),
                "depth_jpeg_base64": base64.b64encode(color_encoded.tobytes()).decode("ascii"),
                "depth_raw_png_base64": base64.b64encode(raw_encoded.tobytes()).decode("ascii"),
                "depth_raw_min": raw_low, "depth_raw_max": raw_high,
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
