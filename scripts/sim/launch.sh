#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$OSTYPE" == "darwin"* ]]; then
    exec "$SCRIPT_DIR/launch.macos.sh" "$@"
else
    exec "$SCRIPT_DIR/launch.linux.sh" "$@"
fi
