#!/usr/bin/env bash
set -euo pipefail

core_root="${HOME}/.arduino15/packages/arduino/hardware/zephyr"
mapfile -t overlays < <(find "$core_root" -path '*/variants/arduino_ventuno_q_stm32h5f5xx/arduino_ventuno_q_stm32h5f5xx.overlay' -type f | sort -V)
if [[ ${#overlays[@]} -eq 0 ]]; then
  echo "VENTUNO Q Zephyr board overlay not found under $core_root" >&2
  exit 1
fi

overlay="${overlays[-1]}"
if grep -Fq '/* PandoraBOX: enable LD2450 UART7 on JDIGITAL. */' "$overlay"; then
  echo "UART7 already enabled in $overlay"
  exit 0
fi

backup="${overlay}.pandorabox-pre-uart7.bak"
if [[ ! -e "$backup" ]]; then
  cp -p "$overlay" "$backup"
fi

cat >> "$overlay" <<'EOF'

/* PandoraBOX: enable LD2450 UART7 on JDIGITAL. */
&uart7 {
    pinctrl-0 = <&uart7_tx_pb4 &uart7_rx_pb3>;
    pinctrl-names = "default";
    current-speed = <256000>;
    status = "okay";
};
EOF

echo "Enabled direct Zephyr UART7 access (D8/TX, D7/RX) in $overlay"
echo "Original overlay backup: $backup"
