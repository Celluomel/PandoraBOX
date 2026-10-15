"""Submit the trained segmentation ONNX model for Ventuno Q QNN/DLC compilation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(".training-runtime/segformer-ade-coco-onnx/segformer_ade_coco_512.onnx"),
    )
    parser.add_argument("--output", type=Path, default=Path(".training-runtime/segformer-ade-coco-ventuno.dlc"))
    parser.add_argument("--device", default="Arduino VENTUNO Q")
    parser.add_argument(
        "--options",
        default="--target_runtime qnn_dlc --quantize_full_type int8",
        help="Qualcomm AI Hub compile options",
    )
    parser.add_argument(
        "--qai-hub-site-packages",
        type=Path,
        default=Path(".qaihm_runtime"),
        help="Local directory containing the Qualcomm AI Hub SDK, if not installed in this Python environment",
    )
    parser.add_argument("--profile", help="Optional Qualcomm AI Hub CLI profile name")
    args = parser.parse_args()

    if not args.model.is_file():
        raise SystemExit(f"ONNX model not found: {args.model}")
    if args.qai_hub_site_packages.exists():
        sys.path.append(str(args.qai_hub_site_packages.resolve()))
    if args.profile:
        os.environ["QAIHUB_CLIENT_INI"] = str(
            (Path.home() / ".qai_hub" / f"{args.profile}.ini").resolve()
        )
    try:
        import qai_hub as hub
        from qai_hub.api_utils import load_default_api_config

        load_default_api_config()
    except (ImportError, FileNotFoundError) as exc:
        raise SystemExit(
            "Qualcomm AI Hub SDK/profile is unavailable. Configure an AI Hub profile, then retry."
        ) from exc

    device = hub.Device(args.device)
    job = hub.submit_compile_job(
        model=str(args.model),
        device=device,
        name="PandoraBOX SegFormer ADE+COCO 247-class Ventuno Q",
        options=args.options,
    )
    print(f"Compile job submitted: {job.url}", flush=True)
    status = job.wait()
    if not status.success:
        raise RuntimeError(f"Qualcomm compile job finished with status {status}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = job.download_target_model(str(args.output))
    print(f"Compile status: {status}; DLC: {result or args.output}", flush=True)


if __name__ == "__main__":
    main()
