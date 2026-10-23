/*
 * File       Class for remote of Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#pragma once
#if defined(ARDUINO_AVR_UNO)

#include <Arduino.h>

#include "FNHROrders.h"

#include <SPI.h>
#include "RF24.h"

class FNHRRemote
{
public:
  FNHRRemote();

 /*
  * Brief     Start the remote
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Start();

 /*
  * Brief     Update the remote
  *           The loop() function should only call this function.
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Update();

 /*
  * Brief     Set remote address
  *           Call this function before Start()
  *           If don't call this function, will use default address.
  *           The robot should set the same address to be able to controlled by this romote.
  * Param     bytex     bytes to define the address
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Set(byte byte0, byte byte1, byte byte2, byte byte3, byte byte4);

 /*
  * Brief     Set remote channel
  *           Call this function before Start()
  *           If don't call this function, will use default channel.
  *           The robot should set the same channel to be able to controlled by this romote.
  * Param     channel   RF24 channel, 0 ~ 125, default: 125
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetChannel(byte channel);

private:
  const int pot1Pin = A0,
    pot2Pin = A1,
    joystickXPin = A2,
    joystickYPin = A3,
    joystickZPin = 7,
    s1Pin = 4,
    s2Pin = 3,
    s3Pin = 2,
    led1Pin = 6,
    led2Pin = 5,
    led3Pin = 8;

  const int joystickIgnoredLength = 50;
  const int potIgnoredLength = 10;

  void StartPins();

  static const int outDataSize = 32;

  RF24 rf24 = RF24(9, 10);
  byte rf24Address[6] = { 'F', 'N', 'K', '2', '9' };
  byte rf24Channel = 125;
  byte rf24OutData[outDataSize];
  byte rf24OutDataCounter = 0;

  const unsigned int rf24WriteInterval = 20;
  unsigned long lastRf24WriteMillis = 0;
  bool lastRf24Connected = false;
  const unsigned int rf24BlinkInterval = 250;

  void StartRF24();

  int lastChangeBodyHeightValue = 0;
  int lastMoveBodyJoystickXValue = 512;
  int lastMoveBodyJoystickYValue = 512;
};

#endif
