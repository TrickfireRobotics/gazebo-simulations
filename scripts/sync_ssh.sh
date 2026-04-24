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

declare -A KNOWN_HOSTS=(
	[xavier]="192.168.0.205"
	[orin]="192.168.0.211"
)

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
	if [[ -t 0 ]]; then
		echo "No target specified. Choose a machine:"
		OPTIONS=($(printf "%s\n" "${!KNOWN_HOSTS[@]}" | sort))
		select CHOICE in "${OPTIONS[@]}" "quit"; do
			if [[ "$CHOICE" == "quit" ]]; then
				echo "Cancelled."
				exit 0
			elif [[ -n "$CHOICE" ]]; then
				TARGET="$CHOICE"
				break
			fi
			echo "Invalid selection. Try again."
		done
	else
		echo "Usage: $0 <target>"
		echo "Known PCs: ${!KNOWN_HOSTS[*]}"
		exit 1
	fi
fi


REMOTE_IP="${KNOWN_HOSTS[$TARGET]:-$TARGET}"
REPO_ROOT="$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)"

printf "\e[0;35m${REMOTE_USER}@${REMOTE_IP}\e[0m : \e[0;32m${REMOTE_PATH}\e[0m\n"

rsync -az \
	--out-format='%n' \
	--filter=':- .gitignore' \
	--exclude='.git/' \
	-e "sshpass -p trickfire ssh -q -o StrictHostKeyChecking=no -o GSSAPIAuthentication=no -o ConnectTimeout=5" \
	"${REPO_ROOT}/" \
	"${REMOTE_USER}@${REMOTE_IP}:${REMOTE_PATH}" || {
	echo "Host unreachable!"
	exit 1
}
