# VENTUNO Q local LD2450 Bridge

This sketch reads the HLK-LD2450 256000-baud target frames on the VENTUNO Q
STM32 hardware UART (Zephyr UART7) and provides the most recent compact JSON frame
to the Linux Body Runtime through `Arduino_RouterBridge`. Sensor measurements
stay on the board; no LAN sensor gateway is used.

## Wiring

Run `scripts/configure_ventuno_uart7.sh` once on the Ventuno before compiling.
It preserves the existing USART3 mapping (`Serial1`, D0/D1 for GPS), and enables
direct UART7 access on D7/D8. Connect LD2450 TX to D7/RX, optional LD2450 RX to
D8/TX, and sensor GND to board GND. The radar TX is 3.3 V logic; do not connect
its 5 V supply pin to a GPIO. Power the radar from the board's protected 5 V
rail only if the module label/datasheet confirms 5 V input.

## Install

After the helper configures UART7, compile with
`arduino-cli compile --fqbn arduino:zephyr:ventunoq firmware/ventuno_ld2450_bridge`.
The sketch uses the stock Arduino Router service and does not replace Linux, the
Body service, or FNK0031 firmware. The provided RPC method is
`body_ld2450_read()` and returns `available`, `sequence`, `frame`, and up to
three metric targets. Linux reads the latest sample on demand, so UART capture
continues even between Body polls.

The Body GUI transport **Ventuno STM32 UART · local Bridge** is only usable on
the VENTUNO Q itself. On Jetson, use **USB-UART · local to Body host** instead.
