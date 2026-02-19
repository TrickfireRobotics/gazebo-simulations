ros2 topic pub /joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- shoulder_1
- elbow_1
- wrist_1
- wrist_2

points:
- positions: [0.5, 0.5, 0.2, 0.0]
  time_from_start: {sec: 2}
"
