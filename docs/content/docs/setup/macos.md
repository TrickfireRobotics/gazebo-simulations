---
title: Native Setup
description: Run the simulation natively on Linux, macOS, or WSL2 using pixi.
---

The native workflow installs ROS 2 Jazzy and Gazebo Harmonic into a self-contained environment inside the repository using [pixi](https://pixi.sh). No Docker required. Deleting the repo also deletes the environment — your system stays clean.

**Supported platforms:** Linux (x86-64, ARM64), macOS (Intel and Apple Silicon), WSL2.

## 1. Install pixi

```bash title="Terminal"
curl -fsSL https://pixi.sh/install.sh | bash
```

Restart your shell after installation (`source ~/.bashrc` or `source ~/.zshrc`).

## 2. Install dependencies

From the repo root, install ROS 2 Jazzy + Gazebo Harmonic into `.pixi/`:

```bash title="Terminal"
pixi install
```

This downloads ~3–5 GB on first run. Subsequent runs are instant.

## 3. Launch a simulation

```bash title="Terminal"
pixi run sim native arm
```

This builds the ROS 2 workspace and launches Gazebo, RViz, and the Joint GUI.

See [Running Simulations](../../guides/running-simulations/) for full CLI options and flags.

:::tip
Do not use `pixi shell` as your regular working shell — it modifies library paths in a way that can break system tools like `git` on macOS. Use `pixi run <command>` instead.
:::
