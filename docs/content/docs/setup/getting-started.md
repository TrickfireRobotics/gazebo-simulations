---
title: Getting Started
description: Clone the repository and pick your simulation environment.
---

Clone the repo, then choose one of the two workflows below.

## Clone the repository

```bash title="Terminal"
git clone https://github.com/TrickfireRobotics/genesis-simulations.git
cd genesis-simulations
```

## Choose your workflow

| Workflow                         | When to use                                                          |
| -------------------------------- | -------------------------------------------------------------------- |
| [Native](../macos/)              | macOS or Linux, no Docker required — Genesis renders a native window |
| [Docker (VNC)](../devcontainer/) | Any machine with Docker — Genesis renders to a VNC display           |
| [Nvidia GPU](../nvidia/)         | Docker with GPU acceleration                                         |

### Native — `sim native`

Runs entirely on your host machine. On first run, the CLI downloads miniconda to `.conda/` inside the repo and creates a conda env with ROS 2 Humble + Genesis. No system-wide installs — deleting the repo removes everything.

**Prerequisites:** macOS or Linux, internet access.

### Docker — `sim docker`

Runs inside a Docker container with a built-in VNC server. Connect via your VNC viewer or browser to see the simulation. This is also the VS Code Dev Container workflow.

**Prerequisites:**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension (for the Dev Container workflow)
- A VNC viewer ([RealVNC](https://www.realvnc.com/en/connect/download/viewer/), [TigerVNC](https://tigervnc.org/)) or use the browser at `http://localhost:6080`
