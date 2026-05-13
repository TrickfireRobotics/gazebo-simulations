---
title: Docker Setup (VNC)
description: Run the simulation inside a Docker container with a VNC display.
---

`sim docker` builds and launches the simulation inside a Docker container. Genesis renders headlessly to a virtual display that you connect to via VNC or browser.

:::note
Code blocks labeled **Host terminal** run on your local machine. **Inside devcontainer** runs inside the container.
:::

## Option A — VS Code Dev Container (recommended)

Open the cloned folder in VS Code. You should see a prompt to **Reopen in Container** — click it. If it doesn't appear, open the Command Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**.

The first build downloads and installs ROS 2 Humble + Genesis into the image — this takes several minutes. Subsequent opens are fast.

Once inside you'll be the `trickfire` user at `/home/trickfire/gazebo-simulations`.

### Start the display

The Dev Container starts the VNC display stack automatically via the `postStartCommand`. If you ever need to restart it manually:

```bash title="Inside devcontainer"
./.devcontainer/x_server.sh
```

This starts Xorg (dummy driver), Openbox, x11vnc on port `5900`, and noVNC on port `6080`.

Connect with your VNC viewer at `localhost:5900`, or open `http://localhost:6080/vnc.html` in your browser.

### Launch the simulation

```bash title="Inside devcontainer"
sim docker arm
```

The Genesis simulation runs headless inside the container and renders to the VNC display.

## Option B — Docker Compose directly

```bash title="Host terminal"
cd docker
docker compose up --build
```

Then exec into the running container and run `sim docker arm`.

## Troubleshooting

**"No space left on device" during build:** Docker Desktop's virtual disk is full. Run `docker system prune -a --volumes` to free space, then rebuild.

**"Current working directory is outside container mount namespace root":** Rebuild the container image — this error appears when attaching to a stale container built before the Dockerfile added the `WORKDIR` layer.

**VNC shows a blank screen:** The display starts automatically, but if you restarted the container manually run `.devcontainer/x_server.sh &` inside the container.
