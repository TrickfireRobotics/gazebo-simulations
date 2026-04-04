# genbot

`genbot` is a CLI tool that takes a robot CAD model from [OnShape](https://www.onshape.com/), downloads its URDF via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot), post-processes it for Gazebo simulation, and generates ready-to-build ROS2 packages.

It runs locally or via the `generate-urdf` GitHub Actions workflow, which opens a PR with the results.

## Commands

| Command | What it does |
| ------- | ------------ |
| `create` | Download from OnShape and generate packages from scratch |
| `update` | Re-download from OnShape and refresh only the URDF and meshes |
| `raw` | Download raw URDF + assets from OnShape, no package generation |
| `local` | Generate packages from a local URDF, no API calls |

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

| Input | Description |
| ----- | ----------- |
| `mode` | `create` or `update` |
| `robot_name` | Robot identifier (e.g. `arm`) |
| `onshape_url` | Full OnShape URL (required for `create`, ignored for `update`) |

The workflow checks out the repo, installs dependencies, runs genbot with credentials from repository secrets, and opens a PR on branch `genbot/<mode>-<robot_name>`.

### Required secrets

| Secret | Description |
| ------ | ----------- |
| `ONSHAPE_ACCESS_KEY` | OnShape API key |
| `ONSHAPE_SECRET_KEY` | OnShape API secret |

## RViz

Generated robots include an RViz config template (`config/<robot>.rviz`). See the [RViz setup guide](./rviz-setup.md) for how to wire it into the launch file.
