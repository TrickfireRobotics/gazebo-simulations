# Gazebo simulations

> This repository is for Gazebo simulations for drivebase, arm, and autonomous

## First Time Setup

### MacOS

You need Docker if you don't have it:

```bash
brew install --cask docker
```
Than you also need [XQuartz](https://www.xquartz.org):

```bash
# Install and start XQuartz
brew install --cask xquartz
defaults write org.xquartz.X11 nolisten_tcp -bool false
```

After install, open XQuartz → Settings → Security and check “Allow connections from network clients.”

### TODO: Windows and MacOS

There are existing instructions [here](https://github.com/TrickfireRobotics/drivebase-gazebo-simulation#firsttime-setup), they need to be reviewed and placed here.

## Running Docker

### Opening the `.devcontainer`

Open the repo in VSCode, ensure you have `ms-vscode-remote.remote-containers` extension installed.
In the bottom right you should get a prompt to open the project in a container, click on `Reopen in Container` option.
It is going to take a while (20 to 30 minutes) to open for the first time.

### Attaching to Docker on MacOS

You cannot run Gazebo just yet, because everytime you want to run Gazebo in Docker on MacOS you need to open XQuartz and run command to configure it.
There is a script at `scripts/run_macos.sh` direectory that you can run in a terminal to configure XQuartz and attach to the container

> [!WARNING]
> Don't run the script inside of the Docker container shell! It needs to be run outside! The script will automatically attach you to the `.devcontainer.` Make sure VSCode is running with the opened `.devcontainer`
