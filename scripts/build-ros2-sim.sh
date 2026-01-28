#!/bin/bash

# --------------------------------------------------------------------------------------------
# build-ros2-sim.sh
# --------------------------------------------------------------------------------------------
# Builds the ROS 2 Gazebo simulation workspace, sets up the environment,
# registers custom Gazebo models, and launches the ROS2 robot simulation.
# --------------------------------------------------------------------------------------------

# Checkout Sim template folder
cd /home/trickfire/gazebo-simulations/robot-sim || exit 1

# Build all of the folders Within our Folder
colcon build --cmake-args -DBUILD_TESTING=ON

# Give setup script executable perms
chmod a+x install/setup.bash

# Source our newly build dependencies
source install/setup.bash

# Source models
export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:$(pwd)/install/models_and_worlds/share/models_and_worlds/models

# Launch simulations
ros2 launch Launch_files diff_drive.launch.py
