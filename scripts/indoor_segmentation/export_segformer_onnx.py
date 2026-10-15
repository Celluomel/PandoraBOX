"""Export the trained merged-taxonomy SegFormer as a fixed-shape ONNX graph."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import torch
from transformers import AutoImageProcessor, SegformerForSemanticSegmentation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path(".training-runtime/segformer-ade-coco-full"))
    parser.add_argument("--output", type=Path, default=Path(".training-runtime/segformer-ade-coco-onnx"))
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument(
        "--onnx-site-packages",
        type=Path,
        help="Optional site-packages path when ONNX is not installed in the training environment",
    )
    args = parser.parse_args()

    if args.onnx_site_packages:
        sys.path.append(str(args.onnx_site_packages.resolve()))
    try:
        import onnx
    except ImportError as exc:
        raise SystemExit("Install ONNX in this Python environment or pass --onnx-site-packages") from exc

    model = SegformerForSemanticSegmentation.from_pretrained(args.model).cpu().eval()
    processor = AutoImageProcessor.from_pretrained(args.model)
    model.config.return_dict = False
    sample = torch.zeros((1, 3, args.size, args.size), dtype=torch.float32)
    args.output.mkdir(parents=True, exist_ok=True)
    onnx_path = args.output / "segformer_ade_coco_512.onnx"

    torch.onnx.export(
        model,
        (sample,),
        str(onnx_path),
        export_params=True,
        opset_version=args.opset,
        do_constant_folding=True,
        input_names=["pixel_values"],
        output_names=["logits"],
        dynamic_axes=None,
        dynamo=False,
    )
    graph = onnx.load(str(onnx_path))
    onnx.checker.check_model(graph, full_check=True)
    onnx.save_model(graph, str(onnx_path))
    shutil.copy2(args.model / "taxonomy.json", args.output / "taxonomy.json")
    shutil.copy2(args.model / "config.json", args.output / "config.json")
    processor.save_pretrained(args.output)
    print(
        json.dumps(
            {
                "onnx": str(onnx_path),
                "opset": args.opset,
                "input_shape": [1, 3, args.size, args.size],
                "output_shape": [1, model.config.num_labels, args.size // 4, args.size // 4],
                "parameters": sum(parameter.numel() for parameter in model.parameters()),
                "model_bytes": onnx_path.stat().st_size,
                "onnx_checker": "passed",
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
