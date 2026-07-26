---
title: Docker
description: Run the simulation inside a container.
---

With this approcach everything runs inside a Docker container with everything deterministically installed. The native approach is faster (except on Linux system, Docker runs with native speeds there) but you can have issues installing or running the sim using it. This project uses [devcontainers](https://containers.dev/) to build the Docker environment. You can build it either using the [VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) or the [CLI](https://code.visualstudio.com/docs/devcontainers/devcontainer-cli) if you do not want to/cannot use VSCode.

## 1. Build the devcontainer

If you are using VSCode, open the cloned folder in VSCode. You should see a prompt to **Reopen in Container** in your bottom right. If the prompt doesn't appear, make sure you have the [extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed.

If you are using the CLI, navigate to the folder in your terminal and then run `devcontainer up`.

:::note
This will take a long time if it is your first time (30 mins)! Docker builds Chrono and its dependencies (many lines of C++) from source, and then the same for Gazebo and ROS! Subsequent launches will be very fast though.
:::

## 2. Check if display works

Gazebo and RViz need a display to render their GUIs. When the Dev Container starts, a script detects your host setup and picks the best display path automatically. Check the terminal you launched the container from — the log line it prints tells you which case applies to you.

### Linux host with Wayland (no VNC needed)

If your host runs a Wayland compositor (GNOME, KDE, Hyprland, etc.), the log prints:

```
[X11] Using Wayland socket at /run/host-runtime/wayland-1
```

The container forwards Wayland and X11 directly to your host compositor. GUI windows appear on your desktop natively — you can skip the VNC steps below.

### WSL2 with WSLg (no VNC needed)

WSL2 includes WSLg, a built-in Wayland compositor with X11 forwarding. Gazebo and RViz windows appear via WSLg automatically, the same as on native Linux with Wayland above.

### All other cases (macOS, headless servers, Windows without WSLg)

On hosts without a Wayland socket, the script starts a VNC stack. Depending on what GPU or virtual display driver is available, you will see one of the following:

```
[X11] Desktop NVIDIA GPU detected, using Xorg nvidia driver
[X11] Using vkms virtual display (/dev/dri/card1)
[X11] vkms unavailable, falling back to dummy driver (no DRI3)
[X11] Jetson/Tegra detected (no DRI), using Xvfb + EGL
```

followed by:

```
[noVNC] Desktop available at: http://localhost:6080/vnc.html
[MAIN] All services started
```

Once you see `[MAIN] All services started`, connect with a VNC viewer at `localhost:5900`. You should see a blank desktop.

:::note
Good VNC viewers I would reccomend are [TigerVNC](https://tigervnc.org/) or [VNCViewer](https://www.realvnc.com/en/connect/download/viewer/?lai_sr=0-4&lai_sl=l)
:::

:::tip
For a quick check without a VNC client, open `http://localhost:6080/vnc.html` in your browser. Note that noVNC doesn't forward modifier keys (Alt, Super, etc.) correctly, so a native VNC viewer is better for regular use.
:::

If the script fails, it automatically dumps `/tmp/start_x_server.log` to the terminal to help you diagnose the problem.

### Verify the display works

Before launching the sim, confirm both display paths are functioning:

- **X11 (Gazebo / RViz):** Run `xeyes` inside the container. If a pair of animated eyes appears (in your VNC viewer or on your local desktop), X11 is working and Gazebo will render.
- **Vulkan (Chrono):** Run `vkcube` inside the container. If a spinning textured cube renders without errors, Vulkan is working and Chrono's VSG visualizer will function.

## 3. Launch the sim

Once the display is running, head to [Running Gazebo](../../guides/gazebo/) to launch your first sim.
