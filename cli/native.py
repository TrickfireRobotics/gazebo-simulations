"""Native simulation launcher for the `sim` CLI.

Downloads miniconda to .conda/ if needed, creates the 'sim' conda env from
environment.yml if needed, then builds the colcon workspace and launches the
Genesis simulation with a native viewer window.

Mirrors the approach proven in the genesis-sim PoC branch (genesis-sim/conda_setup.sh).
"""

from __future__ import annotations

import os
import platform
import shutil
import signal
import stat
import subprocess
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

from .output import die, info, warn
from .paths import CONDA_BIN, CONDA_DIR, CONDA_ENV_NAME, CONDA_ENV_YML, WORKSPACE_DIR

_TORCH_SENTINEL = CONDA_DIR / ".torch_upgraded"

_ANSI_RE = __import__("re").compile(r"\x1B\[[0-9;]*[mK]")

# Conda env vars that must be stripped so a user's existing conda install
# doesn't redirect our operations into their personal envs/pkgs dirs.
_CONDA_VARS = {
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "CONDA_SHLVL",
    "CONDA_ENVS_DIRS",
    "CONDA_ENVS_PATH",
    "CONDA_PKGS_DIRS",
    "CONDA_PROMPT_MODIFIER",
    "CONDA_PYTHON_EXE",
    "CONDA_EXE",
    "CONDA_ROOT",
}


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _clean_env() -> dict[str, str]:
    """Return os.environ with system conda vars stripped and project .condarc active."""
    env = {k: v for k, v in os.environ.items() if k not in _CONDA_VARS}
    env["CONDARC"] = str(CONDA_DIR / ".condarc")

    # Defensive: if the user has LD_PRELOAD set (common in some robotics/toolchain setups),
    # it can break conda + Python extension imports.
    env.pop("LD_PRELOAD", None)

    # Ensure we prefer the conda env's runtime libraries (libstdc++, etc.) over system /lib.
    env_dir = CONDA_DIR / "envs" / CONDA_ENV_NAME
    env_lib = str(env_dir / "lib")
    old_ld = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = f"{env_lib}:{old_ld}" if old_ld else env_lib

    return env


def _conda(args: list[str]) -> list[str]:
    return [str(CONDA_BIN)] + args


def _conda_run(args: list[str]) -> list[str]:
    """Wrap a command to run inside the sim conda env."""
    return _conda(["run", "--no-capture-output", "-n", CONDA_ENV_NAME] + args)


def _miniconda_url() -> str:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        arch = "arm64" if machine in ("arm64", "aarch64") else "x86_64"
        return f"https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-{arch}.sh"
    elif system == "Linux":
        arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
        return f"https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-{arch}.sh"
    else:
        die(f"Unsupported platform for sim native: {system} {machine}")


def _write_condarc() -> None:
    (CONDA_DIR / ".condarc").write_text(
        f"channels:\n"
        f"  - robostack-staging\n"
        f"  - conda-forge\n"
        f"  - nodefaults\n"
        f"channel_priority: flexible\n"
        f"envs_dirs:\n"
        f"  - {CONDA_DIR}/envs\n"
        f"pkgs_dirs:\n"
        f"  - {CONDA_DIR}/pkgs\n"
    )


def _ensure_conda() -> None:
    if not CONDA_BIN.exists():
        info("Downloading miniconda into .conda/ — one-time setup...")
        url = _miniconda_url()
        installer_dir = Path(tempfile.mkdtemp(prefix="miniconda_installer_"))
        installer = installer_dir / "installer.sh"
        try:
            info(f"Fetching {url}")
            urllib.request.urlretrieve(url, installer)
            installer.chmod(installer.stat().st_mode | stat.S_IEXEC)

            result = subprocess.run(
                ["bash", str(installer), "-b", "-p", str(CONDA_DIR)],
                check=False,
            )
            if result.returncode != 0:
                die("Miniconda installation failed. See output above.")
        finally:
            shutil.rmtree(installer_dir, ignore_errors=True)
        info("Miniconda ready")

    # Always rewrite — ensures channel config is up to date even on existing installs.
    _write_condarc()


def _ensure_conda_env() -> None:
    env_dir = CONDA_DIR / "envs" / CONDA_ENV_NAME
    if env_dir.exists():
        return

    if not CONDA_ENV_YML.exists():
        die(f"environment.yml not found at {CONDA_ENV_YML}")

    info(
        "Creating conda 'sim' environment — this takes 5–15 min the first time\n"
        "        (downloading ROS 2 Humble + Genesis + dependencies)..."
    )
    result = subprocess.run(
        _conda(
            ["env", "create", "-y", "-n", CONDA_ENV_NAME, "--file", str(CONDA_ENV_YML)]
        ),
        env=_clean_env(),
        check=False,
    )
    if result.returncode != 0:
        die("Failed to create conda environment. See output above.")

    # Install torch>=2.8.0 and genesis-world via pip.
    # Conda-forge ships an older torch; genesis requires 2.8+.
    info("Installing torch>=2.8.0 and genesis-world via pip...")
    result = subprocess.run(
        _conda_run(
            [
                "pip",
                "install",
                "--upgrade",
                "torch>=2.8.0",
                "torchvision",
                "torchaudio",
                "genesis-world",
            ]
        ),
        env=_clean_env(),
        check=False,
    )
    if result.returncode != 0:
        die("Failed to install genesis-world / torch. See output above.")

    info("Conda environment ready")


def _ensure_torch_version() -> None:
    if _TORCH_SENTINEL.exists():
        return

    info("Upgrading torch>=2.8.0 for Genesis (one-time)...")
    result = subprocess.run(
        _conda_run(
            [
                "pip",
                "install",
                "--upgrade",
                "torch>=2.8.0",
                "torchvision",
                "torchaudio",
                "genesis-world",
            ]
        ),
        env=_clean_env(),
        check=False,
    )
    if result.returncode != 0:
        die("Failed to upgrade torch. See output above.")

    _TORCH_SENTINEL.touch()
    info("Torch upgrade complete")


def _validate_robot(robot_name: str) -> None:
    robot_dir = WORKSPACE_DIR / robot_name
    if not robot_dir.is_dir():
        die(
            f"Robot package '{robot_name}' not found in {WORKSPACE_DIR}\n"
            f"        Expected directory: {robot_dir}\n"
            "        Run 'sim create <robot> <onshape_url>' first."
        )


def _run_logged(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
) -> None:
    cmd_display = " ".join(command)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"$ {cmd_display}\n")
        log_file.flush()

        proc = subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,  # new process group so we can kill the whole tree
        )

        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="")
                log_file.write(_strip_ansi(line))
                log_file.flush()
        except KeyboardInterrupt:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            except (ProcessLookupError, OSError):
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    proc.kill()
                proc.wait()
            raise

        rc = proc.wait()

    if rc != 0:
        raise subprocess.CalledProcessError(rc, command)


def build_and_launch(
    robot_name: str, *, build_only: bool = False, no_build: bool = False
) -> None:
    """Bootstrap conda + env if needed, build workspace, launch Genesis simulation."""
    if build_only and no_build:
        die("Use either --build-only or --no-build, not both")

    _validate_robot(robot_name)
    _ensure_conda()
    _ensure_conda_env()
    _ensure_torch_version()

    build = not no_build
    launch = not build_only
    env = _clean_env()

    if build:
        for d in ("build", "install", "log"):
            p = WORKSPACE_DIR / d
            if p.exists():
                shutil.rmtree(p)

    log_dir = WORKSPACE_DIR / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{robot_name}-genesis-{datetime.now():%Y-%m-%d_%H-%M}.log"

    print("--------------------------------------------------------------")
    print(f"Robot:     {robot_name}")
    print("Simulator: genesis (native)")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Conda env: {CONDA_DIR}/envs/{CONDA_ENV_NAME}")
    print(f"Log:       {log_path}")
    print("--------------------------------------------------------------")

    setup_bash = WORKSPACE_DIR / "install" / "setup.bash"

    if build:
        info("Building ROS 2 workspace inside conda env...")
        _run_logged(
            _conda_run(
                [
                    "colcon",
                    "build",
                    "--packages-up-to",
                    robot_name,
                    "sim_common",
                    "--cmake-args",
                    "-DBUILD_TESTING=OFF",
                ]
            ),
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

    info("Sourcing workspace and launching Genesis simulation...")
    launch_script = (
        f"set -e\n"
        f"source install/setup.bash\n"
        f"exec ros2 launch sim_common sim.launch.py robot:={robot_name} headless:=false"
    )

    try:
        _run_logged(
            _conda_run(["/bin/bash", "-c", launch_script]),
            cwd=WORKSPACE_DIR,
            env=env,
            log_path=log_path,
        )
    except subprocess.CalledProcessError as error:
        warn(f"Launch failed with exit code {error.returncode}")
        raise
