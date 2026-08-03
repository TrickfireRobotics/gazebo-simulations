"""ArduPilot SITL + ardupilot_gazebo plugin setup for the drone simulation.

Builds both from source into `.native/` (gitignored), separate from the
Docker image build - run once via `sim gazebo setup-drone`.
"""

from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path

from ..output import die, info, run_step
from ..paths import ARDUPILOT_DIR, ARDUPILOT_GAZEBO_DIR

ARDUPILOT_REPO = "https://github.com/ArduPilot/ardupilot.git"
ARDUPILOT_REF = "Copter-4.3.7"

# Copter-4.3.7 pins modules/waf at a 2019-era commit that still uses the
# `imp` module, removed in Python 3.12 (Ubuntu 24.04's default python3).
# waf is only a host-side build tool - it isn't part of the firmware - so
# it's safe to move just this submodule forward to the commit later
# ArduPilot releases (e.g. Copter-4.6.2) use, which supports Python 3.12.
ARDUPILOT_WAF_COMMIT = "35eadbb64e2052099a853b571e507c33032b392c"

ARDUPILOT_GAZEBO_REPO = "https://github.com/ArduPilot/ardupilot_gazebo.git"

ARDUCOPTER_BIN = ARDUPILOT_DIR / "build" / "sitl" / "bin" / "arducopter"
ARDUPILOT_GAZEBO_BUILD_DIR = ARDUPILOT_GAZEBO_DIR / "build"
ARDUPILOT_GAZEBO_PLUGIN = ARDUPILOT_GAZEBO_BUILD_DIR / "libArduPilotPlugin.so"


def is_installed() -> bool:
    """Whether ArduCopter SITL and the ardupilot_gazebo plugin are already built"""
    return ARDUCOPTER_BIN.is_file() and ARDUPILOT_GAZEBO_PLUGIN.is_file()


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, check=False)  # noqa: S603
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)


def _clone_ardupilot() -> None:
    if ARDUPILOT_DIR.is_dir():
        info(f"ArduPilot already cloned at {ARDUPILOT_DIR}")
        return
    ARDUPILOT_DIR.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "git",
            "clone",
            "--recurse-submodules",
            "--branch",
            ARDUPILOT_REF,
            ARDUPILOT_REPO,
            str(ARDUPILOT_DIR),
        ],
        cwd=ARDUPILOT_DIR.parent,
    )


_BUILD_APT_PACKAGES = [
    "build-essential",
    "ccache",
    "g++",
    "gawk",
    "git",
    "make",
    "wget",
    "python3-dev",
    "python3-pip",
    "libtool-bin",
    "rsync",
]

# empy is pinned: newer empy (4.x) changed its API and breaks ArduPilot's
# waf build scripts, which still use the old empy 3.3.4 templating API.
_BUILD_PIP_PACKAGES = [
    "future",
    "lxml",
    "pymavlink",
    "pyserial",
    "ptyprocess",
    "pexpect",
    "setuptools<81",  # older ArduPilot build scripts need the legacy pkg_resources module
    "empy==3.3.4",
]


def _install_ardupilot_prereqs() -> None:
    """Install just what's needed to configure/build SITL and generate MAVLink headers.

    ArduPilot's own Tools/environment_install/install-prereqs-ubuntu.sh (as
    pinned at ARDUPILOT_REF) predates Ubuntu 24.04 "noble" support and also
    pulls in a large MAVProxy/wxPython/SFML stack only needed for its
    graphical GCS console - `sim gazebo drone` runs the `arducopter` binary
    directly (not sim_vehicle.py/MAVProxy), so none of that is needed here.
    """
    _run(["sudo", "apt-get", "update"], cwd=ARDUPILOT_DIR)
    _run(
        ["sudo", "apt-get", "install", "-y", "--no-install-recommends", *_BUILD_APT_PACKAGES],
        cwd=ARDUPILOT_DIR,
    )
    _run(
        ["pip3", "install", "--break-system-packages", *_BUILD_PIP_PACKAGES],
        cwd=ARDUPILOT_DIR,
    )

    env = os.environ.copy()
    user = env.get("USER") or getpass.getuser()
    _run(["sudo", "usermod", "-a", "-G", "dialout", user], cwd=ARDUPILOT_DIR)


def _pin_waf_for_python312() -> None:
    waf_dir = ARDUPILOT_DIR / "modules" / "waf"
    result = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "HEAD"], cwd=waf_dir, capture_output=True, text=True, check=False
    )
    if result.stdout.strip() == ARDUPILOT_WAF_COMMIT:
        info("modules/waf already pinned to the Python 3.12-compatible commit")
        return
    _run(["git", "fetch", "--depth", "1", "origin", ARDUPILOT_WAF_COMMIT], cwd=waf_dir)
    _run(["git", "checkout", ARDUPILOT_WAF_COMMIT], cwd=waf_dir)


# ARDUPILOT_REF predates GCC 13 (Ubuntu 24.04's default): some files rely on
# standard headers transitively including <cstdint>/<cstring>, which newer
# libstdc++ no longer does. Each entry adds a missing include right before
# an existing one, purely a header fix with no behavior change. Extend this
# list if `./waf copter` hits more "does not name a type" errors.
_GCC13_HEADER_FIXES: list[tuple[str, str, str]] = [
    (
        "libraries/AP_HAL_SITL/CANSocketIface.cpp",
        "#include <linux/can/raw.h>",
        "#include <cstdint>",
    ),
]


def _patch_gcc13_headers() -> None:
    for rel_path, anchor, missing_include in _GCC13_HEADER_FIXES:
        path = ARDUPILOT_DIR / rel_path
        text = path.read_text()
        if missing_include in text:
            continue
        path.write_text(text.replace(anchor, f"{anchor}\n{missing_include}", 1))


def _build_arducopter() -> None:
    if ARDUCOPTER_BIN.is_file():
        info(f"ArduCopter SITL already built at {ARDUCOPTER_BIN}")
        return
    _pin_waf_for_python312()
    _patch_gcc13_headers()
    _run(["./waf", "configure", "--board", "sitl"], cwd=ARDUPILOT_DIR)
    _run(["./waf", "copter"], cwd=ARDUPILOT_DIR)
    if not ARDUCOPTER_BIN.is_file():
        die(f"Build finished but {ARDUCOPTER_BIN} was not produced")


def _clone_ardupilot_gazebo() -> None:
    if ARDUPILOT_GAZEBO_DIR.is_dir():
        info(f"ardupilot_gazebo already cloned at {ARDUPILOT_GAZEBO_DIR}")
        return
    ARDUPILOT_GAZEBO_DIR.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["git", "clone", ARDUPILOT_GAZEBO_REPO, str(ARDUPILOT_GAZEBO_DIR)],
        cwd=ARDUPILOT_GAZEBO_DIR.parent,
    )


_GAZEBO_PLUGIN_APT_PACKAGES = [
    "libgstreamer1.0-dev",
    "libgstreamer-plugins-base1.0-dev",
]

# ardupilot_gazebo's CMakeLists.txt calls ament_package(), which needs catkin_pkg
# (to parse package.xml) on whatever python ROS2's ament_cmake_core invokes.
_GAZEBO_PLUGIN_PIP_PACKAGES = ["catkin_pkg"]


def _build_ardupilot_gazebo_plugin() -> None:
    if ARDUPILOT_GAZEBO_PLUGIN.is_file():
        info(f"ardupilot_gazebo plugin already built at {ARDUPILOT_GAZEBO_PLUGIN}")
        return
    _run(["sudo", "apt-get", "update"], cwd=ARDUPILOT_GAZEBO_DIR)
    _run(
        [
            "sudo",
            "apt-get",
            "install",
            "-y",
            "--no-install-recommends",
            *_GAZEBO_PLUGIN_APT_PACKAGES,
        ],
        cwd=ARDUPILOT_GAZEBO_DIR,
    )
    _run(
        ["pip3", "install", "--break-system-packages", *_GAZEBO_PLUGIN_PIP_PACKAGES],
        cwd=ARDUPILOT_GAZEBO_DIR,
    )
    env = os.environ.copy()
    env["GZ_VERSION"] = "harmonic"
    _run(
        ["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=RelWithDebInfo"],
        cwd=ARDUPILOT_GAZEBO_DIR,
        env=env,
    )
    _run(
        ["cmake", "--build", "build", "--parallel", str(os.cpu_count() or 1)],
        cwd=ARDUPILOT_GAZEBO_DIR,
        env=env,
    )
    if not ARDUPILOT_GAZEBO_PLUGIN.is_file():
        die(f"Build finished but {ARDUPILOT_GAZEBO_PLUGIN} was not produced")


def setup() -> None:
    """Clone and build ArduPilot SITL (ArduCopter) and the ardupilot_gazebo plugin"""
    if is_installed():
        info("ArduPilot SITL + ardupilot_gazebo plugin are already set up")
        info(f"  {ARDUCOPTER_BIN}")
        info(f"  {ARDUPILOT_GAZEBO_PLUGIN}")
        return

    try:
        run_step("Cloning ArduPilot", _clone_ardupilot)
        run_step("Installing ArduPilot build prerequisites", _install_ardupilot_prereqs)
        run_step("Building ArduCopter SITL (this takes a while)", _build_arducopter)
        run_step("Cloning ardupilot_gazebo", _clone_ardupilot_gazebo)
        run_step("Building ardupilot_gazebo plugin", _build_ardupilot_gazebo_plugin)
    except subprocess.CalledProcessError as error:
        die(f"Command failed with exit code {error.returncode}: {' '.join(error.cmd)}")

    info("ArduPilot SITL + ardupilot_gazebo plugin are ready")
    info("Run 'sim gazebo drone' to launch the drone simulation")
