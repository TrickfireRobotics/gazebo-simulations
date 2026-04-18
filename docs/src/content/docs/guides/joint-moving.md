---
title: Moving Robot Joints
description: Use the move_joints node to send joint trajectory commands to any robot in the simulation.
---

# Moving Robot Joints

Use the `move_joints` node from `sim_common` to send joint trajectory commands to any robot in the simulation.

## Usage

```bash
ros2 run sim_common move_joints --ros-args \
    -p joints:="['shoulder_1', 'elbow_1', 'wrist_1', 'wrist_2']" \
    -p positions:="[0.5, 0.5, 0.2, 0.0]" \
    -p duration:=2.0
```

## Parameters

| Parameter   | Required | Default                                         | Description                          |
| ----------- | -------- | ----------------------------------------------- | ------------------------------------ |
| `joints`    | Yes      | -                                               | List of joint names to move          |
| `positions` | Yes      | -                                               | Target positions (radians) per joint |
| `duration`  | No       | `2.0`                                           | Time to reach the target (seconds)   |
| `topic`     | No       | `/joint_trajectory_controller/joint_trajectory` | Trajectory topic to publish on       |

## Arm Example

With the arm simulation running (`./scripts/launch_sim.sh arm`):

```bash
# Move shoulder and elbow
ros2 run sim_common move_joints --ros-args \
    -p joints:="['shoulder_1', 'elbow_1', 'wrist_1', 'wrist_2']" \
    -p positions:="[0.5, 0.5, 0.2, 0.0]" \
    -p duration:=2.0
```

The node waits for the trajectory controller to be ready, publishes the command, and exits.
