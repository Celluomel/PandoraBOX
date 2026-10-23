/*
 * File       Communication class for Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#pragma once
#if defined(ARDUINO_AVR_MEGA2560)

#include "FNHRBasic.h"
#include "FNHROrders.h"

#include <SPI.h>
#include "RF24.h"

class Communication
{
public:
  Communication();
  void Start(bool commFunction = true);

  void SetWiFi(String name, String password);
  void SetWiFiChannel(byte channel);
  void SetRemote(byte byte0, byte byte1, byte byte2, byte byte3, byte byte4);
  void SetRemoteChannel(byte channel);

  void UpdateCommunication();
  void UpdateOrder();

  RobotAction robotAction;
  bool commFunction;

private:
  const int stateLedPin = 13;
  bool stateLedState = LOW;
  void StartStateLed();
  void SetStateLed(bool state);
  void ReverseStateLed();

  const int pins[8] = { 20,21,A0,A1,15,14,2,3 };
  void StartPins();

  static const int inDataSize = 32;
  static const int outDataSize = 32;

  byte serialInData[inDataSize];
  byte serialInDataCounter = 0;
  void StartSerial();
  void UpdateSerial();

  RF24 rf24 = RF24(9, 53);
  byte rf24Address[6] = { 'F', 'N', 'K', '2', '9' };
  byte rf24Channel = 125;
  bool isRF24Available = false;
  byte rf24InData[inDataSize];
  byte rf24InDataCounter = 0;
  void StartRF24();
  void UpdateRF24();

  String esp8266SSID = "Freenove Hexapod Robot";
  String esp8266PWD = "Freenove";
  byte esp8266CHL = 1;
  const unsigned long esp8266Port = 65535;
  HardwareSerial& esp8266Serial = Serial2;
  unsigned long esp8266Baud = 115200;
  bool isESP8266Available = false;
  byte esp8266ClientID;
  byte esp8266InData[inDataSize];
  byte esp8266InDataCounter = 0;
  void SendCommandESP8266(String command);
  bool ReceiveCommandESP8266(String flag, unsigned long timeOut = 100, unsigned long timeWait = 0);
  bool SendDataESP8266(byte muxId, byte* buffer, byte length);
  bool ReceiveDataESP8266(byte* muxId, byte* buffer, byte* length);
  void StartESP8266();
  void UpdateESP8266();

  enum OrderSource { FromSerial, FromRF24, FromESP8266, FromNone };
  OrderSource orderSource = OrderSource::FromNone;

  enum OrderState { ExecuteStart, ExecuteDone, ExecuteNone };
  OrderState orderState = OrderState::ExecuteNone;

  volatile byte blockedOrder = 0;

  byte crawlParameters[3];
  byte changeHeightParameters[1];
  byte moveBodyParameters[3];
  byte rotateBodyParameters[3];
  byte twistBodyParameters[6];

  void HandleOrder(byte data[], OrderSource orderSource);

  void UpdateBlockedOrder();

  void CheckBlockedOrder();

  unsigned long lastBlockedOrderTime = 0;
  const unsigned long autoSleepOvertime = 10000;
  void UpdateAutoSleep();

  unsigned long ledCounter = 0;
  const unsigned int ledBlinkCycle = 20;
  int ledState = 0;
  void UpdateStateLED();

  float GetSupplyVoltage();

  void SaveRobotBootState(Robot::State state);
  Robot::State GetRobotBootState();
  void SetRobotBootState(Robot::State state);
};

void UpdateService();

#endif
