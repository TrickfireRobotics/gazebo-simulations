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
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        # bash and ros2 launch already received SIGINT from the terminal (same
        # process group). Don't send an additional SIGTERM — that would kill bash
        # immediately and orphan ros2 launch, causing its child-process cleanup
        # messages to appear after the shell prompt. Instead, re-enter wait() so
        # Python blocks until ros2 launch finishes shutting down all its nodes.
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(flush=True)  # blank line so the shell prompt starts cleanly
