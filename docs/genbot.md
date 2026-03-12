# genbot - OnShape model to ROS2 package generator

`genbot` is a CLI tool that downloads a robot URDF from OnShape via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot) and creates or updates ROS2 packages (`<robot>_description` and `<robot>_bringup`) for simulation.

## Setup

### 1. Credentials

Copy the example env file and fill in your OnShape API keys:

```bash
cp genbot/templates/.env.example genbot/.env
```

> [!NOTE]
> `genbot/.env` is gitignored and will never be committed.

### 2. Get the OnShape URL

Open the OnShape document you want to export, copy the full URL from the browser. It should look like:

```
https://cad.onshape.com/documents/<docId>/w/<workspaceId>/e/<elementId>
```

## Usage

### Create a new robot

```bash
genbot/genbot.py create <robot_name> "<onshape_url>"
```

**Example:**

```bash
genbot/genbot.py create arm "https://cad.onshape.com/documents/abc123/w/def456/e/ghi789"
```

This will:
1. Download the URDF and meshes from OnShape into a temp directory
2. Post-process the URDF (add xacro namespace, rewrite mesh paths, extract joints)
3. Generate `robot-sim/<robot>_description/` with geometry URDF + control xacro
4. Generate `robot-sim/<robot>_bringup/` with launch files and controller config
5. Register the robot in `robots.json`

### Update an existing robot

```bash
genbot/genbot.py update <robot_name>
```

**Example:**

```bash
genbot/genbot.py update arm
```

This will:
1. Look up the OnShape coordinates from `robots.json`
2. Download the latest URDF and meshes
3. Replace only `<robot>_description/urdf/<robot>.urdf` and `<robot>_description/meshes/`
4. Leave `_bringup` and the control xacro untouched

### Options

| Flag                      | Description                                                                       |
| ------------------------- | --------------------------------------------------------------------------------- |
| `--output-dir PATH`       | Write packages to a different directory (default: `robot-sim/`)                   |
| `--skip-download WORKDIR` | Skip the OnShape download and use an existing `onshape-to-robot` output directory |

`--skip-download` is useful for re-generating the ROS2 packages without re-downloading from OnShape:

```bash
genbot/genbot.py create arm "..." --skip-download /tmp/genbot_xyz123
genbot/genbot.py update arm --skip-download /tmp/genbot_xyz123
```

## Generated output

### Create mode

```
robot-sim/
  <robot>_description/
    CMakeLists.txt
    package.xml
    urdf/<robot>.urdf                    ← geometry URDF with xacro includes
    urdf/<robot>_control.urdf.xacro      ← ros2_control + gazebo plugin block
    meshes/                              ← copied from onshape-to-robot output
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

## Robot Registry — `robots.json`

The file `robots.json` at the repo root maps robot names to their OnShape document coordinates. It is written automatically by `create` mode and read by `update` mode.

## Shared Utilities — `sim_common`

The `robot-sim/sim_common/` package provides shared launch utilities (`log`, `err`, `get_asset`) used by all `_bringup` packages, avoiding code duplication across launch files.

## Building and launching

After generation, build and launch the simulation:

```bash
cd robot-sim && colcon build --packages-select sim_common <robot>_description <robot>_bringup
./scripts/launch_sim.sh <robot>
```

## GitHub Actions

The workflow `.github/workflows/generate-urdf.yaml` supports both `create` and `update` modes via `workflow_dispatch`. It runs genbot and opens a PR with the changes.

## Templates

All generated file content lives in `genbot/templates/`. The placeholder `__ROBOT__` is substituted with the robot name at generation time. If you want to change the structure of generated packages (e.g. add a new launch file), edit the templates directly.

```
genbot/templates/
  .env.example
  description/
    CMakeLists.txt
    package.xml
  bringup/
    CMakeLists.txt
    package.xml
    config/controller.yaml
    launch/gazebo.launch.py
```
