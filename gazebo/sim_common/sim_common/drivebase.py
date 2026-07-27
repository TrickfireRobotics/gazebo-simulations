"""
Sim equivalent of the real rover's drivebase node
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Float64MultiArray

# matches urc-2023/src/drivebase/drivebase/drivebase.py so a given joystick
# deflection produces the same wheel speed on the sim as on the real rover
SPEED = 6.28 * 1.5  # rad/s

# order must match the joints list in chassis_bringup/config/chassis.controller.yaml
WHEEL_ORDER = ["fl_wheel", "ml_wheel", "bl_wheel", "fr_wheel", "mr_wheel", "br_wheel"]
LEFT_WHEELS = ("fl_wheel", "ml_wheel", "bl_wheel")
RIGHT_WHEELS = ("fr_wheel", "mr_wheel", "br_wheel")


class Drivebase(Node):
    """Main class"""

    def __init__(self):
        super().__init__("drivebase")

        self.wheel_velocity = dict.fromkeys(WHEEL_ORDER, 0.0)

        self.command_pub = self.create_publisher(
            Float64MultiArray, "/forward_velocity_controller/commands", 10
        )

        self.create_subscription(Float32, "move_left_drivebase_side_message", self._on_left, 10)
        self.create_subscription(Float32, "move_right_drivebase_side_message", self._on_right, 10)

    def _on_left(self, msg: Float32) -> None:
        vel = msg.data * SPEED
        for wheel in LEFT_WHEELS:
            self.wheel_velocity[wheel] = vel
        self._publish()

    def _on_right(self, msg: Float32) -> None:
        vel = msg.data * SPEED
        for wheel in RIGHT_WHEELS:
            self.wheel_velocity[wheel] = -vel
        self._publish()

    def _publish(self) -> None:
        msg = Float64MultiArray()
        msg.data = [self.wheel_velocity[wheel] for wheel in WHEEL_ORDER]
        self.command_pub.publish(msg)


def main(args=None):
    """Main method"""
    rclpy.init(args=args)
    node = Drivebase()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
