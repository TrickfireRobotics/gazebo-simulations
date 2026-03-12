# genbot - OnShape to ROS2 Simulation Pipeline

`genbot` is a GitHub Actions tool that takes a robot CAD model from [OnShape](https://www.onshape.com/), downloads its URDF via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot), post-processes it for Gazebo simulation, and generates ready-to-build ROS2 packages. It runs via the `generate-urdf` workflow and opens a PR with the results.

## Overview

### Create mode pipeline

Used when adding a new robot for the first time. Requires an OnShape URL. Generates both `_description` and `_bringup` packages and registers the robot in `robots.json`.

```
OnShape CAD Model
    |
    v
1. DOWNLOAD (onshape-to-robot)
    |  Connects to OnShape API with credentials
    |  Downloads URDF (robot.urdf) + mesh files (meshes/*.stl)
    |  Output: raw URDF with relative mesh paths
    |
    v
2. POST-PROCESS (genbot.py)
    |  a) Add xmlns:xacro namespace to <robot> tag
    |  b) Inject xacro properties: mesh_path, controller_config arg
    |  c) Rewrite mesh paths: meshes/foo.stl -> ${mesh_path}/foo.stl
    |  d) Parse URDF to extract all revolute joints + their limits
    |  e) Generate <robot>_control.urdf.xacro:
    |     - ros2_control hardware interface (gz_ros2_control/GazeboSimSystem)
    |     - Per-joint position command + state interfaces
    |     - Gazebo plugin block (libgz_ros2_control-system.so, 60 Hz)
    |  f) Inject <xacro:include> for control xacro into geometry URDF
    |
    v
3. SCAFFOLD (genbot.py)
    |  Renders templates with __ROBOT__ placeholder replaced
    |
    |-- <robot>_description/
    |     urdf/<robot>.urdf                  (post-processed geometry)
    |     urdf/<robot>_control.urdf.xacro    (generated control block)
    |     meshes/                            (copied from download)
    |     CMakeLists.txt, package.xml        (from templates)
    |
    |-- <robot>_bringup/
    |     launch/sim.launch.py            (from template)
    |     config/<robot>.controller.yaml     (from template, joints filled in)
    |     CMakeLists.txt, package.xml        (from templates)
    |
    |-- robots.json                          (registers OnShape coordinates)
```

### Update mode pipeline

Used when the OnShape CAD model has changed and you want to pull in new geometry. Reads the OnShape URL from `robots.json` - no need to re-enter it. Only replaces the geometry URDF and meshes. The control xacro, bringup package, and any manual edits are preserved.

```
robots.json (stored OnShape coordinates)
    |
    v
1. DOWNLOAD (onshape-to-robot)
    |  Same as create - downloads fresh URDF + meshes
    |
    v
2. POST-PROCESS (genbot.py)
    |  Same transforms as create (steps a-c, f)
    |  Control xacro is NOT regenerated
    |
    v
3. REPLACE (genbot.py)
    |  Only these files are overwritten:
    |-- <robot>_description/urdf/<robot>.urdf    (new geometry)
    |-- <robot>_description/meshes/*             (new meshes, old deleted)
    |
    |  These are NOT touched:
    |   <robot>_description/urdf/<robot>_control.urdf.xacro
    |   <robot>_bringup/ (entire package)
    |   robots.json
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

## Two-layer URDF architecture

genbot splits the URDF into two files to keep geometry and control concerns separate:

- **`<robot>.urdf`** - Contains links, joints, visual/collision meshes (from OnShape). Includes a `xacro:include` pointing to the control xacro. This file gets replaced on `update`.
- **`<robot>_control.urdf.xacro`** - Contains `ros2_control` hardware interface definitions, joint command/state interfaces, and the Gazebo `gz_ros2_control` plugin config. This file is generated once during `create` and never overwritten by `update`, so manual edits are preserved.

At build time, xacro merges both files into a single robot description.

## URDF post-processing

The URDF post-processing step in `genbot.py` transforms the raw URDF from `onshape-to-robot` into a format ready for Gazebo simulation. The processing steps are:

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
    "onshapeUrl": "https://trickfire.onshape.com/documents/..."
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
    launch/sim.launch.py
```

After editing templates, newly created robots will use the updated templates. Existing robots are not affected unless you delete and re-create them.

## Setting up RViz

Generated robots do not include an RViz config out of the box. See the [RViz setup guide](./rviz-setup.md) for how to create one and wire it into the launch file.
