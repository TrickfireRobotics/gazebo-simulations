#!/usr/bin/env bash

set -euo pipefail

# --------------------------------------------------------------------------------------------
# attach_to_container.sh
# Attaches a terminal to the running devcontainer. Run from the host.
# --------------------------------------------------------------------------------------------

CONTAINER_NAME="vsc-gazebo-simulations"
USER_NAME="trickfire"

CONTAINER_ID=$(docker ps -q --filter "name=$CONTAINER_NAME" | head -n1)
if [ -z "$CONTAINER_ID" ]; then
	echo "No running container matching '$CONTAINER_NAME'" >&2
	exit 1
fi

WORKSPACE=$(basename "$(realpath "${BASH_SOURCE[0]%/*}/..")")
docker exec -it -u "$USER_NAME" -e TERM=xterm-256color "$CONTAINER_ID" \
	bash -il -c "cd /home/$USER_NAME/$WORKSPACE 2>/dev/null; exec bash -il"
