# Contributing

Thanks for wanting to contribute! This guide covers the repo layout and how to work on each part.

## Repo structure

```
gazebo-simulations/
├── robot-sim/        # ROS 2 workspace — simulation packages
├── cli/              # Python CLI for building and launching simulations
├── docker/           # Dockerfile and Docker Compose files
├── docs/             # Documentation site (Astro / Starlight)
├── environment.yml   # Conda environment for sim native
├── robots.json       # Robot configuration registry
└── pyproject.toml    # Python tooling config
```

## Projects

### `robot-sim/` — Simulation

The ROS 2 workspace. Built with `colcon` either inside the conda env (`sim native`) or inside the Docker container (`sim docker`).

**Packages:**
- `<robot>/` — URDF, meshes, and RViz config for each robot (one package per robot)
- `sim_common/` — shared Genesis simulation node, joint GUI, launch utils

When adding or modifying a package, keep `package.xml` and `CMakeLists.txt` up to date so `colcon` can resolve dependencies.

### `cli/` — Simulation CLI

Python package providing the `sim` CLI:

- `cli.py` — entry point and argument parsing
- `native.py` — `sim native`: conda bootstrap + colcon build + Genesis launch
- `docker.py` — `sim docker`: colcon build + Genesis launch inside Docker
- `create/` — `sim create` / `sim update`: OnShape download, URDF processing, package scaffolding
- `paths.py` — workspace path constants
- `output.py` — terminal output helpers (`info`, `warn`, `die`)

### `docker/` — Docker environment

`Dockerfile` builds the image used by `sim docker` and the VS Code Dev Container. The image includes ROS 2 Humble, Genesis, and a full VNC/noVNC display stack.

### `docs/` — Documentation site

An [Astro Starlight](https://starlight.astro.build/) site published to GitHub Pages. Source lives in `docs/content/docs/` and follows the existing directory structure (`setup/`, `guides/`, `reference/`).

```bash
# from docs/
npm install
npm run dev     # local dev server
npm run build   # production build
```

## Dev setup

There are two ways to work on `robot-sim/` code:

- **Native:** run `sim native <robot>` — bootstraps a conda env at `.conda/` inside the repo on first run.
- **Docker:** open in the VS Code Dev Container and run `sim docker <robot>`.

For `docs/` changes, only Node.js is required — no ROS or container needed.

## Formatting

Formatters run automatically on save in VS Code. Install the recommended extensions when prompted.

| Language | Formatter |
|---|---|
| Python | [Ruff](https://docs.astral.sh/ruff/) (`charliermarsh.ruff`) |
| Astro | Astro (`astro-build.astro-vscode`) |
| JS / TS / JSON / JSONC | Prettier (`esbenp.prettier-vscode`) — 4-space indentation |
| XML | XML Tools (`DotJoshJohnson.xml`) |
| Shell | shfmt (`mkhl.shfmt`) |

Run Ruff manually before submitting:

```bash
ruff check .
ruff format .
```

Configuration lives in `pyproject.toml`. The `robot-sim/build`, `install`, `log`, and `.conda/` directories are excluded automatically.
