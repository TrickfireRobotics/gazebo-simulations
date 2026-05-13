"""sim create/update - robot package generation from OnShape."""

from __future__ import annotations

import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path

from ..output import info
from ..paths import REPO_DIR

PACKAGE_DIR = Path(__file__).parent
TEMPLATES = PACKAGE_DIR / "templates"
REPO_ROOT = REPO_DIR
ROBOTS_JSON = REPO_DIR / "robots.json"

_ONSHAPE_ENV = REPO_DIR / "cli" / "onshape.env"
_AGE_FILE = REPO_DIR / "cli" / "onshape.env.age"

_SSH_KEY_CANDIDATES = [
    Path.home() / ".ssh" / "id_ed25519",
    Path.home() / ".ssh" / "id_rsa",
    Path.home() / ".ssh" / "id_ecdsa",
    Path.home() / ".ssh" / "id_dsa",
]


def _try_age_decrypt() -> bool:
    if not _AGE_FILE.exists() or not shutil.which("age"):
        return False
    for ssh_key in _SSH_KEY_CANDIDATES:
        if not ssh_key.exists():
            continue
        result = subprocess.run(
            ["age", "--decrypt", "--identity", str(ssh_key), str(_AGE_FILE)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()
            return True
    return False


def _load_credentials() -> None:
    # cli/onshape.env is an explicit override — takes priority over everything
    if _ONSHAPE_ENV.exists():
        for line in _ONSHAPE_ENV.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip()
        return
    # Already set (CI injects these directly)
    if os.environ.get("ONSHAPE_API_KEY") and os.environ.get("ONSHAPE_API_SECRET"):
        return
    # Auto-decrypt from age file in memory
    _try_age_decrypt()


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
