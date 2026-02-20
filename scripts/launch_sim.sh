#!/bin/bash
set -e

# --------------------------------------------------------------------------------------------
# Universal ROS2 Gazebo build + launch script
# Usage: ./launch_sim.sh <robot_name> [--build-only] [--no-build]
#
# Expects packages named:
#   <robot_name>_description  →  URDF, meshes
#   <robot_name>_bringup      →  launch files, configs
#   sim_worlds                →  shared world files and models
#
# Example: ./launch_sim.sh arm
# --------------------------------------------------------------------------------------------

ROBOT_NAME=""
BUILD=true
LAUNCH=true

for arg in "$@"; do
    case "$arg" in
        --build-only) LAUNCH=false ;;
        --no-build)   BUILD=false ;;
        --help)
            echo "Usage: $0 <robot_name> [--build-only] [--no-build]"
            exit 0
            ;;
        -*) echo "[Error] Unknown option: $arg"; exit 1 ;;
        *)  ROBOT_NAME="$arg" ;;
    esac
done

if [ -z "$ROBOT_NAME" ]; then
    echo "Usage: $0 <robot_name> [--build-only] [--no-build]"
    exit 1
fi

# --------------------------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="$PROJECT_DIR/robot-sim"

LOG_DIR="$WORKSPACE_DIR/log"
LOG_PATH="$LOG_DIR/${ROBOT_NAME}-$(date +'%Y-%m-%d_%H-%M').log"

cd "$WORKSPACE_DIR"

# --------------------------------------------------------------------------------------------
# VALIDATE — check expected packages exist before bothering to build
# --------------------------------------------------------------------------------------------

BRINGUP_PKG="${ROBOT_NAME}_bringup"
DESCRIPTION_PKG="${ROBOT_NAME}_description"

if [ ! -d "$BRINGUP_PKG" ]; then
    echo "[Error] Package '$BRINGUP_PKG' not found in $WORKSPACE_DIR"
    echo "        Expected directory: $WORKSPACE_DIR/$BRINGUP_PKG"
    exit 1
fi

if [ ! -d "$DESCRIPTION_PKG" ]; then
    echo "[Error] Package '$DESCRIPTION_PKG' not found in $WORKSPACE_DIR"
    echo "        Expected directory: $WORKSPACE_DIR/$DESCRIPTION_PKG"
    exit 1
fi

LAUNCH_FILE_SRC="$BRINGUP_PKG/launch/${ROBOT_NAME}.launch.py"
if [ ! -f "$LAUNCH_FILE_SRC" ]; then
    echo "[Error] Launch file not found: $LAUNCH_FILE_SRC"
    exit 1
fi

#

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_PATH") 2>&1

echo "--------------------------------------------------------------"
echo "Robot:     $ROBOT_NAME"
echo "Workspace: $WORKSPACE_DIR"
echo "Log:       $LOG_PATH"
echo "--------------------------------------------------------------"

# --------------------------------------------------------------------------------------------
# BUILD
# --------------------------------------------------------------------------------------------

if [ "$BUILD" = true ]; then
    echo ""
    echo "[INFO] Building ROS2 workspace..."

    colcon build \
        --packages-up-to "$BRINGUP_PKG" "$DESCRIPTION_PKG" sim_worlds \
        --cmake-args -DBUILD_TESTING=OFF

    if [ ! -f install/setup.bash ]; then
        echo "[Error] install/setup.bash not found — build may have failed"
        exit 1
    fi

    echo "[INFO] Build complete"
fi

# --------------------------------------------------------------------------------------------
# SOURCE
# --------------------------------------------------------------------------------------------

echo "[INFO] Sourcing ROS2 environment..."
# shellcheck disable=SC1091
source install/setup.bash

# --------------------------------------------------------------------------------------------
# REGISTER MODELS
# --------------------------------------------------------------------------------------------

SIM_WORLDS_SHARE="$WORKSPACE_DIR/install/sim_worlds/share/sim_worlds"

if [ -d "$SIM_WORLDS_SHARE/worlds" ]; then
    export GZ_SIM_RESOURCE_PATH="${GZ_SIM_RESOURCE_PATH:+$GZ_SIM_RESOURCE_PATH:}$SIM_WORLDS_SHARE"
    echo "[INFO] GZ_SIM_RESOURCE_PATH set to: $GZ_SIM_RESOURCE_PATH"
else
    echo "[Warn] sim_worlds share directory not found — world files may not load"
    echo "       Expected: $SIM_WORLDS_SHARE/worlds"
fi

# --------------------------------------------------------------------------------------------
# LAUNCH
# --------------------------------------------------------------------------------------------

if [ "$LAUNCH" = true ]; then
    echo ""
    echo "[INFO] Launching simulation for robot: $ROBOT_NAME"
    echo "------------------------------------------------------------"
    ros2 launch "$BRINGUP_PKG" "${ROBOT_NAME}.launch.py"
fi
