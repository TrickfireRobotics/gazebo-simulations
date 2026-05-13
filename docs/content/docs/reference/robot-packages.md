---
title: Robot Packages
description: What sim create generates, how URDF post-processing works, and how the robot registry is structured.
---

Reference for `sim create` and `sim update` - what they produce and how the underlying pipeline works.

## Generated package layout

`sim create` writes two packages into `robot-sim/`:

```
<robot>_description/
  urdf/<robot>.urdf                  ← Post-processed geometry URDF
  urdf/<robot>_control.urdf.xacro   ← ros2_control hardware interface
  meshes/                            ← Decimated STL files
  CMakeLists.txt
  package.xml

<robot>_bringup/
  launch/<robot>.launch.py           ← Launch orchestration
  config/<robot>.controller.yaml     ← Joint controller definitions
  config/<robot>.rviz                ← RViz config
  CMakeLists.txt
  package.xml
```

The `_description` / `_bringup` split is a ROS convention: description holds the robot model (changes when CAD changes), bringup holds runtime config (things you tune during development). `sim update` can safely replace the description without touching bringup.

## URDF post-processing

`sim create` downloads a raw URDF from OnShape via `onshape-to-robot`, then runs it through several transforms before writing the final files:

1. **Xacro namespace** - adds `xmlns:xacro` to the `<robot>` tag so the file can use xacro macros
2. **Mesh path rewriting** - rewrites `filename="package://assets/foo.stl"` to `filename="${mesh_path}/foo.stl"` so paths resolve correctly in ROS
3. **World base link** - if `--attach-to-world`, inserts a `world` link and a fixed `world_to_base_link` joint before the first `<link>`
4. **Joint extraction** - finds all `revolute` joints with their limits
5. **Control xacro generation** - produces `<robot>_control.urdf.xacro` with a `ros2_control` block containing `position` command interfaces and `position`/`velocity`/`effort` state interfaces for every joint
6. **Control include injection** - appends `<xacro:include>` for the control xacro at the end of the geometry URDF
7. **Reindent** - normalises indentation from 2-space (OnShape default) to 4-space

## What `sim update` touches

Only geometry - everything authored by hand is preserved:

| File                                                  | `sim update`                       |
| ----------------------------------------------------- | ---------------------------------- |
| `<robot>_description/urdf/<robot>.urdf`               | Replaced                           |
| `<robot>_description/meshes/`                         | Replaced (old files deleted first) |
| `<robot>_description/urdf/<robot>_control.urdf.xacro` | **Untouched**                      |
| `<robot>_bringup/` (all files)                        | **Untouched**                      |

## robots.json

`robots.json` at the repo root is the robot registry. `sim create` writes to it; `sim update` reads from it to find the OnShape URL.

```json
[
    {
        "name": "arm",
        "url": "https://cad.onshape.com/documents/...",
        "world_base_link": true
    }
]
```

## Debugging raw OnShape output

If the generated packages look wrong, inspect what OnShape actually produced before post-processing:

```bash title="Inside devcontainer"
sim create <robot_name> <onshape_url> --raw
```

This downloads the raw URDF and assets into `cli/create/tests/<robot_name>/` (gitignored) without running any post-processing. Inspect `robot.urdf` there to see what OnShape produced.

Once you've identified a fix, re-run the full generation on those local files without hitting OnShape again:

```bash title="Inside devcontainer"
sim create <robot_name> --local
```

## Code structure

| File                         | Responsibility                                           |
| ---------------------------- | -------------------------------------------------------- |
| `cli/create/__init__.py`     | `create()` / `update()` entry points, credential loading |
| `cli/create/commands.py`     | `cmd_create`, `cmd_update`, `cmd_local`, `cmd_raw`       |
| `cli/create/onshape.py`      | URL parsing, `onshape-to-robot` invocation               |
| `cli/create/urdf.py`         | All URDF transforms (steps 1–7 above)                    |
| `cli/create/ros_packages.py` | File scaffolding from templates                          |
| `cli/create/template.py`     | `__ROBOT__` token replacement                            |
| `cli/create/reduce_stl.py`   | STL decimation via `open3d`                              |
| `cli/create/credentials.py`  | `ONSHAPE_API_KEY` / `ONSHAPE_API_SECRET` from env        |
| `cli/create/registry.py`     | `robots.json` read/write                                 |
| `cli/create/templates/`      | Template files for generated packages                    |
