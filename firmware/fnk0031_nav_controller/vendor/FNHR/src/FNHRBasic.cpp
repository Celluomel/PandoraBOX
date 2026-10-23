/*
 * File       Basic classes for Freenove Hexapod Robot
 * Author     Ethan Pan @ Freenove (support@freenove.com)
 * Date       2023/09/19
 * Version    V12.6
 * Copyright  Copyright © Freenove (http://www.freenove.com)
 * License    Creative Commons Attribution ShareAlike 3.0
 *            (http://creativecommons.org/licenses/by-sa/3.0/legalcode)
 * -----------------------------------------------------------------------------------------------*/

#if defined(ARDUINO_AVR_MEGA2560)

#include "FNHRBasic.h"

Power::Power() {}

void Power::Set(float adcReference, float samplingProportion, bool powerGroupAutoSwitch)
{
  this->adcReference = adcReference;
  this->samplingProportion = samplingProportion;
  this->powerGroupAutoSwitch = powerGroupAutoSwitch;

  for (int i = 0; i < samplingSize; i++)
    samplingData[i] = 0;

  pinMode(powerGroup1Pin, OUTPUT);
  pinMode(powerGroup2Pin, OUTPUT);
  pinMode(powerGroup3Pin, OUTPUT);
}

void Power::Update()
{
  Sampling();

  if (!powerGroupAutoSwitch)
    return;

  if (voltage > powerGroupOnVoltage)
    powerGroupState = true;
  else if (voltage < powerGroupOffVoltage)
    powerGroupState = false;

  if (++updateCounter < powerGroupBootInterval)
    return;
  updateCounter = 0;

  if (powerGroupState)
  {
    if (!powerGroup1State)
    {
      SetPowerGroupState(1, true);
      return;
    }
    else if (!powerGroup2State)
    {
      SetPowerGroupState(2, true);
      return;
    }
    else if (!powerGroup3State)
    {
      SetPowerGroupState(3, true);
      return;
    }
  }
  else
  {
    if (powerGroup1State)
    {
      SetPowerGroupState(1, false);
      return;
    }
    else if (powerGroup2State)
    {
      SetPowerGroupState(2, false);
      return;
    }
    else if (powerGroup3State)
    {
      SetPowerGroupState(3, false);
      return;
    }
  }
}

void Power::Sampling()
{
  float voltage = analogRead(samplingPin) * adcReference / 1023 / samplingProportion;

  samplingData[samplingDataCounter++] = voltage;
  if (samplingDataCounter == samplingSize)
    samplingDataCounter = 0;

  float peakVoltage = 0;
  for (int i = 0; i < samplingSize; i++)
    if (peakVoltage < samplingData[i])
      peakVoltage = samplingData[i];

  samplingPeakData[samplingPeakDataCounter++] = peakVoltage;
  if (samplingPeakDataCounter == samplingPeakSize)
    samplingPeakDataCounter = 0;

  float averagePeakVoltage = 0;
  for (int i = 0; i < samplingPeakSize; i++)
    averagePeakVoltage += samplingPeakData[i];
  averagePeakVoltage /= samplingPeakSize;

  this->voltage = averagePeakVoltage;
}

void Power::SetPowerGroupState(int group, bool state)
{
  switch (group)
  {
  case 1:
    digitalWrite(powerGroup1Pin, state);
    powerGroup1State = state;
    break;
  case 2:
    digitalWrite(powerGroup2Pin, state);
    powerGroup2State = state;
    break;
  case 3:
    digitalWrite(powerGroup3Pin, state);
    powerGroup3State = state;
    break;
  }
}

Point::Point() {}

Point::Point(float x, float y, float z)
{
  this->x = x;
  this->y = y;
  this->z = z;
}

float Point::GetDistance(Point point1, Point point2)
{
  return sqrt(pow(point1.x - point2.x, 2) + pow(point1.y - point2.y, 2) + pow(point1.z - point2.z, 2));
}

RobotLegsPoints::RobotLegsPoints() {}

RobotLegsPoints::RobotLegsPoints(Point leg1, Point leg2, Point leg3, Point leg4, Point leg5, Point leg6)
{
  this->leg1 = leg1;
  this->leg2 = leg2;
  this->leg3 = leg3;
  this->leg4 = leg4;
  this->leg5 = leg5;
  this->leg6 = leg6;
}

RobotJoint::RobotJoint() {}

int RobotJoint::firstRotateDelay = 0;

void RobotJoint::Set(int servoPin, float jointZero, bool jointDir, float jointMinAngle, float jointMaxAngle, int offsetAddress)
{
  this->servoPin = servoPin;
  this->jointZero = jointZero;
  this->jointDir = jointDir;
  this->offsetAddress = offsetAddress;
  this->jointMinAngle = jointMinAngle;
  this->jointMaxAngle = jointMaxAngle;

  int offsetInt = EEPROM.read(offsetAddress) * 256 + EEPROM.read(offsetAddress + 1);
  offsetInt = offsetInt / 2 * ((offsetInt % 2) ? 1 : -1);
  float offset = offsetInt * 0.01;
  this->offset = offset;
}

void RobotJoint::SetOffset(float offset)
{
  while (offset > 180)
    offset -= 360;
  while (offset < -180)
    offset += 360;

  int offsetInt = offset * 100;
  offsetInt = abs(offsetInt) * 2 + ((offset > 0) ? 1 : 0);

  if (offsetInt < 0 || offsetInt > 65535)
    return;

  EEPROM.write(offsetAddress, offsetInt / 256);
  EEPROM.write(offsetAddress + 1, offsetInt % 256);
  this->offset = offset;
}

void RobotJoint::SetOffsetEnableState(bool state)
{
  isOffsetEnable = state;
}

void RobotJoint::RotateToDirectly(float jointAngle)
{
  if (!CheckJointAngle(jointAngle))
    return;

  float servoAngle;

  if (isOffsetEnable)
    servoAngle = jointZero + (jointDir ? 1 : -1) * (jointAngle + offset);
  else
    servoAngle = jointZero + (jointDir ? 1 : -1) * jointAngle;

  while (servoAngle > 360)
    servoAngle -= 360;
  while (servoAngle < 0)
    servoAngle += 360;
  if (servoAngle > 180)
    return;

  if (isFirstRotate)
  {
    isFirstRotate = false;
    servo.attach(servoPin);
    servo.write(servoAngle);
    delay(firstRotateDelay);
  }
  else
  {
    servo.write(servoAngle);
  }

  jointAngleNow = jointAngle;
  servoAngleNow = servoAngle;
}

float RobotJoint::GetJointAngle(float servoAngle)
{
  return (jointDir ? 1 : -1) * (servoAngle - jointZero);
}

bool RobotJoint::CheckJointAngle(float jointAngle)
{
  while (jointAngle > jointMaxAngle)
    jointAngle -= 360;
  while (jointAngle < jointMinAngle)
    jointAngle += 360;

  if (jointAngle >= jointMinAngle && jointAngle <= jointMaxAngle)
    return true;
  else
    return false;
}

RobotLeg::RobotLeg() {}

void RobotLeg::Set(float xOrigin, float yOrigin, RobotShape robotShape)
{
  this->xOrigin = xOrigin;
  this->yOrigin = yOrigin;
  this->robotShape = robotShape;
}

void RobotLeg::SetOffsetEnableState(bool state)
{
  jointA.SetOffsetEnableState(state);
  jointB.SetOffsetEnableState(state);
  jointC.SetOffsetEnableState(state);
}

void RobotLeg::CalculatePoint(float alpha, float beta, float gamma, volatile float &x, volatile float &y, volatile float &z)
{
  // transform angle to radian
  alpha = alpha * PI / 180;
  beta = beta * PI / 180;
  gamma = gamma * PI / 180;
  // calculate u-v coordinate
  float u, v;
  u = robotShape.d + robotShape.e * sin(beta) + robotShape.f * sin(gamma - beta);
  v = robotShape.c + robotShape.e * cos(beta) - robotShape.f * cos(gamma - beta);
  // calculate x-y-z coordinate
  x = xOrigin + u * cos(alpha);
  y = yOrigin + u * sin(alpha);
  z = v;
}

void RobotLeg::CalculatePoint(float alpha, float beta, float gamma, Point &point)
{
  CalculatePoint(alpha, beta, gamma, point.x, point.y, point.z);
}

void RobotLeg::CalculateAngle(float x, float y, float z, float &alpha, float &beta, float &gamma)
{
  // calculate u-v angle
  float u, v;
  u = sqrt(pow(x - xOrigin, 2) + pow(y - yOrigin, 2));
  v = z;
  beta = PI / 2 - acos((pow(robotShape.e, 2) + (pow(u - robotShape.d, 2) + pow(v - robotShape.c, 2)) - pow(robotShape.f, 2)) / (2 * robotShape.e * sqrt(pow(u - robotShape.d, 2) + pow(v - robotShape.c, 2)))) - atan2(v - robotShape.c, u - robotShape.d);
  gamma = acos((pow(robotShape.e, 2) + pow(robotShape.f, 2) - (pow(u - robotShape.d, 2) + pow(v - robotShape.c, 2))) / (2 * robotShape.e * robotShape.f));
  // calculate x-y-z angle
  alpha = atan2(y - yOrigin, x - xOrigin);
  if (xOrigin < 0 && yOrigin < 0)
    alpha = alpha + PI;
  if (xOrigin < 0 && yOrigin < 0)
    alpha = alpha + PI;
  // transform radian to angle
  alpha = alpha * 180 / PI;
  beta = beta * 180 / PI;
  gamma = gamma * 180 / PI;
}

void RobotLeg::CalculateAngle(Point point, float &alpha, float &beta, float &gamma)
{
  CalculateAngle(point.x, point.y, point.z, alpha, beta, gamma);
}

bool RobotLeg::CheckPoint(Point point)
{
  float alpha, beta, gamma;
  CalculateAngle(point, alpha, beta, gamma);
  if (CheckAngle(alpha, beta, gamma))
  {
    Point pointNew;
    CalculatePoint(alpha, beta, gamma, pointNew);
    if (Point::GetDistance(point, pointNew) < negligibleDistance)
      return true;
  }
  return false;
}

bool RobotLeg::CheckAngle(float alpha, float beta, float gamma)
{
  if (jointA.CheckJointAngle(alpha) && jointB.CheckJointAngle(beta) && jointC.CheckJointAngle(gamma))
    return true;
  else
    return false;
}

void RobotLeg::MoveTo(Point point)
{
  pointGoal = point;
  isBusy = true;
}

void RobotLeg::MoveToRelatively(Point point)
{
  point = Point(pointGoal.x + point.x, pointGoal.y + point.y, pointGoal.z + point.z);
  MoveTo(point);
}

void RobotLeg::WaitUntilFree()
{
  while (isBusy);
}

void RobotLeg::ServosRotateTo(float angleA, float angleB, float angleC)
{
  float alpha = jointA.GetJointAngle(angleA);
  float beta = jointB.GetJointAngle(angleB);
  float gamma = jointC.GetJointAngle(angleC);

  Point point;
  CalculatePoint(alpha, beta, gamma, point);

  MoveTo(point);
}

void RobotLeg::MoveToDirectly(Point point)
{
  float alpha, beta, gamma;
  CalculateAngle(point, alpha, beta, gamma);
  RotateToDirectly(alpha, beta, gamma);
}

void RobotLeg::MoveToDirectlyRelatively(Point point)
{
  point = Point(pointGoal.x + point.x, pointGoal.y + point.y, pointGoal.z + point.z);
  MoveToDirectly(point);
}

void RobotLeg::RotateToDirectly(float alpha, float beta, float gamma)
{
  jointC.RotateToDirectly(gamma);
  jointB.RotateToDirectly(beta);
  jointA.RotateToDirectly(alpha);

  Point point;
  CalculatePoint(alpha, beta, gamma, point);

  if (isFirstMove)
  {
    isFirstMove = false;
    pointGoal = point;
  }

  pointNow = point;
}

Robot::Robot() {}

void Robot::Start()
{
  dataFormatVersion = EEPROM.read(EepromAddresses::dataFormatVersion);

  switch (dataFormatVersion)
  {
    float defaultReference;
    float externalReference;

  case 1:
    productVersion = EEPROM.read(EepromAddresses::productVersion);
    switch (productVersion)
    {
    case 30:
    case 31:
    case 32:
      productVersion = 3;
      RobotJoint::firstRotateDelay = 0;

      robotShape.a = 35;
      robotShape.b = 50;
      robotShape.g = 49;
      robotShape.c = 15.75;
      robotShape.d = 22.75;
      robotShape.e = 55;
      robotShape.f = 70;

      defaultReference = 2.5 / analogRead(A6) * 1023;
      analogReference(EXTERNAL);
      externalReference = defaultReference * 2 / (6.2 + 2) / analogRead(A8) * 1023;
      power.Set(externalReference, 2.0 / (6.2 + 2.0), true);
      break;

    default:
      while (true);
    }
    break;

  case 20:
    productVersion = 2;
    RobotJoint::firstRotateDelay = 0;

    robotShape.a = 32;
    robotShape.b = 50;
    robotShape.g = 46;
    robotShape.c = 15.75;
    robotShape.d = 22.75;
    robotShape.e = 55;
    robotShape.f = 70;

    analogReference(EXTERNAL);
    power.Set(2.5 * 32.0 / (6.2 + 32.0), 2.0 / (6.2 + 2.0), true);
    break;

  default:
    productVersion = 1;
    RobotJoint::firstRotateDelay = 50;

    robotShape.a = 32;
    robotShape.b = 50;
    robotShape.g = 46;
    robotShape.c = 15.75;
    robotShape.d = 22.75;
    robotShape.e = 55;
    robotShape.f = 70;

    power.Set(5.0, 10.0 / (10.0 + 10.0), false);
    break;
  }

  leg1.Set(-robotShape.a, robotShape.b, robotShape);
  leg2.Set(-robotShape.g, 0, robotShape);
  leg3.Set(-robotShape.a, -robotShape.b, robotShape);
  leg4.Set(robotShape.a, robotShape.b, robotShape);
  leg5.Set(robotShape.g, 0, robotShape);
  leg6.Set(robotShape.a, -robotShape.b, robotShape);

  leg1.jointA.Set(22, -45, true, 90, 200, EepromAddresses::servo22);
  leg1.jointB.Set(23, 0, true, 0, 180, EepromAddresses::servo23);
  leg1.jointC.Set(24, 0, true, 0, 180, EepromAddresses::servo24);
  leg2.jointA.Set(25, -90, true, 135, 225, EepromAddresses::servo25);
  leg2.jointB.Set(26, 0, true, 0, 180, EepromAddresses::servo26);
  leg2.jointC.Set(27, 0, true, 0, 180, EepromAddresses::servo27);
  leg3.jointA.Set(28, -135, true, -200, -90, EepromAddresses::servo28);
  leg3.jointB.Set(29, 0, true, 0, 180, EepromAddresses::servo29);
  leg3.jointC.Set(30, 0, true, 0, 180, EepromAddresses::servo30);
  leg4.jointA.Set(39, 45, true, -20, 90, EepromAddresses::servo39);
  leg4.jointB.Set(38, 180, false, 0, 180, EepromAddresses::servo38);
  leg4.jointC.Set(37, 180, false, 0, 180, EepromAddresses::servo37);
  leg5.jointA.Set(36, 90, true, -45, 45, EepromAddresses::servo36);
  leg5.jointB.Set(35, 180, false, 0, 180, EepromAddresses::servo35);
  leg5.jointC.Set(34, 180, false, 0, 180, EepromAddresses::servo34);
  leg6.jointA.Set(33, 135, true, -90, 20, EepromAddresses::servo33);
  leg6.jointB.Set(32, 180, false, 0, 180, EepromAddresses::servo32);
  leg6.jointC.Set(31, 180, false, 0, 180, EepromAddresses::servo31);

  MoveToDirectly(bootPoints);
}

void Robot::InstallState()
{
  state = State::Install;
  SetOffsetEnableState(false);
  SetSpeed(RobotLeg::defaultStepDistance);
  leg1.ServosRotateTo(90, 90, 90);
  leg2.ServosRotateTo(90, 90, 90);
  leg3.ServosRotateTo(90, 90, 90);
  leg4.ServosRotateTo(90, 90, 90);
  leg5.ServosRotateTo(90, 90, 90);
  leg6.ServosRotateTo(90, 90, 90);
  WaitUntilFree();
}

void Robot::CalibrateState()
{
  state = State::Calibrate;
  SetOffsetEnableState(false);
  SetSpeed(RobotLeg::defaultStepDistance);
  MoveTo(calibrateStatePoints);
  WaitUntilFree();
}

void Robot::CalibrateServos()
{
  if (state != State::Calibrate)
    return;
  CalibrateLeg(leg1, calibratePoints.leg1);
  CalibrateLeg(leg2, calibratePoints.leg2);
  CalibrateLeg(leg3, calibratePoints.leg3);
  CalibrateLeg(leg4, calibratePoints.leg4);
  CalibrateLeg(leg5, calibratePoints.leg5);
  CalibrateLeg(leg6, calibratePoints.leg6);
  SetOffsetEnableState(true);
}

void Robot::CalibrateVerify()
{
  state = State::Calibrate;
  SetSpeed(RobotLeg::defaultStepDistance);
  MoveTo(calibrateStatePoints);
  WaitUntilFree();
  SetOffsetEnableState(true);
  MoveTo(calibratePoints);
  WaitUntilFree();
}

void Robot::BootState()
{
  SetOffsetEnableState(true);
  SetSpeed(RobotLeg::defaultStepDistance);
  MoveTo(bootPoints);
  WaitUntilFree();
  state = State::Boot;
}

void Robot::MoveTo(RobotLegsPoints points)
{
  leg1.MoveTo(points.leg1);
  leg2.MoveTo(points.leg2);
  leg3.MoveTo(points.leg3);
  leg4.MoveTo(points.leg4);
  leg5.MoveTo(points.leg5);
  leg6.MoveTo(points.leg6);
}

void Robot::MoveTo(RobotLegsPoints points, float speed)
{
  SetSpeed(speed);
  MoveTo(points);
}

void Robot::MoveToRelatively(Point point)
{
  leg1.MoveToRelatively(point);
  leg2.MoveToRelatively(point);
  leg3.MoveToRelatively(point);
  leg4.MoveToRelatively(point);
  leg5.MoveToRelatively(point);
  leg6.MoveToRelatively(point);
}

void Robot::MoveToRelatively(Point point, float speed)
{
  SetSpeed(speed);
  MoveToRelatively(point);
}

void Robot::WaitUntilFree()
{
  while (leg1.isBusy || leg2.isBusy || leg3.isBusy || leg4.isBusy || leg5.isBusy || leg6.isBusy);
}

void Robot::SetSpeed(float speed)
{
  leg1.stepDistance = speed;
  leg2.stepDistance = speed;
  leg3.stepDistance = speed;
  leg4.stepDistance = speed;
  leg5.stepDistance = speed;
  leg6.stepDistance = speed;
}

void Robot::SetSpeed(float speed1, float speed2, float speed3, float speed4, float speed5, float speed6)
{
  leg1.stepDistance = speed1;
  leg2.stepDistance = speed2;
  leg3.stepDistance = speed3;
  leg4.stepDistance = speed4;
  leg5.stepDistance = speed5;
  leg6.stepDistance = speed6;
}

void Robot::SetSpeedMultiple(float multiple)
{
  multiple = constrain(multiple, 0.01, 1);
  speedMultiple = multiple;
}

bool Robot::CheckPoints(RobotLegsPoints points)
{
  if (leg1.CheckPoint(points.leg1) &&
    leg2.CheckPoint(points.leg2) &&
    leg3.CheckPoint(points.leg3) &&
    leg4.CheckPoint(points.leg4) &&
    leg5.CheckPoint(points.leg5) &&
    leg6.CheckPoint(points.leg6))
    return true;
  return false;
}

void Robot::GetPointsNow(RobotLegsPoints & points)
{
  points.leg1 = leg1.pointNow;
  points.leg2 = leg2.pointNow;
  points.leg3 = leg3.pointNow;
  points.leg4 = leg4.pointNow;
  points.leg5 = leg5.pointNow;
  points.leg6 = leg6.pointNow;
}

void Robot::Update()
{
  UpdateAction();
  power.Update();
}

void Robot::CalibrateLeg(RobotLeg &leg, Point calibratePoint)
{
  float alpha, beta, gamma;
  leg.CalculateAngle(calibratePoint, alpha, beta, gamma);
  leg.jointA.SetOffset(leg.jointA.jointAngleNow - alpha);
  leg.jointB.SetOffset(leg.jointB.jointAngleNow - beta);
  leg.jointC.SetOffset(leg.jointC.jointAngleNow - gamma);
}

void Robot::UpdateAction()
{
  UpdateLegAction(leg1);
  UpdateLegAction(leg2);
  UpdateLegAction(leg3);
  UpdateLegAction(leg4);
  UpdateLegAction(leg5);
  UpdateLegAction(leg6);
}

void Robot::UpdateLegAction(RobotLeg &leg)
{
  float distance = Point::GetDistance(leg.pointNow, leg.pointGoal);
  float xDistance = leg.pointGoal.x - leg.pointNow.x;
  float yDistance = leg.pointGoal.y - leg.pointNow.y;
  float zDistance = leg.pointGoal.z - leg.pointNow.z;
  float xStep = xDistance / distance * leg.stepDistance * speedMultiple;
  float yStep = yDistance / distance * leg.stepDistance * speedMultiple;
  float zStep = zDistance / distance * leg.stepDistance * speedMultiple;
  Point pointGoal = Point(leg.pointNow.x + xStep, leg.pointNow.y + yStep, leg.pointNow.z + zStep);

  if (distance >= leg.stepDistance * speedMultiple && distance >= RobotLeg::negligibleDistance)
  {
    leg.isBusy = true;
    leg.MoveToDirectly(pointGoal);
  }
  else if (leg.isBusy)
  {
    leg.MoveToDirectly(leg.pointGoal);
    leg.isBusy = false;
  }
}

void Robot::MoveToDirectly(RobotLegsPoints points)
{
  leg1.MoveToDirectly(points.leg1);
  leg2.MoveToDirectly(points.leg2);
  leg3.MoveToDirectly(points.leg3);
  leg4.MoveToDirectly(points.leg4);
  leg5.MoveToDirectly(points.leg5);
  leg6.MoveToDirectly(points.leg6);
}

void Robot::SetOffsetEnableState(bool state)
{
  leg1.SetOffsetEnableState(state);
  leg2.SetOffsetEnableState(state);
  leg3.SetOffsetEnableState(state);
  leg4.SetOffsetEnableState(state);
  leg5.SetOffsetEnableState(state);
  leg6.SetOffsetEnableState(state);
}

RobotAction::RobotAction() {}

void RobotAction::Start()
{
  robot.Start();

  initialPoints = robot.bootPoints;
  GetCrawlPoints(initialPoints, Point(0, 0, -bodyLift));
}

void RobotAction::SetSpeedMultiple(float multiple)
{
  robot.SetSpeedMultiple(multiple);
}

void RobotAction::SetActionGroup(int group)
{
  switch (group)
  {
  case 2:
    crawlSteps = 4;
    break;
  case 3:
    crawlSteps = 6;
    break;
  default:
    crawlSteps = 2;
  }
}

void RobotAction::ActiveMode()
{
  ActionState();
  if (legsState != LegsState::CrawlState)
    InitialState();
  if (mode == Mode::Active)
    return;

  LegsMoveToRelatively(Point(0, 0, -bodyLift), bodyLiftSpeed);

  legsState = LegsState::CrawlState;
  mode = Mode::Active;
}

void RobotAction::SleepMode()
{
  ActionState();
  if (legsState != LegsState::CrawlState)
    InitialState();
  if (mode == Mode::Sleep)
    return;

  LegsMoveToRelatively(Point(0, 0, bodyLift), bodyLiftSpeed);

  legsState = LegsState::CrawlState;
  mode = Mode::Sleep;
}

void RobotAction::SwitchMode()
{
  ActionState();
  if (mode == Mode::Active)
    SleepMode();
  else
    ActiveMode();
}

void RobotAction::CrawlForward()
{
  Crawl(0, crawlLength, 0);
}

void RobotAction::CrawlBackward()
{
  Crawl(0, -crawlLength, 0);
}

void RobotAction::CrawlLeft()
{
  Crawl(crawlLength, 0, 0);
}

void RobotAction::CrawlRight()
{
  Crawl(-crawlLength, 0, 0);
}

void RobotAction::TurnLeft()
{
  Crawl(0, 0, -turnAngle);
}

void RobotAction::TurnRight()
{
  Crawl(0, 0, turnAngle);
}

void RobotAction::MoveBody(float x, float y, float z)
{
  TwistBody(Point(x, y, z), Point(0, 0, 0));
}

void RobotAction::RotateBody(float x, float y, float z)
{
  TwistBody(Point(0, 0, 0), Point(x, y, z));
}

void RobotAction::TwistBody(Point move, Point rotate)
{
  float angle = sqrt(pow(rotate.x, 2) + pow(rotate.y, 2) + pow(rotate.z, 2));
  TwistBody(move, rotate, angle);
}

void RobotAction::InitialState()
{
  ActionState();
  if (legsState == LegsState::CrawlState)
  {
    ActiveMode();
  }
  else if (legsState == LegsState::TwistBodyState)
  {
    TwistBody(Point(0, 0, bodyLift - defaultBodyLift), Point(0, 0, 0), 0);
  }
  else if (legsState == LegsState::LegMoveState)
  {
    RobotLegsPoints points;
    robot.GetPointsNow(points);

    points.leg1.z = -bodyLift;
    points.leg2.z = -bodyLift;
    points.leg3.z = -bodyLift;
    points.leg4.z = -bodyLift;
    points.leg5.z = -bodyLift;
    points.leg6.z = -bodyLift;

    LegsMoveTo(points, bodyLiftSpeed);
  }
  robot.GetPointsNow(lastChangeLegsStatePoints);
  mode = Mode::Active;
  legsState = LegsState::CrawlState;
}

void RobotAction::LegMoveToRelatively(int leg, Point point)
{
  ActionState();
  if (legsState != LegsState::LegMoveState)
    InitialState();

  LegMoveToRelativelyDirectly(leg, point);
  robot.WaitUntilFree();

  legsState = LegsState::LegMoveState;
}

void RobotAction::LegMoveToRelativelyDirectly(int leg, Point point)
{
  RobotLegsPoints points;
  robot.GetPointsNow(points);

  switch (leg)
  {
  case 1:
    points.leg1.x += point.x;
    points.leg1.y += point.y;
    points.leg1.z += point.z;
    break;
  case 2:
    points.leg2.x += point.x;
    points.leg2.y += point.y;
    points.leg2.z += point.z;
    break;
  case 3:
    points.leg3.x += point.x;
    points.leg3.y += point.y;
    points.leg3.z += point.z;
    break;
  case 4:
    points.leg4.x += point.x;
    points.leg4.y += point.y;
    points.leg4.z += point.z;
    break;
  case 5:
    points.leg5.x += point.x;
    points.leg5.y += point.y;
    points.leg5.z += point.z;
    break;
  case 6:
    points.leg6.x += point.x;
    points.leg6.y += point.y;
    points.leg6.z += point.z;
    break;
  }

  if (!robot.CheckPoints(points))
    return;

  robot.SetSpeed(legLiftSpeed);
  robot.MoveTo(points);
}

void RobotAction::ActionState()
{
  if (robot.state != Robot::State::Action)
  {
    robot.BootState();
    robot.state = Robot::State::Action;
    mode = Mode::Sleep;
    legsState = LegsState::CrawlState;
    lastChangeLegsStatePoints = initialPoints;
  }
}

void RobotAction::Crawl(float x, float y, float angle)
{
  ActionState();
  if (legsState != LegsState::CrawlState)
    InitialState();
  if (mode != Mode::Active)
    ActiveMode();

  float length = sqrt(pow(x, 2) + pow(y, 2));
  if (length > crawlLength)
  {
    x = x * crawlLength / length;
    y = y * crawlLength / length;
  }
  angle = constrain(angle, -turnAngle, turnAngle);

  x /= crawlSteps;
  y /= crawlSteps;
  angle /= crawlSteps;

  RobotLegsPoints points1;
  robot.GetPointsNow(points1);

  RobotLegsPoints points2 = points1;
  GetCrawlPoints(points2, Point(-x / 2, -y / 2, 0));
  GetTurnPoints(points2, -angle / 2);

  RobotLegsPoints points3 = points1;
  GetCrawlPoints(points3, Point(-x, -y, 0));
  GetTurnPoints(points3, -angle);

  RobotLegsPoints points4 = robot.bootPoints;
  GetCrawlPoints(points4, Point(x  * (crawlSteps - 1) / 2 / 2, y  * (crawlSteps - 1) / 2 / 2, -bodyLift + legLift));
  GetTurnPoints(points4, angle  * (crawlSteps - 1) / 2 / 2);

  RobotLegsPoints points5 = robot.bootPoints;
  GetCrawlPoints(points5, Point(x * (crawlSteps - 1) / 2, y  * (crawlSteps - 1) / 2, -bodyLift));
  GetTurnPoints(points5, angle  * (crawlSteps - 1) / 2);

  legMoveIndex < crawlSteps ? legMoveIndex++ : legMoveIndex = 1;

  switch (crawlSteps)
  {
  case 2:
    switch (legMoveIndex)
    {
    case 1:
      points2.leg1 = points4.leg1;
      points3.leg1 = points5.leg1;
      points2.leg3 = points4.leg3;
      points3.leg3 = points5.leg3;
      points2.leg5 = points4.leg5;
      points3.leg5 = points5.leg5;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg1.z = points1.leg1.z;
          points3.leg3.z = points1.leg3.z;
          points3.leg5.z = points1.leg5.z;
        }
        LegsMoveTo(points2, 1, legLiftSpeed);
        LegsMoveTo(points3, 1, legLiftSpeed);
      }
      break;
    case 2:
      points2.leg2 = points4.leg2;
      points3.leg2 = points5.leg2;
      points2.leg4 = points4.leg4;
      points3.leg4 = points5.leg4;
      points2.leg6 = points4.leg6;
      points3.leg6 = points5.leg6;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg2.z = points1.leg2.z;
          points3.leg4.z = points1.leg4.z;
          points3.leg6.z = points1.leg6.z;
        }
        LegsMoveTo(points2, 2, legLiftSpeed);
        LegsMoveTo(points3, 2, legLiftSpeed);
      }
      break;
    }
    break;
  case 4:
    switch (legMoveIndex)
    {
    case 1:
      points2.leg1 = points4.leg1;
      points3.leg1 = points5.leg1;
      points2.leg6 = points4.leg6;
      points3.leg6 = points5.leg6;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg1.z = points1.leg1.z;
          points3.leg6.z = points1.leg6.z;
        }
        LegsMoveTo(points2, 1, legLiftSpeed);
        LegsMoveTo(points3, 1, legLiftSpeed);
      }
      break;
    case 2:
      points2.leg5 = points4.leg5;
      points3.leg5 = points5.leg5;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg5.z = points1.leg5.z;
        }
        LegsMoveTo(points2, 5, legLiftSpeed);
        LegsMoveTo(points3, 5, legLiftSpeed);
      }
      break;
    case 3:
      points2.leg3 = points4.leg3;
      points3.leg3 = points5.leg3;
      points2.leg4 = points4.leg4;
      points3.leg4 = points5.leg4;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg3.z = points1.leg3.z;
          points3.leg4.z = points1.leg4.z;
        }
        LegsMoveTo(points2, 3, legLiftSpeed);
        LegsMoveTo(points3, 3, legLiftSpeed);
      }
      break;
    case 4:
      points2.leg2 = points4.leg2;
      points3.leg2 = points5.leg2;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg2.z = points1.leg2.z;
        }
        LegsMoveTo(points2, 2, legLiftSpeed);
        LegsMoveTo(points3, 2, legLiftSpeed);
      }
      break;
    }
    break;
  case 6:
    switch (legMoveIndex)
    {
    case 1:
      points2.leg1 = points4.leg1;
      points3.leg1 = points5.leg1;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg1.z = points1.leg1.z;
        }
        LegsMoveTo(points2, 1, legLiftSpeed);
        LegsMoveTo(points3, 1, legLiftSpeed);
      }
      break;
    case 2:
      points2.leg5 = points4.leg5;
      points3.leg5 = points5.leg5;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg5.z = points1.leg5.z;
        }
        LegsMoveTo(points2, 5, legLiftSpeed);
        LegsMoveTo(points3, 5, legLiftSpeed);
      }
      break;
    case 3:
      points2.leg3 = points4.leg3;
      points3.leg3 = points5.leg3;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg3.z = points1.leg3.z;
        }
        LegsMoveTo(points2, 3, legLiftSpeed);
        LegsMoveTo(points3, 3, legLiftSpeed);
      }
      break;
    case 4:
      points2.leg4 = points4.leg4;
      points3.leg4 = points5.leg4;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg4.z = points1.leg4.z;
        }
        LegsMoveTo(points2, 4, legLiftSpeed);
        LegsMoveTo(points3, 4, legLiftSpeed);
      }
      break;
    case 5:
      points2.leg2 = points4.leg2;
      points3.leg2 = points5.leg2;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg2.z = points1.leg2.z;
        }
        LegsMoveTo(points2, 2, legLiftSpeed);
        LegsMoveTo(points3, 2, legLiftSpeed);
      }
      break;
    case 6:
      points2.leg6 = points4.leg6;
      points3.leg6 = points5.leg6;
      if (CheckCrawlPoints(points2))
      {
        if (!CheckCrawlPoints(points3))
        {
          points3 = points2;
          points3.leg6.z = points1.leg6.z;
        }
        LegsMoveTo(points2, 6, legLiftSpeed);
        LegsMoveTo(points3, 6, legLiftSpeed);
      }
      break;
    }
    break;
  }

  legsState = LegsState::CrawlState;
}

void RobotAction::ChangeBodyHeight(float height)
{
  ActionState();
  if (legsState != LegsState::CrawlState)
    InitialState();
  if (mode != Mode::Active)
    ActiveMode();

  height = constrain(height, 0, 45);
  bodyLift = defaultBodyLift + height;

  RobotLegsPoints points;
  robot.GetPointsNow(points);

  points.leg1.z = -bodyLift;
  points.leg2.z = -bodyLift;
  points.leg3.z = -bodyLift;
  points.leg4.z = -bodyLift;
  points.leg5.z = -bodyLift;
  points.leg6.z = -bodyLift;

  LegsMoveTo(points, bodyLiftSpeed);

  legsState = LegsState::CrawlState;
}

bool RobotAction::CheckCrawlPoints(RobotLegsPoints points)
{
  float alpha1, alpha2, alpha3, alpha4, alpha5, alpha6;
  float beta, gamma;

  robot.leg1.CalculateAngle(points.leg1, alpha1, beta, gamma);
  robot.leg2.CalculateAngle(points.leg2, alpha2, beta, gamma);
  robot.leg3.CalculateAngle(points.leg3, alpha3, beta, gamma);
  robot.leg4.CalculateAngle(points.leg4, alpha4, beta, gamma);
  robot.leg5.CalculateAngle(points.leg5, alpha5, beta, gamma);
  robot.leg6.CalculateAngle(points.leg6, alpha6, beta, gamma);

  if (alpha1 < 0) alpha1 += 360;
  if (alpha2 < 0) alpha2 += 360;
  if (alpha3 < 0) alpha3 += 360;
  if (alpha4 < -180) alpha4 += 360; else if (alpha4 > 180) alpha4 -= 360;
  if (alpha5 < -180) alpha4 += 360; else if (alpha5 > 180) alpha4 -= 360;
  if (alpha6 < -180) alpha4 += 360; else if (alpha6 > 180) alpha4 -= 360;

  if (alpha1 < 90 || alpha1 > 180 ||
    alpha3 < 180 || alpha3 > 270 ||
    alpha4 < 0 || alpha4 > 90 ||
    alpha6 < -90 || alpha6 > 0 ||
    alpha2 - alpha1 < minAlphaInterval ||
    alpha3 - alpha2 < minAlphaInterval ||
    alpha4 - alpha5 < minAlphaInterval ||
    alpha5 - alpha6 < minAlphaInterval)
    return false;

  return true;
}

void RobotAction::GetCrawlPoints(RobotLegsPoints & points, Point point)
{
  GetCrawlPoint(points.leg1, point);
  GetCrawlPoint(points.leg2, point);
  GetCrawlPoint(points.leg3, point);
  GetCrawlPoint(points.leg4, point);
  GetCrawlPoint(points.leg5, point);
  GetCrawlPoint(points.leg6, point);
}

void RobotAction::GetCrawlPoint(Point & point, Point direction)
{
  point = Point(point.x + direction.x, point.y + direction.y, point.z + direction.z);
}

void RobotAction::GetTurnPoints(RobotLegsPoints & points, float angle)
{
  GetTurnPoint(points.leg1, angle);
  GetTurnPoint(points.leg2, angle);
  GetTurnPoint(points.leg3, angle);
  GetTurnPoint(points.leg4, angle);
  GetTurnPoint(points.leg5, angle);
  GetTurnPoint(points.leg6, angle);
}

void RobotAction::GetTurnPoint(Point & point, float angle)
{
  float radian = angle * PI / 180;
  float radius = sqrt(pow(point.x, 2) + pow(point.y, 2));

  float x = radius * cos(atan2(point.y, point.x) + radian);
  float y = radius * sin(atan2(point.y, point.x) + radian);

  point = Point(x, y, point.z);
}

void RobotAction::TwistBody(Point move, Point rotateAxis, float rotateAngle)
{
  ActionState();
  if (legsState != LegsState::TwistBodyState)
    InitialState();

  RobotLegsPoints points = lastChangeLegsStatePoints;
  points.leg1.z = -defaultBodyLift;
  points.leg2.z = -defaultBodyLift;
  points.leg3.z = -defaultBodyLift;
  points.leg4.z = -defaultBodyLift;
  points.leg5.z = -defaultBodyLift;
  points.leg6.z = -defaultBodyLift;

  // move body
  move.x = constrain(move.x, -30, 30);
  move.y = constrain(move.y, -30, 30);
  move.z = constrain(move.z, 0, 45);
  GetMoveBodyPoints(points, move);

  // rotate body
  rotateAngle = constrain(rotateAngle, -15, 15);
  GetRotateBodyPoints(points, rotateAxis, rotateAngle);

  LegsMoveTo(points, speedTwistBody);

  legsState = LegsState::TwistBodyState;
}

void RobotAction::GetMoveBodyPoints(RobotLegsPoints & points, Point point)
{
  GetMoveBodyPoint(points.leg1, point);
  GetMoveBodyPoint(points.leg2, point);
  GetMoveBodyPoint(points.leg3, point);
  GetMoveBodyPoint(points.leg4, point);
  GetMoveBodyPoint(points.leg5, point);
  GetMoveBodyPoint(points.leg6, point);
}

void RobotAction::GetMoveBodyPoint(Point & point, Point direction)
{
  point = Point(point.x - direction.x, point.y - direction.y, point.z - direction.z);
}

void RobotAction::GetRotateBodyPoints(RobotLegsPoints &points, Point rotateAxis, float rotateAngle)
{
  float rotateAxisLength = sqrt(pow(rotateAxis.x, 2) + pow(rotateAxis.y, 2) + pow(rotateAxis.z, 2));
  if (rotateAxisLength == 0)
  {
    rotateAxis.x = 0;
    rotateAxis.y = 0;
    rotateAxis.z = 1;
  }
  else
  {
    rotateAxis.x /= rotateAxisLength;
    rotateAxis.y /= rotateAxisLength;
    rotateAxis.z /= rotateAxisLength;
  }

  GetRotateBodyPoint(points.leg1, rotateAxis, rotateAngle);
  GetRotateBodyPoint(points.leg2, rotateAxis, rotateAngle);
  GetRotateBodyPoint(points.leg3, rotateAxis, rotateAngle);
  GetRotateBodyPoint(points.leg4, rotateAxis, rotateAngle);
  GetRotateBodyPoint(points.leg5, rotateAxis, rotateAngle);
  GetRotateBodyPoint(points.leg6, rotateAxis, rotateAngle);
}

void RobotAction::GetRotateBodyPoint(Point & point, Point rotateAxis, float rotateAngle)
{
  Point oldPoint = point;

  rotateAngle = rotateAngle * PI / 180;
  float c = cos(rotateAngle);
  float s = sin(rotateAngle);

  point.x = (rotateAxis.x * rotateAxis.x * (1 - c) + c) * oldPoint.x + (rotateAxis.x * rotateAxis.y * (1 - c) - rotateAxis.z * s) * oldPoint.y + (rotateAxis.x * rotateAxis.z * (1 - c) + rotateAxis.y * s) * oldPoint.z;
  point.y = (rotateAxis.y * rotateAxis.x * (1 - c) + rotateAxis.z * s) * oldPoint.x + (rotateAxis.y * rotateAxis.y * (1 - c) + c) * oldPoint.y + (rotateAxis.y * rotateAxis.z * (1 - c) - rotateAxis.x * s) * oldPoint.z;
  point.z = (rotateAxis.x * rotateAxis.z * (1 - c) - rotateAxis.y * s) * oldPoint.x + (rotateAxis.y * rotateAxis.z * (1 - c) + rotateAxis.x * s) * oldPoint.y + (rotateAxis.z * rotateAxis.z * (1 - c) + c) * oldPoint.z;
}

void RobotAction::LegsMoveTo(RobotLegsPoints points)
{
  if (!robot.CheckPoints(points))
    return;

  robot.MoveTo(points);
  robot.WaitUntilFree();
}

void RobotAction::LegsMoveTo(RobotLegsPoints points, float speed)
{
  if (!robot.CheckPoints(points))
    return;

  robot.SetSpeed(speed);
  robot.MoveTo(points);
  robot.WaitUntilFree();
}

void RobotAction::LegsMoveTo(RobotLegsPoints points, int leg, float legSpeed)
{
  if (!robot.CheckPoints(points))
    return;

  float distance[6] = {
    Point::GetDistance(robot.leg1.pointNow, points.leg1),
    Point::GetDistance(robot.leg2.pointNow, points.leg2),
    Point::GetDistance(robot.leg3.pointNow, points.leg3),
    Point::GetDistance(robot.leg4.pointNow, points.leg4),
    Point::GetDistance(robot.leg5.pointNow, points.leg5),
    Point::GetDistance(robot.leg6.pointNow, points.leg6) };

  float speed[6] = {
    distance[0] / distance[leg - 1] * legSpeed,
    distance[1] / distance[leg - 1] * legSpeed,
    distance[2] / distance[leg - 1] * legSpeed,
    distance[3] / distance[leg - 1] * legSpeed,
    distance[4] / distance[leg - 1] * legSpeed,
    distance[5] / distance[leg - 1] * legSpeed };

  robot.SetSpeed(speed[0], speed[1], speed[2], speed[3], speed[4], speed[5]);
  robot.MoveTo(points);
  robot.WaitUntilFree();
}

void RobotAction::LegsMoveToRelatively(Point point, float speed)
{
  RobotLegsPoints points;

  robot.GetPointsNow(points);
  GetCrawlPoints(points, point);

  LegsMoveTo(points, speed);
}

#endif
