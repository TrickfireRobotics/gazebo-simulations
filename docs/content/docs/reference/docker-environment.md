---
title: Docker Environment
description: The multi-stage Dockerfile, display stack, and Dev Container configuration.
---

The Docker image is used by both `sim docker` and the VS Code Dev Container. It is defined in `docker/Dockerfile`.

## Multi-stage Dockerfile

```
runtime  →  ROS 2 Humble + Genesis + VNC display stack
dev      →  runtime + ruff + shfmt  (Dev Container target)
```

### Runtime stage

Base: `ros:humble-ros-base` (Ubuntu 22.04 + ROS 2 Humble core)

**Simulation stack:**

| Package                            | Purpose                                          |
| ---------------------------------- | ------------------------------------------------ |
| `genesis-world` (pip)              | Genesis physics engine                           |
| `ros-humble-robot-state-publisher` | TF tree from URDF                                |
| `ros-humble-xacro`                 | URDF macro processing                            |
| `ros-humble-rosbridge-suite`       | WebSocket bridge for Mission Control             |
| `ros-humble-ros2-controllers`      | Joint state broadcaster (kept for compatibility) |
| `ros-humble-rviz2`                 | Robot visualization                              |
| `python3-colcon-common-extensions` | ROS 2 workspace build system                     |
| `python3-tk`                       | Tkinter for the Joint GUI                        |

**Display stack (headless GUI over VNC):**

| Package                                          | Purpose                              |
| ------------------------------------------------ | ------------------------------------ |
| `xserver-xorg-core` + `xserver-xorg-video-dummy` | Virtual X server with dummy driver   |
| `openbox`                                        | Lightweight window manager           |
| `x11vnc`                                         | VNC server for remote X11 access     |
| `novnc` + `websockify`                           | Browser-based VNC client (port 6080) |
| `xvfb`                                           | Virtual framebuffer fallback         |
| `mesa-utils`, `libgl1-mesa-*`                    | Software OpenGL rendering            |

### Dev stage

Adds on top of runtime:

| Package | Purpose                   |
| ------- | ------------------------- |
| `ruff`  | Python linter / formatter |
| `shfmt` | Shell script formatter    |

## Display architecture

```
Xorg (dummy driver)
    ↑
 Openbox WM
    ↑
 Genesis viewer / RViz
    ↓
 x11vnc  →  websockify  →  Browser (noVNC, port 6080)
                        →  VNC viewer (port 5900)
```

Xorg with a dummy driver plus Mesa software rendering gives full OpenGL support without a physical GPU. The VNC + noVNC layer makes the desktop accessible from any browser or VNC client.

The display stack starts automatically via `postStartCommand` in `devcontainer.json`. Restart manually inside the container if needed:

```bash title="Inside devcontainer"
./.devcontainer/x_server.sh
```

## Container user

The container runs as `trickfire` with passwordless sudo. The repo is bind-mounted at `/home/trickfire/genesis-simulations` (the directory exists in the image so Docker Engine 27.3+ doesn't reject it as the working directory).

## Dev Container configuration

`devcontainer.json` configures the VS Code Dev Container:

- **Build target:** `dev` stage
- **Workspace mount:** repo root → `/home/trickfire/genesis-simulations`
- **Port forwarding:** `6080` (noVNC) and `5900` (VNC) forwarded to host
- **SSH keys:** `~/.ssh` bind-mounted for `sim create` / `sim auth`
- **Extensions:** Python, C++, ROS/URDF, Docker, formatters, Astro

## Extending the image

To add system packages, edit `docker/Dockerfile` and rebuild. Add to the `runtime` stage for things needed at simulation time, `dev` stage for development-only tools. After changing the Dockerfile, run **Dev Containers: Rebuild Container** from the VS Code Command Palette.

To add Python packages:

```dockerfile
RUN pip3 install --no-cache-dir <package>
```

The `--no-cache-dir` flag keeps the image layer smaller.
