"""sim create/update - robot package generation from OnShape."""

from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

from ..output import info
from ..paths import REPO_DIR

PACKAGE_DIR = Path(__file__).parent
TEMPLATES = PACKAGE_DIR / "templates"
REPO_ROOT = REPO_DIR
ROBOTS_JSON = REPO_DIR / "robots.json"

_ONSHAPE_ENV = REPO_DIR / "cli" / "onshape.env"


def _load_credentials() -> None:
    if _ONSHAPE_ENV.exists():
        for line in _ONSHAPE_ENV.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def create(
    robot: str,
    onshape_url: str,
    *,
    output_dir: str | None = None,
    no_reduce: bool = False,
    attach_to_world: bool | None = None,
) -> None:
    _load_credentials()
    from .commands import cmd_create

    info(f"Creating robot packages for '{robot}' from OnShape...")

    # Use output_dir if provided, otherwise look for robot-sim in current directory, else use workspace root
    if not output_dir:
        cwd = Path.cwd()
        if (cwd / "robot-sim").exists():
            output_dir = str(cwd / "robot-sim")
        else:
            output_dir = str(REPO_ROOT / "robot-sim")

    cmd_create(
        Namespace(
            robot_name=robot,
            onshape_url=onshape_url,
            output_dir=output_dir,
            no_reduce=no_reduce,
            attach_to_world=attach_to_world,
        )
    )


def update(
    robot: str,
    *,
    output_dir: str | None = None,
    no_reduce: bool = False,
) -> None:
    _load_credentials()
    from .commands import cmd_update

    info(f"Updating robot packages for '{robot}'...")
    cmd_update(
        Namespace(
            robot_name=robot,
            output_dir=output_dir or str(REPO_ROOT / "robot-sim"),
            no_reduce=no_reduce,
        )
    )
