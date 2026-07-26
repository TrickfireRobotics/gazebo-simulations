---
title: Running Chrono
description: How to run Project Chrono SCM terrain simulations.
---

Chrono SCM (Soil Contact Model) terrain simulations run inside the Dev Container, where Project Chrono is pre-built into the image.

## Dev Container

```bash title="Inside devcontainer"
sim chrono run
```

This builds the C++ simulation from `chrono/` (if not already built) and runs it. A Vulkan window opens in the VNC desktop showing the terrain simulation.

## Cleaning

```bash title="Inside devcontainer"
sim chrono clean
```

Deletes `chrono/build/`. Use this to force a clean rebuild.

## Troubleshooting

**Chrono window doesn't appear:**
Chrono uses Vulkan for rendering. Make sure the VNC desktop is running (`localhost:5900`) and that the container has Wayland/display access. If the window still doesn't appear, check the terminal output for Vulkan errors.
