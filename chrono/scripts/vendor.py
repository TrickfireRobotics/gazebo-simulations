#!/usr/bin/env python3
"""
Copies Chrono/VSG/Eigen headers into chrono/vendor/ and rewrites
compile_commands.json so host clangd can find them.

Invoked automatically on container creation via postCreateCommand.
Can also be run manually inside the container via: make vendor
"""

import os
import shutil
import subprocess
from pathlib import Path

SIM = Path(__file__).resolve().parent.parent.parent
VENDOR = SIM / "chrono/vendor"
BUILD = SIM / "chrono/build"

# Host workspace root — set by devcontainer via ${localWorkspaceFolder}.
# Falls back to the container path; fix_paths.py corrects it for `make vendor`.
HOST_ROOT = os.environ.get("HOST_WORKSPACE", str(SIM)).rstrip("/")

# (container source path, vendor subdirectory name, headers_only)
# headers_only=True for large dirs where we only need .h/.hpp (e.g. the build root)
DEPS = [
    (Path("/home/trickfire/chrono/src"), "chrono_src", False),
    (Path("/home/trickfire/chrono/build"), "chrono_build", True),
    (Path("/opt/vsg/include"), "vsg", False),
    (Path("/usr/include/eigen3"), "eigen3", False),
]


def run_cmake() -> None:
    subprocess.run(
        [
            "cmake",
            "-GNinja",
            f"-B{BUILD}",
            f"-S{SIM / 'chrono'}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ],
        check=True,
    )


def copy_deps() -> None:
    VENDOR.mkdir(exist_ok=True)
    for src, name, headers_only in DEPS:
        if not src.exists():
            print(f"  skip  {src} (not found)")
            continue
        dest = VENDOR / name
        if dest.exists():
            shutil.rmtree(dest)
        if headers_only:
            dest.mkdir(parents=True)
            for header in src.rglob("*.[h]"):
                out = dest / header.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(header, out)
            for header in src.rglob("*.hpp"):
                out = dest / header.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(header, out)
        else:
            shutil.copytree(src, dest)
        print(f"  copy  {src} → vendor/{name}")


def rewrite_db() -> None:
    db_file = BUILD / "compile_commands.json"
    content = db_file.read_text()
    # Remap dependency headers to their vendor copies.
    # Sort longest path first so /chrono/build doesn't clobber /chrono/build/src.
    for src, name, _ in sorted(DEPS, key=lambda d: len(str(d[0])), reverse=True):
        content = content.replace(str(src), str(VENDOR / name))
    # Remap the container workspace prefix to the host path
    content = content.replace(str(SIM) + "/", HOST_ROOT + "/")
    db_file.write_text(content)


print("==> cmake configure")
run_cmake()
print("==> copying headers")
copy_deps()
print("==> rewriting compile_commands.json")
rewrite_db()
if HOST_ROOT == str(SIM):
    print("Done — HOST_WORKSPACE not set; run 'python3 chrono/scripts/fix_paths.py' on the host.")
else:
    print(f"Done — paths written for host root: {HOST_ROOT}")
