"""macOS native sim launcher"""

import os
import re
import subprocess
from pathlib import Path
from ..paths import (
    WORKSPACE_DIR,
    MACOS_DIR,
    MACOS_BIN,
    MACOS_ENVS,
    MACOS_ROS_BASE,
    MACOS_ROS_GZ_WS,
    MACOS_CONTROL_WS,
    MACOS_ENV_LOCK,
    MACOS_ENV_PREFIX,
    MACOS_VERSIONS_FILE,
)
from ..output import die, warn, run_step, info
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


def _set_versions_env() -> None:
    for key, value in _VERSIONS.items():
        os.environ[key] = value


def _run_script(name: str, *args: str) -> None:
    subprocess.run(["bash", str(_SHELL_DIR / name), *args], check=True)


def _step_prereqs() -> None:
    if subprocess.run(["which", "git"], capture_output=True, check=False).returncode != 0:
        die("Git missing! Please install Git and try again")
    if subprocess.run(["xcode-select", "-p"], capture_output=True, check=False).returncode != 0:
        die("Xcode Command Line Tools missing! Run: xcode-select --install")
    if not (MACOS_BIN / "micromamba").exists():
        install_micromamba(MACOS_BIN)


def _step_conda_env(mamba_exe: str) -> None:
    python_exe = MACOS_ENV_PREFIX / "bin" / "python"
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
            warn(f"Recreating ros_env because it is Python {result.stdout.strip()}, expected 3.12")
            import shutil

            shutil.rmtree(MACOS_ENV_PREFIX)

    if MACOS_ENV_PREFIX.exists():
        return

    MACOS_ENVS.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            mamba_exe,
            "create",
            "-y",
            "-p",
            str(MACOS_ENV_PREFIX),
            "-f",
            str(MACOS_ENV_LOCK),
            "python=3.12",
        ],
        check=True,
    )


def _step_patches() -> None:
    conda_prefix = str(MACOS_ENV_PREFIX)

    rust_gen = os.path.join(
        conda_prefix,
        "share/rosidl_generator_rs/cmake/rosidl_generator_rs_generate_interfaces.cmake",
    )
    if os.path.exists(rust_gen):
        src = open(rust_gen).read()
        if "if(NOT APPLE)" not in src:
            patched = re.sub(
                r'(set\(CMAKE_SHARED_LINKER_FLAGS\s+"\$\{CMAKE_SHARED_LINKER_FLAGS\}\s+-Wl,-undefined,error"\))',
                "if(NOT APPLE)\n  \\1\nendif()",
                src,
                count=1,
            )
            if patched != src:
                open(rust_gen, "w").write(patched)

    cmake_dir = os.path.join(conda_prefix, "lib/cmake")
    if os.path.isdir(cmake_dir):
        for root, dirs, files in os.walk(cmake_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    content = open(fpath).read()
                    if "TINYXML2::TINYXML2" in content:
                        content = content.replace("TINYXML2::TINYXML2", "tinyxml2::tinyxml2")
                        content = content.replace(
                            "find_package(TINYXML2", "find_package(tinyxml2 CONFIG"
                        )
                        open(fpath, "w").write(content)
                except Exception:
                    pass


def _step_ros_base(mamba_exe: str) -> None:
    cmd = "install" if (MACOS_ROS_BASE / "setup.bash").exists() else "create"
    if cmd == "create":
        MACOS_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            mamba_exe,
            cmd,
            "-y",
            "-p",
            str(MACOS_ROS_BASE),
            "-c",
            "robostack-humble",
            "-c",
            "conda-forge",
            *ROS_BASE_PKGS,
        ],
        check=True,
    )


def _step_ros_gz(mamba_exe: str) -> None:
    src = MACOS_ROS_GZ_WS / "src" / "ros_gz"
    src.parent.mkdir(parents=True, exist_ok=True)

    ros_gz_repo = _VERSIONS.get("ROS_GZ_REPO")
    ros_gz_branch = _VERSIONS.get("ROS_GZ_BRANCH")
    ros_gz_sha = _VERSIONS.get("ROS_GZ_SHA")
    if not ros_gz_repo or not ros_gz_branch or not ros_gz_sha:
        die("Missing ROS_GZ configuration in versions file")
    assert (
        isinstance(ros_gz_repo, str)
        and isinstance(ros_gz_branch, str)
        and isinstance(ros_gz_sha, str)
    )

    if not src.exists():
        subprocess.run(
            ["git", "clone", "--branch", ros_gz_branch, ros_gz_repo, str(src)], check=True
        )
    else:
        subprocess.run(["git", "-C", str(src), "fetch", "--quiet", "origin"], check=False)
    subprocess.run(["git", "-C", str(src), "checkout", "--quiet", ros_gz_sha], check=True)

    marker = MACOS_ROS_GZ_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == ros_gz_sha
        and (MACOS_ROS_GZ_WS / "install" / "setup.bash").exists()
    ):
        return

    _run_script(
        "macos_ros_gz.sh",
        mamba_exe,
        str(MACOS_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
    )
    marker.write_text(ros_gz_sha)


def _step_control(mamba_exe: str) -> None:
    src = MACOS_CONTROL_WS / "src" / "gz_ros2_control"
    src.parent.mkdir(parents=True, exist_ok=True)

    gz_repo = _VERSIONS.get("GZ_ROS2_CONTROL_REPO")
    gz_branch = _VERSIONS.get("GZ_ROS2_CONTROL_BRANCH")
    gz_sha = _VERSIONS.get("GZ_ROS2_CONTROL_SHA")
    if not gz_repo or not gz_branch or not gz_sha:
        die("Missing GZ_ROS2_CONTROL configuration in versions file")
    assert isinstance(gz_repo, str) and isinstance(gz_branch, str) and isinstance(gz_sha, str)

    if not src.exists():
        subprocess.run(["git", "clone", "--branch", gz_branch, gz_repo, str(src)], check=True)
    else:
        subprocess.run(["git", "-C", str(src), "fetch", "--quiet", "origin"], check=False)
    subprocess.run(["git", "-C", str(src), "checkout", "--quiet", gz_sha], check=True)

    marker = MACOS_CONTROL_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == gz_sha
        and (MACOS_CONTROL_WS / "install" / "setup.bash").exists()
    ):
        return

    _run_script(
        "macos_control.sh",
        mamba_exe,
        str(MACOS_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
        str(MACOS_CONTROL_WS),
    )
    marker.write_text(gz_sha)


def _step_workspace(
    mamba_exe: str, robot: str
) -> None:  # robot unused: macOS builds full workspace
    if not WORKSPACE_DIR.exists():
        die(f"Workspace not found: {WORKSPACE_DIR}")
    native_command.cmake_clean("macos")
    _run_script(
        "macos_workspace.sh",
        mamba_exe,
        str(MACOS_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
        str(MACOS_CONTROL_WS),
        str(WORKSPACE_DIR),
    )


def _launch_sim(mamba_exe: str, robot: str) -> None:
    launch_path = WORKSPACE_DIR / f"{robot}_bringup" / "launch" / f"{robot}.launch.py"
    if not launch_path.exists():
        die(f"Launch file not found: {launch_path}")

    info(f"Launching simulation for robot {robot}")

    proc = subprocess.Popen(
        [
            "bash",
            str(_SHELL_DIR / "macos_launch.sh"),
            mamba_exe,
            str(MACOS_ENV_PREFIX),
            str(MACOS_ROS_BASE),
            str(MACOS_ROS_GZ_WS),
            str(MACOS_CONTROL_WS),
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
    _set_versions_env()
    mamba_exe = get_mamba_exe(MACOS_BIN)

    print("Building macOS environment...")

    run_step("Prerequisites", _step_prereqs)
    run_step("Conda environment", lambda: _step_conda_env(mamba_exe))
    run_step("macOS patches", _step_patches)
    run_step("ROS base packages", lambda: _step_ros_base(mamba_exe))

    ros_gz_sha = _VERSIONS.get("ROS_GZ_SHA", "unknown")[:9]
    run_step(f"ros_gz ({ros_gz_sha}…)", lambda: _step_ros_gz(mamba_exe))

    gz_sha = _VERSIONS.get("GZ_ROS2_CONTROL_SHA", "unknown")[:9]
    run_step(f"gz_ros2_control ({gz_sha}…)", lambda: _step_control(mamba_exe))

    if not no_build:
        run_step("robot-sim workspace", lambda: _step_workspace(mamba_exe, robot))

    if build_only:
        print()
        print("Build complete")
        print()
        return

    _launch_sim(mamba_exe, robot)
