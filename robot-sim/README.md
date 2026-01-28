## System breakdown

This project folder is soley responsible for the system and what files are within it. This project is based off ROS2 Gazebo template project. Link below. Documentation is also provided for this project template however to make it more readable I renamed the folders to make a little more sense.

[Template Repo](https://github.com/gazebosim/ros_gz_project_template)

[Documentation](https://gazebosim.org/docs/latest/ros_gz_project_template_guide/)

### How it works

Each of the folders in this project directory are based on a different folder from the original project

`Gazebo_code`: Originally `ros_gz_example_gazebo` for gazebo specific configurations and code

` Launch_files`: Originally `ros_gz_example_bringup` for launch files corresponding to each model we are trying to include

`Models_and_worlds`: Originally `ros_gz_example_description` which contains the config files and sdf files to configure the models we want to launch.

`Ros_configs`: Originally `ros_gz_example_application` which holds ros2 specific code and configurations for custom plugins or general Ros2 code

## Issues and important build details

While I was working on this there were a few things I noticed that were important to keep in mind as you work on this.

When you build the project or add packages, make sure to update the `package.xml` and `CMakeLists.txt` In each of the respective folders. Each package needs these in their code to be included in the build. These signal to the colcon build system that a package has been added or modified. Additionally in the XML make sure to properly include the dependencies so colcon can properly build the packages in their required order.
