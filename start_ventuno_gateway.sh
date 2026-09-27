#!/usr/bin/env bash
set -euo pipefail

# Linux side of the Arduino VENTUNO Q. The FNK0031 board remains the servo
# controller; this process only exposes the Body API and forwards commands.
export FNK0031_BOARD_URL="${FNK0031_BOARD_URL:-http://fnk0031.local:9100}"
export VENTUNO_GATEWAY_PORT="${VENTUNO_GATEWAY_PORT:-9100}"
export VENTUNO_GATEWAY_TOKEN="${VENTUNO_GATEWAY_TOKEN:-}"
export VENTUNO_ACTUATION_ENABLED="${VENTUNO_ACTUATION_ENABLED:-0}"
export VENTUNO_DEPLOY_ENABLED="${VENTUNO_DEPLOY_ENABLED:-0}"
export VENTUNO_DEPLOY_DIR="${VENTUNO_DEPLOY_DIR:-/opt/pandorabox/deployments}"

exec python3 -m body_runtime_host.ventuno_gateway \
  --board-url "$FNK0031_BOARD_URL" \
  --port "$VENTUNO_GATEWAY_PORT" \
  --deploy-dir "$VENTUNO_DEPLOY_DIR"
