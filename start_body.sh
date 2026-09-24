#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
BODY_PYTHON="body_venv/bin/python"
if [[ ! -x "$BODY_PYTHON" ]] || ! "$BODY_PYTHON" -c "import sys" >/dev/null 2>&1; then
  echo "[*] Creating or repairing the independent Body virtual environment..."
  python3 -m venv --clear body_venv
fi
"$BODY_PYTHON" -m pip install --upgrade pip -q
"$BODY_PYTHON" -m pip install -r body_requirements.txt -q
echo "Starting standalone PandoraBOX Body Runtime..."
echo "Body management page: http://127.0.0.1:8766/"
exec "$BODY_PYTHON" -m body_runtime_host
