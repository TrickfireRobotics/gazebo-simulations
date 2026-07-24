"""sim create/update - robot package generation from OnShape."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from ...output import info
from ...paths import REPO_DIR, GAZEBO_WORKSPACE_DIR

PACKAGE_DIR = Path(__file__).parent
TEMPLATES = PACKAGE_DIR / "templates"
REPO_ROOT = REPO_DIR
ROBOTS_JSON = REPO_DIR / "robots.json"


def create(
    robot: str,
    onshape_url: str,
    *,
    output_dir: str | None = None,
    no_reduce: bool = False,
    attach_to_world: bool | None = None,
) -> None:
    from .commands import cmd_create

    info(f"Creating robot packages for '{robot}' from OnShape...")

    if not output_dir:
        output_dir = str(GAZEBO_WORKSPACE_DIR)

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
    from .commands import cmd_update

    info(f"Updating robot packages for '{robot}'...")
    cmd_update(
        Namespace(
            robot_name=robot,
            output_dir=output_dir or str(GAZEBO_WORKSPACE_DIR),
            no_reduce=no_reduce,
        )
    )
