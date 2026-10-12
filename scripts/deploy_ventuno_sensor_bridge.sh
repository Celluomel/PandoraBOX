#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sketch_dir="${repo_root}/firmware/ventuno_sensor_bridge"
fqbn="arduino:zephyr:ventunoq"
upload_address="${VENTUNO_Q_UPLOAD_ADDRESS:-192.168.0.14}"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli is required on the VENTUNO Q." >&2
  exit 1
fi

"${repo_root}/scripts/configure_ventuno_uart7.sh"
echo "Compiling the combined Modulino IMU + LD2450 bridge for ${fqbn}..."
if ! arduino-cli compile --fqbn "${fqbn}" "${sketch_dir}"; then
  cat >&2 <<'EOF'
Compile failed; the current STM32 firmware was not changed.
If the error names DT_NODELABEL(uart7) or a missing device ordinal, the
installed Arduino Zephyr variant's generated devicetree does not expose UART7.
Do not upload a standalone sketch as a workaround: it would remove the IMU RPC.
EOF
  exit 1
fi

if [[ "${1:-}" != "--upload" ]]; then
  echo "Build succeeded. Firmware was not flashed. Review the wiring, then run:"
  echo "  $0 --upload"
  exit 0
fi

echo "Uploading combined sensor firmware to ${upload_address}."
echo "Arduino CLI will prompt for the network upload password."
arduino-cli upload --fqbn "${fqbn}" --port "${upload_address}" "${sketch_dir}"
echo "Upload complete. Verify both body_imu_read and body_ld2450_read over the local Router Bridge."
