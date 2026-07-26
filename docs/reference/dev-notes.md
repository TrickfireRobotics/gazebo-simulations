---
title: Dev Notes
description: Internal notes, tips, and architectural decisions for contributors.
---

## Architecture decisions

### Why pixi for the native workflow?

ROS 2 + Gazebo + their dependencies are notoriously painful to install natively, especially across different OS versions. [pixi](https://pixi.sh) solves this by storing the entire environment (ROS 2 Jazzy, Gazebo Harmonic, all dependencies) inside the repo's `.pixi/` directory via conda. Deleting the repo also deletes the environment - your system stays completely clean. The same `pixi install` works on Linux, macOS, and WSL2 without any OS-level ROS installation.

### Why a Dev Container (alternative)?

The Docker Dev Container is an alternative for users who prefer a containerized environment or already have Docker set up. It provides the same ROS 2 Jazzy + Gazebo Harmonic environment inside a container. The Dev Container is useful for Windows users (via Docker Desktop), CI systems, or anyone who wants strong isolation from their host system.

### Why Gazebo Harmonic?

Gazebo Harmonic (gz-sim 8.x) is the current LTS release of the new-generation Gazebo and pairs with ROS 2 Jazzy. It replaces the old Gazebo Fortress (ignition-fortress). The package prefix changed from `ign` to `gz` in this generation - use `gz topic`, `gz service`, etc.

### Why two packages per robot?

The `_description` / `_bringup` split is a ROS convention:
- **`_description`** contains the robot model (URDF + meshes) -- things that change when the CAD changes
- **`_bringup`** contains runtime config (launch files, controller YAML, RViz config) -- things you tweak during development

This separation means `sim gazebo update` can safely replace the description without touching your launch customizations.

## Useful CLI commands

### Gazebo camera position

To set the camera position in the Gazebo viewer:

```bash title="Terminal"
gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 2000 \
    --req "pose: {position: {x: 0.0, y: -2.0, z: 2.0} orientation: {x: -0.2706, y: 0.2706, z: 0.6533, w: 0.6533}}"
```

To read the current camera position:

```bash title="Terminal"
gz topic -e -t /gui/camera/pose
```

### ROS 2 inspection

```bash title="Terminal"
# List all topics
ros2 topic list

# See joint states in real time
ros2 topic echo /joint_states

# List active controllers
ros2 control list_controllers

# Check controller manager status
ros2 control list_hardware_interfaces
```

### Building a single package

```bash title="Terminal"
cd gazebo
colcon build --packages-select arm_description
source install/setup.bash
```

## Community `apt` repository (Dev Container)

Some ROS packages live in the `universe` repository rather than `main`. If `apt` can't find a package inside the container:

```bash title="Inside devcontainer"
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y universe
apt-get update
```

:::note
The Dockerfile already enables `universe` for the packages that need it.
:::

## Common pitfalls

**Forgetting to source after build:** ROS 2 can't find packages until you run `source gazebo/install/setup.bash`. The launch script does this automatically, but if you're running ROS commands manually, you need to source first.

**Stale build artifacts:** If something breaks for no obvious reason, run `sim gazebo clean` and rebuild. Colcon's incremental builds can get confused after certain types of changes.

**X server not running (Dev Container only):** Gazebo and RViz will fail silently or crash if the X server isn't started. The Dev Container starts it automatically, but if you need to restart it manually, run `.devcontainer/x_server.sh`.

**Port conflicts (Dev Container only):** If port 6080 or 5900 is already in use, the X server script will fail. Make sure no other VNC sessions or containers are using those ports.
