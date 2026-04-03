"""Command-line interface and subcommands for genbot."""

import argparse
import shutil
from pathlib import Path

from genbot import REPO_ROOT
from genbot.log import err, info, warn
from genbot.onshape import download, parse_onshape_url
from genbot.packages import (
    generate_bringup_pkg,
    generate_description_pkg,
    update_description_pkg,
)
from genbot.registry import load_robots_json, save_robots_json
from genbot.urdf import postprocess


# ---------------------------------------------------------------------------
# Subcommand helpers
# ---------------------------------------------------------------------------


def _scaffold_packages(robot: str, urdf_path: Path, meshes_src: Path, out_dir: Path) -> None:
    """Post-process URDF and write _description + _bringup packages."""
    if not meshes_src.exists():
        warn(f"Meshes directory {meshes_src} was not created")
    elif not any(meshes_src.iterdir()):
        warn(f"Meshes directory {meshes_src} is empty")

    info("Post-processing URDF...")
    geometry_urdf, control_xacro, joints, links = postprocess(urdf_path, robot)

    if joints:
        joint_names = [name for name, _, _ in joints]
        info(f"Found {len(joints)} revolute joint(s): {', '.join(joint_names)}")
    else:
        info("No revolute joints found - controller YAML will have a placeholder.")

    info("Generating description package...")
    generate_description_pkg(robot, geometry_urdf, control_xacro, meshes_src, out_dir)

    info("Generating bringup package...")
    generate_bringup_pkg(robot, joints, links, out_dir)

    info("Done!")
    info(f"Packages written to: {out_dir}")
    info(f"  {robot}_description/")
    info(f"  {robot}_bringup/")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_create(args) -> None:
    """Create mode: full scaffold of _description + _bringup packages"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Creating packages for robot: {robot}")

    api_url, doc_id, ws_id, el_id = parse_onshape_url(args.onshape_url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    urdf_path = workdir / "robot.urdf"
    if not urdf_path.exists():
        err(
            f"Expected {urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    _scaffold_packages(robot, urdf_path, workdir / "assets", out_dir)

    # Register in robots.json
    registry = load_robots_json()
    registry = [e for e in registry if e["name"] != robot]
    registry.append({"name": robot, "url": args.onshape_url})
    save_robots_json(registry)
    info(f"Registered '{robot}' in robots.json")


def cmd_local(args) -> None:
    """Local mode: generate packages from a local URDF file, no API calls."""
    robot = args.robot_name
    out_dir = Path(args.output_dir)
    urdf_path = Path(args.urdf)
    meshes_src = Path(args.assets) if args.assets else urdf_path.parent / "assets"

    if not urdf_path.exists():
        err(f"URDF file not found: {urdf_path}")

    info(f"Creating packages for robot: {robot} (local mode)")
    _scaffold_packages(robot, urdf_path, meshes_src, out_dir)


def cmd_raw(args) -> None:
    """raw mode: download raw URDF and assets from OnShape into a local directory."""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    if args.onshape_url:
        url = args.onshape_url
    else:
        registry = load_robots_json()
        entry = next((e for e in registry if e["name"] == robot), None)
        if entry is None:
            names = ", ".join(e["name"] for e in registry) or "(none)"
            err(
                f"Robot '{robot}' not found in robots.json.\n"
                f"  Available robots: {names}\n"
                "  Pass an OnShape URL as the second argument to use it directly."
            )
        url = entry["url"]

    api_url, doc_id, ws_id, el_id = parse_onshape_url(url)
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    dest = out_dir / robot
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest)

    info(f"Saved raw URDF and assets to: {dest}")
    info(f"  {dest}/robot.urdf")
    info(f"  {dest}/assets/")
    info("")
    info("Use with genbot local:")
    info(f"  python3 -m genbot local {robot} {dest}/robot.urdf --assets {dest}/assets/")


def cmd_update(args) -> None:
    """Update mode: replace only URDF and meshes in existing _description package"""
    robot = args.robot_name
    out_dir = Path(args.output_dir)

    info(f"Updating packages for robot: {robot}")

    registry = load_robots_json()
    entry = next((e for e in registry if e["name"] == robot), None)
    if entry is None:
        names = ", ".join(e["name"] for e in registry) or "(none)"
        err(
            f"Robot '{robot}' not found in robots.json.\n"
            f"  Available robots: {names}\n"
            "  Use 'create' mode to add a new robot."
        )

    api_url, doc_id, ws_id, el_id = parse_onshape_url(entry["url"])
    info(f"documentId={doc_id}  workspaceId={ws_id}  elementId={el_id}")

    workdir = download(robot, doc_id, ws_id, el_id, api_url)

    exported_urdf_path = workdir / "robot.urdf"
    exported_meshes_src = workdir / "assets"

    if not exported_urdf_path.exists():
        err(
            f"Expected {exported_urdf_path} but it was not found.\n"
            "  Check onshape-to-robot output above for errors."
        )

    if not exported_meshes_src.exists():
        warn(f"Meshes directory {exported_meshes_src} was not created")
    elif not any(exported_meshes_src.iterdir()):
        warn(f"Meshes directory {exported_meshes_src} is empty")

    info("Post-processing URDF...")
    geometry_urdf, _, _, _ = postprocess(exported_urdf_path, robot)

    info("Updating description package...")
    update_description_pkg(robot, geometry_urdf, exported_meshes_src, out_dir)

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

    # --- local ---
    local_parser = subparsers.add_parser(
        "local", help="Create packages from a local URDF (no API calls)"
    )
    local_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    local_parser.add_argument("urdf", help="Path to a local URDF file")
    local_parser.add_argument(
        "--assets",
        default=None,
        help="Path to meshes/assets directory (default: <urdf_dir>/assets/)",
    )
    local_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "robot-sim"),
        help="Directory to write packages into (default: robot-sim/)",
    )

    # --- raw ---
    raw_parser = subparsers.add_parser(
        "raw", help="Download raw URDF and assets from onshape into a local directory"
    )
    raw_parser.add_argument("robot_name", help="Name for the robot (e.g. arm, rover)")
    raw_parser.add_argument(
        "onshape_url",
        nargs="?",
        default=None,
        help="OnShape URL (optional, looks for robot in robot.json if not passed)",
    )
    raw_parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / ".github" / "genbot" / "tests"),
        help="Directory to save raw files into (default: .github/genbot/tests/)",
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
    elif args.command == "local":
        cmd_local(args)
    elif args.command == "raw":
        cmd_raw(args)
    elif args.command == "update":
        cmd_update(args)
