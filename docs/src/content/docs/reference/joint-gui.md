---
title: Joint GUI
description: Reference for the Tkinter-based joint control GUI that launches with the simulation.
---

The Joint GUI is a Tkinter application that provides interactive slider-based control of robot joints during simulation. It launches automatically as part of the ROS 2 launch file.

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

The GUI doesn't hardcode joint names. Instead:

1. It parses the robot's URDF file (passed as an argument) for all joints of type `revolute`
2. It subscribes to `/joint_states` and waits for the first message to arrive
3. The joints reported in that message become the active joints shown in the GUI

This means the GUI works with any robot -- it adapts to whatever joints exist.

### Origin angles

When joints are first discovered, their current positions (from `/joint_states`) are saved as "origin angles." Slider values are offsets from these origins. When you hit **Send**, the published position is `slider_value + origin_angle`.

This matters because joints may not start at position 0 -- the origin angle ensures the slider's zero position matches the robot's natural resting state.

## Controls

| Control | Description |
| --- | --- |
| **Topic dropdown** | Select which `JointTrajectory` topic to publish on. Auto-populated from available topics. |
| **Refresh** | Re-scan for available trajectory topics |
| **Joint sliders** | One per joint. Range is set by the URDF's `<limit lower="..." upper="...">` values. |
| **Duration** | Time in seconds for the trajectory to complete (default: 2.0s) |
| **Send** | Publish current slider positions as a trajectory command |
| **Sync** | Read current positions from `/joint_states` and update sliders to match |
| **Reset** | Zero all sliders (back to origin position) |

## ROS 2 interface

**Subscribes to:**
- `/joint_states` (`sensor_msgs/msg/JointState`) -- reads current joint positions

**Publishes to:**
- Configurable trajectory topic (default: `/joint_trajectory_controller/joint_trajectory`)
- Message type: `trajectory_msgs/msg/JointTrajectory`

## Running standalone

The GUI is registered as a console script entry point. You can run it outside of the launch file:

```bash title="Inside devcontainer"
ros2 run sim_common joint_gui <path_to_urdf>
```

For example:

```bash title="Inside devcontainer"
ros2 run sim_common joint_gui \
    $(ros2 pkg prefix arm_description)/share/arm_description/urdf/arm.urdf
```

The simulation must already be running with controllers active for the GUI to discover joints.

## Source

The implementation is in `robot-sim/sim_common/sim_common/joint_gui.py`. Key classes:

- **`JointPublisher`** (ROS 2 Node) -- handles URDF parsing, joint state subscription, topic discovery, and trajectory publishing
- **`JointGui`** (Tkinter) -- builds the UI, manages sliders, and dispatches commands to `JointPublisher`
