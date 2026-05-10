#!/usr/bin/env bash
# Build the gz_ros2_control workspace on Linux using the self-contained conda env.
# Args: MAMBA_EXE ENV_PREFIX CONTROL_WS
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
CONTROL_WS="$3"

eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

set +u
source "$ENV_PREFIX/setup.bash"
set -u

export PATH="$ENV_PREFIX/bin:$PATH"
export GZ_VERSION=harmonic
export CMAKE_PREFIX_PATH="$ENV_PREFIX${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"

cd "$CONTROL_WS"
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
