"""Paths to various files and directories used by the CLI"""

from pathlib import Path


def _find_repo_root() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(
        "Could not locate repo root (no .git directory found). "
        "Run 'sim' from within the repository."
    )


REPO_DIR = _find_repo_root()
WORKSPACE_DIR = REPO_DIR / "robot-sim"
DOCKER_DIR = REPO_DIR / "docker"

# Native sim: miniconda and conda env are stored inside the repo at .conda/
# (never committed — see .gitignore).
CONDA_DIR = REPO_DIR / ".conda"
CONDA_BIN = CONDA_DIR / "bin" / "conda"
CONDA_ENV_NAME = "sim"
CONDA_ENV_YML = REPO_DIR / "environment.yml"
