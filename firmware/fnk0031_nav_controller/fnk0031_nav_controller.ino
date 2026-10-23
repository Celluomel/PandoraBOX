#include <FNHR.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

FNHR robot;

static const unsigned long SERIAL_BAUD = 115200;
static const unsigned long ACTION_WATCHDOG_MS = 1200;
static const size_t LINE_CAPACITY = 64;

char lineBuffer[LINE_CAPACITY];
size_t lineLength = 0;
bool lineOverflow = false;
bool actionActive = false;
unsigned long lastActionCompletedAt = 0;

static bool parseFinite(char *text, float &value) {
  char *end = nullptr;
  value = static_cast<float>(strtod(text, &end));
  return end != text && *end == '\0' && isfinite(value);
}

static void runAction(const char *name) {
  Serial.print("STARTED ");
  Serial.println(name);
  Serial.flush();

  if (strcmp(name, "forward") == 0) robot.CrawlForward();
  else if (strcmp(name, "backward") == 0) robot.CrawlBackward();
  else if (strcmp(name, "left") == 0) robot.CrawlLeft();
  else if (strcmp(name, "right") == 0) robot.CrawlRight();
  else if (strcmp(name, "turn_left") == 0) robot.TurnLeft();
  else if (strcmp(name, "turn_right") == 0) robot.TurnRight();
  else return;

  lastActionCompletedAt = millis();
  actionActive = true;
  Serial.print("DONE ");
  Serial.println(name);
}

static void handleCommand(char *line) {
  if (strcmp(line, "PING") == 0) {
    Serial.println("PONG FNK0031_NAV_V2");
    return;
  }
  if (strcmp(line, "CMD state") == 0) {
    Serial.print("STATE ");
    Serial.print(millis());
    for (int leg = 1; leg <= 6; ++leg) {
      float x, y, z, jointA, jointB, jointC;
      if (!robot.GetEstimatedLegState(leg, x, y, z, jointA, jointB, jointC)) {
        Serial.println("ERROR state_unavailable");
        return;
      }
      Serial.print(' '); Serial.print(x, 2);
      Serial.print(' '); Serial.print(y, 2);
      Serial.print(' '); Serial.print(z, 2);
      Serial.print(' '); Serial.print(jointA, 2);
      Serial.print(' '); Serial.print(jointB, 2);
      Serial.print(' '); Serial.print(jointC, 2);
    }
    Serial.println();
    return;
  }
  if (strcmp(line, "CMD stop") == 0) {
    robot.SleepMode();
    actionActive = false;
    Serial.println("DONE stop");
    return;
  }
  if (strncmp(line, "CMD ", 4) != 0) {
    Serial.println("ERROR unsupported_request");
    return;
  }

  char *context = nullptr;
  char *action = strtok_r(line + 4, " ", &context);
  if (!action) {
    Serial.println("ERROR missing_action");
    return;
  }
  if (strcmp(action, "crawl") == 0) {
    char *xText = strtok_r(nullptr, " ", &context);
    char *yText = strtok_r(nullptr, " ", &context);
    char *angleText = strtok_r(nullptr, " ", &context);
    char *extra = strtok_r(nullptr, " ", &context);
    float x, y, angle;
    if (!xText || !yText || !angleText || extra ||
        !parseFinite(xText, x) || !parseFinite(yText, y) || !parseFinite(angleText, angle) ||
        fabs(x) > 42.0f || fabs(y) > 42.0f || fabs(angle) > 18.0f) {
      Serial.println("ERROR crawl_out_of_range");
      return;
    }
    Serial.println("STARTED crawl");
    Serial.flush();
    robot.Crawl(x, y, angle);
    lastActionCompletedAt = millis();
    actionActive = true;
    Serial.println("DONE crawl");
    return;
  }

  if (strcmp(action, "leg") == 0) {
    char *legText = strtok_r(nullptr, " ", &context);
    char *zText = strtok_r(nullptr, " ", &context);
    char *extra = strtok_r(nullptr, " ", &context);
    char *legEnd = nullptr;
    long leg = legText ? strtol(legText, &legEnd, 10) : 0;
    float deltaZ = 0;
    if (!legText || !zText || extra || legEnd == legText || *legEnd != '\0' ||
        leg < 1 || leg > 6 || !parseFinite(zText, deltaZ) ||
        fabs(fabs(deltaZ) - 5.0f) > 0.01f) {
      Serial.println("ERROR leg_test_out_of_range");
      return;
    }
    if (actionActive) {
      Serial.println("ERROR action_busy");
      return;
    }
    Serial.print("STARTED leg ");
    Serial.println(leg);
    Serial.flush();
    robot.LegMoveToRelatively(static_cast<int>(leg), 0, 0, deltaZ);
    Serial.print("DONE leg ");
    Serial.println(leg);
    return;
  }

  if (strcmp(action, "forward") == 0 || strcmp(action, "backward") == 0 ||
      strcmp(action, "left") == 0 || strcmp(action, "right") == 0 ||
      strcmp(action, "turn_left") == 0 || strcmp(action, "turn_right") == 0) {
    if (strtok_r(nullptr, " ", &context)) {
      Serial.println("ERROR unexpected_arguments");
      return;
    }
    runAction(action);
    return;
  }
  Serial.println("ERROR unsupported_action");
}

static void receiveSerial() {
  while (Serial.available() > 0) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\r') continue;
    if (value == '\n') {
      if (lineOverflow) {
        Serial.println("ERROR line_too_long");
      } else if (lineLength > 0) {
        lineBuffer[lineLength] = '\0';
        handleCommand(lineBuffer);
      }
      lineLength = 0;
      lineOverflow = false;
      continue;
    }
    if (lineLength + 1 < LINE_CAPACITY) lineBuffer[lineLength++] = value;
    else lineOverflow = true;
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  robot.Start(false);
  Serial.println("READY FNK0031_NAV_V2");
}

void loop() {
  receiveSerial();
  if (actionActive && millis() - lastActionCompletedAt >= ACTION_WATCHDOG_MS) {
    robot.SleepMode();
    actionActive = false;
    Serial.println("WATCHDOG stopped");
  }
}
