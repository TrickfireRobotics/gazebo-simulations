"""
Launch script for the arm.urdf model
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    """ROS launch method, must have this name"""

    # Locate the shared directory of the package that contains
    # models, URDFs, and world files
    pkg_models_and_worlds = get_package_share_directory("models_and_worlds")

    # Build the absolute path to the URDF file, then read its contents
    # so it can be passed directly to Gazebo and robot_state_publisher
    urdf_file = os.path.join(pkg_models_and_worlds, "models", "arm", "arm.urdf")
    with open(urdf_file, "r") as infp:
        robot_desc = infp.read()

    # Launch Gazebo Sim (ros_gz_sim)
    # This includes the Gazebo simulator launch file and starts an
    # empty world using gz_args
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
    )

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

    # Publish robot transforms (TF) using robot_state_publisher
    # This allows tools like RViz to visualize the robot and its joint
    # states based on the URDF model
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": robot_desc}],
    )

    # Return the final launch description
    # Order matters!! Gazebo starts first, then the robot is spawned,
    # then TF publishing begins
    return LaunchDescription([gz_sim, spawn_robot, robot_state_publisher])
