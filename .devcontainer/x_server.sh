#!/usr/bin/env bash
set -eo pipefail

# --------------------------------------------------------------------------------------------
# Starts a headless X11 desktop (Xorg/Xvfb + Openbox + x11vnc + noVNC) inside the container.
# Intended for running GUI apps (Gazebo) in Docker.
# Supports --verbose flag for debugging (prints all output to console instead of log file).
# --------------------------------------------------------------------------------------------

VERBOSE=false
LOG_FILE="/tmp/start_x_server.log"
PIDS=()
: >"$LOG_FILE"

log() { printf "\033[1;36m%s\033[0m\n" "$1"; }

# Foreground commands: exit with log dump on failure
run() {
	if $VERBOSE; then
		"$@"
	else "$@" >>"$LOG_FILE" 2>&1 || {
		echo
		echo "[ERROR] Command failed: $*"
		echo "────────── OUTPUT START ──────────"
		cat "$LOG_FILE"
		echo "─────────── OUTPUT END ───────────"
		exit 1
	}; fi
}

# Background services: just redirect output
start() {
	if $VERBOSE; then
		"$@" &
	else "$@" >>"$LOG_FILE" 2>&1 & fi
	PIDS+=($!)
}

# Cleanup function to kill background processes on exit
cleanup() {
	trap - SIGINT SIGTERM EXIT
	log "[CLEANUP] Shutting down X11 / VNC / noVNC…"
	for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
	wait 2>/dev/null || true
}

# --------------------------------------------------------------------------------------------

# Parse --verbose flag
for arg in "$@"; do
	case "$arg" in -v | --verbose) VERBOSE=true ;; esac
done

# Jetson/Tegra has no /dev/dri but Xorg drivers (nvidia, modesetting, dummy) all need it.
# Use Xvfb on Jetson; GPU rendering still happens via EGL through the injected Tegra libs.
# Desktop NVIDIA has /proc/driver/nvidia; everything else gets the dummy Xorg driver.
if [ -e /dev/nvmap ] && [ ! -d /dev/dri ]; then
	BACKEND="xvfb"
	XORG_CONF="/etc/X11/xorg.nvidia.conf"
	log "[X11] Jetson/Tegra detected (no DRI), using Xvfb + EGL"
elif [ -e /proc/driver/nvidia ] || nvidia-smi &>/dev/null; then
	BACKEND="xorg"
	XORG_CONF="/etc/X11/xorg.nvidia.conf"
	log "[X11] Desktop NVIDIA GPU detected, using Xorg nvidia driver"
else
	BACKEND="xorg"
	XORG_CONF="/etc/X11/xorg.dummy.conf"
	log "[X11] No GPU detected, using Xorg dummy driver"
fi

# Parse screen resolution from Xorg config (in docker/xorg.dummy|nvidia.conf)
SCREEN_MODE=$(grep -oP '(?<=Modes ")[^"]+' "$XORG_CONF" | head -1)
SCREEN_WIDTH=$(echo "$SCREEN_MODE" | cut -dx -f1)
SCREEN_HEIGHT=$(echo "$SCREEN_MODE" | cut -dx -f2)
SCREEN_DEPTH=$(grep -oP '(?<=DefaultDepth )\d+' "$XORG_CONF" | head -1)
if [ -z "$SCREEN_WIDTH" ] || [ -z "$SCREEN_HEIGHT" ] || [ -z "$SCREEN_DEPTH" ]; then
	echo "[ERROR] Could not parse resolution from $XORG_CONF"
	exit 1
fi

# Set in the Dockerfile and docker compose.
: "${DISPLAY:?DISPLAY is not set}"
: "${VNC_PORT:?VNC_PORT is not set}"
: "${NOVNC_PORT:?NOVNC_PORT is not set}"

# Check if display is already available:
#   - pgrep covers local Xorg/Xvfb including root-owned (reads /proc, no permission issues)
#   - socket-without-lockfile covers forwarded displays (host X server mounted into container)
#   - socket+lockfile with no process = stale from a previous container run, clean up
_XDISPLAY="${DISPLAY%%.*}"
_DISPLAY_NUM="${_XDISPLAY#:}"
_SOCKET="/tmp/.X11-unix/X${_DISPLAY_NUM}"
_LOCK="/tmp/.X${_DISPLAY_NUM}-lock"
if pgrep -f "Xorg $_XDISPLAY" >/dev/null 2>&1 || pgrep -f "Xvfb $_XDISPLAY" >/dev/null 2>&1; then
	log "[X11] X server already running on $DISPLAY, skipping startup"
	exit 0
elif [ -S "$_SOCKET" ] && [ ! -f "$_LOCK" ]; then
	log "[X11] Display $DISPLAY is forwarded from host, skipping startup"
	exit 0
elif [ -f "$_LOCK" ]; then
	log "[X11] Removing stale X lock file and socket from previous run"
	rm -f "$_LOCK" "$_SOCKET"
fi
unset _XDISPLAY _DISPLAY_NUM _SOCKET _LOCK

# Kill all child processes on exit
trap cleanup SIGINT SIGTERM

# Start X server (Xorg or Xvfb determined above)
if [ "$BACKEND" = "xvfb" ]; then
	log "[X11] Starting Xvfb on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
	start Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
else
	log "[X11] Starting Xorg on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
	start sudo Xorg "$DISPLAY" -noreset -config "$XORG_CONF"
fi
sleep 1
stty sane 2>/dev/null || true # Xorg alters terminal CR/LF settings

# Start window manager
log "[WM] Starting Openbox window manager"
start openbox-session

# Start x11vnc server for VNC connection
log "[VNC] Starting x11vnc on port ${VNC_PORT}"
start x11vnc -display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -nopw -xkb

# Start noVNC web client to serve the VNC desktop in a browser
log "[noVNC] Starting browser-based desktop on port ${NOVNC_PORT}"
start /usr/share/novnc/utils/launch.sh --vnc "localhost:${VNC_PORT}" --listen "${NOVNC_PORT}"
log "[noVNC] Desktop available at: http://localhost:${NOVNC_PORT}/vnc.html"

# Detach all background services so they survive this script exiting
disown "${PIDS[@]}"
log "[MAIN] All services started"
