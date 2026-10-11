#include <Arduino_RouterBridge.h>
#include <Arduino_Modulino.h>
#include <stdio.h>

ModulinoMovement movement;
bool movementReady = false;
uint32_t lastInitAttempt = 0;
uint32_t sequenceNumber = 0;

String readMovementSample() {
  if (!movementReady) {
    return String("{\"available\":false,\"error\":\"modulino_movement_not_detected\"}");
  }
  if (!movement.update()) {
    return String("{\"available\":false,\"error\":\"imu_sample_not_ready\"}");
  }

  char payload[320];
  const int written = snprintf(
      payload, sizeof(payload),
      "{\"available\":true,\"device\":\"modulino_movement_lsm6dsox\","
      "\"frame\":\"imu_sensor\",\"sequence\":%lu,\"timestamp_ms\":%lu,"
      "\"acceleration_g\":[%.5f,%.5f,%.5f],"
      "\"angular_velocity_dps\":[%.5f,%.5f,%.5f]}",
      static_cast<unsigned long>(++sequenceNumber),
      static_cast<unsigned long>(millis()),
      movement.getX(), movement.getY(), movement.getZ(),
      movement.getRoll(), movement.getPitch(), movement.getYaw());
  if (written <= 0 || static_cast<size_t>(written) >= sizeof(payload)) {
    return String("{\"available\":false,\"error\":\"imu_payload_overflow\"}");
  }
  return String(payload);
}

void setup() {
  Modulino.begin();
  movementReady = movement.begin();
  lastInitAttempt = millis();

  Bridge.begin();
  // The callback reads I2C, so execute it in the sketch loop context.
  Bridge.provide_safe("body_imu_read", readMovementSample);
}

void loop() {
  if (!movementReady && millis() - lastInitAttempt >= 2000) {
    lastInitAttempt = millis();
    movementReady = movement.begin();
  }
}
