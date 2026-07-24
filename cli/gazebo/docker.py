"""Docker simulation launcher for the `sim` CLI"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from ..output import die, info, warn
from ..paths import WORKSPACE_DIR

_ANSI_RE = re.compile(r"\x1B\[[0-9;]*[mK]")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _workspace_package(name: str) -> Path:
    return WORKSPACE_DIR / name


def _validate_robot_layout(robot_name: str) -> tuple[str, str, str]:
    bringup_pkg = f"{robot_name}_bringup"
    description_pkg = f"{robot_name}_description"
    launch_file_name = f"{robot_name}.launch.py"

    bringup_dir = _workspace_package(bringup_pkg)
    if not bringup_dir.is_dir():
        die(
            f"Package '{bringup_pkg}' not found in {WORKSPACE_DIR}\n"
            f"        Expected directory: {bringup_dir}"
        )

    description_dir = _workspace_package(description_pkg)
    if not description_dir.is_dir():
        die(
            f"Package '{description_pkg}' not found in {WORKSPACE_DIR}\n"
            f"        Expected directory: {description_dir}"
        )

    launch_file = bringup_dir / "launch" / launch_file_name
    if not launch_file.is_file():
        die(f"Launch file not found: {launch_file}")

    return bringup_pkg, description_pkg, launch_file_name


def _clean_workspace() -> None:
    for directory_name in ("build", "install", "log"):
        directory_path = WORKSPACE_DIR / directory_name
        if directory_path.exists():
            shutil.rmtree(directory_path)


def _drop_missing_prefix_paths(env: dict[str, str]) -> None:
    for key in ("AMENT_PREFIX_PATH", "CMAKE_PREFIX_PATH"):
        if key not in env:
            continue
        live = [p for p in env[key].split(":") if p and Path(p).exists()]
        if live:
            env[key] = ":".join(live)
        else:
            del env[key]


def _run_logged_command(
    command: list[str] | str,
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
    shell: bool = False,
) -> None:
    command_display = command if isinstance(command, str) else " ".join(command)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"$ {command_display}\n")
        log_file.flush()

        process = subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            executable="/bin/bash" if shell else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        try:
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                log_file.write(_strip_ansi(line))
                log_file.flush()
        except KeyboardInterrupt:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise

        return_code = process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)


def check_display() -> None:
    """Check that a display is available and can be connected to"""
    info("Checking for display...")
    display = os.environ.copy().get("DISPLAY")
    if not display:
        die("DISPLAY environment variable not set")

    display_running = subprocess.call(
        ["xdpyinfo", "-display", display], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if display_running != 0:
        die("Cannot connect to display " + display)


def build_and_launch(robot_name: str, *, build_only: bool = False, no_build: bool = False) -> None:
    """Build the workspace and launch a robot simulation."""
    if build_only and no_build:
        die("Use either --build-only or --no-build, not both")

    build = not no_build
    launch = not build_only
    env = os.environ.copy()
    bringup_pkg, description_pkg, launch_file_name = _validate_robot_layout(robot_name)

    if build:
        _clean_workspace()
        _drop_missing_prefix_paths(env)

    log_dir = WORKSPACE_DIR / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{robot_name}-gazebo-{datetime.now():%Y-%m-%d_%H-%M}.log"  # noqa: DTZ005

    print("--------------------------------------------------------------")
    print(f"Robot:     {robot_name}")
    print("Simulator: gazebo")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Log:       {log_path}")
    print("--------------------------------------------------------------")

    setup_bash = WORKSPACE_DIR / "install" / "setup.bash"

    if build:
        info("Building ROS2 workspace...")
        _run_logged_command(
            [
                "colcon",
                "build",
                "--packages-up-to",
                bringup_pkg,
                description_pkg,
                "sim_worlds",
                "sim_common",
                "--cmake-args",
                "-DBUILD_TESTING=OFF",
            ],
            cwd=WORKSPACE_DIR,
            env=env,
            log_path=log_path,
        )
        info("Build complete")

    if not setup_bash.is_file():
        die(
            "Missing install/setup.bash.\n"
            "        Run without --no-build once to generate install artifacts."
        )

    if not launch:
        info("Build-only requested; skipping launch")
        return

    info("Sourcing ROS2 environment and launching simulation...")
    launch_script = f"""
set -e
source install/setup.bash

SIM_WORLDS_SHARE=\"$PWD/install/sim_worlds/share/sim_worlds\"
if [ -d \"$SIM_WORLDS_SHARE/worlds\" ]; then
    export GZ_SIM_RESOURCE_PATH=\"${{GZ_SIM_RESOURCE_PATH:+$GZ_SIM_RESOURCE_PATH:}}$SIM_WORLDS_SHARE\"
    echo \"[INFO] GZ_SIM_RESOURCE_PATH set to: $GZ_SIM_RESOURCE_PATH\"
else
    echo \"[WARN] sim_worlds share directory not found - world files may not load\"
    echo \"       Expected: $SIM_WORLDS_SHARE/worlds\"
fi

exec ros2 launch \"{bringup_pkg}\" \"{launch_file_name}\" gui:=true
""".strip()

    try:
        _run_logged_command(
            launch_script,
            cwd=WORKSPACE_DIR,
            env=env,
            log_path=log_path,
            shell=True,
        )
    except subprocess.CalledProcessError as error:
        warn(f"Launch failed with exit code {error.returncode}")
        raise
