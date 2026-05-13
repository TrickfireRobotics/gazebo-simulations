---
title: Launch System
description: How the shared sim.launch.py orchestrates the Genesis simulation, robot_state_publisher, and Joint GUI.
---

All robots share a single launch file at `robot-sim/sim_common/launch/sim.launch.py`. There are no per-robot launch files.

## Launch arguments

| Argument | Default | Description |
| --- | --- | --- |
| `robot` | (required) | Robot package name, e.g. `arm` |
| `gui` | `true` | Launch the Tkinter Joint GUI |
| `headless` | `false` | Run Genesis without a viewer window (used by `sim docker`) |

Invoke directly:

```bash title="Terminal"
ros2 launch sim_common sim.launch.py robot:=arm
ros2 launch sim_common sim.launch.py robot:=arm gui:=false headless:=true
```

## Startup sequence

```
1. robot_state_publisher
   Reads the URDF from the robot package's share directory and
   publishes the TF tree + /robot_description topic.

2. genesis_sim
   Loads the URDF into Genesis, steps physics at 60 Hz.
   Publishes /joint_states, subscribes to joint_trajectory_controller topic.

3. joint_gui  (if gui:=true)
   Tkinter GUI. Reads joint limits from URDF, subscribes to /joint_states,
   publishes JointTrajectory commands.
```

All three start in parallel. When `genesis_sim` exits (window closed, Ctrl+C, or crash), a `RegisterEventHandler(OnProcessExit)` emits a `Shutdown` event that terminates all other nodes.

## Components

### robot_state_publisher

```python
robot_state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    parameters=[{"robot_description": open(urdf_file, encoding="utf-8").read()}],
)
```

Reads the URDF directly from the robot package's share directory (resolved by `get_asset()`). No xacro processing at launch time — the URDF is already fully resolved.

### genesis_sim

```python
genesis_sim = Node(
    package="sim_common",
    executable="genesis_sim",
    arguments=[robot],          # or [robot, "--headless"]
)
```

The `genesis_sim` entry point (`sim_common/genesis_sim.py`) runs the Genesis physics loop in the main thread and spins ROS callbacks in a background `MultiThreadedExecutor`. The main loop:

```python
while rclpy.ok() and node.viewer_alive and not _shutdown.is_set():
    node.step()   # apply commands → scene.step() → publish joint states
```

`SIGINT` / `SIGTERM` set a threading event that breaks the loop cleanly.

### joint_gui

```python
joint_gui = Node(
    package="sim_common",
    executable="joint_gui",
    arguments=[urdf_file],
)
```

Tkinter-based joint slider GUI. Reads joint limits from the URDF at startup, discovers active joints from `/joint_states`, and publishes `JointTrajectory` messages when you click **Send**.

### Shutdown propagation

```python
RegisterEventHandler(
    OnProcessExit(
        target_action=genesis_sim,
        on_exit=[EmitEvent(event=Shutdown())],
    )
)
```

When genesis_sim exits for any reason, the `Shutdown` event terminates the whole launch group. This means closing the Genesis window or pressing Ctrl+C stops robot_state_publisher and joint_gui as well.

## launch_utils.py

`sim_common` provides a `get_asset()` helper:

```python
from sim_common.launch_utils import get_asset

urdf_file = get_asset("arm", "urdf", "arm.urdf")
```

Resolves a file inside a ROS 2 package's share directory and exits with a clear error if the file doesn't exist — catches missing files at launch time rather than mid-simulation.
