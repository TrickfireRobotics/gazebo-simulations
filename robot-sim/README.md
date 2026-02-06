# ROS workspace breakdown

> [!NOTE]
> This workspace was based on an official Gazebo ROS workspace template. You can find the template [here](https://github.com/gazebosim/ros_gz_project_template). You can find the documentation and guide for the template [here](https://gazebosim.org/docs/latest/ros_gz_project_template_guide/).

## How it works

Every directory containing the `package.xml` file in this workspace is a package for ROS. The `xml` file hold information about the package, and it's dependencies. It also has a `CMakeList.txt` that contains the installation steps on how to install that package for ROS during the `colcon build` process.

### List of packages

- `gazebo_code`: Originally `ros_gz_example_gazebo` for gazebo specific configurations and code
- `launch_files`: Originally `ros_gz_example_bringup` for ROS Python launch files
- `models_and_worlds`: Originally `ros_gz_example_description` for `stl` 3D source models, `urdf` files and `sdf` model/world files
- `ros_configs`: Originally `ros_gz_example_application` which holds ROS specific code and configurations for custom plugins or general ROS2 code

## Issues and important build details

> [!TIP]
> If you get an error that you don't know what caused it, delete the ROS build files and rebuild the project. There is a script to do this automatically: `./scripts/delete_ros_build_files.sh`. It usually fixes the issue.

While I was working on this there were a few things I noticed that were important to keep in mind as you work on this:

When you build the project or add packages, make sure to update the `package.xml` and `CMakeLists.txt` In each of the respective folders. Each package needs these in their code to be included in the build. These signal to the colcon build system that a package has been added or modified. Additionally in the XML make sure to properly include the dependencies so colcon can properly build the packages in their required order.
