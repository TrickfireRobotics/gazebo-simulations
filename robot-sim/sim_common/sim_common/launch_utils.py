"""Shared launch utilities for simulation packages."""

import os
import sys
from pathlib import Path

from ament_index_python.packages import get_package_share_directory


def log(msg):
    """Green info log for launch files."""
    print("\033[0;32m", "[INFO] [launch]: ", msg, "\x1b[0m", sep="")


def err(msg):
    """Red error log, exits with code 1."""
    print("\033[0;31m", "[ERROR] [launch]: ", msg, "\x1b[0m", sep="")
    sys.exit(1)


def get_asset(package, *parts):
    """
    Resolve a file path inside a ROS2 package share directory.
    Exits with an error if the resolved path does not exist.
    """
    pkg_dir = get_package_share_directory(package)
    path = os.path.join(pkg_dir, *parts)
    if not Path(path).exists():
        err(f"File {path} does not exist!")
    return path
