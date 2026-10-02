#include <FNHR.h>
#include <string.h>

FNHR robot;

static const unsigned long SERIAL_BAUD = 115200;
static const size_t COMMAND_CAPACITY = 32;
char commandBuffer[COMMAND_CAPACITY];
size_t commandLength = 0;
bool commandOverflow = false;

void executeHighLevelCommand(const char *command) {
  const bool supported = strcmp(command, "forward") == 0 ||
                         strcmp(command, "backward") == 0 ||
                         strcmp(command, "turn_left") == 0 ||
                         strcmp(command, "turn_right") == 0 ||
                         strcmp(command, "stop") == 0;
  if (!supported) {
    Serial.println("ERROR unsupported_command");
    return;
  }

  Serial.print("STARTED ");
  Serial.println(command);
  Serial.flush();

  if (strcmp(command, "stop") == 0) {
    robot.SleepMode();
  } else {
    robot.ActiveMode();
    if (strcmp(command, "forward") == 0) robot.CrawlForward();
    else if (strcmp(command, "backward") == 0) robot.CrawlBackward();
    else if (strcmp(command, "turn_left") == 0) robot.TurnLeft();
    else if (strcmp(command, "turn_right") == 0) robot.TurnRight();
  }

  Serial.print("DONE ");
  Serial.println(command);
}

void handleCommand(char *line) {
  if (strcmp(line, "PING") == 0) {
    Serial.println("PONG FNK0031_BODY_V1");
    return;
  }
  if (strncmp(line, "CMD ", 4) == 0) {
    executeHighLevelCommand(line + 4);
    return;
  }
  Serial.println("ERROR unsupported_request");
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  robot.Start(false);
  Serial.println("READY FNK0031_BODY_V1");
}

void loop() {
  while (Serial.available() > 0) {
    const char value = static_cast<char>(Serial.read());
    if (value == '\r') continue;
    if (value == '\n') {
      if (commandOverflow) {
        Serial.println("ERROR command_too_long");
      } else if (commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        handleCommand(commandBuffer);
      }
      commandLength = 0;
      commandOverflow = false;
      continue;
    }
    if (commandLength + 1 < COMMAND_CAPACITY) {
      commandBuffer[commandLength++] = value;
    } else {
      commandOverflow = true;
    }
  }
}
