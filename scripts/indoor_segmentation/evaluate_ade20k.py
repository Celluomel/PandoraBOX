"""Evaluate an ADE20K semantic-segmentation checkpoint on public validation data."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoImageProcessor, SegformerForSemanticSegmentation


DEFAULT_MODEL = "nvidia/segformer-b0-finetuned-ade-512-512"
DEFAULT_DATASET = "vikhyatk/scene_parse_150"
IGNORE_INDEX = 255


def evaluate(args: argparse.Namespace) -> dict[str, object]:
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    processor = AutoImageProcessor.from_pretrained(args.model, do_reduce_labels=True)
    model = SegformerForSemanticSegmentation.from_pretrained(args.model).to(device).eval()
    label2id = {str(name).lower(): int(index) for name, index in model.config.label2id.items()}
    class_ids = label2id
    if len(class_ids) != model.config.num_labels:
        raise RuntimeError(f"Checkpoint label map is incomplete: {len(class_ids)} / {model.config.num_labels}")

    dataset = load_dataset(args.dataset, split=args.split, streaming=True)
    confusion = torch.zeros((model.config.num_labels, model.config.num_labels), dtype=torch.int64, device=device)
    images, masks = [], []
    seen = 0

    def run_batch() -> None:
        nonlocal images, masks
        inputs = processor(images=images, segmentation_maps=masks, return_tensors="pt")
        labels = inputs.pop("labels").to(device)
        pixel_values = inputs["pixel_values"].to(device)
        with torch.inference_mode():
            logits = model(pixel_values=pixel_values).logits
            predictions = F.interpolate(logits, size=labels.shape[-2:], mode="bilinear", align_corners=False).argmax(1)
        valid = labels != IGNORE_INDEX
        encoded = labels[valid] * model.config.num_labels + predictions[valid]
        confusion.add_(torch.bincount(encoded, minlength=model.config.num_labels**2).reshape_as(confusion))
        images, masks = [], []

    for row in dataset:
        image = row["image"].convert("RGB")
        mask = row.get("annotation", row.get("label"))
        if mask is None:
            raise RuntimeError(f"Dataset row has no annotation field; fields={list(row)}")
        images.append(image)
        masks.append(mask.convert("L"))
        seen += 1
        if len(images) >= args.batch_size:
            run_batch()
        if args.limit and seen >= args.limit:
            break
    if images:
        run_batch()

    matrix = confusion.cpu()
    metrics: dict[str, object] = {
        "model": args.model,
        "dataset": args.dataset,
        "split": args.split,
        "samples": seen,
        "device": str(device),
        "classes": {},
    }
    iou_by_class: dict[str, float | None] = {}
    for name, class_id in class_ids.items():
        intersection = int(matrix[class_id, class_id])
        union = int(matrix[class_id, :].sum() + matrix[:, class_id].sum() - intersection)
        iou = intersection / union if union else None
        iou_by_class[name] = iou
        metrics["classes"][name] = {
            "iou": iou,
            "intersection_pixels": intersection,
            "union_pixels": union,
        }
    present_ious = [score for score in iou_by_class.values() if score is not None]
    metrics["mean_iou"] = sum(present_ious) / len(present_ious) if present_ious else None
    metrics["class_count"] = len(class_ids)
    metrics["best_classes"] = sorted(
        ((name, score) for name, score in iou_by_class.items() if score is not None),
        key=lambda item: item[1], reverse=True,
    )[:20]
    metrics["weakest_present_classes"] = sorted(
        ((name, score) for name, score in iou_by_class.items() if score is not None),
        key=lambda item: item[1],
    )[:20]
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--device", choices=("cuda", "cpu"), default=None)
    parser.add_argument("--output", type=Path, default=Path(".training-runtime/ade20k-baseline.json"))
    args = parser.parse_args()

    if torch.cuda.is_available():
        torch.cuda.init()
        print(f"GPU: {torch.cuda.get_device_name(0)}; ROCm/HIP {torch.version.hip}", flush=True)
    else:
        print("GPU unavailable; evaluating on CPU", flush=True)
    report = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + os.linesep, encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"Saved: {args.output}", flush=True)


if __name__ == "__main__":
    main()
