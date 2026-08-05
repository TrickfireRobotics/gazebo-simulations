#!/usr/bin/env bash

# --------------------------------------------------------------------------------------------
# Starts a headless X11 desktop (Xorg/Xvfb + Openbox + x11vnc + noVNC) inside the container.
# Intended for running GUI apps (Gazebo) in Docker.
# Supports --verbose flag for debugging (prints all output to console instead of log file).
# --------------------------------------------------------------------------------------------

set -eo pipefail
trap '' HUP

VERBOSE=false
FORCE_VNC=${FORCE_VNC:-}
LOG_FILE="/tmp/start_x_server.log"
PIDS=()
: >"$LOG_FILE"

log() { printf "\033[1;36m%s\033[0m\n" "$1"; }

run() {
    if $VERBOSE; then
        "$@"
    else
        "$@" >>"$LOG_FILE" 2>&1 || {
            echo
            echo "[ERROR] Command failed: $*"
            echo "────────── OUTPUT START ──────────"
            cat "$LOG_FILE"
            echo "─────────── OUTPUT END ───────────"
            exit 1
        }
    fi
}

start() {
    if $VERBOSE; then
        "$@" &
    else
        "$@" >>"$LOG_FILE" 2>&1 &
    fi
    PIDS+=($!)
}

cleanup() {
    trap - SIGINT SIGTERM EXIT
    log "[CLEANUP] Shutting down X11 / VNC / noVNC…"
    for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}

parse_args() {
    for arg in "$@"; do
        case "$arg" in
        -v | --verbose) VERBOSE=true ;;
        --force-vnc) FORCE_VNC=1 ;;
        esac
    done
}

# VirtualGL's "3D X server": a container-local headless X server that GL rendering actually
# happens against. Only needed when $DISPLAY is a remote X server (macOS/XQuartz,
# Windows/VcXsrv), which can display windows but can't provide a usable OpenGL context - its
# indirect GLX is deprecated and broken, so OGRE2 apps (Gazebo, RViz) fail to create a
# renderer. VirtualGL renders here instead (Mesa llvmpipe, OpenGL 4.5) and sends only the
# finished frames to the host's X server as plain X11 images.
#
# Skipped for local passthrough (native Linux, WSLg): there the app's GL already works
# directly against the host's GPU, and routing through VirtualGL would only cost performance.
start_vgl_3d_server() {
    if [[ $DISPLAY == :* ]]; then
        return 0
    fi

    if ! command -v vglrun >/dev/null 2>&1; then
        log "[VGL] vglrun not found - skipping (Gazebo/RViz will not be able to render)"
        return 0
    fi

    local vgl_display="${VGL_DISPLAY:-:88}"
    if xdpyinfo -display "$vgl_display" &>/dev/null; then
        log "[VGL] 3D X server already running on $vgl_display"
        return 0
    fi

    log "[VGL] Starting VirtualGL 3D X server (Xvfb) on $vgl_display"
    Xvfb "$vgl_display" -screen 0 2560x1440x24 >>"$LOG_FILE" 2>&1 &
    local vgl_pid=$!
    disown "$vgl_pid" 2>/dev/null || true

    # Xvfb takes a moment to start listening; without this the first `sim gazebo` after a
    # container start could race it and silently fall back to unaccelerated rendering.
    local i
    for i in $(seq 1 20); do
        if xdpyinfo -display "$vgl_display" &>/dev/null; then
            log "[VGL] 3D X server ready on $vgl_display"
            return 0
        fi
        sleep 0.25
    done

    log "[VGL] WARNING: 3D X server on $vgl_display did not come up - see $LOG_FILE"
}

try_display_passthrough() {
    if [ -n "$FORCE_VNC" ]; then
        DISPLAY="${FORCE_VNC_DISPLAY:-:77}"
        unset WAYLAND_DISPLAY
        log "[X11] FORCE_VNC set. Forcing virtual display $DISPLAY + VNC/noVNC"
        return
    fi

    # Case 1: Linux host with a Wayland compositor, or WSL2 with WSLg. The host socket is
    # bind-mounted into /run/host-runtime by docker-compose-dev.yml.
    local wayland_sock="/run/host-runtime/${WAYLAND_DISPLAY:-wayland-0}"
    if [ -S "$wayland_sock" ]; then
        log "[X11] Using Wayland socket at $wayland_sock"
        exit 0
    fi

    # Case 2: a real X11 display is already reachable at $DISPLAY. This covers:
    #   - native Linux X11 (host's /tmp/.X11-unix bind-mounted, DISPLAY inherited from the host)
    #   - WSL2 with WSLg's X11 socket
    #   - macOS + XQuartz reachable over TCP at host.docker.internal:0
    #   - Windows + VcXsrv/X410 reachable over TCP at host.docker.internal:0
    #     (both set by .devcontainer/detect-host-env.sh -> docker/.env.host)
    if [ -n "$DISPLAY" ] && xdpyinfo -display "$DISPLAY" &>/dev/null; then
        log "[X11] Using host X11 display at $DISPLAY"
        start_vgl_3d_server
        exit 0
    fi
}

detect_backend() {
    if [ -n "$FORCE_VNC" ]; then
        BACKEND="xvfb"
        XORG_CONF="/etc/X11/xorg.dummy.conf"
        log "[X11] FORCE_VNC: using Xvfb unconditionally (no direct GPU access)"
    elif [ -e /dev/nvmap ] && [ ! -d /dev/dri ]; then
        BACKEND="xvfb"
        XORG_CONF="/etc/X11/xorg.nvidia.conf"
        log "[X11] Jetson/Tegra detected (no DRI), using Xvfb + EGL"
    elif [ -e /proc/driver/nvidia ] || nvidia-smi &>/dev/null; then
        BACKEND="xorg"
        XORG_CONF="/etc/X11/xorg.nvidia.conf"
        log "[X11] Desktop NVIDIA GPU detected, using Xorg nvidia driver"
    else
        detect_vkms_backend
    fi
}

detect_vkms_backend() {
    BACKEND="xorg"
    log "[X11] No GPU detected - trying vkms for DRI3-capable headless display"
    sudo modprobe vkms 2>/dev/null || true

    local card drv dev_path
    VKMS_CARD=""
    for card in /dev/dri/card*; do
        drv=$(readlink -f "/sys/class/drm/$(basename "$card")/device/driver" 2>/dev/null)
        dev_path=$(readlink -f "/sys/class/drm/$(basename "$card")/device" 2>/dev/null)
        [[ $drv == *vkms* || $dev_path == *vkms* ]] && {
            VKMS_CARD="$card"
            break
        }
    done

    if [ -z "$VKMS_CARD" ]; then
        log "[X11] vkms unavailable, falling back to Xvfb (no real GPU access, no DRI3)"
        BACKEND="xvfb"
        XORG_CONF="/etc/X11/xorg.dummy.conf"
        return
    fi

    log "[X11] Using vkms virtual display ($VKMS_CARD)"
    XORG_CONF=$(mktemp /tmp/xorg-vkms.XXXXXX.conf)
    sed "s|__VKMS_CARD__|$VKMS_CARD|" /etc/X11/xorg.vkms.conf >"$XORG_CONF"
}

parse_screen_resolution() {
    SCREEN_MODE=$(grep -oP '(?<=Modes ")[^"]+' "$XORG_CONF" | head -1)
    SCREEN_WIDTH=$(echo "$SCREEN_MODE" | cut -dx -f1)
    SCREEN_HEIGHT=$(echo "$SCREEN_MODE" | cut -dx -f2)
    SCREEN_DEPTH=$(grep -oP '(?<=DefaultDepth )\d+' "$XORG_CONF" | head -1)
    if [ -z "$SCREEN_WIDTH" ] || [ -z "$SCREEN_HEIGHT" ] || [ -z "$SCREEN_DEPTH" ]; then
        echo "[ERROR] Could not parse resolution from $XORG_CONF"
        exit 1
    fi
}

start_services() {
    trap cleanup SIGINT SIGTERM

    if [ "$BACKEND" = "xvfb" ]; then
        log "[X11] Starting Xvfb on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
        start Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}"
    else
        log "[X11] Starting Xorg on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
        start sudo Xorg "$DISPLAY" -noreset -config "$XORG_CONF"
    fi
    sleep 1
    stty sane 2>/dev/null || true

    log "[WM] Starting Openbox window manager"
    start openbox-session

    log "[VNC] Starting x11vnc on port ${VNC_PORT}"
    start x11vnc -display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -nopw -xkb

    log "[noVNC] Starting browser-based desktop on port ${NOVNC_PORT}"
    start /usr/share/novnc/utils/novnc_proxy --vnc "localhost:${VNC_PORT}" --listen "${NOVNC_PORT}"
    log "[noVNC] Desktop available at: http://localhost:${NOVNC_PORT}/vnc.html"

    disown "${PIDS[@]}" || true
    log "[MAIN] All services started"
}

main() {
    parse_args "$@"
    try_display_passthrough

    # try_display_passthrough only returns (rather than exiting) when no host display was
    # usable, so it's safe to claim $DISPLAY for our own Xvfb/Xorg below - we just confirmed
    # nothing answers on it. However $DISPLAY may hold a remote/TCP spec like
    # "host.docker.internal:0" (macOS/Windows hosts, when XQuartz/VcXsrv wasn't reachable) -
    # that's not a valid local display for Xvfb/Xorg to bind to, so normalize it to a plain
    # local display number first. Valid local specs always start with ':'.
    if [[ $DISPLAY != :* ]]; then
        log "[X11] $DISPLAY unreachable; falling back to internal Xvfb/Xorg on :0"
        DISPLAY=":0"
    fi

    detect_backend
    parse_screen_resolution

    : "${DISPLAY:?DISPLAY is not set}"
    : "${VNC_PORT:?VNC_PORT is not set}"
    : "${NOVNC_PORT:?NOVNC_PORT is not set}"

    start_services
}

main "$@"
