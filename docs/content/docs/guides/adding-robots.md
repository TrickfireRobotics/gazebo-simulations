---
title: Adding a New Robot
description: How to generate a ROS 2 package from an OnShape CAD model and get a new robot running in Genesis.
---

`sim create` takes a robot from OnShape and produces a ready-to-build ROS 2 package — no manual URDF editing or package scaffolding required.

## Via GitHub Actions (recommended)

No credentials or local setup needed. The **Create new robot** workflow runs on CI and opens a PR with the generated package.

1. Go to **Actions** → **Create new robot**
2. Click **Run workflow** and fill in the inputs:
    - **Mode:** `create`
    - **Robot name:** unique, lowercase, no spaces (e.g. `arm`)
    - **OnShape URL:** the full document URL from OnShape
    - **Fix robot to world:** yes for stationary robots (arms, turrets), no for mobile
3. Wait for the workflow to finish, then review and merge the generated PR

## Via CLI (developers only)

Running `sim create` locally requires your GitHub username to be listed in [`authorized_users.jsonc`](https://github.com/TrickfireRobotics/gazebo-simulations/blob/main/authorized_users.jsonc). If you're not listed, ask a repo admin to add you.

The container mounts your SSH keys — make sure your GitHub SSH key is set up, then:

```bash title="Terminal"
sim auth
sim create <robot_name> <onshape_url>
```

:::tip
You can use any OnShape API key/secret by placing them in `cli/onshape.env` as `ONSHAPE_API_KEY` and `ONSHAPE_API_SECRET`.
:::

## Flags

| Flag | Description |
| --- | --- |
| `--attach-to-world` | Fix `base_link` to world frame (stationary robots) |
| `--no-attach-to-world` | Explicitly skip — for mobile robots |
| `--no-reduce` | Skip STL mesh decimation (larger files, higher detail) |
| `--output-dir <path>` | Write package somewhere other than `robot-sim/` |

## Updating an existing robot

When the OnShape CAD changes, pull in the new geometry without touching anything else.

**Via CI (recommended):** Actions → **Create new robot** → mode: `update`

**Locally:**

```bash title="Terminal"
sim update arm
```

This replaces only `arm/urdf/arm.urdf` and `arm/meshes/`. The RViz config and anything else you've edited by hand is left untouched.

## Troubleshooting

**Missing joints:** Joints must be defined as mates in the OnShape assembly. Check the model if joints don't appear after generation.

**URDF errors after generation:** Use `--raw` to inspect what OnShape produced before post-processing:

```bash title="Terminal"
sim create arm <url> --raw
# Raw URDF and assets saved to cli/create/tests/arm/

# Re-run post-processing locally without hitting OnShape again:
sim create arm --local
```

**Large mesh files:** `sim create` decimates STL triangle counts automatically. If meshes are still too large, simplify the geometry in OnShape before re-running.

**`sim auth` fails:** Your GitHub username is not in `authorized_users.jsonc`, or it was added but CI hasn't re-encrypted yet. Check the **Re-encrypt Onshape credentials** workflow in Actions.
