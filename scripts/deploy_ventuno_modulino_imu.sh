#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sketch_dir="${repo_root}/firmware/ventuno_modulino_imu_bridge"
fqbn="arduino:zephyr:ventunoq"
upload_address="${VENTUNO_Q_UPLOAD_ADDRESS:-192.168.0.14}"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli is required on the VENTUNO Q." >&2
  exit 1
fi

echo "Compiling Modulino Movement bridge for ${fqbn}..."
arduino-cli compile --fqbn "${fqbn}" "${sketch_dir}"

echo "Uploading STM32 firmware to ${upload_address}."
echo "Arduino CLI will prompt for the network upload password."
arduino-cli upload --fqbn "${fqbn}" --port "${upload_address}" "${sketch_dir}"
