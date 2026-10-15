"""Build a verified ADE20K + COCO-Stuff label space."""

from __future__ import annotations

import re

import numpy as np


COCO_10K_UNANNOTATED_THING_IDS = {12, 26, 29, 30, 45, 66, 68, 69, 71, 83, 91}
COCO_TO_ADE = {
    "building-other": "building",
    "ceiling-other": "ceiling",
    "ceiling-tile": "ceiling",
    "clouds": "sky",
    "desk-stuff": "desk",
    "door-stuff": "door",
    "floor-marble": "floor",
    "floor-other": "floor",
    "floor-stone": "floor",
    "floor-tile": "floor",
    "floor-wood": "floor",
    "mirror-stuff": "mirror",
    "potted plant": "plant",
    "sky-other": "sky",
    "sports ball": "ball",
    "tv": "screen",
    "wall-brick": "wall",
    "wall-concrete": "wall",
    "wall-other": "wall",
    "wall-panel": "wall",
    "wall-stone": "wall",
    "wall-tile": "wall",
    "wall-wood": "wall",
    "window-blind": "windowpane",
    "window-other": "windowpane",
    "couch": "sofa",
    "dining table": "table",
}


def normalize(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower())


def parse_coco_labels(text: str) -> dict[int, str]:
    labels: dict[int, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(\d+)\s*:\s*(.*?)\s*", line)
        if match:
            labels[int(match.group(1))] = match.group(2)
    if labels.get(0) != "unlabeled" or len(labels) != 183:
        raise ValueError("Expected the official COCO-Stuff labels.txt with IDs 0..182")
    return labels


def build_taxonomy(ade_labels: dict[int, str], coco_labels: dict[int, str]) -> dict[str, object]:
    ade_by_name = {normalize(name): index for index, name in ade_labels.items()}
    aliases: dict[int, int] = {}
    additions: list[tuple[int, str]] = []
    for coco_id, coco_name in coco_labels.items():
        if coco_id == 0 or coco_id in COCO_10K_UNANNOTATED_THING_IDS:
            continue
        target = COCO_TO_ADE.get(normalize(coco_name), normalize(coco_name))
        if target in ade_by_name:
            aliases[coco_id] = ade_by_name[target]
        else:
            additions.append((coco_id, coco_name))

    output_labels = {int(index): str(name) for index, name in ade_labels.items()}
    next_id = max(output_labels, default=-1) + 1
    coco_to_output: dict[int, int] = {}
    for coco_id in sorted(aliases):
        coco_to_output[coco_id] = aliases[coco_id]
    for coco_id, name in additions:
        coco_to_output[coco_id] = next_id
        output_labels[next_id] = name
        next_id += 1
    return {
        "ade_labels": {int(index): str(name) for index, name in ade_labels.items()},
        "coco_to_output": coco_to_output,
        "output_labels": output_labels,
        "new_coco_classes": additions,
        "merged_coco_classes": [
            (coco_id, coco_labels[coco_id], aliases[coco_id]) for coco_id in sorted(aliases)
        ],
        "ignore_coco_ids": [0, *sorted(COCO_10K_UNANNOTATED_THING_IDS)],
    }


def remap_coco_mask(mask: np.ndarray, coco_to_output: dict[int, int], output_classes: int) -> np.ndarray:
    remapped = np.full(mask.shape, 255, dtype=np.uint8)
    for source_id, target_id in coco_to_output.items():
        if target_id >= 255 or target_id >= output_classes:
            raise ValueError(f"Output class {target_id} cannot be represented in an 8-bit mask")
        remapped[mask == source_id] = target_id
    valid = (remapped == 255) | (remapped < output_classes)
    if not bool(valid.all()):
        raise ValueError("Mapped mask contains an output class outside the model label space")
    return remapped
