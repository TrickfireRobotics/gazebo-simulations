---
title: Moving Joints
description: Control robot joints using the Joint GUI or the move_joints CLI node.
---

There are two ways to move joints: the **Joint GUI** (graphical, interactive) and the **`move_joints` node** (scriptable, one-shot commands). Both publish `JointTrajectory` messages to genesis_sim on `/joint_trajectory_controller/joint_trajectory`.

## Joint GUI (interactive)

The Joint GUI launches automatically with the simulation. It provides sliders for each joint discovered from the robot's URDF.

### Controls

| Button | Action |
| --- | --- |
| **Send** | Publishes the current slider positions as a trajectory command |
| **Sync** | Reads current joint positions from `/joint_states` and moves sliders to match |
| **Reset** | Zeros all sliders |

You can also:
- Change the **Duration** (seconds) for how long the trajectory takes
- Select which **Topic** to publish on (auto-discovered from available `JointTrajectory` topics)
- Click **Refresh** to re-scan for topics

### How it works

1. On launch, the GUI parses the URDF file for all `revolute` joints, reading their `lower` and `upper` limits
2. It subscribes to `/joint_states` to discover which joints are active and their current positions
3. When you hit **Send**, it publishes a `JointTrajectory` message with positions offset by each joint's origin angle

:::tip
If the GUI shows "Discovering joints from /joint_states..." for a long time, Genesis may still be loading. Wait for it to finish building the scene.
:::

To suppress the GUI:

```bash title="Terminal"
sim native arm --no-build  # then pass gui:=false directly
ros2 launch sim_common sim.launch.py robot:=arm gui:=false
```

## move_joints node (CLI)

Sends a single trajectory command and exits. Useful for scripting or quick tests.

### Usage

```bash title="Terminal"
ros2 run sim_common move_joints --ros-args \
    -p joints:="['shoulder_1', 'elbow_1', 'wrist_1', 'wrist_2']" \
    -p positions:="[0.5, 0.5, 0.2, 0.0]" \
    -p duration:=2.0
```

### Parameters

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `joints` | Yes | — | List of joint names to move |
| `positions` | Yes | — | Target positions (radians), one per joint |
| `duration` | No | `2.0` | Seconds to reach the target |
| `topic` | No | `/joint_trajectory_controller/joint_trajectory` | Trajectory topic to publish on |

### Behavior

The node waits (polling every 0.5 s) until at least one subscriber is connected before publishing. This means it will wait automatically if Genesis hasn't finished loading yet.

### Examples

```bash title="Terminal"
# Move two joints
ros2 run sim_common move_joints --ros-args \
    -p joints:="['shoulder_1', 'elbow_1']" \
    -p positions:="[1.0, -0.5]" \
    -p duration:=3.0

# Move one joint slowly
ros2 run sim_common move_joints --ros-args \
    -p joints:="['wrist_1']" \
    -p positions:="[0.8]" \
    -p duration:=5.0
```
