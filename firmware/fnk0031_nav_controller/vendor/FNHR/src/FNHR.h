/*
 * File       Class for control Freenove Hexapod Robot
 * Brief      Users can directly use this class to control Freenove Hexapod Robot.
 *            This class is very easy to use, users can use its member functions directly without any concerns.
 *            Conversions between different actions will be performed automatically.
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#pragma once

#include "FNHRRemote.h"

#if defined(ARDUINO_AVR_MEGA2560)

#include "FNHRComm.h"

class FNHR
{
public:
  FNHR();

  // Returns FNHR's command-derived leg state, not measured servo feedback.
  bool GetEstimatedLegState(int leg, float &x, float &y, float &z,
                            float &jointA, float &jointB, float &jointC);

 /*
  * Brief     Start the robot
  * Param     commFunction  Whether to open communication function
  *             true        The robot will be controlled by remote, Android APP or Processing APP
  *             false       You can only use the member functions of this class to control the robot
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Start(bool commFunction = false);

 /*
  * Brief     Update the communication function
  *           If the communication function is opened, the loop() function should only call this function.
  *           Else this function should not be called.
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Update();

 /*
  * Brief     Set Wi-Fi name and password
  *           Call this function before Start()
  *           If don't call this function, will use default name and password.
  * Param     name      Wi-Fi name
  *           password  Wi-Fi password, at least 8 characters, case sensitive
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetWiFi(String name, String password);

 /*
  * Brief     Set Wi-Fi channel
  *           Call this function before Start()
  *           If don't call this function, will select the most unblocked channel.
  * Param     channel   Wi-Fi channel, 1 ~ 13
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetWiFiChannel(byte channel);

 /*
  * Brief     Set remote address
  *           Call this function before Start()
  *           If don't call this function, will use default address.
  *           The remote should set the same address to control this robot.
  * Param     bytex     bytes to define the address
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetRemote(byte byte0, byte byte1, byte byte2, byte byte3, byte byte4);

 /*
  * Brief     Set remote channel
  *           Call this function before Start()
  *           If don't call this function, will use default channel.
  *           The remote should set the same channel  to control this robot.
  * Param     channel   RF24 channel, 0 ~ 125, default: 125
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetRemoteChannel(byte channel);

 /*
  * Brief     Activate the robot
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void ActiveMode();

 /*
  * Brief     Deactivate the robot, this mode is more power saving
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SleepMode();

 /*
  * Brief     Switch between active and sleep mode
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SwitchMode();

 /*
  * Brief     Crawl forward
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void CrawlForward();

 /*
  * Brief     Crawl backward
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void CrawlBackward();

 /*
  * Brief     Crawl left
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void CrawlLeft();

 /*
  * Brief     Crawl right
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void CrawlRight();

 /*
  * Brief     Turn left
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void TurnLeft();

 /*
  * Brief     Turn right
  * Param     None
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void TurnRight();

 /*
  * Brief     Crawl
  *           Move and rotate will only execute 1/steps for each call.
  *           The steps is in a whole loop and defined by action group.
  * Param     x, y      The direction and distance want to move
  *           angle     The angle want to rotate
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void Crawl(float x, float y, float angle);

 /*
  * Brief     Change body height
  * Param     height    The height want to change
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void ChangeBodyHeight(float height);

 /*
  * Brief     Move body
  * Param     x, y, z   The direction and distance want body to move
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void MoveBody(float x, float y, float z);

 /*
  * Brief     Rotate body
  * Param     x, y, z   The direction and degree want body to rotate
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void RotateBody(float x, float y, float z);

 /*
  * Brief     Twist body
  * Param     xMove, yMove, zMove           The direction and distance want body to move
  *           xRotate, yRotate, zRotate     The direction and degree want body to rotate
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void TwistBody(float xMove, float yMove, float zMove, float xRotate, float yRotate, float zRotate);

 /*
  * Brief     Move leg relatively
  * Param     leg       The leg want to move
  *           x, y, z   The direction and distance want leg to move
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void LegMoveToRelatively(int leg, float x, float y, float z);

 /*
  * Brief     Set action speed
  *           If the communication function is opened, call this function before Start().
  *           If don't call this function, will use default action speed.
  * Param     speed     The action speed of the robot, 1~100
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetActionSpeed(float speed);

 /*
  * Brief     Set action group
  *           If the communication function is opened, call this function before Start().
  *           If don't call this function, will use default action group.
  * Param     group     The action group of the robot
  *             1       Need 2 steps to complete a loop, the fastest way
  *             2       Need 4 steps to complete a loop
  *             3       Need 6 steps to complete a loop, the slowest way
  * Retval    None
  * -----------------------------------------------------------------------------------------------*/
  void SetActionGroup(int group);

private:
  Communication communication;
};

#endif
