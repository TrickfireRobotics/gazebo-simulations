"""
Launch script for the robot arm simulation
"""

import os
import sys
from pathlib import Path

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
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
    world_file = get_asset("sim_worlds", "worlds", "empty.world.sdf")
    rviz_config = get_asset("arm_bringup", "config", "arm.rviz")
    urdf_file = get_asset("arm_description", "urdf", "arm.urdf")
    gz_gui_config = get_asset("sim_worlds", "gui", "gui.config")

    # ----------------------------------------------
    # xacro generate URDF
    # ----------------------------------------------

    robot_desc = xacro.process_file(
        urdf_file,
        mappings={"controller_config": controller_config},
    ).toxml()

    # ----------------------------------------------
    # Gazebo launch arguments
    # ----------------------------------------------

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={
            "gz_args": " ".join(["-r", world_file, "--gui-config", gz_gui_config])
        }.items(),
    )

    # ----------------------------------------------
    # Gazebo spawn model
    # ----------------------------------------------

    # Uses the ros_gz_sim 'create' node to send the URDF string to
    # Gazebo’s spawn service and place the robot at a given pose
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "arm",
            "-string",
            robot_desc,
            "-x",
            "0",
            "-y",
            "0",
            "-z",
            "0.1",
        ],
        output="screen",
    )

    # ----------------------------------------------
    # Robot state publisher
    # ----------------------------------------------
    # Publishes robot transforms

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": robot_desc}],
    )

    # ----------------------------------------------
    # Joint controllers
    # ----------------------------------------------
    # Controlls the arm joints

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
        ],
    )
    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--param-file",
            controller_config,
        ],
    )

    # ----------------------------------------------
    # RVIZ
    # ----------------------------------------------

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d",
            rviz_config,
        ],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    # ----------------------------------------------
    # ROS GZ BRIDGE
    # ----------------------------------------------
    # Bridges ROS topics and Gazebo messages

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # ----------------------------------------------
    # Return the final launch description
    # Will be executed in order (order matters)
    return LaunchDescription(
        [
            gz_sim,
            spawn_robot,
            robot_state_publisher,
            DeclareLaunchArgument(
                "rviz", default_value="true", description="Open RViz."
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=spawn_robot,
                    on_exit=[joint_state_broadcaster_spawner],
                )
            ),
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=joint_state_broadcaster_spawner,
                    on_exit=[joint_trajectory_controller_spawner],
                )
            ),
            bridge,
            rviz,
        ]
    )
