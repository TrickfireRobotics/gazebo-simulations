# Gazebo Simulations

> This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

## How to run Gazebo

> [!NOTE]
> If you have Windows with WSL installed, first look [here](#windows-with-wsl)

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

### Windows with WSL

WSL should forward windows from Docker out of the box, meaning you can skip the 5th and 6th step. Just run Gazebo and a Gazebo window should appear. The `start_x_server.sh` script will not work, because WSL binds display `:0`, also it essentially does the same thing WSL does on its own. You can find more info on it [here](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) in case you want to.
