---
title: Running Simulations
description: How to build and launch robot simulations with the sim CLI.
---

Simulations are launched through the `sim` CLI. It builds the ROS 2 workspace, sets up the environment, and runs the shared Genesis launch file for the specified robot.

## Native (local Genesis window)

```bash title="Terminal"
sim native arm
```

Bootstraps the conda env on first run, then builds and launches. Genesis opens a native viewer window.

## Docker (VNC display)

```bash title="Terminal"
sim docker arm
```

Builds the ROS 2 workspace inside the container and launches Genesis headlessly. Connect via VNC at `localhost:5900` or browser at `http://localhost:6080`.

## Flags

Both `sim native` and `sim docker` accept the same flags:

| Flag | Description |
| --- | --- |
| `--no-build` | Skip `colcon build` — use the existing `install/` directory. Faster when you haven't changed any ROS packages. |
| `--build-only` | Build only, don't launch. Useful for CI or checking that your changes compile. |

```bash title="Terminal"
# Already built, just launch
sim native arm --no-build

# Build only (don't open the viewer)
sim native arm --build-only
```

## Cleaning the workspace

```bash title="Terminal"
sim clean
```

Deletes `robot-sim/build/`, `robot-sim/install/`, and `robot-sim/log/`. Use this when you hit unexplained build failures — stale artifacts are the most common cause.

## What launches

Both commands run the shared `sim_common/launch/sim.launch.py` launch file, which starts three components:

1. **`robot_state_publisher`** — publishes the robot's TF tree from the URDF
2. **`genesis_sim`** — Genesis physics simulation, publishes `/joint_states`, subscribes to `/joint_trajectory_controller/joint_trajectory`
3. **Joint GUI** — Tkinter sliders for interactive joint control (disable with `gui:=false`)

When the Genesis window or process exits, the launch file automatically shuts down all other nodes.

## Environment variable

Set `GENESIS_BACKEND=cuda` before launching to enable the CUDA backend (requires an Nvidia GPU and the GPU Docker Compose override):

```bash title="Terminal"
GENESIS_BACKEND=cuda sim docker arm
```

## Troubleshooting

**Build fails with cryptic errors:** Run `sim clean` then retry.

**Genesis takes 15–20 seconds to open:** Normal on the first run after a fresh install — Genesis compiles Taichi kernels. Subsequent runs are faster.

**Joint GUI shows no joints:** Wait a moment for Genesis to finish loading. The GUI discovers joints from `/joint_states`, which genesis_sim starts publishing after `scene.build()` completes.
