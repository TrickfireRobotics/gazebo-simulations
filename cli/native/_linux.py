"""Linux native sim launcher."""

import shutil
import subprocess
from pathlib import Path

from ..output import die, info, run_step, warn
from ..paths import (
    LINUX_BIN,
    LINUX_CONTROL_WS,
    LINUX_DIR,
    LINUX_ENV_PREFIX,
    MACOS_VERSIONS_FILE,
    WORKSPACE_DIR,
)
from . import command as native_command
from ._common import (
    ROS_BASE_PKGS,
    get_mamba_exe,
    install_micromamba,
    launch_process,
    load_versions,
    run_script,
    sync_repo,
)

_SHELL_DIR = Path(__file__).parent / "shell"

LINUX_EXTRA_PKGS = [
    "ros-humble-ros-gz-bridge",
    "colcon-common-extensions",
    "colcon-ros",
    "libcap",
    "gz-harmonic",
]


def _step_prereqs() -> None:
    if subprocess.run(["which", "git"], capture_output=True, check=False).returncode != 0:
        die("git is not installed")
    if not (LINUX_BIN / "micromamba").exists():
        install_micromamba(LINUX_BIN)


def _step_conda_env(mamba_exe: str) -> None:
    python_exe = LINUX_ENV_PREFIX / "bin" / "python"
    if python_exe.exists():
        result = subprocess.run(
            [
                str(python_exe),
                "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip() != "3.12":
            warn(f"Recreating ros_env (Python {result.stdout.strip()}, expected 3.12)")
            shutil.rmtree(LINUX_ENV_PREFIX)

    if LINUX_ENV_PREFIX.exists():
        _ensure_gz_harmonic(mamba_exe)
        return

    LINUX_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            mamba_exe,
            "create",
            "-y",
            "--no-rc",
            "--override-channels",
            "-p",
            str(LINUX_ENV_PREFIX),
            "-c",
            "robostack-humble",
            "-c",
            "conda-forge",
            "python=3.12",
            *ROS_BASE_PKGS,
            *LINUX_EXTRA_PKGS,
        ],
        check=True,
    )


def _ensure_gz_harmonic(mamba_exe: str) -> None:
    if (LINUX_ENV_PREFIX / "include" / "gz" / "sim8").exists():
        return
    info("Installing gz-harmonic into existing ros_env")
    subprocess.run(
        [
            mamba_exe,
            "install",
            "-y",
            "-p",
            str(LINUX_ENV_PREFIX),
            "-c",
            "robostack-humble",
            "-c",
            "conda-forge",
            "gz-harmonic",
        ],
        check=True,
    )


def _step_control(mamba_exe: str, versions: dict[str, str]) -> None:
    repo = versions.get("GZ_ROS2_CONTROL_REPO")
    branch = versions.get("GZ_ROS2_CONTROL_BRANCH")
    sha = versions.get("GZ_ROS2_CONTROL_SHA")
    if not repo or not branch or not sha:
        die(
            "Missing GZ_ROS2_CONTROL_REPO, GZ_ROS2_CONTROL_BRANCH, or GZ_ROS2_CONTROL_SHA in versions file"
        )

    src = LINUX_CONTROL_WS / "src" / "gz_ros2_control"
    src.parent.mkdir(parents=True, exist_ok=True)
    sync_repo(repo, branch, sha, src)

    marker = LINUX_CONTROL_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == sha
        and (LINUX_CONTROL_WS / "install" / "setup.bash").exists()
    ):
        return

    run_script(
        _SHELL_DIR / "linux_control.sh", mamba_exe, str(LINUX_ENV_PREFIX), str(LINUX_CONTROL_WS)
    )
    marker.write_text(sha)


def _step_workspace(mamba_exe: str) -> None:
    if not WORKSPACE_DIR.exists():
        die(f"Workspace not found: {WORKSPACE_DIR}")
    run_script(
        _SHELL_DIR / "linux_workspace.sh", mamba_exe, str(LINUX_ENV_PREFIX), str(WORKSPACE_DIR)
    )


def _launch_sim(mamba_exe: str, robot: str) -> None:
    launch_path = WORKSPACE_DIR / f"{robot}_bringup" / "launch" / f"{robot}.launch.py"
    if not launch_path.exists():
        die(f"Launch file not found: {launch_path}")
    info(f"Launching simulation for robot: {robot}")
    launch_process(
        [
            "bash",
            str(_SHELL_DIR / "linux_launch.sh"),
            mamba_exe,
            str(LINUX_ENV_PREFIX),
            str(LINUX_CONTROL_WS),
            str(WORKSPACE_DIR),
            robot,
        ]
    )


def build_and_launch(robot: str, build_only: bool = False, no_build: bool = False) -> None:
    versions = load_versions(MACOS_VERSIONS_FILE)
    mamba_exe = get_mamba_exe(LINUX_BIN)

    run_step("Prerequisites", _step_prereqs)
    run_step("Conda environment", lambda: _step_conda_env(mamba_exe))
    run_step("Clean CMake artifacts", native_command.cmake_clean)

    gz_sha = versions.get("GZ_ROS2_CONTROL_SHA", "?")[:9]
    run_step(f"gz_ros2_control ({gz_sha}…)", lambda: _step_control(mamba_exe, versions))

    if not no_build:
        run_step("robot-sim workspace", lambda: _step_workspace(mamba_exe))

    if build_only:
        return

    _launch_sim(mamba_exe, robot)
