#!/bin/bash

# Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" -ac +extension GLX +render -noreset &
# XVFB_PID=$!

Xorg :1 -noreset -config /etc/X11/xorg.conf &
sleep 1

openbox-session &
WM_PID=$!

x11vnc -display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -nopw -xkb &
VNC_PID=$!
