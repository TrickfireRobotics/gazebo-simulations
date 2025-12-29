# Gazebo Simulations

> This repository contains Gazebo simulations for the drivebase, arm, and autonomous.

> [!NOTE]
> The first container build can take 20–35 minutes depending on your machine

---

### How to run Gazebo on MacOS

Open the `devcontainer` inside VsCode, and attach to it either from the VsCode terminal or by running the `attach.sh` script in any terminal.

Turn on the X11 server. All of the necessary commands have been put into the `start_x_server.sh` script. This setup the desktop environment that any GUI app ran inside of the container can use.

Run Gazebo using the following command:

```bash
ign gazebo empty.sdf
```

Open up [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) and click on the connect button. You should see Gazebo.

---

### Windows (WSL)
Make sure you have docker desktop installed.

Install [x410 - x server for windows](https://apps.microsoft.com/detail/9pm8lp83g3l3?hl=en-US&gl=KE)
  
Open the `x410` app. Nothing will show up, but it should be running in the background.

Once in the devcontainer, in the terminal run:

```bash
export DISPLAY=host.docker.internal:0.0
```

If you get LibGL errors, run this in the terminal as well:

```bash
export LIBGL_ALWAYS_INDIRECT=1
```

#### Cloning the repository:
 
1.	In a WSL terminal, clone the repository:

```bash
export DISPLAY=host.docker.internal:0.0
```

If you get LibGL errors, run this in the terminal as well:

```bash
export LIBGL_ALWAYS_INDIRECT=1
```

#### Cloning the repository:

1. In a WSL terminal, clone the repository:

```bash
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
```

2. Ensure Docker Desktop is running.

3. Open the repo in VSCode through WSL:

- Press Ctrl+Shift+P
- Run Open Folder in WSL
- Select the cloned repository

4.	Reopen the project in the devcontainer:

- Ctrl+Shift+P
- Run Reopen in Container

5.	Wait for the container to build. This can take ~35 minutes depending on hardware.

6.	Once inside the devcontainer, open a terminal in VSCode and run:
