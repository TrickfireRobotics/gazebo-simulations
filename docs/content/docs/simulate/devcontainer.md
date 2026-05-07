---
title: Docker Dev Container
description: Run the simulation inside a VS Code Dev Container with full display support.
---

This is the primary workflow. Everything runs inside a Docker container - ROS 2 Humble, Gazebo Fortress, and all dependencies are pre-installed. You edit code on your host machine; the container handles building and running.

:::note
Each code block is labeled - **Host terminal** for commands on your local machine, **Inside devcontainer** for commands inside the container.
:::

## 1. Open in the Dev Container

Open the cloned folder in VS Code. You should see a prompt to **Reopen in Container** - click it. If the prompt doesn't appear, open the Command Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**.

The first build downloads the full Docker image with ROS 2 Humble, Gazebo Fortress, and all dependencies - this takes a few minutes. Subsequent opens are fast.

Once inside, you'll be the `trickfire` user at `/home/trickfire/gazebo-simulations`.

:::note
The `postCreateCommand` in `devcontainer.json` automatically runs `scripts/ros_clean.sh` to clear any stale ROS build artifacts from previous sessions.
:::

## 2. Start the display

Gazebo and RViz need a display to render their GUIs. Since the container has no physical monitor, we run a virtual X11 server with VNC so you can view the desktop remotely.

:::note
If your host machine has an X11 server and you've configured X11 forwarding to the container (e.g. via `DISPLAY` and X socket mounting), you can skip this step. Run `xeyes` inside the container to verify - if a pair of eyes appears on your screen, X11 forwarding is already working, and you can skip this step.
:::

```bash title="Inside devcontainer"
./scripts/start_x_server.sh
```

This starts:
1. **Xorg** with a dummy display driver
2. **Openbox** window manager
3. **x11vnc** VNC server on port `5900`
4. **noVNC** web bridge on port `6080`

Connect with your VNC viewer at `localhost:5900`. You should see a blank desktop. Verify it's working by opening a new terminal and running:

```bash title="Inside devcontainer"
xeyes
```

A pair of eyes should appear in the VNC desktop. Leave the X server script running in its terminal. It needs to be running at all times when you need to run a GUI (so do not kill it when you're going to need to launch the simulation). If you do not want to open multiple terminals, you can append `&` at the end of the command (`./scripts/start_x_server.sh &`) to make it run in the background.

:::tip
For a quick check without a VNC client, open `http://localhost:6080/vnc.html` in your browser. Note that noVNC doesn't forward modifier keys (Alt, Super, etc.) correctly, so a native VNC viewer is better for regular use.
:::

## External terminals

If you do not like using the VSCode built in terminal for the container shell, you can attach from any terminal of your choice. There is a script for convenience, you can call it using:

```bash title="Host terminal"
./scripts/attach_to_container.sh
```

This finds the running Dev Container and drops you into a shell as the `trickfire` user. Run the `exit` command if you want to exit the environment back to your host shell.

## Next step

Once the display is running, head to [Running Simulations](../running-simulations/) to launch your first sim.
