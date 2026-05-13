#!/usr/bin/env python3
"""Genesis physics simulation node.

Loads a robot URDF into Genesis, steps physics, and bridges to ROS 2:
  - Publishes /joint_states (sensor_msgs/JointState) at ~60 Hz
  - Subscribes to /joint_trajectory_controller/joint_trajectory (trajectory_msgs/JointTrajectory)

Architecture (mirrors genesis-sim PoC branch):
  - Main thread: Genesis scene.step() loop (required when show_viewer=True)
  - Background thread: MultiThreadedExecutor spinning ROS callbacks
"""

import os
import re
import signal
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, cast

import genesis as gs
import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory


def _resolve_urdf(robot_name: str) -> str:
    """Expand xacro URDF and resolve package:// URIs to absolute paths.

    Returns path to a temp file Genesis can load directly.
    """
    import xacro

    pkg_dir = get_package_share_directory(robot_name)
    urdf_xacro = os.path.join(pkg_dir, "urdf", f"{robot_name}.urdf")

    robot_desc = xacro.process_file(urdf_xacro).toxml()

    def _replace_pkg(m: re.Match) -> str:
        try:
            pkg = get_package_share_directory(m.group(1))
        except Exception:  # pylint: disable=broad-except
            return m.group(0)
        return str(Path(pkg) / m.group(2))

    robot_desc = re.sub(r"package://([^/]+)/(.+?)(?=\")", _replace_pkg, robot_desc)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".urdf", delete=False, prefix=f"{robot_name}_genesis_"
    )
    tmp.write(robot_desc)
    tmp.close()
    return tmp.name


class GenesisSim(Node):
    """ROS 2 node that drives a Genesis scene and bridges joint state I/O."""

    _PUBLISH_HZ = 60

    def __init__(
        self, robot_name: str, urdf_path: str, show_viewer: bool = True
    ) -> None:
        super().__init__("genesis_sim")

        self._lock = threading.Lock()
        self._pending_positions: dict[str, float] = {}

        backend: Any = cast(Any, gs.gpu)  # default to GPU if available

        gs.init(backend=backend, logging_level="warning")

        self._scene = gs.Scene(
            rigid_options=gs.options.RigidOptions(
                dt=1.0 / self._PUBLISH_HZ,
                gravity=(0.0, 0.0, -9.81),
            ),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(3.5, 0.0, 2.5),
                camera_lookat=(0.0, 0.0, 0.5),
                camera_fov=40,
                run_in_thread=False,
            ),
            profiling_options=gs.options.ProfilingOptions(show_FPS=True),
            show_viewer=show_viewer,
        )

        self._scene.add_entity(gs.morphs.Plane())
        self._robot = self._scene.add_entity(
            gs.morphs.URDF(
                file=urdf_path,
                pos=(0.0, 0.0, 0.05),
                quat=(1.0, 0.0, 0.0, 0.0),
                fixed=True,
            )
        )
        self._scene.build()

        # Joints that have DOFs (i.e. not fixed)
        self._controllable_joints = [
            j for j in self._robot.joints if len(j.dofs_idx_local) > 0
        ]
        joint_names = [j.name for j in self._controllable_joints]
        self.get_logger().info(
            f"Genesis loaded '{robot_name}' — controllable joints: {joint_names}"
        )

        self._pub = self.create_publisher(JointState, "/joint_states", 10)
        self.create_subscription(
            JointTrajectory,
            "/joint_trajectory_controller/joint_trajectory",
            self._on_trajectory,
            10,
        )

    # ROS callbacks (run in executor thread)
    def _on_trajectory(self, msg: JointTrajectory) -> None:
        if not msg.points:
            return
        positions = list(msg.points[0].positions)
        with self._lock:
            for name, pos in zip(msg.joint_names, positions):
                self._pending_positions[name] = pos

    # Simulation step (called from main thread)
    def step(self) -> None:
        """Advance the simulation by one step, applying any pending joint commands"""
        self._apply_commands()
        self._scene.step()
        self._publish_joint_states()

    def _apply_commands(self) -> None:
        with self._lock:
            pending = dict(self._pending_positions)

        for joint in self._controllable_joints:
            if joint.name in pending:
                self._robot.control_dofs_position(
                    np.array([pending[joint.name]]),
                    joint.dofs_idx_local,
                )

    def _publish_joint_states(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        for joint in self._controllable_joints:
            try:
                pos = self._robot.get_dofs_pos(joint.dofs_idx_local).flatten().tolist()
            except Exception:  # pylint: disable=broad-except  # type: ignore
                pos = [0.0] * len(joint.dofs_idx_local)
            msg.name.append(joint.name)
            msg.position.extend(pos)
        self._pub.publish(msg)

    @property
    def viewer_alive(self) -> bool:
        """Check if Genesis viewer is still alive (if enabled)"""
        return self._scene.viewer is None or self._scene.viewer.is_alive()


def main() -> None:
    """Main method"""
    if len(sys.argv) < 2:
        print("Usage: genesis_sim <robot_name> [--headless]", file=sys.stderr)
        sys.exit(1)

    robot_name = sys.argv[1]
    show_viewer = "--headless" not in sys.argv

    rclpy.init()
    urdf_path = _resolve_urdf(robot_name)
    node = GenesisSim(robot_name, urdf_path, show_viewer=show_viewer)

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    ros_thread = threading.Thread(target=executor.spin, daemon=True)
    ros_thread.start()

    _shutdown = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: _shutdown.set())
    signal.signal(signal.SIGTERM, lambda *_: _shutdown.set())

    try:
        while rclpy.ok() and node.viewer_alive and not _shutdown.is_set():
            node.step()
    finally:
        executor.shutdown(timeout_sec=2.0)
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
