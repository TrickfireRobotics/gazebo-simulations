---
title: Docker Environment
description: How the container is configured, the multi-stage Dockerfile, standalone docker-compose usage, and how the headless display works.
---

The entire simulation environment runs inside a Docker container. There are two ways to use it:

1. **Dev Container** (VS Code) -- uses the `dev` stage of the Dockerfile with dev tooling pre-installed. This is the primary workflow for development.
2. **Standalone container** (docker-compose) -- uses the `runtime` stage for running simulations on headless NVIDIA hosts (Jetsons, etc.) without VS Code.

## Multi-stage Dockerfile

The Dockerfile at `docker/Dockerfile` has two stages:

```dockerfile
FROM ros:humble-ros-base AS runtime   # simulation + VNC/display stack
FROM runtime AS dev                   # + dev tooling (ruff, genbot, shfmt)
```

### Runtime stage

Everything needed to run simulations:

```
ros:humble-ros-base (Ubuntu Jammy 22.04 + ROS 2 Humble)
```

**Simulation stack:**

| Package | Purpose |
| --- | --- |
| Gazebo Ignition Fortress | Physics simulation engine |
| `ros-humble-ros-gz-sim` | ROS 2 / Gazebo integration |
| `ros-humble-ros-ign-bridge` | Message bridging between ROS and Gazebo |
| `ros-humble-ros2-controllers` | Joint state broadcaster + trajectory controller |
| `ros-humble-gz-ros2-control` | Hardware interface for Gazebo |
| `ros-humble-rviz2` | Robot visualization |
| `ros-humble-xacro` | URDF macro processing |
| `ros-humble-joint-state-publisher-gui` | Joint state publishing GUI |

**Display stack (headless GUI):**

| Package | Purpose |
| --- | --- |
| `xserver-xorg-core` + `xserver-xorg-video-dummy` | Virtual X server with dummy driver (no GPU) |
| `openbox` | Lightweight window manager |
| `x11vnc` | VNC server for remote X11 access |
| `novnc` + `websockify` | Browser-based VNC client |
| `xvfb` | Virtual framebuffer for Jetson/Tegra (no DRI) |
| `mesa-utils`, `libgl1-mesa-*` | Software OpenGL rendering |

**Build tools:**

| Package | Purpose |
| --- | --- |
| `python3-colcon-common-extensions` | ROS 2 workspace build system |
| `python3-rosdep` | ROS dependency installer |
| `git` | Version control |

### Dev stage

Adds on top of runtime:

| Package | Purpose |
| --- | --- |
| `ruff` | Python linter |
| `onshape-to-robot` | CAD-to-URDF conversion (used by genbot) |
| `open3d` | STL mesh decimation |
| `shfmt` | Shell script formatter |

## Container user

The container runs as a non-root user `trickfire` with passwordless sudo:

```dockerfile
RUN useradd trickfire --shell /bin/bash --create-home
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
```

## Shell system

The container sets up a custom shell environment from files in `docker/shell/`:

| File | Purpose |
| --- | --- |
| `trickfire.bashrc` | Main `.bashrc` -- history, color, completion, sources ROS and prompt |
| `prompt.sh` | Unified PS1 prompt with color-coded labels based on `$PROMPT_ENV` |
| `sim.aliases.sh` | Project aliases (`rtl`, `rte`, `genbot`, etc.) |
| `ssh.bashrc.sh` | RC file for SSH sessions on remote hosts |

### Prompt labels

The `$PROMPT_ENV` variable controls the prompt label and color:

| Value | Color | Context |
| --- | --- | --- |
| `local-dev` | Blue | Devcontainer on local machine |
| `<name>-host` | Orange | SSH shell on a remote host |
| `<name>-dev` | Green | Devcontainer on a remote host |
| `<name>-sim` | Magenta | Standalone gazebo-sim container |

## Dev Container configuration

The `devcontainer.json` configures how VS Code opens the container:

**Build target:** `dev` stage of `docker/Dockerfile`

**Workspace mount:** The repo is bind-mounted into the container at `/home/trickfire/gazebo-simulations`.

**Initialize command:** `.devcontainer/launch.sh` runs on the host before the container starts. It detects the host OS (Linux/macOS/WSL) and writes the correct `DISPLAY` and `PROMPT_ENV` values to `.devcontainer/launch.env`, which is passed to the container via `--env-file`.

**Port forwarding:** Ports `6080` (noVNC) and `5900` (VNC) are forwarded to the host.

**Privileged mode:** The container runs with `--privileged` and device access for hardware interaction (USB, CAN bus).

**Post-create command:** `scripts/ros-clean.sh` runs automatically to clear stale build artifacts.

**X11 forwarding:** On Linux, `/tmp/.X11-unix` is mounted into the container so the host's X server can be used directly.

**VS Code extensions:** Pre-installs Python, C++, ROS, URDF, Docker, formatting, and docs (Astro/MDX) extensions.

## Standalone container (docker-compose)

For running simulations on headless NVIDIA hosts without VS Code, use `docker-compose.yml`:

```bash title="Host terminal"
./scripts/nvidia-container.sh
```

This script auto-detects NVIDIA hardware and drivers:

- **NVIDIA GPU detected:** Uses both `docker-compose.yml` and `docker-compose-local.yml`. Mounts the host X11 socket and renders directly to the host display.
- **No NVIDIA GPU:** Uses `docker-compose.yml` only. Starts the VNC/noVNC headless display (accessible at `localhost:6080`).

The compose files live in `docker/`:

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base config: builds `runtime` target, NVIDIA runtime, VNC ports, auto-starts X server |
| `docker-compose-local.yml` | Override for local GPU: mounts X11 socket, keeps container alive for shell attach |

### First-time Jetson setup

Before running `nvidia-container.sh` on a new Jetson, run the one-time setup:

```bash title="Host terminal"
./scripts/setup_jetson.sh
```

This installs the NVIDIA Container Toolkit, configures the Docker nvidia runtime, and adds your user to the docker group.

## Headless display system

Since Docker containers have no monitor, we use a virtual X11 server so Gazebo and RViz can render.

### GPU auto-detection

The `start_x_server.sh` script automatically selects the best X11 backend:

| Condition | Backend | Config |
| --- | --- | --- |
| Jetson/Tegra (no `/dev/dri`) | Xvfb | `xorg.nvidia.conf` |
| Desktop NVIDIA GPU | Xorg with nvidia driver | `xorg.nvidia.conf` |
| No GPU (default) | Xorg with dummy driver | `xorg.dummy.conf` |

### Architecture

```
Xorg/Xvfb  →  x11vnc  →  websockify  →  Browser
    ↑                                       ↑
 Openbox WM                            noVNC client
    ↑                                   (port 6080)
 Gazebo / RViz
```

### Xorg configs

Two configs live in `docker/` and are copied to `/etc/X11/` during the build:

**`xorg.dummy.conf`** -- for environments with no GPU. Uses the `dummy` driver with a virtual 512 MB VRAM device.

**`xorg.nvidia.conf`** -- for NVIDIA GPUs (desktop and Jetson). Uses the `nvidia` driver with `AllowEmptyInitialConfiguration` for headless operation.

Both set 1920x1080 resolution at 24-bit color depth.

### Environment variables

| Variable | Value | Set in |
| --- | --- | --- |
| `DISPLAY` | Host-dependent | `launch.sh` (devcontainer) or `docker-compose.yml` (standalone) |
| `VNC_PORT` | `5900` | Dockerfile |
| `NOVNC_PORT` | `6080` | Dockerfile |

### Why this approach?

Alternatives like Xvfb don't support GLX properly, which means Gazebo's 3D rendering fails. Using Xorg with a dummy driver + Mesa software rendering gives us full OpenGL support without needing a real GPU. The VNC + noVNC layer makes it accessible from any browser. On Jetsons, we fall back to Xvfb because there's no `/dev/dri`, but GPU rendering still works via EGL through injected Tegra libs.

## Extending the container

To add system packages, edit `docker/Dockerfile` and rebuild. For Python packages, add them to the `pip3 install` section in the appropriate stage (`runtime` for things needed at simulation time, `dev` for development-only tools).

After changing the Dockerfile:
- **Dev Container:** Use **Dev Containers: Rebuild Container** in VS Code's Command Palette
- **Standalone:** Run `./scripts/nvidia-container.sh` again (it rebuilds automatically with `--build`)
