---
title: Genbot
description: CLI tool that downloads a robot URDF from OnShape and generates ready-to-build ROS2 packages.
---

# genbot

`genbot` is a CLI tool that takes a robot CAD model from [OnShape](https://www.onshape.com/), downloads its URDF via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot), post-processes it for Gazebo simulation, and generates ready-to-build ROS2 packages.

It runs locally or via the `generate-urdf` GitHub Actions workflow, which opens a PR with the results.

## Commands

| Command  | What it does                                                   |
| -------- | -------------------------------------------------------------- |
| `create` | Download from OnShape and generate packages from scratch       |
| `update` | Re-download from OnShape and refresh only the URDF and meshes  |
| `raw`    | Download raw URDF + assets from OnShape, no package generation |
| `local`  | Generate packages from a local URDF, no API calls              |

All commands are run as:

```bash
PYTHONPATH=.github python3 -m genbot <command> [args]
```

Commands that require Onshape keys are ran like this, passing in the keys:

```bash
ONSHAPE_API_KEY=<your_key> ONSHAPE_API_SECRET=<your_secret> PYTHONPATH=.github python3 -m genbot <command> [args]
```

If you find this too long, don't worry, me too, thats why ther's an alias for it. Make a `.github/genbot/onshape.env` file that includes the key and sectet vars, and then you can just run `genbot <command> [args]`.

## Commands

### `raw`: Download from OnShape

Downloads raw URDF + assets into `.github/genbot/tests/<robot_name>/` (gitignored) without generating any ROS2 packages. For the initial download you need to pass the OnShape URL — after that it's saved in `robots.json` and you can omit it.

```bash
# First time
ONSHAPE_API_KEY=<your_key> ONSHAPE_API_SECRET=<your_secret> PYTHONPATH=.github python3 -m genbot raw <robot_name> https://cad.onshape.com/documents/...

# Subsequent times
ONSHAPE_API_KEY=<your_key> ONSHAPE_API_SECRET=<your_secret> PYTHONPATH=.github python3 -m genbot raw <robot_name>
```

### `local`: Generate from local files

Runs the full post-processing and scaffolding pipeline on a local URDF with no API calls or keys needed. The typical use is to run this after `raw` — if you haven't moved the downloaded files, you can just pass the robot name and it will find them automatically. You can also point at any URDF; meshes are assumed to be in `assets/` next to it, or override with `--assets`.

```bash
# Using raw files from `genbot raw`
PYTHONPATH=.github python3 -m genbot local <robot_name>

# Or point at a specific URDF
PYTHONPATH=.github python3 -m genbot local <robot_name> path/to/robot.urdf
```

> [!TIP]
> Use `--output-dir <directory>` to write somewhere else and avoid overwriting the real packages.

### `create`: New robot from OnShape

Downloads from OnShape and generates both packages in one step. Registers the robot in `robots.json`. Reduces STL triangle counts by default (pass `--no-reduce` to skip).

```bash
ONSHAPE_API_KEY=<your_key> ONSHAPE_API_SECRET=<your_secret> PYTHONPATH=.github python3 -m genbot create <robot_name> <onshape_url> [--output-dir DIR] [--no-reduce]
```

### `update`: Refresh URDF and meshes

Re-downloads from OnShape and replaces only the geometry URDF and meshes. The control xacro, bringup package, and any manual edits are left untouched. Reads the OnShape URL from `robots.json`. Reduces STL triangle counts by default (pass `--no-reduce` to skip).

```bash
ONSHAPE_API_KEY=<your_key> ONSHAPE_API_SECRET=<your_secret> PYTHONPATH=.github python3 -m genbot update <robot_name> [--output-dir DIR] [--no-reduce]
```

## What gets generated

### `create` and `local`

Both packages are written from scratch:

```
<robot>_description/
  urdf/<robot>.urdf                   ← post-processed geometry URDF
  urdf/<robot>_control.urdf.xacro     ← generated ros2_control block
  meshes/                             ← STL files
  CMakeLists.txt, package.xml

<robot>_bringup/
  launch/<robot>.launch.py
  config/<robot>.controller.yaml
  config/<robot>.rviz
  CMakeLists.txt, package.xml
```

### `update`

Only these files are overwritten:

```
<robot>_description/urdf/<robot>.urdf   ← new geometry
<robot>_description/meshes/*            ← new meshes (old ones deleted)
```

These are **not** touched:

```
<robot>_description/urdf/<robot>_control.urdf.xacro
<robot>_bringup/  (entire package)
robots.json
```

## GitHub Actions workflow

The `generate-urdf` workflow runs `create` or `update` on GitHub and opens a PR with the results.

1. Go to **Actions** > **Generate/Update Robot from OnShape**
2. Click **Run workflow** and fill in:

| Input         | Description                                                    |
| ------------- | -------------------------------------------------------------- |
| `mode`        | `create` or `update`                                           |
| `robot_name`  | Robot identifier (e.g. `arm`)                                  |
| `onshape_url` | Full OnShape URL (required for `create`, ignored for `update`) |

The workflow checks out the repo, installs dependencies, runs genbot with credentials from repository secrets, and opens a PR on branch `genbot/<mode>-<robot_name>`.

### Required secrets

| Secret               | Description        |
| -------------------- | ------------------ |
| `ONSHAPE_ACCESS_KEY` | OnShape API key    |
| `ONSHAPE_SECRET_KEY` | OnShape API secret |

## RViz

Generated robots include an RViz config template (`config/<robot>.rviz`). See the [RViz setup guide](../guides/rviz-setup) for how to wire it into the launch file.

## Code structure

All source lives under `.github/genbot/`.

| File              | Responsibility                                                                                                                         |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --- | -------- | ---------------------------------------------------- |
| `__init__.py`     | Package init — defines shared path constants (`REPO_ROOT`, `TEMPLATES`, `ROBOTS_JSON`)                                                 |
| `__main__.py`     | Entry point for `python -m genbot`; just calls `cli.main()`                                                                            |     | `cli.py` | Argument parsing and command dispatch via `argparse` |
| `commands.py`     | Implementation of every subcommand (`cmd_create`, `cmd_local`, `cmd_raw`, `cmd_update`)                                                |
| `onshape.py`      | OnShape integration — parses document URLs and shells out to `onshape-to-robot`                                                        |
| `urdf.py`         | URDF post-processing — injects xacro namespace/properties, rewrites mesh paths, extracts joints/links, generates `_control.urdf.xacro` |
| `ros_packages.py` | Generates and updates the `_description` and `_bringup` ROS2 packages from processed URDF + templates                                  |
| `template.py`     | Template rendering — replaces `__ROBOT__` (and other `__KEY__` tokens) in template files                                               |
| `reduce_stl.py`   | STL decimation via `open3d` — reduces triangle counts to shrink mesh file sizes                                                        |
| `credentials.py`  | Reads `ONSHAPE_API_KEY` / `ONSHAPE_API_SECRET` from the environment                                                                    |
| `registry.py`     | Reads and writes the `robots.json` registry (robot name → OnShape URL)                                                                 |
| `log.py`          | Thin logging helpers: `info()`, `warn()`, `err()` (err exits with code 1)                                                              |
| `templates/`      | Template files copied and rendered into generated packages (`_description` and `_bringup` skeletons)                                   |
