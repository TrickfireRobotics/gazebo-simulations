#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# nvidia-container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
#
# Usage:
#   ./scripts/nvidia-container.sh           # VNC mode (browser at localhost:6080)
#   ./scripts/nvidia-container.sh --local   # Local mode (renders to host display)
#
# IMPORTANT:
#   - Run from the HOST, not inside a container
#   - Requires docker/docker-compose.yml
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="gazebo-sim"
USER_NAME="trickfire"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

LOCAL_MODE=false
for arg in "$@"; do
    case "$arg" in
        --local) LOCAL_MODE=true ;;
    esac
done

# STOP
if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
    echo "[INFO] Stopping running container..."
    docker compose -f docker/docker-compose.yml down
fi
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# START
echo "[INFO] Starting container..."
if $LOCAL_MODE; then
    echo "[INFO] Local mode: rendering to host display ${DISPLAY}"
    xhost +local:docker 2>/dev/null || true

    # Create xauth file with correct cookie for container
    XAUTH_FILE=/tmp/container.xauth
    touch $XAUTH_FILE
    xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH_FILE nmerge -

    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker run -d --rm \
        --name "$CONTAINER_NAME" \
        --runtime nvidia \
        --privileged \
        -e DISPLAY="$DISPLAY" \
        -e XAUTHORITY=/tmp/container.xauth \
        -e NVIDIA_VISIBLE_DEVICES=all \
        -e NVIDIA_DRIVER_CAPABILITIES=graphics,display,compute,utility \
        -e TZ=UTC \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v $XAUTH_FILE:/tmp/container.xauth \
        -v "$(pwd):/home/trickfire/gazebo-simulations" \
        -w /home/trickfire/gazebo-simulations \
        --user trickfire \
        gazebo-simulations:latest \
        sleep infinity
else
    docker compose -f docker/docker-compose.yml up -d
fi

# ATTACH
echo "[INFO] Attaching shell..."
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    -e DISPLAY="$DISPLAY" \
    "$CONTAINER_NAME" \
    bash -il
