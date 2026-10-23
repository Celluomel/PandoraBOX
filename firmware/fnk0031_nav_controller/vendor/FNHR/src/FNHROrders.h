/*
 * File       Control orders for Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#pragma once

class Orders
{
  // Format:  [transStart] [order] [data 0] [data 1] ... [data n] [transEnd]
  //          [x] is byte type and the range of [order] and [data x] is 0~127
  // Process: The requesting party send the order, then the responding party respond the order.
  //          The non blocking order will be responded immediately, and the blocking order will
  //          be responded orderStart immediately, then respond orderDone after completion.

public:
  // Data stream control orders, range is 128 ~ 255
  // These orders are used to control data stream.

  static const byte transStart = 128;
  static const byte transEnd = 129;


  // Orders, range is 0 ~ 127
  // Orders are used to control target.
  // Some orders have proprietary response orders, others use orderStart and orderDone.
  // The even orders is sent by the requesting party, and the odd orders is sent by the responding party.

  // Non blocking orders, range is 0 ~ 63

  // Connection
  // Request echo, to confirm the target
  static const byte requestEcho = 0;                // [order]
  // Respond echo
  static const byte echo = 1;                       // [order]

  // Function
  // Request supply voltage
  static const byte requestSupplyVoltage = 10;      // [order]
  // Respond supply voltage
  static const byte supplyVoltage = 11;             // [order] [voltage * 100 / 128] [voltage * 100 % 128]
  // Request change I/O port state
  static const byte requestChangeIO = 20;           // [order] [IOindex] [1/0]

  // Installation
  static const byte requestMoveLeg = 30;            // [order] [leg] [64 + dx] [64 + dy] [64 + dz]
  static const byte requestCalibrate = 32;          // [order]

  // Blocking orders, range is 64 ~ 127

  // Installation
  static const byte requestInstallState = 64;       // [order]
  static const byte requestCalibrateState = 66;     // [order]
  static const byte requestBootState = 68;          // [order]
  static const byte requestCalibrateVerify = 70;    // [order]

  // Simple action
  static const byte requestCrawlForward = 80;       // [order]
  static const byte requestCrawlBackward = 82;      // [order]
  static const byte requestCrawlLeft = 84;          // [order]
  static const byte requestCrawlRight = 86;         // [order]
  static const byte requestTurnLeft = 88;           // [order]
  static const byte requestTurnRight = 90;          // [order]
  static const byte requestActiveMode = 92;         // [order]
  static const byte requestSleepMode = 94;          // [order]
  static const byte requestSwitchMode = 96;         // [order]

  // Complex action
  static const byte requestCrawl = 110;             // [order] [64 + x] [64 + y] [64 + angle]
  static const byte requestChangeBodyHeight = 112;  // [order] [64 + height]
  static const byte requestMoveBody = 114;          // [order] [64 + x] [64 + y] [64 + z]
  static const byte requestRotateBody = 116;        // [order] [64 + x] [64 + y] [64 + z]
  static const byte requestTwistBody = 118;         // [order] [64 + xMove] [64 + yMove] [64 + zMove] [64 + xRotate] [64 + yRotate] [64 + zRotate]

  // Universal responded orders, range is 21 ~ 127
  // These orders are used to respond orders without proprietary response orders.

  static const byte orderStart = 21;                // [order]
  static const byte orderDone = 23;                 // [order]
};
