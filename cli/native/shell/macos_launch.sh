#!/usr/bin/env bash
# Launch the simulation on macOS.
# Args: MAMBA_EXE ENV_PREFIX ROS_BASE ROS_GZ_WS CONTROL_WS WORKSPACE_DIR ROBOT
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
ROS_BASE="$3"
ROS_GZ_WS="$4"
CONTROL_WS="$5"
WORKSPACE_DIR="$6"
ROBOT="$7"

#Check macos_workspace.sh for explanation
set +u

eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

source "$ROS_BASE/setup.bash"
source "$ROS_GZ_WS/install/setup.bash"
source "$CONTROL_WS/install/setup.bash"
source "$WORKSPACE_DIR/install/setup.bash"
set -u

export GZ_SIM_RESOURCE_PATH="$WORKSPACE_DIR/install/sim_worlds/share:$WORKSPACE_DIR/install/${ROBOT}_description/share"
export GZ_SIM_SYSTEM_PLUGIN_PATH="$CONTROL_WS/install/gz_ros2_control/lib:$CONTROL_WS/install/ign_ros2_control/lib"

mkdir -p "$WORKSPACE_DIR/log"
cd "$WORKSPACE_DIR"
exec ros2 launch "${ROBOT}_bringup" "${ROBOT}.launch.py"
