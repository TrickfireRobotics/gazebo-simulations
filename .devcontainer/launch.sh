#!/usr/bin/env bash

set -euo pipefail

# --------------------------------------------------------------------------------------------
# launch.sh
# --------------------------------------------------------------------------------------------
# Devcontainer initialization script
# This script runs on the host machine via the devcontainer's initializeCommand.
# It sets up the correct DISPLAY environment variable for the container:
#   - Linux: forwards the host DISPLAY variable to the container's X server
#   - Windows WSL: forwards the host DISPLAY variable
#   - macOS: uses a hardcoded :0 for the custom X server
# --------------------------------------------------------------------------------------------


LAUNCH_ENV_FILE=".devcontainer/launch.env"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*"; }
log_error() { echo "[ERROR] $*" >&2; }

OS="$(uname)"
log_info "Detected host OS: $OS"

declare -A ENV_VARS_ARRAY

case "$OS" in
    Darwin)
        log_info "Configuring environment for MacOS"
        ENV_VARS_ARRAY["DISPLAY"]=":0"
        ;;
    Linux)
        log_info "Configuring environment for Linux"
        ENV_VARS_ARRAY["DISPLAY"]="${DISPLAY:-:0}"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        log_info "Configuring environment for Windows WSL"
        ENV_VARS_ARRAY["DISPLAY"]="${DISPLAY:-:0}"
        ;;
    *)
        log_warn "Unknown OS: $OS. No OS-specific environment variables set."
        ;;
esac

# Bash prompt setup
if [ -f /etc/nv_tegra_release ]; then
    log_info "Detected Jetson host — setting PROMPT_ENV=${HOSTNAME}-dev"
    ENV_VARS_ARRAY["PROMPT_ENV"]="${HOSTNAME}-dev"
else
    log_info "Detected local host — setting PROMPT_ENV=local-dev"
    ENV_VARS_ARRAY["PROMPT_ENV"]="local-dev"
fi

# Write env vars into the launch.env file
log_info "Initializing environment file at $LAUNCH_ENV_FILE..."
rm -f "$LAUNCH_ENV_FILE"
touch "$LAUNCH_ENV_FILE"

if [[ ${#ENV_VARS_ARRAY[@]} -gt 0 ]]; then
    > "$LAUNCH_ENV_FILE"
    for var in "${!ENV_VARS_ARRAY[@]}"; do
        echo "$var=${ENV_VARS_ARRAY[$var]}" >> "$LAUNCH_ENV_FILE"
    done

    log_info "Environment file $LAUNCH_ENV_FILE configured successfully with the following variables:"
    echo "--------------------------------------------------"
    for var in "${!ENV_VARS_ARRAY[@]}"; do
        echo "$var=${ENV_VARS_ARRAY[$var]}"
    done
    echo "--------------------------------------------------"
else
    log_warn "No environment variables were set"
fi
