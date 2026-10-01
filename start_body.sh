#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${BODY_INSTALL_ROS2:-0}" == "1" ]]; then
  bash ./install_body_ros2.sh
fi
if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # ROS 2 Python modules are provided by the distro environment, not pip.
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi
BODY_PYTHON="body_venv/bin/python"
if [[ ! -x "$BODY_PYTHON" ]] || ! "$BODY_PYTHON" -c "import sys" >/dev/null 2>&1; then
  echo "[*] Creating or repairing the independent Body virtual environment..."
  if ! python3 -m venv --clear body_venv; then
    PYTHON_MINOR="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    VENV_PACKAGE="python${PYTHON_MINOR}-venv"
    if command -v apt-get >/dev/null 2>&1; then
      echo "[*] Python venv support is missing; installing ${VENV_PACKAGE}..."
      if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
        apt-get update && apt-get install -y "$VENV_PACKAGE"
      elif command -v sudo >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y "$VENV_PACKAGE"
      else
        echo "[ERROR] Install ${VENV_PACKAGE} with apt, then rerun start_body.sh."
        exit 1
      fi
      python3 -m venv --clear body_venv
    else
      echo "[ERROR] Python venv support is missing. Install ${VENV_PACKAGE} (or your OS equivalent), then rerun."
      exit 1
    fi
  fi
fi

if ! "$BODY_PYTHON" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco" >/dev/null 2>&1; then
  echo "[*] Body dependencies are missing or incomplete. Installing them..."
  "$BODY_PYTHON" -m pip install --upgrade pip
  "$BODY_PYTHON" -m pip install -r body_requirements.txt
else
  echo "[OK] Body dependencies already installed."
fi

if ! "$BODY_PYTHON" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco" >/dev/null 2>&1; then
  echo "[ERROR] Body dependencies are still unavailable after installation."
  exit 1
fi
echo "Starting standalone PandoraBOX Body Runtime..."
echo "Body management page: http://127.0.0.1:8766/"
exec "$BODY_PYTHON" -m body_runtime_host
