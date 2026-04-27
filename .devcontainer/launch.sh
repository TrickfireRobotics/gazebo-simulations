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
	# If $DISPLAY is set and its socket exists, use it directly.
	# Otherwise auto-detect from the first socket in /tmp/.X11-unix/,
	# since the display number on Ubuntu can be :1001 or similar and
	# $DISPLAY may not be available in a non-interactive shell.
	DETECTED_DISPLAY=""
	log_info "Configuring environment for Linux"
	if [ -n "${DISPLAY:-}" ] && [ -e "/tmp/.X11-unix/X${DISPLAY#:}" ]; then
		DETECTED_DISPLAY="$DISPLAY"
		log_info "Using DISPLAY from environment: $DETECTED_DISPLAY"
	else
		SOCKET=$(ls /tmp/.X11-unix/X* 2>/dev/null | head -1)
		if [ -n "$SOCKET" ]; then
			DETECTED_DISPLAY=":${SOCKET##*X}"
			log_info "Auto-detected display $DETECTED_DISPLAY from X11 socket"
		else
			log_warn "No X11 socket found, falling back to default :0"
		fi
	fi
	ENV_VARS_ARRAY["DISPLAY"]="${DETECTED_DISPLAY:-:0}"
	;;
MINGW* | CYGWIN* | MSYS*)
	log_info "Configuring environment for Windows WSL"
	ENV_VARS_ARRAY["DISPLAY"]="${DISPLAY:-:0}"
	;;
*)
	log_warn "Unknown OS: $OS. No OS-specific environment variables set."
	;;
esac

# Bash prompt setup
if [ -f /etc/nv_tegra_release ]; then
	log_info "Detected Jetson host - setting PROMPT_ENV=${HOSTNAME}-dev"
	ENV_VARS_ARRAY["PROMPT_ENV"]="${HOSTNAME}-dev"
else
	log_info "Detected local host - setting PROMPT_ENV=local-dev"
	ENV_VARS_ARRAY["PROMPT_ENV"]="local-dev"
fi

# Write env vars into the launch.env file
log_info "Initializing environment file at $LAUNCH_ENV_FILE..."
rm -f "$LAUNCH_ENV_FILE"
touch "$LAUNCH_ENV_FILE"

if [[ ${#ENV_VARS_ARRAY[@]} -gt 0 ]]; then
	>"$LAUNCH_ENV_FILE"
	for var in "${!ENV_VARS_ARRAY[@]}"; do
		echo "$var=${ENV_VARS_ARRAY[$var]}" >>"$LAUNCH_ENV_FILE"
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
