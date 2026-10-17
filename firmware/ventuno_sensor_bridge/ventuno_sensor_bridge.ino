#include <Arduino_RouterBridge.h>
#include <Arduino_Modulino.h>
#include <Adafruit_VL53L1X.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#ifndef BODY_ENABLE_TOF
#define BODY_ENABLE_TOF 0
#endif
#ifndef BODY_ENABLE_IMU
#define BODY_ENABLE_IMU 1
#endif
#ifndef BODY_RADAR_BAUD
#define BODY_RADAR_BAUD 256000
#endif
#ifndef BODY_GPS_BAUD
#define BODY_GPS_BAUD 38400
#endif

// Qwiic Modulino Movement and the LD2450 share one STM32 sketch while keeping
// their existing Linux Router Bridge RPC names stable.
ModulinoMovement movement;
bool movementReady = false;
uint32_t lastImuInitAttempt = 0;
uint32_t lastImuUpdateAt = 0;
uint32_t imuSequence = 0;
uint32_t latestImuAt = 0;
bool latestImuSampleValid = false;
float latestAccelX = 0.0f;
float latestAccelY = 0.0f;
float latestAccelZ = 0.0f;
float latestGyroX = 0.0f;
float latestGyroY = 0.0f;
float latestGyroZ = 0.0f;
float latestRollDeg = 0.0f;
float latestPitchDeg = 0.0f;
float latestYawRelativeDeg = 0.0f;
float gyroBiasX = 0.0f;
float gyroBiasY = 0.0f;
float gyroBiasZ = 0.0f;
float previousAccelNorm = 1.0f;
float latestAccelNorm = 1.0f;
float latestAccelJerk = 0.0f;
uint32_t stationarySince = 0;
bool attitudeFilterReady = false;
bool gyroBiasReady = false;
bool calibrationStable = false;
bool gravityReferenceValid = false;
Adafruit_VL53L1X tof;
bool tofReady = false;
uint32_t lastTofInitAttempt = 0;
uint32_t tofSequence = 0;
uint32_t latestTofAt = 0;
int16_t latestTofDistanceMm = -1;

static const uint32_t GPS_BAUD = BODY_GPS_BAUD;
static const uint16_t GPS_STALE_MS = 3000;
static const uint16_t GPS_GSV_STALE_MS = 6000;
static const uint8_t GPS_GSV_CAPACITY = 16;
char gpsLine[128];
uint8_t gpsLineLength = 0;
char latestNmea[128] = "";
char latestGga[128] = "";
char gpsGsvLines[GPS_GSV_CAPACITY][128] = {};
uint32_t gpsGsvAt[GPS_GSV_CAPACITY] = {};
uint8_t gpsGsvNext = 0;
uint8_t gpsGsvCount = 0;
uint32_t gpsBytesReceived = 0;
uint32_t gpsValidSentences = 0;
uint32_t gpsChecksumErrors = 0;
uint32_t gpsSequence = 0;
uint32_t latestGpsAt = 0;
uint32_t latestGgaAt = 0;

static const uint32_t RADAR_BAUD = BODY_RADAR_BAUD;
static const uint32_t FRAME_STALE_MS = 1000;
static const uint8_t FRAME_SIZE = 30;
static const uint8_t HEADER[] = {0xAA, 0xFF, 0x03, 0x00};
static const uint8_t FOOTER[] = {0x55, 0xCC};
static const uint16_t RADAR_RX_BUFFER_SIZE = 512;

uint8_t frameBuffer[FRAME_SIZE];
uint8_t frameLength = 0;
uint8_t radarRxBuffer[RADAR_RX_BUFFER_SIZE];
volatile uint16_t radarRxHead = 0;
volatile uint16_t radarRxTail = 0;
volatile uint32_t radarRxOverflows = 0;
char latestJson[512] = "{\"available\":false,\"targets\":[],\"error\":\"waiting_for_ld2450\"}";
uint32_t latestFrameAt = 0;
uint32_t frameSequence = 0;
uint32_t radarBytesReceived = 0;
uint32_t radarHeaderMatches = 0;
uint32_t radarHeaderRejects = 0;
uint32_t radarHeaderComplete = 0;
uint32_t radarBadFooters = 0;
uint8_t radarTail[16] = {};
uint8_t radarTailNext = 0;
uint8_t radarLastByte = 0;
bool radarUartReady = false;
int radarUartConfigResult = -1;
int radarUartIrqResult = -1;
const struct device *radarUart = DEVICE_DT_GET(DT_NODELABEL(uart7));

void radarUartIsr(const struct device *dev, void *userData) {
  (void)userData;
  if (!uart_irq_update(dev)) return;
  while (uart_irq_rx_ready(dev)) {
    uint8_t received[32];
    const int count = uart_fifo_read(dev, received, sizeof(received));
    if (count <= 0) break;
    for (int i = 0; i < count; ++i) {
      const uint16_t next = (radarRxHead + 1) % RADAR_RX_BUFFER_SIZE;
      if (next == radarRxTail) {
        ++radarRxOverflows;
        continue;
      }
      radarRxBuffer[radarRxHead] = received[i];
      radarRxHead = next;
    }
  }
}

float signedMagnitude(uint16_t value, float scale) {
  const float magnitude = static_cast<float>(value & 0x7FFF);
  return (value & 0x8000) ? magnitude / scale : -magnitude / scale;
}

uint16_t readU16LE(const uint8_t *data) {
  return static_cast<uint16_t>(data[0]) | (static_cast<uint16_t>(data[1]) << 8);
}

float wrapDegrees(float angle) {
  while (angle > 180.0f) angle -= 360.0f;
  while (angle < -180.0f) angle += 360.0f;
  return angle;
}

void updateImuAttitude(float ax, float ay, float az, float gx, float gy, float gz,
                       uint32_t now) {
  const float dt = latestImuAt ? (now - latestImuAt) / 1000.0f : 0.016f;
  if (!(dt > 0.0f && dt <= 0.1f)) return;

  const float accelNorm = sqrtf(ax * ax + ay * ay + az * az);
  const float gyroNorm = sqrtf(gx * gx + gy * gy + gz * gz);
  const float accelJerk = fabsf(accelNorm - previousAccelNorm) / dt;
  previousAccelNorm = accelNorm;
  latestAccelNorm = accelNorm;
  latestAccelJerk = accelJerk;

  const bool nearGravity = accelNorm >= 0.88f && accelNorm <= 1.12f;
  const bool gravityUsable = nearGravity && accelJerk <= 3.5f;
  gravityReferenceValid = gravityUsable;
  const bool stationaryCandidate = accelNorm >= 0.96f && accelNorm <= 1.04f
      && gyroNorm <= 2.0f && accelJerk <= 0.35f;

  if (stationaryCandidate) {
    if (!stationarySince) stationarySince = now;
    const float elapsed = (now - stationarySince) / 1000.0f;
    if (elapsed >= 3.0f) {
      const float biasGain = fminf(0.02f, dt / 10.0f);
      gyroBiasX += biasGain * (gx - gyroBiasX);
      gyroBiasY += biasGain * (gy - gyroBiasY);
      gyroBiasZ += biasGain * (gz - gyroBiasZ);
      gyroBiasReady = true;
    }
  } else {
    stationarySince = 0;
  }
  calibrationStable = gyroBiasReady && stationarySince != 0
      && now - stationarySince >= 500;

  const float correctedGx = gx - gyroBiasX;
  const float correctedGy = gy - gyroBiasY;
  const float correctedGz = gz - gyroBiasZ;
  const float accelRoll = atan2f(ay, az) * 57.2957795f;
  const float accelPitch = atan2f(-ax, hypotf(ay, az)) * 57.2957795f;

  if (!attitudeFilterReady) {
    latestRollDeg = accelRoll;
    latestPitchDeg = accelPitch;
    attitudeFilterReady = gravityUsable;
  } else {
    latestRollDeg = wrapDegrees(latestRollDeg + correctedGx * dt);
    latestPitchDeg = wrapDegrees(latestPitchDeg + correctedGy * dt);
    latestYawRelativeDeg = wrapDegrees(latestYawRelativeDeg + correctedGz * dt);
    if (gravityUsable) {
      const float correction = 1.0f - expf(-dt / 1.5f);
      latestRollDeg = wrapDegrees(latestRollDeg
          + correction * wrapDegrees(accelRoll - latestRollDeg));
      latestPitchDeg = wrapDegrees(latestPitchDeg
          + correction * wrapDegrees(accelPitch - latestPitchDeg));
    }
  }
}

String readMovementSample() {
#if !BODY_ENABLE_IMU
  return String("{\"available\":false,\"error\":\"imu_disabled_for_sensor_test\"}");
#else
  if (!movementReady) {
    return String("{\"available\":false,\"error\":\"modulino_movement_not_detected\"}");
  }
  if (!latestImuSampleValid || !latestImuAt || millis() - latestImuAt > 1000) {
    return String("{\"available\":false,\"error\":\"imu_sample_stale\"}");
  }

  char payload[640];
  const int written = snprintf(
      payload, sizeof(payload),
      "{\"available\":true,\"device\":\"modulino_movement_lsm6dsox\","
      "\"frame\":\"imu_sensor\",\"sequence\":%lu,\"timestamp_ms\":%lu,"
      "\"acceleration_g\":[%.5f,%.5f,%.5f],"
      "\"angular_velocity_dps\":[%.5f,%.5f,%.5f],"
      "\"roll_deg\":%.4f,\"pitch_deg\":%.4f,\"yaw_relative_deg\":%.4f,"
      "\"attitude_valid\":%s,\"gravity_reference_valid\":%s,"
      "\"gyro_bias_ready\":%s,\"calibration_stable\":%s,"
      "\"acceleration_norm_g\":%.4f,\"acceleration_jerk_gps\":%.4f,"
      "\"yaw_rate_dps\":%.4f,"
      "\"motion_state\":\"%s\"}",
      static_cast<unsigned long>(imuSequence),
      static_cast<unsigned long>(latestImuAt),
      latestAccelX, latestAccelY, latestAccelZ,
      latestGyroX, latestGyroY, latestGyroZ,
      latestRollDeg, latestPitchDeg, latestYawRelativeDeg,
      attitudeFilterReady ? "true" : "false",
      gravityReferenceValid ? "true" : "false",
      gyroBiasReady ? "true" : "false", calibrationStable ? "true" : "false",
      latestAccelNorm, latestAccelJerk, latestGyroZ - gyroBiasZ,
      calibrationStable ? "stationary" : (latestAccelJerk > 3.5f ? "linear_acceleration"
          : (sqrtf(latestGyroX * latestGyroX + latestGyroY * latestGyroY
                   + latestGyroZ * latestGyroZ) > 2.0f ? "turning" : "moving")));
  if (written <= 0 || static_cast<size_t>(written) >= sizeof(payload)) {
    return String("{\"available\":false,\"error\":\"imu_payload_overflow\"}");
  }
  return String(payload);
#endif
}

String readTofSample() {
  if (!tofReady) {
    return String("{\"available\":false,\"sensor\":\"vl53l1x\",\"error\":\"sensor_not_detected\"}");
  }
  if (latestTofDistanceMm < 0 || !latestTofAt || millis() - latestTofAt > 1000) {
    return String("{\"available\":false,\"sensor\":\"vl53l1x\",\"frame\":\"body_front\",\"error\":\"no_valid_range\"}");
  }
  char payload[240];
  snprintf(payload, sizeof(payload),
           "{\"available\":true,\"sensor\":\"cqrobot_vl53l1x\",\"frame\":\"body_front\","
           "\"direction\":\"front\",\"sequence\":%lu,\"timestamp_ms\":%lu,\"distance_mm\":%d}",
           static_cast<unsigned long>(tofSequence),
           static_cast<unsigned long>(latestTofAt), latestTofDistanceMm);
  return String(payload);
}

void acceptGpsLine() {
  if (gpsLineLength < 7 || gpsLine[0] != '$') return;
  char *checksum = strchr(gpsLine, '*');
  if (!checksum || !checksum[1] || !checksum[2]) {
    ++gpsChecksumErrors;
    return;
  }
  unsigned int expected = 0;
  if (sscanf(checksum + 1, "%2x", &expected) != 1) {
    ++gpsChecksumErrors;
    return;
  }
  uint8_t actual = 0;
  for (char *cursor = gpsLine + 1; cursor < checksum; ++cursor) actual ^= *cursor;
  if (actual != expected) {
    ++gpsChecksumErrors;
    return;
  }
  *checksum = '\0';
  strncpy(latestNmea, gpsLine, sizeof(latestNmea) - 1);
  latestNmea[sizeof(latestNmea) - 1] = '\0';
  ++gpsValidSentences;
  ++gpsSequence;
  latestGpsAt = millis();
  char *identifierEnd = strchr(gpsLine, ',');
  if (identifierEnd && identifierEnd - gpsLine >= 6
      && memcmp(identifierEnd - 3, "GGA", 3) == 0) {
    strncpy(latestGga, gpsLine, sizeof(latestGga) - 1);
    latestGga[sizeof(latestGga) - 1] = '\0';
    latestGgaAt = latestGpsAt;
  } else if (identifierEnd && identifierEnd - gpsLine >= 6
             && memcmp(identifierEnd - 3, "GSV", 3) == 0) {
    strncpy(gpsGsvLines[gpsGsvNext], gpsLine, sizeof(gpsGsvLines[0]) - 1);
    gpsGsvLines[gpsGsvNext][sizeof(gpsGsvLines[0]) - 1] = '\0';
    gpsGsvAt[gpsGsvNext] = latestGpsAt;
    gpsGsvNext = (gpsGsvNext + 1) % GPS_GSV_CAPACITY;
    if (gpsGsvCount < GPS_GSV_CAPACITY) ++gpsGsvCount;
  }
}

void consumeGpsByte(uint8_t value) {
  ++gpsBytesReceived;
  if (value == '$') {
    gpsLineLength = 0;
    gpsLine[gpsLineLength++] = '$';
    return;
  }
  if (!gpsLineLength) return;
  if (value == '\n') {
    gpsLine[gpsLineLength] = '\0';
    acceptGpsLine();
    gpsLineLength = 0;
    return;
  }
  if (value == '\r') return;
  if (gpsLineLength + 1 >= sizeof(gpsLine)) {
    gpsLineLength = 0;
    return;
  }
  gpsLine[gpsLineLength++] = static_cast<char>(value);
}

String readGpsSample() {
  const bool fresh = latestGgaAt && millis() - latestGgaAt <= GPS_STALE_MS;
  char payload[2400];
  int used = snprintf(payload, sizeof(payload),
           "{\"available\":%s,\"transport\":\"Serial1_USART3_D0_D1\","
           "\"baudrate\":%lu,\"bytes_received\":%lu,\"valid_sentences\":%lu,"
           "\"checksum_errors\":%lu,\"sequence\":%lu,\"age_ms\":%lu,"
           "\"latest_nmea\":\"%s\",\"latest_gga\":\"%s\",\"latest_gsv\":[",
           fresh ? "true" : "false", static_cast<unsigned long>(GPS_BAUD),
           static_cast<unsigned long>(gpsBytesReceived),
           static_cast<unsigned long>(gpsValidSentences),
           static_cast<unsigned long>(gpsChecksumErrors),
           static_cast<unsigned long>(gpsSequence),
           latestGgaAt ? static_cast<unsigned long>(millis() - latestGgaAt) : 0UL,
           latestNmea, latestGga);
  if (used <= 0 || static_cast<size_t>(used) >= sizeof(payload)) {
    return String("{\"available\":false,\"error\":\"gps_payload_overflow\"}");
  }
  bool first = true;
  const uint32_t now = millis();
  for (uint8_t i = 0; i < gpsGsvCount; ++i) {
    if (!gpsGsvAt[i] || now - gpsGsvAt[i] > GPS_GSV_STALE_MS) continue;
    const int written = snprintf(payload + used, sizeof(payload) - used,
                                 "%s\"%s\"", first ? "" : ",", gpsGsvLines[i]);
    if (written <= 0 || static_cast<size_t>(written) >= sizeof(payload) - used) {
      return String("{\"available\":false,\"error\":\"gps_payload_overflow\"}");
    }
    used += written;
    first = false;
  }
  const int written = snprintf(payload + used, sizeof(payload) - used,
                               "],\"error\":\"%s\"}",
                               fresh ? "" : (gpsBytesReceived ? "waiting_for_fresh_gga" : "no_uart_bytes"));
  if (written <= 0 || static_cast<size_t>(written) >= sizeof(payload) - used) {
    return String("{\"available\":false,\"error\":\"gps_payload_overflow\"}");
  }
  return String(payload);
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
    if (value == HEADER[0]) {
      ++radarHeaderMatches;
      frameBuffer[frameLength++] = value;
    }
    return;
  }
  frameBuffer[frameLength++] = value;
  if (frameLength <= sizeof(HEADER) && value != HEADER[frameLength - 1]) {
    ++radarHeaderRejects;
    frameLength = value == HEADER[0] ? 1 : 0;
    if (frameLength) frameBuffer[0] = value;
    return;
  }
  if (frameLength == sizeof(HEADER)) ++radarHeaderComplete;
  if (frameLength < FRAME_SIZE) return;
  if (frameBuffer[28] == FOOTER[0] && frameBuffer[29] == FOOTER[1]) {
    acceptFrame();
  } else {
    ++radarBadFooters;
  }
  frameLength = 0;
}

void consumeRadarByte(uint8_t value) {
  ++radarBytesReceived;
  radarLastByte = value;
  radarTail[radarTailNext] = value;
  radarTailNext = (radarTailNext + 1) % sizeof(radarTail);
  feedRadarByte(value);
}

String readLatestLd2450() {
  if (!latestFrameAt || millis() - latestFrameAt > FRAME_STALE_MS) {
    char diagnostic[480];
    char tailHex[16 * 3 + 1];
    size_t tailUsed = 0;
    for (uint8_t i = 0; i < sizeof(radarTail); ++i) {
      const uint8_t index = (radarTailNext + i) % sizeof(radarTail);
      const int written = snprintf(tailHex + tailUsed, sizeof(tailHex) - tailUsed,
                                   "%s%02X", i ? " " : "", radarTail[index]);
      if (written <= 0 || static_cast<size_t>(written) >= sizeof(tailHex) - tailUsed) break;
      tailUsed += static_cast<size_t>(written);
    }
    snprintf(diagnostic, sizeof(diagnostic),
             "{\"available\":false,\"targets\":[],\"error\":\"stale_or_missing_frame\","
             "\"uart_ready\":%s,\"uart_config_result\":%d,\"baudrate\":%lu,"
             "\"rx_mode\":\"%s\",\"rx_overflows\":%lu,"
             "\"bytes_received\":%lu,\"header_starts\":%lu,\"header_complete\":%lu,"
             "\"header_rejects\":%lu,\"bad_footers\":%lu,\"partial_frame_bytes\":%u,"
             "\"last_byte_hex\":\"%02X\",\"last_bytes_hex\":\"%s\"}",
             radarUartReady ? "true" : "false", radarUartConfigResult,
             static_cast<unsigned long>(RADAR_BAUD),
             radarUartIrqResult == 0 ? "irq" : "poll", static_cast<unsigned long>(radarRxOverflows),
             static_cast<unsigned long>(radarBytesReceived),
             static_cast<unsigned long>(radarHeaderMatches),
             static_cast<unsigned long>(radarHeaderComplete),
             static_cast<unsigned long>(radarHeaderRejects),
             static_cast<unsigned long>(radarBadFooters), frameLength, radarLastByte, tailHex);
    return String(diagnostic);
  }
  return String(latestJson);
}

void setup() {
  // Register the RPC surface before probing I2C or configuring peripherals so
  // a missing or slow sensor cannot hide every method from the Linux Body.
  Bridge.begin();
  Bridge.provide_safe("body_imu_read", readMovementSample);
  Bridge.provide_safe("body_tof_read", readTofSample);
  Bridge.provide("body_ld2450_read", readLatestLd2450);
  Bridge.provide_safe("body_gps_read", readGpsSample);

  Serial1.begin(GPS_BAUD);

  // The VENTUNO Q's Qwiic connector is on the MCU's Wire1 bus.
#if BODY_ENABLE_IMU
  Modulino.begin(Wire1);
  movementReady = movement.begin();
  lastImuInitAttempt = millis();
#endif
#if BODY_ENABLE_TOF
  tofReady = tof.begin(0x29, &Wire1);
  if (tofReady) {
    tof.setTimingBudget(50);
    tofReady = tof.startRanging();
  }
  lastTofInitAttempt = millis();
#endif

  const struct uart_config radarConfig = {
      .baudrate = RADAR_BAUD,
      .parity = UART_CFG_PARITY_NONE,
      .stop_bits = UART_CFG_STOP_BITS_1,
      .data_bits = UART_CFG_DATA_BITS_8,
      .flow_ctrl = UART_CFG_FLOW_CTRL_NONE,
  };
  radarUartReady = device_is_ready(radarUart);
  if (radarUartReady) radarUartConfigResult = uart_configure(radarUart, &radarConfig);
  if (radarUartReady && radarUartConfigResult == 0) {
    radarUartIrqResult = uart_irq_callback_user_data_set(radarUart, radarUartIsr, nullptr);
    if (radarUartIrqResult == 0) uart_irq_rx_enable(radarUart);
  }
  if (!radarUartReady || radarUartConfigResult != 0) {
    strncpy(latestJson, "{\"available\":false,\"targets\":[],\"error\":\"uart7_unavailable\"}", sizeof(latestJson));
  }

}

void loop() {
  while (Serial1.available() > 0) consumeGpsByte(static_cast<uint8_t>(Serial1.read()));
#if BODY_ENABLE_IMU
  if (!movementReady && millis() - lastImuInitAttempt >= 2000) {
    lastImuInitAttempt = millis();
    movementReady = movement.begin();
  }
  if (movementReady && millis() - lastImuUpdateAt >= 16) {
    lastImuUpdateAt = millis();
    if (movement.update()) {
      latestAccelX = movement.getX();
      latestAccelY = movement.getY();
      latestAccelZ = movement.getZ();
      latestGyroX = movement.getRoll();
      latestGyroY = movement.getPitch();
      latestGyroZ = movement.getYaw();
      updateImuAttitude(latestAccelX, latestAccelY, latestAccelZ,
                        latestGyroX, latestGyroY, latestGyroZ, millis());
      latestImuAt = millis();
      ++imuSequence;
      latestImuSampleValid = isfinite(latestAccelX) && isfinite(latestAccelY)
          && isfinite(latestAccelZ) && isfinite(latestGyroX)
          && isfinite(latestGyroY) && isfinite(latestGyroZ);
    }
  }
#endif
#if BODY_ENABLE_TOF
  if (!tofReady && millis() - lastTofInitAttempt >= 2000) {
    lastTofInitAttempt = millis();
    tofReady = tof.begin(0x29, &Wire1);
    if (tofReady) {
      tof.setTimingBudget(50);
      tofReady = tof.startRanging();
    }
  }
  if (tofReady && tof.dataReady()) {
    const int16_t distance = tof.distance();
    if (distance > 0) {
      latestTofDistanceMm = distance;
      latestTofAt = millis();
      ++tofSequence;
    }
    tof.clearInterrupt();
  }
#endif
  if (radarUartIrqResult == 0) {
    while (radarRxTail != radarRxHead) {
      const uint8_t value = radarRxBuffer[radarRxTail];
      radarRxTail = (radarRxTail + 1) % RADAR_RX_BUFFER_SIZE;
      consumeRadarByte(value);
    }
  } else if (device_is_ready(radarUart)) {
    unsigned char value;
    while (uart_poll_in(radarUart, &value) == 0) {
      consumeRadarByte(value);
    }
  }
  delay(1);
}
