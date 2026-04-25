#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# start-container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
#
# Usage:
#   ./scripts/start-container.sh
#     - Checks for NVIDIA hardware and driver availability
#     - Starts with GPU passthrough and host-display rendering when available
#     - Falls back to VNC/noVNC mode when no GPU is detected (localhost:6080)
#
# IMPORTANT:
#   - Run from the HOST, not inside the container
#   - Uses docker/docker-compose.yml (+ docker/docker-compose-gpu.yml if NVIDIA GPU is detected)
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="gazebo-sim"
USER_NAME="trickfire"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

NVIDIA_GPU=false
if [ -e /dev/nvhost-gpu ] || (command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null); then
	echo "NVIDIA GPU detected. Enabling GPU support in container."
	NVIDIA_GPU=true
else
	echo "No NVIDIA GPU available. Running without GPU support."
fi

# STOP
if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
	echo "[INFO] Stopping running container..."
	if $NVIDIA_GPU; then
		docker compose -f docker/docker-compose.yml -f docker/docker-compose-gpu.yml down
	else
		docker compose -f docker/docker-compose.yml down
	fi
fi

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# START
echo "[INFO] Starting container..."
if $NVIDIA_GPU; then
	echo "[INFO] NVIDIA GPU mode: rendering to host display ${DISPLAY}"
	xhost +local:docker
	docker compose -f docker/docker-compose.yml -f docker/docker-compose-gpu.yml up -d --build
else
	docker compose -f docker/docker-compose.yml up -d --build
	HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || echo '')"
	DISPLAY=":0"
	echo ""
	echo "[INFO] No NVIDIA GPU detected, starting in VNC mode on display ${DISPLAY}"
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
