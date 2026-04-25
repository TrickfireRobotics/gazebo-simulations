#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------
# setup_jetson.sh
# One-time host setup for start-container.sh on a Jetson (or any NVIDIA Linux).
# --------------------------------------------------------------------------------------------

set -euo pipefail

# --------------------------------------------------------------------------------------------
# Install and configure NVIDIA Container Toolkit for Docker.
# This enables GPU passthrough inside containers so ROS/Gazebo workloads can access
# Jetson/NVIDIA hardware acceleration instead of running CPU-only.
# --------------------------------------------------------------------------------------------
echo "[INFO] Setting up NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |
	gpg --dearmor |
	sudo tee /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg >/dev/null
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
	sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
	sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -f -y
sudo apt-get install -y -o Dpkg::Options::="--force-overwrite" nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
echo "[OK] nvidia-container-toolkit installed and configured."

# --------------------------------------------------------------------------------------------
# Ensure the invoking user can run Docker without `sudo`.
# This grants membership in the `docker` group to avoid permission errors during
# normal simulation workflows and Dev Container commands.
# --------------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------------
# Set power mode and performance configuration
# Configures the Jetson for maximum performance:
# - Power mode set to MAXN
# - All CPU cores online
# - GPU running at max frequency
# - Fan set to full cooling profile
# - WiFi power management disabled
# --------------------------------------------------------------------------------------------
echo "[INFO] Configuring Jetson for maximum performance..."

# Set power mode to MAXN (maximum performance)
if command -v nvpmodel &>/dev/null; then
	sudo nvpmodel -m 0
	echo "[OK] Power mode set to MAXN."
else
	echo "[WARN] nvpmodel not found - power mode not configured."
fi

# Enable jetson-clocks service to keep clocks at max and all CPUs online.
# Creates the unit file if not already present (not shipped by all JetPack versions).
JETSON_CLOCKS_SVC=/etc/systemd/system/jetson-clocks.service
if [[ ! -f "$JETSON_CLOCKS_SVC" ]]; then
	sudo tee "$JETSON_CLOCKS_SVC" >/dev/null <<'EOF'
[Unit]
Description=Lock Jetson CPU/GPU/EMC clocks to maximum
After=nvpmodel.service
Wants=nvpmodel.service

[Service]
Type=oneshot
ExecStart=/usr/bin/jetson_clocks
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
	echo "[OK] jetson-clocks.service unit created."
fi
sudo systemctl daemon-reload
sudo systemctl enable --now jetson-clocks.service
echo "[OK] jetson-clocks.service enabled and active."

# Create and enable wifi-disable-powersave service
WIFI_SERVICE_FILE="/etc/systemd/system/wifi-disable-powersave.service"
if [[ ! -f "$WIFI_SERVICE_FILE" ]]; then
	sudo tee "$WIFI_SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=Disable WiFi Power Management
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/iwconfig wlan0 power off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
	echo "[OK] wifi-disable-powersave.service created."
fi
sudo systemctl enable --now wifi-disable-powersave.service 2>/dev/null || echo "[WARN] wifi-disable-powersave.service enable failed (may not have WiFi)."

# Set fan to full speed and persist across reboots.
# nvfancontrol.service (shipped with JetPack) starts after multi-user.target and overwrites
# any sysfs writes made before it, so we disable it and run our service after it to win the
# ordering race on any JetPack version where it can't be fully disabled.
sudo systemctl disable --now nvfancontrol.service 2>/dev/null || true

sudo tee /etc/systemd/system/fan-full-speed.service >/dev/null <<'EOF'
[Unit]
Description=Set fan to full speed
# Run after nvfancontrol in case it starts anyway (e.g. triggered as a dependency)
After=multi-user.target nvfancontrol.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c '\
    echo full > /sys/devices/platform/thermal_fan_est/fan_profile 2>/dev/null || true; \
    for f in /sys/class/hwmon/hwmon*/pwm1; do echo 255 > "$f" 2>/dev/null || true; done'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now fan-full-speed.service
echo "[OK] Fan set to full speed."

echo "[OK] Performance configuration complete."

# --------------------------------------------------------------------------------------------
# Other miscellaneous setup:
#  - Wallpaper from docs/assets/trickfire-wallpaper.png
# --------------------------------------------------------------------------------------------

# Copy wallpaper to a stable system path, then apply it for the invoking user via gsettings.
# gsettings must run as the user (not root) with access to the session D-Bus.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WALLPAPER_SRC="$SCRIPT_DIR/../docs/assets/trickfire-wallpaper.png"
WALLPAPER_DEST="/usr/share/backgrounds/trickfire-wallpaper.png"

USER_ID=$(id -u "$CURRENT_USER")
USER_HOME=$(getent passwd "$CURRENT_USER" | cut -d: -f6)

# Helper: run a command as the invoking user with access to the session D-Bus.
run_as_user() {
	sudo -u "$CURRENT_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${USER_ID}/bus" "$@"
}

if [[ -f "$WALLPAPER_SRC" ]]; then
	sudo cp "$WALLPAPER_SRC" "$WALLPAPER_DEST"
	run_as_user gsettings set org.gnome.desktop.background picture-uri "file://${WALLPAPER_DEST}"
	run_as_user gsettings set org.gnome.desktop.background picture-uri-dark "file://${WALLPAPER_DEST}" 2>/dev/null || true
	echo "[OK] Wallpaper set."
else
	echo "[WARN] Wallpaper not found at $WALLPAPER_SRC — skipping."
fi

# --------------------------------------------------------------------------------------------
# GNOME desktop configuration
# --------------------------------------------------------------------------------------------
echo "[INFO] Configuring GNOME desktop..."

# Dark mode
run_as_user gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true

# Hide desktop icons — disable the ding extension and zero out all its show-* keys so
# the setting survives if the extension is re-enabled later.
run_as_user gnome-extensions disable ding@rastersoft.com 2>/dev/null || true
run_as_user gsettings set org.gnome.shell.extensions.ding show-home false 2>/dev/null || true
run_as_user gsettings set org.gnome.shell.extensions.ding show-trash false 2>/dev/null || true
run_as_user gsettings set org.gnome.shell.extensions.ding show-volumes false 2>/dev/null || true
run_as_user gsettings set org.gnome.shell.extensions.ding show-network-volumes false 2>/dev/null || true
echo "[OK] Desktop icons hidden."

# --------------------------------------------------------------------------------------------
# Install kitty terminal and apply Dracula colour scheme
# --------------------------------------------------------------------------------------------
echo "[INFO] Installing kitty terminal..."
sudo apt-get install -y kitty

sudo -u "$CURRENT_USER" mkdir -p "$USER_HOME/.config/kitty"
sudo -u "$CURRENT_USER" tee "$USER_HOME/.config/kitty/kitty.conf" >/dev/null <<'EOF'
# --- TrickFire colour scheme ---
background            #161616
foreground            #cccccc
selection_background  #242424
selection_foreground  #cccccc
url_color             #00fe00
cursor                #00fe00
cursor_text_color     #161616

# black
color0   #222222
color8   #444444
# red (pink accent)
color1   #e93cac
color9   #ff79d0
# green (brand green)
color2   #00fe00
color10  #99ee99
# yellow
color3   #e0c060
color11  #f0d080
# blue
color4   #4488cc
color12  #66aaee
# magenta (pink accent)
color5   #e93cac
color13  #ff79d0
# cyan
color6   #00ccaa
color14  #00eebb
# white
color7   #cccccc
color15  #ffffff

# --- Font ---
font_size 11.0
EOF

sudo update-alternatives --install /usr/bin/x-terminal-emulator x-terminal-emulator /usr/bin/kitty 50
sudo update-alternatives --set x-terminal-emulator /usr/bin/kitty
echo "[OK] kitty installed and set as default terminal."

# --------------------------------------------------------------------------------------------
echo ""
echo "Setup complete. Rebooting..."
sudo reboot
