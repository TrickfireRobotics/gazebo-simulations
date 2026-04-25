---
title: Jetson Simulating Guide
description: Get the simulation running on a Jetson with a monitor and keyboard connected. Assumes a setup Jetson.
---

This guide is for running simulations directly on an already configured Jetson that has a monitor, keyboard, and mouse attached. If the Jetson is not configured, see the [Jetson Setup](/gazebo-simulations/guides/jetson-setup/) guide first.

## Starting the container

From the Jetson terminal, start the simulation container:

```bash title="Jetson terminal"
cd ~/gazebo-simulations
./scripts/start_container.sh
```

The script detects the NVIDIA GPU, starts the container with GPU passthrough, and drops you into a shell inside the container. There should be a log message confirming the GPU is detected and the container is running. If the log says "No NVIDIA GPU detected, starting in VNC mode" instead, see the troubleshooting section below, something is wrong. You can check the passthrough works by running `xeyes` inside the container, you should see a native window pop up on the Jetson desktop with eyes following your mouse cursor.

## Running a simulation

Once inside the container shell, launch a simulation:

```bash title="Inside nvidia container"
./scripts/launch_sim.sh arm
```

The first run builds the ROS 2 workspace, which takes a few minutes. Subsequent runs are fast unless you've changed code.

See [Running Simulations](/gazebo-simulations/guides/running-simulations/) for flags, logging, and troubleshooting.

## Stopping

:::tip[Tip]
Press `Ctrl+C` in the `launch_sim.sh` terminal to stop the simulation. To exit the container back into the host shell call the `exit` command.
:::

## Updating the codebase

If you are working on the simulation code on your own machine (as you should be, the dev environment should stay out of the Jetson), you can sync your changes without commiting using the `sync_ssh.sh` script:

```bash title="Dev machine terminal"
./scripts/sync_ssh.sh <target>
```

Where `<target>` is the name of the Jetson configured in `remote_pcs.sh`. This will use `rsync` to transfer your local code changes to the Jetson, which you can then run inside the container.

:::warning[Warning]
The `sync_ssh.sh` script does not play well with deleted files. If you delete a file locally, it will still be present on the Jetson after syncing. Also try to avoid multiple people working on the same codebase and syncing to the Jetson, as that will cause problems. If two people are working with different version of the code, it's best to delete the directory on the Jetson before syncing to ensure a clean slate.
:::
