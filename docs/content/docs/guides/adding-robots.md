---
title: Adding a New Robot
description: How to use sim create to generate ROS 2 packages from an OnShape CAD model and get a new robot running in Gazebo.
---

`sim create` takes a robot from OnShape and produces two ready-to-build ROS 2 packages — no manual URDF editing or package scaffolding required.

## Prerequisites: OnShape credentials

`sim create` calls the OnShape API to download the URDF and meshes. You need API credentials.

Create `cli/onshape.env` inside the Dev Container:

```bash title="Inside devcontainer"
ONSHAPE_API_KEY=your_key_here
ONSHAPE_API_SECRET=your_secret_here
```

`sim` picks this file up automatically. You can also export them directly in your shell if you prefer not to write a file.

## Create the packages

```bash title="Inside devcontainer"
sim create <robot_name> <onshape_url>
```

For example:

```bash title="Inside devcontainer"
sim create arm https://cad.onshape.com/documents/...
```

If the robot's base is fixed in place (an arm, turret, anything bolted down), pass `--attach-to-world`. Without it you'll be prompted interactively:

```bash title="Inside devcontainer"
sim create arm https://cad.onshape.com/documents/... --attach-to-world
```

This downloads the CAD, post-processes the URDF, reduces mesh file sizes, and writes two packages into `robot-sim/`:

```
robot-sim/
  arm_description/
    urdf/arm.urdf
    urdf/arm_control.urdf.xacro
    meshes/
    CMakeLists.txt  package.xml

  arm_bringup/
    launch/arm.launch.py
    config/arm.controller.yaml
    config/arm.rviz
    CMakeLists.txt  package.xml
```

The robot is also registered in `robots.json` so `sim update` can find it later.

## Launch it

```bash title="Inside devcontainer"
sim docker arm
```

## Flags

| Flag | Description |
| --- | --- |
| `--attach-to-world` | Fix `base_link` to the Gazebo world (stationary robots) |
| `--no-attach-to-world` | Explicitly skip — for mobile robots |
| `--no-reduce` | Skip STL mesh decimation (larger files, higher detail) |
| `--output-dir <path>` | Write packages somewhere other than `robot-sim/` |

## Updating an existing robot

When the OnShape CAD changes, pull in the new geometry without touching your bringup config:

```bash title="Inside devcontainer"
sim update arm
```

This replaces only `arm_description/urdf/arm.urdf` and `arm_description/meshes/`. Everything else — your control xacro edits, launch file, controller YAML, RViz config — is left untouched.

## Via GitHub Actions

If you'd rather not run it locally, the **Create new robot** workflow does it on CI and opens a PR.

1. Go to **Actions** > **Create new robot**
2. Click **Run workflow** and fill in the inputs
3. Review and merge the generated PR

:::note
The workflow requires `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY` as repository secrets.
:::

## Troubleshooting

**Missing joints:** Joints must be defined as mates in the OnShape assembly. Check the OnShape model if joints don't appear in the generated controller YAML.

**URDF errors after generation:** See [Robot Packages](../../reference/robot-packages/) for details on what post-processing happens and how to inspect the raw OnShape output.

**Large mesh files:** `sim create` decimates STL triangle counts automatically. If meshes are still too large, simplify the geometry in OnShape before re-running.
