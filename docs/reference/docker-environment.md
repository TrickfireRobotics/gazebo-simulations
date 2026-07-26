---
title: Docker Environment
description: How the container is configured, the Dockerfile sections, standalone docker-compose usage, and how the headless display works.
---

The Docker container is the alternative to the [native pixi workflow](../setup/macos/). There are two ways to use it:

1. **Dev Container** (VS Code) -- Open the repo in VS Code and choose **Reopen in Container**.
2. **Standalone container** (docker-compose) -- Run simulations on any host without VS Code. NVIDIA GPU passthrough is enabled automatically when hardware is detected.

Both methods use the same `sim` image built from `docker/Dockerfile`.

## Dockerfile

The Dockerfile at `docker/Dockerfile` produces a single stage named `sim` built on Ubuntu 24.04. It is divided into labelled sections:

```
ubuntu:24.04 AS sim
  ├── BASE    - locale, user setup, libdrm stub
  ├── VSG     - VulkanSceneGraph stack (built from source, /opt/vsg)
  ├── CHRONO  - Project Chrono (built from source, /home/trickfire/chrono)
  ├── GAZEBO  - ROS 2 Jazzy + Gazebo Harmonic
  ├── VNC/DISPLAY - headless GUI stack
  └── DEV TOOLING - SSH server, ruff, pre-commit, shfmt
```

A `BUILD_JOBS` build arg controls parallelism for the C++ builds (defaults to `nproc`).

### VSG section

VulkanSceneGraph and its dependencies are built from source and installed to `/opt/vsg`:

| Library                    | Version  | Purpose                                      |
| -------------------------- | -------- | -------------------------------------------- |
| glslang                    | 16.1.0   | GLSL shader compiler (runtime library)       |
| KTX-Software               | v4.4.2   | Texture format support                       |
| draco                      | 1.5.7    | Mesh compression                             |
| assimp                     | v6.0.5   | 3D asset import                              |
| VulkanSceneGraph (vsg)     | v1.1.15  | Vulkan-based scene graph rendering           |
| vsgXchange                 | v1.1.12  | Asset format bridge for vsg (uses assimp)    |
| vsgImGui                   | v0.7.0   | ImGui integration for vsg overlays           |

`LD_LIBRARY_PATH` is set to `/opt/vsg/lib` so the shared libraries are found at runtime.

### Chrono section

Project Chrono is cloned from source and built with the Vehicle and VSG modules enabled:

```
CH_ENABLE_MODULE_VEHICLE  - wheel/terrain dynamics
CH_ENABLE_MODULE_VSG      - Vulkan-based visualizer
```

The build target is `demo_VEH_SCMTerrain_RigidTire`. An upstream bug in `SCMTerrain.cpp` (domain list not cleared before `AddActiveDomain`) is patched at image build time.

The Chrono source and build live at `/home/trickfire/chrono` and are owned by the `trickfire` user.

### Gazebo section

**Simulation stack:**

| Package                                | Purpose                                         |
| -------------------------------------- | ----------------------------------------------- |
| Gazebo Harmonic                        | Physics simulation engine                       |
| `ros-jazzy-ros-gz`                     | ROS 2 / Gazebo integration + bridge             |
| `ros-jazzy-ros2-controllers`           | Joint state broadcaster + trajectory controller |
| `ros-jazzy-gz-ros2-control`            | Hardware interface for Gazebo                   |
| `ros-jazzy-rviz2`                      | Robot visualization                             |
| `ros-jazzy-xacro`                      | URDF macro processing                           |
| `ros-jazzy-joint-state-publisher-gui`  | Joint state publishing GUI                      |

**Python packages:** `pypresence`, `trimesh`, `pyfqmr`

### VNC / display section

**Display stack (headless GUI):**

| Package                                          | Purpose                                       |
| ------------------------------------------------ | --------------------------------------------- |
| `xserver-xorg-core` + `xserver-xorg-video-dummy` | Virtual X server with dummy driver (no GPU)   |
| `openbox`                                        | Lightweight window manager                    |
| `x11vnc`                                         | VNC server for remote X11 access              |
| `novnc` + `websockify`                           | Browser-based VNC client                      |
| `xvfb`                                           | Virtual framebuffer for Jetson/Tegra (no DRI) |
| `mesa-utils`, `libgl1-mesa-dri`                  | Software OpenGL rendering                     |
| `kmod`                                           | Kernel module tools (for `/lib/modules` mount)|
| `x11-apps`                                       | X11 utilities including `xeyes`               |

### Dev tooling section

| Package/tool   | Purpose                                                  |
| -------------- | -------------------------------------------------------- |
| `openssh-server` | SSH server (used by VS Code remote connection)         |
| `ruff`         | Python linter/formatter                                  |
| `pre-commit`   | Git hook framework                                       |
| `shfmt`        | Shell script formatter                                   |

## Container user

The container runs as a non-root user `trickfire` with passwordless sudo:

```dockerfile
RUN useradd trickfire --uid 1000 --shell /bin/bash --create-home --no-log-init
RUN echo "trickfire ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
```

## Dev Container configuration

The `devcontainer.json` configures how VS Code opens the container:

**Build target:** `sim` stage of `docker/Dockerfile`

**Workspace mount:** The repo is bind-mounted into the container at `/home/trickfire/simulations`.

**Compose config:** `.devcontainer/devcontainer.json` uses `docker/docker-compose.yml` plus `docker/docker-compose-dev.yml`. The override adds Wayland and display environment variables for Vulkan rendering.

**Port forwarding:** Ports `6080` (noVNC) and `5900` (VNC) are forwarded to the host.

**Privileged mode:** The container runs with `--privileged` and device access for hardware interaction (USB, CAN bus).

**VS Code extensions:** Pre-installs Python, C++ (clangd, CMake, Makefile), ROS, URDF, Docker, Prettier, and other formatting extensions.

## X-server Display Architecture

```
Xorg/Xvfb  →  x11vnc  →  websockify  →  Browser
    ↑                                       ↑
 Openbox WM                            noVNC client
    ↑                                   (port 6080)
 Gazebo / RViz / Chrono VSG
```

### Why this approach?

Alternatives like Xvfb don't support GLX properly, which means Gazebo's 3D rendering fails. Using Xorg with a dummy driver + Mesa software rendering gives us full OpenGL support without needing a real GPU. The VNC + noVNC layer makes it accessible from any browser. On Jetsons, we fall back to Xvfb because there's no `/dev/dri`, but GPU rendering still works via EGL through injected Tegra libs.

Chrono uses Vulkan for rendering via the VSG module. Wayland socket passthrough (`WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`) is exposed to the container so Vulkan can reach the host compositor when available.

### Environment variables

| Variable           | Value                  | Set in                              |
| ------------------ | ---------------------- | ----------------------------------- |
| `DISPLAY`          | Host-dependent         | `docker-compose.yml` (standalone)   |
| `WAYLAND_DISPLAY`  | Host-dependent         | `docker-compose-dev.yml`            |
| `XDG_RUNTIME_DIR`  | `/run/host-runtime`    | `docker-compose-dev.yml`            |
| `VNC_PORT`         | `5900`                 | Dockerfile                          |
| `NOVNC_PORT`       | `6080`                 | Dockerfile                          |
| `VSG_INSTALL_DIR`  | `/opt/vsg`             | Dockerfile                          |
| `LD_LIBRARY_PATH`  | `/opt/vsg/lib`         | Dockerfile                          |

## Extending the container

To add system packages, edit `docker/Dockerfile` and rebuild. For Python packages, add them to the `pip3 install` line in the Gazebo section (simulation-time) or the dev tooling section (development-only tools).

After changing the Dockerfile, use **Dev Containers: Rebuild Container** in VS Code's Command Palette.
