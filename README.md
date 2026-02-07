# Gazebo Simulations

This repository contains [Gazebo Fortress](https://gazebosim.org/docs/fortress/install/) simulations for Trickfire’s robot subsystems, including the drivebase, arm, and autonomous systems. The project uses [ROS 2 Humble](https://docs.ros.org/en/humble/index.html) for robot code and runs entirely inside a Docker container, including the codebase and Gazebo GUI.

## How to run Gazebo

> [!NOTE]
> If you have a device with X11 set up like Windows with WSL installed or Linux, first look [here](#systems-with-x11). If you do not mind installing an app, you can look [here](#vnc-viewer), although it is optional.

1. Clone this repo
2. Make sure you have the `ms-vscode-remote.remote-containers` VsCode extension installed.
3. Open the repo inside VsCode. You should see a pop-up asking you if you want to reopen the project in container, do that. The first time doing this can take up to 10 mins depending on how good of a computer you have. If you do not see this pop-up run the `Dev Containers: Rebuild and reopen in container` VsCode command. If it doesn't exist you do not have the extension mentioned above.
4. Attach to the container shell either by opening the VsCode terminal thats already attached or by running the `attach_to_container.sh` script in any host terminal.
5. Run the `start_x_server.sh` script. This sets up the desktop environment that any GUI app ran inside of the container can use.
6. Open up [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) and click on the connect button.
7. You can test if it works with running Gazebo with an empty world using the command below. you should see a Gazebo window on the website above.

```bash
ign gazebo empty.sdf
```

## How to run simulation

Once you launch the `devcontainer`, set up your display environment and verified Gazebo runs, you're ready to start the simulation. There is a script that will build the ROS files and launch the arm simulation (it is the only one we have right now) using our launch file. You can call it using this command:

```bash
./scripts/build_ros2_sim.sh
```

After the script logs `[create-2] [INFO] ... [ros_gz_sim]: OK creation of entity.` the simulation launched. You can go to your Gazebo window and you should see the arm model.

>[!TIP]
>For more information and troubleshooting tips go look at the [simulation README](./robot-sim/README.md).

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
