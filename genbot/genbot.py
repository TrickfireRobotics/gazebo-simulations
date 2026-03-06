#!/usr/bin/env python3

"""genbot - generate ROS2 packages from an OnShape URDF"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NoReturn

from dotenv import load_dotenv

TEMPLATES = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def _green(msg: str) -> str:
    return f"\033[0;32m{msg}\033[0m"


def _red(msg: str) -> str:
    return f"\033[0;31m{msg}\033[0m"


def _cyan(msg: str) -> str:
    return f"\033[0;36m{msg}\033[0m"


def info(msg: str) -> None:
    """Info log"""
    print(_green(f"[genbot] {msg}"))


def err(msg: str) -> NoReturn:
    """Error log, sys exits with 1"""
    print(_red(f"[genbot] ERROR: {msg}"), file=sys.stderr)
    sys.exit(1)


def step(msg: str) -> None:
    """Substep log"""
    print(_cyan(f"\n==> {msg}"))


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render(template_path: Path, robot: str, **extras) -> str:
    """Read a template and substitute __ROBOT__ (and any extras) into it"""
    text = template_path.read_text()
    text = text.replace("__ROBOT__", robot)
    for key, value in extras.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_template(src: Path, dest: Path, robot: str, **extras) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(src, robot, **extras))


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def load_credentials() -> dict:
    """Load ONSHAPE_API_KEY / ONSHAPE_API_SECRET from genbot/.env"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)

    key = os.environ.get("ONSHAPE_API_KEY")
    secret = os.environ.get("ONSHAPE_API_SECRET")

    if not key or not secret:
        err(
            "OnShape credentials not found.\n"
            "  Copy genbot/templates/.env.example → genbot/.env and fill in your keys, or\n"
            "  set ONSHAPE_API_KEY and ONSHAPE_API_SECRET environment variables."
        )

    return {"key": key, "secret": secret}


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

_ONSHAPE_URL_RE = re.compile(
    r"documents/([0-9a-f]+)/[wv]/([0-9a-f]+)/e/([0-9a-f]+)",
    re.IGNORECASE,
)


def parse_onshape_url(url: str) -> tuple:
    """Return (documentId, workspaceId, elementId) from an OnShape URL."""
    m = _ONSHAPE_URL_RE.search(url)
    if not m:
        err(
            f"Could not parse OnShape URL: {url}\n"
            "  Expected format: https://cad.onshape.com/documents/<docId>/w/<wsId>/e/<elId>"
        )
    return m.group(1), m.group(2), m.group(3)


# ---------------------------------------------------------------------------
# onshape-to-robot runner
# ---------------------------------------------------------------------------


def run_onshape_to_robot(doc_id: str, ws_id: str, el_id: str, creds: dict, workdir: Path) -> None:
    """Write config.json and invoke onshape-to-robot in workdir."""
    config = {
        "documentId": doc_id,
        "workspaceId": ws_id,
        "elementId": el_id,
    }
    (workdir / "config.json").write_text(json.dumps(config, indent=2))

    env = os.environ.copy()
    env["ONSHAPE_API_KEY"] = creds["key"]
    env["ONSHAPE_API_SECRET"] = creds["secret"]

    result = subprocess.run(
        ["onshape-to-robot", "."],
        cwd=workdir,
        env=env,
        check=True,
    )
    if result.returncode != 0:
        err(f"onshape-to-robot exited with code {result.returncode}")


# ---------------------------------------------------------------------------
# URDF joint parser
# ---------------------------------------------------------------------------


def parse_revolute_joints(urdf_path: Path) -> list:
    """Return list of joint names with type='revolute' from the URDF."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    return [
        j.get("name")
        for j in root.findall("joint")
        if j.get("type") == "revolute" and j.get("name")
    ]


# ---------------------------------------------------------------------------
# Package generators
# ---------------------------------------------------------------------------


def generate_description_pkg(robot: str, urdf_path: Path, meshes_src: Path, out_dir: Path) -> None:
    """Create <robot>_description package."""
    pkg_dir = out_dir / f"{robot}_description"
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    urdf_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(urdf_path, urdf_dir / f"{robot}.urdf")

    if meshes_src.exists():
        for item in meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    tmpl = TEMPLATES / "description"
    write_template(tmpl / "CMakeLists.txt", pkg_dir / "CMakeLists.txt", robot)
    write_template(tmpl / "package.xml", pkg_dir / "package.xml", robot)

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}")


def generate_bringup_pkg(robot: str, joints: list, out_dir: Path) -> None:
    """Create <robot>_bringup package."""
    pkg_dir = out_dir / f"{robot}_bringup"

    tmpl = TEMPLATES / "bringup"

    write_template(tmpl / "CMakeLists.txt", pkg_dir / "CMakeLists.txt", robot)
    write_template(tmpl / "package.xml", pkg_dir / "package.xml", robot)

    if joints:
        joints_yaml = "".join(f"      - {j}\n" for j in joints)
    else:
        joints_yaml = "      # no revolute joints found — fill in manually\n"

    write_template(
        tmpl / "config" / "controller.yaml",
        pkg_dir / "config" / f"{robot}.controller.yaml",
        robot,
        JOINTS=joints_yaml,
    )

    write_template(
        tmpl / "launch" / "gazebo.launch.py", pkg_dir / "launch" / "gazebo.launch.py", robot
    )
    write_template(
        tmpl / "launch" / "genesis.launch.py", pkg_dir / "launch" / "genesis.launch.py", robot
    )
    write_template(
        tmpl / "genesis" / "genesis_sim.py", pkg_dir / "genesis" / "genesis_sim.py", robot
    )

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Main method"""
    parser = argparse.ArgumentParser(
        description="Generate ROS2 packages from an OnShape model via onshape-to-robot."
    )
    parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    parser.add_argument("onshape_url", help="Full OnShape document URL")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent.parent / "robot-sim"),
        help="Directory to write packages into (default: robot-sim/)",
    )
    parser.add_argument(
        "--skip-download",
        metavar="WORKDIR",
        help="Skip onshape-to-robot; use existing output in WORKDIR",
    )
    args = parser.parse_args()

    robot = args.robot_name
    out_dir = Path(args.output_dir)

    step(f"Generating packages for robot: {robot}")

    creds = load_credentials()

    doc_id, ws_id, el_id = parse_onshape_url(args.onshape_url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    if args.skip_download:
        workdir = Path(args.skip_download)
        info(f"Skipping download; using existing workdir: {workdir}")
    else:
        workdir = Path(tempfile.mkdtemp(prefix="genbot_"))
        step("Running onshape-to-robot (this may take a while)...")
        run_onshape_to_robot(doc_id, ws_id, el_id, creds, workdir)

    urdf_path = workdir / "robot.urdf"
    meshes_src = workdir / "meshes"

    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    step("Parsing revolute joints from URDF...")
    joints = parse_revolute_joints(urdf_path)
    if joints:
        info(f"Found {len(joints)} revolute joint(s): {', '.join(joints)}")
    else:
        info("No revolute joints found — controller YAML will have a placeholder.")

    step("Generating description package...")
    generate_description_pkg(robot, urdf_path, meshes_src, out_dir)

    step("Generating bringup package...")
    generate_bringup_pkg(robot, joints, out_dir)

    step("Done!")
    info(f"Packages written to: {out_dir}")
    info(f"  {robot}_description/")
    info(f"  {robot}_bringup/")
    print()
    print("Next steps:")
    print(f"  cd robot-sim && colcon build --packages-select {robot}_description {robot}_bringup")


if __name__ == "__main__":
    main()
