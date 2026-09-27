#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-body_venv/bin/python}"
exec "$PYTHON" -m body_runtime_host.robot_sim --host "${FNK0031_SIM_HOST:-127.0.0.1}" --port "${FNK0031_SIM_PORT:-9100}"
