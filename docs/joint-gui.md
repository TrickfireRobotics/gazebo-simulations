# joint-gui - joint-gui that controls joint states and sends commands via ros2

'joint-gui' is a gui that runs when we launch the simulation. The gui takes in a urdf model as an argument, parses all of the joints which are of type revolute then builds the gui components.

## Overview

When we run the launch script we pass the urdf file as an argument. It can be disabled via passing the `--no-gui` to the launch script.

The gui is handled during the rest of the bringup process as part of the ros2 launch description.

### Bringup Pipeline

```
Call launch script
1. Construct the joint controller module. Parse the urdf find all the revolute joint types, then find the min and max angles and store them internally.
  |
  v
2. Polls all of the joints, if joints are found then we get the origin angle and open the thread to allow for the gui to continue.
  |
  v
3. Begin building the GUI with the current available joints. We continue to poll as the program runs to add new joints to the application.
  |
  v
4. After that we start a thread to handle the publishing, the main thread handles UI updates.

```

### Publishing via ROS2

Everytime you hit the send command, the gui sends ros2 publish commands to each individual ros2 topic with the updated joint values.
