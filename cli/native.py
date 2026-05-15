"""Native simulation launcher for the `sim` CLI"""

from __future__ import annotations

import os

from .docker import build_and_launch as _build_and_launch
from .output import die
from .paths import REPO_DIR


def _check_pixi_env() -> None:
    in_env = bool(os.environ.get("PIXI_PROJECT_ROOT") or os.environ.get("CONDA_PREFIX"))
    if not in_env:
        die(
            "Not inside a pixi environment.\n"
            "        Activate with: pixi shell\n"
            "        Then re-run:   sim native <robot>"
        )

    pixi_dir = REPO_DIR / ".pixi"
    if not pixi_dir.is_dir():
        die(
            f"No pixi environment at {pixi_dir}\n"
            "        Install dependencies first: pixi install"
        )


def _setup_plugin_paths() -> None:
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if not conda_prefix:
        return
    plugin_lib = f"{conda_prefix}/lib"
    for var in ("GZ_SIM_SYSTEM_PLUGIN_PATH", "GZ_SIM_RESOURCE_PATH"):
        existing = os.environ.get(var, "")
        paths = [p for p in existing.split(":") if p]
        if plugin_lib not in paths:
            os.environ[var] = ":".join([plugin_lib] + paths)


def build_and_launch_native(
    robot_name: str, *, build_only: bool = False, no_build: bool = False
) -> None:
    """Build the workspace and launch a robot simulation using the native pixi environment."""
    _check_pixi_env()
    _setup_plugin_paths()
    _build_and_launch(robot_name, build_only=build_only, no_build=no_build)
