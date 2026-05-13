---
title: Joint GUI
description: Reference for the Tkinter-based joint control GUI that launches with the simulation.
---

The Joint GUI is a Tkinter application that provides interactive slider-based control of robot joints. It launches automatically as part of the simulation.

## How it works

### Startup sequence

```
1. Parse the URDF for all revolute joints
   → Extract joint names, lower/upper limits

2. Subscribe to /joint_states
   → Wait for first message to discover active joints
   → Record origin angles for each joint

3. Build the GUI
   → Create sliders with limits from the URDF
   → Auto-discover available JointTrajectory topics

4. Run two threads
   → Main thread: Tkinter event loop (UI updates)
   → Background thread: ROS 2 spin (message callbacks)
```

### Joint discovery

The GUI doesn't hardcode joint names. It parses the robot's URDF for all `revolute` joints, then subscribes to `/joint_states` and waits for the first message. The joints reported in that message become the active joints shown in the GUI — so it works with any robot automatically.

### Origin angles

When joints are first discovered, their current positions from `/joint_states` are saved as "origin angles." Slider values are offsets from these origins. When you hit **Send**, the published position is `slider_value + origin_angle`.

This ensures the slider's zero position matches the robot's natural resting state, even if joints don't start at position 0.

## Controls

| Control | Description |
| --- | --- |
| **Topic dropdown** | Select which `JointTrajectory` topic to publish on |
| **Refresh** | Re-scan for available trajectory topics |
| **Joint sliders** | One per joint; range from URDF `<limit lower="..." upper="...">` |
| **Duration** | Seconds for the trajectory to complete (default: 2.0 s) |
| **Send** | Publish current slider positions as a trajectory command |
| **Sync** | Read current `/joint_states` and move sliders to match |
| **Reset** | Zero all sliders (back to origin position) |

## ROS 2 interface

**Subscribes to:**
- `/joint_states` (`sensor_msgs/msg/JointState`) — reads current joint positions

**Publishes to:**
- Configurable trajectory topic (default: `/joint_trajectory_controller/joint_trajectory`)
- Message type: `trajectory_msgs/msg/JointTrajectory`

## Running standalone

```bash title="Terminal"
ros2 run sim_common joint_gui <path_to_urdf>
```

For example, using the installed share directory:

```bash title="Terminal"
ros2 run sim_common joint_gui \
    $(ros2 pkg prefix arm)/share/arm/urdf/arm.urdf
```

The Genesis simulation must already be running for the GUI to discover joints from `/joint_states`.

## Source

Implementation: `robot-sim/sim_common/sim_common/joint_gui.py`

- **`JointPublisher`** (ROS 2 Node) — URDF parsing, joint state subscription, topic discovery, trajectory publishing
- **`JointGui`** (Tkinter) — UI, sliders, dispatches commands to `JointPublisher`
