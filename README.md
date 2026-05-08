# Gazebo Simulations

Gazebo Fortress simulations for TrickFire Robotics robot subsystems, running on ROS 2 Humble inside a Docker Dev Container.

## `Documentation`

**Full documentation is at [trickfirerobotics.com/gazebo-simulations](https://trickfirerobotics.com/gazebo-simulations)**

- [Getting Started](https://trickfirerobotics.com/gazebo-simulations/guides/getting-started/) - setup, Dev Container, display, first launch
- [Running Simulations](https://trickfirerobotics.com/gazebo-simulations/guides/running-simulations/) - `launch_sim.sh` usage and flags
- [Moving Joints](https://trickfirerobotics.com/gazebo-simulations/guides/moving-joints/) - Joint GUI and `move_joints` CLI node
- [Adding a New Robot](https://trickfirerobotics.com/gazebo-simulations/guides/adding-robots/) - genbot + OnShape pipeline
- [Reference](https://trickfirerobotics.com/gazebo-simulations/reference/ros-workspace/) - scripts, genbot, launch system, Docker environment in depth

## Optional macOS native setup


An optional, opt-in native macOS setup is included under `macos/` for users who prefer to run ROS 2 + Gazebo natively on macOS (this was originally contributed to support macOS development).

- **Non-destructive:** This is strictly optional and does not replace or modify existing Linux or containerized workflows.
- **How to use:** On macOS, run `scripts/macos_setup.sh` to create the environment and build the native stack, then use `scripts/macos_gui.sh` to open the GUI.
- **When to use:** Use this only on macOS machines where you want a native micromamba-based ROS 2 + Gazebo stack instead of the Docker dev container.

If you are using Linux or the provided Docker container, continue to use the existing setup and launch scripts described above.
