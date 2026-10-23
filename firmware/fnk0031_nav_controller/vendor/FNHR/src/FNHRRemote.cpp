/*
 * File       Class for remote of Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#if defined(ARDUINO_AVR_UNO)

#include "FNHRRemote.h"

FNHRRemote::FNHRRemote() {}

void FNHRRemote::Start()
{
  StartPins();
  StartRF24();
//  Serial.begin(115200); // For debugging.
}

void FNHRRemote::StartPins()
{
  pinMode(joystickZPin, INPUT);
  pinMode(s1Pin, INPUT);
  pinMode(s2Pin, INPUT);
  pinMode(s2Pin, INPUT);
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(led3Pin, OUTPUT);
}

void FNHRRemote::StartRF24()
{
  pinMode(12, INPUT_PULLUP);
  rf24.begin();
  rf24.setRetries(3, 15);
  rf24.setPALevel(RF24_PA_LOW, false);
  rf24.setDataRate(RF24_1MBPS);
  rf24.enableDynamicPayloads();
  rf24.setAutoAck(true);
  rf24.setChannel(rf24Channel);
  rf24.openWritingPipe(rf24Address);
  rf24.openReadingPipe(1, rf24Address);
  rf24.stopListening();
}

void FNHRRemote::Update()
{
  int pot1Value = analogRead(pot1Pin);
  int pot2Value = analogRead(pot2Pin);
  int joystickXValue = analogRead(joystickXPin);
  int joystickYValue = analogRead(joystickYPin);
  bool joystickZValue = digitalRead(joystickZPin);
  bool s1Value = digitalRead(s1Pin);
  bool s2Value = digitalRead(s2Pin);
  bool s3Value = digitalRead(s3Pin);

  rf24OutDataCounter = 0;

  rf24OutData[rf24OutDataCounter++] = Orders::transStart;

  if (!s1Value)
  {
    int joystickLength = sqrt(pow(joystickXValue - 512, 2) + pow(joystickYValue - 512, 2));

    if (joystickLength > joystickIgnoredLength)
    {
      rf24OutData[rf24OutDataCounter++] = Orders::requestCrawl;
      if (s2Value)
      {
        rf24OutData[rf24OutDataCounter++] = map(joystickXValue, 0, 1024, 42, -42) + 64;
        rf24OutData[rf24OutDataCounter++] = map(joystickYValue, 0, 1024, 42, -42) + 64;
        rf24OutData[rf24OutDataCounter++] = 0 + 64;
      }
      else
      {
        rf24OutData[rf24OutDataCounter++] = 0 + 64;
        rf24OutData[rf24OutDataCounter++] = map(joystickYValue, 0, 1024, 42, -42) + 64;
        if(joystickYValue < 512)
          rf24OutData[rf24OutDataCounter++] = map(joystickXValue, 0, 1024, -18, 18) + 64;
        else
          rf24OutData[rf24OutDataCounter++] = map(joystickXValue, 0, 1024, 18, -18) + 64;
      }
    }
    else if (!joystickZValue)
      rf24OutData[rf24OutDataCounter++] = Orders::requestSwitchMode;
    else
    {
      if (abs(pot2Value - lastChangeBodyHeightValue) > potIgnoredLength)
      {
        rf24OutData[rf24OutDataCounter++] = Orders::requestChangeBodyHeight;
        rf24OutData[rf24OutDataCounter++] = map(pot2Value, 0, 1024, 0, 45) + 64;
        lastChangeBodyHeightValue = pot2Value;
      }
    }
  }
  else if (!s2Value)
  {
    if (s3Value)
    {
      rf24OutData[rf24OutDataCounter++] = Orders::requestMoveBody;
      rf24OutData[rf24OutDataCounter++] = map(joystickXValue, 0, 1024, 30, -30) + 64;
      rf24OutData[rf24OutDataCounter++] = map(joystickYValue, 0, 1024, 30, -30) + 64;
      rf24OutData[rf24OutDataCounter++] = map(pot2Value, 0, 1024, 0, 45) + 64;
      lastMoveBodyJoystickXValue = joystickXValue;
      lastMoveBodyJoystickYValue = joystickYValue;
    }
    else
    {
      rf24OutData[rf24OutDataCounter++] = Orders::requestTwistBody;

      rf24OutData[rf24OutDataCounter++] = map(lastMoveBodyJoystickXValue, 0, 1024, 30, -30) + 64;
      rf24OutData[rf24OutDataCounter++] = map(lastMoveBodyJoystickYValue, 0, 1024, 30, -30) + 64;
      rf24OutData[rf24OutDataCounter++] = map(pot2Value, 0, 1024, 0, 45) + 64;

      float x = map(joystickYValue, 0, 1024, 10, -10);
      float y = map(joystickXValue, 0, 1024, -10, 10);
      float z = map(pot1Value, 0, 1024, 10, -10);

      rf24OutData[rf24OutDataCounter++] = x + 64;
      rf24OutData[rf24OutDataCounter++] = y + 64;
      rf24OutData[rf24OutDataCounter++] = z + 64;
    }
  }
  else if (!s3Value)
  {
    rf24OutData[rf24OutDataCounter++] = Orders::requestTwistBody;

    rf24OutData[rf24OutDataCounter++] = 0 + 64;
    rf24OutData[rf24OutDataCounter++] = 0 + 64;
    rf24OutData[rf24OutDataCounter++] = map(pot2Value, 0, 1024, 0, 45) + 64;

    float x = map(joystickYValue, 0, 1024, 10, -10);
    float y = map(joystickXValue, 0, 1024, -10, 10);
    float z = map(pot1Value, 0, 1024, 10, -10);

    rf24OutData[rf24OutDataCounter++] = x + 64;
    rf24OutData[rf24OutDataCounter++] = y + 64;
    rf24OutData[rf24OutDataCounter++] = z + 64;
  }
  else
    rf24OutData[rf24OutDataCounter++] = Orders::requestEcho;

  rf24OutData[rf24OutDataCounter++] = Orders::transEnd;

  unsigned long millisNow = lastRf24WriteMillis;
  while (millisNow - lastRf24WriteMillis < rf24WriteInterval)
    millisNow = millis();
  lastRf24WriteMillis = millisNow;

  if (rf24.isChipConnected())
  {
    if (!lastRf24Connected)
      StartRF24();
    if (rf24.write(rf24OutData, rf24OutDataCounter))
    {
      digitalWrite(led3Pin, HIGH);
      lastRf24Connected = true;
//    Serial.print("OK: ");                         // For debugging.
//    Serial.print(millis() - lastRf24WriteMillis); // For debugging.
//    Serial.println("ms");                         // For debugging.
    }
    else
    {
      digitalWrite(led3Pin, LOW);
      lastRf24Connected = false;
//    Serial.print("                NG: ");         // For debugging.
//    Serial.print(millis() - lastRf24WriteMillis); // For debugging.
//    Serial.println("ms");                         // For debugging.
    }

    analogWrite(led1Pin, map(pot1Value, 0, 1023, 0, 255));
    analogWrite(led2Pin, map(pot2Value, 0, 1023, 0, 255));
  }
  else
  {
    if (millisNow % (rf24BlinkInterval * 2) < rf24BlinkInterval)
    {
      digitalWrite(led1Pin, LOW);
      digitalWrite(led2Pin, HIGH);
    }
    else
    {
      digitalWrite(led1Pin, HIGH);
      digitalWrite(led2Pin, LOW);
    }

    digitalWrite(led3Pin, LOW);
    lastRf24Connected = false;
  }
}

void FNHRRemote::Set(byte byte0, byte byte1, byte byte2, byte byte3, byte byte4)
{
  rf24Address[0] = byte0;
  rf24Address[1] = byte1;
  rf24Address[2] = byte2;
  rf24Address[3] = byte3;
  rf24Address[4] = byte4;
}

void FNHRRemote::SetChannel(byte channel)
{
  channel = constrain(channel, 0, 125);
  rf24Channel = channel;
}

#endif
