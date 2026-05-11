#!/usr/bin/env bash
# Build the ros_gz workspace on macOS.
# Args: MAMBA_EXE ENV_PREFIX ROS_BASE ROS_GZ_WS
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
ROS_BASE="$3"
ROS_GZ_WS="$4"

eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

set +u
source "$ROS_BASE/setup.bash"
set +u
export PATH="$ENV_PREFIX/bin:$PATH"
export GZ_VERSION=harmonic
export CMAKE_PREFIX_PATH="$ENV_PREFIX:$ROS_BASE"

LINKER_FLAGS="-Wl,-headerpad_max_install_names -Wl,-rpath,$ENV_PREFIX/lib -Wl,-rpath,$ROS_BASE/lib -L$ENV_PREFIX/lib -L$ROS_BASE/lib -undefined dynamic_lookup"

cd "$ROS_GZ_WS"
colcon build --symlink-install --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  "-DCMAKE_SHARED_LINKER_FLAGS=$LINKER_FLAGS" \
  "-DCMAKE_MODULE_LINKER_FLAGS=$LINKER_FLAGS"
