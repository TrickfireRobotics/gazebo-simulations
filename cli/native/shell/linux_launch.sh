#!/usr/bin/env bash
# Launch the simulation on Linux using the self-contained conda env.
# Args: MAMBA_EXE ENV_PREFIX WORKSPACE_DIR ROBOT
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
WORKSPACE_DIR="$3"
ROBOT="$4"

eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

source "$ENV_PREFIX/setup.bash"
source "$WORKSPACE_DIR/install/setup.bash"

export GZ_SIM_RESOURCE_PATH="$WORKSPACE_DIR/install/sim_worlds/share:$WORKSPACE_DIR/install/${ROBOT}_description/share"

mkdir -p "$WORKSPACE_DIR/log"
cd "$WORKSPACE_DIR"
ros2 launch "${ROBOT}_bringup" "${ROBOT}.launch.py"
