#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# start_x_server.sh
# --------------------------------------------------------------------------------------------
# Starts a complete headless X11 desktop environment inside the container.
#
# This script sets up:
#   - A virtual X server (Xorg) using a dummy display
#   - A lightweight window manager (Openbox)
#   - A VNC server (x11vnc) for remote access
#
# Intended for:
#   - Running GUI apps (Gazebo) in a Docker container
# --------------------------------------------------------------------------------------------

log() {
    local message="$1"
    local bold_cyan="\033[1;36m"  # 1 = bold, 36 = cyan
    local reset="\033[0m"         # Reset colors
    echo -e "${bold_cyan}${message}${reset}"
}

# --------------------------------------------------------------------------------------------
# ENVIRONMENT VALIDATION
# --------------------------------------------------------------------------------------------
#
# Ensure all required environment variables are set before continuing.
# These are normally defined in the Dockerfile.
#
: "${DISPLAY:?DISPLAY is not set (expected something like :1)}"
: "${VNC_PORT:?VNC_PORT is not set (expected 5900)}"
: "${NOVNC_PORT:?NOVNC_PORT is not set (expected 6080)}"
: "${SCREEN_WIDTH:?SCREEN_WIDTH is not set}"
: "${SCREEN_HEIGHT:?SCREEN_HEIGHT is not set}"
: "${SCREEN_DEPTH:?SCREEN_DEPTH is not set}"


# --------------------------------------------------------------------------------------------
# START X11 SERVER (HEADLESS)
# --------------------------------------------------------------------------------------------
# Launch an Xorg server on display :1
#
# Flags:
#   $DISPLAY              -> Target display (defined in Dockerfile)
#   -noreset              -> Prevent Xorg from restarting when clients disconnect
#   -config xorg.conf     -> Use a custom dummy display configuration
#
log "[X11] Starting Xorg on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
Xorg "$DISPLAY" -noreset -config /etc/X11/xorg.conf &
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
openbox-session &


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
x11vnc \
    -display "$DISPLAY" \
    -forever \
    -shared \
    -rfbport "$VNC_PORT" \
    -nopw \
    -xkb &

# --------------------------------------------------------------------------------------------
# START BROWSER-BASED DESKTOP (noVNC)
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
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 &
log "Done"
