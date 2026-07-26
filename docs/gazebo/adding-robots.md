---
title: Adding a New Robot
description: How to generate ROS 2 packages from an OnShape CAD model and get a new robot running in Gazebo.
---

`sim gazebo create` takes a robot from OnShape and produces two ready-to-build ROS 2 packages - no manual URDF editing or package scaffolding required.

## Via GitHub Actions (recommended)

You do not need any credentials or local setup. The **Create new robot** workflow runs on CI and opens a PR with the generated packages.

1. Go to **Actions** and then to **Create new robot**
2. Click **Run workflow** and fill in the inputs:
    - **Mode:** `create`
    - **Robot name:** unique, lowercase, no spaces (e.g. `arm`)
    - **OnShape URL:** the full document URL from OnShape
    - **Fix robot to world:** yes for stationary robots (arms, turrets), no for mobile
3. Wait for the workflow to finish, then review and merge the generated PR

## Via CLI (developers only)

Running `sim gazebo create` locally requires authentication via the TrickFire dashboard:

:::note[note]
This method uses your GitHub `ssh` key. Make sure it is set up. In the Dev Container, your SSH keys are mounted automatically from the host.
:::

```bash title="Terminal"
sim gazebo auth
```

Then you can create the robot using:

```bash title="Terminal"
sim gazebo create <robot_name> <onshape_url>
```

:::tip[Tip]
This sim will work with any Onshape API key and secret as long as you put them in the `cli/onshape.env` file under `ONSHAPE_API_KEY` and `ONSHAPE_API_SECRET` (in standard env format). The above is just for TrickFire specific robots.
:::

## Flags

| Flag                   | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| `--attach-to-world`    | Fix `base_link` to the Gazebo world (stationary robots) |
| `--no-attach-to-world` | Explicitly skip - for mobile robots                     |
| `--no-reduce`          | Skip STL mesh decimation (larger files, higher detail)  |
| `--output-dir <path>`  | Write packages somewhere other than `gazebo/`           |

## Updating an existing robot

When the OnShape CAD changes, pull in the new geometry without touching your bringup config.

**Via CI (recommended):** Actions → **Create new robot** → mode: `update`

**Locally:**

```bash title="Terminal"
sim gazebo update arm
```

This replaces only `arm_description/urdf/arm.urdf` and `arm_description/meshes/`. Everything else - your control xacro edits, launch file, controller YAML, RViz config - is left untouched.

## Troubleshooting

**Missing joints:** Joints must be defined as mates in the OnShape assembly. Check the OnShape model if joints don't appear in the generated controller YAML.

**URDF errors after generation:** See [Robot Packages](../../reference/robot-packages/) for details on what post-processing happens and how to inspect the raw OnShape output.

**Large mesh files:** `sim gazebo create` decimates STL triangle counts automatically. If meshes are still too large, simplify the geometry in OnShape before re-running.

**`sim gazebo auth` fails with "no access":** Your API key may be invalid or expired. Generate a new one at [dashboard.trickfirerobotics.com](https://dashboard.trickfirerobotics.com) → Settings → CLI access.
