#!/bin/bash

# Deletes the files that ROS build, to prevent unexplainable issues.
# NOTE: This script is also ran as the 'postCreateCommand' for this devcontainer
# ------------------------------------------------------------------------------

cd /home/trickfire/gazebo-simulations/robot-sim || exit 1
echo "Deleting ROS build files..."
rm -r \
    log/ \
    build/ \
    install/
echo "Done!"
