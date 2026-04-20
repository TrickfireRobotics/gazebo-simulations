---
title: Genbot
description: CLI tool that downloads robot URDFs from OnShape and generates ready-to-build ROS 2 simulation packages.
---

`genbot` is a CLI tool that takes a robot CAD model from [OnShape](https://www.onshape.com/), downloads its URDF via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot), post-processes it for Gazebo, and generates two ready-to-build ROS 2 packages (`_description` and `_bringup`).

It can be run locally or through the **Generate/Update Robot from OnShape** GitHub Actions workflow.

## Running genbot

All commands follow this pattern:

```bash title="Inside devcontainer"
PYTHONPATH=.github python3 -m genbot <command> [args]
```

For commands that call the OnShape API, pass your credentials:

```bash title="Inside devcontainer"
ONSHAPE_API_KEY=<key> ONSHAPE_API_SECRET=<secret> PYTHONPATH=.github python3 -m genbot <command> [args]
```

### Shortcut: credential file

Create `.github/genbot/onshape.env` with:

```bash title="Inside devcontainer"
ONSHAPE_API_KEY=your_key_here
ONSHAPE_API_SECRET=your_secret_here
```

Then you can just run `genbot <command> [args]` -- the alias handles the rest.

## Commands

### `create` -- new robot from OnShape

Downloads from OnShape and generates both packages from scratch. Registers the robot in `robots.json`. Reduces STL triangle counts by default.

```bash title="Inside devcontainer"
genbot create <robot_name> <onshape_url> [--attach-to-world] [--no-reduce] [--output-dir DIR]
```

| Option | Description |
| --- | --- |
| `--attach-to-world` | Add a fixed joint from `base_link` to the world (for stationary robots) |
| `--no-reduce` | Skip STL triangle decimation |
| `--output-dir` | Write packages to a different directory |

### `update` -- refresh URDF and meshes

Re-downloads from OnShape and replaces **only** the geometry URDF and meshes. The control xacro, bringup package, and manual edits are preserved. Reads the OnShape URL from `robots.json`.

```bash title="Inside devcontainer"
genbot update <robot_name> [--no-reduce] [--output-dir DIR]
```

### `raw` -- download only

Downloads raw URDF + assets into `.github/genbot/tests/<robot_name>/` (gitignored) without generating ROS 2 packages. Useful for inspecting what `onshape-to-robot` produces.

```bash title="Inside devcontainer"
# First time (saves URL to robots.json)
genbot raw <robot_name> <onshape_url>

# Subsequent times (URL read from robots.json)
genbot raw <robot_name>
```

### `local` -- generate from local URDF

Runs the full post-processing and package generation on a local URDF file. No API keys needed.

```bash title="Inside devcontainer"
# From a previous `genbot raw` download
genbot local <robot_name>

# From a specific URDF file
genbot local <robot_name> path/to/robot.urdf [--assets path/to/meshes]
```

## What gets generated

### `create` and `local`

Both packages are written from scratch:

```
<robot>_description/
  urdf/<robot>.urdf                   ← Post-processed geometry URDF
  urdf/<robot>_control.urdf.xacro     ← Generated ros2_control block
  meshes/                             ← STL mesh files (reduced)
  CMakeLists.txt, package.xml

<robot>_bringup/
  launch/<robot>.launch.py            ← Launch orchestration
  config/<robot>.controller.yaml      ← Controller definitions
  config/<robot>.rviz                 ← RViz config template
  CMakeLists.txt, package.xml
```

### `update`

Only these files are replaced:

```
<robot>_description/urdf/<robot>.urdf   ← New geometry
<robot>_description/meshes/*            ← New meshes (old deleted first)
```

Everything else is untouched -- your control xacro edits, launch file customizations, and controller config are safe.

## GitHub Actions workflow

1. Go to **Actions** > **Generate/Update Robot from OnShape**
2. Click **Run workflow** and fill in:

| Input | Description |
| --- | --- |
| `mode` | `create` or `update` |
| `robot_name` | Robot identifier (e.g. `arm`) |
| `onshape_url` | OnShape document URL (required for `create`, ignored for `update`) |
| `attach_to_world` | Fix robot base to the world |

The workflow runs genbot with credentials from repository secrets and opens a PR on branch `genbot/<mode>-<robot_name>`.

**Required repository secrets:**

| Secret | Description |
| --- | --- |
| `ONSHAPE_ACCESS_KEY` | OnShape API key |
| `ONSHAPE_SECRET_KEY` | OnShape API secret |

## URDF post-processing

When genbot processes a URDF from OnShape, it performs several transformations:

1. **Xacro namespace injection** -- wraps the URDF with xacro support so it can include the control xacro
2. **Mesh path rewriting** -- updates all `<mesh>` tags to use `package://<robot>_description/meshes/` paths
3. **Joint/link extraction** -- identifies all joints and links for control generation
4. **Control xacro generation** -- creates a `ros2_control` hardware interface block with position command interfaces and position/velocity state interfaces for every joint
5. **World base link** -- optionally adds a fixed joint from `base_link` to `world` for stationary robots

## robots.json

The robot registry at the repo root tracks all generated robots:

```json
[
    {
        "name": "arm",
        "url": "https://trickfire.onshape.com/documents/...",
        "world_base_link": true
    }
]
```

This file is written by `create` and `raw`, and read by `update` to look up the OnShape URL.

## Code structure

All source lives in `.github/genbot/`:

| File | Responsibility |
| --- | --- |
| `__init__.py` | Path constants (`REPO_ROOT`, `TEMPLATES`, `ROBOTS_JSON`) |
| `__main__.py` | Entry point for `python -m genbot` |
| `cli.py` | Argument parsing and command dispatch |
| `commands.py` | Implementation of `create`, `local`, `raw`, `update` |
| `onshape.py` | OnShape URL parsing + `onshape-to-robot` integration |
| `urdf.py` | URDF post-processing (xacro, mesh paths, control generation) |
| `ros_packages.py` | Package scaffolding from templates |
| `template.py` | `__ROBOT__` token replacement in template files |
| `reduce_stl.py` | STL decimation via `open3d` |
| `credentials.py` | Reads API keys from environment |
| `registry.py` | `robots.json` read/write |
| `log.py` | Logging helpers |
| `templates/` | Template files for generated packages |
