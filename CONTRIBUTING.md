# Contributing

Thanks for wanting to contribute to this repo! This guide covers the layout of the repo and how to work on each part.

## Repo structure

```
gazebo-simulations/
├── robot-sim/       # ROS 2 workspace - simulation packages
├── cli/             # Python CLI for building and launching simulations
├── pixi.toml        # Native environment definition (ROS 2 Jazzy + Gazebo Harmonic)
├── robots.json      # Robot configuration registry
└── pyproject.toml   # Python tooling config
```

## Projects

### `robot-sim/` - Simulation

The ROS 2 workspace containing the Gazebo Harmonic simulation packages. Built with `colcon` via the native pixi environment or the Dev Container.

**Packages:**

- `<robot>_bringup` - launch files
- `<robot>_description` - URDF/SDF models and worlds
- `sim_common` - shared ROS utilities and configs
- `sim_worlds` - Gazebo world definitions

When adding or modifying a package, keep `package.xml` and `CMakeLists.txt` up to date so `colcon` can resolve build order and dependencies.

### `docs/` - Documentation site

Go look at the [trickfire-docs documentation](https://docs.trickfirerobotics.com/trickfire-docs/) for more info.

### `cli/` - Simulation CLI

Python package providing the `sim` CLI command:

- `cli.py` - Main entry point and argument parsing
- `native.py` - `sim native` build and launch logic (pixi environment)
- `docker.py` - `sim docker` build and launch logic (Dev Container)
- `create/` - `sim create` / `sim update` implementation (OnShape download, URDF processing, package scaffolding)
- `paths.py` - Workspace path utilities
- `output.py` - Terminal output helpers (`info`, `warn`, `die`)

## Dev setup

The primary workflow uses pixi for a self-contained native environment. Follow the [Getting Started](https://trickfirerobotics.github.io/gazebo-simulations/setup/getting-started/) guide.

For `docs/` changes, only Node.js is required.

## Formatting

All formatters run automatically on save in VS Code. Install the recommended extensions when prompted.

| Language               | Formatter                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Python                 | [Ruff](https://docs.astral.sh/ruff/) (`charliermarsh.ruff`)                                                       |
| Astro                  | Astro (`astro-build.astro-vscode`)                                                                                |
| JS / TS / JSON / JSONC | Prettier (`esbenp.prettier-vscode`) - follow the project's Prettier configuration (including 4-space indentation) |
| XML                    | XML Tools (`DotJoshJohnson.xml`)                                                                                  |
| Dockerfile             | Docker (`ms-azuretools.vscode-containers`)                                                                        |

For Python, you can also run Ruff manually before submitting:

```bash
ruff check .
ruff format .
```

Configuration lives in `pyproject.toml`. The `robot-sim/build`, `install`, and `log` directories are excluded automatically.
