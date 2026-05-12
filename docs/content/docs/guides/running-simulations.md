---
title: Running Simulations
description: How to build and launch robot simulations with the sim CLI.
---

All simulations are launched through the `sim` CLI. It builds the workspace, sets up the environment, and runs the ROS 2 launch file for the specified robot.

## Basic usage

```bash title="Inside devcontainer"
sim <robot_name>
```

Or use the explicit `docker` command:

```bash title="Inside devcontainer"
sim docker <robot_name>
```

For example, to run the arm simulation:

```bash title="Inside devcontainer"
sim arm
```

## Options

| Option | Description |
| --- | --- |
| `--no-build` | Skip the `colcon build` step. Use this when you haven't changed any code and want a faster startup. |
| `--build-only` | Build the workspace but don't launch the simulation. Useful for checking if your changes compile. |

```bash title="Inside devcontainer"
# Skip building (already built)
sim arm --no-build

# Only build, don't launch
sim arm --build-only
```

## Cleaning the workspace

To remove build artifacts and do a clean rebuild:

```bash title="Inside devcontainer"
sim clean
```

This deletes `build/`, `install/`, and `log/` directories. Use this when you encounter unexplained build failures.

## Troubleshooting

**Build fails with cryptic errors:**
Run `sim clean` to delete stale build artifacts, then try again. Stale artifacts are the most common cause of unexplained build failures.

**Gazebo window doesn't appear:**
The display starts automatically with the Dev Container. Connect via your VNC viewer at `localhost:5900` and verify it works with `xeyes`. If you restarted the container manually and the display isn't running, restart it with `.devcontainer/x_server.sh`.

**Package not found errors after launch:**
Try running `sim clean` and building again.
