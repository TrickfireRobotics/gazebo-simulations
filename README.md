# Repo for simulations for drivebase, arm, and autonomous
fyi it takes about ~35 min to compile this docker on windows depending on your machine

## Setup steps for windows
In a wsl terminal, clone this repo 

Make sure Docker is running 

In VSCode, open a folder in WSL, and find this repo. Open it, and run the Reopen in Container command

wait for the container to compile

run the command "ign gazebo empty.sdf" in a new terminal

should see a gazebo gui window appear with an empty world
