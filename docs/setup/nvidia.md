---
title: Nvidia Simulating Guide
description: Guide on how to run the simulation on Linux machines with an Nvidia GPU
---

This guide is for running the simulation in a Docker container, but with GPU passthrough, that means that Docker will be able to use your GPU, speeding up the simulation massively. This only works for Nvidia GPU's because they are the only ones with this functionality. This guide also assumes you are running Linux, and was mainly designed for the Nvidia Jetson computers.

:::note[Jetson computers]
If you are using a Nvidia Jetson, this guide assumes it has been set up. If the Jetson is not configured, see the [Jetson Hardware Setup](#how-to-set-up-a-jetson) guide first.
:::

## 1. Setup the codebase

Clone the repository on the Jetson using `git`:

```bash title="Jetson terminal"
git clone https://github.com/TrickfireRobotics/gazebo-simulations.git
cd gazebo-simulations
```

## 2. Launch the simulation with GPU support

Use the `sim` CLI to build and launch the simulation with GPU passthrough:

```bash title="Jetson terminal"
cd gazebo-simulations
sim docker <robot-name>
```

The container detects the NVIDIA GPU and automatically enables GPU passthrough. You should see the container start and drop you into a shell.

## 3. Launch the simulation

You can now move onto the [Running Simulations](../running-simulations/) to launch your sim.

---

# How to set up a Jetson

To set up a Jetson computer for Docker GPU support:

1. **Install NVIDIA Container Toolkit:**

    ```bash title="Jetson terminal"
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
      && curl -fsSL https://nvidia.github.io/libnvidia-container/libnvidia-container.list | \
      sed 's/^deb /deb [signed-by=\/usr\/share\/keyrings\/nvidia-container-toolkit-keyring.gpg] /' | \
      sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
    sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    ```

2. **Configure Jetson for max performance (optional but recommended):**
    - Switch to maximum power mode (MAXN)
    - Set fans to full speed
    - Disable WiFi power management

You should now be ready to run the simulation container on the Jetson with GPU passthrough.
