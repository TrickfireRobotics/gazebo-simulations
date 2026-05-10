#!/usr/bin/env bash
# Build the robot-sim workspace on macOS.
# Args: MAMBA_EXE ENV_PREFIX ROS_BASE ROS_GZ_WS CONTROL_WS WORKSPACE_DIR
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
ROS_BASE="$3"
ROS_GZ_WS="$4"
CONTROL_WS="$5"
WORKSPACE_DIR="$6"

#this looks weird but leaving some environment variables unset is ok
#they set themselves later in the sourcing
set +u

eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

# ROS setup.bash files reference unset path vars; seed them so `set -u` doesn't trip.
source "$ROS_BASE/setup.bash"
source "$ROS_GZ_WS/install/setup.bash"
source "$CONTROL_WS/install/setup.bash"
set +u

LINKER_FLAGS="-Wl,-headerpad_max_install_names -Wl,-rpath,$ENV_PREFIX/lib -Wl,-rpath,$ROS_BASE/lib -Wl,-rpath,$ROS_GZ_WS/install/lib -Wl,-rpath,$CONTROL_WS/install/lib -L$ENV_PREFIX/lib -L$ROS_BASE/lib -undefined dynamic_lookup"

cd "$WORKSPACE_DIR"
colcon build --cmake-args \
  -DBUILD_TESTING=OFF \
  "-DCMAKE_SHARED_LINKER_FLAGS=$LINKER_FLAGS" \
  "-DCMAKE_MODULE_LINKER_FLAGS=$LINKER_FLAGS"
