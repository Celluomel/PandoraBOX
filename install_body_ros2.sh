#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1 || [[ ! -f /etc/os-release ]]; then
  echo "This installer supports Debian/Ubuntu apt-based ROS 2 installations only."
  exit 2
fi

source /etc/os-release
UBUNTU_CODENAME="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
ROS_DISTRO="${ROS_DISTRO:-}"
if [[ -z "$ROS_DISTRO" ]]; then
  case "$UBUNTU_CODENAME" in
    noble) ROS_DISTRO=jazzy ;;
    jammy) ROS_DISTRO=humble ;;
    *) echo "Set ROS_DISTRO explicitly; no default is defined for ${UBUNTU_CODENAME:-this OS}."; exit 2 ;;
  esac
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO}/setup.bash"
ROS_PACKAGES=(
  "ros-${ROS_DISTRO}-ros-base"
  "ros-${ROS_DISTRO}-std-msgs"
  "ros-${ROS_DISTRO}-geometry-msgs"
  "ros-${ROS_DISTRO}-sensor-msgs"
  "ros-${ROS_DISTRO}-nav-msgs"
  "ros-${ROS_DISTRO}-action-msgs"
  "ros-${ROS_DISTRO}-diagnostic-msgs"
  "ros-${ROS_DISTRO}-tf2-msgs"
  "ros-${ROS_DISTRO}-tf2-ros"
  "ros-${ROS_DISTRO}-navigation2"
  "ros-${ROS_DISTRO}-nav2-bringup"
  "ros-${ROS_DISTRO}-joy"
  "ros-${ROS_DISTRO}-teleop-twist-keyboard"
  "ros-${ROS_DISTRO}-teleop-twist-joy"
)
missing=()
for package in "${ROS_PACKAGES[@]}"; do
  if ! dpkg-query -W -f='${db:Status-Status}' "$package" 2>/dev/null | grep -qx installed; then
    missing+=("$package")
  fi
done
if [[ ${#missing[@]} -eq 0 ]]; then
  echo "ROS 2 ${ROS_DISTRO}, Body bridge messages, and Nav2 are already installed."
  exit 0
fi

if [[ "${ID:-}" != ubuntu ]]; then
  echo "Automatic ROS 2 repository setup currently supports Ubuntu only (detected ${ID:-unknown})."
  exit 2
fi

echo "Installing ROS 2 ${ROS_DISTRO}, Body bridge messages, and Nav2 packages..."
sudo apt-get update
sudo apt-get install -y curl ca-certificates software-properties-common
sudo add-apt-repository universe -y
sudo apt-get update

# Use ROS's maintained apt-source package rather than embedding repository keys.
ROS_APT_SOURCE_VERSION="$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')"
ROS_APT_SOURCE_DEB="/tmp/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${UBUNTU_CODENAME}_all.deb"
curl -fL --retry 3 -o "$ROS_APT_SOURCE_DEB" \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${UBUNTU_CODENAME}_all.deb"
sudo dpkg -i "$ROS_APT_SOURCE_DEB"
sudo apt-get update
sudo apt-get install -y "${missing[@]}"

if [[ ! -f "$ROS_SETUP" ]]; then
  echo "Installation finished, but ${ROS_SETUP} was not found."
  exit 1
fi
echo "Installed ROS 2 ${ROS_DISTRO} with Nav2. Start the Body to source ${ROS_SETUP}."
