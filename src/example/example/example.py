import sys


import rclpy  # Import the package
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from std_msgs.msg import String

class ExampleNode(Node):

    def __init__(self) -> None:
        # Call the parent's constructor and pass in the node's name
        super().__init__("my_example_node")
        