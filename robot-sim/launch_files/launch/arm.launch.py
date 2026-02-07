"""
Launch script for the robot arm simulation
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
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
    pkg_project_bringup = get_package_share_directory("launch_files")

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
    rviz_config_file = os.path.join(pkg_project_bringup, "config", "arm.rviz")
    log("RVIZ config file: " + rviz_config_file)

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
    # Action nodes
    # ----------------------------------------------

    # Uses the ros_gz_sim 'create' node to send the URDF string to
    # Gazebo’s spawn service and place the robot at a given pose
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "my_arm",
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

    # Publish robot transforms using robot_state_publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": robot_desc}],
    )

    # GUI for tweaking joint values
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        arguments=[urdf_file],
        output=["screen"],
    )

    # RVIZ
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

    # Bridge ROS topics and Gazebo messages
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    pkg_project_bringup, "config", "ros_gz_example_bridge.yaml"
                ),
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        output="screen",
    )

    # Return the final launch description
    # Will be executed in order (order matters)
    return LaunchDescription(
        [
            gz_sim,
            DeclareLaunchArgument(
                "rviz", default_value="true", description="Open RViz."
            ),
            bridge,
            spawn_robot,
            robot_state_publisher,
            joint_state_publisher_gui,
            rviz,
        ]
    )
