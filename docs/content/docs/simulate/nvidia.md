---
title: Nvidia Simulating Guide
description: Guide on how to run the simulation on Linux machines with an Nvidia GPU
---

This guide is for running the simulation in a Docker container, but with GPU passthrough, that means that Docker will be able to use your GPU, speeding up the simulation massively. This only works for Nvidia GPU's because they are the only ones with this functionality. This guide also assumes you are running Linux, and was mainly designed for the Nvidia Jetson computers.

:::note[Jetson computers]
If you are using a Nvidia Jetson, this guide assumes it has been set up. If the Jetson is not configured, see the [Jetson Hardware Setup](#how-to-set-up-a-jetson) guide first.
:::

## 1. Setup the codebase

First you're going to need to get your codebase onto the Jetson. You can do that by cloning the repo using `git`, but it is usually better to use the provided file sync script, as that will replicate the excact state of the codebase you have on your machine. You need to rerun the sync script everytime you change code on your machine.

```bash title="Dev machine terminal"
./scripts/sync_ssh.sh <target>
```

Where `<target>` is the name of the Jetson configured in `remote_pcs.sh`. This will use `rsync` to transfer your local code changes to the Jetson, which you can then run inside the container.

## 2. Launch the Nvidia container

From the Jetson terminal, start the simulation container:

```bash title="Jetson terminal"
cd ~/gazebo-simulations
./scripts/start_container.sh
```

The script detects the NVIDIA GPU, starts the container with GPU passthrough, and drops you into a shell inside the container. There should be a log message confirming the GPU is detected and the container is running. If the log says "No NVIDIA GPU detected, starting in VNC mode" instead, see the troubleshooting section below, something is wrong. You can check the passthrough works by running `xeyes` inside the container, you should see a native window pop up on the Jetson desktop with eyes following your mouse cursor.

## 3. Launch the simulation

You can now move onto the [Running Simulations](../running-simulations/) to launch your sim.

---

# How to set up a Jetson

To first time setup a Jetson computer for simulation, run this in the Jetson's shell:

```bash title="Jetson terminal"
bash -c $(curl -fsSL https://raw.githubusercontent.com/TrickFireRobotics/gazebo-simulations/scripts/setup_jetson.sh)
```

This script:
- Installs the NVIDIA Container Toolkit so Docker can access the GPU
- Makes the Jetson use maximum performance, ignoring power. This will:
   - Switch to the highest power mode
   - Disables Wi-Fi power management
   - Sets fans to **full** mode, making them spin on max always
- Configures the GNOME desktop (dark mode, TrickFire wallpaper, kitty terminal)
- **Reboots the host at the end**

Wait for the Jetson to finish rebooting before continuing. If you want to check the power changes have applied, and that your Jetson is being throttled, you can run `health_check_remote.sh` and check the power mode and WiFi status. This has to be ran from another machine with ssh access to the Jetson, since the Jetson will be headless after this step: (target again reffers to the Jetson defined in `remote_pcs.sh`)

```bash title="User terminal"
./scripts/health_check_remote.sh <target>
```
You should now be ready to run the simulation container on the Jetson with GPU passthrough. Go back [to the top](#1-setup-the-codebase) and continue.
