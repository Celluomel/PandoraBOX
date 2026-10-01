#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-}"
if [[ -z "$ROS_DISTRO" ]]; then
  echo "Set ROS_DISTRO to an installed ROS 2 distribution (for example jazzy)."
  echo "Configure the official ROS 2 apt repository first: https://docs.ros.org/"
  exit 2
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO}/setup.bash"
if [[ -f "$ROS_SETUP" ]]; then
  echo "ROS 2 ${ROS_DISTRO} is already installed at ${ROS_SETUP}."
  exit 0
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer supports Debian/Ubuntu apt-based ROS 2 installations only."
  exit 2
fi

echo "Installing ROS 2 ${ROS_DISTRO} runtime and Body bridge message packages..."
sudo apt-get update
sudo apt-get install -y "ros-${ROS_DISTRO}-ros-base" "ros-${ROS_DISTRO}-std-msgs"
if [[ ! -f "$ROS_SETUP" ]]; then
  echo "Installation finished, but ${ROS_SETUP} was not found."
  exit 1
fi
echo "Installed. Start the Body with ROS_DISTRO=${ROS_DISTRO} to source the ROS environment."
