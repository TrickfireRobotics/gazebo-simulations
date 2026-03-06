# genbot - OnShape model to ROS2 package generator

`genbot` is a CLI tool that downloads a robot URDF from OnShape via [`onshape-to-robot`](https://github.com/Rhoban/onshape-to-robot) and creates a complete pair of ROS2 packages (`<robot>_description` and `<robot>_bringup`) that are a baseline for the simulation.

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

```bash
genbot/genbot.py <robot_name> "<onshape_url>"
```

**Example:**

```bash
genbot/genbot.py arm "https://cad.onshape.com/documents/abc123/w/def456/e/ghi789"
```

This will:
1. Download the URDF and meshes from OnShape into a temp directory
2. Parse all `revolute` joints from the URDF
3. Generate `robot-sim/arm_description/` and `robot-sim/arm_bringup/` with all files populated

### Options

| Flag                      | Description                                                                       |
| ------------------------- | --------------------------------------------------------------------------------- |
| `--output-dir PATH`       | Write packages to a different directory (default: `robot-sim/`)                   |
| `--skip-download WORKDIR` | Skip the OnShape download and use an existing `onshape-to-robot` output directory |

`--skip-download` is useful for re-generating the ROS2 packages without re-downloading from OnShape:

```bash
genbot/genbot.py arm "..." --skip-download /tmp/genbot_xyz123
```

## Generated output

```
robot-sim/
  <robot>_description/
    CMakeLists.txt
    package.xml
    urdf/<robot>.urdf
    meshes/               ← copied from onshape-to-robot output
  <robot>_bringup/
    CMakeLists.txt
    package.xml
    config/<robot>.controller.yaml
    launch/gazebo.launch.py
    launch/genesis.launch.py
    genesis/genesis_sim.py
```

The controller YAML is pre-populated with all `revolute` joints found in the URDF. If none are found, a comment placeholder is inserted for manual editing.

## Building and launching

After generation, launch the simulation:

```bash
./scripts/launch_sim.sh <robot>
```

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
    launch/genesis.launch.py
    genesis/genesis_sim.py
```
