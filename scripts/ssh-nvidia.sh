#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# ssh-nvidia.sh
# --------------------------------------------------------------------------------------------
# SSHes into a named NVIDIA PC with a labelled prompt.
#
# Usage:
#   ./scripts/ssh-nvidia.sh <target>
# --------------------------------------------------------------------------------------------

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../nvidia-pcs.sh"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
	echo "Usage: $0 <target>"
	echo "Known PCs: ${!NVIDIA_PCS[*]}"
	exit 1
fi

PC_IP="${NVIDIA_PCS[$TARGET]:-}"
if [[ -z "$PC_IP" ]]; then
	echo "Unknown PC: $TARGET"
	echo "Known PCs: ${!NVIDIA_PCS[*]}"
	exit 1
fi

TERM=xterm-256color sshpass -p 'trickfire' ssh -Y -t \
	-o GSSAPIAuthentication=no -o LogLevel=ERROR -o StrictHostKeyChecking=no \
	trickfire@"$PC_IP" \
	"if [ -d ~/gazebo-simulations ]; then \
		PROMPT_ENV=${TARGET}-host bash --rcfile ~/gazebo-simulations/docker/shell/ssh.bashrc.sh; \
	else \
		bash; \
	fi"
