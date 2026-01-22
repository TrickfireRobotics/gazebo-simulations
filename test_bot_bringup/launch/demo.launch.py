"""
demo.launch.py - ROS launch file
https://roboticsbackend.com/ros2-launch-file-example/
https://www.youtube.com/watch?v=xJ3WAs8GndA&
"""

from launch_ros.actions import Node
from launch import LaunchDescription


def generate_launch_description():
    """
    A ROS method, has to have this excact name
    """

    ld = LaunchDescription()

    talker_node = Node(
        package="demo_node_cpp",
        executable="talker",
    )

    listener_node = Node(
        package="demo_nodes_py",
        executable="listener",
    )

    ld.add_action(talker_node)
    ld.add_action(listener_node)

    return ld
