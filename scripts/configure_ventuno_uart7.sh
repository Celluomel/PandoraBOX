#!/usr/bin/env bash
set -euo pipefail

core_root="${HOME}/.arduino15/packages/arduino/hardware/zephyr"
mapfile -t overlays < <(find "$core_root" -path '*/variants/arduino_ventuno_q_stm32h5f5xx/arduino_ventuno_q_stm32h5f5xx.overlay' -type f | sort -V)
if [[ ${#overlays[@]} -eq 0 ]]; then
  echo "VENTUNO Q Zephyr board overlay not found under $core_root" >&2
  exit 1
fi

overlay="${overlays[-1]}"
serials_line='serials = <&usart3>;'
serials_uart7_line='serials = <&usart3 &uart7>;'
if grep -Fq "$serials_uart7_line" "$overlay" && grep -Fq '&uart7 {' "$overlay"; then
  echo "UART7 already exposed as Serial2 in $overlay"
  exit 0
fi
if ! grep -Fq "$serials_line" "$overlay"; then
  echo "Expected default USART3 serial mapping was not found; refusing to patch $overlay" >&2
  exit 1
fi

backup="${overlay}.pandorabox-pre-uart7.bak"
if [[ ! -e "$backup" ]]; then
  cp -p "$overlay" "$backup"
fi

sed -i "s/${serials_line}/${serials_uart7_line}/" "$overlay"
cat >> "$overlay" <<'EOF'

/* PandoraBOX: expose the Ventuno Q JDIGITAL UART7 pins as Arduino Serial2. */
&uart7 {
    pinctrl-0 = <&uart7_tx_pb4 &uart7_rx_pb3>;
    pinctrl-names = "default";
    current-speed = <256000>;
    status = "okay";
};
EOF

echo "Configured Serial2=UART7 (D8/TX, D7/RX) in $overlay"
echo "Original overlay backup: $backup"
