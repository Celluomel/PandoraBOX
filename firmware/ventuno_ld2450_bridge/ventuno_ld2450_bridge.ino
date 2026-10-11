#include <Arduino_RouterBridge.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

// Use UART7 directly so Serial1 remains available for GPS on USART3.
static const uint32_t RADAR_BAUD = 256000;
static const uint32_t FRAME_STALE_MS = 1000;
static const uint8_t FRAME_SIZE = 30;
static const uint8_t HEADER[] = {0xAA, 0xFF, 0x03, 0x00};
static const uint8_t FOOTER[] = {0x55, 0xCC};

uint8_t frameBuffer[FRAME_SIZE];
uint8_t frameLength = 0;
char latestJson[512] = "{\"available\":false,\"targets\":[],\"error\":\"waiting_for_ld2450\"}";
uint32_t latestFrameAt = 0;
uint32_t frameSequence = 0;
const struct device *radarUart = DEVICE_DT_GET(DT_NODELABEL(uart7));

float signedMagnitude(uint16_t value, float scale) {
  const float magnitude = static_cast<float>(value & 0x7FFF);
  return (value & 0x8000) ? magnitude / scale : -magnitude / scale;
}

uint16_t readU16LE(const uint8_t *data) {
  return static_cast<uint16_t>(data[0]) | (static_cast<uint16_t>(data[1]) << 8);
}

void acceptFrame() {
  char targets[390];
  size_t used = 0;
  uint8_t count = 0;
  targets[0] = '\0';

  for (uint8_t slot = 0; slot < 3; ++slot) {
    const uint8_t offset = 4 + slot * 8;
    const uint16_t rawX = readU16LE(&frameBuffer[offset]);
    const uint16_t rawY = readU16LE(&frameBuffer[offset + 2]);
    const uint16_t rawSpeed = readU16LE(&frameBuffer[offset + 4]);
    const uint16_t gate = readU16LE(&frameBuffer[offset + 6]);
    if (!(rawX || rawY || rawSpeed || gate)) continue;

    const int written = snprintf(
        targets + used, sizeof(targets) - used,
        "%s{\"id\":%u,\"x\":%.3f,\"y\":%.3f,\"z\":0,\"vx\":0,\"vy\":0,\"vz\":0,\"radial_speed_mps\":%.2f}",
        count ? "," : "", static_cast<unsigned>(slot + 1),
        signedMagnitude(rawX, 1000.0f), signedMagnitude(rawY, 1000.0f),
        signedMagnitude(rawSpeed, 100.0f));
    if (written <= 0 || static_cast<size_t>(written) >= sizeof(targets) - used) return;
    used += static_cast<size_t>(written);
    ++count;
  }

  ++frameSequence;
  snprintf(latestJson, sizeof(latestJson),
           "{\"available\":true,\"frame\":\"body\",\"sequence\":%lu,\"targets\":[%s]}",
           static_cast<unsigned long>(frameSequence), targets);
  latestFrameAt = millis();
}

void feedRadarByte(uint8_t value) {
  if (frameLength == 0) {
    if (value == HEADER[0]) frameBuffer[frameLength++] = value;
    return;
  }
  frameBuffer[frameLength++] = value;
  if (frameLength <= sizeof(HEADER) && value != HEADER[frameLength - 1]) {
    frameLength = value == HEADER[0] ? 1 : 0;
    if (frameLength) frameBuffer[0] = value;
    return;
  }
  if (frameLength < FRAME_SIZE) return;
  if (frameBuffer[28] == FOOTER[0] && frameBuffer[29] == FOOTER[1]) acceptFrame();
  // Resynchronize from the end of this frame. Frames are fixed-length and
  // the 10 Hz report cadence means one bad frame cannot stall the reader.
  frameLength = 0;
}

String readLatestLd2450() {
  if (!latestFrameAt || millis() - latestFrameAt > FRAME_STALE_MS) {
    return String("{\"available\":false,\"targets\":[],\"error\":\"stale_or_missing_frame\"}");
  }
  return String(latestJson);
}

void setup() {
  const struct uart_config radarConfig = {
      .baudrate = RADAR_BAUD,
      .parity = UART_CFG_PARITY_NONE,
      .stop_bits = UART_CFG_STOP_BITS_1,
      .data_bits = UART_CFG_DATA_BITS_8,
      .flow_ctrl = UART_CFG_FLOW_CTRL_NONE,
  };
  if (!device_is_ready(radarUart) || uart_configure(radarUart, &radarConfig) != 0) {
    strncpy(latestJson, "{\"available\":false,\"targets\":[],\"error\":\"uart7_unavailable\"}", sizeof(latestJson));
  }
  Bridge.begin();
  Bridge.provide("body_ld2450_read", readLatestLd2450);
}

void loop() {
  if (device_is_ready(radarUart)) {
    unsigned char value;
    while (uart_poll_in(radarUart, &value) == 0) feedRadarByte(value);
  }
  delay(1);
}
