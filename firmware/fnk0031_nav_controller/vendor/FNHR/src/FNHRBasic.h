/*
 * File       Basic classes for Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#pragma once
#if defined(ARDUINO_AVR_MEGA2560)

#include <Arduino.h>
#include <Servo.h>
#include <EEPROM.h>
#include <FlexiTimer2.h>

class RobotShape
{
public:
  float a;
  float b;
  float g;
  float c;
  float d;
  float e;
  float f;
};

class EepromAddresses
{
public:
  static constexpr float dataFormatVersion = 0;
  static constexpr float productVersion = 3;

  static constexpr float servo22 = 100;
  static constexpr float servo23 = 102;
  static constexpr float servo24 = 104;
  static constexpr float servo25 = 106;
  static constexpr float servo26 = 108;
  static constexpr float servo27 = 110;
  static constexpr float servo28 = 112;
  static constexpr float servo29 = 114;
  static constexpr float servo30 = 116;
  static constexpr float servo39 = 118;
  static constexpr float servo38 = 120;
  static constexpr float servo37 = 122;
  static constexpr float servo36 = 124;
  static constexpr float servo35 = 126;
  static constexpr float servo34 = 128;
  static constexpr float servo33 = 130;
  static constexpr float servo32 = 132;
  static constexpr float servo31 = 134;

  static constexpr float robotState = 140;
};

class Power
{
public:
  Power();
  void Set(float adcReference, float samplingProportion, bool powerGroupAutoSwitch);

  bool powerGroupAutoSwitch;

  volatile float voltage;
  volatile bool powerGroupState;

  void Update();

private:
  const int samplingPin = A7;
  float adcReference;
  float samplingProportion;
  static const int samplingSize = 25;
  float samplingData[samplingSize];
  int samplingDataCounter = 0;
  static const int samplingPeakSize = 25;
  float samplingPeakData[samplingPeakSize];
  int samplingPeakDataCounter = 0;

  void Sampling();

  const int powerGroup1Pin = A15;
  const int powerGroup2Pin = A13;
  const int powerGroup3Pin = A14;
  const int powerGroupBootInterval = 5;
  const float powerGroupOnVoltage = 6.5;
  const float powerGroupOffVoltage = 5.5;
  bool powerGroup1State = false;
  bool powerGroup2State = false;
  bool powerGroup3State = false;

  void SetPowerGroupState(int group, bool state);

  int updateCounter = 0;
};

class Point
{
public:
  Point();
  Point(float x, float y, float z);

  static float GetDistance(Point point1, Point point2);

  volatile float x, y, z;
};

class RobotLegsPoints
{
public:
  RobotLegsPoints();
  RobotLegsPoints(Point leg1, Point leg2, Point leg3, Point leg4, Point leg5, Point leg6);

  Point leg1, leg2, leg3, leg4, leg5, leg6;
};

class RobotJoint
{
public:
  RobotJoint();
  void Set(int servoPin, float jointZero, bool jointDir, float jointMinAngle, float jointMaxAngle, int offsetAddress);

  void SetOffset(float offset);
  void SetOffsetEnableState(bool state);

  void RotateToDirectly(float jointAngle);

  float GetJointAngle(float servoAngle);

  bool CheckJointAngle(float jointAngle);

  volatile float jointAngleNow;
  volatile float servoAngleNow;

  static int firstRotateDelay;

private:
  Servo servo;
  int servoPin;
  float jointZero;
  bool jointDir;
  float jointMinAngle;
  float jointMaxAngle;
  int offsetAddress;
  volatile float offset = 0;
  volatile bool isOffsetEnable = true;
  volatile bool isFirstRotate = true;
};

class RobotLeg
{
public:
  RobotLeg();
  void Set(float xOrigin, float yOrigin, RobotShape robotShape);

  void SetOffsetEnableState(bool state);

  void CalculatePoint(float alpha, float beta, float gamma, volatile float &x, volatile float &y, volatile float &z);
  void CalculatePoint(float alpha, float beta, float gamma, Point &point);
  void CalculateAngle(float x, float y, float z, float &alpha, float &beta, float &gamma);
  void CalculateAngle(Point point, float &alpha, float &beta, float &gamma);

  bool CheckPoint(Point point);
  bool CheckAngle(float alpha, float beta, float gamma);

  void MoveTo(Point point);
  void MoveToRelatively(Point point);
  void WaitUntilFree();

  void ServosRotateTo(float angleA, float angleB, float angleC);

  void MoveToDirectly(Point point);
  void MoveToDirectlyRelatively(Point point);

  volatile bool isBusy = false;

  RobotJoint jointA, jointB, jointC;
  Point pointNow, pointGoal;

  static constexpr float negligibleDistance = 0.1;
  static constexpr float defaultStepDistance = 2;
  volatile float stepDistance = defaultStepDistance;

private:
  float xOrigin, yOrigin;
  RobotShape robotShape;
  volatile bool isFirstMove = true;

  void RotateToDirectly(float alpha, float beta, float gamma);
};

class Robot
{
public:
  Robot();
  void Start();

  enum State { Install, Calibrate, Boot, Action };
  State state = State::Boot;

  void InstallState();
  void CalibrateState();
  void CalibrateServos();
  void CalibrateVerify();
  void BootState();

  void MoveTo(RobotLegsPoints points);
  void MoveTo(RobotLegsPoints points, float speed);
  void MoveToRelatively(Point point);
  void MoveToRelatively(Point point, float speed);
  void WaitUntilFree();

  void SetSpeed(float speed);
  void SetSpeed(float speed1, float speed2, float speed3, float speed4, float speed5, float speed6);

  void SetSpeedMultiple(float multiple);

  bool CheckPoints(RobotLegsPoints points);

  void GetPointsNow(RobotLegsPoints &points);

  void Update();

  RobotLeg leg1, leg2, leg3, leg4, leg5, leg6;

  const RobotLegsPoints calibrateStatePoints = RobotLegsPoints(
    Point(-133, 100, 25),
    Point(-155, 0, 25),
    Point(-133, -100, 25),
    Point(133, 100, 25),
    Point(155, 0, 25),
    Point(133, -100, 25));
  const RobotLegsPoints calibratePoints = RobotLegsPoints(
    Point(-103, 85, 0),
    Point(-125, 0, 0),
    Point(-103, -85, 0),
    Point(103, 85, 0),
    Point(125, 0, 0),
    Point(103, -85, 0));
  const RobotLegsPoints bootPoints = RobotLegsPoints(
    Point(-81, 99, 0),
    Point(-115, 0, 0),
    Point(-81, -99, 0),
    Point(81, 99, 0),
    Point(115, 0, 0),
    Point(81, -99, 0));

  int dataFormatVersion;
  int productVersion;
  Power power;

private:
  volatile float speedMultiple = 1;

  void CalibrateLeg(RobotLeg &leg, Point calibratePoint);

  void UpdateAction();
  void UpdateLegAction(RobotLeg &leg);

  void MoveToDirectly(RobotLegsPoints points);

  void SetOffsetEnableState(bool state);

  RobotShape robotShape;
};

class RobotAction
{
public:
  RobotAction();
  void Start();

  void SetSpeedMultiple(float multiple);
  void SetActionGroup(int group);

  void ActiveMode();
  void SleepMode();
  void SwitchMode();

  void CrawlForward();
  void CrawlBackward();
  void CrawlLeft();
  void CrawlRight();
  void TurnLeft();
  void TurnRight();

  void Crawl(float x, float y, float angle);

  void ChangeBodyHeight(float height);

  void MoveBody(float x, float y, float z);
  void RotateBody(float x, float y, float z);

  void TwistBody(Point move, Point rotate);

  void InitialState();

  void LegMoveToRelatively(int leg, Point point);

  void LegMoveToRelativelyDirectly(int leg, Point point);

  Robot robot;

private:
  void ActionState();

  enum Mode { Active, Sleep };
  Mode mode = Mode::Sleep;

  enum LegsState { CrawlState, TwistBodyState, LegMoveState };
  LegsState legsState = LegsState::CrawlState;

  RobotLegsPoints initialPoints;
  RobotLegsPoints lastChangeLegsStatePoints;

  const float crawlLength = 42;
  const float turnAngle = 18;

  const float legLift = 20;
  const float legLiftSpeed = 7.5;
  const float defaultBodyLift = 15;
  float bodyLift = defaultBodyLift;
  const float bodyLiftSpeed = 1;

  const float minAlphaInterval = 0;

  int crawlSteps = 2;
  int legMoveIndex = 1;

  bool CheckCrawlPoints(RobotLegsPoints points);

  void GetCrawlPoints(RobotLegsPoints &points, Point point);
  void GetCrawlPoint(Point &point, Point direction);

  void GetTurnPoints(RobotLegsPoints &points, float angle);
  void GetTurnPoint(Point &point, float angle);

  const float speedTwistBody = 1.25;

  void TwistBody(Point move, Point rotateAxis, float rotateAngle);

  void GetMoveBodyPoints(RobotLegsPoints &points, Point point);
  void GetMoveBodyPoint(Point &point, Point direction);

  void GetRotateBodyPoints(RobotLegsPoints &points, Point rotateAxis, float rotateAngle);
  void GetRotateBodyPoint(Point &point, Point rotateAxis, float rotateAngle);

  void LegsMoveTo(RobotLegsPoints points);
  void LegsMoveTo(RobotLegsPoints points, float speed);
  void LegsMoveTo(RobotLegsPoints points, int leg, float legSpeed);
  void LegsMoveToRelatively(Point point, float speed);
};

#endif
