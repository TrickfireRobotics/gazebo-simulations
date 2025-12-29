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

set -e

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
/usr/share/novnc/utils/launch.sh \
    --vnc localhost:$VNC_PORT \
    --listen "$NO_VNC_PORT" &
