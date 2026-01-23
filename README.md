# Gazebo Simulations

> This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

> [!NOTE]
> The first container build can take 20–35 minutes depending on your machine

---

### How to run Gazebo

> [!NOTE]
> If you have Windows with WSL installed, first look [here](#windows-with-wsl)

1. Clone this repo
2. Open the repo inside VsCode, and attach to it either from the VsCode terminal or by running the `attach.sh` script in any terminal. Make sure you have `ms-vscode-remote.remote-containers` extension installed.
3. Run the `start_x_server.sh` script. This sets up the desktop environment that any GUI app ran inside of the container can use.
4. Open up [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) and click on the connect button.
5. You can test if it works with running Gazebo with an empty world using the command below. you should see a Gazebo window on the website above.

```bash
ign gazebo empty.sdf
```

---

### Windows with WSL

WSL should forward the image automatically, meaning you can skip the x-server script part. Just run Gazebo and a window should pop out. The script will not work, because WSL binds display `:0`. You can find more info on it [here](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) in case you want to.

### How to run simulation

Once you launch the docker container run the bash script
'''bash
build-ros2-sim.sh
'''
Then in the X11 server 2 windows should appear, One will contain the model we are currently using for testing, a default mini rover
And a rvis2 window which is used to visualize PUB-SUB communication within ROS

### Read me in Robot-sim-template folder to go over the functionality of the simulation system
