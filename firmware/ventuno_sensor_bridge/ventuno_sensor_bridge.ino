#ifndef BODY_ENABLE_TOF
#define BODY_ENABLE_TOF 0
#endif

#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>
#include <Arduino_Modulino.h>
#if BODY_ENABLE_TOF
#include <Adafruit_VL53L1X.h>
#endif
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#ifndef BODY_ENABLE_IMU
#define BODY_ENABLE_IMU 1
#endif
#ifndef BODY_ENABLE_ULTRASONIC
#define BODY_ENABLE_ULTRASONIC 1
#endif
#ifndef BODY_ULTRASONIC_CHANNEL_MASK
#define BODY_ULTRASONIC_CHANNEL_MASK 7
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
Arduino_LED_Matrix batteryMatrix;
int batteryDisplayPercent = -1;
int batteryRenderedPercent = -2;
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
#if BODY_ENABLE_TOF
Adafruit_VL53L1X tof;
#endif
bool tofReady = false;
uint32_t lastTofInitAttempt = 0;
uint32_t tofSequence = 0;
uint32_t latestTofAt = 0;
int16_t latestTofDistanceMm = -1;

void setBatteryDisplay(int percent) {
  batteryDisplayPercent = constrain(percent, -1, 100);
}

void renderBatteryDisplay() {
  if (batteryRenderedPercent == batteryDisplayPercent) return;
  batteryRenderedPercent = batteryDisplayPercent;

  uint8_t frame[104] = {};
  if (batteryDisplayPercent >= 0) {
    static const uint8_t digits[10][5] = {
        {7, 5, 5, 5, 7}, {2, 6, 2, 2, 7}, {7, 1, 7, 4, 7},
        {7, 1, 7, 1, 7}, {5, 5, 7, 1, 1}, {7, 4, 7, 1, 7},
        {7, 4, 7, 5, 7}, {7, 1, 1, 1, 1}, {7, 5, 7, 5, 7},
        {7, 5, 7, 1, 7}};
    const bool showPercent = batteryDisplayPercent < 100;
    const int digitCount = batteryDisplayPercent >= 100 ? 3
        : (batteryDisplayPercent >= 10 ? 2 : 1);
    const int textWidth = digitCount * 4 - 1 + (showPercent ? 3 : 0);
    int x = (13 - textWidth) / 2;
    int value = batteryDisplayPercent;
    int divisors[3] = {100, 10, 1};
    for (int d = 0; d < digitCount; ++d) {
      const int digit = value / divisors[3 - digitCount + d] % 10;
      for (int row = 0; row < 5; ++row) {
        for (int col = 0; col < 3; ++col) {
          if (digits[digit][row] & (1U << (2 - col)))
            frame[(row + 1) * 13 + x + col] = 1;
        }
      }
      x += 4;
    }
    if (showPercent) {
      const int percentPixels[5][3] = {
          {1, 0, 0}, {0, 0, 1}, {0, 1, 0}, {1, 0, 0}, {0, 0, 1}};
      for (int row = 0; row < 5; ++row)
        for (int col = 0; col < 3; ++col)
          if (percentPixels[row][col])
            frame[(row + 1) * 13 + x + col] = 1;
    }
  }
  batteryMatrix.draw(frame);
}

static const uint8_t ULTRASONIC_COUNT = 3;
static const uint8_t ultrasonicTriggerPins[ULTRASONIC_COUNT] = {D2, D4, D6};
static const uint8_t ultrasonicEchoPins[ULTRASONIC_COUNT] = {D3, D5, D9};
static const char *ultrasonicNames[ULTRASONIC_COUNT] = {
    "front_left", "front_right", "rear"};
static const uint32_t ULTRASONIC_TRIGGER_INTERVAL_US = 100000;
static const uint32_t ULTRASONIC_ECHO_TIMEOUT_US = 30000;
static const uint32_t ULTRASONIC_STALE_MS = 600;
static const uint8_t ULTRASONIC_CHANNEL_MASK = BODY_ULTRASONIC_CHANNEL_MASK & 0x07;
static_assert(BODY_ULTRASONIC_CHANNEL_MASK >= 0 && BODY_ULTRASONIC_CHANNEL_MASK <= 7,
              "BODY_ULTRASONIC_CHANNEL_MASK must be from 0 to 7");
struct UltrasonicChannel {
  uint32_t sampleAtMs = 0;
  uint32_t sequence = 0;
  uint16_t distanceMm = 0;
  const char *error = "waiting_for_echo";
};
UltrasonicChannel ultrasonicChannels[ULTRASONIC_COUNT];
enum UltrasonicPhase : uint8_t { ULTRASONIC_IDLE, ULTRASONIC_TRIGGER, ULTRASONIC_WAIT_RISE, ULTRASONIC_WAIT_FALL };
UltrasonicPhase ultrasonicPhase = ULTRASONIC_IDLE;
uint8_t activeUltrasonic = 0;
uint8_t nextUltrasonic = 0;
uint32_t ultrasonicPhaseAtUs = 0;
uint32_t ultrasonicEchoRiseUs = 0;
uint32_t ultrasonicNextTriggerUs = 0;
uint32_t ultrasonicSequence = 0;
uint8_t firmwareSetupStage = 0;
uint32_t firmwareLoopSequence = 0;

int nextEnabledUltrasonic(uint8_t start) {
  for (uint8_t offset = 0; offset < ULTRASONIC_COUNT; ++offset) {
    const uint8_t index = (start + offset) % ULTRASONIC_COUNT;
    if (ULTRASONIC_CHANNEL_MASK & (1U << index)) return index;
  }
  return -1;
}

void updateUltrasonic() {
#if BODY_ENABLE_ULTRASONIC
  const uint32_t nowUs = micros();
  if (ultrasonicPhase == ULTRASONIC_IDLE) {
    if (static_cast<int32_t>(nowUs - ultrasonicNextTriggerUs) < 0) return;
    const int selected = nextEnabledUltrasonic(nextUltrasonic);
    if (selected < 0) return;
    activeUltrasonic = static_cast<uint8_t>(selected);
    nextUltrasonic = (activeUltrasonic + 1) % ULTRASONIC_COUNT;
    digitalWrite(ultrasonicTriggerPins[activeUltrasonic], HIGH);
    ultrasonicPhaseAtUs = nowUs;
    ultrasonicNextTriggerUs = nowUs + ULTRASONIC_TRIGGER_INTERVAL_US;
    ultrasonicPhase = ULTRASONIC_TRIGGER;
    return;
  }

  if (ultrasonicPhase == ULTRASONIC_TRIGGER) {
    if (nowUs - ultrasonicPhaseAtUs < 10) return;
    digitalWrite(ultrasonicTriggerPins[activeUltrasonic], LOW);
    ultrasonicPhaseAtUs = nowUs;
    ultrasonicPhase = ULTRASONIC_WAIT_RISE;
    return;
  }

  if (ultrasonicPhase == ULTRASONIC_WAIT_RISE) {
    if (digitalRead(ultrasonicEchoPins[activeUltrasonic]) == HIGH) {
      ultrasonicEchoRiseUs = nowUs;
      ultrasonicPhase = ULTRASONIC_WAIT_FALL;
      return;
    }
    if (nowUs - ultrasonicPhaseAtUs >= ULTRASONIC_ECHO_TIMEOUT_US) {
      ultrasonicChannels[activeUltrasonic].error = "no_echo";
      ultrasonicPhase = ULTRASONIC_IDLE;
    }
    return;
  }

  if (digitalRead(ultrasonicEchoPins[activeUltrasonic]) == LOW) {
    const uint32_t pulseUs = nowUs - ultrasonicEchoRiseUs;
    const uint32_t distanceMm = (pulseUs * 343UL + 1000UL) / 2000UL;
    UltrasonicChannel &channel = ultrasonicChannels[activeUltrasonic];
    if (distanceMm < 20) {
      channel.error = "too_close";
    } else if (distanceMm <= 4000) {
      channel.distanceMm = static_cast<uint16_t>(distanceMm);
      channel.sampleAtMs = millis();
      channel.sequence = ++ultrasonicSequence;
      channel.error = "";
    } else {
      channel.error = "too_far";
    }
    ultrasonicPhase = ULTRASONIC_IDLE;
    return;
  }
  if (nowUs - ultrasonicEchoRiseUs >= ULTRASONIC_ECHO_TIMEOUT_US) {
    ultrasonicChannels[activeUltrasonic].error = "echo_timeout";
    ultrasonicPhase = ULTRASONIC_IDLE;
  }
#endif
}

String readUltrasonicSample() {
#if !BODY_ENABLE_ULTRASONIC
  const char *disabledError = "ultrasonic_disabled";
#else
  const char *disabledError = "channel_disabled";
#endif
  const uint32_t now = millis();
  bool anyFresh = false;
  char channels[600];
  size_t used = 0;
  for (uint8_t i = 0; i < ULTRASONIC_COUNT; ++i) {
    const UltrasonicChannel &channel = ultrasonicChannels[i];
    const bool channelEnabled = BODY_ENABLE_ULTRASONIC
        && (ULTRASONIC_CHANNEL_MASK & (1U << i));
    const bool fresh = channelEnabled && channel.sampleAtMs
        && now - channel.sampleAtMs <= ULTRASONIC_STALE_MS
        && channel.error && channel.error[0] == '\0';
    anyFresh = anyFresh || fresh;
    const int written = snprintf(channels + used, sizeof(channels) - used,
        "%s{\"id\":\"%s\",\"trigger_pin\":\"D%u\",\"echo_pin\":\"D%u\","
        "\"available\":%s,\"distance_mm\":%s,\"timestamp_ms\":%lu,\"sequence\":%lu,\"error\":\"%s\"}",
        i ? "," : "", ultrasonicNames[i],
        i == 0 ? 2 : i == 1 ? 4 : 6, i == 0 ? 3 : i == 1 ? 5 : 9,
        fresh ? "true" : "false", fresh ? String(channel.distanceMm).c_str() : "null",
        static_cast<unsigned long>(channel.sampleAtMs),
        static_cast<unsigned long>(channel.sequence),
        fresh ? "" : (channelEnabled ? channel.error : disabledError));
    if (written <= 0 || static_cast<size_t>(written) >= sizeof(channels) - used) {
      return String("{\"available\":false,\"sensor\":\"hc_sr04_array\",\"error\":\"payload_overflow\"}");
    }
    used += static_cast<size_t>(written);
  }
  String payload = String("{\"available\":") + (anyFresh ? "true" : "false")
      + ",\"sensor\":\"hc_sr04_array\",\"transport\":\"stm32_gpio\","
        "\"timestamp_ms\":" + String(now) + ",\"sequence\":"
      + String(ultrasonicSequence) + ",\"setup_stage\":"
      + String(firmwareSetupStage) + ",\"loop_sequence\":"
      + String(firmwareLoopSequence) + ",\"sensors\":[" + channels + "]}";
  return payload;
}

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
  Bridge.provide_safe("body_ultrasonic_read", readUltrasonicSample);
  Bridge.provide("body_ld2450_read", readLatestLd2450);
  Bridge.provide_safe("body_gps_read", readGpsSample);
  Bridge.provide_safe("body_battery_indicator_set", setBatteryDisplay);
  batteryMatrix.begin();
  renderBatteryDisplay();
  firmwareSetupStage = 1;

#if BODY_ENABLE_ULTRASONIC
  for (uint8_t i = 0; i < ULTRASONIC_COUNT; ++i) {
    if (!(ULTRASONIC_CHANNEL_MASK & (1U << i))) continue;
    firmwareSetupStage = static_cast<uint8_t>(10 + i * 3);
    pinMode(ultrasonicTriggerPins[i], OUTPUT);
    ++firmwareSetupStage;
    digitalWrite(ultrasonicTriggerPins[i], LOW);
    ++firmwareSetupStage;
    pinMode(ultrasonicEchoPins[i], INPUT);
    ++firmwareSetupStage;
  }
  ultrasonicNextTriggerUs = micros();
#endif

  firmwareSetupStage = 30;
  Serial1.begin(GPS_BAUD);
  firmwareSetupStage = 31;

  // The VENTUNO Q's Qwiic connector is on the MCU's Wire1 bus.
#if BODY_ENABLE_IMU
  firmwareSetupStage = 40;
  Modulino.begin(Wire1);
  firmwareSetupStage = 41;
  movementReady = movement.begin();
  lastImuInitAttempt = millis();
  firmwareSetupStage = 42;
#endif
#if BODY_ENABLE_TOF
  firmwareSetupStage = 50;
  tofReady = tof.begin(0x29, &Wire1);
  if (tofReady) {
    tof.setTimingBudget(50);
    tofReady = tof.startRanging();
  }
  lastTofInitAttempt = millis();
  firmwareSetupStage = 51;
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
  firmwareSetupStage = 60;
}

void loop() {
  ++firmwareLoopSequence;
  renderBatteryDisplay();
  while (Serial1.available() > 0) consumeGpsByte(static_cast<uint8_t>(Serial1.read()));
  updateUltrasonic();
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
