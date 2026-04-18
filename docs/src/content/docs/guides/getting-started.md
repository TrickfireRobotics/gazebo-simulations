---
title: Getting Started
description: Set up the TrickFire simulation environment from scratch and run your first Gazebo simulation.
---

This guide walks you through the full setup: cloning the repo, opening the Dev Container, and getting a display running so you can launch simulations.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
- A VNC viewer (e.g. [RealVNC](https://www.realvnc.com/en/connect/download/viewer/), [TigerVNC](https://tigervnc.org/), or any VNC client)

## 1. Clone the repository

```bash
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
cd gazebo-simulations
```

## 2. Open in the Dev Container

Open the folder in VS Code. You should see a prompt asking to **Reopen in Container** -- click it. If the prompt doesn't appear, open the Command Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**.

The first build takes a while since it downloads the full Docker image with ROS 2 Humble, Gazebo Fortress, and all dependencies. Subsequent opens are fast.

Once inside, you'll be the `trickfire` user at `/home/trickfire/gazebo-simulations`.

:::note
The `postCreateCommand` in `devcontainer.json` automatically runs `scripts/clean_build.sh` to clear any stale ROS build artifacts.
:::

## 3. Start the display

Gazebo and RViz need a display to render their GUIs. Since the container has no physical monitor, we run a virtual X11 server with VNC so you can view the desktop remotely.

:::note
If your host machine already has an X11 server and you've configured X11 forwarding to the container (e.g. via `DISPLAY` and X socket mounting), you can skip this step entirely. You can verify by running `xeyes` inside the container -- if a pair of eyes appears on your screen, your X11 setup is working.
:::

```bash
./scripts/start_x_server.sh
```

This starts:
1. **Xorg** with a dummy display driver
2. **Openbox** window manager
3. **x11vnc** VNC server on port `5900`
4. **noVNC** web bridge on port `6080`

Connect to the container desktop using your VNC viewer at:

```
localhost:5900
```

You should see a desktop. To verify the display is working, open a new terminal and run:

```bash
xeyes
```

A pair of eyes should appear on the VNC desktop. Leave the X server script running in its terminal.

:::tip
If you just want to quickly check that things work without installing a VNC client, you can open `http://localhost:6080/vnc.html` in your browser to use the noVNC web client. However, noVNC does not forward modifier keys (Alt, Super, etc.) correctly, so a native VNC viewer is recommended for regular use.
:::
