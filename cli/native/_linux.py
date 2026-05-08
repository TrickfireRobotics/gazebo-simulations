"""Linux native sim launcher"""

import subprocess
from pathlib import Path
from ..paths import WORKSPACE_DIR, LINUX_DIR, LINUX_BIN, LINUX_ENV_PREFIX
from ..output import die, run_step, info
from . import command as native_command
from ._common import get_mamba_exe, install_micromamba, ROS_BASE_PKGS

_SHELL_DIR = Path(__file__).parent / "shell"

LINUX_EXTRA_PKGS = [
    "ros-humble-ros-gz",
    "ros-humble-gz-ros2-control",
    "colcon-common-extensions",
    "colcon-ros",
]


def _step_prereqs() -> None:
    if subprocess.run(["which", "git"], capture_output=True, check=False).returncode != 0:
        die("Git missing! Please install Git and try again")
    if not (LINUX_BIN / "micromamba").exists():
        install_micromamba(LINUX_BIN)


def _step_conda_env(mamba_exe: str) -> None:
    if LINUX_ENV_PREFIX.exists():
        return
    LINUX_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            mamba_exe,
            "create",
            "-y",
            "-p",
            str(LINUX_ENV_PREFIX),
            "-c",
            "robostack-humble",
            "-c",
            "conda-forge",
            "python=3.10",
            *ROS_BASE_PKGS,
            *LINUX_EXTRA_PKGS,
        ],
        check=True,
    )


def _step_cmake_clean() -> None:
    native_command.cmake_clean()


def _step_workspace(mamba_exe: str, robot: str) -> None:
    if not WORKSPACE_DIR.exists():
        die(f"Workspace not found: {WORKSPACE_DIR}")
    subprocess.run(
        [
            "bash",
            str(_SHELL_DIR / "linux_workspace.sh"),
            mamba_exe,
            str(LINUX_ENV_PREFIX),
            str(WORKSPACE_DIR),
        ],
        check=True,
    )


def _launch_sim(mamba_exe: str, robot: str) -> None:
    launch_path = WORKSPACE_DIR / f"{robot}_bringup" / "launch" / f"{robot}.launch.py"
    if not launch_path.exists():
        die(f"Launch file not found: {launch_path}")

    info(f"Launching simulation for robot {robot}")

    proc = subprocess.Popen(
        [
            "bash",
            str(_SHELL_DIR / "linux_launch.sh"),
            mamba_exe,
            str(LINUX_ENV_PREFIX),
            str(WORKSPACE_DIR),
            robot,
        ]
    )
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise


def build_and_launch(robot: str, build_only: bool = False, no_build: bool = False) -> None:
    mamba_exe = get_mamba_exe(LINUX_BIN)

    print()
    print("Building Linux environment...")
    print()

    run_step("Prerequisites", _step_prereqs)
    run_step("Conda environment", lambda: _step_conda_env(mamba_exe))
    run_step("Clean CMake artifacts", _step_cmake_clean)

    if not no_build:
        run_step("Build workspace", lambda: _step_workspace(mamba_exe, robot))

    if build_only:
        print()
        print("Build complete")
        print()
        return

    _launch_sim(mamba_exe, robot)
