import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # 1. Setup paths
    pkg_models_and_worlds = get_package_share_directory("models_and_worlds")
    pkg_launch_files = get_package_share_directory("launch_files")

    # Path to your URDF
    urdf_file = os.path.join(pkg_models_and_worlds, "models", "arm", "arm.urdf")
    with open(urdf_file, "r") as infp:
        robot_desc = infp.read()

    # 2. Include the Gazebo Sim launch (starts the simulator)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),  
    )

    # 3. Spawn the model
    # Note: ros_gz_sim uses a 'create' node to interface with Gazebo's spawn service
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
            "0.1",  # spawn slightly above ground
        ],
        output="screen",
    )

    # 4. Robot State Publisher (optional but recommended for RViz)
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": robot_desc}],
    )

    return LaunchDescription([gz_sim, spawn_robot, robot_state_publisher])
