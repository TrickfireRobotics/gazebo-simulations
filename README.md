# Gazebo Simulations

> This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

> [!NOTE]
> The first container build can take 20–35 minutes depending on your machine

---

## Setting up the environment & container:

### MacOS

1. Make sure you have Docker installed, and this repository cloned

2.	Install and configure XQuartz:
    
  ```bash
  brew install --cask xquartz
  defaults write org.xquartz.X11 nolisten_tcp -bool false
  ```

3.	Open XQuartz → Settings → Security and enable Allow connections from network clients
   
   
Now everytime you want to lauch the container, open the project in VSCode, ensure the Remote Containers extension is installed (`ms-vscode-remote.remote-containers`). You should be prompted to `Reopen in Container`.

When the container builds and VSCode opens, you can use this launch script to set up xQuartz for you, and attach you to the container:

```bash
scripts/run_macos.sh
```

This script launches XQuartz, configures it, and then attaches you to the running devcontainer.

> [!WARNING]
> Do not run this script inside the container!
> Run it from your host terminal while VSCode is open in the devcontainer


### Windows (WSL)
	
  1.	In a WSL terminal, clone the repository:

  ```bash
  git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
  ```

  2.	Ensure Docker Desktop is running.
	
  3.	Open the repo in VSCode through WSL:

  - Press Ctrl+Shift+P
	- Run Open Folder in WSL
	- Select the cloned repository
   
	4.	Reopen the project in the devcontainer:

	- Ctrl+Shift+P
  - Run Reopen in Container
    
	6.	Wait for the container to build. This can take ~35 minutes depending on hardware.

	8.	Once inside the devcontainer, open a terminal in VSCode and run:

---

## Running Gazebo inside the container:

When you succesfully attach to the Docker Container, you can launch Gazebo using the following command:

```bash
ign gazebo empty.sdf
```

Or by using a script that runs the same exact thing (easier to type):

```bash
scripts/run_gazebo.sh
```

If everything is configured properly, Gazebo should open with an empty world.
