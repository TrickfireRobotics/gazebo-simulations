#!/usr/bin/env bash
# Launch the simulation on Linux using the self-contained conda env.
# Args: MAMBA_EXE ENV_PREFIX CONTROL_WS WORKSPACE_DIR ROBOT
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
CONTROL_WS="$3"
WORKSPACE_DIR="$4"
ROBOT="$5"

eval "$($MAMBA_EXE shell hook --shell bash)"

set +u
micromamba activate "$ENV_PREFIX"

source "$ENV_PREFIX/setup.bash"
source "$CONTROL_WS/install/setup.bash"
source "$WORKSPACE_DIR/install/setup.bash"
set -u

export GZ_SIM_RESOURCE_PATH="$WORKSPACE_DIR/install/sim_worlds/share:$WORKSPACE_DIR/install/${ROBOT}_description/share"

mkdir -p "$WORKSPACE_DIR/log"
cd "$WORKSPACE_DIR"
ros2 launch "${ROBOT}_bringup" "${ROBOT}.launch.py"
