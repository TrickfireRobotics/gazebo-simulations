#!/usr/bin/env bash
# Build the gz_ros2_control workspace on macOS.
# Args: MAMBA_EXE ENV_PREFIX ROS_BASE ROS_GZ_WS CONTROL_WS
set -euo pipefail

MAMBA_EXE="$1"
ENV_PREFIX="$2"
ROS_BASE="$3"
ROS_GZ_WS="$4"
CONTROL_WS="$5"

set +u
eval "$($MAMBA_EXE shell hook --shell bash)"
micromamba activate "$ENV_PREFIX"

source "$ROS_BASE/setup.bash"
source "$ROS_GZ_WS/install/setup.bash"
set +u
export PATH="$ENV_PREFIX/bin:$PATH"
export GZ_VERSION=harmonic
export CMAKE_PREFIX_PATH="$ENV_PREFIX:$ROS_BASE:$ROS_GZ_WS/install"

_patch_cmake() {
	local search="$1" replace="$2" dir="$3"
	while IFS= read -r f; do
		sed -i.bak "s/${search}/${replace}/g" "$f" && rm -f "$f.bak"
	done < <(grep -rln "$search" "$dir" 2>/dev/null || true)
}

for _dir in "$ENV_PREFIX/lib/cmake" "$ENV_PREFIX/share/cmake"; do
	[ -d "$_dir" ] || continue
	_patch_cmake "TINYXML2::TINYXML2" "tinyxml2::tinyxml2" "$_dir"
	_patch_cmake "find_package(TINYXML2" "find_package(tinyxml2 CONFIG" "$_dir"
	_patch_cmake "CPPZMQ::CPPZMQ" "cppzmq" "$_dir"
	_patch_cmake "find_package(CPPZMQ" "find_package(cppzmq CONFIG" "$_dir"
done

PY_EXE="$ROS_BASE/bin/python3"
PY_VER=$("$PY_EXE" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_INC="$ROS_BASE/include/python${PY_VER}"
PY_LIB="$ROS_BASE/lib/libpython${PY_VER}.dylib"
NP_INC=$("$PY_EXE" -c "import numpy; print(numpy.get_include())")

LINKER_FLAGS="-Wl,-headerpad_max_install_names \
-Wl,-rpath,$ENV_PREFIX/lib -Wl,-rpath,$ROS_BASE/lib \
-L$ENV_PREFIX/lib -L$ROS_BASE/lib -lpython${PY_VER} -Wl,-undefined,dynamic_lookup"

find "$CONTROL_WS/build" -maxdepth 2 -name "CMakeCache.txt" -delete 2>/dev/null || true

cd "$CONTROL_WS"
colcon build --symlink-install --cmake-args \
	-DCMAKE_BUILD_TYPE=Release \
	"-DCMAKE_SHARED_LINKER_FLAGS=$LINKER_FLAGS" \
	"-DCMAKE_MODULE_LINKER_FLAGS=$LINKER_FLAGS" \
	"-DCMAKE_PREFIX_PATH=$ENV_PREFIX;$ROS_BASE;$ROS_GZ_WS/install" \
	"-DPython_EXECUTABLE=$PY_EXE" "-DPython3_EXECUTABLE=$PY_EXE" \
	"-DPython_ROOT_DIR=$ROS_BASE" "-DPython3_ROOT_DIR=$ROS_BASE" \
	"-DPython_INCLUDE_DIR=$PY_INC" "-DPython3_INCLUDE_DIR=$PY_INC" \
	"-DPython_LIBRARY=$PY_LIB" "-DPython3_LIBRARY=$PY_LIB" \
	"-DPython_NumPy_INCLUDE_DIR=$NP_INC" "-DPython3_NumPy_INCLUDE_DIR=$NP_INC" \
	"-DCMAKE_IGNORE_PATH=/opt/homebrew;/opt/homebrew/include;/opt/homebrew/lib;/opt/homebrew/opt" \
	"-DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew"
