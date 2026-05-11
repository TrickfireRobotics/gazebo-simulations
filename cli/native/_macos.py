"""macOS native sim launcher."""

import re
import shutil
import subprocess
from pathlib import Path

from ..output import die, info, run_step, warn
from ..paths import (
    NATIVE_BUILD_DIR,
    NATIVE_BIN,
    NATIVE_CONTROL_WS,
    NATIVE_ENV_PREFIX,
    NATIVE_ENVS,
    MACOS_ENV_LOCK,
    MACOS_ROS_BASE,
    MACOS_ROS_GZ_WS,
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


def _step_prereqs() -> None:
    if subprocess.run(["which", "git"], capture_output=True, check=False).returncode != 0:
        die("git is not installed")
    if subprocess.run(["xcode-select", "-p"], capture_output=True, check=False).returncode != 0:
        die("Xcode Command Line Tools missing — run: xcode-select --install")
    if not (NATIVE_BIN / "micromamba").exists():
        install_micromamba(NATIVE_BIN)


def _step_conda_env(mamba_exe: str) -> None:
    python_exe = NATIVE_ENV_PREFIX / "bin" / "python"
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
            shutil.rmtree(NATIVE_ENV_PREFIX)

    if NATIVE_ENV_PREFIX.exists():
        return

    NATIVE_ENVS.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            mamba_exe,
            "create",
            "-y",
            "-p",
            str(NATIVE_ENV_PREFIX),
            "-f",
            str(MACOS_ENV_LOCK),
            "python=3.12",
        ],
        check=True,
    )


def _step_patches() -> None:
    # Patch rosidl_generator_rs to not error on undefined symbols on macOS.
    rust_gen = (
        NATIVE_ENV_PREFIX
        / "share/rosidl_generator_rs/cmake/rosidl_generator_rs_generate_interfaces.cmake"
    )
    if rust_gen.exists():
        src = rust_gen.read_text()
        if "if(NOT APPLE)" not in src:
            patched = re.sub(
                r'(set\(CMAKE_SHARED_LINKER_FLAGS\s+"\$\{CMAKE_SHARED_LINKER_FLAGS\}\s+-Wl,-undefined,error"\))',
                "if(NOT APPLE)\n  \\1\nendif()",
                src,
                count=1,
            )
            if patched != src:
                rust_gen.write_text(patched)

    # Fix imported-target name mismatches between gz package cmake configs and the
    # config-mode packages installed in the conda env:
    #   gz-msgs10     targets use tinyxml2::tinyxml2, but FindTINYXML2.cmake creates TINYXML2::TINYXML2
    #   gz-transport13 targets use cppzmq, but FindCPPZMQ.cmake creates CPPZMQ::CPPZMQ
    _PATCH_MAP = [
        ("TINYXML2::TINYXML2", "tinyxml2::tinyxml2"),
        ("find_package(TINYXML2", "find_package(tinyxml2 CONFIG"),
        ("CPPZMQ::CPPZMQ", "cppzmq"),
        ("find_package(CPPZMQ", "find_package(cppzmq CONFIG"),
    ]
    for cmake_dir in (NATIVE_ENV_PREFIX / "lib" / "cmake", NATIVE_ENV_PREFIX / "share" / "cmake"):
        if not cmake_dir.is_dir():
            continue
        for fpath in cmake_dir.rglob("*.cmake"):
            try:
                src = fpath.read_text()
                dst = src
                for old, new in _PATCH_MAP:
                    dst = dst.replace(old, new)
                if dst != src:
                    fpath.write_text(dst)
            except OSError:
                pass


def _step_ros_base(mamba_exe: str) -> None:
    cmd = "install" if (MACOS_ROS_BASE / "setup.bash").exists() else "create"
    if cmd == "create":
        NATIVE_BUILD_DIR.mkdir(parents=True, exist_ok=True)
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


def _step_ros_gz(mamba_exe: str, versions: dict[str, str]) -> None:
    repo = versions.get("ROS_GZ_REPO")
    branch = versions.get("ROS_GZ_BRANCH")
    sha = versions.get("ROS_GZ_SHA")
    if not repo or not branch or not sha:
        die("Missing ROS_GZ_REPO, ROS_GZ_BRANCH, or ROS_GZ_SHA in versions file")

    src = MACOS_ROS_GZ_WS / "src" / "ros_gz"
    src.parent.mkdir(parents=True, exist_ok=True)
    sync_repo(repo, branch, sha, src)

    marker = MACOS_ROS_GZ_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == sha
        and (MACOS_ROS_GZ_WS / "install" / "setup.bash").exists()
    ):
        return

    run_script(
        _SHELL_DIR / "macos_ros_gz.sh",
        mamba_exe,
        str(NATIVE_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
    )
    marker.write_text(sha)


def _step_control(mamba_exe: str, versions: dict[str, str]) -> None:
    repo = versions.get("GZ_ROS2_CONTROL_REPO")
    branch = versions.get("GZ_ROS2_CONTROL_BRANCH")
    sha = versions.get("GZ_ROS2_CONTROL_SHA")
    if not repo or not branch or not sha:
        die(
            "Missing GZ_ROS2_CONTROL_REPO, GZ_ROS2_CONTROL_BRANCH, or GZ_ROS2_CONTROL_SHA in versions file"
        )

    src = NATIVE_CONTROL_WS / "src" / "gz_ros2_control"
    src.parent.mkdir(parents=True, exist_ok=True)
    sync_repo(repo, branch, sha, src)

    marker = NATIVE_CONTROL_WS / ".built_sha"
    if (
        marker.exists()
        and marker.read_text().strip() == sha
        and (NATIVE_CONTROL_WS / "install" / "setup.bash").exists()
    ):
        return

    run_script(
        _SHELL_DIR / "macos_control.sh",
        mamba_exe,
        str(NATIVE_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
        str(NATIVE_CONTROL_WS),
    )
    marker.write_text(sha)


def _step_workspace(mamba_exe: str) -> None:
    if not WORKSPACE_DIR.exists():
        die(f"Workspace not found: {WORKSPACE_DIR}")
    native_command.cmake_clean("macos")
    run_script(
        _SHELL_DIR / "macos_workspace.sh",
        mamba_exe,
        str(NATIVE_ENV_PREFIX),
        str(MACOS_ROS_BASE),
        str(MACOS_ROS_GZ_WS),
        str(NATIVE_CONTROL_WS),
        str(WORKSPACE_DIR),
    )


def _launch_sim(mamba_exe: str, robot: str) -> None:
    launch_path = WORKSPACE_DIR / f"{robot}_bringup" / "launch" / f"{robot}.launch.py"
    if not launch_path.exists():
        die(f"Launch file not found: {launch_path}")
    info(f"Launching simulation for robot: {robot}")
    launch_process(
        [
            "bash",
            str(_SHELL_DIR / "macos_launch.sh"),
            mamba_exe,
            str(NATIVE_ENV_PREFIX),
            str(MACOS_ROS_BASE),
            str(MACOS_ROS_GZ_WS),
            str(NATIVE_CONTROL_WS),
            str(WORKSPACE_DIR),
            robot,
        ]
    )


def build_and_launch(robot: str, build_only: bool = False, no_build: bool = False) -> None:
    """Build the native executable for the specified robot and launch it"""
    versions = load_versions(MACOS_VERSIONS_FILE)
    mamba_exe = get_mamba_exe(NATIVE_BIN)

    run_step("Prerequisites", _step_prereqs)
    run_step("Conda environment", lambda: _step_conda_env(mamba_exe))
    run_step("macOS patches", _step_patches)
    run_step("ROS base packages", lambda: _step_ros_base(mamba_exe))

    ros_gz_sha = versions.get("ROS_GZ_SHA", "?")[:9]
    run_step(f"ros_gz ({ros_gz_sha}…)", lambda: _step_ros_gz(mamba_exe, versions))

    gz_sha = versions.get("GZ_ROS2_CONTROL_SHA", "?")[:9]
    run_step(f"gz_ros2_control ({gz_sha}…)", lambda: _step_control(mamba_exe, versions))

    if not no_build:
        run_step("robot-sim workspace", lambda: _step_workspace(mamba_exe))

    if build_only:
        return

    _launch_sim(mamba_exe, robot)
