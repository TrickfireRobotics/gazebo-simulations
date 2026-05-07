---
title: macOS Native Setup
description: Optional native macOS instructions for running ROS 2 + Gazebo (micromamba).
---

## macOS Native Setup (Optional)

This repository includes an optional, opt-in native macOS setup that installs a micromamba-based ROS 2 + Gazebo environment and builds required upstream components from source.

- **Non-destructive:** This is strictly optional and does not replace or modify existing Linux or containerized workflows.
- **Location:** The macOS helpers live at `./robot-sim/sim_common/macos/env.lock.yml` and `./robot-sim/sim_common/macos/versions.env`.
- **Entry points:** Use `scripts/macos_setup.sh` for setup and `scripts/macos_gui.sh` for the GUI.

Prerequisites

- A macOS host (the scripts will abort on non-Darwin hosts).
- Xcode command line tools installed (`xcode-select --install`).
- micromamba installed and `MAMBA_EXE` environment variable set to the micromamba executable.

Quickstart

1. Make the wrapper executable (if needed):

```bash
chmod +x scripts/macos_setup.sh scripts/macos_gui.sh
```

2. Run the macOS setup (this will create a `ros_env` micromamba environment and build from source):

```bash
./scripts/macos_setup.sh
```

## Run the simulator after setup

The macOS workflow uses two terminals. After the setup completes, run the simulation from the repository root:

1. Start the ROS 2 / Gazebo server side:

```bash
./scripts/launch_sim.sh arm
```

2. In a second terminal, start the Gazebo GUI:

```bash
./scripts/macos_gui.sh
```

The GUI launcher is documented in [Scripts](../../reference/scripts/) and is the user-facing entrypoint for the macOS visualization step.

## Notes

- The build steps can be long (compiling gz/ros components). See `scripts/macos_setup.sh` for targeted commands like `env`, `patches`, `ros_gz`, `control`, and `workspace`.
- If you only need a rebuild without relaunching, use `./scripts/macos_setup.sh workspace`.
- To remove the native macOS setup, delete the `macos/` directory and the `robot-sim/build`, `robot-sim/install`, and `robot-sim/log` folders.
- This workflow stays separate from the Linux/container flow documented in [Running Simulations](../running-simulations/).

Support

If you hit platform-specific build issues, open an issue with build logs and the output of the failing step. I can also add a troubleshooting section if you want.
