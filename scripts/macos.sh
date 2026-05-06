#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# macos.sh - Build and launch the TrickFire robot simulation on macOS
# ------------------------------------------------------------------------------
# Automated build and deployment of the TrickFire robot simulation environment
# using Gazebo and ROS 2 for macOS native. Handles conda environment setup,
#  dependency management, workspace compilation, and simulation launch.
#
# Usage:
#   ./scripts/macos.sh [OPTIONS] <robot_name>
#
# Options:
#   --build       Build workspaces and exit (don't launch simulation)
#   --help, -h    Display this help message
# ------------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MACOS_DIR="$REPO_DIR/macos"
WORKSPACE_DIR="$REPO_DIR/robot-sim"

[ "$(uname)" = "Darwin" ] || {
	printf 'This script is macOS-only.\n' >&2
	exit 1
}

# shellcheck disable=SC1090,SC1091
[ -f "$MACOS_DIR/versions.env" ] && source "$MACOS_DIR/versions.env"

ENV_LOCK="$MACOS_DIR/env.lock.yml"
ENV_PREFIX="$MACOS_DIR/envs/ros_env"
MAMBA_ROOT_PREFIX="$MACOS_DIR/mamba"
ROS_BASE_PREFIX="$MACOS_DIR/ros_base"
ROS_GZ_WS="$MACOS_DIR/ros_gz_ws"
CONTROL_WS="$MACOS_DIR/gz_ros2_control_ws"

ROS_BASE_PKGS=(
	ros-humble-ros-base
	ros-humble-actuator-msgs
	ros-humble-gps-msgs
	ros-humble-vision-msgs
	ros-humble-image-transport
	ros-humble-ros2-control
	ros-humble-ros2-controllers
	ros-humble-joint-state-broadcaster
	ros-humble-joint-trajectory-controller
	ros-humble-control-msgs
	ros-humble-control-toolbox
	ros-humble-xacro
	ros-humble-rviz2
)

# Output helpers ---------------------------------------------------------------

if [ -t 1 ]; then
	_B=$'\033[1m' _G=$'\033[1;32m' _Y=$'\033[1;33m' _R=$'\033[1;31m' _P=$'\033[1;35m'
	_D=$'\033[2m' _X=$'\033[0m'
	_TTY=true
else
	_B='' _G='' _Y='' _R='' _P='' _D='' _X=''
	_TTY=false
fi

warn() { printf '%s[WARN]  %s%s\n' "$_Y" "$*" "$_X" >&2; }
die() {
	printf '\n%s[FATAL]  %s%s\n\n' "$_R" "$*" "$_X" >&2
	exit 1
}

run_step() {
	local label="$1"
	shift
	printf '%s[STEP] %s%s\n' "$_P" "$label" "$_X"
	if $_TTY; then
		printf '\0337'
		if "$@"; then
			printf '\0338\033[J'
		else
			local rc=$?
			printf '\n%s[FATAL]  %s - failed (exit %d)%s\n' "$_R" "$label" "$rc" "$_X" >&2
			exit "$rc"
		fi
	else
		"$@" || {
			local rc=$?
			printf '\n%s[FATAL]  %s - failed (exit %d)%s\n' "$_R" "$label" "$rc" "$_X" >&2
			exit "$rc"
		}
	fi
}

# Argument parsing -------------------------------------------------------------

BUILD_ONLY=false
ROBOT_NAME=""

for arg in "$@"; do
	case "$arg" in
	--build) BUILD_ONLY=true ;;
	--help | -h)
		printf 'Usage: %s [--build] <robot_name>\n' "$(basename "$0")"
		exit 0
		;;
	-*) die "unknown option: $arg" ;;
	*)
		[ -z "$ROBOT_NAME" ] || die "unexpected argument: $arg"
		ROBOT_NAME="$arg"
		;;
	esac
done

[ -n "$ROBOT_NAME" ] || die "robot name required - usage: $(basename "$0") [--build] <robot_name>"

# Helpers ----------------------------------------------------------------------

install_micromamba() {
	local target="$MACOS_DIR/bin/micromamba"
	mkdir -p "$MACOS_DIR/bin"
	local arch
	arch="$(uname -m)"
	local platform
	case "$arch" in
	arm64 | aarch64) platform="osx-arm64" ;;
	x86_64 | amd64) platform="osx-64" ;;
	*) die "unsupported CPU architecture: $arch" ;;
	esac
	local url="https://micromamba.snakepit.net/api/micromamba/$platform/latest"
	local tmp="$target.tar.bz2"
	curl -fsSL "$url" -o "$tmp" || die "micromamba download failed: $url"
	if head -c3 "$tmp" 2>/dev/null | grep -q '^BZh'; then
		local tmpd
		tmpd="$(mktemp -d)"
		tar -xjf "$tmp" -C "$tmpd" >/dev/null 2>&1 ||
			{
				rm -rf "$tmpd" "$tmp"
				die "failed to extract micromamba archive"
			}
		local found
		found="$(find "$tmpd" -type f -name micromamba -print -quit)"
		[ -n "$found" ] || {
			rm -rf "$tmpd" "$tmp"
			die "micromamba binary not found in archive"
		}
		mv "$found" "$target"
		chmod +x "$target"
		rm -rf "$tmpd" "$tmp"
	else
		mv "$tmp" "$target"
		chmod +x "$target"
	fi
	"$target" --version >/dev/null 2>&1 ||
		{
			rm -f "$target"
			die "downloaded micromamba is not runnable on this host"
		}
}

activate_env() {
	unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH AMENT_CURRENT_PREFIX
	export MAMBA_ROOT_PREFIX
	set +u
	eval "$("$MAMBA_EXE" shell hook --shell bash)"
	micromamba activate "$ENV_PREFIX"
	set -u
}

source_ros_base() {
	[ -f "$ROS_BASE_PREFIX/setup.bash" ] || die "ROS base missing - run a build first"
	set +u
	source "$ROS_BASE_PREFIX/setup.bash"
	set -u
}

_colcon_build() {
	local ws_dir="$1" conda_pfx="$2"
	shift 2
	local py_exe="$ROS_BASE_PREFIX/bin/python3"
	local py_ver
	py_ver=$("$py_exe" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
	local py_inc="$ROS_BASE_PREFIX/include/python${py_ver}"
	local py_lib="$ROS_BASE_PREFIX/lib/libpython${py_ver}.dylib"
	local np_inc
	np_inc=$("$py_exe" -c "import numpy; print(numpy.get_include())")
	local linker="-Wl,-headerpad_max_install_names \
-Wl,-rpath,$conda_pfx/lib -Wl,-rpath,$ROS_BASE_PREFIX/lib \
-L$conda_pfx/lib -L$ROS_BASE_PREFIX/lib -lpython${py_ver} -Wl,-undefined,dynamic_lookup"
	local cmake_pfx="$conda_pfx:$ROS_BASE_PREFIX"
	[ -d "$ws_dir/install" ] && cmake_pfx="$cmake_pfx:$ws_dir/install"

	(cd "$ws_dir" && colcon build --symlink-install --cmake-args \
		-DCMAKE_BUILD_TYPE=Release \
		"-DCMAKE_SHARED_LINKER_FLAGS=$linker" \
		"-DCMAKE_MODULE_LINKER_FLAGS=$linker" \
		"-DCMAKE_PREFIX_PATH=$cmake_pfx" \
		"-DPython_EXECUTABLE=$py_exe" "-DPython3_EXECUTABLE=$py_exe" \
		"-DPython_ROOT_DIR=$ROS_BASE_PREFIX" "-DPython3_ROOT_DIR=$ROS_BASE_PREFIX" \
		"-DPython_INCLUDE_DIR=$py_inc" "-DPython3_INCLUDE_DIR=$py_inc" \
		"-DPython_LIBRARY=$py_lib" "-DPython3_LIBRARY=$py_lib" \
		"-DPython_NumPy_INCLUDE_DIR=$np_inc" "-DPython3_NumPy_INCLUDE_DIR=$np_inc" \
		"-DCMAKE_IGNORE_PATH=/opt/homebrew;/opt/homebrew/include;/opt/homebrew/lib;/opt/homebrew/opt" \
		"-DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew" \
		"$@")
}

# Build steps ------------------------------------------------------------------

step_prereqs() {
	command -v git >/dev/null 2>&1 || die "Git missing! Please install Git and try again"
	xcode-select -p >/dev/null 2>&1 || die "Xcode Command Line Tools missing! Run: xcode-select --install"
	if [ -x "$MACOS_DIR/bin/micromamba" ]; then
		MAMBA_EXE="$MACOS_DIR/bin/micromamba"
	else
		install_micromamba
		MAMBA_EXE="$MACOS_DIR/bin/micromamba"
	fi
}

step_conda_env() {
	if [ -d "$ENV_PREFIX" ] && [ -x "$ENV_PREFIX/bin/python" ]; then
		local env_py_ver
		env_py_ver=$("$ENV_PREFIX/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
		if [ "$env_py_ver" != "3.12" ]; then
			warn "recreating ros_env because it is Python ${env_py_ver:-unknown}, expected 3.12"
			rm -rf "$ENV_PREFIX"
		fi
	fi
	[ -d "$ENV_PREFIX" ] && return
	mkdir -p "$MACOS_DIR/envs"
	"$MAMBA_EXE" create -y -p "$ENV_PREFIX" -f "$ENV_LOCK" "python=3.12"
}

step_patches() {
	activate_env

	local rust_gen="$CONDA_PREFIX/share/rosidl_generator_rs/cmake/rosidl_generator_rs_generate_interfaces.cmake"
	if [ -f "$rust_gen" ] && ! grep -q "if(NOT APPLE)" "$rust_gen"; then
		python3 - "$rust_gen" <<'PY'
import sys, re
path = sys.argv[1]
src = open(path).read()
patched = re.sub(
    r'(set\(CMAKE_SHARED_LINKER_FLAGS\s+"\$\{CMAKE_SHARED_LINKER_FLAGS\}\s+-Wl,-undefined,error"\))',
    r'if(NOT APPLE)\n  \1\nendif()', src, count=1)
if patched != src:
    open(path, 'w').write(patched)
PY
	fi

	local cmake_dir="$CONDA_PREFIX/lib/cmake"
	if [ -d "$cmake_dir" ]; then
		while IFS= read -r f; do
			sed -i.bak 's/TINYXML2::TINYXML2/tinyxml2::tinyxml2/g' "$f" && rm -f "$f.bak"
		done < <(grep -rln "TINYXML2::TINYXML2" "$cmake_dir" 2>/dev/null || true)
		while IFS= read -r f; do
			sed -i.bak 's/find_package(TINYXML2/find_package(tinyxml2 CONFIG/g' "$f" && rm -f "$f.bak"
		done < <(grep -rln "find_package(TINYXML2" "$cmake_dir" 2>/dev/null || true)
	fi
}

step_ros_base() {
	if [ -f "$ROS_BASE_PREFIX/setup.bash" ]; then
		"$MAMBA_EXE" install -y -p "$ROS_BASE_PREFIX" \
			-c robostack-humble -c conda-forge "${ROS_BASE_PKGS[@]}"
	else
		mkdir -p "$MACOS_DIR"
		"$MAMBA_EXE" create -y -p "$ROS_BASE_PREFIX" \
			-c robostack-humble -c conda-forge "${ROS_BASE_PKGS[@]}"
	fi
}

step_ros_gz() {
	local src="$ROS_GZ_WS/src/ros_gz"
	mkdir -p "$ROS_GZ_WS/src"
	if [ ! -d "$src/.git" ]; then
		git clone --branch "$ROS_GZ_BRANCH" "$ROS_GZ_REPO" "$src"
	fi
	(cd "$src" && git fetch --quiet origin && git checkout --quiet "$ROS_GZ_SHA")

	local marker="$ROS_GZ_WS/.built_sha"
	if [ -f "$marker" ] && [ "$(cat "$marker")" = "$ROS_GZ_SHA" ] &&
		[ -f "$ROS_GZ_WS/install/setup.bash" ]; then
		return
	fi

	activate_env
	local conda_pfx="$CONDA_PREFIX"
	source_ros_base
	export PATH="$conda_pfx/bin:$PATH"
	export GZ_VERSION=harmonic
	export CMAKE_PREFIX_PATH="$conda_pfx:$ROS_BASE_PREFIX"
	_colcon_build "$ROS_GZ_WS" "$conda_pfx"
	printf '%s\n' "$ROS_GZ_SHA" >"$marker"
}

step_control() {
	local src="$CONTROL_WS/src/gz_ros2_control"
	mkdir -p "$CONTROL_WS/src"
	if [ ! -d "$src/.git" ]; then
		git clone --branch "$GZ_ROS2_CONTROL_BRANCH" "$GZ_ROS2_CONTROL_REPO" "$src"
	fi
	(cd "$src" && git fetch --quiet origin && git checkout --quiet "$GZ_ROS2_CONTROL_SHA")

	local marker="$CONTROL_WS/.built_sha"
	if [ -f "$marker" ] && [ "$(cat "$marker")" = "$GZ_ROS2_CONTROL_SHA" ] &&
		[ -f "$CONTROL_WS/install/setup.bash" ]; then
		return
	fi

	activate_env
	local conda_pfx="$CONDA_PREFIX"
	source_ros_base
	export COLCON_TRACE="${COLCON_TRACE:-}"
	set +u
	source "$ROS_GZ_WS/install/setup.bash"
	set -u
	export PATH="$conda_pfx/bin:$PATH"
	export GZ_VERSION=harmonic
	export CMAKE_PREFIX_PATH="$conda_pfx:$ROS_BASE_PREFIX:$ROS_GZ_WS/install"
	_colcon_build "$CONTROL_WS" "$conda_pfx"
	printf '%s\n' "$GZ_ROS2_CONTROL_SHA" >"$marker"
}

step_workspace() {
	[ -d "$WORKSPACE_DIR" ] || die "workspace not found: $WORKSPACE_DIR"

	activate_env
	source_ros_base
	export COLCON_TRACE="${COLCON_TRACE:-}"
	set +u
	source "$ROS_GZ_WS/install/setup.bash"
	source "$CONTROL_WS/install/setup.bash"
	set -u
	find "$WORKSPACE_DIR/build" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	local py_exe="$ROS_BASE_PREFIX/bin/python3"
	(cd "$WORKSPACE_DIR" && PYTHON_EXECUTABLE="$py_exe" colcon build --cmake-args -DBUILD_TESTING=OFF)
}

# Launch -----------------------------------------------------------------------

launch_sim() {
	local robot="$1"
	local bringup="${robot}_bringup"
	local launch_file="${robot}.launch.py"

	[ -f "$WORKSPACE_DIR/$bringup/launch/$launch_file" ] ||
		die "launch file not found: $WORKSPACE_DIR/$bringup/launch/$launch_file"

	printf '\n%sLaunching simulation for robot %s%s\n' "$_G" "$robot" "$_X"

	activate_env
	source_ros_base
	export COLCON_TRACE="${COLCON_TRACE:-}"
	set +u
	source "$ROS_GZ_WS/install/setup.bash"
	source "$CONTROL_WS/install/setup.bash"
	source "$WORKSPACE_DIR/install/setup.bash"
	set -u

	export GZ_SIM_RESOURCE_PATH="\
$WORKSPACE_DIR/install/sim_worlds/share:\
$WORKSPACE_DIR/install/${robot}_description/share:\
${GZ_SIM_RESOURCE_PATH:-}"
	export GZ_SIM_SYSTEM_PLUGIN_PATH="\
$CONTROL_WS/install/gz_ros2_control/lib:\
$CONTROL_WS/install/ign_ros2_control/lib:\
${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"

	mkdir -p "$WORKSPACE_DIR/log"
	local log="$WORKSPACE_DIR/log/sim-$(date +%Y%m%d-%H%M%S).log"

	(cd "$WORKSPACE_DIR" && ros2 launch "$bringup" "$launch_file") 2>&1 | tee "$log" &
	local sim_pid=$!
	trap '[[ -n "${sim_pid:-}" ]] && kill "$sim_pid" 2>/dev/null || true' EXIT INT TERM
	printf '%slog → %s%s\n\n' "$_D" "${log#"$REPO_DIR/"}" "$_X"

	# Close any ephemeral Ogre error windows that sometimes appear empty
	# (window names beginning with "OgreWidnow"). Run in background so
	# it does not block the simulator process.
	if command -v osascript >/dev/null 2>&1; then
		(
			sleep 5
			oosascript <<'AS'
tell application "System Events"
	repeat with p in processes
		try
			repeat with w in (windows of p)
				try
					set wn to name of w
				on error
					set wn to ""
				end try
				if wn starts with "OgreWidnow" then
					try
						click button 1 of w
					end try
				end if
			end repeat
		end try
	end repeat
end tell
AS
		) &
	fi

	wait "$sim_pid" || true
}

# Main -------------------------------------------------------------------------

main() {
	printf '\n%sBuilding environment...%s\n\n' "$_G" "$_X"
	run_step "Prerequisites" step_prereqs
	run_step "Conda environment" step_conda_env
	run_step "macOS patches" step_patches
	run_step "ROS base packages" step_ros_base
	run_step "ros_gz  (${ROS_GZ_SHA:0:9}…)" step_ros_gz
	run_step "gz_ros2_control  (${GZ_ROS2_CONTROL_SHA:0:9}…)" step_control
	run_step "robot-sim workspace" step_workspace

	if $BUILD_ONLY; then
		printf '\n%sBuild complete%s\n\n' "$_G" "$_X"
		return
	fi

	launch_sim "$ROBOT_NAME"
}
main "$@"
