---
title: Docker Environment
description: How the Dev Container is configured, what's installed, and how the headless display works.
---

The entire simulation environment runs inside a Docker container managed by VS Code Dev Containers. This ensures everyone on the team has an identical setup regardless of their host OS.

## Base image

```dockerfile
FROM ros:humble-ros-base
```

This gives us **Ubuntu Jammy 22.04** with **ROS 2 Humble** pre-installed.

## What's installed

### Simulation stack

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

### Display stack (headless GUI)

| Package | Purpose |
| --- | --- |
| `xserver-xorg-core` + `xserver-xorg-video-dummy` | Virtual X server with no real GPU |
| `openbox` | Lightweight window manager |
| `x11vnc` | VNC server for remote X11 access |
| `novnc` + `websockify` | Browser-based VNC client |
| `mesa-utils`, `libgl1-mesa-*` | Software OpenGL rendering |

### Python packages

| Package | Purpose |
| --- | --- |
| `onshape-to-robot` | CAD-to-URDF conversion (used by genbot) |
| `open3d` | STL mesh decimation |
| `ruff` | Python linter |
| `moteus` | Motor controller interface (for hardware integration) |
| `opencv-python` | Computer vision |

### Build tools

| Package | Purpose |
| --- | --- |
| `python3-colcon-common-extensions` | ROS 2 workspace build system |
| `python3-rosdep` | ROS dependency installer |
| `git` | Version control |

## Container user

The container runs as a non-root user `trickfire` with passwordless sudo. This matches standard development practices and avoids permission issues.

```dockerfile
RUN useradd trickfire --shell /bin/bash --create-home
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
```

## Dev Container configuration

The `devcontainer.json` configures how VS Code opens the container:

**Workspace mount:** The repo is bind-mounted into the container at `/home/trickfire/gazebo-simulations`.

**Port forwarding:** Ports `6080` (noVNC) and `5900` (VNC) are forwarded to the host.

**Privileged mode:** The container runs with `--privileged` and device access for hardware interaction (USB, CAN bus).

**Post-create command:** `scripts/clean_build.sh` runs automatically to clear stale build artifacts.

**VS Code extensions:** Pre-installs Python, C++, ROS, URDF, Docker, and formatting extensions.

## Headless display system

Since Docker containers have no monitor, we use a virtual X11 server so Gazebo and RViz can render.

### Architecture

```
Xorg (dummy driver)  →  x11vnc  →  websockify  →  Browser
      ↑                                              ↑
  Openbox WM                                    noVNC client
      ↑                                         (port 6080)
  Gazebo / RViz
```

### xorg.conf explained

The custom X11 config at `/etc/X11/xorg.conf` defines a fake display:

| Section | Purpose |
| --- | --- |
| `Module` | Loads GLX extension for OpenGL support inside X11 |
| `Device` | Creates a virtual GPU using the `dummy` driver with 256 MB of virtual VRAM |
| `Monitor` | Defines a fake monitor with plausible refresh rates |
| `Screen` | Sets the resolution and 24-bit color depth |
| `ServerLayout` | Ties everything together into one virtual display |

### Environment variables

| Variable | Value | Set in |
| --- | --- | --- |
| `DISPLAY` | `:1` | Dockerfile / launch.env |
| `VNC_PORT` | `5900` | Dockerfile |
| `NOVNC_PORT` | `6080` | Dockerfile |

### Why this approach?

Alternatives like Xvfb don't support GLX properly, which means Gazebo's 3D rendering fails. Using Xorg with a dummy driver + Mesa software rendering gives us full OpenGL support without needing a real GPU. The VNC + noVNC layer makes it accessible from any browser.

## Extending the container

To add system packages, edit `.devcontainer/Dockerfile` and rebuild the container. For Python packages, add them to the `pip3 install` section.

After changing the Dockerfile, use **Dev Containers: Rebuild Container** in VS Code's Command Palette.
