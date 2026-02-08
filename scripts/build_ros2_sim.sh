#!/bin/bash

# --------------------------------------------------------------------------------------------
# build_ros2_sim.sh
# --------------------------------------------------------------------------------------------
# Builds the ROS 2 Gazebo simulation workspace, sets up the environment,
# registers custom Gazebo models, and launches the ROS2 robot simulation.
# --------------------------------------------------------------------------------------------

cd /home/trickfire/gazebo-simulations/scripts/log/
logFile="log-$(date +'%Y-%m-%d_%H-%M').log"

exec > >(tee -a "$logFile") 2>&1

cd /home/trickfire/gazebo-simulations/robot-sim || exit 1

# Build our robot files using the ROS build tool
colcon build --cmake-args -DBUILD_TESTING=ON

# Give generated ROS setup script executable perms
chmod a+x install/setup.bash

# Source our newly build dependencies
source install/setup.bash

# Source models
export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:$(pwd)/install/models_and_worlds/share/models_and_worlds/models

# Launch simulations
ros2 launch Launch_files arm.launch.py
