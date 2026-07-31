"""Run commands for chrono, very raw rn"""

import subprocess
import sys

from ..paths import CHRONO_TERRAIN_DIR


def run():
    result = subprocess.run(["make", "run"], cwd=CHRONO_TERRAIN_DIR, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def clean():
    result = subprocess.run(["make", "clean"], cwd=CHRONO_TERRAIN_DIR, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)
