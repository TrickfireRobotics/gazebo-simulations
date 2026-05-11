"""Paths to various files and directories used by the CLI"""

from pathlib import Path


def _find_repo_root() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "robot-sim").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    pkg_root = Path(__file__).parent.parent
    if (pkg_root / "robot-sim").is_dir():
        return pkg_root
    raise RuntimeError(
        "Could not locate gazebo-simulations repo root (no robot-sim/ directory found). "
        "Run 'sim' from the repository root directory."
    )


REPO_DIR = _find_repo_root()
WORKSPACE_DIR = REPO_DIR / "robot-sim"
DOCKER_DIR = REPO_DIR / "docker"

NATIVE_BUILD_DIR = REPO_DIR / ".native"
NATIVE_BIN = NATIVE_BUILD_DIR / "bin"
NATIVE_ENVS = NATIVE_BUILD_DIR / "envs"
NATIVE_ENV_PREFIX = NATIVE_ENVS / "ros_env"
NATIVE_CONTROL_WS = NATIVE_BUILD_DIR / "gz_ros2_control_ws"

MACOS_SOURCE_FILES = WORKSPACE_DIR / "sim_common" / "macos"
MACOS_MAMBA_ROOT = NATIVE_BUILD_DIR / "mamba"
MACOS_ROS_BASE = NATIVE_BUILD_DIR / "ros_base"
MACOS_ROS_GZ_WS = NATIVE_BUILD_DIR / "ros_gz_ws"
MACOS_CONTROL_WS = NATIVE_CONTROL_WS
MACOS_ENV_LOCK = MACOS_SOURCE_FILES / "env.lock.yml"
MACOS_VERSIONS_FILE = MACOS_SOURCE_FILES / "versions.env"
