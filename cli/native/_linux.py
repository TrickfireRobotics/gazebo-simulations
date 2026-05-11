"""Linux native sim launcher"""

import subprocess
from pathlib import Path
from ..paths import WORKSPACE_DIR, LINUX_DIR, LINUX_BIN, LINUX_ENV_PREFIX, LINUX_CONTROL_WS, MACOS_VERSIONS_FILE
from ..output import die, run_step, info, warn
from . import command as native_command
from ._common import get_mamba_exe, install_micromamba, ROS_BASE_PKGS

_SHELL_DIR = Path(__file__).parent / "shell"
_VERSIONS: dict[str, str] = {}


def _load_versions() -> None:
    if not MACOS_VERSIONS_FILE.exists():
        die(f"Versions file not found: {MACOS_VERSIONS_FILE}")
    for line in MACOS_VERSIONS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            _VERSIONS[key.strip()] = value.strip().strip('"').strip("'")


_load_versions()


LINUX_EXTRA_PKGS = [
    "ros-humble-ros-gz-bridge",
    "colcon-common-extensions",
    "colcon-ros",
    "libcap",
    "gz-harmonic",
]


def _step_prereqs() -> None:
    if subprocess.run(["which", "git"], capture_output=True, check=False).returncode != 0:
        die("Git missing! Please install Git and try again")
    if not (LINUX_BIN / "micromamba").exists():
        install_micromamba(LINUX_BIN)


def _step_conda_env(mamba_exe: str) -> None:
    python_exe = LINUX_ENV_PREFIX / "bin" / "python"
    if python_exe.exists():
        result = subprocess.run(
            [str(python_exe), "-c",
             "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip() != "3.12":
            warn(f"Recreating ros_env because it is Python {result.stdout.strip()}, expected 3.12")
            import shutil
            shutil.rmtree(LINUX_ENV_PREFIX)

    if LINUX_ENV_PREFIX.exists():
        _ensure_linux_pkgs(mamba_exe)
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


def _ensure_linux_pkgs(mamba_exe: str) -> None:
    # gz-harmonic was added after some envs were already created; install if missing.
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


def _step_control(mamba_exe: str) -> None:
    src = LINUX_CONTROL_WS / "src" / "gz_ros2_control"
    src.parent.mkdir(parents=True, exist_ok=True)

    gz_repo = _VERSIONS.get("GZ_ROS2_CONTROL_REPO")
    gz_branch = _VERSIONS.get("GZ_ROS2_CONTROL_BRANCH")
    gz_sha = _VERSIONS.get("GZ_ROS2_CONTROL_SHA")
    if not gz_repo or not gz_branch or not gz_sha:
        die("Missing GZ_ROS2_CONTROL configuration in versions file")
    assert isinstance(gz_repo, str) and isinstance(gz_branch, str) and isinstance(gz_sha, str)

    if not src.exists():
        subprocess.run(
            ["git", "clone", "--branch", gz_branch, gz_repo, str(src)], check=True
        )
    else:
        subprocess.run(["git", "-C", str(src), "fetch", "--quiet", "origin"], check=False)
    subprocess.run(["git", "-C", str(src), "checkout", "--quiet", gz_sha], check=True)

    marker = LINUX_CONTROL_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == gz_sha
        and (LINUX_CONTROL_WS / "install" / "setup.bash").exists()
    ):
        return

    subprocess.run(
        [
            "bash",
            str(_SHELL_DIR / "linux_control.sh"),
            mamba_exe,
            str(LINUX_ENV_PREFIX),
            str(LINUX_CONTROL_WS),
        ],
        check=True,
    )
    marker.write_text(gz_sha)


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
            str(LINUX_CONTROL_WS),
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

    gz_sha = _VERSIONS.get("GZ_ROS2_CONTROL_SHA", "unknown")[:9]
    run_step(f"gz_ros2_control ({gz_sha}…)", lambda: _step_control(mamba_exe))

    if not no_build:
        run_step("Build workspace", lambda: _step_workspace(mamba_exe, robot))

    if build_only:
        print()
        print("Build complete")
        print()
        return

    _launch_sim(mamba_exe, robot)
