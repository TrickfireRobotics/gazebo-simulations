#!/bin/bash

cd /home/trickfire/gazebo-simulations/Robot-sim-template
colcon build --cmake-args -DBUILD_TESTING=ON
chmod a+x install/setup.sh
#Attempt to launch
ros2 launch ros_gz_example_bringup diff_drive.launch.py
