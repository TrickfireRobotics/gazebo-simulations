#!/bin/bash

set -e

# --------------------------------------------------------------------------------------------
# build_ros2_sim.sh
# --------------------------------------------------------------------------------------------
# Purpose:
#   Builds the ROS 2 Gazebo simulation workspace, configures the environment,
#   registers custom Gazebo models, and launches the robot simulation.
#
# Responsibilities:
#   - Set up paths and logging
#   - Build ROS 2 workspace using colcon
#   - Validate and source the generated environment
#   - Register Ignition Gazebo model resources
#   - Launch the simulation
# --------------------------------------------------------------------------------------------


# Resolve project root directory (parent dir of the dir the script is in)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Workspace path
ROBOT_SIM_DIR="$PROJECT_DIR/robot-sim"

# Log file path
LOG_DIR="$ROBOT_SIM_DIR/log"
LOG_PATH="$LOG_DIR/script_log-$(date +'%Y-%m-%d_%H-%M').log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Redirect all output to terminal and log file
exec > >(tee -a "$LOG_PATH") 2>&1

# Move into the ROS 2 workspace directory
cd "$ROBOT_SIM_DIR"

# --------------------------------------------------------------------------------------------

# Build ROS 2 workspace
echo "Building ROS 2 workspace..."
colcon build --cmake-args -DBUILD_TESTING=ON

# Ensure the setup script was generated successfully
if [ ! -f install/setup.bash ]; then
    echo "Error: install/setup.bash not found! The build may have failed"
    exit 1
fi

# Give exec perms to script
chmod a+x install/setup.bash

# Source ROS env
echo "Sourcing ROS 2 environment..."
source install/setup.bash

# --------------------------------------------------------------------------------------------

# Register Ignition Gazebo models, append the model path to Gazebo res path
MODEL_PATH="$ROBOT_SIM_DIR/install/models_and_worlds/share/models_and_worlds/models"

export IGN_GAZEBO_RESOURCE_PATH="${IGN_GAZEBO_RESOURCE_PATH:+$IGN_GAZEBO_RESOURCE_PATH:}$MODEL_PATH"

echo "IGN_GAZEBO_RESOURCE_PATH set to:"
echo "  $IGN_GAZEBO_RESOURCE_PATH"

# Launch simulation
echo "Launching ROS 2 simulation..."
ros2 launch launch_files arm.launch.py
