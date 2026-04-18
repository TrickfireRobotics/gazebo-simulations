---
title: Dev Notes
description: Internal notes and tips for contributors.
---

# Community `apt` repository

It can happen that a `ROS` plugin seems to be not installable by `apt`. This is because some of them are not in the main repository, but in another one called `universe`. To enable it, run these commands. I am pretty sure you have to run them in each new shell when you want to install something from it.

```bash
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y universe
apt-get update
```

# How to set/read camera info using CLI commands

To set camera position use this format of command:

```bash
gz service -s /gui/move_to/pose --reqtype gz.msgs.GUICamera --reptype gz.msgs.Boolean --timeout 2000 --req "pose: {position: {x: 0.0, y: -2.0, z: 2.0} orientation: {x: -0.2706, y: 0.2706, z: 0.6533, w: 0.6533}}"
```

To read camera position use this topic listener:

```bash
gz topic -e -t /gui/camera/pose
```
