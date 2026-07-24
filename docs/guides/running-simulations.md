---
title: Running Simulations
description: How to build and launch robot simulations with the sim CLI.
---

All simulations are launched through the `sim` CLI. The first argument selects the simulator (`gazebo` or `chrono`); subsequent arguments control what to run.

## Gazebo

### Native (pixi)

```bash title="Terminal"
pixi run sim gazebo native <robot_name>
```

For example, to run the arm simulation:

```bash title="Terminal"
pixi run sim gazebo native arm
```

### Dev Container

```bash title="Inside devcontainer"
sim gazebo docker <robot_name>
```

### Options

Both `sim gazebo native` and `sim gazebo docker` accept the same flags:

| Option         | Description                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `--no-build`   | Skip the `colcon build` step. Use this when you haven't changed any code and want a faster startup. |
| `--build-only` | Build the workspace but don't launch the simulation. Useful for checking if your changes compile.   |

```bash title="Terminal"
# Skip building (already built)
pixi run sim gazebo native arm --no-build

# Only build, don't launch
pixi run sim gazebo native arm --build-only
```

### Cleaning the workspace

To remove build artifacts and do a clean rebuild:

```bash title="Terminal"
pixi run sim gazebo clean
```

This deletes `gazebo/build/`, `gazebo/install/`, and `gazebo/log/`. Use this when you encounter unexplained build failures.

## Troubleshooting

**Build fails with cryptic errors:**
Run `sim gazebo clean` to delete stale build artifacts, then try again. Stale artifacts are the most common cause of unexplained build failures.

**Gazebo window doesn't appear (Dev Container):**
Connect via your VNC viewer at `localhost:5900` and verify it works with `xeyes`. If the display isn't running, restart it with `.devcontainer/x_server.sh`.

**Package not found errors after launch:**
Try running `sim gazebo clean` and building again.
