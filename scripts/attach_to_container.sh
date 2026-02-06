#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# attach_to_container.sh
# --------------------------------------------------------------------------------------------
# Host-side helper script to attach an external terminal to a running VS Code devcontainer.
#
# This script:
#   - Locates the active devcontainer started by VS Code
#   - Opens an interactive shell inside the container as the configured user
#   - Preserves terminal settings for a proper interactive experience
#
# Intended usage:
#   - Run from the HOST system (e.g. not inside the container)
#   - Useful for attaching additional terminals to an already-running devcontainer
#
# IMPORTANT:
#   - This script is NOT meant to be executed from inside the container
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

WORKSPACE_FOLDER="$(basename "$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)")"
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    -e XAUTHORITY="${XAUTHORITY:-}" \
    "$CONTAINER_ID" \
    bash -il -c "[ -d /home/trickfire/${WORKSPACE_FOLDER} ] && cd /home/trickfire/${WORKSPACE_FOLDER}; exec bash -il"
