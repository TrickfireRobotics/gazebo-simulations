# Gazebo Simulations

> This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

## How to run Gazebo

> [!NOTE]
> If you have a device with X11 set up like Windows with WSL installed or Linux, first look [here](#systems-with-x11)

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

### Systems with X11

On systems that provide X11 (like Linux and WSL), GUI forwarding is typically built-in. You can usually skip steps 5 and 6 and just run Gazebo — a Gazebo window should appear automatically. The `start_x_server.sh` script is not needed in these cases, since these systems already handle the display binding (for example, WSL binds to display :0). For more details, you can check [here](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).
