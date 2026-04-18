---
title: Running Simulations
description: How to build and launch robot simulations with launch_sim.sh, including available flags and what happens under the hood.
---

All simulations are launched through a single script. It builds the workspace, sets up the environment, and runs the ROS 2 launch file for the specified robot.

## Basic usage

```bash
./scripts/launch_sim.sh <robot_name>
```

For example, to run the arm simulation:

```bash
./scripts/launch_sim.sh arm
```

## Flags

| Flag | Description |
| --- | --- |
| `--no-build` | Skip the `colcon build` step. Use this when you haven't changed any code and want a faster startup. |
| `--build-only` | Build the workspace but don't launch the simulation. Useful for checking if your changes compile. |
| `--help` | Print usage info and exit. |

```bash
# Skip building (already built)
./scripts/launch_sim.sh arm --no-build

# Only build, don't launch
./scripts/launch_sim.sh arm --build-only
```

## What happens when you run it

Here's the full sequence `launch_sim.sh` goes through:

### 1. Validation

The script checks that the expected packages exist on disk:
- `robot-sim/<robot>_bringup/` -- launch files and configs
- `robot-sim/<robot>_description/` -- URDF and meshes
- `robot-sim/<robot>_bringup/launch/<robot>.launch.py` -- the launch file itself

If any are missing, the script exits with an error.

### 2. Build

Runs `colcon build` targeting the robot's packages plus shared ones:

```bash
colcon build \
    --packages-up-to <robot>_bringup <robot>_description sim_worlds sim_common \
    --cmake-args -DBUILD_TESTING=OFF
```

The `--packages-up-to` flag ensures all dependencies are built in the right order.

### 3. Source

Sources the workspace overlay so ROS 2 can find the built packages:

```bash
source install/setup.bash
```

### 4. Environment setup

Sets `GZ_SIM_RESOURCE_PATH` so Gazebo can find world files from `sim_worlds`:

```bash
export GZ_SIM_RESOURCE_PATH=".../install/sim_worlds/share/sim_worlds"
```

### 5. Launch

Calls the robot's launch file with the GUI enabled:

```bash
ros2 launch <robot>_bringup <robot>.launch.py gui:=true
```

The launch file then orchestrates everything -- see the [Launch System reference](../../reference/launch-system/) for details.

## Logging

Every run creates a timestamped log file at:

```
robot-sim/log/<robot>-gazebo-YYYY-MM-DD_HH-MM.log
```

The log captures all terminal output with ANSI color codes stripped.

## Troubleshooting

**Build fails with cryptic errors:**
Run `./scripts/clean_build.sh` to delete `build/`, `install/`, and `log/` directories, then try again. Stale build artifacts are the most common cause of unexplained build failures.

**Gazebo window doesn't appear:**
Make sure the X server is running (`./scripts/start_x_server.sh`) and you're connected via your VNC viewer. You can verify the display works by running `xeyes` in the container -- if the eyes appear on the VNC desktop, the display is fine and the issue is elsewhere.

**Package not found errors after launch:**
You may need to re-source the workspace. Open a new terminal or run `source robot-sim/install/setup.bash`.
