"""
ROS2 node that publishes a JointTrajectory message to move robot joints.
Usage documented in `docs/joint-moving.md`
"""

import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class MoveJoints(Node):
    """Main class"""

    def __init__(self):
        super().__init__("move_joints")

        self.declare_parameter("joints", rclpy.Parameter.Type.STRING_ARRAY)
        self.declare_parameter("positions", rclpy.Parameter.Type.DOUBLE_ARRAY)
        self.declare_parameter("duration", 2.0)
        self.declare_parameter("topic", "/joint_trajectory_controller/joint_trajectory")

        joint_names = self.get_parameter("joints").get_parameter_value().string_array_value
        positions = self.get_parameter("positions").get_parameter_value().double_array_value
        duration = self.get_parameter("duration").get_parameter_value().double_value
        topic = self.get_parameter("topic").get_parameter_value().string_value

        if len(joint_names) == 0:
            self.get_logger().error(
                "No joints specified. Use -p joints:=\"['joint-1', 'joint-2']\""
            )
            raise SystemExit(1)

        if len(positions) == 0:
            self.get_logger().error('No positions specified. Use -p positions:="[0.5, 0.2]"')
            raise SystemExit(1)

        if len(joint_names) != len(positions):
            self.get_logger().error(
                f"Joint count ({len(joint_names)}) != position count ({len(positions)})"
            )
            raise SystemExit(1)

        publisher = self.create_publisher(JointTrajectory, topic, 10)

        sec = int(duration)
        nanosec = int((duration - sec) * 1e9)

        msg = JointTrajectory()
        msg.joint_names = list(joint_names)
        point = JointTrajectoryPoint()
        point.positions = list(positions)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)
        msg.points = [point]

        self.msg = msg
        self.publisher = publisher
        self.timer = self.create_timer(0.5, self._publish)

    def _publish(self):
        if self.publisher.get_subscription_count() > 0:
            self.publisher.publish(self.msg)
            self.get_logger().info(
                f"Published trajectory to {self.publisher.topic_name}: "
                f"joints={self.msg.joint_names}, "
                f"positions={list(self.msg.points[0].positions)}"
            )
            raise SystemExit(0)


def main(args=None):
    """Main method"""
    rclpy.init(args=args)
    node = MoveJoints()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
