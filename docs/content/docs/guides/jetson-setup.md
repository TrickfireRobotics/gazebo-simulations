---
title: Running on a Jetson
description: Set up the standalone simulation container on an NVIDIA Jetson (or any NVIDIA Linux host) without VS Code.
---

This guide covers running the simulation environment on a Jetson (or another NVIDIA Linux PC) using the standalone Docker container workflow. This is an alternative to the VS Code Dev Container approach and is intended for NVIDIA hosts, resulting in a way better performace because of direct GPU access and rendering.

:::note
Each code block is labeled -- **Jetson terminal** for commands run on the Jetson itself, **User terminal** for commands run on your development machine.
:::

## Prerequisites

- NVIDIA Jetson (or NVIDIA Linux PC) running Ubuntu with [JetPack](https://developer.nvidia.com/embedded/jetpack) installed
- Docker installed on the Jetson
- Network access to the Jetson

## 1. Clone the repo on the Jetson

On the Jetson, clone the repository:

```bash title="Jetson terminal"
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
cd gazebo-simulations
```

Alternatively, sync it from your dev machine using `sync_ssh.sh`, which uses `rsync` to transfer your local codebase to the Jetson:

```bash title="User terminal"
./scripts/sync_ssh.sh <target>
```

:::note[Note]
The `<target>` reffers to the Jetson defined in `remote_pcs.sh`. Add your Jetson there if it's not already.
:::

## 2. One-time host setup

Run the setup script on the Jetson to configure the host:

```bash title="Jetson terminal"
./scripts/setup_jetson.sh
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

You should now be ready to run the simulation container on the Jetson with GPU passthrough, see the [Simulating on Jetson guide](/gazebo-simulations/guides/jetson-quickstart/) for instructions.
