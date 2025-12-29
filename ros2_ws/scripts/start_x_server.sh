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
