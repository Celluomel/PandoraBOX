#!/usr/bin/env bash
set -euo pipefail

GENIEX_QAIRT="${HOME}/.local/share/geniex/qairt/htp-files"
GENIEX_SKEL="${GENIEX_QAIRT}/libQnnHtpV75Skel.so"
DSP_LINK="/usr/lib/dsp/cdsp/libQnnHtpV75Skel.so.2"

if [[ ! -s "$GENIEX_SKEL" ]]; then
  exit 0
fi

CURRENT_SKEL="$(readlink -f "$DSP_LINK" 2>/dev/null || true)"
YOLOX_SKEL_MARKER="${HOME}/.venvs/yolox-infer/"
if [[ "$CURRENT_SKEL" != *"$YOLOX_SKEL_MARKER"* ]]; then
  exit 0
fi

BACKUP_DIR="${HOME}/.local/share/pandorabox/runtime-backups"
mkdir -p "$BACKUP_DIR"
ln -sfn "$CURRENT_SKEL" "$BACKUP_DIR/libQnnHtpV75Skel.so.2.yolox"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  ln -sfn "$GENIEX_SKEL" "$DSP_LINK"
elif command -v sudo >/dev/null 2>&1; then
  sudo ln -sfn "$GENIEX_SKEL" "$DSP_LINK"
else
  echo "[ERROR] sudo is required to restore the GenieX HTP v75 DSP skeleton." >&2
  exit 1
fi

echo "[OK] GenieX HTP skeleton restored; YOLOX keeps its private AppBuilder path."
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet geniex.service; then
  systemctl --user restart geniex.service
fi
