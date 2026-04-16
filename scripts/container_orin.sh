#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# start_container.sh
# --------------------------------------------------------------------------------------------
# Kills the sim container if running, starts it fresh, and attaches a shell.
#
# Usage:
#   ./scripts/start_container.sh
#
# IMPORTANT:
#   - Run from the HOST, not inside the container
#   - Requires docker-compose.yml at the project root
# --------------------------------------------------------------------------------------------

set -euo pipefail

CONTAINER_NAME="gazebo-sim"
USER_NAME="trickfire"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# STOP
if docker ps -q --filter "name=^${CONTAINER_NAME}$" | grep -q .; then
    echo "[INFO] Stopping running container..."
    docker compose down
fi

# START
echo "[INFO] Starting container..."
docker compose up -d

# ATTACH
echo "[INFO] Attaching shell..."
docker exec -it -u "$USER_NAME" \
    -e TERM=xterm-256color \
    "$CONTAINER_NAME" \
    bash -il
