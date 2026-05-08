import pathlib
import subprocess
import tempfile
from pathlib import Path
from ..output import die, info

# ROS Humble packages installed via conda/robostack on both macOS and Linux.
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
