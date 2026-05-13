---
title: Dev Notes
description: Tips, useful commands, and common pitfalls for contributors.
---

## Architecture decisions

### Why Genesis instead of Gazebo?

Genesis is a Python-native physics engine that integrates directly into the ROS 2 process as a node. This removes the separate Gazebo process, the ROS-Gazebo bridge, `ros2_control` hardware interfaces, and per-robot controller YAML files. The result is a simpler stack: one ROS node drives the simulation loop and publishes joint states directly.

### Why one package per robot?

Each robot only needs its URDF, meshes, and RViz config at runtime — there's nothing robot-specific to configure in a separate launch or config package. The shared `sim_common` launch file handles everything else. This keeps `sim create` output minimal and avoids the confusion of editing launch files in one package that reference URDFs in another.

### Why `sim native` instead of just Docker?

The native workflow (`sim native`) stores everything — miniconda, the conda env, build artifacts — inside the repo at `.conda/`. No system installs, no global state. It's the fastest iteration loop for development, and it works on macOS and Linux without Docker installed.

## Useful ROS 2 commands

```bash title="Terminal"
# List all active topics
ros2 topic list

# Stream joint states in real time
ros2 topic echo /joint_states

# Publish a joint trajectory manually
ros2 topic pub /joint_trajectory_controller/joint_trajectory \
    trajectory_msgs/msg/JointTrajectory \
    '{joint_names: ["shoulder_1"], points: [{positions: [0.5], time_from_start: {sec: 2}}]}'

# Check what nodes are running
ros2 node list

# Inspect a node's parameters
ros2 param list /genesis_sim
```

## Building a single package

```bash title="Terminal"
cd robot-sim
colcon build --packages-select arm
source install/setup.bash
```

Use `--packages-up-to arm` to also rebuild all its dependencies.

## Common pitfalls

**Forgetting to source after build:** ROS 2 won't find packages until you run `source install/setup.bash`. The `sim native` / `sim docker` launch scripts do this automatically, but manual `ros2` commands need it first.

**Stale build artifacts:** Run `sim clean` and rebuild if something breaks for no obvious reason. Colcon's incremental builds can get confused after certain types of changes (especially after renaming packages or changing `setup.py`).

**Genesis takes 15–20 s to open the first time:** Normal — Genesis compiles Taichi JIT kernels on first use. Subsequent runs are much faster. If it hangs indefinitely, check that your torch version is ≥ 2.8.0:

```bash title="Terminal"
python3 -c "import torch; print(torch.__version__)"
```

If it's older, delete the torch sentinel and let the CLI upgrade it:

```bash title="Terminal"
rm .conda/.torch_upgraded
sim native arm
```

**VNC shows blank screen (Docker):** The display stack starts automatically, but if you restarted the container manually run `.devcontainer/x_server.sh &` inside the container.

**Port 6080 / 5900 already in use:** Another VNC session or container is using those ports. Stop it or change the port mapping in `docker/docker-compose.yml`.
