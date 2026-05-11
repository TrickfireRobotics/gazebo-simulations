#!/usr/bin/env bash
# Build the gz_ros2_control workspace on Linux using the self-contained conda env.
# Args: MAMBA_EXE ENV_PREFIX CONTROL_WS
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
CONTROL_WS="$3"

set +u
eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

source "$ENV_PREFIX/setup.bash"
set +u

export PATH="$ENV_PREFIX/bin:$PATH"
export GZ_VERSION=harmonic
export CMAKE_PREFIX_PATH="$ENV_PREFIX${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export LIBRARY_PATH="$ENV_PREFIX/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$ENV_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

LINKER_FLAGS="-Wl,-rpath,$ENV_PREFIX/lib -L$ENV_PREFIX/lib"

cd "$CONTROL_WS"
colcon build --symlink-install --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  "-DCMAKE_SHARED_LINKER_FLAGS=$LINKER_FLAGS" \
  "-DCMAKE_MODULE_LINKER_FLAGS=$LINKER_FLAGS" \
  "-DCMAKE_EXE_LINKER_FLAGS=$LINKER_FLAGS"
