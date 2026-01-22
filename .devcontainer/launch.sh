#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".devcontainer/launch.env"

rm -f "$ENV_FILE"
touch "$ENV_FILE"

OS="$(uname)"

if [[ "$OS" == "Darwin" ]]; then

  cat >> "$ENV_FILE" <<EOF
DISPLAY=:0
EOF

else

  if [[ -n "${DISPLAY:-}" ]]; then
    cat >> "$ENV_FILE" <<EOF
DISPLAY=$DISPLAY
EOF
  fi
fi
