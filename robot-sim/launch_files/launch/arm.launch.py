"""
Launch script for the robot arm simulation
"""

import os

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
    """Log function for this launch file"""
    print("\033[0;35m", "[INFO] [launch]: ", log_msg, "\x1b[0m", sep="")


def generate_launch_description():
    """ROS launch method, must have this name"""

    # ----------------------------------------------
    # Locate project package directories
    # ----------------------------------------------

    # World and model files
    pkg_models_and_worlds = get_package_share_directory("models_and_worlds")
    # Gazebo GUI config
    pkg_gz_code = get_package_share_directory("gazebo_code")
    # RVIZ and bridge configs
    pkg_launch_files = get_package_share_directory("launch_files")

    # ----------------------------------------------
    # Build paths to required files
    # ----------------------------------------------

    # Build the path to the model URDF file
    urdf_file = os.path.join(pkg_models_and_worlds, "models", "arm", "arm.urdf")
    log("URDF model file: " + urdf_file)
    with open(urdf_file, "r", encoding="UTF-8") as infp:
        robot_desc = infp.read()

    # Build the path to Gazebo world file
    world_file = os.path.join(pkg_models_and_worlds, "worlds", "arm_world.sdf")
    log("Gazebo world file: " + world_file)

    # Build the path to Gazebo GUI config
    gz_gui_config_file = os.path.join(pkg_gz_code, "gui", "gui.config")
    log("Gazebo GUI config file: " + gz_gui_config_file)

    # Build the path to RVIZ config
    rviz_config_file = os.path.join(pkg_launch_files, "config", "arm.rviz")
    log("RVIZ config file: " + rviz_config_file)

    # Build the path to the YAML bridge mappings
    bridge_file = os.path.join(pkg_launch_files, "config", "arm_gz_ros_bridge.yaml")
    log("Bridge YAML definition file: " + bridge_file)

    robot_controllers_file = os.path.join(
        pkg_launch_files, "config", "arm_controller.yaml"
    )
    log("Robot controllers definition file: " + robot_controllers_file)

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
            "gz_args": " ".join(["-r", world_file, "--gui-config", gz_gui_config_file])
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
            robot_controllers_file,
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
            rviz_config_file,
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
        parameters=[
            {
                "config_file": bridge_file,
            }
        ],
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
