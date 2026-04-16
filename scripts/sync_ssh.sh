#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# sync_ssh.sh
# --------------------------------------------------------------------------------------------
# Syncs the local gazebo-simulations repo to a Jetson over rsync.
# Excludes are sourced from .gitignore automatically.
#
# Usage:
#   ./scripts/sync_ssh.sh <target>
#
#   target  - "xavier", "orin", or a raw IP address
#
# Examples:
#   ./scripts/sync_ssh.sh xavier
#   ./scripts/sync_ssh.sh 192.168.0.148
# --------------------------------------------------------------------------------------------

set -euo pipefail

REMOTE_USER="trickfire"
REMOTE_PATH="/home/trickfire/gazebo-simulations"

declare -A KNOWN_HOSTS=(
    [xavier]="192.168.0.148"
    [orin]="192.168.0.211"
)

# Pretty-print rsync output.
#
# rsync is invoked with --out-format='%n' (bare filenames only) and --stats.
# We show each transferred file with a tick and pull out the two summary lines
# from the stats block; everything else is suppressed.
_pretty_rsync() {
    local is_tty=false; [[ -t 1 ]] && is_tty=true

    local OFF="" BOLD="" DIM="" G="" B=""
    if $is_tty; then
        OFF=$'\033[0m' BOLD=$'\033[1m' DIM=$'\033[2m'
        G=$'\033[32m'  B=$'\033[36m'
    fi

    local count=0

    while IFS= read -r line; do
        line="${line%$'\r'}"

        case "$line" in
            ""|"./")
                ;;
            "sent "*)
                printf "\n${BOLD}${B}  %s${OFF}\n" "$line"
                ;;
            "total size"*)
                printf "${DIM}  %s${OFF}\n" "$line"
                ;;
            "Number of"*|"Total file"*|"Total transferred"*|"Literal"*|\
            "Matched"*|"Unmatched"*|"File list"*|"Total bytes"*|\
            "Total sent"*|"Total received"*)
                :
                ;;
            */)
                :   # directory — suppress
                ;;
            *)
                printf "  ${G}✓${OFF}  %s\n" "$line"
                (( count++ )) || true
                ;;
        esac
    done

    if [[ $count -eq 0 ]]; then
        printf "${DIM}  (nothing to sync)${OFF}\n"
    fi
}

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo "Usage: $0 <target>"
    echo "  target  'xavier', 'orin', or a raw IP address"
    exit 1
fi

if [[ -v KNOWN_HOSTS[$TARGET] ]]; then
    REMOTE_IP="${KNOWN_HOSTS[$TARGET]}"
else
    REMOTE_IP="$TARGET"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

printf "\n\e[0;35m  ${REMOTE_USER}@${REMOTE_IP}\e[0m : \e[0;32m${REMOTE_PATH}\n"

rsync -az \
    --out-format='%n' \
    --stats \
    --filter=':- .gitignore' \
    --exclude='.git/' \
    -e "sshpass -p trickfire ssh -q -o StrictHostKeyChecking=no -o GSSAPIAuthentication=no" \
    "${REPO_ROOT}/" \
    "${REMOTE_USER}@${REMOTE_IP}:${REMOTE_PATH}" \
    | _pretty_rsync
