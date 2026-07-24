---
title: Launch System
description: How the ROS 2 launch files orchestrate Gazebo, controllers, RViz, and the Joint GUI.
---

Each robot has a launch file at `robot-sim/<robot>_bringup/launch/<robot>.launch.py` that orchestrates the full simulation startup. This page explains the architecture using the arm as an example.

## Launch arguments

| Argument | Default | Description |
| --- | --- | --- |
| `rviz` | `true` | Open RViz with the robot's config file |
| `gui` | `true` | Open the Joint GUI |

These are set via command line:

```bash title="Terminal"
ros2 launch arm_bringup arm.launch.py gui:=false rviz:=false
```

## Startup sequence

The launch file orchestrates several components with specific ordering dependencies:

```
1. Gazebo Simulator
   Start gz_sim with the world file and GUI config
   ↓
2. Spawn Robot + Robot State Publisher (parallel)
   - Spawn the URDF model into Gazebo
   - Start robot_state_publisher with the URDF
   ↓ (waits for spawn to finish)
3. Joint State Broadcaster
   Starts reading joint states from Gazebo
   ↓ (waits for broadcaster to finish)
4. Joint Trajectory Controller
   Accepts trajectory commands and drives joints

5. ROS-Gazebo Bridge, RViz, Joint GUI (parallel)
   - Bridge /clock between Gazebo and ROS
   - Open RViz with saved config
   - Open Joint GUI with URDF file
```

The robot spawn uses a `TimerAction` with a 5-second delay to give Gazebo time to fully initialize before the model is spawned. Steps 3 and 4 use `RegisterEventHandler` with `OnProcessExit` to enforce ordering -- the trajectory controller can't start until the state broadcaster is ready, and the broadcaster can't start until the robot is spawned.

## Components

### Gazebo simulation

```python
gz_sim = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
    ),
    launch_arguments={
        "gz_args": " ".join(["-r", world_file, "--gui-config", gz_gui_config])
    }.items(),
)
```

Launches Gazebo Harmonic with:
- `-r` -- start running immediately (not paused)
- The world SDF file from `sim_worlds` (default: `empty.world.sdf`)
- A custom GUI config from `sim_worlds/gui/gui.config`

### URDF processing

```python
robot_desc = xacro.process_file(
    urdf_file,
    mappings={"controller_config": controller_config},
).toxml()
```

The URDF is processed through xacro at launch time. The `controller_config` mapping passes the path to the controller YAML so the control xacro can reference it. The result is a fully resolved URDF string used for both spawning and state publishing.

### Robot spawn

```python
spawn_robot = Node(
    package="ros_gz_sim",
    executable="create",
    arguments=["-name", "arm", "-string", robot_desc, "-x", "0", "-y", "0", "-z", "0.1"],
)
```

Spawns the robot into the Gazebo world from the processed URDF string. The `-z 0.1` offset prevents the robot from spawning inside the ground plane.

### Robot state publisher

```python
robot_state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    parameters=[{"robot_description": robot_desc}],
)
```

Publishes the robot's TF tree and makes the URDF available on the `/robot_description` topic. RViz uses this to render the robot model.

### Controllers

Two controllers are spawned in sequence:

1. **`joint_state_broadcaster`** -- reads joint states from Gazebo hardware interfaces and publishes them to `/joint_states`
2. **`joint_trajectory_controller`** -- listens for `JointTrajectory` messages on `/joint_trajectory_controller/joint_trajectory` and commands Gazebo to move the joints

The controller configuration lives in `config/<robot>.controller.yaml`:

```yaml
controller_manager:
  ros__parameters:
    use_sim_time: true
    update_rate: 60 # Hz

joint_trajectory_controller:
  ros__parameters:
    joints:
      - shoulder_1
      - elbow_1
      - wrist_1
      - wrist_2
    command_interfaces:
      - position
    state_interfaces:
      - position
      - velocity
```

### ROS-Gazebo bridge

```python
bridge = Node(
    package="ros_gz_bridge",
    executable="parameter_bridge",
    arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
)
```

Bridges the `/clock` topic from Gazebo to ROS 2. This is essential for `use_sim_time: true` -- without it, ROS nodes won't have synchronized time with the simulation.

### RViz

Launches RViz2 with a saved config file. Conditional on the `rviz` launch argument.

### Joint GUI

Launches the Tkinter joint control GUI with the URDF file path as an argument. Conditional on the `gui` launch argument.

## launch_utils.py

The `sim_common` package provides a `get_asset()` helper used throughout launch files:

```python
from sim_common.launch_utils import get_asset

controller_config = get_asset("arm_bringup", "config", "arm.controller.yaml")
```

It resolves a file path inside a ROS 2 package's share directory and exits with an error if the file doesn't exist. This catches missing files early rather than failing mid-launch.

## Writing a custom launch file

If you need to customize a robot's launch beyond what `sim create` generates:

1. Edit `robot-sim/<robot>_bringup/launch/<robot>.launch.py`
2. The file is standard ROS 2 launch Python -- you can add nodes, change parameters, or modify the startup sequence
3. `sim update` will **not** overwrite your launch file changes

Common customizations:
- Adding sensor bridges (cameras, lidar)
- Changing spawn position
- Adding additional ROS 2 nodes
- Modifying controller parameters
