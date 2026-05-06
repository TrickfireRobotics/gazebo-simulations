---
title: Scripts
description: Reference for all shell scripts in the scripts/ directory.
---

All scripts live in the `scripts/` directory at the repository root. They're designed to be run from the project root.

## remote_pcs.sh (registry)

`remote_pcs.sh` lives at the **repository root** (not in `scripts/`) and is the single source of truth for remote PC names and IP addresses. Scripts that need to SSH or rsync to a remote host source this file instead of hardcoding IPs. To add or change a PC, edit this file. All scripts that use it (`ssh.sh`, `sync_ssh.sh`, `health_check_remote.sh`) will pick up the change automatically.

---

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

## macos_setup.sh

One-shot native macOS setup for the ROS 2 Humble + Gazebo Harmonic stack.

```bash title="Host terminal"
./scripts/macos_setup.sh [env|patches|ros_gz|control|workspace|all]
```

This script:
1. Creates or reuses the `ros_env` micromamba environment from `.macos/env.lock.yml`
2. Applies the macOS-specific patches inline during setup
3. Builds `ros_gz`, `gz_ros2_control`, and the repository workspace
4. Prints the two-terminal launch sequence for `launch_sim.sh` and `macos_gui.sh`

To remove the native macOS setup, delete the `macos/` directory and the `robot-sim/build`, `robot-sim/install`, and `robot-sim/log` folders.

**Use it with:** the macOS setup guide at [macOS Native Setup](../../guides/macos-native-setup/).

---

## macos_gui.sh

Launches the Gazebo GUI for the native macOS workflow after the simulator server is already running.

```bash title="Host terminal"
./scripts/macos_gui.sh
```

This script:
1. Sources the `ros_gz` workspace at `.macos/ros_gz_ws`
2. Sources the repository workspace overlay at `robot-sim/install/setup.bash`
3. Sets `GZ_SIM_RESOURCE_PATH` so Gazebo can find world and model assets
4. Starts `gz sim --force-version 8 -g` with the repo's GUI config

**Use it with:** the macOS setup guide at [macOS Native Setup](../../guides/macos-native-setup/).

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

---

## ros_clean.sh

Deletes ROS 2 build artifacts to resolve unexplained build failures.

```bash title="Inside devcontainer"
./scripts/ros_clean.sh
```

Removes `build/`, `install/`, and `log/` from the `robot-sim/` directory. This is also run automatically as the Dev Container's `postCreateCommand`.

:::tip
If a build fails and the error doesn't make sense, run this first. Stale artifacts are the most common cause of mysterious build issues.
:::

---

## start_container.sh

Starts the standalone simulation container on any host. Kills any existing container, builds and starts a fresh one, and attaches a shell. Run from the **host machine**, not inside the container.

```bash title="Host terminal"
./scripts/start_container.sh
```

**What it does:**
1. Checks for NVIDIA hardware (`/dev/nvhost-gpu` on Jetson, or `nvidia-smi` on desktop)
2. Stops any existing `gazebo-sim` container
3. Starts the container using `docker-compose.yml` (and `docker-compose-gpu.yml` if NVIDIA GPU is detected)
4. Attaches an interactive shell as the `trickfire` user

**GPU modes:**
- **NVIDIA GPU detected:** Adds `runtime: nvidia`, NVIDIA env vars, and the host X11 socket via `docker-compose-gpu.yml`. Renders directly to the host display. Runs `xhost +local:docker` to allow container X11 access.
- **No GPU:** Starts VNC/noVNC in headless mode. Prints connection URLs for VNC viewer and browser.

---

## attach_to_container.sh

Opens a new interactive terminal inside a running Dev Container. Run this from the **host machine**, not inside the container.

```bash title="Host terminal"
./scripts/attach_to_container.sh
```

It finds the running VS Code Dev Container by matching the image name `vsc-gazebo-simulations`, then attaches with `docker exec` as the `trickfire` user. Useful when you need extra terminal sessions beyond what VS Code provides.

---

## ssh.sh

SSHes into a named remote PC with a project-configured prompt.

```bash title="Host terminal"
./scripts/ssh.sh <target>
```

Targets and IPs are loaded from [`remote_pcs.sh`](#remote_pcssh-registry) at the repo root.

The SSH session loads the project shell config (`docker/shell/ssh.bashrc.sh`) and sets `PROMPT_ENV` to `<target>-host` for an orange-colored prompt label.

---

## sync_ssh.sh

Syncs the local repo to a remote PC over rsync. Useful for deploying code changes to a Jetson.

```bash title="Host terminal"
./scripts/sync_ssh.sh <target>
```

Uses targets from [`remote_pcs.sh`](#remote_pcssh-registry) (or accepts a raw IP address). Excludes files listed in `.gitignore` and the `.git/` directory.

---

## health_check_remote.sh

Runs a health check on remote PCs and reports power mode, CPU/GPU state, fan, thermals, network, and service status with color-coded output.

```bash title="Host terminal"
./scripts/health_check_remote.sh <target>
```

Targets and IPs are loaded from [`remote_pcs.sh`](#remote_pcssh-registry) at the repo root.

**What it checks:**
- Reachability (ping latency and packet loss)
- Power mode (expects `MAXN`)
- CPUs online (expects all 8)
- GPU frequency
- Fan profile (expects `full`)
- Thermal zones (warns at 65C, critical at 80C)
- Ethernet and WiFi power management
- `jetson-clocks.service` and `wifi-disable-powersave` service status

---

## setup_jetson.sh

One-time host setup for running the standalone container on a Jetson (or any NVIDIA Linux host). Run this before using `start_container.sh` for the first time.

```bash title="Host terminal"
./scripts/setup_jetson.sh
```

**What it does:**
1. Installs the NVIDIA Container Toolkit and configures the Docker nvidia runtime
2. Adds the current user to the `docker` group and restarts Docker
3. Sets Jetson power mode to `MAXN` (`nvpmodel -m 0`)
4. Creates and enables `jetson-clocks.service` to keep all CPUs online and clocks at max
5. Creates and enables `wifi-disable-powersave.service` to keep WiFi at full throughput
6. Disables `nvfancontrol.service` and installs `fan-full-speed.service` to run the fan at full speed
7. Sets the desktop wallpaper from `docs/assets/trickfire-wallpaper.png`
8. Configures GNOME: dark mode, desktop icons hidden
9. Installs the kitty terminal with the TrickFire color scheme and sets it as the default
10. Reboots the host
