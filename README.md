# Gazebo Simulations

This repository contains [Gazebo Fortress](https://gazebosim.org/docs/fortress/install/) simulations for Trickfire's robot subsystems, including the drivebase, arm, and autonomous systems. The project uses [ROS 2 Humble](https://docs.ros.org/en/humble/index.html) for robot code and runs entirely inside a Docker container, including the codebase and Gazebo GUI.

## How to run Gazebo

> [!NOTE]
> If you have a device with X11 set up like Windows with WSL installed or Linux, first look [here](#systems-with-x11). If you do not mind installing an app, you can look [here](#vnc-viewer), although it is optional.

1. Clone this repo
2. Make sure you have the `ms-vscode-remote.remote-containers` VsCode extension installed.
3. Open the repo inside VsCode. You should see a pop-up asking you if you want to reopen the project in container, do that. The first time doing this can take up to 10 mins depending on how good of a computer you have. If you do not see this pop-up run the `Dev Containers: Rebuild and reopen in container` VsCode command. If it doesn't exist you do not have the extension mentioned above.
4. Attach to the container shell either by opening the VsCode terminal thats already attached or by running the `scripts/attach_to_container.sh` script in any host terminal.
5. Run the `scripts/start_x_server.sh` script. This sets up the desktop environment that any GUI app ran inside of the container can use.
6. Open up [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) and click on the connect button.
7. You can test if it works with running Gazebo with an empty world using the command below. you should see a Gazebo window on the website above.

```bash
ign gazebo empty.sdf
```

## How to run simulation

Once you launch the `devcontainer`, set up your display environment and verified Gazebo runs, you're ready to start the simulation. The `launch_sim.sh` script builds the ROS2 packages and launches the simulation for a given robot:

```bash
./scripts/launch_sim.sh arm
```

The script accepts the robot name as an argument (currently only `arm` is available). It builds the required packages (`<robot>_description`, `<robot>_bringup`, `sim_common`, `sim_worlds`), sources the workspace, and launches the Gazebo simulation with RViz.

Options:
- `--build-only` — Build the packages without launching the simulation
- `--no-build` — Skip the build step and launch directly (if already built)

> [!TIP]
> For more information and troubleshooting tips go look at the [ROS workspace docs](./docs/ros-workspace.md).

## Moving robot joints

Once the simulation is running, you can send joint trajectory commands using the `move_joints` node:

```bash
ros2 run sim_common move_joints --ros-args \
    -p joints:="['shoulder_1', 'elbow_1', 'wrist_1', 'wrist_2']" \
    -p positions:="[0.5, 0.5, 0.2, 0.0]" \
    -p duration:=2.0
```

> [!TIP]
> See the [joint moving docs](./docs/joint-moving.md) for all parameters and examples.

## Generating packages from OnShape

To create or update a robot simulation from an OnShape model, use the **Generate/Update Robot from OnShape** GitHub Actions workflow. Go to **Actions** > **Generate/Update Robot from OnShape**, click **Run workflow**, and fill in the robot name and OnShape URL. The workflow downloads the URDF and meshes, scaffolds the ROS2 packages, and opens a PR automatically.

> [!TIP]
> See the [genbot documentation](./docs/genbot.md) for details on the pipeline, generated output, and required repository secrets.

---

## Additional information

### Systems with X11

On systems that provide X11 (like Linux and WSL), GUI forwarding is typically built-in. You can usually skip steps 5 and 6 and just run Gazebo — a Gazebo window should appear automatically. The `start_x_server.sh` script is not needed in these cases, since these systems already handle the display binding (for example, WSL binds to display :0). For more details about WSL gui-apps, you can check [here](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

### VNC Viewer

> [!NOTE]
> If you're using a system with `X11` provided, this does nothing better than what you already have. For people using the `noVNC` in the browser this is optional, but provides more functionality.

If you don't mind installing an app, there is a better way to open up Gazebo on Mac, that allows passing through key combos like `alt-tab` and simillar. You can install the app [from here](https://www.realvnc.com/en/connect/download/viewer/) or using Homebrew like this: `brew install --cask vnc-viewer` To make the app work skip the 6th and 7th step in the directions and instead open this app. Create a new connection by doing `CTRL+N` or `CMD+N` depending on OS, and to adress paste this:

```ip
localhost:5900
```

You're going to get a popup informing you that the connection is not secure. You do not have to worry about this as it is run locally.
