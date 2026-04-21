---
title: Scripts
description: Reference for all shell scripts in the scripts/ directory.
---

All scripts live in the `scripts/` directory at the repository root. They're designed to be run from the project root.

## launch_sim.sh

The main entry point for running simulations. Builds the ROS 2 workspace and launches Gazebo with the specified robot.

```bash title="Inside devcontainer"
./scripts/launch_sim.sh <robot_name> [flags]
```

**Flags:**

| Flag | Description |
| --- | --- |
| `--no-build` | Skip the `colcon build` step |
| `--build-only` | Build only, don't launch |
| `--help` | Print usage and exit |

**What it does:**
1. Validates that `<robot>_bringup` and `<robot>_description` packages exist in `robot-sim/`
2. Runs `colcon build --packages-up-to` targeting the robot's packages plus `sim_worlds` and `sim_common`
3. Sources `install/setup.bash`
4. Sets `GZ_SIM_RESOURCE_PATH` for Gazebo world file discovery
5. Runs `ros2 launch <robot>_bringup <robot>.launch.py gui:=true`

**Logging:** All output is teed to `robot-sim/log/<robot>-gazebo-<timestamp>.log` with ANSI codes stripped.

**Source:** `scripts/launch_sim.sh`

---

## start_x_server.sh

Starts a headless X11 desktop inside the container so Gazebo, RViz, and other GUI apps can render. Automatically detects the GPU environment and selects the appropriate backend.

```bash title="Inside devcontainer"
./scripts/start_x_server.sh [-v|--verbose]
```

**GPU auto-detection:**

| Condition | Backend | Xorg Config |
| --- | --- | --- |
| Jetson/Tegra (no `/dev/dri`) | Xvfb | `xorg.nvidia.conf` |
| Desktop NVIDIA GPU detected | Xorg with nvidia driver | `xorg.nvidia.conf` |
| No GPU (default) | Xorg with dummy driver | `xorg.dummy.conf` |

**What it starts (in order):**
1. **Xorg or Xvfb** -- virtual X server, using the auto-detected config from `docker/`
2. **Openbox** -- lightweight window manager for window decorations and resizing
3. **x11vnc** -- VNC server on port `5900` for remote access to the X display
4. **noVNC** -- web-based VNC client on port `6080`, accessible at `http://localhost:6080/vnc.html`

**Environment variables used** (set in the Dockerfile or `launch.env`):
- `DISPLAY` -- X display identifier
- `VNC_PORT` -- VNC server port (`5900`)
- `NOVNC_PORT` -- noVNC web port (`6080`)

The script traps `SIGINT`/`SIGTERM` and cleans up all child processes on exit.

**Source:** `scripts/start_x_server.sh`

---

## ros-clean.sh

Deletes ROS 2 build artifacts to resolve unexplained build failures.

```bash title="Inside devcontainer"
./scripts/ros-clean.sh
```

Removes `build/`, `install/`, and `log/` from the `robot-sim/` directory. This is also run automatically as the Dev Container's `postCreateCommand`.

:::tip
If a build fails and the error doesn't make sense, run this first. Stale artifacts are the most common cause of mysterious build issues.
:::

**Source:** `scripts/ros-clean.sh`

---

## nvidia-container.sh

Manages the standalone simulation container on NVIDIA hosts. Kills any existing container, builds and starts a fresh one, and attaches a shell. Run from the **host machine**, not inside the container.

```bash title="Host terminal"
./scripts/nvidia-container.sh
```

**What it does:**
1. Checks for NVIDIA hardware (`lspci`) and drivers (`nvidia-smi`)
2. Stops any existing `gazebo-sim` container
3. Starts the container using `docker-compose.yml` (and `docker-compose-local.yml` if NVIDIA GPU is detected)
4. Attaches an interactive shell as the `trickfire` user

**GPU modes:**
- **NVIDIA GPU detected:** Enables `runtime: nvidia`, mounts the host X11 socket, and renders to the host display. Runs `xhost +local:docker` to allow container X11 access.
- **No NVIDIA GPU:** Starts the VNC/noVNC headless display. Prints connection URLs for VNC viewer and browser.

**Source:** `scripts/nvidia-container.sh`

---

## attach_to_container.sh

Opens a new interactive terminal inside a running Dev Container. Run this from the **host machine**, not inside the container.

```bash title="Host terminal"
./scripts/attach_to_container.sh
```

It finds the running VS Code Dev Container by matching the image name `vsc-gazebo-simulations`, then attaches with `docker exec` as the `trickfire` user. Useful when you need extra terminal sessions beyond what VS Code provides.

**Source:** `scripts/attach_to_container.sh`

---

## ssh-nvidia.sh

SSHes into a named NVIDIA PC (Jetson) with a project-configured prompt.

```bash title="Host terminal"
./scripts/ssh-nvidia.sh <target>
```

**Known targets:**

| Name | IP |
| --- | --- |
| `orin` | `192.168.0.211` |
| `xavier` | `192.168.0.148` |

The SSH session loads the project shell config (`docker/shell/ssh.bashrc.sh`) and sets `PROMPT_ENV` to `<target>-host` for an orange-colored prompt label.

**Source:** `scripts/ssh-nvidia.sh`

---

## sync_ssh.sh

Syncs the local repo to a Jetson over rsync. Useful for deploying code changes to a remote host.

```bash title="Host terminal"
./scripts/sync_ssh.sh <target>
```

Uses the same named targets as `ssh-nvidia.sh` (or accepts a raw IP address). Excludes files listed in `.gitignore` and the `.git/` directory.

**Source:** `scripts/sync_ssh.sh`

---

## health-check-nvidia.sh

Runs a health check on NVIDIA PCs (Jetsons) and reports power mode, CPU/GPU state, fan, thermals, network, and service status with color-coded output.

```bash title="Host terminal"
./scripts/health-check-nvidia.sh           # check all PCs
./scripts/health-check-nvidia.sh xavier    # check a specific PC
```

**What it checks:**
- Reachability (ping latency and packet loss)
- Power mode (expects `MAXN`)
- CPUs online (expects all 8)
- GPU frequency
- Fan profile (expects `full`)
- Thermal zones (warns at 65C, critical at 80C)
- Ethernet and WiFi power management
- `jetson-clocks.service` and `wifi-disable-powersave` service status

**Source:** `scripts/health-check-nvidia.sh`

---

## setup_jetson.sh

One-time host setup for running the standalone container on a Jetson (or any NVIDIA Linux host). Run this before using `nvidia-container.sh` for the first time.

```bash title="Host terminal"
./scripts/setup_jetson.sh
```

**What it does:**
1. Installs the NVIDIA Container Toolkit and configures the Docker nvidia runtime
2. Adds the current user to the `docker` group
3. Restarts Docker

**Source:** `scripts/setup_jetson.sh`
