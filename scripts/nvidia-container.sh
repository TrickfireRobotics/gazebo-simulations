#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# nvidia-container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
# Access the desktop via VNC viewer (port 5900) or browser (port 6080).
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="gazebo-sim"
USER_NAME="trickfire"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Stop any running instance
if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
	echo "[INFO] Stopping running container..."
	docker compose -f docker/docker-compose.yml down
fi
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "[INFO] Starting container..."
docker compose -f docker/docker-compose.yml up -d --build
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "[INFO] VNC viewer -> ${HOST_IP:-<host-ip>}:${VNC_PORT:-5900}"
echo "[INFO] Browser    -> http://${HOST_IP:-<host-ip>}:${NOVNC_PORT:-6080}/vnc.html"

echo "[INFO] Attaching shell..."
docker exec -it -u "$USER_NAME" -e TERM=xterm-256color "$CONTAINER_NAME" bash -il
