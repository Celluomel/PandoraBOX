#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sketch_dir="${repo_root}/firmware/ventuno_sensor_bridge"
fqbn="arduino:zephyr:ventunoq"
upload_address="${VENTUNO_Q_UPLOAD_ADDRESS:-192.168.0.14}"
app_id="user:pandorabox-body-sensors"
app_sketch_dir="${HOME}/ArduinoApps/pandorabox-body-sensors/sketch"
app_backup_root="${HOME}/ArduinoApps/.backups/pandorabox-body-sensors"
tof_enabled="${BODY_ENABLE_TOF:-0}"
imu_enabled="${BODY_ENABLE_IMU:-1}"
ultrasonic_enabled="${BODY_ENABLE_ULTRASONIC:-1}"
ultrasonic_channel_mask="${BODY_ULTRASONIC_CHANNEL_MASK:-7}"
radar_baud="${BODY_RADAR_BAUD:-256000}"
gps_baud="${BODY_GPS_BAUD:-38400}"

if [[ "${tof_enabled}" != "0" && "${tof_enabled}" != "1" ]]; then
  echo "BODY_ENABLE_TOF must be 0 or 1." >&2
  exit 2
fi
if [[ "${imu_enabled}" != "0" && "${imu_enabled}" != "1" ]]; then
  echo "BODY_ENABLE_IMU must be 0 or 1." >&2
  exit 2
fi
if [[ "${ultrasonic_enabled}" != "0" && "${ultrasonic_enabled}" != "1" ]]; then
  echo "BODY_ENABLE_ULTRASONIC must be 0 or 1." >&2
  exit 2
fi
if ! [[ "${ultrasonic_channel_mask}" =~ ^[0-7]$ ]]; then
  echo "BODY_ULTRASONIC_CHANNEL_MASK must be an integer from 0 to 7." >&2
  exit 2
fi
if ! [[ "${radar_baud}" =~ ^[0-9]+$ ]] || (( radar_baud < 1200 || radar_baud > 3000000 )); then
  echo "BODY_RADAR_BAUD must be an integer from 1200 to 3000000." >&2
  exit 2
fi
if ! [[ "${gps_baud}" =~ ^[0-9]+$ ]] || (( gps_baud < 1200 || gps_baud > 3000000 )); then
  echo "BODY_GPS_BAUD must be an integer from 1200 to 3000000." >&2
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
compiled_dir="${build_root}/compiled"
mkdir -p "${build_dir}"
cp "${sketch_dir}/ventuno_sensor_bridge.ino" "${build_dir}/ventuno_sensor_bridge.ino"
trap 'rm -rf "${build_root}"' EXIT
libraries_dir="${HOME}/Arduino/libraries"
echo "Compiling sensor bridge for ${fqbn} (BODY_ENABLE_IMU=${imu_enabled}, BODY_ENABLE_TOF=${tof_enabled}, BODY_ENABLE_ULTRASONIC=${ultrasonic_enabled}, BODY_ULTRASONIC_CHANNEL_MASK=${ultrasonic_channel_mask}, BODY_RADAR_BAUD=${radar_baud}, BODY_GPS_BAUD=${gps_baud})..."
if ! arduino-cli compile --fqbn "${fqbn}" \
    --libraries "${libraries_dir}" \
    --output-dir "${compiled_dir}" \
    --build-property "compiler.cpp.extra_flags=-DBODY_ENABLE_IMU=${imu_enabled} -DBODY_ENABLE_TOF=${tof_enabled} -DBODY_ENABLE_ULTRASONIC=${ultrasonic_enabled} -DBODY_ULTRASONIC_CHANNEL_MASK=${ultrasonic_channel_mask} -DBODY_RADAR_BAUD=${radar_baud} -DBODY_GPS_BAUD=${gps_baud}" \
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

echo "Uploading combined sensor firmware to persistent STM32 flash on ${upload_address}."
echo "Use this direct Arduino CLI uploader, not App Lab app start: App Lab loads its MCU sketch into volatile RAM."
if ! command -v arduino-app-cli >/dev/null 2>&1; then
  echo "arduino-app-cli is required to keep App Lab aligned with the flashed firmware." >&2
  exit 1
fi
if [[ ! -d "${app_sketch_dir}" || ! -f "${sketch_dir}/sketch.yaml" ]]; then
  echo "App Lab sketch directory or canonical sketch.yaml is missing; refusing to flash out of sync." >&2
  exit 1
fi

app_state="$(arduino-app-cli app list --format json | python3 -c '
import json, sys
apps = json.load(sys.stdin).get("apps", [])
app = next((item for item in apps if item.get("name") == "pandorabox-body-sensors"), {})
print(app.get("status", "missing"), str(app.get("default", False)).lower())
')"
read -r app_status app_is_default <<<"${app_state}"
if [[ "${app_status}" == "missing" ]]; then
  echo "${app_id} is not registered in App Lab; refusing to flash without alignment." >&2
  exit 1
fi
if [[ "${app_is_default}" == "true" ]]; then
  echo "Clearing the App Lab default: its MCU sketch is RAM-loaded and not power-cycle persistent."
  arduino-app-cli properties set default none
fi
if [[ "${app_status}" == "running" ]]; then
  echo "Stopping ${app_id} before persistent MCU upload."
  arduino-app-cli app stop "${app_id}"
fi

mkdir -p "${app_backup_root}"
app_backup_dir="$(mktemp -d "${app_backup_root}/$(date +%Y%m%d_%H%M%S)-XXXXXX")"
for app_file in sketch.ino sketch.yaml; do
  if [[ "${app_file}" == "sketch.ino" ]]; then
    source_file="${sketch_dir}/ventuno_sensor_bridge.ino"
  else
    source_file="${sketch_dir}/sketch.yaml"
  fi
  target_file="${app_sketch_dir}/${app_file}"
  if [[ -e "${target_file}" ]]; then
    if ! cmp -s "${source_file}" "${target_file}"; then
      cp -p "${target_file}" "${app_backup_dir}/${app_file}"
    fi
  else
    touch "${app_backup_dir}/${app_file}.was_missing"
  fi
done
restore_applab_files() {
  for app_file in sketch.ino sketch.yaml; do
    target_file="${app_sketch_dir}/${app_file}"
    if [[ -f "${app_backup_dir}/${app_file}" ]]; then
      cp -p "${app_backup_dir}/${app_file}" "${target_file}"
    elif [[ -f "${app_backup_dir}/${app_file}.was_missing" ]]; then
      rm -f -- "${target_file}"
    fi
  done
}
app_sync_in_progress=0
upload_succeeded=0
cleanup_deploy() {
  if [[ "${app_sync_in_progress}" == "1" && "${upload_succeeded}" != "1" ]]; then
    restore_applab_files
  fi
  rm -rf -- "${build_root}"
}
trap cleanup_deploy EXIT

echo "Aligning App Lab sketch and manifest; differing originals are backed up in ${app_backup_dir}."
app_sync_in_progress=1
install -m 0664 "${sketch_dir}/ventuno_sensor_bridge.ino" "${app_sketch_dir}/sketch.ino"
install -m 0664 "${sketch_dir}/sketch.yaml" "${app_sketch_dir}/sketch.yaml"
if ! cmp -s "${sketch_dir}/ventuno_sensor_bridge.ino" "${app_sketch_dir}/sketch.ino" \
    || ! cmp -s "${sketch_dir}/sketch.yaml" "${app_sketch_dir}/sketch.yaml"; then
  restore_applab_files
  echo "App Lab source verification failed; restored its previous files and did not flash." >&2
  exit 1
fi

echo "Arduino CLI may prompt for upload credentials, depending on the detected transport."
if ! arduino-cli upload --fqbn "${fqbn}" --port "${upload_address}" \
    --input-dir "${compiled_dir}" "${build_dir}"; then
  echo "STM32 upload failed; restoring App Lab's previous sketch and manifest." >&2
  exit 1
fi
upload_succeeded=1
app_sync_in_progress=0
echo "Upload complete. Verify body_ultrasonic_read, body_imu_read, body_tof_read, body_ld2450_read, and body_gps_read over the local Router Bridge."
