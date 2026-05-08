#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# sync_ssh.sh
# --------------------------------------------------------------------------------------------
# Syncs the local gazebo-simulations repo to a Jetson over rsync.
# Excludes are sourced from .gitignore automatically.
#
# Usage:
#   ./scripts/sync_ssh.sh <target>
# --------------------------------------------------------------------------------------------

set -euo pipefail

REMOTE_USER="trickfire"
REMOTE_PATH="/home/trickfire/gazebo-simulations"

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../remote_pcs.sh"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
	echo "Usage: $0 <target>"
	echo "Known PCs: ${!NVIDIA_PCS[*]}"
	exit 1
fi

REMOTE_IP="${NVIDIA_PCS[$TARGET]:-$TARGET}"
REPO_ROOT="$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)"

printf "\e[0;35m${REMOTE_USER}@${REMOTE_IP}\e[0m : \e[0;32m${REMOTE_PATH}\e[0m\n"

rsync -az \
	--recursive \
	--delete \
	--out-format='%n' \
	--filter=':- .gitignore' \
	--exclude='.git/' \
	-e "sshpass -p trickfire ssh -q -o StrictHostKeyChecking=no -o GSSAPIAuthentication=no -o ConnectTimeout=5" \
	"${REPO_ROOT}/" \
	"${REMOTE_USER}@${REMOTE_IP}:${REMOTE_PATH}" || {
	echo "Host unreachable!"
	exit 1
}
