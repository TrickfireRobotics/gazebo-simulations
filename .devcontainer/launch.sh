#!/usr/bin/env bash

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

set -euo pipefail

ENV_FILE=".devcontainer/launch.env"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*"; }
log_error() { echo "[ERROR] $*" >&2; }

log_info "Initializing environment file at $ENV_FILE..."
rm -f "$ENV_FILE"
touch "$ENV_FILE"

OS="$(uname)"
log_info "Detected host OS: $OS"

# -----------------------------
# Set environment variables
# -----------------------------
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
        log_info "Configuring environment for Windows"
        ENV_VARS_ARRAY["DISPLAY"]="${DISPLAY:-:0}"
        ;;
    *)
        log_warn "Unknown OS: $OS. No OS-specific environment variables set."
        ;;
esac

# -----------------------------
# Write env file
# -----------------------------
if [[ ${#ENV_VARS_ARRAY[@]} -gt 0 ]]; then
    > "$ENV_FILE"
    for var in "${!ENV_VARS_ARRAY[@]}"; do
        echo "$var=${ENV_VARS_ARRAY[$var]}" >> "$ENV_FILE"
    done

    log_info "Environment file $ENV_FILE configured successfully with the following variables:"
    echo "--------------------------------------------------"
    echo "$var=${ENV_VARS_ARRAY[$var]}"
    echo "--------------------------------------------------"
else
    log_warn "No environment variables were set"
fi
