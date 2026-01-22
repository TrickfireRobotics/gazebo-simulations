# Gazebo Simulations

This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

## How to run Gazebo

> [!NOTE]
> If you have Windows with WSL installed, first look [here](#windows-with-wsl)

1. Clone this repo
2. Open the repo inside VsCode, and attach to it either from the VsCode terminal or by running the `attach.sh` script in any terminal. Make sure you have `ms-vscode-remote.remote-containers` extension installed.
3. VsCode should ask you if you want to reopen the project in container, do that. The first time doing this can take up to 10 mins depending on how good of a computer you have. If you do not see this pop-up run the `Dev Containers: Rebuild and reopen in container` VsCode command.
4. Run the `start_x_server.sh` script. This sets up the desktop environment that any GUI app ran inside of the container can use.
5. Open up [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) and click on the connect button.
6. You can test if it works with running Gazebo with an empty world using the command below. you should see a Gazebo window on the website above.

```bash
ign gazebo empty.sdf
```

---

### Windows with WSL

WSL should forward the image automatically, meaning you can skip the x-server script part. Just run Gazebo and a window should pop out. The script will not work, because WSL binds display `:0`. You can find more info on it [here](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) in case you want to.
