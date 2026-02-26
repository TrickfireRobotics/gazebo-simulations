"""
Launch script for the Genesis robot arm simulation
"""

import os
import sys
from pathlib import Path

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def log(log_msg):
    """Basic log"""
    print("\033[0;32m", "[INFO] [launch]: ", log_msg, "\x1b[0m", sep="")


def err(log_msg):
    """Error log"""
    print("\033[0;31m", "[ERROR] [launch]: ", log_msg, "\x1b[0m", sep="")
    sys.exit(1)


def get_asset(package, *parts):
    """Getter for assets"""
    pkg_dir = get_package_share_directory(package)
    path = os.path.join(pkg_dir, *parts)
    if not Path(path).exists():
        err(f"File {path} does not exist!")
    return path


def generate_launch_description():
    """ROS launch method, must have this name"""

    controller_config = get_asset("arm_bringup", "config", "arm.controller.yaml")
    urdf_file = get_asset("arm_description", "urdf", "arm.urdf")

    # ----------------------------------------------
    # xacro generate URDF
    # ----------------------------------------------

    robot_desc = xacro.process_file(
        urdf_file,
        mappings={"controller_config": controller_config},
    ).toxml()

    # ----------------------------------------------
    # Genesis simulation node
    # ----------------------------------------------

    genesis_sim = Node(
        package="arm_bringup",
        executable="genesis_sim",
        name="genesis_sim",
        output="screen",
        parameters=[{"robot_description": robot_desc}],
    )

    return LaunchDescription([genesis_sim])
