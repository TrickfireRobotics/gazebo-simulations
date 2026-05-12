---
title: Docker Environment
description: How the container is configured, the multi-stage Dockerfile, standalone docker-compose usage, and how the headless display works.
---

The entire simulation environment runs inside a Docker container. There are two ways to use it:

1. **Dev Container** (VS Code) -- uses the `dev` stage of the Dockerfile with dev tooling pre-installed. This is the primary workflow for development.
2. **Standalone container** (docker-compose) -- uses the `runtime` stage for running simulations on any host without VS Code. NVIDIA GPU passthrough is enabled automatically when hardware is detected.

## Multi-stage Dockerfile

The Dockerfile at `docker/Dockerfile` has two stages:

```dockerfile
FROM ros:humble-ros-base AS runtime   # simulation + VNC/display stack
FROM runtime AS dev                   # + dev tooling (ruff, onshape-to-robot, shfmt)
```

### Runtime stage

Everything needed to run simulations:

```
ros:humble-ros-base (Ubuntu Jammy 22.04 + ROS 2 Humble)
```

**Simulation stack:**

| Package                                | Purpose                                         |
| -------------------------------------- | ----------------------------------------------- |
| Gazebo Ignition Fortress               | Physics simulation engine                       |
| `ros-humble-ros-gz-sim`                | ROS 2 / Gazebo integration                      |
| `ros-humble-ros-ign-bridge`            | Message bridging between ROS and Gazebo         |
| `ros-humble-ros2-controllers`          | Joint state broadcaster + trajectory controller |
| `ros-humble-gz-ros2-control`           | Hardware interface for Gazebo                   |
| `ros-humble-rviz2`                     | Robot visualization                             |
| `ros-humble-xacro`                     | URDF macro processing                           |
| `ros-humble-joint-state-publisher-gui` | Joint state publishing GUI                      |

**Display stack (headless GUI):**

| Package                                          | Purpose                                       |
| ------------------------------------------------ | --------------------------------------------- |
| `xserver-xorg-core` + `xserver-xorg-video-dummy` | Virtual X server with dummy driver (no GPU)   |
| `openbox`                                        | Lightweight window manager                    |
| `x11vnc`                                         | VNC server for remote X11 access              |
| `novnc` + `websockify`                           | Browser-based VNC client                      |
| `xvfb`                                           | Virtual framebuffer for Jetson/Tegra (no DRI) |
| `mesa-utils`, `libgl1-mesa-*`                    | Software OpenGL rendering                     |

**Build tools:**

| Package                            | Purpose                      |
| ---------------------------------- | ---------------------------- |
| `python3-colcon-common-extensions` | ROS 2 workspace build system |
| `python3-rosdep`                   | ROS dependency installer     |
| `git`                              | Version control              |

### Dev stage

Adds on top of runtime:

| Package            | Purpose                                 |
| ------------------ | --------------------------------------- |
| `ruff`             | Python linter                           |
| `onshape-to-robot` | CAD-to-URDF conversion (used by `sim create`) |
| `open3d`           | STL mesh decimation                     |
| `shfmt`            | Shell script formatter                  |

## Container user

The container runs as a non-root user `trickfire` with passwordless sudo:

```dockerfile
RUN useradd trickfire --shell /bin/bash --create-home
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
```

## Dev Container configuration

The `devcontainer.json` configures how VS Code opens the container:

**Build target:** `dev` stage of `docker/Dockerfile`

**Workspace mount:** The repo is bind-mounted into the container at `/home/trickfire/gazebo-simulations`.

**Compose config:** `.devcontainer/devcontainer.json` uses `docker/docker-compose.yml` plus `.devcontainer/docker-compose.devcontainer.yml`. The override only switches the build target to `dev`; the base compose file starts the X server / VNC stack automatically.

**Port forwarding:** Ports `6080` (noVNC) and `5900` (VNC) are forwarded to the host.

**Privileged mode:** The container runs with `--privileged` and device access for hardware interaction (USB, CAN bus).

**X11 forwarding:** The devcontainer relies on the Compose-managed VNC desktop. The standalone GPU compose stack can still mount `/tmp/.X11-unix` when you want host X11 rendering.

**VS Code extensions:** Pre-installs Python, C++, ROS, URDF, Docker, formatting, and docs (Astro/MDX) extensions.

## X-server Display Architecture

```
Xorg/Xvfb  →  x11vnc  →  websockify  →  Browser
    ↑                                       ↑
 Openbox WM                            noVNC client
    ↑                                   (port 6080)
 Gazebo / RViz
```

### Why this approach?

Alternatives like Xvfb don't support GLX properly, which means Gazebo's 3D rendering fails. Using Xorg with a dummy driver + Mesa software rendering gives us full OpenGL support without needing a real GPU. The VNC + noVNC layer makes it accessible from any browser. On Jetsons, we fall back to Xvfb because there's no `/dev/dri`, but GPU rendering still works via EGL through injected Tegra libs.

### Environment variables

| Variable     | Value          | Set in                            |
| ------------ | -------------- | --------------------------------- |
| `DISPLAY`    | Host-dependent | `docker-compose.yml` (standalone) |
| `VNC_PORT`   | `5900`         | Dockerfile                        |
| `NOVNC_PORT` | `6080`         | Dockerfile                        |

## Extending the container

To add system packages, edit `docker/Dockerfile` and rebuild. For Python packages, add them to the `pip3 install` section in the appropriate stage (`runtime` for things needed at simulation time, `dev` for development-only tools).

After changing the Dockerfile, use **Dev Containers: Rebuild Container** in VS Code's Command Palette.
