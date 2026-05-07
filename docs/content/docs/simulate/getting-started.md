---
title: Getting Started
description: Clone the repository and pick your simulation environment.
---

Clone the repo, install the prerequisites for your chosen environment, then follow the guide for it.

## Clone the repository

```bash title="Host terminal"
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
cd gazebo-simulations
```

## Choose your workflow

| Environment | When to use |
| --- | --- |
| [Dev Container](../devcontainer/) | Standard setup on any machine with Docker |
| [Nvidia GPU](../nvidia/) | If you have an Nvidia GPU |
| [MacOS Native](../macos/) | No Docker, runs natively, MacOS only |

### Prerequisites by environment

**Docker Dev Container:**
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
  - [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
  - A VNC viewer ([RealVNC](https://www.realvnc.com/en/connect/download/viewer/), [TigerVNC](https://tigervnc.org/))


**Jetson:**
  - Nvidia GPU
  - Docker

**MacOS Native:**
  - MacOS with internet access
