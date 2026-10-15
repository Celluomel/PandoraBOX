"""Pilot fine-tuning of one ADE + COCO-Stuff semantic label space."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import load_dataset
from PIL import Image
from transformers import AutoImageProcessor, SegformerForSemanticSegmentation

from taxonomy import build_taxonomy, parse_coco_labels, remap_coco_mask


BASE_MODEL = "nvidia/segformer-b0-finetuned-ade-512-512"
ADE_DATASET = "vikhyatk/scene_parse_150"
COCO_DATASET = "GATE-engine/COCOStuff10K"
IGNORE_INDEX = 255


def ade_mask_to_output(mask: Image.Image, class_count: int) -> Image.Image:
    source = np.asarray(mask.convert("L"), dtype=np.uint8)
    target = np.full(source.shape, IGNORE_INDEX, dtype=np.uint8)
    valid = (source >= 1) & (source <= 150)
    target[valid] = source[valid] - 1
    if (target[valid] >= class_count).any():
        raise ValueError("ADE20K mask contains a label outside its 150-class taxonomy")
    return Image.fromarray(target, mode="L")


def coco_mask_to_output(mask: Image.Image, taxonomy: dict[str, object]) -> Image.Image:
    output_labels = taxonomy["output_labels"]
    result = remap_coco_mask(
        np.asarray(mask.convert("L"), dtype=np.uint8),
        taxonomy["coco_to_output"],
        len(output_labels),
    )
    return Image.fromarray(result, mode="L")


def make_batch(rows: list[dict], source: str, processor, taxonomy, device):
    if source == "ade":
        masks = [ade_mask_to_output(row["annotation"], len(taxonomy["output_labels"])) for row in rows]
    else:
        masks = [coco_mask_to_output(row["mask"], taxonomy) for row in rows]
    images = [row["image"].convert("RGB") for row in rows]
    encoded = processor(
        images=images,
        segmentation_maps=masks,
        return_tensors="pt",
    )
    return encoded["pixel_values"].to(device), encoded["labels"].long().to(device)


def add_coco_head(model, taxonomy: dict[str, object], device: torch.device) -> None:
    old = model.decode_head.classifier
    labels = taxonomy["output_labels"]
    new = nn.Conv2d(
        old.in_channels,
        len(labels),
        kernel_size=old.kernel_size,
        stride=old.stride,
        padding=old.padding,
        dilation=old.dilation,
        groups=old.groups,
        bias=old.bias is not None,
        padding_mode=old.padding_mode,
    ).to(device=device, dtype=old.weight.dtype)
    nn.init.kaiming_uniform_(new.weight, a=5**0.5)
    if new.bias is not None:
        nn.init.zeros_(new.bias)
    new.weight.data[: old.out_channels].copy_(old.weight.data)
    new.weight.data[old.out_channels :].zero_()
    if old.bias is not None:
        new.bias.data[: old.out_channels].copy_(old.bias.data)
        new.bias.data[old.out_channels :].fill_(-4.0)
    model.decode_head.classifier = new
    model.config.num_labels = len(labels)
    model.config.id2label = {int(index): name for index, name in labels.items()}
    model.config.label2id = {name: int(index) for index, name in labels.items()}


def update_confusion(confusion, logits, labels):
    logits = F.interpolate(logits, size=labels.shape[-2:], mode="bilinear", align_corners=False)
    predicted = logits.argmax(1)
    valid = labels != IGNORE_INDEX
    classes = confusion.shape[0]
    encoded = labels[valid] * classes + predicted[valid]
    confusion.add_(torch.bincount(encoded, minlength=classes**2).reshape_as(confusion))


def evaluate(model, processor, dataset, source, taxonomy, limit, batch_size, device):
    classes = len(taxonomy["output_labels"])
    confusion = torch.zeros((classes, classes), dtype=torch.int64, device=device)
    rows = []
    count = 0
    model.eval()

    def run_batch():
        pixels, labels = make_batch(rows, source, processor, taxonomy, device)
        with torch.inference_mode():
            update_confusion(confusion, model(pixel_values=pixels).logits, labels)

    for row in dataset:
        rows.append(row)
        count += 1
        if len(rows) == batch_size:
            run_batch()
            rows.clear()
        if limit and count >= limit:
            break
    if rows:
        run_batch()

    matrix = confusion.cpu()
    scores = {}
    if source == "ade":
        scored_ids = {int(index) for index in taxonomy["ade_labels"]}
    else:
        scored_ids = set(taxonomy["coco_to_output"].values())
    for index, name in taxonomy["output_labels"].items():
        if int(index) not in scored_ids:
            continue
        intersection = int(matrix[index, index])
        union = int(matrix[index, :].sum() + matrix[:, index].sum() - intersection)
        if union:
            scores[name] = intersection / union
    return {
        "samples": count,
        "mean_iou_present_classes": sum(scores.values()) / max(1, len(scores)),
        "classes_scored": len(scores),
        "iou": scores,
    }


def save_checkpoint(model, processor, taxonomy, destination: Path, report: dict) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(destination, safe_serialization=True)
    processor.save_pretrained(destination)
    (destination / "taxonomy.json").write_text(
        json.dumps(taxonomy, indent=2) + os.linesep, encoding="utf-8"
    )
    (destination / "progress.json").write_text(
        json.dumps(report, indent=2) + os.linesep, encoding="utf-8"
    )


def train(args):
    if not torch.cuda.is_available() and args.device != "cpu":
        raise RuntimeError("ROCm GPU unavailable; refusing an accidental CPU training run")
    device = torch.device("cpu" if args.device == "cpu" else "cuda")
    source_model = SegformerForSemanticSegmentation.from_pretrained(BASE_MODEL)
    ade_labels = {int(index): str(name) for index, name in source_model.config.id2label.items()}
    coco_labels = parse_coco_labels(Path(__file__).with_name("coco_stuff_labels.txt").read_text(encoding="utf-8"))
    taxonomy = build_taxonomy(ade_labels, coco_labels)
    if args.resume:
        model = SegformerForSemanticSegmentation.from_pretrained(args.resume).to(device)
        config_processor = AutoImageProcessor.from_pretrained(args.resume)
        expected = {int(index): str(name) for index, name in taxonomy["output_labels"].items()}
        actual = {int(index): str(name) for index, name in model.config.id2label.items()}
        if actual != expected:
            raise ValueError("Resume checkpoint label map does not match the current ADE+COCO taxonomy")
    else:
        model = source_model.to(device)
        config_processor = AutoImageProcessor.from_pretrained(BASE_MODEL)
        add_coco_head(model, taxonomy, device)
    config_processor.do_reduce_labels = False

    head_ids = {id(parameter) for parameter in model.decode_head.classifier.parameters()}
    backbone = [parameter for parameter in model.parameters() if id(parameter) not in head_ids]
    optimizer = torch.optim.AdamW(
        [
            {"params": backbone, "lr": args.learning_rate},
            {"params": model.decode_head.classifier.parameters(), "lr": args.head_learning_rate},
        ],
        weight_decay=0.01,
    )

    ade_train = load_dataset(ADE_DATASET, split="train", streaming=True)
    coco_train = load_dataset(COCO_DATASET, split="train", streaming=True)
    ade_val = load_dataset(ADE_DATASET, split="validation", streaming=True)
    coco_val = load_dataset(COCO_DATASET, split="test", streaming=True)
    report = {
        "base_model": BASE_MODEL,
        "datasets": {"ade": ADE_DATASET, "coco_stuff": COCO_DATASET},
        "class_count": len(taxonomy["output_labels"]),
        "merged_coco_classes": len(taxonomy["merged_coco_classes"]),
        "new_coco_classes": len(taxonomy["new_coco_classes"]),
        "device": str(device),
        "resumed_from": str(args.resume) if args.resume else None,
        "target_train_samples_per_dataset": args.train_samples,
        "target_validation_samples_per_dataset": args.val_samples,
        "baseline": {},
        "training": {},
        "validation": {},
    }

    for key, dataset, source in (("ade", ade_val, "ade"), ("coco_stuff", coco_val, "coco")):
        report["baseline"][key] = evaluate(
            model, config_processor, dataset, source, taxonomy, args.val_samples, args.batch_size, device
        )
    print(json.dumps({"baseline": report["baseline"]}), flush=True)

    ade_train = ade_train.shuffle(seed=args.seed, buffer_size=args.shuffle_buffer)
    coco_train = coco_train.shuffle(seed=args.seed + 1, buffer_size=args.shuffle_buffer)
    ade_iter, coco_iter = iter(ade_train), iter(coco_train)
    model.train()
    losses = []
    trained = {"ade": 0, "coco_stuff": 0}
    for step in range(args.steps):
        for source, iterator, limit in (
            ("ade", ade_iter, args.train_samples),
            ("coco", coco_iter, args.train_samples),
        ):
            key = "ade" if source == "ade" else "coco_stuff"
            if trained[key] >= limit:
                continue
            batch = []
            for _ in range(min(args.batch_size, limit - trained[key])):
                try:
                    batch.append(next(iterator))
                except StopIteration:
                    break
            if not batch:
                continue
            trained[key] += len(batch)
            pixels, labels = make_batch(batch, source, config_processor, taxonomy, device)
            optimizer.zero_grad(set_to_none=True)
            output = model(pixel_values=pixels, labels=labels)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(output.loss.detach().cpu()))
        if (step + 1) % 32 == 0 or step + 1 == args.steps:
            progress = {
                "step": step + 1,
                "steps": args.steps,
                "samples": trained,
                "mean_loss": sum(losses) / max(1, len(losses)),
            }
            print(json.dumps(progress), flush=True)
        if args.checkpoint_interval and (step + 1) % args.checkpoint_interval == 0:
            report["training"] = {
                "step": step + 1,
                "samples": trained,
                "mean_loss": sum(losses) / max(1, len(losses)),
            }
            save_checkpoint(model, config_processor, taxonomy, args.output, report)
            print(json.dumps({"checkpoint_saved": str(args.output), "step": step + 1}), flush=True)

    model.eval()
    report["training"] = {"samples": trained, "mean_loss": sum(losses) / max(1, len(losses))}
    for key, dataset, source in (("ade", ade_val, "ade"), ("coco_stuff", coco_val, "coco")):
        report["validation"][key] = evaluate(
            model, config_processor, dataset, source, taxonomy, args.val_samples, args.batch_size, device
        )

    save_checkpoint(model, config_processor, taxonomy, args.output, report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + os.linesep, encoding="utf-8")
    print(json.dumps({"validation": report["validation"], "model": str(args.output), "report": str(args.report)}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=2250)
    parser.add_argument("--train-samples", type=int, default=9000, help="Maximum samples per dataset")
    parser.add_argument("--val-samples", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--head-learning-rate", type=float, default=2e-4)
    parser.add_argument("--shuffle-buffer", type=int, default=512)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--checkpoint-interval", type=int, default=128)
    parser.add_argument("--resume", type=Path, help="Optional existing merged-taxonomy model checkpoint")
    parser.add_argument("--output", type=Path, default=Path(".training-runtime/segformer-ade-coco-full"))
    parser.add_argument("--report", type=Path, default=Path(".training-runtime/segformer-ade-coco-full.json"))
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    if args.device == "cuda":
        torch.cuda.init()
        print(f"Training on {torch.cuda.get_device_name(0)}; ROCm/HIP {torch.version.hip}", flush=True)
    train(args)


if __name__ == "__main__":
    main()
