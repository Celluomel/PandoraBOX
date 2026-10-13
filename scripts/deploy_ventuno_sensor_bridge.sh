#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sketch_dir="${repo_root}/firmware/ventuno_sensor_bridge"
fqbn="arduino:zephyr:ventunoq"
upload_address="${VENTUNO_Q_UPLOAD_ADDRESS:-192.168.0.14}"
tof_enabled="${BODY_ENABLE_TOF:-0}"
imu_enabled="${BODY_ENABLE_IMU:-1}"
radar_baud="${BODY_RADAR_BAUD:-256000}"

if [[ "${tof_enabled}" != "0" && "${tof_enabled}" != "1" ]]; then
  echo "BODY_ENABLE_TOF must be 0 or 1." >&2
  exit 2
fi
if [[ "${imu_enabled}" != "0" && "${imu_enabled}" != "1" ]]; then
  echo "BODY_ENABLE_IMU must be 0 or 1." >&2
  exit 2
fi
if ! [[ "${radar_baud}" =~ ^[0-9]+$ ]] || (( radar_baud < 1200 || radar_baud > 3000000 )); then
  echo "BODY_RADAR_BAUD must be an integer from 1200 to 3000000." >&2
  exit 2
fi

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli is required on the VENTUNO Q." >&2
  exit 1
fi

bash "${repo_root}/scripts/configure_ventuno_uart7.sh"
arduino-cli lib install "Arduino_Modulino@0.9.1" "Adafruit VL53L1X" "Adafruit BusIO"
build_root="$(mktemp -d)"
build_dir="${build_root}/ventuno_sensor_bridge"
mkdir -p "${build_dir}"
cp "${sketch_dir}/ventuno_sensor_bridge.ino" "${build_dir}/ventuno_sensor_bridge.ino"
trap 'rm -rf "${build_root}"' EXIT
libraries_dir="${HOME}/Arduino/libraries"
echo "Compiling sensor bridge for ${fqbn} (BODY_ENABLE_IMU=${imu_enabled}, BODY_ENABLE_TOF=${tof_enabled}, BODY_RADAR_BAUD=${radar_baud})..."
if ! arduino-cli compile --fqbn "${fqbn}" \
    --libraries "${libraries_dir}" \
    --build-property "compiler.cpp.extra_flags=-DBODY_ENABLE_IMU=${imu_enabled} -DBODY_ENABLE_TOF=${tof_enabled} -DBODY_RADAR_BAUD=${radar_baud}" \
    "${build_dir}"; then
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
arduino-cli upload --fqbn "${fqbn}" --port "${upload_address}" "${build_dir}"
echo "Upload complete. Verify body_imu_read, body_tof_read, and body_ld2450_read over the local Router Bridge."
