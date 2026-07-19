---
title: Getting Started
description: Clone the repository and pick your simulation environment.
---

Clone the repo, install the prerequisites for your chosen environment, then follow the guide for it.

## Clone the repository

```bash title="Terminal"
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
cd gazebo-simulations
```

## Choose your workflow

| Environment | Platforms | When to use |
| --- | --- | --- |
| [Native (pixi)](../macos/) | Linux, macOS, WSL2 | **Recommended** — no Docker required |
| [Dev Container](../devcontainer/) | Any OS with Docker | Consistent containerized environment |
| [Nvidia GPU](../nvidia/) | Linux with Nvidia GPU | GPU-accelerated simulation on Jetson |

### Prerequisites by environment

**Native (pixi):**
- [pixi](https://pixi.sh) installed

**Docker Dev Container:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

**Nvidia / Jetson:**
- Nvidia GPU with Docker
