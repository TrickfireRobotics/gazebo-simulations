---
title: Robot Packages
description: What sim create generates, how URDF post-processing works, and how the robot registry is structured.
---

Reference for `sim create` and `sim update` — what they produce and how the underlying pipeline works.

## Generated package layout

`sim create` writes a single package into `robot-sim/`:

```
<robot>/
  urdf/<robot>.urdf      ← Post-processed geometry URDF
  meshes/                ← Decimated STL files
  config/<robot>.rviz    ← RViz visualization config
  CMakeLists.txt
  package.xml
```

The package is built with `ament_cmake`. `CMakeLists.txt` installs `urdf/`, `meshes/`, and `config/` to the share directory so ROS 2 can find them at runtime.

## URDF post-processing

`sim create` downloads a raw URDF from OnShape via `onshape-to-robot`, then transforms it before writing the final file:

1. **Xacro namespace** — adds `xmlns:xacro` to the `<robot>` tag
2. **Mesh path rewriting** — rewrites `filename="package://assets/foo.stl"` to `filename="package://<robot>/meshes/foo.stl"` so paths resolve correctly in ROS
3. **World base link** — if `--attach-to-world`, inserts a `world` link and a fixed `world_to_base_link` joint before the first `<link>`
4. **Joint extraction** — finds all `revolute` joints with their limits (used for reporting; genesis_sim discovers joints at runtime)
5. **Reindent** — normalises indentation from 2-space (OnShape default) to 4-space

## What `sim update` touches

Only geometry — anything you've edited by hand is preserved:

| File | `sim update` |
| --- | --- |
| `<robot>/urdf/<robot>.urdf` | Replaced |
| `<robot>/meshes/` | Replaced (old files deleted first) |
| `<robot>/config/<robot>.rviz` | **Untouched** |

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

If the generated package looks wrong, inspect what OnShape produced before post-processing:

```bash title="Terminal"
sim create <robot_name> <onshape_url> --raw
```

This saves the raw URDF and assets to `cli/create/tests/<robot_name>/` (gitignored) without post-processing. Once you've identified a fix, re-run on the local files without hitting OnShape again:

```bash title="Terminal"
sim create <robot_name> --local
```

## Code structure

| File | Responsibility |
| --- | --- |
| `cli/create/__init__.py` | `create()` / `update()` entry points, credential loading |
| `cli/create/commands.py` | `cmd_create`, `cmd_update`, `cmd_local`, `cmd_raw` |
| `cli/create/onshape.py` | URL parsing, `onshape-to-robot` invocation |
| `cli/create/urdf.py` | All URDF transforms (steps 1–5 above) |
| `cli/create/ros_packages.py` | File scaffolding from templates |
| `cli/create/template.py` | `__ROBOT__` token replacement |
| `cli/create/reduce_stl.py` | STL decimation via `open3d` |
| `cli/create/credentials.py` | `ONSHAPE_API_KEY` / `ONSHAPE_API_SECRET` from env |
| `cli/create/registry.py` | `robots.json` read/write |
| `cli/create/templates/` | Template files for generated packages |
