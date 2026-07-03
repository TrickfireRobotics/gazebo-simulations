---
title: Running Simulations
description: How to build and launch robot simulations with the sim CLI.
---

All simulations are launched through the `sim` CLI. It builds the ROS 2 workspace, sets up the environment, and runs the launch file for the specified robot.

## Native (pixi)

```bash title="Terminal"
pixi run sim native <robot_name>
```

For example, to run the arm simulation:

```bash title="Terminal"
pixi run sim native arm
```

## Dev Container

```bash title="Inside devcontainer"
sim docker <robot_name>
```

## Options

Both `sim native` and `sim docker` accept the same flags:

| Option | Description |
| --- | --- |
| `--no-build` | Skip the `colcon build` step. Use this when you haven't changed any code and want a faster startup. |
| `--build-only` | Build the workspace but don't launch the simulation. Useful for checking if your changes compile. |

```bash title="Terminal"
# Skip building (already built)
pixi run sim native arm --no-build

# Only build, don't launch
pixi run sim native arm --build-only
```

## Cleaning the workspace

To remove build artifacts and do a clean rebuild:

```bash title="Terminal"
pixi run sim clean
```

This deletes `build/`, `install/`, and `log/` directories. Use this when you encounter unexplained build failures.

## Troubleshooting

**Build fails with cryptic errors:**
Run `sim clean` to delete stale build artifacts, then try again. Stale artifacts are the most common cause of unexplained build failures.

**Gazebo window doesn't appear (Dev Container):**
Connect via your VNC viewer at `localhost:5900` and verify it works with `xeyes`. If the display isn't running, restart it with `.devcontainer/x_server.sh`.

**Package not found errors after launch:**
Try running `sim clean` and building again.
