#!/bin/bash
set -e

# --------------------------------------------------------------------------------------------
# Universal ROS2 Gazebo build + launch script
# Usage: ./build_ros2_sim.sh <robot_name>
# --------------------------------------------------------------------------------------------

ROBOT_NAME="$1"

if [ -z "$ROBOT_NAME" ]; then
    echo "Usage: $0 <robot_name>"
    exit 1
fi

# Find project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Workspace path
ROBOT_SIM_DIR="$PROJECT_DIR/robot-sim"

# Log file path
LOG_DIR="$ROBOT_SIM_DIR/log"
LOG_PATH="$LOG_DIR/${ROBOT_NAME}_log-$(date +'%Y-%m-%d_%H-%M').log"

mkdir -p "$LOG_DIR"

# Redirect all output to terminal + log file
exec > >(tee -a "$LOG_PATH") 2>&1

cd "$ROBOT_SIM_DIR"

# --------------------------------------------------------------------------------------------
# BUILD
# --------------------------------------------------------------------------------------------

echo "Building ROS 2 workspace..."
colcon build --cmake-args -DBUILD_TESTING=ON

if [ ! -f install/setup.bash ]; then
    echo "[Error] Install/setup.bash not found! Build may have failed"
    exit 1
fi

chmod a+x install/setup.bash

echo "[INFO] Sourcing ROS 2 environment..."
source install/setup.bash

# --------------------------------------------------------------------------------------------
# REGISTER MODELS
# --------------------------------------------------------------------------------------------

MODEL_PATH="$ROBOT_SIM_DIR/install/models_and_worlds/share/models_and_worlds/models"

export IGN_GAZEBO_RESOURCE_PATH="${IGN_GAZEBO_RESOURCE_PATH:+$IGN_GAZEBO_RESOURCE_PATH:}$MODEL_PATH"

echo "IGN_GAZEBO_RESOURCE_PATH:"
echo "  $IGN_GAZEBO_RESOURCE_PATH"

# --------------------------------------------------------------------------------------------
# LAUNCH
# --------------------------------------------------------------------------------------------

LAUNCH_FILE="$ROBOT_SIM_DIR/launch_files/launch/${ROBOT_NAME}.launch.py"

if [ ! -f "$LAUNCH_FILE" ]; then
    echo "[Error] Launch file for robot '$ROBOT_NAME' not found"
    exit 1
fi

echo "Launching simulation for robot: $ROBOT_NAME"
ros2 launch launch_files "${ROBOT_NAME}.launch.py"
