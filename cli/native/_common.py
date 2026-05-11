import pathlib
import subprocess
import tempfile
from pathlib import Path

from ..output import die, info

ROS_BASE_PKGS = [
    "ros-humble-ros-base",
    "ros-humble-actuator-msgs",
    "ros-humble-gps-msgs",
    "ros-humble-vision-msgs",
    "ros-humble-image-transport",
    "ros-humble-ros2-control",
    "ros-humble-ros2-controllers",
    "ros-humble-joint-state-broadcaster",
    "ros-humble-joint-trajectory-controller",
    "ros-humble-control-msgs",
    "ros-humble-control-toolbox",
    "ros-humble-xacro",
    "ros-humble-rviz2",
]


def load_versions(path: Path) -> dict[str, str]:
    """Parse a shell-style KEY=value env file, ignoring blanks and comments."""
    if not path.exists():
        die(f"Versions file not found: {path}")
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def install_micromamba(bin_dir: Path) -> None:
    import platform as _plat
    import sys

    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "micromamba"

    machine = _plat.machine()
    if sys.platform == "darwin":
        plat = "osx-arm64" if machine in ("arm64", "aarch64") else "osx-64"
    elif machine in ("aarch64", "arm64"):
        plat = "linux-aarch64"
    elif machine == "ppc64le":
        plat = "linux-ppc64le"
    else:
        plat = "linux-64"

    url = f"https://micromamba.snakepit.net/api/micromamba/{plat}/latest"
    tmp = target.with_suffix(".tar.bz2")

    info(f"Downloading micromamba from {url}")
    subprocess.run(["curl", "-fsSL", url, "-o", str(tmp)], check=True)

    if tmp.exists():
        with open(tmp, "rb") as f:
            header = f.read(3)
        if header == b"BZh":
            with tempfile.TemporaryDirectory() as tmpd:
                subprocess.run(["tar", "-xjf", str(tmp), "-C", tmpd], check=True)
                found = list(pathlib.Path(tmpd).rglob("micromamba"))
                if not found:
                    die("Micromamba binary not found in archive")
                found[0].chmod(0o755)
                found[0].rename(target)
        else:
            target.write_bytes(tmp.read_bytes())
            target.chmod(0o755)
        tmp.unlink(missing_ok=True)

    result = subprocess.run([str(target), "--version"], capture_output=True, check=False)
    if result.returncode != 0:
        target.unlink(missing_ok=True)
        die("Downloaded micromamba is not runnable on this host")


def get_mamba_exe(bin_dir: Path) -> str:
    mamba = bin_dir / "micromamba"
    if not mamba.exists():
        install_micromamba(bin_dir)
    return str(mamba)


def run_script(script: Path, *args: str) -> None:
    """Run a shell script with bash."""
    subprocess.run(["bash", str(script), *args], check=True)


def sync_repo(repo: str, branch: str, sha: str, dest: Path) -> None:
    """Clone or fetch a git repo and check out the given commit."""
    if not dest.exists():
        subprocess.run(["git", "clone", "--branch", branch, repo, str(dest)], check=True)
    else:
        subprocess.run(["git", "-C", str(dest), "fetch", "--quiet", "origin"], check=False)
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", sha], check=True)


def launch_process(cmd: list[str]) -> None:
    """Run a process and block until it exits, cleanly handling Ctrl+C."""
    import os
    import signal

    # Isolate the child in its own process group so Ctrl+C (SIGINT to the
    # terminal's foreground group) does not reach it automatically. Python
    # catches the KeyboardInterrupt and then drives the shutdown explicitly,
    # which lets us wait for ros2 launch to finish killing all its nodes
    # before we return — ensuring cleanup messages appear before the prompt.
    # The launch scripts use `exec ros2 launch`, so proc.pid IS ros2 launch.
    proc = subprocess.Popen(cmd, preexec_fn=os.setpgrp)
    try:
        proc.wait()
    except KeyboardInterrupt:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
