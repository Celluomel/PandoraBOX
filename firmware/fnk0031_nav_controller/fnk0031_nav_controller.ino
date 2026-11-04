#include <FNHR.h>
#include <EEPROM.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

FNHR robot;

static const unsigned long SERIAL_BAUD = 115200;
static const unsigned long ACTION_WATCHDOG_MS = 1200;
static const size_t LINE_CAPACITY = 224;
static const int WIFI_EEPROM_BASE = 160;  // FNHR V12.6 uses addresses 0..140.
static const byte WIFI_EEPROM_MAGIC[4] = {'F', 'N', 'K', 'W'};
static const byte WIFI_SSID_MAX = 32;
static const byte WIFI_PASSWORD_MAX = 64;
static const byte WIFI_SSID_LENGTH_ADDRESS = WIFI_EEPROM_BASE + 4;
static const byte WIFI_PASSWORD_LENGTH_ADDRESS = WIFI_EEPROM_BASE + 5;
static const byte WIFI_DATA_ADDRESS = WIFI_EEPROM_BASE + 6;
static const char *WIFI_AP_SSID = "Freenove Hexapod Robot";
static const char *WIFI_AP_PASSWORD = "Freenove";
static const unsigned long ESP_BAUD = 115200;
static const unsigned int WIFI_CONTROL_PORT = 8888;
static const byte WIFI_LINKS = 5;
static const int WIFI_TOKEN_MAGIC_ADDRESS = 296;
static const int WIFI_TOKEN_ADDRESS = 300;
static const byte WIFI_TOKEN_LENGTH = 64;

char lineBuffer[LINE_CAPACITY];
size_t lineLength = 0;
bool lineOverflow = false;
bool actionActive = false;
unsigned long lastActionCompletedAt = 0;
char wifiSsid[WIFI_SSID_MAX + 1] = {0};
char wifiPassword[WIFI_PASSWORD_MAX + 1] = {0};
bool wifiConfigured = false;
bool wifiConnected = false;
char wifiStationIp[16] = {0};
char wifiControlToken[WIFI_TOKEN_LENGTH + 1] = {0};
bool wifiLinkAuthorized[WIFI_LINKS] = {false};
String wifiRxBuffer;
char wifiLineBuffers[WIFI_LINKS][LINE_CAPACITY];
size_t wifiLineLengths[WIFI_LINKS] = {0};
bool wifiLineOverflows[WIFI_LINKS] = {false};
bool wifiFrameActive[WIFI_LINKS] = {false};
byte wifiFrameLengths[WIFI_LINKS] = {0};
byte wifiFrameBuffers[WIFI_LINKS][32] = {{0}};
unsigned long freenoveFramesReceived = 0;
unsigned long freenoveRepliesSent = 0;
unsigned long freenoveReplyFailures = 0;
int freenoveLastOrder = -1;
byte freenoveLastLength = 0;
int activeWifiLink = -1;

static int hexValue(char value) {
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'a' && value <= 'f') return value - 'a' + 10;
  if (value >= 'A' && value <= 'F') return value - 'A' + 10;
  return -1;
}

static bool decodeHexText(const char *encoded, char *output, byte maxBytes) {
  const size_t length = strlen(encoded);
  if (length == 0 || (length % 2) != 0 || length / 2 > maxBytes) return false;
  for (size_t index = 0; index < length / 2; ++index) {
    const int high = hexValue(encoded[index * 2]);
    const int low = hexValue(encoded[index * 2 + 1]);
    if (high < 0 || low < 0 || (high == 0 && low == 0)) return false;
    output[index] = static_cast<char>((high << 4) | low);
  }
  output[length / 2] = '\0';
  return true;
}

static void loadWifiCredentials() {
  for (byte index = 0; index < 4; ++index) {
    if (EEPROM.read(WIFI_EEPROM_BASE + index) != WIFI_EEPROM_MAGIC[index]) return;
  }
  const byte ssidLength = EEPROM.read(WIFI_SSID_LENGTH_ADDRESS);
  const byte passwordLength = EEPROM.read(WIFI_PASSWORD_LENGTH_ADDRESS);
  if (ssidLength == 0 || ssidLength > WIFI_SSID_MAX || passwordLength > WIFI_PASSWORD_MAX) return;
  for (byte index = 0; index < ssidLength; ++index)
    wifiSsid[index] = static_cast<char>(EEPROM.read(WIFI_DATA_ADDRESS + index));
  for (byte index = 0; index < passwordLength; ++index)
    wifiPassword[index] = static_cast<char>(EEPROM.read(WIFI_DATA_ADDRESS + ssidLength + index));
  wifiSsid[ssidLength] = '\0';
  wifiPassword[passwordLength] = '\0';
  wifiConfigured = true;
}

static void loadWifiControlToken() {
  if (EEPROM.read(WIFI_TOKEN_MAGIC_ADDRESS) != 'K' ||
      EEPROM.read(WIFI_TOKEN_MAGIC_ADDRESS + 1) != 'E' ||
      EEPROM.read(WIFI_TOKEN_MAGIC_ADDRESS + 2) != 'Y' ||
      EEPROM.read(WIFI_TOKEN_MAGIC_ADDRESS + 3) != '1') return;
  for (byte index = 0; index < WIFI_TOKEN_LENGTH; ++index) {
    const char value = static_cast<char>(EEPROM.read(WIFI_TOKEN_ADDRESS + index));
    if (!((value >= '0' && value <= '9') || (value >= 'a' && value <= 'f'))) return;
    wifiControlToken[index] = value;
  }
  wifiControlToken[WIFI_TOKEN_LENGTH] = '\0';
}

static void saveWifiControlToken(const char *token) {
  for (byte index = 0; index < 4; ++index) EEPROM.update(WIFI_TOKEN_MAGIC_ADDRESS + index, "KEY1"[index]);
  for (byte index = 0; index < WIFI_TOKEN_LENGTH; ++index) {
    wifiControlToken[index] = token[index];
    EEPROM.update(WIFI_TOKEN_ADDRESS + index, static_cast<byte>(token[index]));
  }
  wifiControlToken[WIFI_TOKEN_LENGTH] = '\0';
}

static void saveWifiCredentials(const char *ssid, const char *password) {
  const byte ssidLength = static_cast<byte>(strlen(ssid));
  const byte passwordLength = static_cast<byte>(strlen(password));
  for (byte index = 0; index < 4; ++index)
    EEPROM.update(WIFI_EEPROM_BASE + index, WIFI_EEPROM_MAGIC[index]);
  EEPROM.update(WIFI_SSID_LENGTH_ADDRESS, ssidLength);
  EEPROM.update(WIFI_PASSWORD_LENGTH_ADDRESS, passwordLength);
  for (byte index = 0; index < ssidLength; ++index)
    EEPROM.update(WIFI_DATA_ADDRESS + index, static_cast<byte>(ssid[index]));
  for (byte index = 0; index < passwordLength; ++index)
    EEPROM.update(WIFI_DATA_ADDRESS + ssidLength + index, static_cast<byte>(password[index]));
  strncpy(wifiSsid, ssid, WIFI_SSID_MAX);
  strncpy(wifiPassword, password, WIFI_PASSWORD_MAX);
  wifiSsid[ssidLength] = '\0';
  wifiPassword[passwordLength] = '\0';
  wifiConfigured = true;
}

static String quoteAtValue(const char *value) {
  String quoted = "\"";
  for (const char *cursor = value; *cursor; ++cursor) {
    if (*cursor == '\\' || *cursor == '"') quoted += '\\';
    quoted += *cursor;
  }
  quoted += '"';
  return quoted;
}

static bool sendEspCommand(const String &command, const char *expected, unsigned long timeoutMs,
                           String *response = nullptr) {
  while (Serial2.available()) Serial2.read();
  Serial2.println(command);
  String received;
  const unsigned long started = millis();
  while (millis() - started < timeoutMs) {
    while (Serial2.available()) {
      const char value = static_cast<char>(Serial2.read());
      if (received.length() < 240) received += value;
      if (received.indexOf(expected) >= 0) {
        if (response) *response = received;
        return true;
      }
    }
    delay(1);
  }
  if (response) *response = received;
  return false;
}

static bool connectConfiguredWifi() {
  wifiConnected = false;
  wifiStationIp[0] = '\0';
  if (!wifiConfigured) return false;
  sendEspCommand("AT+CWQAP", "OK", 1500);
  const String join = String("AT+CWJAP_CUR=") + quoteAtValue(wifiSsid) + "," + quoteAtValue(wifiPassword);
  if (!sendEspCommand(join, "OK", 20000)) return false;
  String addressResponse;
  sendEspCommand("AT+CIFSR", "OK", 2500, &addressResponse);
  const int marker = addressResponse.indexOf("STAIP,\"");
  if (marker >= 0) {
    const int start = marker + 7;
    const int end = addressResponse.indexOf('"', start);
    if (end > start && end - start < static_cast<int>(sizeof(wifiStationIp))) {
      addressResponse.substring(start, end).toCharArray(wifiStationIp, sizeof(wifiStationIp));
    }
  }
  wifiConnected = wifiStationIp[0] != '\0' && strcmp(wifiStationIp, "0.0.0.0") != 0;
  return wifiConnected;
}

static bool sendWifiBytes(int linkId, const byte *payload, size_t length) {
  if (linkId < 0 || linkId >= WIFI_LINKS || !payload || length == 0) return false;
  while (Serial2.available()) Serial2.read();
  Serial2.print("AT+CIPSEND="); Serial2.print(linkId); Serial2.print(','); Serial2.println(length);
  String received;
  const unsigned long promptDeadline = millis() + 1500;
  bool prompt = false;
  while (millis() < promptDeadline && !prompt) {
    while (Serial2.available()) {
      const char value = static_cast<char>(Serial2.read());
      if (value == '>') { prompt = true; break; }
      if (received.length() < 100) received += value;
    }
    if (!prompt) delay(1);
  }
  if (!prompt) return false;
  Serial2.write(payload, length);
  received = "";
  const unsigned long sendDeadline = millis() + 2500;
  while (millis() < sendDeadline) {
    while (Serial2.available()) {
      const char value = static_cast<char>(Serial2.read());
      if (received.length() < 160) received += value;
      if (received.indexOf("SEND OK") >= 0) return true;
      if (received.indexOf("ERROR") >= 0 || received.indexOf("CLOSED") >= 0) return false;
    }
    delay(1);
  }
  return false;
}

static bool sendWifiTcp(int linkId, const String &payload) {
  return sendWifiBytes(linkId, reinterpret_cast<const byte *>(payload.c_str()), payload.length());
}

static void sendCommandLine(const String &line) {
  if (activeWifiLink >= 0) sendWifiTcp(activeWifiLink, line + "\n");
  else Serial.println(line);
}

static void startWifi() {
  Serial2.begin(ESP_BAUD);
  Serial2.setTimeout(20);
  sendEspCommand("AT+RST", "ready", 5000);
  sendEspCommand("AT+CWMODE_CUR=3", "OK", 2500);  // Keep Freenove AP and add router station mode.
  sendEspCommand(String("AT+CWSAP_CUR=\"") + WIFI_AP_SSID + "\",\"" + WIFI_AP_PASSWORD + "\",1,4", "OK", 3000);
  if (wifiConfigured) connectConfiguredWifi();
  sendEspCommand("AT+CIPMUX=1", "OK", 2000);
  sendEspCommand(String("AT+CIPSERVER=1,") + WIFI_CONTROL_PORT, "OK", 2500);
}

static void handleWifiCommand(char *line) {
  if (strcmp(line, "WIFI STATUS") == 0) {
    if (wifiConfigured) {
      String addressResponse;
      sendEspCommand("AT+CIFSR", "OK", 2500, &addressResponse);
      const int marker = addressResponse.indexOf("STAIP,\"");
      if (marker >= 0) {
        const int start = marker + 7;
        const int end = addressResponse.indexOf('"', start);
        if (end > start && end - start < static_cast<int>(sizeof(wifiStationIp)))
          addressResponse.substring(start, end).toCharArray(wifiStationIp, sizeof(wifiStationIp));
      }
      wifiConnected = wifiStationIp[0] != '\0' && strcmp(wifiStationIp, "0.0.0.0") != 0;
    }
    if (wifiConnected) {
      Serial.print("WIFI CONNECTED "); Serial.println(wifiStationIp);
    } else if (wifiConfigured) {
      Serial.println("WIFI JOIN FAILED");
    } else {
      Serial.print("WIFI NOT CONFIGURED AP "); Serial.println(WIFI_AP_SSID);
    }
    return;
  }
  if (strcmp(line, "WIFI CLEAR") == 0) {
    sendEspCommand("AT+CWQAP", "OK", 1500);
    for (byte index = 0; index < 4; ++index) EEPROM.update(WIFI_EEPROM_BASE + index, 0);
    for (int address = WIFI_DATA_ADDRESS; address < WIFI_DATA_ADDRESS + WIFI_SSID_MAX + WIFI_PASSWORD_MAX; ++address)
      EEPROM.update(address, 0);
    EEPROM.update(WIFI_TOKEN_MAGIC_ADDRESS, 0);
    for (byte index = 0; index < WIFI_TOKEN_LENGTH; ++index) EEPROM.update(WIFI_TOKEN_ADDRESS + index, 0);
    memset(wifiSsid, 0, sizeof(wifiSsid));
    memset(wifiPassword, 0, sizeof(wifiPassword));
    memset(wifiControlToken, 0, sizeof(wifiControlToken));
    wifiConfigured = false;
    wifiConnected = false;
    wifiStationIp[0] = '\0';
    Serial.println("WIFI CLEARED");
    return;
  }
  if (strncmp(line, "WIFI TOKEN ", 11) == 0) {
    const char *token = line + 11;
    if (strlen(token) != WIFI_TOKEN_LENGTH) { Serial.println("ERROR wifi_token_invalid"); return; }
    for (byte index = 0; index < WIFI_TOKEN_LENGTH; ++index) {
      if (!((token[index] >= '0' && token[index] <= '9') || (token[index] >= 'a' && token[index] <= 'f'))) {
        Serial.println("ERROR wifi_token_invalid"); return;
      }
    }
    saveWifiControlToken(token);
    Serial.println("WIFI TOKEN SAVED");
    return;
  }
  if (strncmp(line, "WIFI SET ", 9) == 0) {
    char *separator = strchr(line + 9, ' ');
    if (!separator) { Serial.println("ERROR wifi_config_format"); return; }
    *separator++ = '\0';
    char nextSsid[WIFI_SSID_MAX + 1] = {0};
    char nextPassword[WIFI_PASSWORD_MAX + 1] = {0};
    if (!decodeHexText(line + 9, nextSsid, WIFI_SSID_MAX) ||
        (strlen(separator) > 0 && !decodeHexText(separator, nextPassword, WIFI_PASSWORD_MAX))) {
      Serial.println("ERROR wifi_config_invalid");
      return;
    }
    saveWifiCredentials(nextSsid, nextPassword);
    const bool joined = connectConfiguredWifi();
    if (joined) {
      Serial.print("WIFI CONNECTED "); Serial.println(wifiStationIp);
    } else {
      Serial.println("WIFI SAVED JOIN FAILED");
    }
    memset(nextPassword, 0, sizeof(nextPassword));
    return;
  }
  Serial.println("ERROR wifi_command_unsupported");
}

static bool parseFinite(char *text, float &value) {
  char *end = nullptr;
  value = static_cast<float>(strtod(text, &end));
  return end != text && *end == '\0' && isfinite(value);
}

static void runAction(const char *name) {
  sendCommandLine(String("STARTED ") + name);
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
  sendCommandLine(String("DONE ") + name);
}

static void handleCommand(char *line, int wifiLink = -1) {
  activeWifiLink = wifiLink;
  if (wifiLink >= 0) {
    if (!wifiLinkAuthorized[wifiLink]) {
      if (strncmp(line, "AUTH ", 5) == 0 && wifiControlToken[0] && strcmp(line + 5, wifiControlToken) == 0) {
        wifiLinkAuthorized[wifiLink] = true;
        sendCommandLine("AUTH OK");
      } else {
        sendCommandLine("ERROR unauthorized");
      }
      activeWifiLink = -1;
      return;
    }
    if (strncmp(line, "WIFI ", 5) == 0) {
      sendCommandLine("ERROR wifi_setup_requires_usb");
      activeWifiLink = -1;
      return;
    }
  }
  if (strncmp(line, "WIFI ", 5) == 0) { handleWifiCommand(line); return; }
  if (strcmp(line, "PING") == 0) {
    sendCommandLine("PONG FNK0031_NAV_V2");
    activeWifiLink = -1;
    return;
  }
  if (strcmp(line, "CMD freenove") == 0) {
    String diagnostic = String("FREENOVE rx=") + freenoveFramesReceived +
      " reply_ok=" + freenoveRepliesSent +
      " reply_fail=" + freenoveReplyFailures +
      " last_order=" + freenoveLastOrder +
      " last_bytes=" + freenoveLastLength;
    sendCommandLine(diagnostic);
    activeWifiLink = -1;
    return;
  }
  if (strcmp(line, "CMD state") == 0) {
    String state = String("STATE ") + millis();
    for (int leg = 1; leg <= 6; ++leg) {
      float x, y, z, jointA, jointB, jointC;
      if (!robot.GetEstimatedLegState(leg, x, y, z, jointA, jointB, jointC)) {
        sendCommandLine("ERROR state_unavailable");
        activeWifiLink = -1;
        return;
      }
      state += " "; state += String(x, 2);
      state += " "; state += String(y, 2);
      state += " "; state += String(z, 2);
      state += " "; state += String(jointA, 2);
      state += " "; state += String(jointB, 2);
      state += " "; state += String(jointC, 2);
    }
    sendCommandLine(state);
    activeWifiLink = -1;
    return;
  }
  if (strcmp(line, "CMD stop") == 0) {
    robot.SleepMode();
    actionActive = false;
    sendCommandLine("DONE stop");
    activeWifiLink = -1;
    return;
  }
  if (strncmp(line, "CMD ", 4) != 0) {
    sendCommandLine("ERROR unsupported_request");
    activeWifiLink = -1;
    return;
  }

  char *context = nullptr;
  char *action = strtok_r(line + 4, " ", &context);
  if (!action) {
    sendCommandLine("ERROR missing_action"); activeWifiLink = -1;
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
      sendCommandLine("ERROR crawl_out_of_range"); activeWifiLink = -1;
      return;
    }
    if (actionActive) {
      sendCommandLine("ERROR action_busy"); activeWifiLink = -1;
      return;
    }
    sendCommandLine("STARTED crawl");
    Serial.flush();
    robot.Crawl(x, y, angle);
    lastActionCompletedAt = millis();
    actionActive = true;
    sendCommandLine("DONE crawl"); activeWifiLink = -1;
    return;
  }

  if (strcmp(action, "twist") == 0) {
    float values[6];
    bool valid = true;
    for (int index = 0; index < 6; ++index) {
      char *text = strtok_r(nullptr, " ", &context);
      if (!text || !parseFinite(text, values[index])) valid = false;
    }
    if (strtok_r(nullptr, " ", &context)) valid = false;
    if (!valid || fabs(values[0]) > 30.0f || fabs(values[1]) > 30.0f ||
        values[2] < 0.0f || values[2] > 45.0f || fabs(values[3]) > 15.0f ||
        sqrt(values[3] * values[3] + values[4] * values[4] + values[5] * values[5]) > 15.0f) {
      sendCommandLine("ERROR twist_out_of_range"); activeWifiLink = -1;
      return;
    }
    if (actionActive) {
      sendCommandLine("ERROR action_busy"); activeWifiLink = -1;
      return;
    }
    sendCommandLine("STARTED twist");
    Serial.flush();
    robot.TwistBody(values[0], values[1], values[2], values[3], values[4], values[5]);
    lastActionCompletedAt = millis();
    actionActive = true;
    sendCommandLine("DONE twist"); activeWifiLink = -1;
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
      sendCommandLine("ERROR leg_test_out_of_range"); activeWifiLink = -1;
      return;
    }
    if (actionActive) {
      sendCommandLine("ERROR action_busy"); activeWifiLink = -1;
      return;
    }
    sendCommandLine(String("STARTED leg ") + leg);
    Serial.flush();
    robot.LegMoveToRelatively(static_cast<int>(leg), 0, 0, deltaZ);
    sendCommandLine(String("DONE leg ") + leg); activeWifiLink = -1;
    return;
  }

  if (strcmp(action, "forward") == 0 || strcmp(action, "backward") == 0 ||
      strcmp(action, "left") == 0 || strcmp(action, "right") == 0 ||
      strcmp(action, "turn_left") == 0 || strcmp(action, "turn_right") == 0) {
    if (strtok_r(nullptr, " ", &context)) {
      sendCommandLine("ERROR unexpected_arguments"); activeWifiLink = -1;
      return;
    }
    runAction(action);
    return;
  }
  sendCommandLine("ERROR unsupported_action"); activeWifiLink = -1;
}

static void handleWifiLine(int linkId, char *line) {
  if (linkId < 0 || linkId >= WIFI_LINKS || !line || !*line) return;
  handleCommand(line, linkId);
}

static void sendFreenoveReply(int linkId, byte order, const byte *data = nullptr, byte dataLength = 0) {
  byte response[32];
  if (dataLength > sizeof(response) - 3) return;
  response[0] = 0x80;
  response[1] = order;
  for (byte index = 0; index < dataLength; ++index) response[index + 2] = data[index];
  response[dataLength + 2] = 0x81;
  if (sendWifiBytes(linkId, response, dataLength + 3)) ++freenoveRepliesSent;
  else ++freenoveReplyFailures;
}

static bool freenoveLengthIs(const byte *frame, byte length, byte order, byte expectedLength) {
  return length == expectedLength && frame[0] == 0x80 && frame[1] == order && frame[length - 1] == 0x81;
}

// The Android/Processing app sends the original FNHR binary frame:
// 0x80, order, zero or more 7-bit arguments, 0x81. This is separate from the
// authenticated ASCII protocol used by the Body on the same TCP port.
static void handleFreenoveWifiFrame(int linkId, const byte *frame, byte length) {
  ++freenoveFramesReceived;
  freenoveLastLength = length;
  freenoveLastOrder = length >= 2 ? frame[1] : -1;
  if (length < 3 || frame[0] != 0x80 || frame[length - 1] != 0x81) return;
  for (byte index = 1; index + 1 < length; ++index) {
    if (frame[index] > 127) return;
  }
  const byte order = frame[1];
  if (order == 0 && freenoveLengthIs(frame, length, order, 3)) {
    sendFreenoveReply(linkId, 1);
    return;
  }
  if (order == 10 && freenoveLengthIs(frame, length, order, 3)) {
    const int voltageCentivolts = static_cast<int>(robot.GetSupplyVoltage() * 100.0f);
    const byte voltage[] = {
      static_cast<byte>(voltageCentivolts / 128),
      static_cast<byte>(voltageCentivolts % 128)
    };
    sendFreenoveReply(linkId, 11, voltage, sizeof(voltage));
    return;
  }
  if (order == 20 && freenoveLengthIs(frame, length, order, 5)) {
    const byte pins[] = {20, 21, A0, A1, 15, 14, 2, 3};
    if (frame[2] >= sizeof(pins) || frame[3] > 1) return;
    pinMode(pins[frame[2]], OUTPUT);
    digitalWrite(pins[frame[2]], frame[3] ? HIGH : LOW);
    sendFreenoveReply(linkId, 23);
    return;
  }

  bool isBlockingAction = false;
  if (order == 80 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 82 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 84 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 86 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 88 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 90 && freenoveLengthIs(frame, length, order, 3)) isBlockingAction = true;
  else if (order == 92 && freenoveLengthIs(frame, length, order, 3)) {
    robot.ActiveMode();
    sendFreenoveReply(linkId, 23);
    return;
  } else if (order == 94 && freenoveLengthIs(frame, length, order, 3)) {
    robot.SleepMode();
    actionActive = false;
    sendFreenoveReply(linkId, 23);
    return;
  } else if (order == 96 && freenoveLengthIs(frame, length, order, 3)) {
    robot.SwitchMode();
    sendFreenoveReply(linkId, 23);
    return;
  } else if (order == 110 && freenoveLengthIs(frame, length, order, 6)) {
    isBlockingAction = true;
  } else if (order == 112 && freenoveLengthIs(frame, length, order, 4)) {
    isBlockingAction = true;
  } else if (order == 114 && freenoveLengthIs(frame, length, order, 6)) {
    isBlockingAction = true;
  } else if (order == 116 && freenoveLengthIs(frame, length, order, 6)) {
    isBlockingAction = true;
  } else if (order == 118 && freenoveLengthIs(frame, length, order, 9)) {
    isBlockingAction = true;
  } else if (order == 30 && freenoveLengthIs(frame, length, order, 7)) {
    robot.LegMoveToRelatively(frame[2], frame[3] - 64, frame[4] - 64, frame[5] - 64);
    sendFreenoveReply(linkId, 23);
    return;
  } else {
    // Installation and calibration orders are not acknowledged as successful
    // because they are not implemented by this custom profile.
    return;
  }

  if (!isBlockingAction) return;
  sendFreenoveReply(linkId, 21);
  Serial.flush();
  if (order == 80) robot.CrawlForward();
  else if (order == 82) robot.CrawlBackward();
  else if (order == 84) robot.CrawlLeft();
  else if (order == 86) robot.CrawlRight();
  else if (order == 88) robot.TurnLeft();
  else if (order == 90) robot.TurnRight();
  else if (order == 110) robot.Crawl(frame[2] - 64, frame[3] - 64, frame[4] - 64);
  else if (order == 112) robot.ChangeBodyHeight(frame[2] - 64);
  else if (order == 114) robot.MoveBody(frame[2] - 64, frame[3] - 64, frame[4] - 64);
  else if (order == 116) robot.RotateBody(frame[2] - 64, frame[3] - 64, frame[4] - 64);
  else if (order == 118) {
    robot.TwistBody(frame[2] - 64, frame[3] - 64, frame[4] - 64,
                    frame[5] - 64, frame[6] - 64, frame[7] - 64);
  }
  lastActionCompletedAt = millis();
  actionActive = true;
  sendFreenoveReply(linkId, 23);
}

static void receiveWifiPayloadByte(int linkId, byte value) {
  if (linkId < 0 || linkId >= WIFI_LINKS) return;
  if (value == 0x80) {
    wifiFrameActive[linkId] = true;
    wifiFrameLengths[linkId] = 0;
    wifiLineLengths[linkId] = 0;
    wifiLineOverflows[linkId] = false;
    wifiFrameBuffers[linkId][wifiFrameLengths[linkId]++] = value;
    return;
  }
  if (wifiFrameActive[linkId]) {
    if (wifiFrameLengths[linkId] >= sizeof(wifiFrameBuffers[linkId])) {
      wifiFrameActive[linkId] = false;
      wifiFrameLengths[linkId] = 0;
      return;
    }
    wifiFrameBuffers[linkId][wifiFrameLengths[linkId]++] = value;
    if (value == 0x81) {
      handleFreenoveWifiFrame(linkId, wifiFrameBuffers[linkId], wifiFrameLengths[linkId]);
      wifiFrameActive[linkId] = false;
      wifiFrameLengths[linkId] = 0;
    }
    return;
  }
  if (value == '\r') return;
  if (value == '\n') {
    if (wifiLineOverflows[linkId]) sendWifiTcp(linkId, "ERROR line_too_long\n");
    else if (wifiLineLengths[linkId] > 0) {
      wifiLineBuffers[linkId][wifiLineLengths[linkId]] = '\0';
      handleWifiLine(linkId, wifiLineBuffers[linkId]);
    }
    wifiLineLengths[linkId] = 0;
    wifiLineOverflows[linkId] = false;
  } else if (wifiLineLengths[linkId] + 1 < LINE_CAPACITY) {
    wifiLineBuffers[linkId][wifiLineLengths[linkId]++] = static_cast<char>(value);
  } else wifiLineOverflows[linkId] = true;
}

static void receiveWifi() {
  while (Serial2.available()) {
    if (wifiRxBuffer.length() >= 768) wifiRxBuffer.remove(0, wifiRxBuffer.length() - 256);
    wifiRxBuffer += static_cast<char>(Serial2.read());
  }
  while (true) {
    for (byte linkId = 0; linkId < WIFI_LINKS; ++linkId) {
      const String closed = String(linkId) + ",CLOSED";
      const String connected = String(linkId) + ",CONNECT";
      const int closedAt = wifiRxBuffer.indexOf(closed);
      if (closedAt >= 0) {
        wifiLinkAuthorized[linkId] = false;
        wifiFrameActive[linkId] = false;
        wifiFrameLengths[linkId] = 0;
        wifiLineLengths[linkId] = 0;
        wifiLineOverflows[linkId] = false;
        wifiRxBuffer.remove(closedAt, closed.length());
      }
      const int connectedAt = wifiRxBuffer.indexOf(connected);
      if (connectedAt >= 0) {
        wifiLinkAuthorized[linkId] = false;
        wifiFrameActive[linkId] = false;
        wifiFrameLengths[linkId] = 0;
        wifiLineLengths[linkId] = 0;
        wifiLineOverflows[linkId] = false;
        wifiRxBuffer.remove(connectedAt, connected.length());
      }
    }
    const int marker = wifiRxBuffer.indexOf("+IPD,");
    if (marker < 0) {
      if (wifiRxBuffer.length() > 32) wifiRxBuffer.remove(0, wifiRxBuffer.length() - 16);
      return;
    }
    if (marker > 0) wifiRxBuffer.remove(0, marker);
    const int comma = wifiRxBuffer.indexOf(',', 5);
    const int colon = wifiRxBuffer.indexOf(':', comma + 1);
    if (comma < 0 || colon < 0) return;
    const int linkId = wifiRxBuffer.substring(5, comma).toInt();
    const int payloadLength = wifiRxBuffer.substring(comma + 1, colon).toInt();
    if (linkId < 0 || linkId >= WIFI_LINKS || payloadLength < 0 || payloadLength > 256) {
      wifiRxBuffer.remove(0, colon + 1);
      continue;
    }
    if (wifiRxBuffer.length() < colon + 1 + payloadLength) return;
    const String payload = wifiRxBuffer.substring(colon + 1, colon + 1 + payloadLength);
    wifiRxBuffer.remove(0, colon + 1 + payloadLength);
    for (unsigned int index = 0; index < payload.length(); ++index) {
      receiveWifiPayloadByte(linkId, static_cast<byte>(payload[index]));
    }
  }
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
  loadWifiCredentials();
  loadWifiControlToken();
  startWifi();
  Serial.println("READY FNK0031_NAV_V2");
}

void loop() {
  receiveSerial();
  receiveWifi();
  if (actionActive && millis() - lastActionCompletedAt >= ACTION_WATCHDOG_MS) {
    robot.SleepMode();
    actionActive = false;
    Serial.println("WATCHDOG stopped");
  }
}
