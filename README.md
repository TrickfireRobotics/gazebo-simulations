# Repo for simulations for drivebase, arm, and autonomous
fyi it takes about ~35 min to compile this docker on windows depending on your machine

## Setup steps for Windows
In a WSL terminal, clone this repo 

`git clone https://github.com/TrickfireRobotics/gazebo-simulations.git`

Make sure Docker Desktop is running on your machine

In VSCode, press `Ctrl+Shift+P` to open the command palette. Search for the "Open Folder in WSL" command and select it. Find and select this repo's folder in your WSL file system. 

Run the Reopen in Container command (`Ctrl+Shift+P` and search "Reopen in Container")

Wait for the container to compile, this will take a while

In VSCode, open a new terminal and run the command `ign gazebo empty.sdf` 

You should see a Gazebo GUI window appear with an empty world
