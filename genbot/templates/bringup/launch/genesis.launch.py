"""
Launch script for the Genesis __ROBOT__ simulation
"""

import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from sim_common.launch_utils import get_asset


def generate_launch_description():
    """ROS launch method, must have this name"""

    controller_config = get_asset("__ROBOT___bringup", "config", "__ROBOT__.controller.yaml")
    urdf_file = get_asset("__ROBOT___description", "urdf", "__ROBOT__.urdf")

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
        package="__ROBOT___bringup",
        executable="genesis_sim",
        name="genesis_sim",
        output="screen",
        parameters=[{"robot_description": robot_desc}],
    )

    return LaunchDescription([genesis_sim])
