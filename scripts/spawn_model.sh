# from https://gazebosim.org/docs/latest/ros2_spawn_model/

ros2 launch ros_gz_sim gz_spawn_model.launch.py \
 world:=empty \
 file:=/home/trickfire/gazebo-simulations/ros2_ws/src/rover_description/models/tfr_bot.sdf \
 entity_name:=my_vehicle \
 x:=5.0 y:=5.0 z:=0.5
