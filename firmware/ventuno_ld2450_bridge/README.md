# VENTUNO Q local LD2450 Bridge

This sketch reads the HLK-LD2450 256000-baud target frames on the VENTUNO Q
STM32 hardware UART (`Serial1`) and provides the most recent compact JSON frame
to the Linux Body Runtime through `Arduino_RouterBridge`. Sensor measurements
stay on the board; no LAN sensor gateway is used.

## Wiring

The currently installed Arduino VENTUNO Q board overlay exposes `Serial1` as
USART3 on D0/D1. Connect LD2450 TX to D0/RX and sensor GND to board GND only if
those pins are free. The current project wiring assigns D0/D1 to GPS, so do not
flash/use this sketch with that wiring unchanged. We must first either move GPS
to another independent interface or update the board overlay to expose UART7
on D7/D8 as a second serial device. The radar TX is 3.3 V logic; do not connect
its 5 V supply pin to a GPIO. Power the radar from the board's protected 5 V
rail only if the module label/datasheet confirms 5 V input.

## Install

After resolving the UART pin conflict above, open the sketch in Arduino App Lab
with VENTUNO Q selected, build, and deploy it to the MCU. It uses the stock
Arduino Router service and does not replace Linux, the Body service, or FNK0031
firmware. The provided RPC method is
`body_ld2450_read()` and returns `available`, `sequence`, `frame`, and up to
three metric targets. Linux reads the latest sample on demand, so UART capture
continues even between Body polls.

The Body GUI transport **Ventuno STM32 UART · local Bridge** is only usable on
the VENTUNO Q itself. On Jetson, use **USB-UART · local to Body host** instead.
