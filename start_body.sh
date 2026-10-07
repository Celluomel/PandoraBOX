#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

SECURE_PROXY_SETUP=0
if [[ "${1:-}" == "--setup-secure-proxy" ]]; then
  SECURE_PROXY_SETUP=1
  shift
fi

setup_secure_proxy() {
  if [[ "$(uname -s)" != "Linux" ]] || ! command -v systemctl >/dev/null 2>&1; then
    echo "[ERROR] Secure proxy setup requires Linux with systemd (the Ventuno Q runtime)."
    exit 1
  fi
  if ! command -v sudo >/dev/null 2>&1; then
    echo "[ERROR] sudo is required to install and configure the Caddy system service."
    exit 1
  fi

  LAN_HOST="${BODY_PROXY_HOST:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
  if [[ -z "$LAN_HOST" ]]; then
    read -r -p "LAN hostname or IP for the Body (for example 192.168.0.14): " LAN_HOST
  else
    read -r -p "LAN hostname or IP for HTTPS [${LAN_HOST}]: " INPUT_HOST
    LAN_HOST="${INPUT_HOST:-$LAN_HOST}"
  fi
  if [[ ! "$LAN_HOST" =~ ^[A-Za-z0-9._:-]+$ ]]; then
    echo "[ERROR] Invalid LAN hostname or IP."
    exit 1
  fi

  if ! command -v caddy >/dev/null 2>&1; then
    echo "[*] Installing Caddy system package..."
    sudo apt-get update
    sudo apt-get install --yes debian-keyring debian-archive-keyring apt-transport-https curl gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
    sudo apt-get update
    sudo apt-get install --yes caddy
  fi
  if ! command -v caddy >/dev/null 2>&1; then
    echo "[ERROR] Caddy installation did not provide the caddy command."
    exit 1
  fi

  read -r -p "Login name for the Body proxy [body]: " PROXY_USER
  PROXY_USER="${PROXY_USER:-body}"
  if [[ ! "$PROXY_USER" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "[ERROR] Login name may contain only letters, numbers, underscores, and hyphens."
    exit 1
  fi
  read -r -s -p "Choose a new Body proxy password (12+ characters): " PROXY_PASSWORD
  printf '\n'
  read -r -s -p "Confirm password: " PROXY_PASSWORD_CONFIRM
  printf '\n'
  if [[ ${#PROXY_PASSWORD} -lt 12 || "$PROXY_PASSWORD" != "$PROXY_PASSWORD_CONFIRM" ]]; then
    echo "[ERROR] Passwords must match and contain at least 12 characters."
    exit 1
  fi
  PROXY_HASH="$(sudo caddy hash-password --plaintext "$PROXY_PASSWORD")"
  unset PROXY_PASSWORD PROXY_PASSWORD_CONFIRM

  CADDY_TMP="$(mktemp)"
  trap 'rm -f "$CADDY_TMP"' RETURN
  cat >"$CADDY_TMP" <<EOF
https://${LAN_HOST} {
	tls internal
	basic_auth {
		${PROXY_USER} ${PROXY_HASH}
	}
	header {
		Cache-Control "no-store, no-cache, must-revalidate, max-age=0"
		Pragma "no-cache"
		Expires "0"
	}
	reverse_proxy 127.0.0.1:8766
}
EOF
  sudo install -D -m 0644 "$CADDY_TMP" /etc/caddy/Caddyfile
  sudo caddy validate --config /etc/caddy/Caddyfile

  BODY_PYTHON="body_venv/bin/python"
  if [[ -x "$BODY_PYTHON" ]]; then
    "$BODY_PYTHON" - <<'PY'
import json, os, tempfile
path = "data/body/config.json"
with open(path, encoding="utf-8") as stream:
    config = json.load(stream)
config["BODY_HOST"] = "127.0.0.1"
fd, temporary = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".config.", suffix=".tmp")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(config, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
  else
    echo "[ERROR] Body virtual environment is missing; cannot safely set BODY_HOST to loopback."
    exit 1
  fi

  sudo systemctl enable --now caddy
  sudo systemctl restart caddy
  echo "[OK] Secure Body proxy configured: https://${LAN_HOST}/"
  echo "[OK] Backend is restricted to 127.0.0.1:8766; Caddy provides TLS and login."
  echo "[NOTE] Trust Caddy's local root certificate on each client before using the URL."
}

if [[ "$SECURE_PROXY_SETUP" == "1" ]]; then
  setup_secure_proxy
  exit 0
fi

if [[ "$(uname -s)" == "Linux" ]] && command -v systemctl >/dev/null 2>&1; then
  echo "Secure LAN access setup: ./start_body.sh --setup-secure-proxy"
  if systemctl is-active --quiet caddy 2>/dev/null; then
    echo "[OK] Caddy secure proxy service is active."
  else
    echo "[NOTE] Secure LAN proxy is not active; Body will remain loopback-only."
  fi
fi

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

if ! "$BODY_PYTHON" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco, fastembed, serial" >/dev/null 2>&1; then
  echo "[*] Body dependencies are missing or incomplete. Installing them..."
  "$BODY_PYTHON" -m pip install --upgrade pip
  "$BODY_PYTHON" -m pip install -r body_requirements.txt
else
  echo "[OK] Body dependencies already installed."
fi

if ! "$BODY_PYTHON" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco, fastembed, serial" >/dev/null 2>&1; then
  echo "[ERROR] Body dependencies are still unavailable after installation."
  exit 1
fi
echo "Starting standalone PandoraBOX Body Runtime..."
echo "Body management page: http://127.0.0.1:8766/"
exec "$BODY_PYTHON" -m body_runtime_host
