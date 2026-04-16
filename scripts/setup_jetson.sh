#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# setup_jetson.sh
# One-time host setup for nvidia-container.sh on a Jetson (or any NVIDIA Linux).
# --------------------------------------------------------------------------------------------

set -euo pipefail

# Install nvidia-container-toolkit and configure the Docker nvidia runtime
echo "[INFO] Setting up NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |
	gpg --dearmor |
	sudo tee /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg >/dev/null
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
	sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
	sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
echo "[OK] nvidia-container-toolkit installed and configured."

# Add current user to docker group so docker runs without sudo
CURRENT_USER="${SUDO_USER:-$USER}"
if ! getent group docker >/dev/null 2>&1; then
	echo "[WARN] docker group not found - is Docker installed?"
	exit 1
fi
if id -nG "$CURRENT_USER" | grep -qw docker; then
	echo "[INFO] '$CURRENT_USER' already in docker group."
else
	sudo usermod -aG docker "$CURRENT_USER"
	echo "[OK] '$CURRENT_USER' added to docker group."
fi

sudo systemctl restart docker
echo "[OK] Docker restarted."

echo ""
echo "Setup complete. Run 'exec newgrp docker' to apply the docker group without logging out."
