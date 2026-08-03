"""Gazebo simulation launcher for the `sim` CLI"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path

from ..output import die, info, warn
from ..paths import REPO_DIR, WORKSPACE_DIR

_ANSI_RE = re.compile(r"\x1B\[[0-9;]*[mK]")


def in_pixi() -> bool:
    return bool(os.environ.get("PIXI_PROJECT_ROOT") or os.environ.get("CONDA_PREFIX"))


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _validate_robot_layout(robot_name: str) -> tuple[str, str, str]:
    bringup_pkg = f"{robot_name}_bringup"
    description_pkg = f"{robot_name}_description"
    launch_file_name = f"{robot_name}.launch.py"

    bringup_dir = WORKSPACE_DIR / bringup_pkg
    if not bringup_dir.is_dir():
        die(
            f"Package '{bringup_pkg}' not found in {WORKSPACE_DIR}\n"
            f"        Expected directory: {bringup_dir}"
        )

    description_dir = WORKSPACE_DIR / description_pkg
    if not description_dir.is_dir():
        die(
            f"Package '{description_pkg}' not found in {WORKSPACE_DIR}\n"
            f"        Expected directory: {description_dir}"
        )

    launch_file = bringup_dir / "launch" / launch_file_name
    if not launch_file.is_file():
        die(f"Launch file not found: {launch_file}")

    return bringup_pkg, description_pkg, launch_file_name


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


def _x11_port_for(display: str) -> int:
    """The X11 protocol's TCP port for a display spec is 6000 + display number."""
    try:
        num_part = display.rsplit(":", 1)[-1].split(".")[0]
        return 6000 + int(num_part)
    except (ValueError, IndexError):
        return 6000


def _diagnose_display(display: str, xdpyinfo_stderr: str) -> str:
    """Build a specific, actionable explanation for why `display` couldn't be opened.

    Runs its own DNS/TCP checks (independent of xdpyinfo) so the error points at the
    layer that's actually broken, instead of a bare "cannot connect".
    """
    lines = [f"Cannot connect to display {display}", ""]
    is_local = display.startswith(":")

    if is_local:
        lines += [
            "This is a local display spec - the container expected a Wayland/X11 socket to",
            "already be forwarded in (native Linux host, or WSL2/WSLg).",
            "",
            "Checks to run inside the container:",
            "  1. grep X11 /tmp/start_x_server.log",
            "     Look for '[X11] Using host X11 display' or '[X11] Using Wayland socket'.",
            "     If you see Xvfb/vkms/dummy-driver/noVNC lines instead, passthrough failed",
            "     at container startup and it fell back to the internal VNC stack - connect",
            "     a VNC viewer to localhost:5900 (or http://localhost:6080/vnc.html), or fix",
            "     passthrough on the host and restart the container to retry it.",
            "  2. ls -la /tmp/.X11-unix/",
            "     Empty means the host's X11 socket wasn't bind-mounted in, or nothing is",
            "     listening on it on the host.",
        ]
        return "\n".join(lines)

    host = display.split(":", 1)[0]
    lines += [
        f"This is a remote display spec (host '{host}') - used by the macOS/Windows",
        "devcontainer configs to forward GUI windows to XQuartz/VcXsrv over TCP.",
        "",
    ]

    try:
        ip = socket.gethostbyname(host)
        lines.append(f"  [OK]   DNS: '{host}' resolves to {ip}")
    except OSError as e:
        lines += [
            f"  [FAIL] DNS: '{host}' did not resolve ({e})",
            "",
            "         Docker Desktop provides this name automatically to containers. If it's",
            "         missing, Docker Desktop may not be running, or this isn't actually",
            "         running inside the container (check your shell prompt).",
        ]
        return "\n".join(lines)

    port = _x11_port_for(display)
    try:
        with socket.create_connection((host, port), timeout=3):
            lines.append(f"  [OK]   TCP: port {port} on {host} is reachable")
    except OSError as e:
        lines += [
            f"  [FAIL] TCP: could not connect to {host}:{port} ({e})",
            "",
            "         macOS + XQuartz:",
            "           - Is XQuartz actually running? (`ps aux | grep -i xquartz` on the Mac)",
            "           - XQuartz > Settings > Security > 'Allow connections from network",
            "             clients' must be checked, then XQuartz fully restarted for it to",
            "             take effect.",
            "         Windows + VcXsrv/X410:",
            "           - Is the X server running? For VcXsrv, XLaunch must have 'Disable",
            "             access control' checked.",
            "           - Windows Defender Firewall may be silently blocking it - check for a",
            "             blocked-app prompt, or allow it manually for Private networks.",
        ]
        return "\n".join(lines)

    lines += [
        "  [FAIL] X11: connected over TCP, but the X server rejected the session:",
        f"         {xdpyinfo_stderr.strip() or '(no error output captured)'}",
        "",
        "         DNS and TCP are both fine, so this is an X11 access-control problem, not a",
        "         network problem:",
        "",
        "         macOS:",
        "           Run on the Mac (not in the container): `DISPLAY=:0 xhost + 127.0.0.1`",
        "           Do NOT use `xhost -display :0 + ...` - this is a documented xhost bug:",
        "           '-display' is parsed as 'remove a host named display', not a real flag.",
        "           xhost always connects using your shell's $DISPLAY env var instead, so set",
        "           it as a one-off prefix like above. This resets every time XQuartz",
        "           restarts, so you'll need to re-run it after any XQuartz restart.",
        "         Windows:",
        "           Relaunch VcXsrv/X410 with 'Disable access control' checked - there's no",
        "           separate allow-list step needed once that's set.",
    ]
    return "\n".join(lines)


def _display_reachable(display: str) -> bool:
    """Whether an X server is answering on `display`."""
    return (
        subprocess.run(
            ["xdpyinfo", "-display", display],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _check_display() -> None:
    info("Checking for display...")
    display = os.environ.get("DISPLAY")
    if not display:
        die(
            "DISPLAY environment variable not set\n\n"
            "        This is normally set by the devcontainer's compose config. If you're\n"
            "        seeing this, something stripped it from your shell - try a fresh\n"
            "        terminal/container restart, or run `env | grep DISPLAY` to confirm."
        )

    result = subprocess.run(
        ["xdpyinfo", "-display", display],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        die(_diagnose_display(display, result.stderr))


def _configure_virtualgl_rendering(env: dict[str, str]) -> list[str]:
    """Route GL rendering through VirtualGL when displaying on a remote X server.

    macOS (XQuartz) and Windows (VcXsrv/X410) can display X11 windows over TCP, but can't
    hand back a usable OpenGL context: their indirect GLX is deprecated and broken, so OGRE2
    - which both Gazebo and RViz use - fails at glXMakeCurrent and never creates a renderer.

    VirtualGL splits the two concerns. GL rendering runs against a container-local headless X
    server (Mesa llvmpipe, OpenGL 4.5) started by .devcontainer/x_server.sh, and only the
    finished frames go to the host's X server as ordinary X11 images - which it handles fine.

    Returns the command prefix to launch under, or an empty prefix if VirtualGL isn't needed
    or isn't usable (in which case the launch still proceeds, just without GL acceleration).
    """
    display = os.environ.get("DISPLAY", "")
    if display.startswith(":"):
        return []  # local passthrough (Linux/WSLg) - the app's GL already works directly

    if not shutil.which("vglrun"):
        warn(
            "VirtualGL (vglrun) is not installed, so Gazebo/RViz have no way to get a\n"
            "        working GL context on this host - expect a blank Gazebo window and\n"
            "        rviz2 dying with 'Unable to create the rendering window'.\n"
            "        \n"
            "        Rebuild the container to pick it up, or set FORCE_VNC=1 in docker/.env\n"
            "        and recreate the container to render over VNC instead."
        )
        return []

    vgl_display = os.environ.get("VGL_DISPLAY", ":88")
    if not _display_reachable(vgl_display):
        warn(
            f"VirtualGL's 3D X server on {vgl_display} isn't running, so Gazebo/RViz can't\n"
            "        get a working GL context - expect rendering to fail.\n"
            "        \n"
            "        Start it with: bash .devcontainer/x_server.sh\n"
            "        (it normally starts automatically when the container starts)"
        )
        return []

    # These force Mesa onto the host X server's indirect-GLX path - the very thing VirtualGL
    # exists to avoid. Left set, they also break the local GL context VirtualGL renders into,
    # so drop them for the launched processes.
    for stale in ("LIBGL_ALWAYS_INDIRECT", "MESA_LOADER_DRIVER_OVERRIDE"):
        env.pop(stale, None)

    env["VGL_DISPLAY"] = vgl_display
    # X11 Transport: hand rendered frames over as ordinary X11 images on the connection we
    # already have. No vglclient process on the host and no extra port needed.
    env.setdefault("VGL_COMPRESS", "proxy")

    info(f"Rendering through VirtualGL ({vgl_display} -> {display})")
    return ["vglrun"]


def _configure_rendering(env: dict[str, str]) -> list[str]:
    """Pick how Gazebo/OGRE2 should get its GL context, based on where it's being displayed."""
    if os.environ.get("FORCE_VNC"):
        info("FORCE_VNC: forcing software rendering (llvmpipe) - no direct GPU access")
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        return []

    return _configure_virtualgl_rendering(env)


def _setup_pixi_env() -> None:
    """Configure Gazebo plugin/resource paths and Qt platform for a pixi environment"""
    pixi_dir = REPO_DIR / ".pixi"
    if not pixi_dir.is_dir():
        die(f"No pixi environment at {pixi_dir}\nInstall dependencies first: pixi install")

    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if conda_prefix:
        plugin_lib = f"{conda_prefix}/lib"
        for var in ("GZ_SIM_SYSTEM_PLUGIN_PATH", "GZ_SIM_RESOURCE_PATH"):
            existing = os.environ.get(var, "")
            paths = [p for p in existing.split(":") if p]
            if plugin_lib not in paths:
                os.environ[var] = ":".join([plugin_lib] + paths)

        engine_plugins = f"{conda_prefix}/lib/gz-rendering-8/engine-plugins"
        existing = os.environ.get("GZ_RENDERING_PLUGIN_PATH", "")
        paths = [p for p in existing.split(":") if p]
        if engine_plugins not in paths:
            os.environ["GZ_RENDERING_PLUGIN_PATH"] = ":".join([engine_plugins] + paths)

        ogre2_media = f"{conda_prefix}/share/gz/gz-rendering8/ogre2/media"
        existing = os.environ.get("GZ_RENDERING_RESOURCE_PATH", "")
        paths = [p for p in existing.split(":") if p]
        if ogre2_media not in paths:
            os.environ["GZ_RENDERING_RESOURCE_PATH"] = ":".join([ogre2_media] + paths)

    if os.environ.get("QT_QPA_PLATFORM") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"


def build_and_launch(robot_name: str, *, build_only: bool = False, no_build: bool = False) -> None:
    """Build the ROS 2 workspace and launch a robot simulation.

    Auto-detects the environment: configures pixi paths when running natively,
    or checks the X display when running inside the Dev Container.
    """
    if build_only and no_build:
        die("Use either --build-only or --no-build, not both")

    if in_pixi():
        _setup_pixi_env()
    else:
        _check_display()

    build = not no_build
    launch = not build_only
    env = os.environ.copy()
    render_prefix = _configure_rendering(env)
    bringup_pkg, description_pkg, launch_file_name = _validate_robot_layout(robot_name)

    if build:
        for directory_name in ("build", "install", "log"):
            directory_path = WORKSPACE_DIR / directory_name
            if directory_path.exists():
                shutil.rmtree(directory_path)
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

exec {" ".join(render_prefix)} ros2 launch \"{bringup_pkg}\" \"{launch_file_name}\" gui:=true
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
