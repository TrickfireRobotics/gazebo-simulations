---
title: MacOS Native Setup
description: Guide on how to setup this simulation natively on MacOS
---

This guide is for MacOS systems only. It provides an optional native setup using micromamba to create the simulation environment fully locally, not using Docker at all. This is not required to run the simulations, but can be useful for users who want to people who want to run the simulation with better performance. Note that this is:

- **Size & Time:** This setup requires quide a bit of storage and time to build. On an M2 Air it takes about 10 to 15 minutes for the initial build, and the resulting `.macos/` build directory ends up being a little under **8GB**.
- **Non-destructive:** This setup does not install anythig on your system outside of the `.macos/` directory in the repository. You can remove the native setup by deleting it.
- **Works with the rest:** This way also does not break other ways of executing the sim (like in the devcontainer). There are scripts in place to remove any of the MaOS patches and `CMakeCaches`.

## How to use

This is really quite simple. I tried my best to make the setup one script that will handle everything for you so just run this:

```bash title="MacOS terminal"
./scripts/macos.sh <robot-name>
```

`<robot-name>` reffers to the robot package name, same as you would define it using the standard `launch_sim` script. Four windows should pop up when it finishes, Gazebo, RViz2, our custom joint gui python window and an empty window with a plain one color gray background named something like `OgreWidnow...`. You can close the last one, it is a parasitic window from a Gazebo renderer fail, it is fine trust me.

:::caution[Do not panic!]
There is going to be **A LOT** of errors when you're going to be building this for the first time, mainly `CMake` errors. Do not freak out, they are fine, everything is going to work. On the same note, when launching the simulation, you are going to get a Gazebo error in red, also ignore that, it is fine.
:::

## Notes & Troubleshooting

Some steps (mainly the `colcon build`) steps take very long with little to none output. Trust me, it is not hung! It really takes 5+ minutes, like for example for the `ros_gz` `colcon` build. I assure you that the program will exit on error.

If you get any errors using the `macos.sh` script follow these steps. After each one try to redo what you were doing, if it does not work, start from the top but go one step further. (So first try only `1.` than rerun, if it still does not work try `1.` AND `2.` and rerun, you can see the pattern)

- Run `./scripts/ros_clean.sh`
- Run `./scripts/cmake_clean.sh --mac`
- Delete the `.macos/` directory

If you got all the way here, and it still does not work, please create an issue on [our GitHub page](https://github.com/TrickfireRobotics/gazebo-simulations/issues). I will try to get back to you with a fix.
