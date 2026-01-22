#!/usr/bin/env bash
set -o pipefail

# --------------------------------------------------------------------------------------------
# start_x_server.sh
# --------------------------------------------------------------------------------------------
# Starts a complete headless X11 desktop environment inside the container.
#
# This script sets up:
#   - A virtual X server (Xorg) using a dummy display
#   - A lightweight window manager (Openbox)
#   - A VNC server (x11vnc) for remote access
#   - noVNC for accesing the VNC server through a browser
#
# Intended for:
#   - Running GUI apps (Gazebo) in a Docker container

# --------------------------------------------------------------------------------------------
# VARIABLES
# --------------------------------------------------------------------------------------------
# These are all the values the commands below use

SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
SCREEN_DEPTH=24

# These are defined in the .devcontainer Dockerfile
# or in the .devcontainer/launch.env file
# The following lines check if the env vars are set
: "${DISPLAY:?DISPLAY is not set}"
: "${VNC_PORT:?VNC_PORT is not set}"
: "${NOVNC_PORT:?NOVNC_PORT is not set}"

VERBOSE=false
LOG_FILE="/tmp/start_x_server.log"
: > "$LOG_FILE"

# --------------------------------------------------------------------------------------------
# ARGUMENT PARSING
# --------------------------------------------------------------------------------------------

for arg in "$@"; do
    case "$arg" in
        -v|--verbose)
            VERBOSE=true
            ;;
    esac
done

# --------------------------------------------------------------------------------------------
# HELPER METHODS
# --------------------------------------------------------------------------------------------

log() {
    local message="$1"
    local bold_cyan="\033[1;36m"  # 1 = bold, 36 = cyan
    local reset="\033[0m"         # Reset colors
    echo -e "${bold_cyan}${message}${reset}"
}

run() {
    if $VERBOSE; then
        "$@"
    else
        "$@" >>"$LOG_FILE" 2>&1 || {
            echo
            echo "❌ Command failed: $*"
            echo "────────── OUTPUT START ──────────"
            cat "$LOG_FILE"
            echo "─────────── OUTPUT END ───────────"
            exit 1
        }
    fi
}

cleanup() {
    # disable traps to prevent infinitre rercustion
    trap - SIGINT SIGTERM EXIT
    log "[CLEANUP] Shutting down X11 / VNC / noVNC…"
    kill -- -$$ 2>/dev/null
    wait 2>/dev/null
    exit 0
}

# --------------------------------------------------------------------------------------------
# DISPLAY CHECK
# --------------------------------------------------------------------------------------------
# Checks if anything is already using the display this x-server is planning to use
#
if xdpyinfo -display "$DISPLAY" &>/dev/null; then
    log "[ERROR] Display $DISPLAY is in use!"
    exit 1
fi

# --------------------------------------------------------------------------------------------
# CLEANUP
# --------------------------------------------------------------------------------------------
# Kills all the processes this script startet when it ends. This method specifically traps
# the method cleanup on the three events.
#
trap cleanup SIGINT SIGTERM EXIT

# --------------------------------------------------------------------------------------------
# START X11 SERVER
# --------------------------------------------------------------------------------------------
# Launch an Xorg server on display :1
#
# Flags:
#   $DISPLAY              -> Target display (defined in Dockerfile)
#   -noreset              -> Prevent Xorg from restarting when clients disconnect
#   -config xorg.conf     -> Use a custom dummy display configuration
#
log "[X11] Starting Xorg on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
run Xorg "$DISPLAY" -noreset -config /etc/X11/xorg.conf &
sleep 1

# --------------------------------------------------------------------------------------------
# START WINDOW MANAGER
# --------------------------------------------------------------------------------------------
# Openbox is a very lightweight window manager.
# It provides:
#   - Window decorations
#   - Basic window movement / resizing
#   - A usable desktop environment
#
log "[WM] Starting Openbox window manager"
run openbox-session &

# --------------------------------------------------------------------------------------------
# START VNC SERVER
# --------------------------------------------------------------------------------------------
# x11vnc allows remote access to the X11 display over VNC.
#
# Flags:
#   -display "$DISPLAY"   -> Display used in Xorg (defined in Dockerfile)
#   -forever              -> Keep running after clients disconnect
#   -shared               -> Allow multiple VNC clients at once
#   -rfbport "$VNC_PORT"  -> Port to listen on (defined in Dockerfile)
#   -nopw                 -> Disable password auth
#   -xkb                  -> Enable proper keyboard mapping
#
log "[VNC] Starting x11vnc on port ${VNC_PORT}"
run x11vnc \
    -display "$DISPLAY" \
    -forever \
    -shared \
    -rfbport "$VNC_PORT" \
    -nopw \
    -xkb &

# --------------------------------------------------------------------------------------------
# START noVNC
# --------------------------------------------------------------------------------------------
# launch.sh is the official noVNC helper script.
# It starts:
#   - websockify (WebSocket <-> VNC bridge)
#   - a small web server that serves the noVNC HTML/JS client
#
# This allows connecting to the container's desktop from a web browser
#
# Flags:
#   --vnc localhost:$VNC_PORT  -> Address of the local VNC server (defined in Dockerfile)
#   --listen $NO_VMC_PORT             -> Port exposed for browser access (defined in Dockerfile)
#
# Usage:
#   Open a browser and navigate to:
#     http://<docker-host>:6080/vnc.html
#
# Runs in the background so the script continues normally.
#
log "[noVNC] Starting browser-based desktop on port ${NOVNC_PORT}"
run /usr/share/novnc/utils/launch.sh \
    --vnc "localhost:${VNC_PORT}" \
    --listen "${NOVNC_PORT}" &
log "[noVNC] Desktop available at: http://localhost:${NOVNC_PORT}/vnc.html"

log "[MAIN] All services started. Press Ctrl+C to stop"
wait
