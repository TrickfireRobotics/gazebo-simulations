#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# nvidia-container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
#
# Usage:
#   ./scripts/nvidia-container.sh           # VNC mode: container runs its own X server
#   ./scripts/nvidia-container.sh --local   # X11 mode: renders to $DISPLAY directly
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="gazebo-sim"
USER_NAME="trickfire"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

LOCAL_MODE=false
for arg in "$@"; do
	case "$arg" in --local) LOCAL_MODE=true ;; esac
done

# Stop any running instance
if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
	echo "[INFO] Stopping running container..."
	docker compose -f docker/docker-compose.yml down
fi
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "[INFO] Starting container..."
if $LOCAL_MODE; then
	echo "[INFO] Local X11 mode: rendering to host display ${DISPLAY}"
	xhost +local: 2>/dev/null || true
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.local.yml up -d --build
else
	docker compose -f docker/docker-compose.yml up -d --build
	HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
	echo "[INFO] VNC viewer -> ${HOST_IP:-<host-ip>}:${VNC_PORT:-5900}"
	echo "[INFO] Browser    -> http://${HOST_IP:-<host-ip>}:${NOVNC_PORT:-6080}/vnc.html"
fi

echo "[INFO] Attaching shell..."
docker exec -it -u "$USER_NAME" -e TERM=xterm-256color "$CONTAINER_NAME" bash -il
