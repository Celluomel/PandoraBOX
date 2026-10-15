"""Fine-tune all 150 SegFormer ADE20K semantic classes on public ADE20K data."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoImageProcessor, SegformerForSemanticSegmentation


BASE_MODEL = "nvidia/segformer-b0-finetuned-ade-512-512"
DATASET_ID = "vikhyatk/scene_parse_150"
IGNORE_INDEX = 255


def prepare_batch(processor, rows: list[dict], device: torch.device):
    images = [row["image"].convert("RGB") for row in rows]
    masks = [row["annotation"].convert("L") for row in rows]
    inputs = processor(images=images, segmentation_maps=masks, return_tensors="pt")
    labels = inputs.pop("labels").to(device)
    return inputs["pixel_values"].to(device), labels


def update_confusion(confusion: torch.Tensor, logits: torch.Tensor, labels: torch.Tensor) -> None:
    logits = F.interpolate(logits, size=labels.shape[-2:], mode="bilinear", align_corners=False)
    predictions = logits.argmax(1)
    valid = labels != IGNORE_INDEX
    class_count = confusion.shape[0]
    encoded = labels[valid] * class_count + predictions[valid]
    confusion.add_(torch.bincount(encoded, minlength=class_count**2).reshape_as(confusion))


def iou_scores(confusion: torch.Tensor, id2label: dict[int, str]) -> dict[str, float | None]:
    matrix = confusion.cpu()
    scores = {}
    for index, label in id2label.items():
        intersection = int(matrix[index, index])
        union = int(matrix[index, :].sum() + matrix[:, index].sum() - intersection)
        scores[label] = intersection / union if union else None
    return scores


def validate(model, processor, dataset, limit: int, batch_size: int, device: torch.device):
    model.eval()
    class_count = model.config.num_labels
    id2label = {int(index): str(label) for index, label in model.config.id2label.items()}
    confusion = torch.zeros((class_count, class_count), dtype=torch.int64, device=device)
    batch: list[dict] = []
    count = 0

    def run_batch() -> None:
        pixels, labels = prepare_batch(processor, batch, device)
        with torch.inference_mode():
            update_confusion(confusion, model(pixel_values=pixels).logits, labels)

    for row in dataset:
        batch.append(row)
        count += 1
        if len(batch) == batch_size:
            run_batch()
            batch.clear()
        if limit and count >= limit:
            break
    if batch:
        run_batch()
    return iou_scores(confusion, id2label), count


def train(args: argparse.Namespace) -> dict[str, object]:
    if not torch.cuda.is_available() and args.device != "cpu":
        raise RuntimeError("AMD ROCm GPU is unavailable; refusing an accidental CPU training run.")
    device = torch.device("cpu" if args.device == "cpu" else "cuda")
    processor = AutoImageProcessor.from_pretrained(BASE_MODEL, do_reduce_labels=True)
    model = SegformerForSemanticSegmentation.from_pretrained(
        BASE_MODEL,
    ).to(device)

    head = model.decode_head.classifier.parameters()
    head_ids = {id(parameter) for parameter in head}
    backbone = [parameter for parameter in model.parameters() if id(parameter) not in head_ids]
    optimizer = torch.optim.AdamW(
        [
            {"params": backbone, "lr": args.learning_rate},
            {"params": model.decode_head.classifier.parameters(), "lr": args.head_learning_rate},
        ],
        weight_decay=0.01,
    )

    train_data = load_dataset(DATASET_ID, split="train", streaming=True)
    val_data = load_dataset(DATASET_ID, split="validation", streaming=True)
    best_mean_iou = -1.0
    report: dict[str, object] = {"base_model": BASE_MODEL, "dataset": DATASET_ID, "device": str(device), "epochs": []}

    for epoch in range(args.epochs):
        if hasattr(train_data, "set_epoch"):
            train_data.set_epoch(epoch)
        shuffled = train_data.shuffle(seed=args.seed + epoch, buffer_size=args.shuffle_buffer)
        model.train()
        losses = []
        batch: list[dict] = []
        seen = 0

        def train_batch() -> None:
            pixels, labels = prepare_batch(processor, batch, device)
            optimizer.zero_grad(set_to_none=True)
            output = model(pixel_values=pixels, labels=labels)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(output.loss.detach().cpu()))

        for row in shuffled:
            batch.append(row)
            seen += 1
            if len(batch) == args.batch_size:
                train_batch()
                batch.clear()
            if args.train_samples and seen >= args.train_samples:
                break
        if batch:
            train_batch()

        scores, val_count = validate(model, processor, val_data, args.val_samples, args.batch_size, device)
        present_scores = [score for score in scores.values() if score is not None]
        mean_iou = sum(present_scores) / max(1, len(present_scores))
        epoch_result = {
            "epoch": epoch + 1,
            "train_samples": seen,
            "mean_loss": sum(losses) / max(1, len(losses)),
            "validation_samples": val_count,
            "iou": scores,
        }
        report["epochs"].append(epoch_result)
        print(json.dumps(epoch_result), flush=True)

        if mean_iou > best_mean_iou:
            best_mean_iou = mean_iou
            args.output.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(args.output, safe_serialization=True)
            processor.save_pretrained(args.output)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + os.linesep, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--train-samples", type=int, default=2048)
    parser.add_argument("--val-samples", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--head-learning-rate", type=float, default=2e-4)
    parser.add_argument("--shuffle-buffer", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--output", type=Path, default=Path(".training-runtime/segformer-ade20k-all-classes"))
    parser.add_argument("--report", type=Path, default=Path(".training-runtime/segformer-ade20k-all-classes-training.json"))
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    if args.device == "cuda":
        torch.cuda.init()
        print(f"Training on {torch.cuda.get_device_name(0)}; ROCm/HIP {torch.version.hip}", flush=True)
    print(json.dumps(train(args), indent=2), flush=True)


if __name__ == "__main__":
    main()
