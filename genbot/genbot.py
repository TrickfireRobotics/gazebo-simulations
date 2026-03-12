#!/usr/bin/env python3

"""genbot - generate and update ROS2 packages from an OnShape URDF"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

from urdf_postprocess import postprocess

TEMPLATES = Path(__file__).parent / "templates"
REPO_ROOT = Path(__file__).parent.parent
ROBOTS_JSON = REPO_ROOT / "robots.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def info(msg: str) -> None:
    """Info log"""
    print(f"[genbot] {msg}")


def err(msg: str) -> NoReturn:
    """Error log, sys exits with 1"""
    print(f"[genbot] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


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


def get_credentials() -> dict:
    """Read ONSHAPE_API_KEY / ONSHAPE_API_SECRET from environment variables."""
    key = os.environ.get("ONSHAPE_API_KEY")
    secret = os.environ.get("ONSHAPE_API_SECRET")

    if not key or not secret:
        err(
            "OnShape credentials not found.\n"
            "  Set ONSHAPE_API_KEY and ONSHAPE_API_SECRET environment variables."
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
# robots.json registry
# ---------------------------------------------------------------------------


def load_robots_json() -> dict:
    """Load the robot registry."""
    if not ROBOTS_JSON.exists():
        return {}
    return json.loads(ROBOTS_JSON.read_text())


def save_robots_json(data: dict) -> None:
    """Write the robot registry."""
    ROBOTS_JSON.write_text(json.dumps(data, indent=2) + "\n")


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
# Package generators
# ---------------------------------------------------------------------------


def generate_description_pkg(
    robot: str,
    geometry_urdf: str,
    control_xacro: str,
    meshes_src: Path,
    out_dir: Path,
) -> None:
    """Create <robot>_description package."""
    pkg_dir = out_dir / f"{robot}_description"
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    urdf_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir.mkdir(parents=True, exist_ok=True)

    # Write processed URDF
    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    # Write control xacro
    (urdf_dir / f"{robot}_control.urdf.xacro").write_text(control_xacro)

    # Copy meshes
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
        joints_yaml = "".join(f"      - {name}\n" for name, _, _ in joints)
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

    info(f"Created {pkg_dir.relative_to(out_dir.parent)}")


def update_description_pkg(robot: str, geometry_urdf: str, meshes_src: Path, out_dir: Path) -> None:
    """Update only the URDF and meshes in an existing <robot>_description package."""
    pkg_dir = out_dir / f"{robot}_description"
    urdf_dir = pkg_dir / "urdf"
    meshes_dir = pkg_dir / "meshes"

    if not pkg_dir.exists():
        err(f"Package {pkg_dir} does not exist. Use 'create' mode first.")

    # Replace URDF (but NOT the control xacro)
    (urdf_dir / f"{robot}.urdf").write_text(geometry_urdf)

    # Replace meshes
    if meshes_src.exists():
        if meshes_dir.exists():
            shutil.rmtree(meshes_dir)
        meshes_dir.mkdir(parents=True, exist_ok=True)
        for item in meshes_src.iterdir():
            dest = meshes_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    info(f"Updated {pkg_dir.relative_to(out_dir.parent)}/urdf and meshes")


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------


def download(doc_id: str, ws_id: str, el_id: str) -> Path:
    """Run onshape-to-robot and return the working directory."""
    creds = get_credentials()
    workdir = Path(tempfile.mkdtemp(prefix="genbot_"))
    info("Running onshape-to-robot (this may take a while)...")
    run_onshape_to_robot(doc_id, ws_id, el_id, creds, workdir)
    return workdir


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_create(args) -> None:
    """Create mode: full scaffold of _description + _bringup packages."""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Creating packages for robot: {robot}")

    if not args.onshape_url:
        err("OnShape URL is required for 'create' mode.")

    doc_id, ws_id, el_id = parse_onshape_url(args.onshape_url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(doc_id, ws_id, el_id)

    urdf_path = workdir / "robot.urdf"
    meshes_src = workdir / "meshes"

    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    info("Post-processing URDF...")
    geometry_urdf, control_xacro, joints = postprocess(urdf_path, robot)

    if joints:
        joint_names = [name for name, _, _ in joints]
        info(f"Found {len(joints)} revolute joint(s): {', '.join(joint_names)}")
    else:
        info("No revolute joints found — controller YAML will have a placeholder.")

    info("Generating description package...")
    generate_description_pkg(robot, geometry_urdf, control_xacro, meshes_src, out_dir)

    info("Generating bringup package...")
    generate_bringup_pkg(robot, joints, out_dir)

    # Register in robots.json
    registry = load_robots_json()
    registry[robot] = {
        "documentId": doc_id,
        "workspaceId": ws_id,
        "elementId": el_id,
        "onshapeUrl": args.onshape_url,
    }
    save_robots_json(registry)
    info(f"Registered '{robot}' in robots.json")

    info("Done!")
    info(f"Packages written to: {out_dir}")
    info(f"  {robot}_description/")
    info(f"  {robot}_bringup/")


def cmd_update(args) -> None:
    """Update mode: replace only URDF and meshes in existing _description package."""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Updating packages for robot: {robot}")

    registry = load_robots_json()
    if robot not in registry:
        err(
            f"Robot '{robot}' not found in robots.json.\n"
            f"  Available robots: {', '.join(registry.keys()) or '(none)'}\n"
            "  Use 'create' mode to add a new robot."
        )

    entry = registry[robot]
    doc_id = entry["documentId"]
    ws_id = entry["workspaceId"]
    el_id = entry["elementId"]
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(doc_id, ws_id, el_id)

    urdf_path = workdir / "robot.urdf"
    meshes_src = workdir / "meshes"

    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    info("Post-processing URDF...")
    geometry_urdf, _, _ = postprocess(urdf_path, robot)

    info("Updating description package...")
    update_description_pkg(robot, geometry_urdf, meshes_src, out_dir)

    info("Done!")
    info(f"Updated {robot}_description/urdf and meshes only.")
    info("Bringup package and control xacro were NOT modified.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Main method"""
    parser = argparse.ArgumentParser(
        description="Generate or update ROS2 packages from an OnShape model via onshape-to-robot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- create ---
    create_parser = subparsers.add_parser("create", help="Create new robot packages")
    create_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    create_parser.add_argument("onshape_url", help="Full OnShape document URL")
    create_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory to write packages into (default: robot-sim/)",
    )

    # --- update ---
    update_parser = subparsers.add_parser("update", help="Update existing robot URDF and meshes")
    update_parser.add_argument(
        "robot_name", help="Name of the robot to update (must exist in robots.json)"
    )
    update_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory containing packages (default: robot-sim/)",
    )

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "update":
        cmd_update(args)


if __name__ == "__main__":
    main()
