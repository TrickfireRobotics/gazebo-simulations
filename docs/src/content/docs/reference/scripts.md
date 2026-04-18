---
title: Scripts
description: Reference for all shell scripts in the scripts/ directory.
---

All scripts live in the `scripts/` directory at the repository root. They're designed to be run from the project root.

## launch_sim.sh

The main entry point for running simulations. Builds the ROS 2 workspace and launches Gazebo with the specified robot.

```bash
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

Starts a complete headless X11 desktop inside the container so Gazebo, RViz, and other GUI apps can render.

```bash
./scripts/start_x_server.sh [-v|--verbose]
```

**What it starts (in order):**
1. **Xorg** -- virtual X server using the dummy display driver, configured via `/etc/X11/xorg.conf`
2. **Openbox** -- lightweight window manager for window decorations and resizing
3. **x11vnc** -- VNC server on port `5900` for remote access to the X display
4. **noVNC** -- web-based VNC client on port `6080`, accessible at `http://localhost:6080/vnc.html`

**Environment variables used** (set in the Dockerfile):
- `DISPLAY` -- X display identifier (`:1`)
- `VNC_PORT` -- VNC server port (`5900`)
- `NOVNC_PORT` -- noVNC web port (`6080`)

The script traps `SIGINT`/`SIGTERM` and cleans up all child processes on exit.

**Source:** `scripts/start_x_server.sh`

---

## clean_build.sh

Deletes ROS 2 build artifacts to resolve unexplained build failures.

```bash
./scripts/clean_build.sh
```

Removes `build/`, `install/`, and `log/` from the `robot-sim/` directory. This is also run automatically as the Dev Container's `postCreateCommand`.

:::tip
If a build fails and the error doesn't make sense, run this first. Stale artifacts are the most common cause of mysterious build issues.
:::

**Source:** `scripts/clean_build.sh`

---

## attach_to_container.sh

Opens a new interactive terminal inside a running Dev Container. Run this from the **host machine**, not inside the container.

```bash
./scripts/attach_to_container.sh
```

It finds the running VS Code Dev Container by matching the image name `vsc-gazebo-simulations`, then attaches with `docker exec` as the `trickfire` user. Useful when you need extra terminal sessions beyond what VS Code provides.

**Source:** `scripts/attach_to_container.sh`

