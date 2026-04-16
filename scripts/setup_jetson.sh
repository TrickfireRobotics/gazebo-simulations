#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# setup_jetson.sh
# --------------------------------------------------------------------------------------------
# One-time host setup for running the Gazebo sim container on a Jetson (or any NVIDIA Linux).
#
# Does:
#   1. Installs nvidia-container-toolkit
#   2. Configures the nvidia Docker runtime
#   3. Installs podman + distrobox
#   4. Generates a CDI spec for Podman/Distrobox NVIDIA passthrough
#   5. Installs Xvfb + x11vnc (for start_sim_display.sh)
#   6. Adds the current user to the docker group (no-sudo docker)
#   7. Restarts Docker
#
# Usage:
#   ./scripts/setup_jetson.sh
#
# IMPORTANT:
#   - Run from the HOST (not inside a container)
#   - Requires sudo
# --------------------------------------------------------------------------------------------

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info() { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
success() { printf "${GREEN}[OK]${RESET}    %s\n" "$*"; }
warn() { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }

printf "\n${BOLD}${CYAN}Jetson Docker Setup${RESET}\n\n"

# --------------------------------------------------------------------------------------------
# NVIDIA Container Toolkit
# --------------------------------------------------------------------------------------------

info "Setting up NVIDIA Container Toolkit apt repository..."

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |
	gpg --dearmor |
	sudo tee /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg >/dev/null

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
	sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
	sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

info "Installing nvidia-container-toolkit..."
sudo apt-get update -qq
sudo apt-get install -y nvidia-container-toolkit
success "nvidia-container-toolkit installed."

# --------------------------------------------------------------------------------------------
# Configure nvidia runtime with Docker
# --------------------------------------------------------------------------------------------

info "Configuring nvidia runtime for Docker..."
sudo nvidia-ctk runtime configure --runtime=docker
success "nvidia runtime configured for Docker."

# --------------------------------------------------------------------------------------------
# Install Podman + Distrobox
# --------------------------------------------------------------------------------------------

# podman is not in Ubuntu 20.04 default repos — use the Kubic OBS repository.
info "Adding Kubic OBS repository for podman..."
UBUNTU_VERSION_ID=$(lsb_release -rs)
curl -fsSL "https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${UBUNTU_VERSION_ID}/Release.key" |
	gpg --dearmor |
	sudo tee /usr/share/keyrings/libcontainers-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/libcontainers-keyring.gpg] https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${UBUNTU_VERSION_ID}/ /" |
	sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y podman
success "podman installed."

# distrobox requires Ubuntu 22.10+ in the standard apt repos — use the official install script.
info "Installing distrobox via install script..."
curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sudo sh
success "distrobox installed."

# --------------------------------------------------------------------------------------------
# Configure nvidia for Podman via CDI
# --------------------------------------------------------------------------------------------
# nvidia-ctk does not support --runtime=podman directly. Instead, generate a CDI spec,
# which lets Podman (and distrobox's --nvidia flag) discover and use the GPU.

info "Generating CDI spec for Podman/Distrobox NVIDIA passthrough..."
sudo mkdir -p /etc/cdi
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
success "CDI spec written to /etc/cdi/nvidia.yaml."

# --------------------------------------------------------------------------------------------
# Install VNC / virtual display tools (for start_sim_display.sh)
# --------------------------------------------------------------------------------------------

info "Installing Xvfb and x11vnc..."
sudo apt-get install -y xvfb x11vnc
success "Xvfb and x11vnc installed."

# --------------------------------------------------------------------------------------------
# Add current user to docker group
# --------------------------------------------------------------------------------------------

CURRENT_USER="${SUDO_USER:-$USER}"
ADDED_TO_DOCKER=false

if getent group docker >/dev/null 2>&1; then
	if id -nG "$CURRENT_USER" | grep -qw docker; then
		warn "User '$CURRENT_USER' is already in the docker group."
	else
		info "Adding '$CURRENT_USER' to the docker group..."
		sudo usermod -aG docker "$CURRENT_USER"
		success "User '$CURRENT_USER' added to the docker group."
		ADDED_TO_DOCKER=true
	fi
else
	warn "docker group does not exist — is Docker installed? Skipping group setup."
fi

# --------------------------------------------------------------------------------------------
# Restart
# --------------------------------------------------------------------------------------------

info "Restarting Docker daemon..."
sudo systemctl restart docker
success "Docker restarted."

printf "\n${GREEN}${BOLD}Setup complete.${RESET}\n\n"

# Apply docker group to the current shell without requiring logout.
# exec replaces this process with a new shell that has the docker group active.
if [[ "$ADDED_TO_DOCKER" == true ]]; then
	info "Please run 'exec newgrp docker' to apply the docker group to your current shell session"
fi
