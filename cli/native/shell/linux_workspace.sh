#!/usr/bin/env bash
# Build the robot-sim workspace on Linux using the self-contained conda env.
# Args: MAMBA_EXE ENV_PREFIX WORKSPACE_DIR
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
WORKSPACE_DIR="$3"

eval "$($MAMBA_EXE shell hook --shell bash)"

set +u
micromamba activate "$ENV_PREFIX"
source "$ENV_PREFIX/setup.bash"
set -u

cd "$WORKSPACE_DIR"
colcon build --cmake-args -DBUILD_TESTING=OFF
