"""Run one synthetic end-to-end inference on the AI Hub Ventuno Q target."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("models/indoor-segmentation/segformer-ade-coco-247.dlc"))
    parser.add_argument("--device", default="Arduino VENTUNO Q")
    parser.add_argument("--qai-hub-site-packages", type=Path, default=Path(".qaihm_runtime"))
    parser.add_argument("--job-id", help="Resume a previously submitted inference job")
    parser.add_argument("--status-only", action="store_true", help="Print current status and exit")
    parser.add_argument("--profile-output", type=Path, default=Path(".training-runtime/segformer-ade-coco-ventuno-profile.json"))
    args = parser.parse_args()
    if not args.model.is_file():
        raise SystemExit(f"Compiled DLC not found: {args.model}")
    if args.qai_hub_site_packages.exists():
        sys.path.append(str(args.qai_hub_site_packages.resolve()))
    try:
        import qai_hub as hub
        from qai_hub.api_utils import load_default_api_config

        load_default_api_config()
    except (ImportError, FileNotFoundError) as exc:
        raise SystemExit(f"Qualcomm AI Hub SDK/profile is unavailable ({type(exc).__name__}).") from exc

    client = hub.Client()
    if args.job_id:
        job = client.get_job(args.job_id)
        if args.status_only:
            status = job.get_status()
            print(f"Inference job status: {status.code}")
            return
    else:
        # Input is normalized like the runtime preprocessing, but generated locally.
        y, x = np.mgrid[0:512, 0:512].astype(np.float32)
        image = np.stack((x / 511.0, y / 511.0, np.zeros_like(x)), axis=0)
        image = ((image - np.asarray([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None])
                 / np.asarray([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None])
        tensor = image[None].astype(np.float32)
        job = client.submit_inference_job(
            model=str(args.model),
            device=hub.Device(args.device),
            inputs={"pixel_values": [tensor]},
            name="PandoraBOX SegFormer 247-class Ventuno Q smoke inference",
            profile=True,
        )
        print(f"Inference job submitted: {job.url}", flush=True)
    status = job.wait()
    if not status.success:
        raise RuntimeError(f"Ventuno Q inference failed: {status}")
    output = job.download_output_data()
    if not output:
        raise RuntimeError("Inference succeeded but no output dataset was returned")
    first = np.asarray(next(iter(output.values()))[0])
    if first.shape != (1, 247, 128, 128) or not np.isfinite(first).all():
        raise RuntimeError(f"Unexpected or non-finite SegFormer output: {first.shape}")
    predicted_classes = int(np.unique(first.argmax(axis=1)).size)
    print(f"Inference status: success; output shape: {first.shape}; predicted classes: {predicted_classes}")
    profile = job.download_profile()
    if profile:
        args.profile_output.parent.mkdir(parents=True, exist_ok=True)
        args.profile_output.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        units = Counter(layer.get("compute_unit", "UNKNOWN") for layer in profile.get("execution_detail", []))
        latency_us = profile.get("execution_summary", {}).get("estimated_inference_time")
        latency_ms = latency_us / 1000.0 if latency_us is not None else None
        print(f"Inference profile: {dict(units)}; estimated inference time: {latency_ms} ms")
        print(f"Profile saved: {args.profile_output}")
    else:
        print("Inference profile: unavailable")


if __name__ == "__main__":
    main()
