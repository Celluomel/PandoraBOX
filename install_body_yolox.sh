#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
YOLOX_VENV="${BODY_YOLOX_VENV:-$HOME/.venvs/yolox-infer}"
YOLOX_PYTHON="$YOLOX_VENV/bin/python"
YOLOX_BIN="$YOLOX_VENV/bin"
MODEL_DIR="${BODY_YOLOX_MODEL_DIR:-$HOME/models/yolox-qairt245/yolox-qnn_dlc-w8a8}"
MODEL_PATH="$MODEL_DIR/yolox.dlc"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "aarch64" ]]; then
  echo "[ERROR] YOLOX QNN install is intended for the Ventuno Q Linux ARM64 host."
  exit 1
fi

PYTHON_BASE="${BODY_YOLOX_BASE_PYTHON:-$(command -v python3.12 || command -v python3)}"
if [[ -z "$PYTHON_BASE" ]]; then
  echo "[ERROR] Install Python 3.12 for ARM64, then rerun this script."
  exit 1
fi
"$PYTHON_BASE" -c 'import sys; assert sys.version_info >= (3, 10) and sys.version_info < (3, 14), sys.version'
if [[ ! -x "$YOLOX_PYTHON" ]]; then
  mkdir -p "$(dirname "$YOLOX_VENV")"
  "$PYTHON_BASE" -m venv "$YOLOX_VENV"
fi

if ! "$YOLOX_PYTHON" -c 'import qai_appbuilder, cv2, numpy' >/dev/null 2>&1; then
  echo "[*] Installing isolated Qualcomm QNN and image dependencies..."
  "$YOLOX_PYTHON" -m pip install --upgrade pip
  "$YOLOX_PYTHON" -m pip install 'qai-appbuilder==2.48.40' 'opencv-python-headless>=4.8,<5' 'numpy>=1.24,<3'
fi

if [[ ! -s "$MODEL_PATH" ]]; then
  echo "[*] Installing Qualcomm AI Hub Models CLI to fetch the precompiled IQ-8275 W8A8 model..."
  "$YOLOX_PYTHON" -m pip install 'qai_hub_models_cli'
  mkdir -p "$MODEL_DIR"
  "$YOLOX_BIN/qai-hub-models" fetch Yolo-X --runtime qnn --precision w8a8 \
    --chipset qualcomm-qcs8275 --sdk-version qairt=2.45 --quiet >"$MODEL_DIR/fetch-path.txt"
  FETCHED_PATH="$(tr -d '\r\n' <"$MODEL_DIR/fetch-path.txt")"
  if [[ -d "$FETCHED_PATH" ]]; then
    FETCHED_PATH="$(find "$FETCHED_PATH" -type f -name '*.dlc' -print -quit)"
  fi
  if [[ -f "$FETCHED_PATH" && "$FETCHED_PATH" != *.dlc ]]; then
    echo "[ERROR] AI Hub returned an unexpected asset: $FETCHED_PATH"
    exit 1
  fi
  if [[ ! -s "$FETCHED_PATH" ]]; then
    FETCHED_PATH="$(find "$MODEL_DIR" "$HOME/.qaihm" -type f -name '*.dlc' -print -quit 2>/dev/null || true)"
  fi
  if [[ -z "$FETCHED_PATH" || ! -s "$FETCHED_PATH" ]]; then
    echo "[ERROR] No QNN DLC downloaded. Run: $YOLOX_BIN/qai-hub-models info Yolo-X"
    exit 1
  fi
  cp "$FETCHED_PATH" "$MODEL_PATH"
fi

"$YOLOX_PYTHON" -c 'import qai_appbuilder, cv2, numpy; print("YOLOX runtime dependencies ready")'
echo "[OK] YOLOX QNN model: $MODEL_PATH"
echo "[OK] YOLOX Python: $YOLOX_PYTHON"
echo "[NOTE] Runtime selection defaults to HTP with explicit CPU fallback if HTP cannot initialize."
