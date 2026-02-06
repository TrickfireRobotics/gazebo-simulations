#!/bin/bash

cd /home/trickfire/gazebo-simulations/robot-sim || exit 1
echo "Deleting ROS build files..."
rm -r \
    log/ \
    build/ \
    install/
echo "Done!"
