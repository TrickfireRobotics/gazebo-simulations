#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# nvidia-container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
#
# Usage:
#   ./scripts/nvidia-container.sh           # VNC mode (browser at localhost:6080)
#   ./scripts/nvidia-container.sh --local   # Local mode (uses compose extension + host display)
#
# IMPORTANT:
#   - Run from the HOST, not inside the container
#   - Uses docker/docker-compose.yml (+ docker/docker-compose-local.yml with --local)
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
    if $LOCAL_MODE; then
        docker compose -f docker/docker-compose.yml -f docker/docker-compose-local.yml down
    else
        docker compose -f docker/docker-compose.yml down
    fi
fi

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true


# START
echo "[INFO] Starting container..."
if $LOCAL_MODE; then
    echo "[INFO] Local mode: rendering to host display ${DISPLAY}"
    xhost +local:docker
    docker compose -f docker/docker-compose.yml -f docker/docker-compose-local.yml up -d --build
else
    docker compose -f docker/docker-compose.yml up -d --build
	HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
	echo "[INFO] VNC viewer -> ${HOST_IP:-<host-ip>}:${VNC_PORT:-5900}"
	echo "[INFO] Browser    -> http://${HOST_IP:-<host-ip>}:${NOVNC_PORT:-6080}/vnc.html"
fi

# ATTACH
echo "[INFO] Attaching shell..."
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    -e DISPLAY="$DISPLAY" \
    "$CONTAINER_NAME" \
    bash -il
