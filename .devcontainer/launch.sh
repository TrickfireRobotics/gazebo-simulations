#!/usr/bin/env bash

set -euo pipefail

# --------------------------------------------------------------------------------------------
# launch.sh
# --------------------------------------------------------------------------------------------
# Devcontainer initialization script.
#
# This script:
#   - Creates or overwrites the .devcontainer/launch.env file
#   - Sets environment variables based on host OS
#   - Uses defaults when host variables are not set
# --------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------
# VARIABLES & METHODS
# --------------------------------------------------------------------------------------------
# These are the variables the script uses, and simple log methods for easier logging
#
LAUNCH_ENV_FILE=".devcontainer/launch.env"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*"; }
log_error() { echo "[ERROR] $*" >&2; }

OS="$(uname)"
log_info "Detected host OS: $OS"

# --------------------------------------------------------------------------------------------
# ENV VARS SETUP
# --------------------------------------------------------------------------------------------
# This switch statement will set some enviromental variables based on the host os:
# DISPLAY
#   - MacOS: Hardset to :0
#   - Linux & Windows WSL: forward host DISPLAY
#
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

# --------------------------------------------------------------------------------------------
# LAUNCH ENV FILE
# --------------------------------------------------------------------------------------------
# Writes the env vars defined above into .devcontainer/launch.env to be source by
# the container.
#
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
    echo "$var=${ENV_VARS_ARRAY[$var]}"
    echo "--------------------------------------------------"
else
    log_warn "No environment variables were set"
fi
