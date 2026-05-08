from pathlib import Path


def _find_repo_root() -> Path:
    # Walk up from cwd looking for the repo (has both robot-sim/ and pyproject.toml)
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "robot-sim").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    # Fallback: __file__-based path (works for editable installs run from repo root)
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

# macOS-specific directories
MACOS_DIR = REPO_DIR / ".macos"
LINUX_DIR = REPO_DIR / ".linux"
LINUX_BIN = LINUX_DIR / "bin"
LINUX_ENVS = LINUX_DIR / "envs"
LINUX_ENV_PREFIX = LINUX_ENVS / "ros_env"


MACOS_SOURCE_FILES = WORKSPACE_DIR / "sim_common" / "macos"
MACOS_BIN = MACOS_DIR / "bin"
MACOS_ENVS = MACOS_DIR / "envs"
MACOS_MAMBA_ROOT = MACOS_DIR / "mamba"
MACOS_ROS_BASE = MACOS_DIR / "ros_base"
MACOS_ROS_GZ_WS = MACOS_DIR / "ros_gz_ws"
MACOS_CONTROL_WS = MACOS_DIR / "gz_ros2_control_ws"
MACOS_ENV_LOCK = MACOS_SOURCE_FILES / "env.lock.yml"
MACOS_ENV_PREFIX = MACOS_ENVS / "ros_env"
MACOS_VERSIONS_FILE = MACOS_SOURCE_FILES / "versions.env"
