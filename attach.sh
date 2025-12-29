#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# run_macos.sh
# --------------------------------------------------------------------------------------------
# Finds the running vscode devcontainer, and than attaches to it
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="vsc-gazebo-simulations"
USER_NAME="trickfire"


# Find vscode devcontainer -------------------------------------------------------------------

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

# Attach to .devcontainer --------------------------------------------------------------------

echo ""
echo "Attaching to .devcontainer $CONTAINER_ID ..."
echo "--------------------------------"
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    -e XAUTHORITY="${XAUTHORITY:-}" \
    "$CONTAINER_ID" \
    bash -il -c '[ -d /home/trickfire/gazebo-simulations/ros2_ws ] && cd /home/trickfire/gazebo-simulations/ros2_ws; exec bash -il'
