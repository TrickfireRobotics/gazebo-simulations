# genbot - OnShape to ROS2 Simulation Pipeline

`genbot` is a GitHub Actions tool that takes a robot CAD model from [OnShape](https://www.onshape.com/), downloads its URDF via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot), post-processes it for Gazebo simulation, and generates ready-to-build ROS2 packages. It runs via the `generate-urdf` workflow and opens a PR with the results.

## Overview

The pipeline works in three stages:

1. **Download** - `onshape-to-robot` exports the CAD model as a URDF with mesh files
2. **Post-process** - genbot transforms the raw URDF into a simulation-ready format (xacro namespaces, dynamic mesh paths, ros2_control blocks, Gazebo plugins)
3. **Generate** - genbot scaffolds two ROS2 packages (`<robot>_description` and `<robot>_bringup`) with all the files needed to build and launch a Gazebo simulation

```
OnShape CAD Model
    |
    v
onshape-to-robot          (downloads URDF + meshes)
    |
    v
urdf_postprocess.py        (transforms URDF for Gazebo)
    |-- adds xacro namespace and properties
    |-- rewrites mesh paths to use package:// URIs
    |-- extracts revolute joints
    |-- generates ros2_control xacro with Gazebo plugin
    |-- injects control include into geometry URDF
    |
    v
genbot.py                  (scaffolds ROS2 packages)
    |-- <robot>_description/   (URDF, meshes, control xacro)
    |-- <robot>_bringup/       (launch files, controller config)
    |-- robots.json            (registers robot for future updates)
```

## Usage (GitHub Actions)

1. Go to **Actions** > **Generate/Update Robot from OnShape**
2. Click **Run workflow**
3. Fill in the inputs:

| Input         | Description                                                    |
| ------------- | -------------------------------------------------------------- |
| `mode`        | `create` or `update`                                           |
| `robot_name`  | Robot identifier (e.g. `arm`, `rover`)                         |
| `onshape_url` | Full OnShape URL (required for `create`, ignored for `update`) |

The OnShape URL should look like:

```
https://cad.onshape.com/documents/<docId>/w/<workspaceId>/e/<elementId>
```

### What the workflow does

1. Checks out the repo
2. Installs Python 3.11 and `onshape-to-robot`
3. Validates inputs (URL required for create, robot must exist in `robots.json` for update)
4. Runs genbot with OnShape credentials from repository secrets
5. Opens a PR on branch `genbot/<mode>-<robot_name>` with the generated/updated files

The PR can then be reviewed and merged like any other code change.

### Required repository secrets

| Secret               | Description        |
| -------------------- | ------------------ |
| `ONSHAPE_ACCESS_KEY` | OnShape API key    |
| `ONSHAPE_SECRET_KEY` | OnShape API secret |

You can get API keys from [OnShape Developer Portal](https://dev-portal.onshape.com/keys).

## Generated output

### Create mode

```
robot-sim/
  <robot>_description/
    CMakeLists.txt
    package.xml
    urdf/<robot>.urdf                    <-- geometry URDF with xacro includes
    urdf/<robot>_control.urdf.xacro      <-- ros2_control + gazebo plugin block
    meshes/                              <-- copied from onshape-to-robot output
  <robot>_bringup/
    CMakeLists.txt
    package.xml
    config/<robot>.controller.yaml
    launch/gazebo.launch.py
```

### Update mode

Only these files are replaced:
- `<robot>_description/urdf/<robot>.urdf`
- `<robot>_description/meshes/*`

## Two-layer URDF architecture

genbot splits the URDF into two files to keep geometry and control concerns separate:

- **`<robot>.urdf`** - Contains links, joints, visual/collision meshes (from OnShape). Includes a `xacro:include` pointing to the control xacro. This file gets replaced on `update`.
- **`<robot>_control.urdf.xacro`** - Contains `ros2_control` hardware interface definitions, joint command/state interfaces, and the Gazebo `gz_ros2_control` plugin config. This file is generated once during `create` and never overwritten by `update`, so manual edits are preserved.

At build time, xacro merges both files into a single robot description.

## URDF post-processing

The `urdf_postprocess.py` module transforms the raw URDF from `onshape-to-robot` into a format ready for Gazebo simulation. The processing steps are:

1. **Xacro namespace** - adds `xmlns:xacro` to the `<robot>` tag
2. **Xacro properties** - injects a `mesh_path` property (`package://<robot>_description/meshes`) and a `controller_config` arg
3. **Mesh path rewriting** - converts relative `meshes/foo.stl` paths to `${mesh_path}/foo.stl` so meshes resolve correctly via ROS package paths
4. **Joint extraction** - parses all revolute joints and their limits, used to generate the controller config
5. **Control xacro generation** - creates the `<robot>_control.urdf.xacro` with:
   - `ros2_control` hardware interface using `gz_ros2_control/GazeboSimSystem`
   - Per-joint position command interface with min/max bounds
   - Per-joint state interfaces (position, velocity, effort)
   - Gazebo plugin block (`libgz_ros2_control-system.so`) at 60 Hz update rate
6. **Control include injection** - appends `<xacro:include>` before `</robot>` to pull in the control xacro

## Robot registry - `robots.json`

The file `robots.json` at the repo root maps robot names to their OnShape document coordinates:

```json
{
  "arm": {
    "documentId": "...",
    "workspaceId": "...",
    "elementId": "...",
    "onshapeUrl": "https://cad.onshape.com/documents/..."
  }
}
```

This registry is written automatically by `create` mode and read by `update` mode so you don't need to re-enter the OnShape URL.

## Shared utilities - `sim_common`

The `robot-sim/sim_common/` package provides shared launch utilities used by all `_bringup` packages:

| Function              | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `log(msg)`            | Green info log for launch files                                             |
| `err(msg)`            | Red error log, exits with code 1                                            |
| `get_asset(pkg, ...)` | Resolves file path inside a ROS2 package share directory, errors if missing |

This avoids duplicating path resolution and logging logic across launch files.

## Templates

All generated file content lives in `genbot/templates/`. The placeholder `__ROBOT__` is substituted with the robot name at generation time. If you want to change the structure of generated packages (e.g. add a new launch file or change the controller config), edit the templates directly.

```
genbot/templates/
  description/
    CMakeLists.txt
    package.xml
  bringup/
    CMakeLists.txt
    package.xml
    config/controller.yaml
    launch/gazebo.launch.py
```

After editing templates, newly created robots will use the updated templates. Existing robots are not affected unless you delete and re-create them.
