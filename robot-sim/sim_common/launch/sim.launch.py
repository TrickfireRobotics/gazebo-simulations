"""Sim launch file for ROS Genesis simulation"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from sim_common.launch_utils import get_asset


def _launch_setup(context):
    robot = LaunchConfiguration("robot").perform(context)
    gui = LaunchConfiguration("gui").perform(context).lower() == "true"
    headless = LaunchConfiguration("headless").perform(context).lower() == "true"

    urdf_file = get_asset(robot, "urdf", f"{robot}.urdf")

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": open(urdf_file, encoding="utf-8").read()}],
    )

    genesis_args = [robot]
    if headless:
        genesis_args.append("--headless")

    genesis_sim = Node(
        package="sim_common",
        executable="genesis_sim",
        arguments=genesis_args,
        output="screen",
    )

    joint_gui = Node(
        package="sim_common",
        executable="joint_gui",
        arguments=[urdf_file],
        output="screen",
    )

    webbridge = Node(package="sim_common", executable="web_bridge", output="screen")

    on_genesis_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=genesis_sim,
            on_exit=[EmitEvent(event=Shutdown())],
        )
    )

    nodes = [robot_state_publisher, genesis_sim, webbridge, on_genesis_exit]
    if gui:
        nodes.append(joint_gui)

    return nodes


def generate_launch_description():
    """ROS2 launch descriptions"""
    return LaunchDescription(
        [
            DeclareLaunchArgument("robot", description="Robot package name (e.g. arm)"),
            DeclareLaunchArgument(
                "gui", default_value="true", description="Launch the joint control GUI"
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                description="Run Genesis without a viewer window (use for VNC/CI)",
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
