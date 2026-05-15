#!/bin/bash

# Gazebo plugin search path
export GZ_SIM_SYSTEM_PLUGIN_PATH="${CONDA_PREFIX}/lib${GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}"

# Switch to Cyclone DDS
# Fast-DDS calls pthread_setaffinity_np which macOS doesn't support
# flooding the log with 'Protocol family not supported' errors on
# every DDS thread startup
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
