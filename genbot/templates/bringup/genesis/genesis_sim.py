#!/usr/bin/env python3

"""Node to control Genesis from ROS launch files"""

import os

import genesis as gs
import rclpy
from ament_index_python import get_package_share_directory
from rclpy.node import Node
import xacro


class GenesisSim(Node):
    """The Genesis Simulation Node"""

    def __init__(self):
        super().__init__("genesis_sim")

        # ----------------------------------------------
        # Genesis setup
        # ----------------------------------------------

        gs.init(backend=gs.cpu)  # pylint: disable=no-member

        self.scene = gs.Scene(show_viewer=True)

        self.scene.add_entity(gs.morphs.Plane())

        mesh_dir = get_package_share_directory("__ROBOT___description")

        urdf_dir = os.path.join(get_package_share_directory("__ROBOT___description"), "urdf")
        urdf_file = os.path.join(urdf_dir, "__ROBOT__.urdf")

        robot_desc = xacro.process_file(urdf_file).toxml()
        robot_desc = robot_desc.replace("package://__ROBOT___description/", f"{mesh_dir}/")

        # Write temp file next to the actual URDF so relative mesh paths resolve
        urdf_path = os.path.join(urdf_dir, "__ROBOT___resolved.urdf")
        with open(urdf_path, "w") as f:
            f.write(robot_desc)

        self.robot = self.scene.add_entity(gs.morphs.URDF(file=urdf_path))

        self.scene.build()

        # Step the sim on a timer (~60hz)
        self.create_timer(1.0 / 60.0, self.step)
        self.get_logger().info("Genesis simulation running")

    def step(self):
        """Step"""
        self.scene.step()


def main():
    """Main function"""
    rclpy.init()
    node = GenesisSim()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
