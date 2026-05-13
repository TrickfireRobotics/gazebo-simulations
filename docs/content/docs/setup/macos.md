---
title: Native Setup (macOS / Linux)
description: Run Genesis simulations natively with sim native — no Docker required.
---

`sim native` runs ROS 2 Humble and Genesis entirely on your host machine. On first run it bootstraps a self-contained conda environment inside the repo. Genesis opens a native window.

:::note
All code blocks labeled **Terminal** run on your host machine — no container.
:::

## First run

```bash title="Terminal"
sim native arm
```

That's it. On the first run the CLI will:

1. Download miniconda to `.conda/` inside the repo (~90 MB, one-time)
2. Create a conda env named `sim` with ROS 2 Humble and all dependencies (~5–15 min, one-time)
3. Build the ROS 2 workspace with `colcon`
4. Launch robot_state_publisher + Genesis simulation + Joint GUI

Subsequent runs skip steps 1–2 and go straight to building and launching.

## What gets installed and where

Everything lives inside the repo under `.conda/`. It is gitignored and never touches your system Python, system ROS, or any other global state. Deleting the repo removes all of it.

```
genesis-simulations/
└── .conda/
    ├── bin/conda          ← miniconda binary
    ├── envs/sim/          ← ROS 2 Humble + Genesis conda env
    └── .condarc           ← project-local channel config
```

## Flags

```bash title="Terminal"
# Skip colcon rebuild (use existing install/)
sim native arm --no-build

# Build only, don't launch
sim native arm --build-only
```

## Updating the conda environment

The CLI manages the env automatically. If you need to rebuild it from scratch, delete the env directory and re-run:

```bash title="Terminal"
rm -rf .conda/envs/sim
sim native arm
```

## Troubleshooting

**Genesis window doesn't appear:** On the very first run, Genesis compiles Taichi kernels which takes 10–20 seconds. Subsequent runs are faster.

**Build errors:** Run `sim clean` to delete stale build artifacts, then retry.

**`sim` command not found:** Make sure you installed the CLI:

```bash title="Terminal"
pip install -e .
```
