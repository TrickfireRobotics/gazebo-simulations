#!/usr/bin/env bash
set -eo pipefail

# --------------------------------------------------------------------------------------------
# Starts a headless X11 desktop (Xorg/Xvfb + Openbox + x11vnc + noVNC) inside the container.
# Intended for running GUI apps (Gazebo) in Docker.
# Supports --verbose flag for debugging (prints all output to console instead of log file).
# --------------------------------------------------------------------------------------------

VERBOSE=false
FORCE_VNC=${FORCE_VNC:-}
LOG_FILE="/tmp/start_x_server.log"
PIDS=()
: >"$LOG_FILE"

log() { printf "\033[1;36m%s\033[0m\n" "$1"; }

# Foreground commands: exit with log dump on failure
run() {
    if $VERBOSE; then
        "$@"
    else "$@" >>"$LOG_FILE" 2>&1 || {
        echo
        echo "[ERROR] Command failed: $*"
        echo "────────── OUTPUT START ──────────"
        cat "$LOG_FILE"
        echo "─────────── OUTPUT END ───────────"
        exit 1
    }; fi
}

# Background services: just redirect output
start() {
    if $VERBOSE; then
        "$@" &
    else "$@" >>"$LOG_FILE" 2>&1 & fi
    PIDS+=($!)
}

# Cleanup function to kill background processes on exit
cleanup() {
    trap - SIGINT SIGTERM EXIT
    log "[CLEANUP] Shutting down X11 / VNC / noVNC…"
    for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}

# --------------------------------------------------------------------------------------------

# Parse flags
for arg in "$@"; do
    case "$arg" in
    -v | --verbose) VERBOSE=true ;;
    --force-vnc) FORCE_VNC=1 ;;
    esac
done

if [ -n "$FORCE_VNC" ]; then
    # Dev/testing override: skip Wayland/host-X11 passthrough and always stand up
    # our own virtual X server + x11vnc + noVNC. Use a display number distinct from
    # the host's (rather than $DISPLAY) so we don't collide with the real host X11
    # socket bind-mounted into /tmp/.X11-unix by docker-compose-dev.yml.
    DISPLAY="${FORCE_VNC_DISPLAY:-:77}"
    log "[X11] FORCE_VNC set - forcing virtual display $DISPLAY + VNC/noVNC"
else
    # wayland is the best for this, just use that if the host has it
    WAYLAND_SOCK="/run/host-runtime/${WAYLAND_DISPLAY:-wayland-0}"
    if [ -S "$WAYLAND_SOCK" ]; then
        log "[X11] Using Wayland socket at $WAYLAND_SOCK"
        exit 0
    fi
fi

# Jetson/Tegra has no /dev/dri but Xorg drivers (nvidia, modesetting, dummy) all need it.
# Use Xvfb on Jetson; GPU rendering still happens via EGL through the injected Tegra libs.
# Desktop NVIDIA has /proc/driver/nvidia; everything else gets the dummy Xorg driver.
if [ -e /dev/nvmap ] && [ ! -d /dev/dri ]; then
    BACKEND="xvfb"
    XORG_CONF="/etc/X11/xorg.nvidia.conf"
    log "[X11] Jetson/Tegra detected (no DRI), using Xvfb + EGL"
elif [ -e /proc/driver/nvidia ] || nvidia-smi &>/dev/null; then
    BACKEND="xorg"
    XORG_CONF="/etc/X11/xorg.nvidia.conf"
    log "[X11] Desktop NVIDIA GPU detected, using Xorg nvidia driver"
else
    BACKEND="xorg"
    log "[X11] No GPU detected - trying vkms for DRI3-capable headless display"
    sudo modprobe vkms 2>/dev/null || true
    VKMS_CARD=""
    for card in /dev/dri/card*; do
        drv=$(readlink -f "/sys/class/drm/$(basename "$card")/device/driver" 2>/dev/null) || continue
        [[ $drv == *vkms* ]] && {
            VKMS_CARD="$card"
            break
        }
    done
    if [ -n "$VKMS_CARD" ]; then
        log "[X11] Using vkms virtual display ($VKMS_CARD)"
        XORG_CONF=$(mktemp /tmp/xorg-vkms.XXXXXX.conf)
        cat >"$XORG_CONF" <<XCONF
Section "Module"
  Load "glx"
EndSection
Section "Device"
  Identifier "VKMSDevice"
  Driver "modesetting"
  Option "kmsdev" "$VKMS_CARD"
  Option "DRI" "3"
EndSection
Section "Monitor"
  Identifier "DummyMonitor"
  HorizSync 28-80
  VertRefresh 48-75
EndSection
Section "Screen"
  Identifier "DummyScreen"
  Device "VKMSDevice"
  Monitor "DummyMonitor"
  DefaultDepth 24
  SubSection "Display"
    Depth 24
    Modes "1920x1080"
  EndSubSection
EndSection
Section "ServerLayout"
  Identifier "DummyLayout"
  Screen "DummyScreen"
EndSection
XCONF
    else
        log "[X11] vkms unavailable, falling back to dummy driver (no DRI3)"
        XORG_CONF="/etc/X11/xorg.dummy.conf"
    fi
fi

# Parse screen resolution from Xorg config (in docker/xorg.dummy|nvidia.conf)
SCREEN_MODE=$(grep -oP '(?<=Modes ")[^"]+' "$XORG_CONF" | head -1)
SCREEN_WIDTH=$(echo "$SCREEN_MODE" | cut -dx -f1)
SCREEN_HEIGHT=$(echo "$SCREEN_MODE" | cut -dx -f2)
SCREEN_DEPTH=$(grep -oP '(?<=DefaultDepth )\d+' "$XORG_CONF" | head -1)
if [ -z "$SCREEN_WIDTH" ] || [ -z "$SCREEN_HEIGHT" ] || [ -z "$SCREEN_DEPTH" ]; then
    echo "[ERROR] Could not parse resolution from $XORG_CONF"
    exit 1
fi

# Set in the Dockerfile and docker compose.
: "${DISPLAY:?DISPLAY is not set}"
: "${VNC_PORT:?VNC_PORT is not set}"
: "${NOVNC_PORT:?NOVNC_PORT is not set}"

# Check if DISPLAY is already in use
if xdpyinfo -display "$DISPLAY" &>/dev/null; then
    log "[ERROR] Display $DISPLAY is already in use!"
    exit 1
fi

# Kill all child processes on exit
trap cleanup SIGINT SIGTERM

# Start X server (Xorg or Xvfb determined above)
if [ "$BACKEND" = "xvfb" ]; then
    log "[X11] Starting Xvfb on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
    start Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
else
    log "[X11] Starting Xorg on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
    start sudo Xorg "$DISPLAY" -noreset -config "$XORG_CONF"
fi
sleep 1
stty sane 2>/dev/null || true # Xorg alters terminal CR/LF settings

# Start window manager
log "[WM] Starting Openbox window manager"
start openbox-session

# Start x11vnc server for VNC connection
log "[VNC] Starting x11vnc on port ${VNC_PORT}"
start x11vnc -display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -nopw -xkb

# Start noVNC web client to serve the VNC desktop in a browser
log "[noVNC] Starting browser-based desktop on port ${NOVNC_PORT}"
start /usr/share/novnc/utils/novnc_proxy --vnc "localhost:${VNC_PORT}" --listen "${NOVNC_PORT}"
log "[noVNC] Desktop available at: http://localhost:${NOVNC_PORT}/vnc.html"

# Detach all background services so they survive this script exiting
disown "${PIDS[@]}" || true
log "[MAIN] All services started"
