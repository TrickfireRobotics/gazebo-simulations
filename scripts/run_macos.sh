#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# run_macos.sh
# --------------------------------------------------------------------------------------------
# Open XQuartz, allows local connections, and then tries to find a running vscode
# devcontainer, and than attaches to it
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="vsc-gazebo-simulations"
USER_NAME="trickfire"

# Setup XQuartz ----------------------------------------------------------------------

# 1) Install XQuartz from https://www.xquartz.org/ (once)
# 2) In XQuartz Preferences > Security, check:
#    [x] Allow connections from network clients
# 3) Start XQuartz, then run this script.

# Check if XQuartz is running
if pgrep -x "XQuartz" > /dev/null; then
    echo "XQuartz already running."
    sleep_time=2
else
    echo "Opening XQuartz..."
    open -ga XQuartz
    sleep_time=10
fi

sleep "$sleep_time"

# Allow local connections
echo "Allowing local connections..."
xhost + 127.0.0.1 >/dev/null 2>&1 || true
xhost + localhost >/dev/null 2>&1 || true

# Docker Desktop forwards host.docker.internal to the host
echo "Setting up display..."
export DISPLAY=host.docker.internal:0

# Attach to .devcontainer ------------------------------------------------------------

# Find the vscode devcontainer
CONTAINER_ID=$(
    docker ps --format "{{.ID}} {{.Image}}" |
        grep "^.* $CONTAINER_NAME" |
        awk '{print $1}' |
        head -n 1
)

# Check if it is running
if [ -z "$CONTAINER_ID" ]; then
    echo "No running dev container found for flaggi"
    echo "Make sure VS Code has reopened the project in the container"
    exit 1
fi

echo "Attaching to .devcontainer $CONTAINER_ID ..."
echo "--------------------------------"
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    -e DISPLAY="$DISPLAY" \
    -e XAUTHORITY="${XAUTHORITY:-}" \
    "$CONTAINER_ID" \
    bash -il -c '[ -d /home/trickfire/gazebo-simulations/ros2_ws ] && cd /home/trickfire/gazebo-simulations/ros2_ws; exec bash -il'
