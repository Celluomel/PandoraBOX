"""Persistent Qualcomm QNN YOLOX worker; speaks one JSON request per line."""
from __future__ import annotations

import argparse
import base64
import gc
import json
import os
import sys
import time

import cv2
import numpy as np

COCO = (
    "person,bicycle,car,motorcycle,airplane,bus,train,truck,boat,traffic light,fire hydrant,"
    "stop sign,parking meter,bench,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe,"
    "backpack,umbrella,handbag,tie,suitcase,frisbee,skis,snowboard,sports ball,kite,baseball bat,"
    "baseball glove,skateboard,surfboard,tennis racket,bottle,wine glass,cup,fork,knife,spoon,bowl,"
    "banana,apple,sandwich,orange,broccoli,carrot,hot dog,pizza,donut,cake,chair,couch,potted plant,"
    "bed,dining table,toilet,tv,laptop,mouse,remote,keyboard,cell phone,microwave,oven,toaster,sink,"
    "refrigerator,book,clock,vase,scissors,teddy bear,hair drier,toothbrush"
).split(",")


def _nms(boxes, scores, threshold=0.45, limit=40):
    order = np.argsort(scores)[::-1]
    kept = []
    while len(order) and len(kept) < limit:
        index = int(order[0])
        kept.append(index)
        if len(order) == 1:
            break
        rest = order[1:]
        x1 = np.maximum(boxes[index, 0], boxes[rest, 0])
        y1 = np.maximum(boxes[index, 1], boxes[rest, 1])
        x2 = np.minimum(boxes[index, 2], boxes[rest, 2])
        y2 = np.minimum(boxes[index, 3], boxes[rest, 3])
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        area = np.maximum(0, boxes[:, 2] - boxes[:, 0]) * np.maximum(0, boxes[:, 3] - boxes[:, 1])
        iou = intersection / np.maximum(1e-8, area[index] + area[rest] - intersection)
        order = rest[iou <= threshold]
    return kept


def _decode_outputs(outputs, confidence, input_size, original_size, pad, scale, ambiguity_margin=0.12):
    arrays = [np.asarray(item).astype(np.float32, copy=False) for item in outputs]
    arrays = [np.squeeze(item, axis=0) if item.ndim >= 3 and item.shape[0] == 1 else item for item in arrays]
    detections = []
    ambiguous = False
    # AI Hub YOLO apps may expose already-decoded [boxes, class scores, ids].
    box_array = next((item for item in arrays if item.ndim == 2 and item.shape[-1] == 4), None)
    if box_array is not None and len(arrays) >= 2:
        remainder = [item for item in arrays if item is not box_array]
        score_matrix = next((item for item in remainder if item.ndim == 2 and item.shape[0] == len(box_array) and item.shape[1] > 1), None)
        score_array = next((item for item in remainder if item.ndim >= 1 and item.size == len(box_array)), None)
        class_array = next((item for item in remainder if item.ndim >= 1 and item.size == len(box_array) and item is not score_array), None)
        if score_matrix is not None:
            class_ids = np.argmax(score_matrix, axis=1)
            scores = np.max(score_matrix, axis=1)
            if scores.size and float(np.nanmax(scores)) > 1.0:
                scores = scores / 100.0
            for box, score, cls in zip(box_array, scores, class_ids):
                if score >= confidence:
                    detections.append((box.astype(float), float(score), int(cls), []))
        elif score_array is not None:
            scores = score_array.reshape(-1)
            if scores.size and float(np.nanmax(scores)) > 1.0:
                scores = scores / 100.0
            classes = class_array.reshape(-1).astype(int) if class_array is not None else np.zeros(len(scores), dtype=int)
            for box, score, cls in zip(box_array, scores, classes):
                if score >= confidence:
                    detections.append((box.astype(float), float(score), int(cls), []))
    if not detections and len(arrays) == 1:
        rows = arrays[0]
        if rows.ndim == 2 and rows.shape[0] in {85, 84} and rows.shape[1] > rows.shape[0]:
            rows = rows.T
        if rows.ndim == 2 and rows.shape[-1] >= 6:
            # Exported YOLOX detections use cx,cy,w,h,obj,classes; exports that
            # already decoded coordinates are also accepted in this layout.
            for row in rows:
                objectness = float(row[4])
                class_scores = row[5:]
                if objectness > 1.0:
                    objectness /= 100.0
                if class_scores.size and float(np.nanmax(class_scores)) > 1.0:
                    class_scores = class_scores / 100.0
                cls = int(np.argmax(class_scores)) if class_scores.size else 0
                score = objectness * float(class_scores[cls]) if class_scores.size else objectness
                if score < confidence:
                    continue
                cx, cy, width, height = (float(value) for value in row[:4])
                box = np.array([cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2])
                order = np.argsort(class_scores)[::-1][:2]
                alternatives = [float(class_scores[index] * objectness) for index in order]
                if len(alternatives) > 1 and alternatives[0] - alternatives[1] < ambiguity_margin:
                    ambiguous = True
                detections.append((box, score, cls, alternatives))
    if not detections:
        if box_array is not None and score_array is not None:
            return [], True
        if not arrays or not any(item.ndim == 2 and item.shape[-1] >= 6 for item in arrays):
            shapes = [list(item.shape) for item in arrays]
            raise RuntimeError(f"Unsupported YOLOX output tensors: {shapes}")
        return [], True

    boxes = np.stack([item[0] for item in detections]).astype(np.float32)
    scores = np.array([item[1] for item in detections], dtype=np.float32)
    kept = _nms(boxes, scores)
    input_w, input_h = input_size
    original_w, original_h = original_size
    pad_x, pad_y = pad
    output = []
    for index in kept:
        box, score, cls, alternatives = detections[index]
        x1 = np.clip((box[0] - pad_x) / scale / original_w, 0, 1)
        y1 = np.clip((box[1] - pad_y) / scale / original_h, 0, 1)
        x2 = np.clip((box[2] - pad_x) / scale / original_w, 0, 1)
        y2 = np.clip((box[3] - pad_y) / scale / original_h, 0, 1)
        if x2 <= x1 or y2 <= y1:
            continue
        label = COCO[cls] if 0 <= cls < len(COCO) else f"class_{cls}"
        output.append({"label": label, "class_id": cls, "confidence": round(score, 4),
                       "bbox": [round(float(x), 5) for x in (x1, y1, x2, y2)],
                       "alternatives": [round(float(value), 4) for value in alternatives[:2]]})
        ambiguous |= score < min(0.55, confidence + 0.2)
    return output, ambiguous


def _load_model(path, requested_runtime):
    from qai_appbuilder import QNNConfig, QNNContext, Runtime, LogLevel
    runtimes = [Runtime.HTP, Runtime.CPU] if requested_runtime == "htp_auto" else [
        Runtime.HTP if requested_runtime == "htp" else Runtime.CPU
    ]
    errors = []
    for runtime in runtimes:
        try:
            QNNConfig.Config(runtime=runtime, log_level=LogLevel.ERROR)
            model = QNNContext(model_name="body_yolox", model_path=path)
            return model, "htp" if runtime == Runtime.HTP else "cpu"
        except Exception as exc:
            errors.append(f"{runtime}: {str(exc)[:180]}")
    raise RuntimeError("; ".join(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--runtime", choices=("htp_auto", "htp", "cpu"), default="htp_auto")
    args = parser.parse_args()
    # Keep AppBuilder/QNN diagnostics out of the line-oriented JSON protocol.
    protocol_out = os.fdopen(os.dup(sys.stdout.fileno()), "w", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    model, actual_runtime = _load_model(args.model, args.runtime)
    try:
        input_shapes = model.getInputShapes()
    except Exception:
        if args.runtime != "htp_auto" or actual_runtime != "htp":
            raise
        model = None
        gc.collect()
        model, actual_runtime = _load_model(args.model, "cpu")
        input_shapes = model.getInputShapes()
    if not input_shapes and args.runtime == "htp_auto" and actual_runtime == "htp":
        model = None
        gc.collect()
        model, actual_runtime = _load_model(args.model, "cpu")
        input_shapes = model.getInputShapes()
    if not input_shapes:
        raise RuntimeError("YOLOX model reports no input tensor")
    shape = tuple(int(value) for value in input_shapes[0])
    for line in sys.stdin:
        try:
            request = json.loads(line)
            started = time.monotonic()
            raw = base64.b64decode(request["image_base64"], validate=True)
            image_bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image_bgr is None:
                raise RuntimeError("camera JPEG could not be decoded")
            image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            original_h, original_w = image.shape[:2]
            if len(shape) != 4:
                raise RuntimeError(f"unsupported model input shape: {shape}")
            channels_last = shape[-1] == 3
            net_h, net_w = (shape[1], shape[2]) if channels_last else (shape[2], shape[3])
            scale = min(net_w / original_w, net_h / original_h)
            resized = cv2.resize(image, (round(original_w * scale), round(original_h * scale)))
            canvas = np.full((net_h, net_w, 3), 114, dtype=np.uint8)
            pad_x, pad_y = (net_w - resized.shape[1]) // 2, (net_h - resized.shape[0]) // 2
            canvas[pad_y:pad_y + resized.shape[0], pad_x:pad_x + resized.shape[1]] = resized
            tensor = canvas.astype(np.float32) / 255.0
            if not channels_last:
                tensor = tensor.transpose(2, 0, 1)
            tensor = tensor[None, ...]
            try:
                outputs = model.Inference([tensor])
            except Exception:
                if args.runtime != "htp_auto" or actual_runtime != "htp":
                    raise
                model = None
                gc.collect()
                model, actual_runtime = _load_model(args.model, "cpu")
                outputs = model.Inference([tensor])
            if isinstance(outputs, np.ndarray):
                outputs = [outputs]
            ambiguity_margin = max(0.0, min(0.5, float(request.get("ambiguity_margin", 0.12))))
            detections, ambiguous = _decode_outputs(
                outputs, max(0.01, min(0.95, float(request.get("confidence", 0.25)))),
                (net_w, net_h), (original_w, original_h), (pad_x, pad_y), scale, ambiguity_margin,
            )
            if detections and len(detections[0].get("alternatives") or []) > 1:
                first = detections[0]["alternatives"]
                ambiguous |= first[0] - first[1] < ambiguity_margin
            response = {"ok": True, "detections": detections, "ambiguous": ambiguous,
                        "runtime": actual_runtime,
                        "inference_ms": round((time.monotonic() - started) * 1000, 1),
                        "frame_id": request.get("frame_id"), "width": original_w, "height": original_h}
        except Exception as exc:
            response = {"ok": False, "error": str(exc)[:300]}
        protocol_out.write(json.dumps(response, separators=(",", ":")) + "\n")
        protocol_out.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.__stdout__.write(json.dumps({"ok": False, "error": str(exc)[:300]}) + "\n")
        sys.__stdout__.flush()
