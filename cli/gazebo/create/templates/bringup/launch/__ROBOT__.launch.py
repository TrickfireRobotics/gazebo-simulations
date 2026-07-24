"""
Launch script for the Gazebo __ROBOT__ simulation
"""

import os
import shutil
import subprocess
import sys

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from sim_common.launch_utils import get_asset


def _gz_supports_sim_command():
    """Return True when `gz` exists and exposes the `sim` subcommand."""
    if shutil.which("gz") is None:
        return False

    try:
        result = subprocess.run(
            ["gz", "--commands"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False

    commands = result.stdout.splitlines()
    return any(line.strip() == "sim" for line in commands)


def generate_launch_description():
    """ROS launch method, must have this name"""

    controller_config = get_asset("__ROBOT___bringup", "config", "__ROBOT__.controller.yaml")
    world_file = get_asset("sim_worlds", "worlds", "empty.world.sdf")
    rviz_config = get_asset("__ROBOT___bringup", "config", "__ROBOT__.rviz")
    urdf_file = get_asset("__ROBOT___description", "urdf", "__ROBOT__.urdf")
    gz_gui_config = get_asset("sim_worlds", "gui", "gui.config")

    # ----------------------------------------------
    # xacro generate URDF
    # ----------------------------------------------

    robot_desc = xacro.process_file(
        urdf_file,
        mappings={
            "controller_config": controller_config,
            "plugin_extension": ".dylib" if sys.platform == "darwin" else ".so",
        },
    ).toxml()

    # ----------------------------------------------
    # Gazebo launch arguments
    # ----------------------------------------------

    use_split_gui = _gz_supports_sim_command()
    gz_server_args = (
        ["-r", "-s", world_file]
        if use_split_gui
        else ["-r", world_file, "--gui-config", gz_gui_config]
    )

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": " ".join(gz_server_args)}.items(),
    )

    gz_gui = ExecuteProcess(
        cmd=["gz", "sim", "--force-version", "8", "-g", "--gui-config", gz_gui_config],
        output="screen",
        condition=IfCondition(LaunchConfiguration("gui")),
    )

    # ----------------------------------------------
    # Gazebo spawn model
    # ----------------------------------------------

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "__ROBOT__",
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

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # ----------------------------------------------
    # Joint GUI
    # ----------------------------------------------

    joint_gui = Node(
        package="sim_common",
        executable="joint_gui",
        arguments=[urdf_file],
        condition=IfCondition(LaunchConfiguration("gui")),
        output="screen",
    )

    spawn_robot_delayed = TimerAction(period=5.0, actions=[spawn_robot])
    gz_gui_delayed = TimerAction(period=2.0, actions=[gz_gui])
    maybe_gui_action = gz_gui_delayed if use_split_gui else None

    return LaunchDescription(
        [
            gz_server,
            *([maybe_gui_action] if maybe_gui_action is not None else []),
            spawn_robot_delayed,
            robot_state_publisher,
            DeclareLaunchArgument("rviz", default_value="true", description="Open RViz."),
            DeclareLaunchArgument("gui", default_value="true", description="Open Joint GUI."),
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
            joint_gui,
        ]
    )
