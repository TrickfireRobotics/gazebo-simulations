# Contributing

Thanks for wanting to contribute to this repo! This guide covers the layout of the repo and how to work on each part.

## Repo structure

```
gazebo-simulations/
├── robot-sim/       # ROS 2 workspace - simulation packages
├── docs/            # Documentation site (Astro / Starlight)
├── scripts/         # Shell scripts for launching and managing the sim
├── robots.json      # Robot configuration registry
└── pyproject.toml   # Python tooling config
```

## Projects

### `robot-sim/` - Simulation

The ROS 2 workspace containing the Gazebo Fortress simulation packages. Built with `colcon` inside the Dev Container.

**Packages:**
- `arm_bringup` - launch files
- `arm_description` - URDF/SDF models and worlds
- `sim_common` - shared ROS utilities and configs
- `sim_worlds` - Gazebo world definitions

When adding or modifying a package, keep `package.xml` and `CMakeLists.txt` up to date so `colcon` can resolve build order and dependencies.

See [robot-sim/README.md](robot-sim/README.md) for a deeper breakdown and build notes.

### `docs/` - Documentation site

An [Astro Starlight](https://starlight.astro.build/) site published to GitHub Pages. Source lives in `docs/content/`.

```bash
# from docs/
npm install
npm run dev     # local dev server
npm run build   # production build
```

Content pages live in `docs/content/docs/` and follow the existing directory structure (`guides/`, `reference/`, etc.).

### `scripts/` - Helper scripts

Shell scripts used to manage the Dev Container and simulation:

| Script | Purpose |
|---|---|
| `launch_sim.sh` | Launch the simulation |
| `attach_to_container.sh` | Attach a shell to the running container |
| `start_x_server.sh` | Start the X display server (Linux/WSL) |
| `clean_build.sh` | Full clean and rebuild of the ROS workspace |

## Dev setup

The simulation runs inside a Docker Dev Container. Follow the [Getting Started](https://trickfirerobotics.github.io/gazebo-simulations/guides/getting-started/) guide to set up your environment before making changes to `robot-sim/`.

For `docs/` changes, only Node.js is required, no container needed.

## Python style

Python code is linted and formatted with [ruff](https://docs.astral.sh/ruff/). Run it before submitting:

```bash
ruff check .
ruff format .
```

Configuration lives in `pyproject.toml`. The `robot-sim/build`, `install`, and `log` directories are excluded automatically.
