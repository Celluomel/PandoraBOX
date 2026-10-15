"""Wait for an existing Qualcomm AI Hub compile job and download its artifact."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_id")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".training-runtime/segformer-ade-coco-ventuno.dlc"),
    )
    parser.add_argument(
        "--qai-hub-site-packages",
        type=Path,
        default=Path(".qaihm_runtime"),
    )
    args = parser.parse_args()

    if args.qai_hub_site_packages.exists():
        sys.path.append(str(args.qai_hub_site_packages.resolve()))
    try:
        import qai_hub as hub
        from qai_hub.api_utils import load_default_api_config

        load_default_api_config()
    except (ImportError, FileNotFoundError) as exc:
        raise SystemExit("Qualcomm AI Hub SDK/profile is unavailable.") from exc

    job = hub.Client().get_job(args.job_id)
    status = job.wait()
    if not status.success:
        raise RuntimeError(f"Qualcomm compile job {args.job_id} failed: {status}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = job.download_target_model(str(args.output))
    print(f"Compile status: success; DLC saved to {result or args.output}")


if __name__ == "__main__":
    main()
