#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".devcontainer/launch.env"

rm -f "$ENV_FILE"
touch "$ENV_FILE"

OS="$(uname)"

if [[ "$OS" == "Darwin" ]]; then

  cat >> "$ENV_FILE" <<EOF
DISPLAY_FOR_TRICKFIRE_GZ_SIM=:0
EOF

else

  if [[ -n "${DISPLAY:-}" ]]; then
    cat >> "$ENV_FILE" <<EOF
DISPLAY_FOR_TRICKFIRE_GZ_SIM=$DISPLAY
EOF
  fi
fi

