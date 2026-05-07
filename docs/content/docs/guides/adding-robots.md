---
title: Adding a New Robot
description: How to generate ROS 2 simulation packages for a new robot from an OnShape CAD model using genbot.
---

This guide covers the full process of going from a CAD model in OnShape to a running Gazebo simulation.

## Overview

The pipeline is:

```
OnShape CAD → genbot → ROS 2 packages → launch_sim.sh → Gazebo + RViz
```

`genbot` handles the heavy lifting: it downloads the URDF and meshes from OnShape, post-processes them for Gazebo (xacro injection, mesh path rewriting, control generation), and scaffolds two ROS 2 packages.

## Option A: GitHub Actions (recommended)

The easiest way to add a robot is through the GitHub Actions workflow, which runs genbot on CI and opens a PR with the generated packages.

1. Go to **Actions** > **Generate/Update Robot from OnShape**
2. Click **Run workflow**
3. Fill in the inputs:

| Input | Description |
| --- | --- |
| `mode` | `create` for a new robot |
| `robot_name` | Identifier for the robot (e.g. `arm`, `rover`). Used for package names. |
| `onshape_url` | Full OnShape document URL for the CAD model |
| `attach_to_world` | Check this if the robot's base should be fixed in place (not free-floating) |

4. The workflow generates the packages and opens a PR on branch `genbot/create-<robot_name>`
5. Review the PR, set up RViz (see below), and merge

:::note
The workflow requires `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY` to be configured as repository secrets.
:::

## Option B: Run genbot locally

If you prefer to run it locally (useful for iteration):

### 1. Set up OnShape credentials

Create a file at `.github/genbot/onshape.env`:

```bash title="Inside devcontainer"
ONSHAPE_API_KEY=your_key_here
ONSHAPE_API_SECRET=your_secret_here
```

This lets you run `genbot` without passing credentials every time. Alternatively, export them directly:

```bash title="Inside devcontainer"
export ONSHAPE_API_KEY=your_key
export ONSHAPE_API_SECRET=your_secret
```

### 2. Run the create command

```bash title="Inside devcontainer"
PYTHONPATH=.github python3 -m genbot create <robot_name> <onshape_url> --attach-to-world
```

Or if you set up `onshape.env`, the alias works:

```bash title="Inside devcontainer"
genbot create <robot_name> <onshape_url> --attach-to-world
```

Options:
- `--attach-to-world` -- adds a fixed joint from the robot's `base_link` to the Gazebo world (use for arms, turrets, anything bolted down). Without this flag, genbot will prompt you interactively asking whether to attach to the world.
- `--no-reduce` -- skip STL triangle reduction (meshes will be larger but higher detail)
- `--output-dir <path>` -- write packages somewhere else instead of `robot-sim/`

### 3. What gets generated

```
robot-sim/
  <robot>_description/
    urdf/<robot>.urdf                   ← Post-processed geometry URDF
    urdf/<robot>_control.urdf.xacro     ← Generated ros2_control block
    meshes/                             ← STL mesh files
    CMakeLists.txt
    package.xml

  <robot>_bringup/
    launch/<robot>.launch.py            ← Launch orchestration
    config/<robot>.controller.yaml      ← Joint controller config
    config/<robot>.rviz                 ← RViz config (template)
    CMakeLists.txt
    package.xml
```

The robot is also registered in `robots.json` at the repo root with its OnShape URL and settings.

## 4. Launch

```bash title="Inside devcontainer"
./scripts/launch_sim.sh <robot_name>
```

## Updating an existing robot

If the OnShape model changes and you need to refresh the URDF and meshes:

```bash title="Inside devcontainer"
genbot update <robot_name>
```

Or use the GitHub Actions workflow with `mode: update`.

This **only** replaces:
- `<robot>_description/urdf/<robot>.urdf` (geometry)
- `<robot>_description/meshes/*` (mesh files)

It does **not** touch:
- `<robot>_description/urdf/<robot>_control.urdf.xacro` (your control edits)
- The entire `<robot>_bringup/` package (launch files, configs, RViz)
- `robots.json`

This means any manual edits you've made to the control xacro or bringup package are preserved.

## Debugging generation issues

**URDF parsing errors:** Run `genbot raw <robot_name>` first to download the raw URDF without processing. Inspect it in `.github/genbot/tests/<robot_name>/` to see what OnShape produced.

**Missing joints:** Check the OnShape model -- joints must be properly defined as mates in the assembly. `genbot` only picks up joints that `onshape-to-robot` successfully converts.

**Large mesh files:** By default, `genbot create` reduces STL triangle counts using `open3d`. If meshes are still too large, you can manually decimate them or simplify the CAD model.
